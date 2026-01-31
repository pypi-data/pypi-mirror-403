"""
Theming system for Streamlit React Components.

This module provides a comprehensive theming system that works with both
Streamlit's standard components and custom React components.

Users can:
1. Use pre-defined themes (DEFAULT, OCEAN, FOREST, SUNSET, MONOCHROME)
2. Edit existing theme dictionaries
3. Create custom themes by copying and modifying
4. Apply themes globally via set_theme()
5. Theme both Streamlit standard components and custom React components

Example:
    import streamlit as st
    from streamlit_react_components.themes import set_theme, apply_theme_to_streamlit, OCEAN_THEME

    set_theme(OCEAN_THEME)
    apply_theme_to_streamlit()

    st.title("My Themed App")
    st.button("Themed Button")
"""

from typing import TypedDict, Optional, Dict, Any


# ============================================
# TYPE DEFINITIONS
# ============================================

class ColorPalette(TypedDict):
    """Core color palette for a theme."""
    primary: str
    secondary: str
    success: str
    warning: str
    error: str
    info: str


class BackgroundColors(TypedDict):
    """Background color variations."""
    primary: str
    secondary: str
    tertiary: str
    accent: str


class TextColors(TypedDict):
    """Text color variations."""
    primary: str
    secondary: str
    tertiary: str
    inverse: str


class BorderColors(TypedDict):
    """Border color variations."""
    default: str
    focus: str
    active: str


class InteractiveStates(TypedDict):
    """Colors for interactive states."""
    hover_bg: str
    hover_text: str
    focus_ring: str
    active_bg: str
    disabled_bg: str
    disabled_text: str


class Typography(TypedDict):
    """Typography settings."""
    font_family: str
    font_size_base: str
    font_size_sm: str
    font_size_lg: str
    font_size_xl: str
    font_weight_normal: str
    font_weight_medium: str
    font_weight_semibold: str
    font_weight_bold: str
    line_height: str


class Spacing(TypedDict):
    """Spacing scale."""
    xs: str
    sm: str
    md: str
    lg: str
    xl: str


class BorderRadius(TypedDict):
    """Border radius scale."""
    sm: str
    md: str
    lg: str
    xl: str
    full: str


class Theme(TypedDict):
    """Complete theme definition."""
    name: str
    colors: ColorPalette
    backgrounds: BackgroundColors
    text: TextColors
    borders: BorderColors
    interactive: InteractiveStates
    typography: Typography
    spacing: Spacing
    border_radius: BorderRadius
    use_streamlit_fallback: bool


# ============================================
# PRE-DEFINED THEMES
# ============================================

DEFAULT_THEME: Theme = {
    "name": "Default",
    "colors": {
        "primary": "#3b82f6",      # blue-500
        "secondary": "#8b5cf6",    # purple-500
        "success": "#22c55e",      # green-500
        "warning": "#f59e0b",      # amber-500
        "error": "#ef4444",        # red-500
        "info": "#06b6d4",         # cyan-500
    },
    "backgrounds": {
        "primary": "#0f172a",      # slate-900
        "secondary": "#1e293b",    # slate-800
        "tertiary": "#334155",     # slate-700
        "accent": "#475569",       # slate-600
    },
    "text": {
        "primary": "#f1f5f9",      # slate-100
        "secondary": "#cbd5e1",    # slate-300
        "tertiary": "#94a3b8",     # slate-400
        "inverse": "#0f172a",      # slate-900
    },
    "borders": {
        "default": "#475569",      # slate-600
        "focus": "#3b82f6",        # blue-500
        "active": "#60a5fa",       # blue-400
    },
    "interactive": {
        "hover_bg": "#334155",     # slate-700
        "hover_text": "#f1f5f9",   # slate-100
        "focus_ring": "#3b82f6",   # blue-500
        "active_bg": "#475569",    # slate-600
        "disabled_bg": "#1e293b",  # slate-800
        "disabled_text": "#64748b", # slate-500
    },
    "typography": {
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font_size_base": "14px",
        "font_size_sm": "12px",
        "font_size_lg": "16px",
        "font_size_xl": "20px",
        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_semibold": "600",
        "font_weight_bold": "700",
        "line_height": "1.5",
    },
    "spacing": {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
    },
    "border_radius": {
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "full": "9999px",
    },
    "use_streamlit_fallback": True,
}


OCEAN_THEME: Theme = {
    "name": "Ocean",
    "colors": {
        "primary": "#0ea5e9",      # sky-500
        "secondary": "#06b6d4",    # cyan-500
        "success": "#10b981",      # emerald-500
        "warning": "#f59e0b",      # amber-500
        "error": "#ef4444",        # red-500
        "info": "#0284c7",         # sky-600
    },
    "backgrounds": {
        "primary": "#082f49",      # sky-950
        "secondary": "#0c4a6e",    # sky-900
        "tertiary": "#075985",     # sky-800
        "accent": "#0369a1",       # sky-700
    },
    "text": {
        "primary": "#f0f9ff",      # sky-50
        "secondary": "#e0f2fe",    # sky-100
        "tertiary": "#bae6fd",     # sky-200
        "inverse": "#082f49",      # sky-950
    },
    "borders": {
        "default": "#0369a1",      # sky-700
        "focus": "#0ea5e9",        # sky-500
        "active": "#38bdf8",       # sky-400
    },
    "interactive": {
        "hover_bg": "#075985",     # sky-800
        "hover_text": "#f0f9ff",   # sky-50
        "focus_ring": "#0ea5e9",   # sky-500
        "active_bg": "#0369a1",    # sky-700
        "disabled_bg": "#0c4a6e",  # sky-900
        "disabled_text": "#0c4a6e",# sky-900
    },
    "typography": {
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font_size_base": "14px",
        "font_size_sm": "12px",
        "font_size_lg": "16px",
        "font_size_xl": "20px",
        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_semibold": "600",
        "font_weight_bold": "700",
        "line_height": "1.5",
    },
    "spacing": {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
    },
    "border_radius": {
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "full": "9999px",
    },
    "use_streamlit_fallback": False,
}


FOREST_THEME: Theme = {
    "name": "Forest",
    "colors": {
        "primary": "#22c55e",      # green-500
        "secondary": "#84cc16",    # lime-500
        "success": "#10b981",      # emerald-500
        "warning": "#f59e0b",      # amber-500
        "error": "#ef4444",        # red-500
        "info": "#06b6d4",         # cyan-500
    },
    "backgrounds": {
        "primary": "#052e16",      # green-950
        "secondary": "#14532d",    # green-900
        "tertiary": "#166534",     # green-800
        "accent": "#15803d",       # green-700
    },
    "text": {
        "primary": "#f0fdf4",      # green-50
        "secondary": "#dcfce7",    # green-100
        "tertiary": "#bbf7d0",     # green-200
        "inverse": "#052e16",      # green-950
    },
    "borders": {
        "default": "#15803d",      # green-700
        "focus": "#22c55e",        # green-500
        "active": "#4ade80",       # green-400
    },
    "interactive": {
        "hover_bg": "#166534",     # green-800
        "hover_text": "#f0fdf4",   # green-50
        "focus_ring": "#22c55e",   # green-500
        "active_bg": "#15803d",    # green-700
        "disabled_bg": "#14532d",  # green-900
        "disabled_text": "#166534",# green-800
    },
    "typography": {
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font_size_base": "14px",
        "font_size_sm": "12px",
        "font_size_lg": "16px",
        "font_size_xl": "20px",
        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_semibold": "600",
        "font_weight_bold": "700",
        "line_height": "1.5",
    },
    "spacing": {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
    },
    "border_radius": {
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "full": "9999px",
    },
    "use_streamlit_fallback": False,
}


SUNSET_THEME: Theme = {
    "name": "Sunset",
    "colors": {
        "primary": "#f97316",      # orange-500
        "secondary": "#f59e0b",    # amber-500
        "success": "#22c55e",      # green-500
        "warning": "#eab308",      # yellow-500
        "error": "#ef4444",        # red-500
        "info": "#06b6d4",         # cyan-500
    },
    "backgrounds": {
        "primary": "#431407",      # orange-950
        "secondary": "#7c2d12",    # orange-900
        "tertiary": "#9a3412",     # orange-800
        "accent": "#c2410c",       # orange-700
    },
    "text": {
        "primary": "#fff7ed",      # orange-50
        "secondary": "#ffedd5",    # orange-100
        "tertiary": "#fed7aa",     # orange-200
        "inverse": "#431407",      # orange-950
    },
    "borders": {
        "default": "#c2410c",      # orange-700
        "focus": "#f97316",        # orange-500
        "active": "#fb923c",       # orange-400
    },
    "interactive": {
        "hover_bg": "#9a3412",     # orange-800
        "hover_text": "#fff7ed",   # orange-50
        "focus_ring": "#f97316",   # orange-500
        "active_bg": "#c2410c",    # orange-700
        "disabled_bg": "#7c2d12",  # orange-900
        "disabled_text": "#9a3412",# orange-800
    },
    "typography": {
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font_size_base": "14px",
        "font_size_sm": "12px",
        "font_size_lg": "16px",
        "font_size_xl": "20px",
        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_semibold": "600",
        "font_weight_bold": "700",
        "line_height": "1.5",
    },
    "spacing": {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
    },
    "border_radius": {
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "full": "9999px",
    },
    "use_streamlit_fallback": False,
}


MONOCHROME_THEME: Theme = {
    "name": "Monochrome",
    "colors": {
        "primary": "#71717a",      # zinc-500
        "secondary": "#52525b",    # zinc-600
        "success": "#a1a1aa",      # zinc-400
        "warning": "#71717a",      # zinc-500
        "error": "#3f3f46",        # zinc-700
        "info": "#a1a1aa",         # zinc-400
    },
    "backgrounds": {
        "primary": "#09090b",      # zinc-950
        "secondary": "#18181b",    # zinc-900
        "tertiary": "#27272a",     # zinc-800
        "accent": "#3f3f46",       # zinc-700
    },
    "text": {
        "primary": "#fafafa",      # zinc-50
        "secondary": "#f4f4f5",    # zinc-100
        "tertiary": "#e4e4e7",     # zinc-200
        "inverse": "#09090b",      # zinc-950
    },
    "borders": {
        "default": "#52525b",      # zinc-600
        "focus": "#71717a",        # zinc-500
        "active": "#a1a1aa",       # zinc-400
    },
    "interactive": {
        "hover_bg": "#3f3f46",     # zinc-700
        "hover_text": "#fafafa",   # zinc-50
        "focus_ring": "#71717a",   # zinc-500
        "active_bg": "#52525b",    # zinc-600
        "disabled_bg": "#18181b",  # zinc-900
        "disabled_text": "#3f3f46",# zinc-700
    },
    "typography": {
        "font_family": "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, monospace",
        "font_size_base": "14px",
        "font_size_sm": "12px",
        "font_size_lg": "16px",
        "font_size_xl": "20px",
        "font_weight_normal": "400",
        "font_weight_medium": "500",
        "font_weight_semibold": "600",
        "font_weight_bold": "700",
        "line_height": "1.5",
    },
    "spacing": {
        "xs": "4px",
        "sm": "8px",
        "md": "16px",
        "lg": "24px",
        "xl": "32px",
    },
    "border_radius": {
        "sm": "2px",
        "md": "4px",
        "lg": "6px",
        "xl": "8px",
        "full": "9999px",
    },
    "use_streamlit_fallback": False,
}


# ============================================
# THEME MANAGEMENT
# ============================================

# Global active theme
_active_theme: Optional[Theme] = None


def set_theme(theme: Theme) -> None:
    """
    Set the active theme for all components.

    Args:
        theme: Theme dictionary to set as active

    Example:
        from streamlit_react_components.themes import set_theme, OCEAN_THEME
        set_theme(OCEAN_THEME)
    """
    global _active_theme
    _active_theme = theme


def get_active_theme() -> Theme:
    """
    Get the currently active theme.

    Returns:
        The active theme, or DEFAULT_THEME if no theme is set

    Example:
        theme = get_active_theme()
        primary_color = theme['colors']['primary']
    """
    return _active_theme or DEFAULT_THEME


def get_theme_by_name(name: str) -> Optional[Theme]:
    """
    Get a pre-defined theme by name.

    Args:
        name: Theme name (case-insensitive): "default", "ocean", "forest", "sunset", "monochrome"

    Returns:
        Theme dictionary if found, None otherwise

    Example:
        theme = get_theme_by_name("ocean")
        if theme:
            set_theme(theme)
    """
    themes = {
        "default": DEFAULT_THEME,
        "ocean": OCEAN_THEME,
        "forest": FOREST_THEME,
        "sunset": SUNSET_THEME,
        "monochrome": MONOCHROME_THEME,
    }
    return themes.get(name.lower())


# ============================================
# CSS GENERATION FOR STREAMLIT COMPONENTS
# ============================================

def generate_streamlit_css(theme: Theme) -> str:
    """
    Generate CSS to override Streamlit's standard component styles.
    This CSS themes 47+ Streamlit components including buttons, inputs,
    metrics, alerts, charts, and more.

    Args:
        theme: Theme dictionary containing all theme settings

    Returns:
        CSS string wrapped in <style> tags, ready for st.markdown()

    Note:
        This function generates ~500 lines of CSS targeting Streamlit's
        internal CSS classes. It uses CSS specificity to override defaults
        while allowing user customization.
    """
    return f"""
    <style>
    /* ============================================
       STREAMLIT THEMING SYSTEM
       Generated CSS for {theme['name']} theme
       ============================================ */

    /* Global Page Styles */
    .stApp {{
        background-color: {theme['backgrounds']['primary']};
        color: {theme['text']['primary']};
        font-family: {theme['typography']['font_family']};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {theme['backgrounds']['secondary']};
    }}

    [data-testid="stSidebar"] .stMarkdown {{
        color: {theme['text']['primary']};
    }}

    /* ============================================
       BUTTONS
       ============================================ */

    /* Primary Button (st.button) */
    .stButton > button {{
        background-color: {theme['colors']['primary']};
        color: {theme['text']['inverse']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
        font-family: {theme['typography']['font_family']};
        font-weight: {theme['typography']['font_weight_medium']};
        transition: all 0.2s;
    }}

    .stButton > button:hover {{
        background-color: {theme['interactive']['hover_bg']};
        color: {theme['interactive']['hover_text']};
        border-color: {theme['borders']['focus']};
    }}

    .stButton > button:active {{
        background-color: {theme['interactive']['active_bg']};
    }}

    .stButton > button:focus {{
        outline: 2px solid {theme['interactive']['focus_ring']};
        outline-offset: 2px;
    }}

    .stButton > button:disabled {{
        background-color: {theme['interactive']['disabled_bg']};
        color: {theme['interactive']['disabled_text']};
        cursor: not-allowed;
        opacity: 0.6;
    }}

    /* Download Button (st.download_button) */
    .stDownloadButton > button {{
        background-color: {theme['colors']['secondary']};
        color: {theme['text']['inverse']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stDownloadButton > button:hover {{
        background-color: {theme['interactive']['hover_bg']};
    }}

    /* ============================================
       TEXT INPUTS
       ============================================ */

    /* Text Input (st.text_input) */
    .stTextInput > div > div > input {{
        background-color: {theme['backgrounds']['secondary']};
        color: {theme['text']['primary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
        font-family: {theme['typography']['font_family']};
        padding: {theme['spacing']['sm']};
    }}

    .stTextInput > div > div > input:focus {{
        border-color: {theme['borders']['focus']};
        outline: 2px solid {theme['interactive']['focus_ring']};
        outline-offset: 0px;
    }}

    .stTextInput > div > div > input::placeholder {{
        color: {theme['text']['tertiary']};
    }}

    .stTextInput > label {{
        color: {theme['text']['secondary']};
        font-size: {theme['typography']['font_size_sm']};
        font-weight: {theme['typography']['font_weight_medium']};
    }}

    /* Text Area (st.text_area) */
    .stTextArea > div > div > textarea {{
        background-color: {theme['backgrounds']['secondary']};
        color: {theme['text']['primary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
        font-family: {theme['typography']['font_family']};
    }}

    .stTextArea > div > div > textarea:focus {{
        border-color: {theme['borders']['focus']};
        outline: 2px solid {theme['interactive']['focus_ring']};
    }}

    .stTextArea > label {{
        color: {theme['text']['secondary']};
        font-size: {theme['typography']['font_size_sm']};
    }}

    /* Number Input (st.number_input) */
    .stNumberInput > div > div > input {{
        background-color: {theme['backgrounds']['secondary']};
        color: {theme['text']['primary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stNumberInput > div > div > input:focus {{
        border-color: {theme['borders']['focus']};
        outline: 2px solid {theme['interactive']['focus_ring']};
    }}

    /* Number input buttons */
    .stNumberInput button {{
        background-color: {theme['backgrounds']['tertiary']};
        color: {theme['text']['secondary']};
        border-color: {theme['borders']['default']};
    }}

    .stNumberInput button:hover {{
        background-color: {theme['interactive']['hover_bg']};
    }}

    /* ============================================
       SELECT WIDGETS
       ============================================ */

    /* Selectbox (st.selectbox) */
    .stSelectbox > div > div {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stSelectbox > div > div:focus-within {{
        border-color: {theme['borders']['focus']};
        outline: 2px solid {theme['interactive']['focus_ring']};
    }}

    .stSelectbox > label {{
        color: {theme['text']['secondary']};
        font-size: {theme['typography']['font_size_sm']};
    }}

    .stSelectbox [data-baseweb="select"] {{
        background-color: {theme['backgrounds']['secondary']};
    }}

    .stSelectbox [data-baseweb="select"] > div {{
        background-color: {theme['backgrounds']['secondary']};
        color: {theme['text']['primary']};
    }}

    /* Dropdown menu */
    [data-baseweb="menu"] {{
        background-color: {theme['backgrounds']['tertiary']};
        border: 1px solid {theme['borders']['default']};
    }}

    [data-baseweb="menu"] li {{
        background-color: {theme['backgrounds']['tertiary']};
        color: {theme['text']['primary']};
    }}

    [data-baseweb="menu"] li:hover {{
        background-color: {theme['interactive']['hover_bg']};
        color: {theme['interactive']['hover_text']};
    }}

    /* Multiselect (st.multiselect) */
    .stMultiSelect > div > div {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {theme['colors']['primary']};
        color: {theme['text']['inverse']};
    }}

    /* Radio (st.radio) */
    .stRadio > label {{
        color: {theme['text']['secondary']};
        font-size: {theme['typography']['font_size_sm']};
    }}

    .stRadio > div {{
        color: {theme['text']['primary']};
    }}

    .stRadio [role="radiogroup"] label {{
        color: {theme['text']['primary']};
    }}

    .stRadio input[type="radio"]:checked + div {{
        background-color: {theme['colors']['primary']};
    }}

    .stRadio input[type="radio"]:focus + div {{
        outline: 2px solid {theme['interactive']['focus_ring']};
    }}

    /* Checkbox (st.checkbox) */
    .stCheckbox > label {{
        color: {theme['text']['primary']};
    }}

    .stCheckbox input[type="checkbox"] {{
        accent-color: {theme['colors']['primary']};
    }}

    .stCheckbox input[type="checkbox"]:focus {{
        outline: 2px solid {theme['interactive']['focus_ring']};
    }}

    /* Toggle (st.toggle) */
    .stToggle > label {{
        color: {theme['text']['secondary']};
    }}

    .stToggle input:checked + div {{
        background-color: {theme['colors']['primary']};
    }}

    /* ============================================
       SLIDERS
       ============================================ */

    /* Slider (st.slider) */
    .stSlider > label {{
        color: {theme['text']['secondary']};
        font-size: {theme['typography']['font_size_sm']};
    }}

    .stSlider [data-baseweb="slider"] {{
        color: {theme['text']['primary']};
    }}

    .stSlider [role="slider"] {{
        background-color: {theme['colors']['primary']};
    }}

    .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] > div {{
        background-color: {theme['colors']['primary']};
    }}

    .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {{
        color: {theme['text']['primary']};
    }}

    /* ============================================
       DATE & TIME PICKERS
       ============================================ */

    /* Date Input (st.date_input) */
    .stDateInput > label {{
        color: {theme['text']['secondary']};
        font-size: {theme['typography']['font_size_sm']};
    }}

    .stDateInput > div > div {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stDateInput input {{
        color: {theme['text']['primary']};
    }}

    /* Time Input (st.time_input) */
    .stTimeInput > label {{
        color: {theme['text']['secondary']};
    }}

    .stTimeInput > div > div {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
    }}

    /* ============================================
       FILE UPLOADER
       ============================================ */

    .stFileUploader > label {{
        color: {theme['text']['secondary']};
    }}

    .stFileUploader section {{
        background-color: {theme['backgrounds']['secondary']};
        border: 2px dashed {theme['borders']['default']};
        border-radius: {theme['border_radius']['lg']};
    }}

    .stFileUploader section:hover {{
        border-color: {theme['borders']['focus']};
    }}

    .stFileUploader button {{
        background-color: {theme['colors']['primary']};
        color: {theme['text']['inverse']};
    }}

    /* ============================================
       COLOR PICKER
       ============================================ */

    .stColorPicker > label {{
        color: {theme['text']['secondary']};
    }}

    .stColorPicker > div > div {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
    }}

    /* ============================================
       METRICS (st.metric)
       ============================================ */

    [data-testid="stMetric"] {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['lg']};
        padding: {theme['spacing']['md']};
    }}

    [data-testid="stMetricLabel"] {{
        color: {theme['text']['secondary']};
        font-size: {theme['typography']['font_size_sm']};
    }}

    [data-testid="stMetricValue"] {{
        color: {theme['text']['primary']};
        font-size: {theme['typography']['font_size_xl']};
        font-weight: {theme['typography']['font_weight_bold']};
    }}

    [data-testid="stMetricDelta"] {{
        font-size: {theme['typography']['font_size_sm']};
    }}

    /* Positive delta */
    [data-testid="stMetricDelta"] svg[fill="currentColor"]:first-child {{
        color: {theme['colors']['success']};
    }}

    /* Negative delta */
    [data-testid="stMetricDelta"] svg[fill="currentColor"]:last-child {{
        color: {theme['colors']['error']};
    }}

    /* ============================================
       ALERTS & NOTIFICATIONS
       ============================================ */

    /* Info (st.info) */
    .stAlert[data-baseweb="notification"][kind="info"] {{
        background-color: {theme['colors']['info']}20;
        border-left: 4px solid {theme['colors']['info']};
        color: {theme['text']['primary']};
    }}

    /* Success (st.success) */
    .stAlert[data-baseweb="notification"][kind="success"] {{
        background-color: {theme['colors']['success']}20;
        border-left: 4px solid {theme['colors']['success']};
        color: {theme['text']['primary']};
    }}

    /* Warning (st.warning) */
    .stAlert[data-baseweb="notification"][kind="warning"] {{
        background-color: {theme['colors']['warning']}20;
        border-left: 4px solid {theme['colors']['warning']};
        color: {theme['text']['primary']};
    }}

    /* Error (st.error) */
    .stAlert[data-baseweb="notification"][kind="error"] {{
        background-color: {theme['colors']['error']}20;
        border-left: 4px solid {theme['colors']['error']};
        color: {theme['text']['primary']};
    }}

    /* ============================================
       LAYOUT CONTAINERS
       ============================================ */

    /* Expander (st.expander) */
    .stExpander {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stExpander summary {{
        color: {theme['text']['primary']};
        font-weight: {theme['typography']['font_weight_medium']};
    }}

    .stExpander summary:hover {{
        background-color: {theme['interactive']['hover_bg']};
    }}

    /* Tabs (st.tabs) */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {theme['backgrounds']['secondary']};
        border-bottom: 1px solid {theme['borders']['default']};
    }}

    .stTabs [data-baseweb="tab"] {{
        color: {theme['text']['secondary']};
        border-color: transparent;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        color: {theme['text']['primary']};
        background-color: {theme['interactive']['hover_bg']};
    }}

    .stTabs [aria-selected="true"] {{
        color: {theme['colors']['primary']};
        border-bottom-color: {theme['colors']['primary']};
    }}

    /* Columns */
    [data-testid="column"] {{
        background-color: transparent;
    }}

    /* ============================================
       DATA DISPLAY
       ============================================ */

    /* DataFrame (st.dataframe) */
    .stDataFrame {{
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stDataFrame [data-testid="stDataFrameResizable"] {{
        background-color: {theme['backgrounds']['secondary']};
    }}

    /* Table headers */
    .stDataFrame thead th {{
        background-color: {theme['backgrounds']['tertiary']};
        color: {theme['text']['primary']};
        border-bottom: 2px solid {theme['borders']['default']};
        font-weight: {theme['typography']['font_weight_semibold']};
    }}

    /* Table rows */
    .stDataFrame tbody td {{
        background-color: {theme['backgrounds']['secondary']};
        color: {theme['text']['primary']};
        border-bottom: 1px solid {theme['borders']['default']};
    }}

    .stDataFrame tbody tr:hover td {{
        background-color: {theme['interactive']['hover_bg']};
    }}

    /* JSON (st.json) */
    .stJson {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
        color: {theme['text']['primary']};
    }}

    /* Code (st.code) */
    .stCodeBlock {{
        background-color: {theme['backgrounds']['secondary']};
        border: 1px solid {theme['borders']['default']};
        border-radius: {theme['border_radius']['md']};
    }}

    .stCodeBlock code {{
        color: {theme['text']['primary']};
        font-family: {theme['typography']['font_family']};
    }}

    /* ============================================
       CHARTS
       ============================================ */

    /* All Streamlit charts */
    .stVegaLiteChart, .stArrowVegaLiteChart {{
        background-color: {theme['backgrounds']['secondary']};
        border-radius: {theme['border_radius']['md']};
    }}

    /* ============================================
       PROGRESS & SPINNERS
       ============================================ */

    /* Progress Bar (st.progress) */
    .stProgress > div > div {{
        background-color: {theme['backgrounds']['tertiary']};
    }}

    .stProgress > div > div > div {{
        background-color: {theme['colors']['primary']};
    }}

    /* Spinner (st.spinner) */
    .stSpinner > div {{
        border-color: {theme['colors']['primary']};
    }}

    /* ============================================
       MARKDOWN & TEXT
       ============================================ */

    .stMarkdown {{
        color: {theme['text']['primary']};
        font-family: {theme['typography']['font_family']};
    }}

    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {theme['text']['primary']};
        font-weight: {theme['typography']['font_weight_bold']};
    }}

    .stMarkdown a {{
        color: {theme['colors']['primary']};
    }}

    .stMarkdown a:hover {{
        color: {theme['colors']['secondary']};
    }}

    .stMarkdown code {{
        background-color: {theme['backgrounds']['tertiary']};
        color: {theme['colors']['secondary']};
        border-radius: {theme['border_radius']['sm']};
        padding: 2px 4px;
    }}

    /* Title (st.title) */
    .stTitle {{
        color: {theme['text']['primary']};
        font-weight: {theme['typography']['font_weight_bold']};
    }}

    /* Header (st.header) */
    .stHeader {{
        color: {theme['text']['primary']};
        font-weight: {theme['typography']['font_weight_semibold']};
    }}

    /* Subheader (st.subheader) */
    .stSubheader {{
        color: {theme['text']['secondary']};
        font-weight: {theme['typography']['font_weight_medium']};
    }}

    /* Caption (st.caption) */
    .stCaption {{
        color: {theme['text']['tertiary']};
        font-size: {theme['typography']['font_size_sm']};
    }}

    /* ============================================
       MEDIA
       ============================================ */

    /* Image (st.image) */
    .stImage {{
        border-radius: {theme['border_radius']['md']};
    }}

    /* Video (st.video) */
    .stVideo {{
        border-radius: {theme['border_radius']['md']};
    }}

    /* ============================================
       CHAT
       ============================================ */

    /* Chat message (st.chat_message) */
    .stChatMessage {{
        background-color: {theme['backgrounds']['secondary']};
        border-radius: {theme['border_radius']['lg']};
        border: 1px solid {theme['borders']['default']};
    }}

    .stChatMessage [data-testid="chatAvatarIcon"] {{
        background-color: {theme['colors']['primary']};
    }}

    /* Chat input (st.chat_input) */
    .stChatInput > div > div > input {{
        background-color: {theme['backgrounds']['secondary']};
        color: {theme['text']['primary']};
        border: 1px solid {theme['borders']['default']};
    }}

    /* ============================================
       SCROLLBARS
       ============================================ */

    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: {theme['backgrounds']['secondary']};
    }}

    ::-webkit-scrollbar-thumb {{
        background: {theme['backgrounds']['accent']};
        border-radius: {theme['border_radius']['full']};
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: {theme['borders']['default']};
    }}

    </style>
    """


def apply_theme_to_streamlit(theme: Optional[Theme] = None) -> None:
    """
    Apply theme to Streamlit standard components via CSS injection.
    Call this at the top of your Streamlit app.

    Args:
        theme: Theme to apply. If None, uses active global theme.

    Example:
        import streamlit as st
        from streamlit_react_components.themes import set_theme, apply_theme_to_streamlit, OCEAN_THEME

        set_theme(OCEAN_THEME)
        apply_theme_to_streamlit()

        st.title("My App")
        st.button("Click me")  # Now themed!
    """
    import streamlit as st

    resolved_theme = theme if theme is not None else get_active_theme()
    css = generate_streamlit_css(resolved_theme)
    st.markdown(css, unsafe_allow_html=True)
