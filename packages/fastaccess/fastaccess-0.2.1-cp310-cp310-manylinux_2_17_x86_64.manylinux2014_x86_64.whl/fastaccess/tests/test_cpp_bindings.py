"""
Tests specifically for C++ bindings and comparison with Python implementation.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastaccess import using_cpp_backend
from fastaccess.api import FastaStore

# Import Python fallbacks for comparison
from fastaccess.index import build_index as py_build_index
from fastaccess.store import fetch_subseq as py_fetch_subseq

# Test fixtures paths
TEST_DIR = Path(__file__).parent
WRAPPED_FA = TEST_DIR / "wrapped.fa"
UNWRAPPED_FA = TEST_DIR / "unwrapped.fa"
WINDOWS_FA = TEST_DIR / "windows.fa"


class TestCppBackend:
    """Tests to verify C++ backend is working."""

    def test_cpp_backend_available(self):
        """Test that C++ backend is available."""
        # This test will pass if C++ extension is compiled
        assert using_cpp_backend() is True, "C++ backend should be available"

    def test_cpp_build_index_matches_python(self):
        """Test that C++ index matches Python index."""
        if not using_cpp_backend():
            pytest.skip("C++ backend not available")

        from fastaccess._backend import _cpp_build_index

        # Build index with both implementations
        cpp_index = _cpp_build_index(str(WRAPPED_FA))
        py_index = py_build_index(str(WRAPPED_FA))

        # Compare
        assert set(cpp_index.keys()) == set(py_index.keys())

        for name in py_index:
            cpp_entry = cpp_index[name]
            py_entry = py_index[name]

            assert cpp_entry.name == py_entry.name
            assert cpp_entry.description == py_entry.description
            assert cpp_entry.length == py_entry.length
            assert cpp_entry.line_blen == py_entry.line_blen
            assert cpp_entry.line_len == py_entry.line_len
            assert cpp_entry.offset == py_entry.offset

    def test_cpp_fetch_matches_python(self):
        """Test that C++ fetch matches Python fetch for various cases."""
        if not using_cpp_backend():
            pytest.skip("C++ backend not available")

        from fastaccess._backend import _cpp_build_index, _cpp_fetch_subseq

        # Test wrapped file
        cpp_index = _cpp_build_index(str(WRAPPED_FA))
        py_index = py_build_index(str(WRAPPED_FA))

        test_cases = [
            ("seq1", 1, 30),      # Start of sequence
            ("seq1", 50, 70),     # Across line break
            ("seq1", 55, 125),    # Across multiple line breaks
            ("seq1", 180, 180),   # Last base
            ("seq1", 1, 180),     # Full sequence
            ("seq2", 1, 60),      # First line of second seq
            ("seq2", 61, 120),    # Second line of second seq
        ]

        for name, start, stop in test_cases:
            cpp_result = _cpp_fetch_subseq(str(WRAPPED_FA), cpp_index, name, start, stop)
            py_result = py_fetch_subseq(str(WRAPPED_FA), py_index, name, start, stop)
            assert cpp_result == py_result, f"Mismatch for {name}:{start}-{stop}"

    def test_cpp_fetch_unwrapped(self):
        """Test C++ fetch on unwrapped sequences."""
        if not using_cpp_backend():
            pytest.skip("C++ backend not available")

        from fastaccess._backend import _cpp_build_index, _cpp_fetch_subseq

        cpp_index = _cpp_build_index(str(UNWRAPPED_FA))
        py_index = py_build_index(str(UNWRAPPED_FA))

        test_cases = [
            ("single1", 1, 30),
            ("single1", 100, 120),
            ("single1", 1, 180),
        ]

        for name, start, stop in test_cases:
            cpp_result = _cpp_fetch_subseq(str(UNWRAPPED_FA), cpp_index, name, start, stop)
            py_result = py_fetch_subseq(str(UNWRAPPED_FA), py_index, name, start, stop)
            assert cpp_result == py_result, f"Mismatch for {name}:{start}-{stop}"

    def test_cpp_reverse_complement(self):
        """Test C++ reverse complement function."""
        if not using_cpp_backend():
            pytest.skip("C++ backend not available")

        from fastaccess._backend import _cpp_reverse_complement

        # Test basic complement
        assert _cpp_reverse_complement("ACGT") == "ACGT"  # Palindrome
        assert _cpp_reverse_complement("AAAA") == "TTTT"
        assert _cpp_reverse_complement("TTTT") == "AAAA"
        assert _cpp_reverse_complement("GGGG") == "CCCC"
        assert _cpp_reverse_complement("CCCC") == "GGGG"

        # Test actual reverse complement
        assert _cpp_reverse_complement("ACGTACGT") == "ACGTACGT"  # Palindrome
        assert _cpp_reverse_complement("AAAAGGGG") == "CCCCTTTT"
        assert _cpp_reverse_complement("ATCG") == "CGAT"

        # Test IUPAC codes
        assert _cpp_reverse_complement("N") == "N"
        assert _cpp_reverse_complement("RY") == "RY"  # R->Y, Y->R, reversed = RY
        assert _cpp_reverse_complement("SW") == "WS"  # S->S, W->W, reversed = WS

        # Test longer sequence
        seq = "ACGTACGTACGTACGT"
        rc = _cpp_reverse_complement(seq)
        assert len(rc) == len(seq)
        # Verify double reverse complement gives original
        assert _cpp_reverse_complement(rc) == seq

    def test_reverse_complement_via_api(self):
        """Test reverse complement through the FastaStore API."""
        store = FastaStore(str(WRAPPED_FA))

        # Fetch a sequence
        forward = store.fetch("seq1", 1, 60)
        reverse = store.fetch("seq1", 1, 60, reverse_complement=True)

        # Reverse complement of reverse complement should give original
        store_rc_of_rc = store._reverse_complement(reverse)
        assert store_rc_of_rc == forward


class TestCppPerformance:
    """Basic performance sanity checks."""

    def test_cpp_is_faster_than_python(self):
        """Verify C++ backend is at least as fast as Python."""
        if not using_cpp_backend():
            pytest.skip("C++ backend not available")

        import time
        from fastaccess._backend import _cpp_build_index, _cpp_fetch_subseq

        # Build indexes
        cpp_index = _cpp_build_index(str(WRAPPED_FA))
        py_index = py_build_index(str(WRAPPED_FA))

        iterations = 100

        # Time Python
        start = time.perf_counter()
        for _ in range(iterations):
            py_fetch_subseq(str(WRAPPED_FA), py_index, "seq1", 50, 70)
        py_time = time.perf_counter() - start

        # Time C++
        start = time.perf_counter()
        for _ in range(iterations):
            _cpp_fetch_subseq(str(WRAPPED_FA), cpp_index, "seq1", 50, 70)
        cpp_time = time.perf_counter() - start

        # C++ should not be significantly slower
        # (It should actually be faster, but allow some margin)
        assert cpp_time <= py_time * 2, f"C++ ({cpp_time:.4f}s) should not be much slower than Python ({py_time:.4f}s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
