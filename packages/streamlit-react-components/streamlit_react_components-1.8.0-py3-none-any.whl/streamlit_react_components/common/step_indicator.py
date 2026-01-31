"""StepIndicator component - A multi-step wizard progress indicator."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def step_indicator(
    steps: List[str],
    current_step: int,
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Optional[int]:
    """
    Display a multi-step wizard progress indicator.

    Args:
        steps: List of step labels (e.g., ["Supply Plan", "Levers", "Review"])
        current_step: Current active step (1-indexed)
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Returns:
        The step number that was clicked, or None if no click

    Example:
        step = step_indicator(
            steps=["Supply Plan", "Levers", "Review"],
            current_step=2
        )
        if step:
            st.session_state.step = step
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    return _component(
        component="step_indicator",
        steps=steps,
        currentStep=current_step,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
