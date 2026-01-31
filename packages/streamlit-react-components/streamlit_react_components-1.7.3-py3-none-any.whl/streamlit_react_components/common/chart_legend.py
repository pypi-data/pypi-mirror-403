"""ChartLegend component - A chart legend with colored indicators."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def chart_legend(
    items: List[Dict[str, str]],
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> None:
    """
    Display a chart legend with colored indicators.

    Args:
        items: List of legend items, each with:
               - color: CSS color value (e.g., "#3b82f6", "rgb(59,130,246)")
               - label: Legend label text
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Example:
        chart_legend(
            items=[
                {"color": "#94a3b8", "label": "Historical"},
                {"color": "#ef4444", "label": "Outlier"},
                {"color": "#8b5cf6", "label": "Prophet"},
                {"color": "#10b981", "label": "ARIMA"}
            ]
        )
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    _component(
        component="chart_legend",
        items=items,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
