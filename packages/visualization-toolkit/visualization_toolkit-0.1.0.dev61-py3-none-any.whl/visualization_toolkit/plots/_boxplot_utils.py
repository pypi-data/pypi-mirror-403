"""Helper functions for plotting boxplot."""

from typing import Sequence

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


def is_broken(y_limits: Sequence) -> bool:
    """
    Use the limits to check if the axle is broken.
    Parameters:
       y_limits (Sequence): Sequence of (min, max) pairs.

    Returns:
        bool: True if the axle is broken, False otherwise.
    """
    return y_limits is not None and len(y_limits) >= 2


def check_y_limits(y_limits: Sequence) -> None:
    """
    Validate the y_limits parameter.
    Parameters:
       y_limits: Sequence of (min, max) pairs.
    """
    if y_limits is not None:
        if not all(
            isinstance(lim, (tuple, list)) and len(lim) == 2 for lim in y_limits
        ):
            raise ValueError(
                "y_limits must be a sequence of (min, max) tuples, "
                "e.g. y_limits=((1e-2, 1e-1),) or "
                "y_limits=((1e-3, 1e-2), (1e1, 1e2))"
            )


def create_axes(
    y_limits: Sequence,
    height_ratios: tuple,
    fig_size: tuple,
    ax: matplotlib.axes.Axes | None = None,
):
    """
    Create the axes for the boxplot.

    Parameters:
        y_limits (Sequence): Sequence of (min, max) pairs.
        height_ratios (tuple): Height ratios for the axes.
        fig_size (tuple): Size of the figure.
        ax (matplotlib.axes.Axes | None): Ax to plot.
    Returns:
        fig, axes: Figure and axes.
    """
    check_y_limits(y_limits)
    if y_limits is None or len(y_limits) < 2:
        if ax is None:
            fig, ax_main = plt.subplots(figsize=fig_size)
        else:
            fig = ax.figure
            ax_main = ax
        if (y_limits is not None) and (len(y_limits) == 1):
            ax_main.set_ylim(y_limits[0])
        return fig, (ax_main,)
    bottom_ylim, top_ylim = y_limits
    if bottom_ylim is None or top_ylim is None:
        raise ValueError("bottom_ylim and top_ylim required if broken=True")
    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=fig_size,
        gridspec_kw={
            "height_ratios": height_ratios,
            "hspace": 0.05,
        },
    )
    _draw_axis_break(ax_top, ax_bottom)
    ax_bottom.set_ylim(bottom_ylim)
    ax_top.set_ylim(top_ylim)
    return fig, (ax_top, ax_bottom)


def get_x_levels(data: pd.DataFrame, x: str) -> list:
    """
    Get the unique values of a column as list.
    """
    if x is None:
        return [None]
    x_levels = data[x].unique()
    x_levels.sort()
    return x_levels


def add_legend(
    fig: plt.Figure, styles: dict, hue_levels: list, fontsize: float
) -> None:
    """
    Add a legend to the figure.

    Parameters:
        fig (plt.Figure): The figure to add legend.
        styles (dict): A dictionary of styles for each hue level.
        hue_levels (list): A list of hue levels.
        fontsize (float): The font size for the legend.
    """
    legend_handles = []
    n_hue = len(hue_levels)

    for hue_val in hue_levels:
        style = styles.get(hue_val, {})

        boxprops = style.get("boxprops", {})
        patch = Patch(
            facecolor=boxprops.get("facecolor", "none"),
            edgecolor=boxprops.get("edgecolor", "black"),
            hatch=boxprops.get("hatch", None),
            label=str(hue_val),
        )
        legend_handles.append(patch)

    fig.legend(
        handles=legend_handles,
        fontsize=fontsize,
        loc="lower center",
        ncol=n_hue,
    )


def _draw_axis_break(ax_top, ax_bottom, d=0.5, **kwargs):
    """
    Draw a broken axis between two axes.

    Parameters:
        ax_top(matplotlib.axes.Axes): The top axis.
        ax_bottom(matplotlib.axes.Axes): The bottom axis.
        d(float): The distance from the top axis to the bottom.
        **kwargs: Additional keyword arguments to override default marker properties.
                  Common options include: color, markersize, markeredgewidth (mew), etc.

    Returns:
      None: Modifies the axes in-place by adding break markers.
    """
    default_kwargs = {
        "color": "k",
        "clip_on": False,
        "marker": [(-1, -d), (1, d)],
        "markersize": 12,
        "linestyle": "none",
        "mec": "k",
        "mew": 1,
    }
    default_kwargs.update(kwargs)
    ax_top.plot([0, 1], [0, 0], transform=ax_top.transAxes, **default_kwargs)
    ax_bottom.plot([0, 1], [1, 1], transform=ax_bottom.transAxes, **default_kwargs)
