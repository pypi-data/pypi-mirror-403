"""
Dashboard configuration for Convexity app visualization.

Allows programmatic configuration of the analytics dashboard layout
that will be displayed when the model is loaded in the Convexity app.

Example:
    >>> from pyconvexity.dashboard import set_dashboard_config, DashboardConfig, auto_layout
    >>> 
    >>> charts = [
    ...     {
    ...         "id": "dispatch-1",
    ...         "title": "Generation by Carrier",
    ...         "visible": True,
    ...         "view": {
    ...             "timeseries": {
    ...                 "component": "Generator",
    ...                 "attribute": "p",
    ...                 "group_by": "carrier"
    ...             }
    ...         }
    ...     },
    ...     {
    ...         "id": "lmp-1",
    ...         "title": "Locational Marginal Prices",
    ...         "visible": True,
    ...         "view": {
    ...             "timeseries": {
    ...                 "component": "Bus",
    ...                 "attribute": "marginal_price"
    ...             }
    ...         }
    ...     }
    ... ]
    >>> 
    >>> config = DashboardConfig(charts=charts, layout=auto_layout(charts))
    >>> set_dashboard_config(conn, config)
"""

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class DashboardConfig:
    """
    Dashboard configuration for the Convexity app analytics view.
    
    Attributes:
        charts: List of chart configurations. Each chart is a dict with:
            - id: Unique identifier (e.g., "dispatch-1", "lmp-main")
            - title: Display title
            - visible: Whether chart is shown
            - view: Chart type configuration (see below)
            - filters: Optional chart-specific filters
            
        layout: List of layout positions. Each position is a dict with:
            - i: Chart ID (must match a chart's id)
            - x: Grid column (0-11)
            - y: Grid row
            - w: Width in grid units (max 12)
            - h: Height in grid units
            
        selected_scenario_id: Pre-selected scenario ID (optional)
        selected_ensemble_name: Pre-selected ensemble name (optional)
        selected_bus_id: Pre-selected bus ID for filtering (optional)
    
    Chart View Types:
        Timeseries (dispatch, LMP, etc.):
            {"timeseries": {"component": "Generator", "attribute": "p", "group_by": "carrier"}}
            {"timeseries": {"component": "Bus", "attribute": "marginal_price"}}
            {"timeseries": {"component": "Load", "attribute": "p"}}
            
        Network map:
            {"network": {"network": true}}
            
        Statistics/Summary:
            {"statistic": {"statistic": "optimal_capacity", "metric": "capacity"}}
            {"statistic": {"statistic": "total_cost"}}
    """
    charts: List[Dict[str, Any]]
    layout: List[Dict[str, Any]]
    selected_scenario_id: Optional[int] = None
    selected_ensemble_name: Optional[str] = None
    selected_bus_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "charts": self.charts,
            "layout": self.layout,
        }
        # Only include optional fields if set (matches Rust's skip_serializing_if)
        if self.selected_scenario_id is not None:
            result["selected_scenario_id"] = self.selected_scenario_id
        if self.selected_ensemble_name is not None:
            result["selected_ensemble_name"] = self.selected_ensemble_name
        if self.selected_bus_id is not None:
            result["selected_bus_id"] = self.selected_bus_id
        return result


def set_dashboard_config(conn: sqlite3.Connection, config: DashboardConfig) -> int:
    """
    Save dashboard configuration to the database.
    
    This configuration will be loaded by the Convexity app when the model
    is opened, setting up the analytics dashboard with the specified charts
    and layout.
    
    Args:
        conn: Database connection
        config: Dashboard configuration
        
    Returns:
        Row ID of the stored configuration
        
    Example:
        >>> config = DashboardConfig(
        ...     charts=[{"id": "dispatch-1", "title": "Dispatch", "visible": True, 
        ...              "view": {"timeseries": {"component": "Generator", "attribute": "p", "group_by": "carrier"}}}],
        ...     layout=[{"i": "dispatch-1", "x": 0, "y": 0, "w": 12, "h": 40}]
        ... )
        >>> set_dashboard_config(conn, config)
    """
    data_json = json.dumps(config.to_dict())
    data_bytes = data_json.encode('utf-8')
    
    # Check if analytics config exists
    cursor = conn.execute(
        "SELECT id FROM network_data_store WHERE category = 'analytics_view' AND name = 'default'"
    )
    row = cursor.fetchone()
    
    if row:
        # Update existing
        row_id = row[0]
        conn.execute(
            "UPDATE network_data_store SET data = ?, updated_at = datetime('now') WHERE id = ?",
            (data_bytes, row_id)
        )
    else:
        # Insert new
        conn.execute(
            """INSERT INTO network_data_store (category, name, data_format, data, created_at, updated_at)
               VALUES ('analytics_view', 'default', 'json', ?, datetime('now'), datetime('now'))""",
            (data_bytes,)
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    conn.commit()
    return row_id


def get_dashboard_config(conn: sqlite3.Connection) -> Optional[DashboardConfig]:
    """
    Get the current dashboard configuration from the database.
    
    Args:
        conn: Database connection
        
    Returns:
        DashboardConfig if one exists, None otherwise
    """
    cursor = conn.execute(
        """SELECT data FROM network_data_store 
           WHERE category = 'analytics_view' 
           ORDER BY updated_at DESC LIMIT 1"""
    )
    row = cursor.fetchone()
    
    if not row:
        return None
    
    data_bytes = row[0]
    if isinstance(data_bytes, bytes):
        data_str = data_bytes.decode('utf-8')
    else:
        data_str = data_bytes
        
    data = json.loads(data_str)
    
    return DashboardConfig(
        charts=data.get("charts", []),
        layout=data.get("layout", []),
        selected_scenario_id=data.get("selected_scenario_id"),
        selected_ensemble_name=data.get("selected_ensemble_name"),
        selected_bus_id=data.get("selected_bus_id"),
    )


def auto_layout(charts: List[Dict[str, Any]], cols: int = 12) -> List[Dict[str, Any]]:
    """
    Automatically generate layout positions for charts.
    
    Places charts in a vertical stack, each taking full width.
    Timeseries charts get height 40, others get height 20.
    
    Args:
        charts: List of chart configurations
        cols: Grid columns (default 12)
        
    Returns:
        List of layout position dicts
        
    Example:
        >>> charts = [
        ...     {"id": "dispatch-1", "title": "Dispatch", "visible": True, 
        ...      "view": {"timeseries": {...}}},
        ...     {"id": "network-1", "title": "Network", "visible": True,
        ...      "view": {"network": {"network": True}}}
        ... ]
        >>> layout = auto_layout(charts)
        >>> # Returns: [{"i": "dispatch-1", "x": 0, "y": 0, "w": 12, "h": 40}, ...]
    """
    layout = []
    y = 0
    
    for chart in charts:
        if not chart.get("visible", True):
            continue
            
        chart_id = chart["id"]
        view = chart.get("view", {})
        
        # Determine chart dimensions based on type
        if "timeseries" in view:
            w, h = 12, 40
        elif "network" in view:
            w, h = 6, 40
        elif "statistic" in view:
            w, h = 6, 20
        else:
            w, h = 12, 20
        
        layout.append({
            "i": chart_id,
            "x": 0,
            "y": y,
            "w": w,
            "h": h,
        })
        
        y += h
    
    return layout


def clear_dashboard_config(conn: sqlite3.Connection) -> bool:
    """
    Remove any existing dashboard configuration.
    
    Args:
        conn: Database connection
        
    Returns:
        True if a config was deleted, False if none existed
    """
    cursor = conn.execute(
        "DELETE FROM network_data_store WHERE category = 'analytics_view' AND name = 'default'"
    )
    conn.commit()
    return cursor.rowcount > 0
