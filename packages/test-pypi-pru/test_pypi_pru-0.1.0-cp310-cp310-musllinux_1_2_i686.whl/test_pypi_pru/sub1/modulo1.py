"""Module modulo1 in sub1 package."""

import numpy as np


def func1(data: np.ndarray) -> np.ndarray:
    """Returns the square of the input array."""
    return np.square(data)


def func2(value: float, decimals: int) -> float:
    """Rounds the value to the specified number of decimal places."""
    return round(value, decimals)
