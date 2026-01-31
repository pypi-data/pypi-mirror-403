"""Styles for line plots."""

line_markers = [
    "o",  # circle
    "s",  # square
    "p",  # pentagon
    "v",  # triangle_down
    "<",  # triangle_left
    ">",  # triangle_right
    "^",  # triangle_up
    "*",  # star
    "h",  # hexagon
    "8",  # octagon
]


def _base_linestyle(
    marker: str,
    linestyle: str = "-",
    markerfacecolor: str = "none",
    markeredgecolor: str = "black",
    markersize: int = 8,
    linewidth: float = 1.5,
    color: str = "black",
):
    """
    Base style factory for line plots.

    This mirrors your boxplot style factories.

    Returns:
        dict: Style kwargs for plt.plot.
    """
    return {
        "marker": marker,
        "linestyle": linestyle,
        "markerfacecolor": markerfacecolor,
        "markeredgecolor": markeredgecolor,
        "markersize": markersize,
        "linewidth": linewidth,
        "color": color,
    }


def line_empty_marker(marker="o", color=None, linestyle="-"):
    """
    Line with empty markers and a solid black line.
    """
    return _base_linestyle(
        marker=marker,
        linestyle=linestyle,
        markerfacecolor="none",
        markeredgecolor=color,
        color=color,
    )


def line_filled_marker(marker="o", color=None, facecolor=None, linestyle="-"):
    """
    Line with filled markers.
    """
    if facecolor is None:
        facecolor = color
    return _base_linestyle(
        marker=marker,
        linestyle=linestyle,
        markerfacecolor=facecolor,
        markeredgecolor=color,
        color=color,
    )
