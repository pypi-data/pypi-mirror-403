"""
Time axis modification for PyConvexity networks.

Handles truncation and resampling of network time periods and all associated timeseries data.
"""

import logging
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from pyconvexity.core.database import database_context
from pyconvexity.core.types import TimePeriod
from pyconvexity.models.network import get_network_info, get_network_time_periods
from pyconvexity.timeseries import get_timeseries, set_timeseries

logger = logging.getLogger(__name__)


class TimeAxisModifier:
    """
    Service for modifying network time axis and resampling all timeseries data.

    This class handles the complete workflow of:
    1. Copying a network database
    2. Modifying the time axis (start, end, resolution)
    3. Resampling all timeseries data to match the new time axis

    Example:
        modifier = TimeAxisModifier()
        result = modifier.modify_time_axis(
            source_db_path="original.db",
            target_db_path="resampled.db",
            new_start="2024-01-01 00:00:00",
            new_end="2024-01-07 23:00:00",
            new_resolution_minutes=60,
        )
    """

    def __init__(self):
        logger.debug("TimeAxisModifier initialized")

    def _minutes_to_freq_str(self, minutes: int) -> str:
        """Convert minutes to a pandas frequency string, preferring aliases like 'D' or 'h'."""
        if minutes == 1440:
            return "D"
        if minutes % (60 * 24) == 0:
            days = minutes // (60 * 24)
            return f"{days}D"
        if minutes == 60:
            return "h"
        if minutes % 60 == 0:
            hours = minutes // 60
            return f"{hours}h"
        return f"{minutes}min"

    def modify_time_axis(
        self,
        source_db_path: str,
        target_db_path: str,
        new_start: str,
        new_end: str,
        new_resolution_minutes: int,
        new_network_name: Optional[str] = None,
        convert_timeseries: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new database with modified time axis and resampled timeseries data.

        This method creates a copy of the source database and modifies its time axis,
        optionally resampling all timeseries data to match the new time periods.

        Args:
            source_db_path: Path to source database
            target_db_path: Path to target database (will be created)
            new_start: Start datetime as ISO string (e.g., "2024-01-01 00:00:00")
            new_end: End datetime as ISO string (e.g., "2024-12-31 23:00:00")
            new_resolution_minutes: New time resolution in minutes (e.g., 60 for hourly)
            new_network_name: Optional new name for the network
            convert_timeseries: If True, resample timeseries data. If False, wipe all timeseries
            progress_callback: Optional callback for progress updates (progress: float, message: str)

        Returns:
            Dictionary with results and statistics:
                - success: bool
                - source_db_path: str
                - target_db_path: str
                - new_periods_count: int
                - new_resolution_minutes: int
                - new_start: str
                - new_end: str
                - processing_stats: dict with detailed statistics

        Raises:
            ValueError: If time parameters are invalid
            FileNotFoundError: If source database doesn't exist
        """

        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
            logger.info(f"[{progress:.1f}%] {message}")

        try:
            update_progress(0, "Starting time axis modification...")

            # Validate inputs
            start_dt = pd.Timestamp(new_start)
            end_dt = pd.Timestamp(new_end)

            if end_dt <= start_dt:
                raise ValueError("End time must be after start time")

            if new_resolution_minutes <= 0:
                raise ValueError("Time resolution must be positive")

            update_progress(5, "Validating source database...")

            # Validate source database and get network info
            with database_context(source_db_path, read_only=True) as source_conn:
                network_info = get_network_info(source_conn)
                if not network_info:
                    raise ValueError("No network metadata found in source database")

            # Generate new time periods
            update_progress(10, "Generating new time axis...")
            new_time_periods = self._generate_time_periods(
                start_dt, end_dt, new_resolution_minutes
            )
            update_progress(15, f"Generated {len(new_time_periods)} new time periods")

            # Copy database schema and static data
            update_progress(20, "Creating target database...")
            self._copy_database_structure(
                source_db_path,
                target_db_path,
                new_time_periods,
                new_resolution_minutes,
                new_network_name,
                update_progress,
            )

            # Process timeseries data based on convert_timeseries flag
            if convert_timeseries:
                update_progress(40, "Processing timeseries data...")
                stats = self._process_all_timeseries(
                    source_db_path,
                    target_db_path,
                    new_time_periods,
                    new_resolution_minutes,
                    update_progress,
                )
            else:
                update_progress(40, "Wiping timeseries data...")
                stats = self._wipe_all_timeseries(target_db_path, update_progress)

            update_progress(95, "Finalizing database...")

            # Validate target database
            with database_context(target_db_path, read_only=True) as target_conn:
                target_network_info = get_network_info(target_conn)
                if not target_network_info:
                    raise ValueError("Failed to create target network")

            update_progress(100, "Time axis modification completed successfully")

            return {
                "success": True,
                "source_db_path": source_db_path,
                "target_db_path": target_db_path,
                "new_periods_count": len(new_time_periods),
                "original_resolution_minutes": None,  # Could be calculated from source
                "new_resolution_minutes": new_resolution_minutes,
                "new_start": new_start,
                "new_end": new_end,
                "processing_stats": stats,
            }

        except Exception as e:
            logger.error(f"Time axis modification failed: {e}", exc_info=True)

            # Clean up partial target file
            try:
                target_path = Path(target_db_path)
                if target_path.exists():
                    target_path.unlink()
                    logger.info(f"Cleaned up partial target database: {target_db_path}")
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to clean up partial target database: {cleanup_error}"
                )

            raise

    def _generate_time_periods(
        self, start: pd.Timestamp, end: pd.Timestamp, resolution_minutes: int
    ) -> List[TimePeriod]:
        """Generate new time periods based on start, end, and resolution."""

        # Create time range
        freq_str = self._minutes_to_freq_str(resolution_minutes)
        timestamps = pd.date_range(
            start=start, end=end, freq=freq_str, inclusive="both"
        )

        periods = []
        for i, timestamp in enumerate(timestamps):
            # Convert to Unix timestamp (seconds)
            unix_timestamp = int(timestamp.timestamp())

            # Create formatted time string (UTC to avoid DST issues)
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            periods.append(
                TimePeriod(
                    timestamp=unix_timestamp,
                    period_index=i,
                    formatted_time=formatted_time,
                )
            )

        logger.info(
            f"Generated {len(periods)} time periods from {start} to {end} "
            f"at {resolution_minutes}min resolution"
        )
        return periods

    def _copy_database_structure(
        self,
        source_path: str,
        target_path: str,
        new_periods: List[TimePeriod],
        new_resolution_minutes: int,
        new_network_name: Optional[str],
        progress_callback: Callable[[float, str], None],
    ):
        """Copy database schema and static data, update time periods."""

        # Copy entire database file as starting point
        progress_callback(25, "Copying database file...")
        shutil.copy2(source_path, target_path)

        # Connect to target database and update time periods
        progress_callback(30, "Updating time periods...")

        with database_context(target_path) as target_conn:
            # Clear existing time periods (single row for entire database)
            target_conn.execute("DELETE FROM network_time_periods")

            # Insert new optimized time periods metadata
            if new_periods:
                period_count = len(new_periods)
                start_timestamp = new_periods[0].timestamp

                # Calculate interval in seconds
                if len(new_periods) > 1:
                    interval_seconds = (
                        new_periods[1].timestamp - new_periods[0].timestamp
                    )
                else:
                    interval_seconds = new_resolution_minutes * 60

                target_conn.execute(
                    """
                    INSERT INTO network_time_periods (period_count, start_timestamp, interval_seconds)
                    VALUES (?, ?, ?)
                """,
                    (period_count, start_timestamp, interval_seconds),
                )

            # Update network metadata with new time range and resolution
            start_time = new_periods[0].formatted_time if new_periods else None
            end_time = new_periods[-1].formatted_time if new_periods else None

            # Convert resolution to ISO 8601 duration format
            if new_resolution_minutes < 60:
                time_interval = f"PT{new_resolution_minutes}M"
            elif new_resolution_minutes % 60 == 0:
                hours = new_resolution_minutes // 60
                time_interval = f"PT{hours}H"
            else:
                time_interval = f"PT{new_resolution_minutes}M"

            # Update network metadata including name if provided
            if new_network_name:
                target_conn.execute(
                    """
                    UPDATE network_metadata 
                    SET name = ?, time_start = ?, time_end = ?, time_interval = ?, updated_at = datetime('now')
                """,
                    (new_network_name, start_time, end_time, time_interval),
                )
            else:
                target_conn.execute(
                    """
                    UPDATE network_metadata 
                    SET time_start = ?, time_end = ?, time_interval = ?, updated_at = datetime('now')
                """,
                    (start_time, end_time, time_interval),
                )

            # Clear data that becomes invalid with new time axis
            progress_callback(32, "Clearing time-dependent data...")

            # Clear solve results (they're tied to specific time periods)
            target_conn.execute("DELETE FROM network_solve_results")

            # Clear year-based solve results (also tied to specific time periods)
            target_conn.execute("DELETE FROM network_solve_results_by_year")

            # Clear any cached data in network_data_store that might be time-dependent
            target_conn.execute(
                """
                DELETE FROM network_data_store 
                WHERE category IN ('results', 'statistics', 'cache')
            """
            )

            target_conn.commit()
            progress_callback(35, f"Updated time periods: {len(new_periods)} periods")

    def _process_all_timeseries(
        self,
        source_path: str,
        target_path: str,
        new_periods: List[TimePeriod],
        new_resolution_minutes: int,
        progress_callback: Callable[[float, str], None],
    ) -> Dict[str, Any]:
        """Process all timeseries attributes across all scenarios."""

        stats = {
            "total_components_processed": 0,
            "total_attributes_processed": 0,
            "total_scenarios_processed": 0,
            "attributes_by_component_type": {},
            "errors": [],
        }

        try:
            # Find all components with timeseries data
            components_with_timeseries = self._find_components_with_timeseries(
                source_path
            )

            total_items = len(components_with_timeseries)
            progress_callback(
                45, f"Found {total_items} timeseries attributes to process"
            )

            if total_items == 0:
                progress_callback(90, "No timeseries data found to process")
                return stats

            # Group by scenario for batch processing efficiency
            by_scenario: Dict[Optional[int], List[Tuple[int, str]]] = {}
            for comp_id, attr_name, scenario_id in components_with_timeseries:
                if scenario_id not in by_scenario:
                    by_scenario[scenario_id] = []
                by_scenario[scenario_id].append((comp_id, attr_name))

            stats["total_scenarios_processed"] = len(by_scenario)
            logger.info(
                f"Processing timeseries across {len(by_scenario)} scenarios: "
                f"{list(by_scenario.keys())}"
            )

            # Process each scenario
            processed = 0
            for scenario_id, items in by_scenario.items():
                scenario_name = f"scenario_{scenario_id}" if scenario_id else "base"
                progress_callback(
                    45 + (processed * 40 / total_items),
                    f"Processing scenario {scenario_name} ({len(items)} attributes)",
                )

                for comp_id, attr_name in items:
                    try:
                        # Get component type for statistics
                        comp_type = self._get_component_type(source_path, comp_id)
                        if comp_type not in stats["attributes_by_component_type"]:
                            stats["attributes_by_component_type"][comp_type] = 0

                        # Load original timeseries using pyconvexity API
                        original_timeseries = get_timeseries(
                            source_path, comp_id, attr_name, scenario_id
                        )

                        if not original_timeseries or not original_timeseries.values:
                            logger.warning(
                                f"No timeseries data found for component {comp_id}, "
                                f"attribute {attr_name}"
                            )
                            continue

                        # Get original time periods to understand the time mapping
                        with database_context(
                            source_path, read_only=True
                        ) as source_conn:
                            original_periods = get_network_time_periods(source_conn)

                        # Resample to new time axis with proper time-based slicing
                        resampled_values = self._resample_timeseries_with_time_mapping(
                            original_timeseries.values,
                            original_periods,
                            new_periods,
                            new_resolution_minutes,
                        )

                        if resampled_values:
                            # Save to target database using pyconvexity API
                            set_timeseries(
                                target_path,
                                comp_id,
                                attr_name,
                                resampled_values,
                                scenario_id,
                            )
                            stats["attributes_by_component_type"][comp_type] += 1
                            stats["total_attributes_processed"] += 1

                        processed += 1

                        if processed % 10 == 0:  # Update progress every 10 items
                            progress = 45 + (processed * 40 / total_items)
                            progress_callback(
                                progress,
                                f"Processed {processed}/{total_items} attributes",
                            )

                    except Exception as e:
                        error_msg = (
                            f"Failed to process component {comp_id}, "
                            f"attribute {attr_name}: {str(e)}"
                        )
                        logger.error(error_msg)
                        stats["errors"].append(error_msg)
                        continue

            # Count unique components processed
            unique_components = set()
            for comp_id, _, _ in components_with_timeseries:
                unique_components.add(comp_id)
            stats["total_components_processed"] = len(unique_components)

            progress_callback(
                87,
                f"Completed processing {stats['total_attributes_processed']} "
                "timeseries attributes",
            )

            # VACUUM the database to reclaim space from replaced timeseries data
            progress_callback(88, "Reclaiming database space...")
            with database_context(target_path) as conn:
                conn.execute("VACUUM")
            progress_callback(
                90,
                f"Database space reclaimed. Processed "
                f"{stats['total_attributes_processed']} timeseries attributes.",
            )

        except Exception as e:
            logger.error(f"Error processing timeseries data: {e}", exc_info=True)
            stats["errors"].append(f"General processing error: {str(e)}")
            raise

        return stats

    def _wipe_all_timeseries(
        self, target_db_path: str, progress_callback: Callable[[float, str], None]
    ) -> Dict[str, Any]:
        """Wipes all timeseries attributes."""

        with database_context(target_db_path) as target_conn:
            try:
                # Count timeseries attributes before deletion for statistics
                cursor = target_conn.execute(
                    """
                    SELECT COUNT(*) FROM component_attributes
                    WHERE storage_type = 'timeseries'
                """
                )
                count_before = cursor.fetchone()[0]

                # Clear all timeseries attributes
                target_conn.execute(
                    """
                    DELETE FROM component_attributes
                    WHERE storage_type = 'timeseries'
                """
                )

                target_conn.commit()
                progress_callback(
                    85, f"Wiped {count_before} timeseries attributes from network."
                )

                # VACUUM the database to reclaim space and reduce file size
                progress_callback(87, "Reclaiming database space...")
                target_conn.execute("VACUUM")
                progress_callback(
                    90,
                    f"Database space reclaimed. Wiped {count_before} timeseries attributes.",
                )

                return {
                    "total_attributes_wiped": count_before,
                    "total_components_processed": 0,
                    "total_attributes_processed": 0,
                    "total_scenarios_processed": 0,
                    "attributes_by_component_type": {},
                    "errors": [],
                }
            except Exception as e:
                logger.error(
                    f"Failed to wipe timeseries attributes: {e}", exc_info=True
                )
                return {
                    "total_attributes_wiped": 0,
                    "total_components_processed": 0,
                    "total_attributes_processed": 0,
                    "total_scenarios_processed": 0,
                    "attributes_by_component_type": {},
                    "errors": [f"Failed to wipe timeseries attributes: {str(e)}"],
                }

    def _find_components_with_timeseries(
        self, db_path: str
    ) -> List[Tuple[int, str, Optional[int]]]:
        """Find all components that have timeseries attributes."""

        with database_context(db_path, read_only=True) as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT component_id, attribute_name, scenario_id
                FROM component_attributes
                WHERE storage_type = 'timeseries'
                AND timeseries_data IS NOT NULL
                ORDER BY component_id, attribute_name, scenario_id
            """
            )

            results = cursor.fetchall()
            logger.info(f"Found {len(results)} timeseries attributes in database")

            return results

    def _get_component_type(self, db_path: str, component_id: int) -> str:
        """Get component type for statistics tracking."""
        with database_context(db_path, read_only=True) as conn:
            cursor = conn.execute(
                "SELECT component_type FROM components WHERE id = ?", (component_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else "UNKNOWN"

    def _resample_timeseries_with_time_mapping(
        self,
        original_values: List[float],
        original_periods: List[TimePeriod],
        new_periods: List[TimePeriod],
        new_resolution_minutes: int,
    ) -> List[float]:
        """
        Resample timeseries data to new time axis with proper time-based slicing.

        This method:
        1. First slices the original data to match the new time range
        2. Then resamples the sliced data to the new resolution

        Args:
            original_values: Original timeseries values
            original_periods: Original time periods from source database
            new_periods: New time periods for target database
            new_resolution_minutes: New time resolution in minutes

        Returns:
            Resampled values list, or empty list if resampling fails
        """

        if not original_values or not new_periods or not original_periods:
            return []

        try:
            # Get time bounds for the new time axis
            new_start_timestamp = new_periods[0].timestamp
            new_end_timestamp = new_periods[-1].timestamp
            
            # Calculate the duration of one new period in seconds
            # This is needed to properly include all original data within the last new period
            new_period_duration_seconds = new_resolution_minutes * 60
            
            # The end timestamp represents the START of the last period, not its end.
            # To include all original data that falls within the last period,
            # we need to extend the end boundary by the period duration (minus 1 second
            # to avoid including the start of the next period).
            effective_end_timestamp = new_end_timestamp + new_period_duration_seconds - 1

            logger.debug(
                f"Original data: {len(original_values)} points, "
                f"{len(original_periods)} periods"
            )
            logger.debug(
                f"New time range: {new_periods[0].formatted_time} to "
                f"{new_periods[-1].formatted_time}"
            )
            logger.debug(
                f"Effective end timestamp for slicing: {effective_end_timestamp} "
                f"(added {new_period_duration_seconds}s period duration)"
            )

            # Find the slice of original data that falls within the new time range
            start_idx = 0
            end_idx = len(original_periods)

            # Find start index - first period >= new_start_timestamp
            for i, period in enumerate(original_periods):
                if period.timestamp >= new_start_timestamp:
                    start_idx = i
                    break

            # Find end index - last period <= effective_end_timestamp
            # Use effective_end_timestamp to include all data within the last new period
            for i in range(len(original_periods) - 1, -1, -1):
                if original_periods[i].timestamp <= effective_end_timestamp:
                    end_idx = i + 1  # +1 because slice end is exclusive
                    break

            # Slice the original data to the new time range
            if start_idx >= len(original_values):
                logger.warning("Start index beyond original data range")
                return []

            end_idx = min(end_idx, len(original_values))
            sliced_values = original_values[start_idx:end_idx]
            sliced_periods = original_periods[start_idx:end_idx]

            logger.debug(
                f"Sliced data: {len(sliced_values)} points from index "
                f"{start_idx} to {end_idx}"
            )

            if not sliced_values:
                logger.warning("No data in the specified time range")
                return []

            # Now resample the sliced data to the new resolution
            return self._resample_sliced_data(sliced_values, len(new_periods))

        except Exception as e:
            logger.error(
                f"Failed to resample timeseries with time mapping: {e}", exc_info=True
            )
            # Return empty list rather than failing the entire operation
            return []

    def _resample_sliced_data(
        self, sliced_values: List[float], target_length: int
    ) -> List[float]:
        """
        Resample already time-sliced data to target length.

        For downsampling (fewer periods): Use mean aggregation
        For upsampling (more periods): Use interpolation
        For same length: Return as-is
        """

        if not sliced_values:
            return []

        try:
            original_length = len(sliced_values)

            if original_length == target_length:
                # Same length, return as-is
                return sliced_values
            elif original_length > target_length:
                # Downsample using mean aggregation for better accuracy
                return self._downsample_with_mean(sliced_values, target_length)
            else:
                # Upsample using linear interpolation
                return self._upsample_with_interpolation(sliced_values, target_length)

        except Exception as e:
            logger.error(f"Failed to resample sliced data: {e}", exc_info=True)
            return []

    def _downsample_with_mean(
        self, values: List[float], target_length: int
    ) -> List[float]:
        """Downsample using mean aggregation for better accuracy than simple sampling."""
        if target_length >= len(values):
            return values

        # Calculate how many original points to average for each new point
        chunk_size = len(values) / target_length
        resampled = []

        for i in range(target_length):
            start_idx = int(i * chunk_size)
            end_idx = int((i + 1) * chunk_size)

            # Handle the last chunk to include any remaining values
            if i == target_length - 1:
                end_idx = len(values)

            # Calculate mean of the chunk
            chunk_values = values[start_idx:end_idx]
            if chunk_values:
                mean_value = sum(chunk_values) / len(chunk_values)
                resampled.append(mean_value)
            else:
                # Fallback to last known value
                resampled.append(values[start_idx] if start_idx < len(values) else 0.0)

        return resampled

    def _upsample_with_interpolation(
        self, values: List[float], target_length: int
    ) -> List[float]:
        """Upsample using linear interpolation for smoother results."""
        if target_length <= len(values):
            return values[:target_length]

        # Use numpy for efficient interpolation
        original_indices = np.linspace(0, len(values) - 1, len(values))
        target_indices = np.linspace(0, len(values) - 1, target_length)

        # Perform linear interpolation
        interpolated = np.interp(target_indices, original_indices, values)

        return interpolated.tolist()
