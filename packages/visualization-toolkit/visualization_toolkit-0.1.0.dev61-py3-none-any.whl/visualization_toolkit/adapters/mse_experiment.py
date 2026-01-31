"""MSE Noise Experiment"""

import numpy as np
import pandas as pd

from ..metrics.mse import mse


def mse_experiment(
    original_signals: np.ndarray,
    malformed_signals: dict[str, np.ndarray],
    hue_values: list,
    hue_name: str,
) -> pd.DataFrame:
    """
    Computes MSE between clean and malformed signals for different
    metrics and returns the results in a tidy DataFrame.

    The function assumes that signals are ordered such that for each hue value
    there are `n_samples` consecutive signal realizations.

    Returns a DataFrame with the following columns:
        - hue_name: value from the `hue_values` list
        - mse: mean squared error between clean and corresponding signal
        - label: key from the `signals` dictionary identifying the method/signal
        - run: index of the run within the same hue value

    Parameters:
        original_signals (np.ndarray):
            Array of clean reference signals with shape
            (n_levels * n_samples, ...).

        malformed_signals (dict[str, np.ndarray]):
            Dictionary mapping signal labels to arrays of signals
            (e.g. noisy or reconstructed), each having the same shape
            and ordering as `original_signals`.

        hue_values (array-like):
            Sequence of hue values corresponding to signal blocks.

        hue_name (str): Name of the column to use for the hue column.

    Returns:
        pd.DataFrame:
            DataFrame containing MSE statistics for each signal,
            hue value, level, and run.
    """
    hue_values = np.asarray(hue_values)
    n_ratios = len(hue_values)
    n_samples = len(original_signals) // n_ratios
    rows = []
    for label, signals in malformed_signals.items():
        for i, hue_value in enumerate(hue_values):
            for run in range(n_samples):
                idx = i * n_samples + run
                rows.append(
                    {
                        hue_name: hue_value,
                        "mse": mse(
                            original_signals[idx],
                            signals[idx],
                        ),
                        "label": label,
                        "run": run,
                    }
                )

    return pd.DataFrame(rows)
