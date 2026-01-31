"""SectionHeader component - A styled section title with optional actions."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def section_header(
    title: str,
    icon: str = "",
    actions: Optional[List[Dict[str, Any]]] = None,
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Optional[str]:
    """
    Display a section header with optional action buttons.

    Args:
        title: The header title text
        icon: Optional emoji or icon to display before the title
        actions: List of action button configs, each with:
                 - id: Unique identifier for the action
                 - label: Button text (optional)
                 - icon: Button icon (optional)
                 - color: Preset name ("blue", "green", "red", "yellow", "purple",
                   "slate") or hex value like "#94a3b8" (optional)
                 - style: Inline CSS styles dict for this button (optional)
                 - className: Tailwind CSS classes for this button (optional)
                 - href: URL for link actions. External URLs (http/https) open
                   in a new tab. Internal paths return the ID for use with
                   st.switch_page() (optional)
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Returns:
        The ID of the clicked action button, or None if no click

    Example:
        # Using preset colors
        clicked = section_header(
            title="Dashboard",
            icon="📊",
            actions=[{"id": "refresh", "label": "Refresh", "color": "blue"}]
        )

        # Using hex colors and custom styling
        clicked = section_header(
            title="Dashboard",
            actions=[
                {"id": "custom", "label": "Custom", "color": "#94a3b8"},
                {"id": "styled", "label": "Styled", "style": {"padding": "12px"}}
            ]
        )

        # External link (opens in new tab)
        clicked = section_header(
            title="Resources",
            actions=[
                {"id": "docs", "label": "Documentation", "href": "https://docs.example.com", "icon": "📚"}
            ]
        )

        # Internal navigation
        clicked = section_header(
            title="Settings",
            actions=[{"id": "home", "label": "Home", "icon": "🏠"}]
        )
        if clicked == "home":
            st.switch_page("pages/home.py")
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    return _component(
        component="section_header",
        title=title,
        icon=icon,
        actions=actions or [],
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
