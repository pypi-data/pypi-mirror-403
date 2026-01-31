"""FormDateSlider component - A date slider with optional range selection."""

import streamlit.components.v1 as components
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, Any, Optional, Union, Tuple

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


def form_date_slider(
    label: str,
    min_val: date,
    max_val: date,
    value: Union[date, Tuple[date, date]],
    step_type: Optional[str] = "month",
    step: Optional[timedelta] = None,
    format: str = "YYYY-MM",
    color: str = "blue",
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    defer_update: bool = False,
    key: Optional[str] = None,
) -> Union[date, Tuple[date, date]]:
    """
    Display a date slider with single or range selection.

    Args:
        label: Label text for the slider
        min_val: Minimum selectable date
        max_val: Maximum selectable date
        value: Current value - single date or tuple of (start, end) for range mode
        step_type: Step granularity - "month", "quarter", "year", "week", "day", or None
                   When set to a calendar unit, snaps to boundaries (e.g., 1st of month).
                   When "day" or None, uses the `step` timedelta parameter.
        step: Step increment as timedelta (only used when step_type is "day" or None)
              Defaults to timedelta(days=1)
        format: Display format string - "YYYY-MM", "YYYY-MM-DD", "MMM YYYY", etc.
        color: Accent color - preset name or hex value
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
        defer_update: If True, don't trigger Streamlit rerun on change.
        key: Unique key for the component

    Returns:
        Single date if value was a date, or tuple (start, end) if value was a tuple

    Example:
        # Monthly range selection
        start, end = form_date_slider(
            label="Date Range",
            min_val=date(2024, 1, 1),
            max_val=date(2025, 12, 31),
            value=(date(2024, 3, 1), date(2024, 9, 1)),
            step_type="month",
            format="YYYY-MM",
            key="date_range"
        )

        # Single month selection
        selected = form_date_slider(
            label="Select Month",
            min_val=date(2024, 1, 1),
            max_val=date(2025, 12, 31),
            value=date(2024, 6, 1),
            step_type="month",
            format="YYYY-MM",
            key="single_month"
        )

        # Daily stepping with custom interval
        selected = form_date_slider(
            label="Select Date",
            min_val=date(2024, 1, 1),
            max_val=date(2024, 12, 31),
            value=date(2024, 6, 15),
            step_type="day",
            step=timedelta(days=7),  # Weekly steps
            format="YYYY-MM-DD",
            key="weekly_date"
        )
    """
    # Determine if range mode based on value type
    is_range = isinstance(value, (tuple, list))

    # Convert dates to ISO strings
    min_val_str = min_val.isoformat()
    max_val_str = max_val.isoformat()

    if is_range:
        value_data = [value[0].isoformat(), value[1].isoformat()]
        default_data = value_data
    else:
        value_data = value.isoformat()
        default_data = value_data

    # Convert step timedelta to days if provided
    step_days = None
    if step is not None:
        step_days = step.days
    elif step_type in ("day", None):
        step_days = 1  # Default to 1 day

    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    result = _component(
        component="form_date_slider",
        label=label,
        minVal=min_val_str,
        maxVal=max_val_str,
        value=value_data,
        stepType=step_type,
        stepDays=step_days,
        format=format,
        color=color,
        style=style,
        className=class_name,
        theme=resolved_theme,
        deferUpdate=defer_update,
        componentKey=key,
        key=key,
        default=default_data,
    )

    # Parse result back to date objects
    if result is None:
        return value

    if is_range:
        if isinstance(result, (list, tuple)) and len(result) == 2:
            return (date.fromisoformat(result[0]), date.fromisoformat(result[1]))
        return value
    else:
        if isinstance(result, str):
            return date.fromisoformat(result)
        return value
