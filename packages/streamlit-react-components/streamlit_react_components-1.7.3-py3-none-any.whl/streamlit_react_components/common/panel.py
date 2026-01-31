"""Panel component - A styled container wrapper."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def panel(
    children: str = "",
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> None:
    """
    Display a styled panel/card container.

    Args:
        children: HTML content to render inside the panel
        style: Inline CSS styles as a dictionary (e.g., {"background": "#1e293b"})
        class_name: Tailwind CSS classes (e.g., "bg-slate-900 p-4")
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Example:
        panel(
            children="<h3>Title</h3><p>Content here</p>",
            class_name="mt-4"
        )
    """
    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    _component(
        component="panel",
        children=children,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )
