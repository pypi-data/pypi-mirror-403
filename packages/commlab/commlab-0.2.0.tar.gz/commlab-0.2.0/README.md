# CommLab - Communication Laboratory Utilities

A Python package providing utility functions for communication systems experiments and simulations.

## Features

- **AWGN Noise Addition**: Add Additive White Gaussian Noise to signals with specified SNR
- Supports both real and complex-valued signals
- Works with multi-dimensional arrays
- Easy to use and extend

## Installation

### From source (Development mode)

1. Clone or download this repository
2. Navigate to the package directory
3. Install in editable mode:

```bash
pip install -e .
```

This allows you to modify the source code and see changes immediately without reinstalling.

## Usage

### Basic Example

```python
import numpy as np
from commlab import awgn

# Create a simple BPSK signal
signal = np.array([1, -1, 1, -1, 1, -1])

# Add AWGN with SNR = 10 dB
noisy_signal = awgn(signal, SNRdb=10)
```

### QPSK Example

```python
import numpy as np
from commlab import awgn

# Create QPSK symbols
qpsk_symbols = np.array([1+1j, -1+1j, -1-1j, 1-1j]) / np.sqrt(2)

# Add noise with 15 dB SNR
noisy_qpsk = awgn(qpsk_symbols, SNRdb=15)
```

### With Oversampling

```python
import numpy as np
from commlab import awgn

# Oversampled signal (4 samples per symbol)
oversampled_signal = np.repeat([1, -1, 1, -1], 4)

# Add noise (L=4 for 4 samples per symbol)
noisy_signal = awgn(oversampled_signal, SNRdb=10, L=4)
```

## Function Reference

### `awgn(s, SNRdb, L=1)`

Add Additive White Gaussian Noise to a signal.

**Parameters:**
- `s` (array_like): Input signal (real or complex)
- `SNRdb` (float): Signal-to-Noise Ratio in dB
- `L` (int, optional): Samples per symbol (default=1)

**Returns:**
- `r` (ndarray): Noisy signal

## Requirements

- Python >= 3.7
- NumPy >= 1.20.0

## Future Extensions

This package is designed to be easily extensible. Future versions may include:
- Modulation schemes (BPSK, QPSK, QAM)
- Demodulation functions
- BER calculation utilities
- Eye diagram plotting
- Channel models

## License

MIT License

## Contributing

Feel free to add more functions as needed for your communication lab experiments!