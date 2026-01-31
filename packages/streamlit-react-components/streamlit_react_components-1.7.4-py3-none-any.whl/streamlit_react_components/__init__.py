"""
Streamlit React Components

Reusable React-based Streamlit components with Tailwind CSS styling.
"""

from .common import (
    panel,
    section_header,
    stat_card,
    metric_row,
    data_table,
    step_indicator,
    button_group,
    chart_legend,
    plotly_chart,
    smart_chart,
)

from .form import (
    form_select,
    form_slider,
    checkbox_group,
    radio_group,
)

from .tailwind import (
    tw,
    parse_tailwind_classes,
    tailwind_to_css,
    hex_to_rgba,
)

from .styled_container import (
    styled_container,
    css,
)

__version__ = "1.7.4"

__all__ = [
    # Common components
    "panel",
    "section_header",
    "stat_card",
    "metric_row",
    "data_table",
    "step_indicator",
    "button_group",
    "chart_legend",
    "plotly_chart",
    "smart_chart",
    # Form components
    "form_select",
    "form_slider",
    "checkbox_group",
    "radio_group",
    # Tailwind utilities
    "tw",
    "parse_tailwind_classes",
    "tailwind_to_css",
    "hex_to_rgba",
    # Styled container
    "styled_container",
    "css",
]
