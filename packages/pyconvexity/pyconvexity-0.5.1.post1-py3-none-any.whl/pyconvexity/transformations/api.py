"""
High-level API for network transformations.

Provides user-friendly functions for transforming network data.
"""

from typing import Any, Callable, Dict, Optional

from pyconvexity.transformations.time_axis import TimeAxisModifier


def modify_time_axis(
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

    This function copies a network database while adjusting the time axis -
    useful for truncating time periods, changing resolution, or both.
    All timeseries data is automatically resampled to match the new time axis.

    Args:
        source_db_path: Path to source database
        target_db_path: Path to target database (will be created)
        new_start: Start datetime as ISO string (e.g., "2024-01-01 00:00:00")
        new_end: End datetime as ISO string (e.g., "2024-12-31 23:00:00")
        new_resolution_minutes: New time resolution in minutes (e.g., 60 for hourly)
        new_network_name: Optional new name for the network
        convert_timeseries: If True, resample timeseries data to new time axis.
            If False, wipe all timeseries attributes (useful for creating templates)
        progress_callback: Optional callback for progress updates.
            Called with (progress: float, message: str) where progress is 0-100.

    Returns:
        Dictionary with results and statistics:
            - success: bool - Whether the operation completed successfully
            - source_db_path: str - Path to source database
            - target_db_path: str - Path to created target database
            - new_periods_count: int - Number of time periods in new database
            - new_resolution_minutes: int - Resolution in minutes
            - new_start: str - Start time
            - new_end: str - End time
            - processing_stats: dict - Detailed processing statistics

    Raises:
        ValueError: If time parameters are invalid (end before start, negative resolution)
        FileNotFoundError: If source database doesn't exist

    Example:
        # Truncate a yearly model to one week with hourly resolution
        result = modify_time_axis(
            source_db_path="full_year_model.db",
            target_db_path="one_week_model.db",
            new_start="2024-01-01 00:00:00",
            new_end="2024-01-07 23:00:00",
            new_resolution_minutes=60,
            new_network_name="One Week Test Model",
        )

        if result["success"]:
            print(f"Created {result['target_db_path']} with {result['new_periods_count']} periods")

    Example with progress tracking:
        def on_progress(progress: float, message: str):
            print(f"[{progress:.0f}%] {message}")

        result = modify_time_axis(
            source_db_path="original.db",
            target_db_path="resampled.db",
            new_start="2024-01-01",
            new_end="2024-06-30",
            new_resolution_minutes=60,
            progress_callback=on_progress,
        )
    """
    modifier = TimeAxisModifier()
    return modifier.modify_time_axis(
        source_db_path=source_db_path,
        target_db_path=target_db_path,
        new_start=new_start,
        new_end=new_end,
        new_resolution_minutes=new_resolution_minutes,
        new_network_name=new_network_name,
        convert_timeseries=convert_timeseries,
        progress_callback=progress_callback,
    )
