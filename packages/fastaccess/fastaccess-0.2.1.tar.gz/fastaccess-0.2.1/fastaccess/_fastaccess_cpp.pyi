"""Type stubs for the C++ backend module."""

from typing import Dict, List, Tuple

class Entry:
    """Index entry for a single FASTA record."""

    name: str
    """Sequence name (from header)."""

    description: str
    """Full description text after name."""

    length: int
    """Total number of bases in the sequence."""

    line_blen: int
    """Bases per full line; 0 if unwrapped (single line)."""

    line_len: int
    """Bytes per line including newline(s); 0 if unwrapped."""

    offset: int
    """Byte offset where sequence data starts."""

    def __init__(
        self,
        name: str = ...,
        description: str = ...,
        length: int = ...,
        line_blen: int = ...,
        line_len: int = ...,
        offset: int = ...,
    ) -> None: ...

    def __repr__(self) -> str: ...

def build_index(path: str) -> Dict[str, Entry]:
    """
    Build an in-memory index of all FASTA records in the file.

    Args:
        path: Path to the FASTA file

    Returns:
        Dictionary mapping sequence name to Entry with index information

    Raises:
        RuntimeError: If file cannot be opened
    """
    ...

def fetch_subseq(
    path: str,
    index: Dict[str, Entry],
    name: str,
    start: int,
    stop: int,
) -> str:
    """
    Fetch a subsequence using 1-based inclusive coordinates.

    Args:
        path: Path to the FASTA file
        index: Pre-built index dictionary
        name: Sequence name
        start: Start position (1-based, inclusive)
        stop: Stop position (1-based, inclusive)

    Returns:
        Uppercase string containing the requested subsequence

    Raises:
        RuntimeError: If sequence name not found or coordinates invalid
    """
    ...

def fetch_many(
    path: str,
    index: Dict[str, Entry],
    queries: List[Tuple[str, int, int]],
) -> List[str]:
    """
    Fetch multiple subsequences in batch.

    Args:
        path: Path to the FASTA file
        index: Pre-built index dictionary
        queries: List of (name, start, stop) tuples

    Returns:
        List of uppercase strings, one for each query
    """
    ...

def reverse_complement(seq: str) -> str:
    """
    Get the reverse complement of a DNA sequence.

    Handles standard IUPAC ambiguity codes:
    A<->T, G<->C, R<->Y, S<->S, W<->W, K<->M, B<->V, D<->H, N<->N

    Args:
        seq: Input sequence (uppercase)

    Returns:
        Reverse complement of the sequence
    """
    ...

__version__: str
"""Version of the C++ backend module."""
