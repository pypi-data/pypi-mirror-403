"""
Tests for gzip-compressed FASTA file support.
"""

import gzip
import os
import tempfile
from pathlib import Path

import pytest

from fastaccess.api import FastaStore
from fastaccess._backend import using_cpp_backend

# Test fixtures paths
TEST_DIR = Path(__file__).parent
WRAPPED_FA = TEST_DIR / "wrapped.fa"
WRAPPED_GZ = TEST_DIR / "wrapped.fa.gz"
UNWRAPPED_FA = TEST_DIR / "unwrapped.fa"
UNWRAPPED_GZ = TEST_DIR / "unwrapped.fa.gz"


class TestGzipWrappedFasta:
    """Tests for gzip-compressed wrapped FASTA files."""

    def setup_method(self):
        """Initialize FastaStore for each test."""
        # Skip if gzip file doesn't exist
        if not WRAPPED_GZ.exists():
            pytest.skip("wrapped.fa.gz not found")
        self.store = FastaStore(str(WRAPPED_GZ))
        self.uncompressed_store = FastaStore(str(WRAPPED_FA))

    def test_index_building(self):
        """Test that index is built correctly from gzip file."""
        assert "seq1" in self.store.index
        assert "seq2" in self.store.index

        entry1 = self.store.index["seq1"]
        assert entry1.length == 180  # 3 lines * 60 bp
        assert entry1.line_blen == 60
        assert entry1.line_len == 61  # 60 bp + 1 newline

        entry2 = self.store.index["seq2"]
        assert entry2.length == 240  # 4 lines * 60 bp

    def test_fetch_matches_uncompressed(self):
        """Test that fetching from gzip matches uncompressed results."""
        # Test various regions
        regions = [
            ("seq1", 1, 30),
            ("seq1", 50, 70),  # across line break
            ("seq1", 1, 180),  # full sequence
            ("seq2", 1, 60),
            ("seq2", 61, 120),
        ]

        for name, start, stop in regions:
            gz_seq = self.store.fetch(name, start, stop)
            normal_seq = self.uncompressed_store.fetch(name, start, stop)
            assert gz_seq == normal_seq, f"Mismatch for {name}:{start}-{stop}"

    def test_fetch_many_gzip(self):
        """Test batch fetching from gzip files."""
        queries = [
            ("seq1", 1, 60),
            ("seq1", 61, 120),
            ("seq2", 1, 60),
            ("seq2", 61, 120),
        ]

        gz_results = self.store.fetch_many(queries)
        normal_results = self.uncompressed_store.fetch_many(queries)

        assert len(gz_results) == len(normal_results)
        for gz, normal in zip(gz_results, normal_results):
            assert gz == normal


class TestGzipUnwrappedFasta:
    """Tests for gzip-compressed unwrapped FASTA files."""

    def setup_method(self):
        """Initialize FastaStore for each test."""
        if not UNWRAPPED_GZ.exists():
            pytest.skip("unwrapped.fa.gz not found")
        self.store = FastaStore(str(UNWRAPPED_GZ))
        self.uncompressed_store = FastaStore(str(UNWRAPPED_FA))

    def test_index_building(self):
        """Test that unwrapped gzip sequences are indexed correctly."""
        entry = self.store.index["single1"]
        assert entry.line_blen == 0  # Unwrapped
        assert entry.line_len == 0
        assert entry.length == 180

    def test_fetch_matches_uncompressed(self):
        """Test that fetching from gzip matches uncompressed results."""
        regions = [
            ("single1", 1, 30),
            ("single1", 100, 120),
            ("single1", 1, 180),
        ]

        for name, start, stop in regions:
            gz_seq = self.store.fetch(name, start, stop)
            normal_seq = self.uncompressed_store.fetch(name, start, stop)
            assert gz_seq == normal_seq, f"Mismatch for {name}:{start}-{stop}"


class TestGzipDynamicCreation:
    """Tests using dynamically created gzip files."""

    def test_create_and_read_gzip(self):
        """Test creating a gzip file on the fly and reading it."""
        fasta_content = b">testseq Description here\nACGTACGTACGTACGT\nTGCATGCATGCATGCA\n"

        with tempfile.NamedTemporaryFile(suffix='.fa.gz', delete=False) as f:
            temp_path = f.name
            with gzip.open(f, 'wb') as gz:
                gz.write(fasta_content)

        try:
            store = FastaStore(temp_path)

            assert "testseq" in store.index
            entry = store.index["testseq"]
            assert entry.length == 32
            assert entry.description == "Description here"

            seq = store.fetch("testseq", 1, 16)
            assert seq == "ACGTACGTACGTACGT"

            seq = store.fetch("testseq", 17, 32)
            assert seq == "TGCATGCATGCATGCA"
        finally:
            os.unlink(temp_path)
            # Clean up cache file if created
            cache_path = temp_path + '.fidx'
            if os.path.exists(cache_path):
                os.unlink(cache_path)

    def test_gzip_reverse_complement(self):
        """Test reverse complement with gzip files."""
        fasta_content = b">testseq\nACGT\n"

        with tempfile.NamedTemporaryFile(suffix='.fa.gz', delete=False) as f:
            temp_path = f.name
            with gzip.open(f, 'wb') as gz:
                gz.write(fasta_content)

        try:
            store = FastaStore(temp_path)
            seq = store.fetch("testseq", 1, 4, reverse_complement=True)
            assert seq == "ACGT"  # ACGT reverse complement is ACGT
        finally:
            os.unlink(temp_path)
            cache_path = temp_path + '.fidx'
            if os.path.exists(cache_path):
                os.unlink(cache_path)


class TestGzipEdgeCases:
    """Edge case tests for gzip support."""

    def test_empty_description(self):
        """Test gzip file with no description."""
        fasta_content = b">seqname\nACGT\n"

        with tempfile.NamedTemporaryFile(suffix='.fa.gz', delete=False) as f:
            temp_path = f.name
            with gzip.open(f, 'wb') as gz:
                gz.write(fasta_content)

        try:
            store = FastaStore(temp_path)
            assert store.index["seqname"].description == ""
        finally:
            os.unlink(temp_path)
            cache_path = temp_path + '.fidx'
            if os.path.exists(cache_path):
                os.unlink(cache_path)

    def test_single_base_fetch_gzip(self):
        """Test fetching single base from gzip file."""
        fasta_content = b">seq\nACGT\n"

        with tempfile.NamedTemporaryFile(suffix='.fa.gz', delete=False) as f:
            temp_path = f.name
            with gzip.open(f, 'wb') as gz:
                gz.write(fasta_content)

        try:
            store = FastaStore(temp_path)
            assert store.fetch("seq", 1, 1) == "A"
            assert store.fetch("seq", 2, 2) == "C"
            assert store.fetch("seq", 3, 3) == "G"
            assert store.fetch("seq", 4, 4) == "T"
        finally:
            os.unlink(temp_path)
            cache_path = temp_path + '.fidx'
            if os.path.exists(cache_path):
                os.unlink(cache_path)


def test_backend_info():
    """Print which backend is being used for gzip tests."""
    print(f"\nUsing C++ backend: {using_cpp_backend()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
