"""MSE function"""

import numpy as np


def mse(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute the mean squared error (MSE) between two arrays.

    Parameters:
        a (np.ndarray):
            First input array (e.g. reference or ground-truth signal).

        b (np.ndarray):
            Second input array (e.g. noisy or reconstructed signal).
            Must have the same shape as `a`.

    Returns:
        float:
            Mean squared error between `a` and `b`.
    """
    return np.mean((a - b) ** 2)
