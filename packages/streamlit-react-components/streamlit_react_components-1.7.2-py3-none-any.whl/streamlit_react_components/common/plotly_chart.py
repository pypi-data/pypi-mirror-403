"""PlotlyChart component - Render Plotly charts with full interactivity."""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

_FRONTEND_DIR = Path(__file__).parent.parent / "_frontend"

_component = components.declare_component(
    "streamlit_react_components",
    path=str(_FRONTEND_DIR),
)


# Global key for expanded chart dialog - only ONE dialog can be open at a time
_EXPANDED_DIALOG_KEY = "_plotly_expanded_chart_dialog"
_PROCESSED_EXPAND_KEY = "_plotly_processed_expand_ts"


def _maybe_render_expanded_dialog() -> None:
    """Check if an expanded chart dialog should be rendered. Call at start of plotly_chart()."""
    import plotly.graph_objects as go

    if _EXPANDED_DIALOG_KEY not in st.session_state:
        return

    dialog_data = st.session_state[_EXPANDED_DIALOG_KEY]
    if not dialog_data.get("open"):
        return

    # Clear the flag IMMEDIATELY to prevent re-rendering on subsequent plotly_chart calls
    st.session_state[_EXPANDED_DIALOG_KEY] = {"open": False}

    figure_dict = dialog_data["figure"]
    title = dialog_data.get("title", "")

    @st.dialog(title or "Chart View", width="large")
    def _expanded_dialog():
        fig = go.Figure(figure_dict)
        st.plotly_chart(fig, width="stretch", key="_expanded_plotly_chart")

    _expanded_dialog()


def _dataframe_to_figure(
    data: Any,
    x: Optional[str],
    y: Optional[Union[str, List[str]]],
    color: Optional[str],
    chart_type: str,
    title: Optional[str],
) -> Dict[str, Any]:
    """Convert a DataFrame to a Plotly figure dict."""
    traces = []
    layout: Dict[str, Any] = {}

    if title:
        layout["title"] = title

    # Determine y columns
    y_cols = [y] if isinstance(y, str) else (y or [])

    # Color grouping
    if color and color in data.columns:
        groups = data[color].unique()
        for group in groups:
            group_data = data[data[color] == group]
            for y_col in y_cols:
                trace = _create_trace(
                    chart_type,
                    group_data[x].tolist() if x else list(range(len(group_data))),
                    group_data[y_col].tolist(),
                    f"{group}" if len(y_cols) == 1 else f"{group} - {y_col}",
                )
                traces.append(trace)
    else:
        # No color grouping
        x_data = data[x].tolist() if x else list(range(len(data)))
        for y_col in y_cols:
            trace = _create_trace(
                chart_type,
                x_data,
                data[y_col].tolist(),
                y_col if len(y_cols) > 1 else None,
            )
            traces.append(trace)

    return {"data": traces, "layout": layout}


def _create_trace(
    chart_type: str,
    x_data: List[Any],
    y_data: List[Any],
    name: Optional[str],
) -> Dict[str, Any]:
    """Create a single Plotly trace based on chart type."""
    base: Dict[str, Any] = {"x": x_data, "y": y_data}
    if name:
        base["name"] = name

    if chart_type == "line":
        return {"type": "scatter", "mode": "lines", **base}
    elif chart_type == "scatter":
        return {"type": "scatter", "mode": "markers", **base}
    elif chart_type == "bar":
        return {"type": "bar", **base}
    elif chart_type == "area":
        return {"type": "scatter", "mode": "lines", "fill": "tozeroy", **base}
    elif chart_type == "histogram":
        return {"type": "histogram", "x": x_data}
    elif chart_type == "pie":
        return {"type": "pie", "labels": x_data, "values": y_data}
    else:
        # Default to scatter with lines
        return {"type": "scatter", "mode": "lines", **base}


def plotly_chart(
    figure: Optional[Any] = None,
    data: Optional[Any] = None,
    x: Optional[str] = None,
    y: Optional[Union[str, List[str]]] = None,
    color: Optional[str] = None,
    chart_type: str = "line",
    title: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    on_click: bool = False,
    on_select: bool = False,
    on_hover: bool = False,
    on_relayout: bool = False,
    expandable: bool = False,
    modal_title: str = "",
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Render a Plotly chart with full interactivity and custom styling.

    Supports two modes:
    1. Pass a Plotly figure object directly
    2. Pass a pandas DataFrame with chart configuration

    Args:
        figure: Plotly figure object (go.Figure) or dict with 'data' and 'layout'.
                Takes precedence over `data` parameter.
        data: pandas DataFrame for quick chart creation
        x: Column name for x-axis (when using DataFrame)
        y: Column name(s) for y-axis - string or list of strings (when using DataFrame)
        color: Column name for color grouping (when using DataFrame)
        chart_type: Chart type when using DataFrame - "line", "bar", "scatter",
                   "area", "pie", or "histogram" (default "line")
        title: Chart title (when using DataFrame)
        config: Plotly config options (displayModeBar, scrollZoom, etc.)
        on_click: Enable click events (returns clicked points)
        on_select: Enable selection events (box/lasso selection)
        on_hover: Enable hover events (returns hovered points)
        on_relayout: Enable relayout events (zoom/pan state)
        expandable: Show expand button to open chart in full-page dialog
        modal_title: Title displayed in dialog header when expanded
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
               Set to False to disable theming for this component.
        key: Unique key for the component

    Returns:
        Event dict with 'type' and event data, or None if no event.
        Event types: 'click', 'select', 'hover', 'relayout'

    Example using Plotly figure:
        import plotly.graph_objects as go

        fig = go.Figure(
            data=[go.Scatter(x=[1,2,3], y=[4,5,6], mode='lines+markers')],
            layout=go.Layout(title='My Chart')
        )

        event = plotly_chart(
            figure=fig,
            on_click=True,
            on_select=True,
            style={"height": "400px"}
        )

        if event and event['type'] == 'click':
            st.write(f"Clicked: {event['points']}")

    Example using DataFrame:
        import pandas as pd

        df = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'sales': [100, 150, 120, 180],
            'orders': [50, 75, 60, 90]
        })

        # Simple line chart
        event = plotly_chart(
            data=df,
            x='month',
            y='sales',
            chart_type='line',
            title='Monthly Sales',
            on_click=True
        )

        # Multiple y columns as bar chart
        event = plotly_chart(
            data=df,
            x='month',
            y=['sales', 'orders'],
            chart_type='bar',
            title='Sales vs Orders'
        )

        # Scatter with color grouping
        event = plotly_chart(
            data=df,
            x='sales',
            y='orders',
            color='month',
            chart_type='scatter'
        )

    Example with expandable modal:
        event = plotly_chart(
            figure=fig,
            expandable=True,
            modal_title="Sales Dashboard",
            style={"height": "300px"}
        )
        # Click the expand button to open chart in full-page dialog
    """
    # Check if we should render an expanded dialog (from previous expand click)
    # This MUST be called first, before any other plotly_chart processing
    _maybe_render_expanded_dialog()

    # Determine figure dict
    if figure is not None:
        # Convert Plotly figure to dict if needed
        if hasattr(figure, "to_dict"):
            figure_dict = figure.to_dict()
        else:
            figure_dict = figure
    elif data is not None:
        # Create figure from DataFrame
        figure_dict = _dataframe_to_figure(data, x, y, color, chart_type, title)
    else:
        raise ValueError("Either 'figure' or 'data' parameter is required")

    # Resolve theme (None = use global, False = disable)
    from ..themes import get_active_theme
    resolved_theme = None
    if theme is not False:
        resolved_theme = theme if theme is not None else get_active_theme()

    # Render the component
    result = _component(
        component="plotly_chart",
        figure=figure_dict,
        config=config,
        onClickEnabled=on_click,
        onSelectEnabled=on_select,
        onHoverEnabled=on_hover,
        onRelayoutEnabled=on_relayout,
        expandable=expandable,
        modalTitle=modal_title,
        style=style,
        className=class_name,
        theme=resolved_theme,
        key=key,
        default=None,
    )

    # Handle expand event - store in session state and trigger rerun
    if result and isinstance(result, dict) and result.get("type") == "expand":
        event_ts = result.get("timestamp", 0)
        last_processed = st.session_state.get(_PROCESSED_EXPAND_KEY, 0)

        # Only process if this is a NEW expand click (different timestamp)
        if event_ts > last_processed:
            st.session_state[_PROCESSED_EXPAND_KEY] = event_ts
            st.session_state[_EXPANDED_DIALOG_KEY] = {
                "open": True,
                "figure": result.get("figure", figure_dict),
                "title": result.get("modalTitle", modal_title)
            }
            st.rerun()

    return result
