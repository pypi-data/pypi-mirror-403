"""
MistrasDTA-hdf5

Streaming parser and HDF5 exporter for Mistras DTA files.
"""

from .stream import read_bin_stream
from .hdf5 import stream_to_h5

__version__ = "0.1.6"

__all__ = [
    "read_bin_stream",
    "stream_to_h5",
]
