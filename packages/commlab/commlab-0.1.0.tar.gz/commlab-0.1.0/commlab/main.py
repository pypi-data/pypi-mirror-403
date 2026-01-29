"""
Noise generation functions for communication systems.
"""

import numpy as np


def awgn(s, SNRdb, L=1):
    """
    Add Additive White Gaussian Noise (AWGN) to a signal.
    
    This function adds AWGN to the input signal based on the specified 
    Signal-to-Noise Ratio (SNR) in dB. It works with both real and 
    complex-valued signals of any dimension.
    
    Parameters
    ----------
    s : array_like
        Input signal (real or complex-valued). Can be 1D or multi-dimensional.
    SNRdb : float
        Signal-to-Noise Ratio in decibels (dB).
    L : int, optional
        Samples per symbol for oversampled signals (default=1).
        Used to normalize the signal power calculation.
    
    Returns
    -------
    r : ndarray
        Noisy signal with the same shape as input signal s.
        r = s + n, where n is the generated AWGN.
    
    Examples
    --------
    >>> import numpy as np
    >>> from commlab import awgn
    >>> 
    >>> # Real signal
    >>> signal = np.array([1, -1, 1, -1])
    >>> noisy_signal = awgn(signal, SNRdb=10)
    >>> 
    >>> # Complex signal (QPSK)
    >>> qpsk_signal = np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2)
    >>> noisy_qpsk = awgn(qpsk_signal, SNRdb=15)
    
    Notes
    -----
    The noise power is calculated as N0 = P/gamma, where:
    - P is the average signal power
    - gamma is the SNR in linear scale (10^(SNRdb/10))
    
    For complex signals, the noise is generated with equal power in 
    both I and Q components.
    """
    # Convert SNR from dB to linear scale
    gamma = 10**(SNRdb / 10.0)
    
    # Calculate average signal power
    P = L * np.sum(np.abs(s)**2) / s.size
    
    # Calculate noise power spectral density
    N0 = P / gamma
    
    # Generate AWGN based on signal type
    if np.isrealobj(s):
        # Real-valued signal: generate real Gaussian noise
        n = np.sqrt(N0 / 2) * np.random.standard_normal(s.shape)
    else:
        # Complex-valued signal: generate complex Gaussian noise
        # with equal power in real and imaginary components
        n = np.sqrt(N0 / 2) * (
            np.random.standard_normal(s.shape) + 
            1j * np.random.standard_normal(s.shape)
        )
    
    # Return noisy signal
    return s + n