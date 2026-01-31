"""DataTable component - A styled data table with click support."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def data_table(
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    show_header: bool = True,
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Display a styled data table with row click support.

    Args:
        columns: List of column definitions, each with:
                 - key: Data key in each row
                 - label: Column header text
                 - align: "left", "center", or "right" (optional)
                 - format: "number" or "percent" (optional)
                 - colorByValue: True to color based on status values (optional)
        rows: List of row data dictionaries
        show_header: Whether to show the header row (default True)
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Returns:
        Dictionary with rowIndex and rowData when a row is clicked, None otherwise

    Example:
        columns = [
            {"key": "site", "label": "Site"},
            {"key": "util", "label": "Utilization", "align": "right", "format": "percent"},
            {"key": "status", "label": "Status", "colorByValue": True}
        ]
        rows = [
            {"site": "AML_14", "util": 94, "status": "above"},
            {"site": "ADL", "util": 72, "status": "within"}
        ]
        clicked = data_table(columns=columns, rows=rows)
        if clicked:
            st.write(f"Clicked row: {clicked['rowData']}")
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    return _component(
        component="data_table",
        columns=columns,
        rows=rows,
        showHeader=show_header,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
