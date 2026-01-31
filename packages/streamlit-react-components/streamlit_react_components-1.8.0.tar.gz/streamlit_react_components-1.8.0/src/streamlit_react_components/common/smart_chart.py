"""SmartChart component - Simplified chart creation for line, gauge, and waterfall charts."""

from typing import Dict, Any, Optional, List, Union
from .plotly_chart import plotly_chart, _dataframe_to_figure


def _dataframe_to_gauge(
    data: Any,
    value_column: str,
    min_value: Optional[float],
    max_value: Optional[float],
    threshold_low: Optional[float],
    threshold_medium: Optional[float],
    threshold_high: Optional[float],
    title: Optional[str],
) -> Dict[str, Any]:
    """Convert a DataFrame to a Plotly gauge indicator figure."""
    from ..themes import get_active_theme

    # Validate required column exists
    if value_column not in data.columns:
        raise ValueError(f"Column '{value_column}' not found in DataFrame. Available columns: {list(data.columns)}")

    # Extract value (first row if multiple)
    value = float(data[value_column].iloc[0])

    # Auto-calculate min/max if not provided
    if min_value is None:
        min_value = 0
    if max_value is None:
        max_value = float(data[value_column].max() * 1.2)

    # Validate threshold ordering
    if threshold_low is not None and threshold_medium is not None and threshold_low >= threshold_medium:
        raise ValueError("threshold_low must be less than threshold_medium")
    if threshold_medium is not None and threshold_high is not None and threshold_medium >= threshold_high:
        raise ValueError("threshold_medium must be less than threshold_high")

    # Get theme colors
    theme = get_active_theme()
    primary = theme['colors']['primary']
    success = theme['colors']['success']
    warning = theme['colors']['warning']
    error = theme['colors']['error']

    # Build gauge configuration
    gauge_config = {
        'axis': {'range': [min_value, max_value]},
        'bar': {'color': primary}
    }

    # Add colored threshold ranges
    if threshold_low is not None or threshold_medium is not None or threshold_high is not None:
        steps = []
        if threshold_low is not None:
            steps.append({'range': [min_value, threshold_low], 'color': error})
        if threshold_medium is not None:
            start = threshold_low if threshold_low is not None else min_value
            steps.append({'range': [start, threshold_medium], 'color': warning})
        if threshold_high is not None:
            start = threshold_medium if threshold_medium is not None else min_value
            steps.append({'range': [start, threshold_high], 'color': success})
            # Add a final green band if there's space
            if threshold_high < max_value:
                steps.append({'range': [threshold_high, max_value], 'color': success})

        gauge_config['steps'] = steps

    return {
        'data': [{
            'type': 'indicator',
            'mode': 'gauge+number',
            'value': value,
            'title': {'text': title or ''},
            'gauge': gauge_config,
            'domain': {'x': [0, 1], 'y': [0, 1]}
        }],
        'layout': {}
    }


def _dataframe_to_waterfall(
    data: Any,
    category_column: str,
    value_column: str,
    measure_column: Optional[str],
    title: Optional[str],
) -> Dict[str, Any]:
    """Convert a DataFrame to a Plotly waterfall figure."""
    from ..themes import get_active_theme

    # Validate required columns exist
    if category_column not in data.columns:
        raise ValueError(f"Column '{category_column}' not found in DataFrame. Available columns: {list(data.columns)}")
    if value_column not in data.columns:
        raise ValueError(f"Column '{value_column}' not found in DataFrame. Available columns: {list(data.columns)}")

    categories = data[category_column].tolist()
    values = data[value_column].tolist()

    # Use measure_column if provided, otherwise auto-detect
    if measure_column and measure_column in data.columns:
        measures = data[measure_column].tolist()
    else:
        # Auto-detect: zero values are likely totals
        measures = ['total' if v == 0 else 'relative' for v in values]

    # Get theme colors
    theme = get_active_theme()
    success = theme['colors']['success']
    error = theme['colors']['error']
    info = theme['colors']['info']

    return {
        'data': [{
            'type': 'waterfall',
            'x': categories,
            'y': values,
            'measure': measures,
            'connector': {'line': {'color': '#475569'}},  # slate-600
            'increasing': {'marker': {'color': success}},
            'decreasing': {'marker': {'color': error}},
            'totals': {'marker': {'color': info}},
        }],
        'layout': {
            'title': title or '',
            'showlegend': False,
            'xaxis': {'title': category_column},
            'yaxis': {'title': 'Value'}
        }
    }


def _dataframe_to_scatter(
    data: Any,
    x: str,
    y: str,
    size: Optional[str] = None,
    color_column: Optional[str] = None,
    text: Optional[str] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert DataFrame to Plotly scatter figure."""
    from ..themes import get_active_theme

    # Validate required columns
    if x not in data.columns:
        raise ValueError(f"Column '{x}' not found in DataFrame. Available columns: {list(data.columns)}")
    if y not in data.columns:
        raise ValueError(f"Column '{y}' not found in DataFrame. Available columns: {list(data.columns)}")

    # Build marker config
    marker_config = {}
    if size and size in data.columns:
        marker_config['size'] = data[size].tolist()
    if color_column and color_column in data.columns:
        marker_config['color'] = data[color_column].tolist()
        marker_config['colorscale'] = 'Viridis'
        marker_config['showscale'] = True

    # Build hover text
    hover_text = data[text].tolist() if text and text in data.columns else None

    return {
        'data': [{
            'type': 'scatter',
            'mode': 'markers',
            'x': data[x].tolist(),
            'y': data[y].tolist(),
            'marker': marker_config,
            'text': hover_text,
            'hovertemplate': f'{x}: %{{x}}<br>{y}: %{{y}}<extra></extra>'
        }],
        'layout': {
            'title': title or '',
            'xaxis': {'title': x},
            'yaxis': {'title': y}
        }
    }


def _dataframe_to_bar(
    data: Any,
    x: str,
    y: Union[str, List[str]],
    orientation: str = 'v',
    barmode: str = 'group',
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert DataFrame to Plotly bar figure."""
    from ..themes import get_active_theme

    theme = get_active_theme()
    colors = [
        theme['colors']['primary'],
        theme['colors']['secondary'],
        theme['colors']['success'],
        theme['colors']['warning'],
        theme['colors']['info']
    ]

    # Validate columns
    if x not in data.columns:
        raise ValueError(f"Column '{x}' not found in DataFrame. Available columns: {list(data.columns)}")

    y_cols = [y] if isinstance(y, str) else y
    for y_col in y_cols:
        if y_col not in data.columns:
            raise ValueError(f"Column '{y_col}' not found in DataFrame. Available columns: {list(data.columns)}")

    traces = []
    for idx, y_col in enumerate(y_cols):
        if orientation == 'v':
            trace = {
                'type': 'bar',
                'x': data[x].tolist(),
                'y': data[y_col].tolist(),
                'name': y_col,
                'marker': {'color': colors[idx % len(colors)]}
            }
        else:  # horizontal
            trace = {
                'type': 'bar',
                'x': data[y_col].tolist(),
                'y': data[x].tolist(),
                'orientation': 'h',
                'name': y_col,
                'marker': {'color': colors[idx % len(colors)]}
            }
        traces.append(trace)

    return {
        'data': traces,
        'layout': {
            'title': title or '',
            'barmode': barmode,
            'xaxis': {'title': x if orientation == 'v' else 'Value'},
            'yaxis': {'title': 'Value' if orientation == 'v' else x}
        }
    }


def _dataframe_to_histogram(
    data: Any,
    x: str,
    nbins: int = 30,
    show_mean: bool = True,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert DataFrame to Plotly histogram figure."""
    from ..themes import get_active_theme

    if x not in data.columns:
        raise ValueError(f"Column '{x}' not found in DataFrame. Available columns: {list(data.columns)}")

    theme = get_active_theme()
    primary = theme['colors']['primary']
    success = theme['colors']['success']

    figure = {
        'data': [{
            'type': 'histogram',
            'x': data[x].tolist(),
            'nbinsx': nbins,
            'marker': {'color': primary, 'opacity': 0.75},
            'name': 'Distribution'
        }],
        'layout': {
            'title': title or f'{x} Distribution',
            'xaxis': {'title': x},
            'yaxis': {'title': 'Frequency'},
            'showlegend': True
        }
    }

    # Add mean line if requested
    if show_mean:
        mean_val = float(data[x].mean())
        figure['layout']['shapes'] = [{
            'type': 'line',
            'x0': mean_val,
            'x1': mean_val,
            'y0': 0,
            'y1': 1,
            'yref': 'paper',
            'line': {'color': success, 'dash': 'dash', 'width': 2}
        }]
        figure['layout']['annotations'] = [{
            'x': mean_val,
            'y': 1,
            'yref': 'paper',
            'text': f'Mean: {mean_val:.2f}',
            'showarrow': False,
            'yshift': 10
        }]

    return figure


def _dataframe_to_pie(
    data: Any,
    labels: str,
    values: str,
    hole: float = 0.0,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert DataFrame to Plotly pie/donut figure."""
    from ..themes import get_active_theme

    if labels not in data.columns:
        raise ValueError(f"Column '{labels}' not found in DataFrame. Available columns: {list(data.columns)}")
    if values not in data.columns:
        raise ValueError(f"Column '{values}' not found in DataFrame. Available columns: {list(data.columns)}")

    theme = get_active_theme()
    colors = [
        theme['colors']['primary'],
        theme['colors']['secondary'],
        theme['colors']['success'],
        theme['colors']['warning'],
        theme['colors']['info'],
        theme['colors']['error']
    ]

    return {
        'data': [{
            'type': 'pie',
            'labels': data[labels].tolist(),
            'values': data[values].tolist(),
            'hole': hole,
            'marker': {'colors': colors}
        }],
        'layout': {
            'title': title or ''
        }
    }


def smart_chart(
    data: Any,
    chart_type: str,
    # Common chart parameters
    x: Optional[str] = None,
    y: Optional[Union[str, List[str]]] = None,
    # Scatter plot parameters
    size: Optional[str] = None,
    text: Optional[str] = None,
    # Bar chart parameters
    orientation: str = 'v',
    barmode: str = 'group',
    # Histogram parameters
    nbins: int = 30,
    show_mean: bool = True,
    # Pie chart parameters
    labels: Optional[str] = None,
    values: Optional[str] = None,
    hole: float = 0.0,
    # Gauge chart parameters
    value_column: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    threshold_low: Optional[float] = None,
    threshold_medium: Optional[float] = None,
    threshold_high: Optional[float] = None,
    # Waterfall chart parameters
    category_column: Optional[str] = None,
    value_column_waterfall: Optional[str] = None,
    measure_column: Optional[str] = None,
    # Common parameters
    title: Optional[str] = None,
    color: Optional[str] = None,
    # Pass-through to plotly_chart
    on_click: bool = False,
    on_select: bool = False,
    on_hover: bool = False,
    on_relayout: bool = False,
    expandable: bool = False,
    modal_title: str = "",
    # Styling
    style: Optional[Dict[str, Any]] = None,
    class_name: str = "",
    theme: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create a smart chart that automatically converts DataFrames to Plotly charts.

    This is a wrapper component that simplifies chart creation by transforming DataFrames
    into appropriate Plotly figure configurations based on the specified chart_type.

    Args:
        data: pandas DataFrame containing the data to plot
        chart_type: Type of chart to create - 'line', 'scatter', 'bar', 'bar_horizontal',
                   'histogram', 'pie', 'gauge', or 'waterfall'

        # Common Chart Parameters
        x: Column name for x-axis (required for line, scatter, bar, histogram charts)
        y: Column name(s) for y-axis - string or list of strings (required for line, scatter, bar charts)

        # Scatter Plot Parameters
        size: Column name for marker sizes (optional)
        text: Column name for hover text (optional)

        # Bar Chart Parameters
        orientation: 'v' for vertical (default) or 'h' for horizontal
        barmode: 'group' (default), 'stack', or 'overlay'

        # Histogram Parameters
        nbins: Number of bins (default: 30)
        show_mean: Show mean line on histogram (default: True)

        # Pie Chart Parameters
        labels: Column name for pie slice labels (required for pie charts)
        values: Column name for pie slice values (required for pie charts)
        hole: Hole size for donut chart (0.0-1.0, default: 0.0 for pie)

        # Gauge Chart Parameters
        value_column: Column name containing the value to display (required for gauge charts)
        min_value: Minimum value for gauge range (auto-calculated if not provided)
        max_value: Maximum value for gauge range (auto-calculated if not provided)
        threshold_low: Low threshold value (red zone below this)
        threshold_medium: Medium threshold value (amber zone)
        threshold_high: High threshold value (green zone above this)

        # Waterfall Chart Parameters
        category_column: Column name for categories (required for waterfall charts)
        value_column_waterfall: Column name for values (required for waterfall charts)
        measure_column: Optional column specifying 'relative' or 'total' for each row.
                       If not provided, auto-detects: zeros are 'total', non-zeros are 'relative'

        # Common Parameters
        title: Chart title
        color: Column name for color grouping (line charts only)
        on_click: Enable click events
        on_select: Enable selection events (box/lasso)
        on_hover: Enable hover events
        on_relayout: Enable relayout events (zoom/pan)
        expandable: Show expand button to open chart in full-page dialog
        modal_title: Title displayed in dialog header when expanded
        style: Inline CSS styles as a dictionary
        class_name: Tailwind CSS classes
        theme: Optional theme dictionary. If None, uses active global theme.
        key: Unique key for the component

    Returns:
        Event dict with 'type' and event data, or None if no event.

    Examples:
        # Line Chart
        import pandas as pd

        df = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr'],
            'revenue': [100, 150, 120, 180],
            'costs': [60, 90, 70, 100]
        })

        smart_chart(
            data=df,
            chart_type='line',
            x='month',
            y=['revenue', 'costs'],
            title='Monthly Performance'
        )

        # Gauge Chart
        df_gauge = pd.DataFrame({'conversion_rate': [73.5]})

        smart_chart(
            data=df_gauge,
            chart_type='gauge',
            value_column='conversion_rate',
            min_value=0,
            max_value=100,
            threshold_low=30,
            threshold_medium=70,
            threshold_high=90,
            title='Conversion Rate'
        )

        # Waterfall Chart
        df_waterfall = pd.DataFrame({
            'category': ['Sales', 'Consulting', 'Net Revenue', 'Purchases', 'Other', 'Profit'],
            'amount': [60, 80, 0, -40, -20, 0],
            'measure': ['relative', 'relative', 'total', 'relative', 'relative', 'total']
        })

        smart_chart(
            data=df_waterfall,
            chart_type='waterfall',
            category_column='category',
            value_column_waterfall='amount',
            measure_column='measure',
            title='Revenue Breakdown'
        )
    """
    # Validate DataFrame
    if data is None or (hasattr(data, 'empty') and data.empty):
        raise ValueError("DataFrame cannot be None or empty")

    # Validate chart_type
    valid_types = ['line', 'scatter', 'bar', 'bar_horizontal', 'histogram', 'pie', 'gauge', 'waterfall']
    if chart_type not in valid_types:
        raise ValueError(f"Invalid chart_type: '{chart_type}'. Must be one of: {', '.join(valid_types)}")

    # Route to appropriate transformer and validate required parameters
    if chart_type == 'scatter':
        if x is None or y is None:
            raise ValueError("Scatter chart requires 'x' and 'y' parameters")
        figure = _dataframe_to_scatter(data, x, y, size, color, text, title)

    elif chart_type in ['bar', 'bar_horizontal']:
        if x is None or y is None:
            raise ValueError("Bar chart requires 'x' and 'y' parameters")
        orient = 'h' if chart_type == 'bar_horizontal' else 'v'
        figure = _dataframe_to_bar(data, x, y, orient, barmode, title)

    elif chart_type == 'histogram':
        if x is None:
            raise ValueError("Histogram requires 'x' parameter")
        figure = _dataframe_to_histogram(data, x, nbins, show_mean, title)

    elif chart_type == 'pie':
        if labels is None or values is None:
            raise ValueError("Pie chart requires 'labels' and 'values' parameters")
        figure = _dataframe_to_pie(data, labels, values, hole, title)

    elif chart_type == 'line':
        if x is None or y is None:
            raise ValueError("Line chart requires 'x' and 'y' parameters")

        # Validate columns exist
        if x not in data.columns:
            raise ValueError(f"Column '{x}' not found in DataFrame. Available columns: {list(data.columns)}")

        y_cols = [y] if isinstance(y, str) else y
        for y_col in y_cols:
            if y_col not in data.columns:
                raise ValueError(f"Column '{y_col}' not found in DataFrame. Available columns: {list(data.columns)}")

        # Use existing _dataframe_to_figure for line charts
        figure = _dataframe_to_figure(data, x, y, color, 'line', title)

    elif chart_type == 'gauge':
        if value_column is None:
            raise ValueError("Gauge chart requires 'value_column' parameter")

        figure = _dataframe_to_gauge(
            data,
            value_column,
            min_value,
            max_value,
            threshold_low,
            threshold_medium,
            threshold_high,
            title
        )

    elif chart_type == 'waterfall':
        if category_column is None or value_column_waterfall is None:
            raise ValueError("Waterfall chart requires 'category_column' and 'value_column_waterfall' parameters")

        figure = _dataframe_to_waterfall(
            data,
            category_column,
            value_column_waterfall,
            measure_column,
            title
        )

    # Delegate to plotly_chart
    return plotly_chart(
        figure=figure,
        on_click=on_click,
        on_select=on_select,
        on_hover=on_hover,
        on_relayout=on_relayout,
        expandable=expandable,
        modal_title=modal_title or title or "",
        style=style,
        class_name=class_name,
        theme=theme,
        key=key,
    )
