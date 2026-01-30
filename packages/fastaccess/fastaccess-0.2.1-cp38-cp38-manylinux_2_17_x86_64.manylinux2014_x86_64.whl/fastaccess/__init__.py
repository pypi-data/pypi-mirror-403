"""
fastaccess - Efficient random access to subsequences in FASTA files.

Provides indexed, random-access retrieval of subsequences from large multi-record
FASTA files using 1-based inclusive coordinates.

This library includes an optional C++ backend for improved performance. The C++
backend is automatically used when available; otherwise, the pure Python
implementation is used as a fallback.
"""

from .api import FastaStore
from ._backend import using_cpp_backend

__version__ = "0.2.1"
__all__ = ["FastaStore", "using_cpp_backend"]
