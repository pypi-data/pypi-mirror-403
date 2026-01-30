#!/usr/bin/env python3
"""
Performance benchmark for fastaccess library comparing Python vs C++ backends.
"""

import time
import tempfile
from pathlib import Path

from fastaccess import using_cpp_backend
from fastaccess.api import FastaStore

# Import Python implementation directly for comparison
from fastaccess.index import build_index as py_build_index
from fastaccess.store import fetch_subseq as py_fetch_subseq


def create_test_fasta(path, num_sequences=10, seq_length=1_000_000):
    """Create a test FASTA file with multiple large sequences."""
    print(f"Creating test FASTA: {num_sequences} sequences × {seq_length:,} bp")
    with open(path, 'w') as f:
        for i in range(num_sequences):
            f.write(f'>seq{i+1} Test sequence {i+1}\n')
            # Write in 60-character lines
            seq = ('ACGT' * (seq_length // 4))[:seq_length]
            for j in range(0, len(seq), 60):
                f.write(seq[j:j+60] + '\n')

    file_size = Path(path).stat().st_size
    print(f"Created file: {file_size / 1024 / 1024:.1f} MB")
    return file_size


def benchmark_index_building(fasta_path):
    """Benchmark index building time for both backends."""
    print("\n--- Index Building ---")

    # Python implementation
    start = time.perf_counter()
    py_index = py_build_index(fasta_path)
    py_elapsed = time.perf_counter() - start
    py_total_bases = sum(e.length for e in py_index.values())

    print(f"Python: {py_elapsed * 1000:.2f} ms ({py_total_bases / py_elapsed / 1_000_000:.1f} Mbp/s)")

    # C++ implementation (via FastaStore which uses C++ if available)
    if using_cpp_backend():
        from fastaccess._backend import _cpp_build_index

        start = time.perf_counter()
        cpp_index = _cpp_build_index(fasta_path)
        cpp_elapsed = time.perf_counter() - start

        print(f"C++:    {cpp_elapsed * 1000:.2f} ms ({py_total_bases / cpp_elapsed / 1_000_000:.1f} Mbp/s)")
        print(f"Speedup: {py_elapsed / cpp_elapsed:.1f}x")
    else:
        print("C++ backend not available")
        cpp_index = None

    # Return FastaStore for other benchmarks
    fa = FastaStore(fasta_path, use_cache=False)
    return fa, py_index, cpp_index


def benchmark_fetching(fa, py_index, cpp_index, fasta_path, num_fetches=1000):
    """Benchmark subsequence fetching for both backends."""
    print("\n--- Subsequence Fetching ---")

    sequences = fa.list_sequences()

    # Prepare queries
    test_cases = [
        ("Small (100 bp)", 1000, 1099, num_fetches),
        ("Medium (10 KB)", 5000, 14999, num_fetches // 10),
        ("Large (100 KB)", 10000, 109999, num_fetches // 100),
    ]

    for name, start, stop, iterations in test_cases:
        print(f"\n{name} × {iterations} fetches:")

        # Python
        start_time = time.perf_counter()
        for i in range(iterations):
            seq_name = sequences[i % len(sequences)]
            py_fetch_subseq(fasta_path, py_index, seq_name, start, stop)
        py_elapsed = time.perf_counter() - start_time
        print(f"  Python: {py_elapsed * 1000:.2f} ms ({py_elapsed / iterations * 1000:.4f} ms/fetch)")

        # C++
        if using_cpp_backend() and cpp_index is not None:
            from fastaccess._backend import _cpp_fetch_subseq

            start_time = time.perf_counter()
            for i in range(iterations):
                seq_name = sequences[i % len(sequences)]
                _cpp_fetch_subseq(fasta_path, cpp_index, seq_name, start, stop)
            cpp_elapsed = time.perf_counter() - start_time
            print(f"  C++:    {cpp_elapsed * 1000:.2f} ms ({cpp_elapsed / iterations * 1000:.4f} ms/fetch)")
            print(f"  Speedup: {py_elapsed / cpp_elapsed:.1f}x")


def benchmark_reverse_complement(num_iterations=10000):
    """Benchmark reverse complement for both backends."""
    print("\n--- Reverse Complement ---")

    # Create test sequence
    test_seq = "ACGTACGT" * 1000  # 8000 bp

    # Python implementation
    def py_reverse_complement(seq):
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
                     'N': 'N', 'R': 'Y', 'Y': 'R', 'S': 'S',
                     'W': 'W', 'K': 'M', 'M': 'K', 'B': 'V',
                     'V': 'B', 'D': 'H', 'H': 'D'}
        return ''.join(complement.get(base, base) for base in reversed(seq))

    print(f"\nReverse complement of {len(test_seq)} bp × {num_iterations}:")

    # Python
    start = time.perf_counter()
    for _ in range(num_iterations):
        py_reverse_complement(test_seq)
    py_elapsed = time.perf_counter() - start
    print(f"  Python: {py_elapsed * 1000:.2f} ms ({py_elapsed / num_iterations * 1000:.4f} ms/call)")

    # C++
    if using_cpp_backend():
        from fastaccess._backend import _cpp_reverse_complement

        start = time.perf_counter()
        for _ in range(num_iterations):
            _cpp_reverse_complement(test_seq)
        cpp_elapsed = time.perf_counter() - start
        print(f"  C++:    {cpp_elapsed * 1000:.2f} ms ({cpp_elapsed / num_iterations * 1000:.4f} ms/call)")
        print(f"  Speedup: {py_elapsed / cpp_elapsed:.1f}x")


def main():
    """Run benchmarks."""
    print("=" * 60)
    print("fastaccess Performance Benchmark")
    print("=" * 60)
    print(f"C++ backend available: {using_cpp_backend()}")

    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fa', delete=False) as f:
        temp_path = f.name

    try:
        # Create test data: 10 sequences of 1 MB each = ~10 MB file
        file_size = create_test_fasta(temp_path, num_sequences=10, seq_length=1_000_000)

        # Benchmark index building
        fa, py_index, cpp_index = benchmark_index_building(temp_path)

        # Benchmark fetching
        benchmark_fetching(fa, py_index, cpp_index, temp_path, num_fetches=1000)

        # Benchmark reverse complement
        benchmark_reverse_complement(num_iterations=10000)

        print("\n" + "=" * 60)
        print("Benchmark complete!")
        print("=" * 60)

    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)
        cache_path = Path(temp_path + '.fidx')
        if cache_path.exists():
            cache_path.unlink()


if __name__ == "__main__":
    main()
