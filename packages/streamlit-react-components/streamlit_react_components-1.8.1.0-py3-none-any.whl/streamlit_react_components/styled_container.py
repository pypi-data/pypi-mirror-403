"""
Styled container component for wrapping native Streamlit components with Tailwind styling.

This module provides a context manager that enables Tailwind CSS-like styling
for native Streamlit components (st.slider, st.button, st.text_input, etc.).

Supports:
- All Tailwind utility classes
- Opacity modifiers (bg-blue-500/50)
- Hover, focus, and active variants
- Transitions and animations
"""

from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
import uuid

import streamlit as st

from .tailwind import parse_tailwind_classes


@contextmanager
def styled_container(
    *classes: str,
    style: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Generator[None, None, None]:
    """
    Context manager for styling native Streamlit components with Tailwind classes.

    Wraps Streamlit components in a styled container with support for Tailwind CSS
    utility classes, including hover:, focus:, and active: variants.

    Args:
        *classes: Tailwind CSS class names (e.g., "bg-slate-800", "hover:bg-slate-700")
        style: Optional dict of additional inline CSS properties to merge
        key: Optional unique key for the container (auto-generated if not provided)

    Yields:
        None - use as a context manager with 'with' statement

    Example:
        Basic usage with Tailwind classes::

            with styled_container("bg-slate-800", "border", "border-blue-500", "rounded-xl", "p-4"):
                st.slider("Risk Threshold", 0, 100, 75)
                st.button("Apply")

        With hover and focus states::

            with styled_container(
                "bg-slate-800",
                "border-2",
                "border-slate-600",
                "rounded-xl",
                "p-6",
                "transition-all",
                "duration-200",
                "hover:bg-slate-700",
                "hover:border-blue-500",
                "focus:border-blue-400"
            ):
                st.text_input("Username")
                st.text_input("Password", type="password")
                st.button("Login")

        With opacity modifiers::

            with styled_container(
                "bg-rose-500/20",
                "border",
                "border-rose-500/50",
                "rounded-lg",
                "p-4"
            ):
                st.write("Rose-tinted container")

        With gradient backgrounds::

            with styled_container(
                "bg-gradient-to-br",
                "from-slate-800",
                "to-slate-900",
                "rounded-2xl",
                "p-6"
            ):
                st.metric("Revenue", "$12,450", "+8.2%")

        With custom inline styles::

            with styled_container(
                "bg-slate-800",
                "rounded-lg",
                style={"min-height": "200px", "box-shadow": "0 0 20px rgba(59,130,246,0.3)"}
            ):
                st.write("Custom styled container")

    Note:
        - The focus: variant uses :focus-within, which triggers when any child
          element (like an input) receives focus
        - Transitions work with hover/focus states for smooth animations
        - Gradient classes (from-, to-, via-) work with bg-gradient-to-* classes
    """
    # Generate unique container ID
    container_id = key or f"stc-{uuid.uuid4().hex[:8]}"

    # Parse classes into categorized CSS dicts
    parsed = parse_tailwind_classes(classes)

    # Merge with custom style dict
    if style:
        parsed["base"].update(style)

    # Build CSS rules for each state
    css_blocks = []

    # Use a more specific selector that targets the container's parent block
    selector = f'[data-testid="stVerticalBlock"]:has(> [data-stc-id="{container_id}"])'

    # Base styles
    if parsed["base"]:
        base_css = "; ".join(f"{k}: {v}" for k, v in parsed["base"].items())
        css_blocks.append(f"{selector} {{ {base_css} }}")

    # Hover styles
    if parsed["hover"]:
        hover_css = "; ".join(f"{k}: {v}" for k, v in parsed["hover"].items())
        css_blocks.append(f"{selector}:hover {{ {hover_css} }}")

    # Focus styles (uses :focus-within for child focus)
    if parsed["focus"]:
        focus_css = "; ".join(f"{k}: {v}" for k, v in parsed["focus"].items())
        css_blocks.append(f"{selector}:focus-within {{ {focus_css} }}")

    # Active styles
    if parsed["active"]:
        active_css = "; ".join(f"{k}: {v}" for k, v in parsed["active"].items())
        css_blocks.append(f"{selector}:active {{ {active_css} }}")

    # Inject CSS and marker element
    css_content = "\n        ".join(css_blocks)
    st.markdown(
        f"""
        <style>
        {css_content}
        </style>
        <div data-stc-id="{container_id}" style="display:none;"></div>
        """,
        unsafe_allow_html=True,
    )

    yield


# Convenience function for inline style conversion
def css(*classes: str, **extra_styles: str) -> str:
    """
    Convert Tailwind classes to an inline CSS string.

    Useful for applying Tailwind-like styles to st.markdown HTML content.

    Args:
        *classes: Tailwind CSS class names
        **extra_styles: Additional CSS properties as keyword arguments

    Returns:
        CSS string suitable for inline style attribute

    Example:
        >>> css("bg-slate-800", "p-4", "rounded-lg")
        'background-color: #1e293b; padding: 1rem; border-radius: 0.5rem'

        >>> css("text-blue-500", font_size="20px")
        'color: #3b82f6; font-size: 20px'

        With st.markdown::

            st.markdown(
                f'<div style="{css("bg-slate-800", "p-4", "rounded-lg")}">Content</div>',
                unsafe_allow_html=True
            )
    """
    from .tailwind import tw

    styles = tw(*classes)

    # Add extra styles (convert underscores to hyphens)
    for key, value in extra_styles.items():
        css_key = key.replace("_", "-")
        styles[css_key] = value

    return "; ".join(f"{k}: {v}" for k, v in styles.items())
