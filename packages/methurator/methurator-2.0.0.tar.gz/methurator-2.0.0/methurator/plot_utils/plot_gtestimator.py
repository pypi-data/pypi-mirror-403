import numpy as np
from rich.console import Console
import plotly.graph_objs as go

# ===============================================================
# Plotting Functions
# ===============================================================

console = Console()


def human_readable(num):
    """Format large numbers into human-readable form (e.g., 1.5K, 2.3M, 1.1B)."""
    for unit, divisor in [("B", 1e9), ("M", 1e6), ("K", 1e3)]:
        if num >= divisor:
            return f"{num/divisor:.1f}{unit}"
    return str(int(num))


def fmt_list(values):
    """Round and convert a list of numbers to human-readable strings."""
    return [human_readable(round(v, 0)) for v in values]


def make_base_plot(
    title,
    xaxis="Extrapolation factor (t = 1 means observed sequencing depth)",
    yaxis="Number of CpGs",
):
    """Create a preformatted Plotly figure."""
    fig = go.Figure()
    fig.update_xaxes(title_text=xaxis, showgrid=True)
    fig.update_yaxes(title_text=yaxis, showgrid=True)
    fig.update_layout(
        title=dict(text=title, x=0.5, y=0.9),
        width=950,
        height=620,
        template="plotly_white",
        showlegend=False,
    )
    return fig


def plot_gtestimator(plot_obj):
    """Plot observed and predicted CpG values based on fitted asymptotic growth.
    Arguments:
        plot_obj: PlotObject containing all necessary data for plotting.
    """
    # Extract data from plot object
    x_all = plot_obj.t_data
    y_all = plot_obj.cpgs_data

    # Separate interpolated (t <= 1) and extrapolated (t > 1) data
    interpolated_indices = [i for i, x in enumerate(x_all) if x <= 1.0]
    extrapolated_indices = [i for i, x in enumerate(x_all) if x > 1.0]

    # Format the data to human-readable strings
    y_all_fmt = fmt_list(y_all)
    reads_all_fmt = [str(round(x, 2)) for x in x_all]

    # Create base plot
    fig = make_base_plot(plot_obj.sample_name)
    fig.update_layout(showlegend=True)
    fig.update_xaxes(tickangle=45)

    # Interpolated predicted data (t <= 1)
    if interpolated_indices:
        interp_x = [reads_all_fmt[i] for i in interpolated_indices]
        interp_y = [y_all[i] for i in interpolated_indices]
        interp_y_fmt = [y_all_fmt[i] for i in interpolated_indices]
        interp_t = [x_all[i] for i in interpolated_indices]

        fig.add_trace(
            go.Scatter(
                x=interp_x,
                y=interp_y,
                mode="lines+markers",
                name="Interpolated",
                customdata=np.column_stack((interp_y_fmt, interp_t)),
                hovertemplate=(
                    "<b>Interpolated</b><br>"
                    "Number CpGs: %{customdata[0]}<br>"
                    "Extrapolation factor (t): %{customdata[1]}<br>"
                    "<extra></extra>"
                ),
                line=dict(color="#1f77b4", width=2),
                marker=dict(size=5),
            )
        )

    # Extrapolated predicted data (t > 1)
    if extrapolated_indices:
        extrap_x = [reads_all_fmt[i] for i in extrapolated_indices]
        extrap_y = [y_all[i] for i in extrapolated_indices]
        extrap_y_fmt = [y_all_fmt[i] for i in extrapolated_indices]
        extrap_t = [x_all[i] for i in extrapolated_indices]

        fig.add_trace(
            go.Scatter(
                x=extrap_x,
                y=extrap_y,
                mode="lines+markers",
                name="Extrapolated",
                customdata=np.column_stack((extrap_y_fmt, extrap_t)),
                hovertemplate=(
                    "<b>Extrapolated</b><br>"
                    "Number CpGs: %{customdata[0]}<br>"
                    "Extrapolation factor (t): %{customdata[1]}<br>"
                    "<extra></extra>"
                ),
                line=dict(color="#ff7f0e", width=2, dash="dash"),
                marker=dict(size=5),
            )
        )

    fig.write_html(plot_obj.output_path)
    print(f"✅ Plot saved to: {plot_obj.output_path}")
