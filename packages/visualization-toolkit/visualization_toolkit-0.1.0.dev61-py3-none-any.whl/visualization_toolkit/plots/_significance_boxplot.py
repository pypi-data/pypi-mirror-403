"""
Base versions of the significance levels and funtions.
"""

import itertools

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from visualization_toolkit.plots._boxplot_utils import get_x_levels


def pvalue_to_symbol(p: float, levels: dict) -> str:
    """
    Convert a p-value to a significance symbol based on threshold levels.

    Parameters:
        p (float): The p-value to convert.
        levels (dict): Dictionary mapping p-value thresholds to symbols.
                       Example: {0.001: '***', 0.01: '**', 0.05: '*'}

    Returns:
        str or None: The symbol corresponding to the first threshold that the p-value
                     is less than or equal to. Returns None if p-value exceeds all thresholds.
    """
    for thr, sym in sorted(levels.items()):
        if p <= thr:
            return sym
    return None


def draw_bracket(ax, x1, x2, y0, h, text, linewidth):
    """
    Draw a statistical significance bracket with text annotation on a matplotlib axes.

    Parameters:
        ax (matplotlib.axes.Axes): The axes to draw the bracket on.
        x1 (float): Starting x-coordinate of the bracket.
        x2 (float): Ending x-coordinate of the bracket.
        y0 (float): Base y-coordinate of the bracket.
        h (float): Height of the bracket above the base.
        text (str): Text to display above the bracket (typically significance symbols).
        linewidth (float): Line width for drawing the bracket.
    """
    ax.plot([x1, x1, x2, x2], [y0, y0 + h, y0 + h, y0], lw=linewidth, c="black")
    ax.text((x1 + x2) / 2, y0 + h, text, ha="center", va="bottom")


def compute_group_max(data, x, y, x_levels):
    """
    Compute maximum y-values for each x-group in the data.

    Parameters:
        data (pandas.DataFrame): Input data containing x and y columns.
        x (str): Column name for grouping variable.
        y (str): Column name for numeric values to compute maximum.
        x_levels (list): List of all possible levels in the x variable.

    Returns:
        dict: Dictionary mapping each x-level to its maximum y-value.
    """
    return {xv: data.loc[data[x] == xv, y].dropna().max() for xv in x_levels}


def get_x_position(row, hue, group_max, base_positions, x_levels, hue_levels):
    """
    Calculate x-positions for bracket endpoints based on grouping and hue variables.

    Parameters:
        row (pandas.Series or dict): Row containing bracket endpoint information with keys:
                                     - 'x1', 'x2' for simple brackets (hue=None)
                                     - 'x', 'hue1', 'hue2' for hue-based brackets
        hue (str or None): Column name for hue (secondary grouping) variable, or None if no hue.
        group_max (dict): Dictionary of maximum y-values per x-group (from compute_group_max).
        base_positions (list): Base x-positions for each x-level.
        x_levels (list): List of all possible levels in the x variable.
        hue_levels (list): List of all possible levels in the hue variable.

    Returns:
        tuple: (x_val, x1, x2) where:
               - x_val: x-level where bracket should be centered
               - x1: x-coordinate for left bracket endpoint
               - x2: x-coordinate for right bracket endpoint
    """
    n_hue = len(hue_levels)
    width = 0.8 / max(1, n_hue)

    def box_x(x_val, hue_val=None):
        j = list(x_levels).index(x_val)
        base = base_positions[j]
        if hue is None:
            return base
        i = list(hue_levels).index(hue_val)
        return base + (i - (n_hue - 1) / 2) * width

    if hue is None:
        x_val1 = row["x1"]
        x_val2 = row["x2"]
        x1 = box_x(row["x1"])
        x2 = box_x(row["x2"])
        if group_max[x_val1] > group_max[x_val2]:
            x_val = row["x1"]
        else:
            x_val = row["x2"]
    else:
        x_val = row["x"]
        x1 = box_x(x_val, row["hue1"])
        x2 = box_x(x_val, row["hue2"])
    return x_val, x1, x2


def add_significance(
    *,
    ax,
    data: pd.DataFrame,
    significance_fn,
    x: str,
    y: str,
    hue: str | None,
    hue_levels,
    x_levels,
    base_positions,
    levels: dict[float, str],
    base_offset: float = 0.05,  # насколько выше max значения начинать
    step_offset: float = 0.30,  # расстояние между скобками
    linewidth: float = 1.5,
) -> None:
    """
    Add significance brackets to a plot showing statistical comparisons.

    Parameters:
        ax (matplotlib.axes.Axes): The axes to draw the significance brackets on.
        data (pd.DataFrame): Data containing the variables to compare.
        significance_fn (callable): Function that returns a DataFrame with pairwise comparisons.
                                    Expected columns: 'pvalue', and either ('x1', 'x2') or
                                    ('x', 'hue1', 'hue2') depending on hue parameter.
        x (str): Column name for the primary grouping variable on x-axis.
        y (str): Column name for the numeric values being compared.
        hue (str or None): Column name for secondary grouping variable, or None.
        hue_levels (list): List of all possible levels in the hue variable.
        x_levels (list): List of all possible levels in the x variable.
        base_positions (list): Base x-positions for each x-level.
        levels (dict[float, str]): Mapping of p-value thresholds to significance symbols.
                                   Example: {0.001: '***', 0.01: '**', 0.05: '*', 0.1: '†'}
        base_offset (float): Relative offset from max y-value to start the first bracket.
                             Expressed as fraction of max y-value. Default: 0.05.
        step_offset (float): Relative vertical spacing between multiple brackets.
                             Expressed as fraction of max y-value. Default: 0.30.
        linewidth (float): Line width for drawing the brackets. Default: 1.5.

    Returns:
        None: The function modifies the plot in-place by adding significance brackets.
    """
    sig_df = significance_fn(data)
    group_max = compute_group_max(data, x, y, x_levels)
    group_counts = {xv: 0 for xv in x_levels}
    for _, row in sig_df.iterrows():
        sym = pvalue_to_symbol(row["pvalue"], levels)
        if sym is None:
            continue

        x_val, x1, x2 = get_x_position(
            row, hue, group_max, base_positions, x_levels, hue_levels
        )

        gmax = group_max[x_val]
        if not np.isfinite(gmax):
            continue
        base_y = gmax * (1 + base_offset)
        step_y = gmax * step_offset

        y0 = base_y + group_counts[x_val] * step_y
        group_counts[x_val] += 1

        draw_bracket(ax, x1, x2, y0, step_y * 0.2, sym, linewidth)


significance_levels_asterisk = {
    0.001: "***",
    0.01: "**",
    0.05: "*",
}


def compare_all_pairs(
    data: pd.DataFrame,
    x: str,
    y: str,
) -> pd.DataFrame:
    """
    Perform pairwise statistical comparisons between all levels of x-variable.

    Parameters:
        data (pd.DataFrame): Input data containing the variables to analyze.
        x (str): Column name for the grouping variable to compare between groups.
        y (str): Column name for the numeric variable to analyze.

    Returns:
        pd.DataFrame: DataFrame with columns:
                     - 'x1': First group in comparison
                     - 'x2': Second group in comparison
                     - 'pvalue': Mann-Whitney U test p-value for the pair
    """
    rows = []

    x_levels = data[x].unique()
    x_levels.sort()

    for x1, x2 in itertools.combinations(x_levels, 2):
        v1 = data.loc[data[x] == x1, y].dropna()
        v2 = data.loc[data[x] == x2, y].dropna()

        if len(v1) < 2 or len(v2) < 2:
            continue

        _, p = mannwhitneyu(v1, v2, alternative="two-sided")

        rows.append(
            {
                "x1": x1,
                "x2": x2,
                "pvalue": p,
            }
        )

    return pd.DataFrame(rows)


def compare_hue_within_groups(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: str,
    min_n: int = 2,
) -> pd.DataFrame:
    """
    Compare hue levels within each group of x-variable.

    Parameters:
        data (pd.DataFrame): Input data containing the variables to analyze.
        x (str): Column name for the primary grouping variable.
        y (str): Column name for the numeric variable to analyze.
        hue (str): Column name for the secondary grouping variable (hue) to compare within x-groups.
        min_n (int): Minimum sample size required for comparison. Default: 2.

    Returns:
        pd.DataFrame: DataFrame with columns:
                     - 'x': Group identifier from x-variable
                     - 'hue1': First hue level in comparison
                     - 'hue2': Second hue level in comparison
                     - 'pvalue': Mann-Whitney U test p-value for the pair
    """
    rows = []

    x_levels = get_x_levels(data, x)
    hue_levels = get_x_levels(data, hue)

    for x_val in x_levels:
        df_x = data[data[x] == x_val]

        for h1, h2 in itertools.combinations(hue_levels, 2):
            v1 = df_x.loc[df_x[hue] == h1, y].dropna()
            v2 = df_x.loc[df_x[hue] == h2, y].dropna()

            if len(v1) < min_n or len(v2) < min_n:
                continue

            _, p = mannwhitneyu(v1, v2, alternative="two-sided")

            rows.append(
                {
                    "x": x_val,
                    "hue1": h1,
                    "hue2": h2,
                    "pvalue": p,
                }
            )
    return pd.DataFrame(rows)
