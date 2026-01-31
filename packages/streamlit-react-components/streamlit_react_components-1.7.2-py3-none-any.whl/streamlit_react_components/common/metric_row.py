"""MetricRow component - A key-value display row."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def metric_row(
    label: str,
    value: str,
    value_color: str = "",
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> None:
    """
    Display a key-value metric row.

    Args:
        label: The metric label (left side)
        value: The metric value (right side)
        value_color: Tailwind text color class for the value (e.g., "text-green-400")
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Example:
        metric_row(label="Mean", value="78.4%")
        metric_row(label="Trend", value="↑ +0.4%/mo", value_color="text-green-400")
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    _component(
        component="metric_row",
        label=label,
        value=value,
        valueColor=value_color,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
