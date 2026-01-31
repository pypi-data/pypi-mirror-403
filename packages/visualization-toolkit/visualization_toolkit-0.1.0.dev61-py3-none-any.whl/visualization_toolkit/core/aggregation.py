"""Statistics Aggregation"""

import numpy as np
import pandas as pd


def aggregate(
    data: pd.DataFrame,
    x: str,
    y: str,
    estimator: str = "mean",
    errorbar_type="p",
    errorbar_data=(5, 95),
):
    """
    Aggregate a metric grouped by values of another column.

    For each unique value in column `x`, the function computes a central tendency
    estimate of column `y` and corresponding asymmetric error bars.

    Currently supported:
        - estimator: "mean" | "median"
        - errorbar_type: "p", for percentile-based error bars
        - errorbar_data: (0, 95), for percentile-based error bars

    Parameters:
        data (pd.DataFrame):
            Input DataFrame containing at least columns `x` and `y`.

        x (str):
            Name of the column used for grouping.

        y (str):
            Name of the metric column to aggregate.

        estimator (str, default="mean"):
            Aggregation method for the central value.
            Currently "mean" or "median" are supported.

        errorbar_type (str, default="p"):
            Error bar specification.
                - "p": percentile-based error bars
        errorbar_data (tuple, default=(0, 95)):
            Error bar specification.
            The tuple of data. Default is two percentiles (low, high) for percentile-based error bars.

    Returns:
        tuple[np.ndarray, np.ndarray]:
            - x_list: array of unique `x` values
            - metric_list: array of aggregated metric values for each unique `x`
            - metric_err: 2×N array of asymmetric errors
              (lower_errors, upper_errors), suitable for plotting
    """
    x_list = np.sort(data[x].unique())
    metric_list = []
    metric_err_list = []

    for x_value in x_list:
        metric = data.loc[data[x] == x_value, y].values

        if estimator == "median":
            center = np.percentile(metric, 50)
        elif estimator == "mean":
            center = np.mean(metric)
        else:
            raise NotImplementedError(estimator)

        if errorbar_type == "p":
            p_low, p_high = errorbar_data
            low = np.percentile(metric, p_low)
            high = np.percentile(metric, p_high)

            metric_err_list.append((center - low, high - center))
        else:
            raise NotImplementedError(errorbar_type)
        metric_list.append(center)

    return (
        np.array(x_list),
        np.array(metric_list),
        np.array(metric_err_list).T,
    )
