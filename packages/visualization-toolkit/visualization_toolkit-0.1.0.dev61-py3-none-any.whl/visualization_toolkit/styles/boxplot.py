"""Styles for the boxplot."""


def _base_boxprops(facecolor: str, hatch: str | None = None):
    """
    Build the base dictionary of properties for boxplot styles.

    Parameters:
      facecolor (str): The color of the filled box.
      hatch (str | None): Optional hatching pattern.

    Returns:
       dict: A dictionary containing the properties.
    """
    boxprops = {"facecolor": facecolor, "edgecolor": "black", "linewidth": 2}
    if hatch is not None:
        boxprops["hatch"] = hatch

    return {
        "patch_artist": True,
        "flierprops": {
            "markeredgecolor": "black",
            "markeredgewidth": 1.5,
            "markersize": 2,
        },
        "whiskerprops": {"color": "black", "linestyle": "--", "linewidth": 2},
        "capprops": {"color": "black", "linewidth": 2},
        "boxprops": boxprops,
        "medianprops": {"color": "black", "linewidth": 2.3},
    }


def boxprops_filled(facecolor: str = "lightgray"):
    """
    Return a dictionary of properties for filled box (style for printing).

    Parameters:
      facecolor (str): The color of the filled box. Default is "lightgray".

    Returns:
       dict: A dictionary containing the properties.
    """
    return _base_boxprops(facecolor=facecolor)


def boxprops_filled_hatched(facecolor: str = "white", hatch: str = "//"):
    """
    Return a dictionary of properties for hatched box (style for printing).

    Parameters:
      facecolor (str): The color of the filled box. Default is "white".
      hatch (str): The type of hatching pattern. Default is "//".

    Returns:
       dict: A dictionary containing the properties.
    """
    return _base_boxprops(facecolor=facecolor, hatch=hatch)
