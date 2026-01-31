"""FormSlider component - A styled range slider input."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def form_slider(
    label: str,
    value: float,
    min_val: float,
    max_val: float,
    step: float = 1,
    unit: str = "",
    color: str = "blue",
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    defer_update: bool = False,
    key: Optional[str] = None,
) -> float:
    """
    Display a styled range slider input.

    Args:
        label: Label text for the slider
        value: Current value
        min_val: Minimum value
        max_val: Maximum value
        step: Step increment (default 1)
        unit: Unit suffix to display (e.g., "%", "hrs")
        color: Accent color - preset name ("blue", "green", "red", "yellow",
               "purple", "slate") or hex value (e.g., "#94a3b8")
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        defer_update: If True, don't trigger Streamlit rerun on change.
                      Value is stored locally and sent on next rerun (e.g., Apply button).
                      Requires 'key' to be set.
        key: Unique key for the component (required if defer_update=True)

    Returns:
        The current slider value

    Example:
        # Using preset color
        threshold = form_slider(
            label="Upper Threshold",
            value=90,
            min_val=75,
            max_val=100,
            unit="%",
            color="red"
        )

        # Using hex color
        threshold = form_slider(
            label="Custom Slider",
            value=50,
            min_val=0,
            max_val=100,
            color="#ff5733"
        )

        # Deferred update (no rerun until Apply button clicked)
        threshold = form_slider(
            label="Threshold",
            value=50,
            min_val=0,
            max_val=100,
            defer_update=True,
            key="threshold_slider"
        )
        if st.button("Apply"):
            st.rerun()
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    result = _component(
        component="form_slider",
        label=label,
        value=value,
        minVal=min_val,
        maxVal=max_val,
        step=step,
        unit=unit,
        color=color,
        style=style,
        className=class_name,
        theme=resolved_theme,
        deferUpdate=defer_update,
        componentKey=key,
        key=key,
        default=value,
    )
    return float(result) if result is not None else value
