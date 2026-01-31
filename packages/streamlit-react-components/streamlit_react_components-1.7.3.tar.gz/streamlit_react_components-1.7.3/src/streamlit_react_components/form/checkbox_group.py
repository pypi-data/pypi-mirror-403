"""CheckboxGroup component - A group of checkboxes."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def checkbox_group(
    items: List[Dict[str, Any]],
    label: str = "",
    layout: str = "vertical",
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> List[str]:
    """
    Display a group of checkboxes.

    Args:
        items: List of checkbox items, each with:
               - id: Unique identifier
               - label: Display label
               - checked: Initial checked state (optional, default False)
               - disabled: Whether checkbox is disabled (optional, default False)
        label: Optional group label
        layout: Layout direction - "vertical" (default) or "horizontal"
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Returns:
        List of checked item IDs

    Example:
        # Vertical layout (default)
        selected = checkbox_group(
            label="Parameters",
            items=[
                {"id": "vphp", "label": "VPHP Hold", "checked": True},
                {"id": "lot_co", "label": "Lot C/O", "checked": True},
                {"id": "batch", "label": "Batch Size"},
                {"id": "beta", "label": "Beta Feature", "disabled": True}
            ]
        )
        # Returns: ["vphp", "lot_co"] if those are checked

        # Horizontal layout
        selected = checkbox_group(
            label="Options",
            items=[...],
            layout="horizontal"
        )
    """
    # Get default checked items
    default_checked = [item["id"] for item in items if item.get("checked", False)]

    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    result = _component(
        component="checkbox_group",
        label=label,
        items=items,
        layout=layout,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=default_checked,
    )
    return result if result is not None else default_checked
