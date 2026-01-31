"""ButtonGroup component - A group of action buttons."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def button_group(
    buttons: List[Dict[str, Any]],
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Optional[str]:
    """
    Display a group of action buttons.

    Args:
        buttons: List of button configs, each with:
                 - id: Unique identifier
                 - label: Button text (optional)
                 - icon: Button icon/emoji (optional)
                 - color: Preset name ("blue", "green", "red", "yellow", "purple",
                   "slate") or hex value like "#94a3b8" (optional)
                 - disabled: Whether button is disabled (optional)
                 - style: Inline CSS styles dict for this button (optional)
                 - className: Tailwind CSS classes for this button (optional)
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Returns:
        The ID of the clicked button, or None if no click

    Example:
        # Using preset colors
        clicked = button_group(
            buttons=[
                {"id": "view", "icon": "👁️"},
                {"id": "edit", "icon": "✏️"},
                {"id": "approve", "icon": "✓", "color": "green"},
                {"id": "reject", "icon": "✕", "color": "red"}
            ]
        )

        # Using hex colors and custom styling
        clicked = button_group(
            buttons=[
                {"id": "custom", "icon": "🎨", "color": "#ff5733"},
                {"id": "styled", "label": "Styled", "style": {"padding": "12px"}}
            ]
        )
        if clicked == "approve":
            approve_item()
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    return _component(
        component="button_group",
        buttons=buttons,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
