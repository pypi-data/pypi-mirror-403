"""
Internal module for C++ backend detection and imports.

This module handles the detection of the C++ backend and provides
the backend functions to other modules without causing circular imports.
"""

# Try to import C++ backend
try:
    from ._fastaccess_cpp import (
        build_index as _cpp_build_index,
        fetch_subseq as _cpp_fetch_subseq,
        fetch_many as _cpp_fetch_many,
        reverse_complement as _cpp_reverse_complement,
        Entry as _CppEntry,
    )
    _USE_CPP = True
except ImportError:
    _USE_CPP = False
    _cpp_build_index = None
    _cpp_fetch_subseq = None
    _cpp_fetch_many = None
    _cpp_reverse_complement = None
    _CppEntry = None


def using_cpp_backend() -> bool:
    """
    Check if the C++ backend is being used.

    Returns:
        True if C++ backend is available and being used, False otherwise.
    """
    return _USE_CPP
