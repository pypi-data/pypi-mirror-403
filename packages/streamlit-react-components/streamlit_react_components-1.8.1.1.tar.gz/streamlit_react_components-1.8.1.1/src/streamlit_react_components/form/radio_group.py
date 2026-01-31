"""RadioGroup component - A group of radio buttons for single selection."""

import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, List, Optional

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def radio_group(
    items: List[Dict[str, Any]],
    label: str = "",
    layout: str = "vertical",
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    defer_update: bool = False,
    key: Optional[str] = None,
) -> Optional[str]:
    """
    Display a group of radio buttons for single selection.

    Args:
        items: List of radio items, each with:
               - id: Unique identifier
               - label: Display label
               - checked: Initial checked state (optional, default False)
               - disabled: Whether item is disabled (optional, default False)
        label: Optional group label
        layout: Layout direction - "vertical" (default) or "horizontal"
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        defer_update: If True, don't trigger Streamlit rerun on change.
                      Value is stored locally and sent on next rerun (e.g., Apply button).
                      Requires 'key' to be set.
        key: Unique key for the component (required if defer_update=True)

    Returns:
        ID of the selected item (string), or None if nothing selected

    Example:
        selected = radio_group(
            label="Payment Method",
            items=[
                {"id": "credit", "label": "Credit Card", "checked": True},
                {"id": "debit", "label": "Debit Card"},
                {"id": "paypal", "label": "PayPal", "disabled": True}
            ]
        )
        # Returns: "credit" (only one can be selected)

        # Deferred update (no rerun until Apply button clicked)
        selected = radio_group(
            label="Payment Method",
            items=[...],
            defer_update=True,
            key="payment_radio"
        )
        if st.button("Apply"):
            st.rerun()
    """
    # Get default selected item (first checked item)
    default_selected = None
    for item in items:
        if item.get("checked", False):
            default_selected = item["id"]
            break

    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    result = _component(
        component="radio_group",
        label=label,
        items=items,
        layout=layout,
        style=style,
        className=class_name,
        theme=resolved_theme,
        deferUpdate=defer_update,
        componentKey=key,
        key=key,
        default=default_selected,
    )
    return result if result is not None else default_selected
