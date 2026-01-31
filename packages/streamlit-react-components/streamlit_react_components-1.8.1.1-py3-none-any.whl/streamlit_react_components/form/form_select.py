"""FormSelect component - A styled dropdown select input."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def form_select(
    label: str,
    options: List[Union[str, Dict[str, str]]],
    value: str = "",
    groups: Optional[List[Dict[str, Any]]] = None,
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    defer_update: bool = False,
    key: Optional[str] = None,
) -> str:
    """
    Display a styled dropdown select input.

    Args:
        label: Label text for the select
        options: List of options, either strings or dicts with {value, label}
        value: Currently selected value
        groups: Optional list of option groups, each with:
                - label: Group header text
                - options: List of options in this group
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        defer_update: If True, don't trigger Streamlit rerun on change.
                      Value is stored locally and sent on next rerun (e.g., Apply button).
                      Requires 'key' to be set.
        key: Unique key for the component (required if defer_update=True)

    Returns:
        The currently selected value

    Example:
        # Simple string options
        site = form_select(
            label="Site",
            options=["AML_14", "ADL", "Devens"],
            value="AML_14"
        )

        # With option groups
        version = form_select(
            label="Base On",
            groups=[
                {"label": "Baselines", "options": ["Baseline v7"]},
                {"label": "Scenarios", "options": ["Q2 Demand Surge"]}
            ]
        )

        # Deferred update (no rerun until Apply button clicked)
        site = form_select(
            label="Site",
            options=["AML_14", "ADL", "Devens"],
            defer_update=True,
            key="site_select"
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
        component="form_select",
        label=label,
        options=options,
        value=value,
        groups=groups,
        style=style,
        className=class_name,
        theme=resolved_theme,
        deferUpdate=defer_update,
        componentKey=key,
        key=key,
        default=value,
    )
    return result if result is not None else value
