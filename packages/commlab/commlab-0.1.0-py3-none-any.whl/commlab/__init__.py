"""
CommLab - Communication Laboratory Utilities
=============================================

A Python package providing utility functions for communication systems
experiments and simulations.

Available functions
-------------------
awgn : Add Additive White Gaussian Noise to signals

Example usage
-------------
>>> from commlab import awgn
>>> import numpy as np
>>> 
>>> signal = np.array([1, -1, 1, -1])
>>> noisy_signal = awgn(signal, SNRdb=10)
"""

from .main import awgn

__version__ = '0.1.0'
__all__ = ['awgn']