"""StatCard component - A styled statistics display card."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, Optional, Union

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def stat_card(
    label: str,
    value: Union[str, int, float],
    color: str = "blue",
    icon: str = "",
    planned: Optional[Union[str, int, float]] = None,
    delta: Optional[Union[str, int, float]] = None,
    delta_style: str = "auto",
    delta_thresholds: Optional[Dict[str, float]] = None,
    unit: str = "",
    action: Optional[Dict[str, str]] = None,
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Optional[str]:
    """
    Display a styled statistics card with a label and value.

    Args:
        label: The description label (e.g., "Total Users")
        value: The statistic value to display
        color: Accent color - preset name ("blue", "green", "red", "yellow",
               "purple", "slate") or hex value (e.g., "#94a3b8")
        icon: Optional emoji or icon to display with the label
        planned: Optional planned/target value to display
        delta: Optional delta/difference value to display
        delta_style: How to style the delta - "auto" (green/red based on sign),
                     "neutral" (no color), "percentage" (show as %),
                     "inverse" (red for positive, green for negative)
        delta_thresholds: Optional thresholds for delta color based on magnitude
                          e.g., {"warning": 10, "danger": 20}
        unit: Unit of measurement (e.g., "kg", "%", "$")
        action: Optional action config with keys:
                - id: Unique identifier (returned on click)
                - label: Display text
                - icon: Optional emoji/icon (e.g., "📊")
                - style: "button" (default) or "link"
                - className: Optional Tailwind classes for custom styling
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Returns:
        The action button id if clicked, None otherwise

    Example:
        # Basic usage (backwards compatible)
        stat_card(
            label="Within Threshold",
            value="4",
            color="green",
            style={"minWidth": "150px"}
        )

        # With all new features
        clicked = stat_card(
            label="Production Output",
            value=1234,
            planned=1200,
            delta=34,
            delta_style="auto",
            unit="kg",
            color="green",
            icon="📊",
            action={"id": "details", "label": "View Details"}
        )
        if clicked == "details":
            st.write("Details clicked!")

        # With thresholds
        stat_card(
            label="Defect Rate",
            value=15,
            delta=5,
            delta_style="inverse",
            delta_thresholds={"warning": 3, "danger": 10},
            unit="%"
        )

        # With styled action button
        stat_card(
            label="Revenue",
            value=1234,
            action={
                "id": "view",
                "label": "View Details",
                "icon": "👁️",
                "style": "button",
                "className": "bg-cyan-600 hover:bg-cyan-500"
            }
        )

        # With link-style action
        stat_card(
            label="Orders",
            value=567,
            action={
                "id": "expand",
                "label": "See more",
                "icon": "→",
                "style": "link"
            }
        )
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    return _component(
        component="stat_card",
        label=label,
        value=str(value),
        color=color,
        icon=icon,
        planned=str(planned) if planned is not None else None,
        delta=float(delta) if delta is not None else None,
        deltaStyle=delta_style,
        deltaThresholds=delta_thresholds,
        unit=unit,
        action=action,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
