# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
# Install with C++ backend (development)
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest fastaccess/tests/

# Run a single test file
pytest fastaccess/tests/test_fastaccess.py -v

# Run a specific test
pytest fastaccess/tests/test_fastaccess.py::TestWrappedFasta::test_index_building -v

# Type checking
mypy fastaccess/
```

## Architecture

**Dual Backend System**: The library provides identical functionality via pure Python (stdlib only) or an optional C++ backend for performance. The backend is selected automatically at import time.

```
fastaccess/
├── api.py          # FastaStore class - main public interface, handles caching
├── _backend.py     # Backend detection, imports C++ or sets fallbacks to None
├── index.py        # Python: Entry dataclass, build_index() parser
├── store.py        # Python: fetch_subseq() with byte-level seeking

src/fastaccess_cpp/ # C++ backend (pybind11)
├── index.cpp       # Memory-mapped index building
├── store.cpp       # Fetch operations
├── complement.cpp  # Reverse complement with lookup table
├── gzip_utils.cpp  # Gzip decompression
└── bindings.cpp    # pybind11 Python bindings
```

**Key Design Patterns**:

1. **Backend Selection** (`_backend.py`): Tries to import `_fastaccess_cpp`, sets `_USE_CPP=True/False`. All other modules import from `_backend` to avoid circular imports.

2. **Index Structure**: Each FASTA sequence gets an `Entry` with byte offsets enabling O(1) seek to any position. For wrapped sequences (60bp/line), math converts base position to byte offset accounting for newlines.

3. **Cache System** (`api.py`): JSON `.fidx` files store index data with FASTA mtime for invalidation. Cache can use custom directory for read-only FASTA locations.

4. **Gzip Handling**: Gzip files are fully decompressed to `BytesIO` for random access (gzip doesn't support seeking). The `_open_file()` helper in `index.py` handles this transparently.

## Testing

Test fixtures are in `fastaccess/tests/`: `wrapped.fa`, `unwrapped.fa`, `windows.fa` (CRLF), and gzip variants. Tests verify Python and C++ backends produce identical output.
