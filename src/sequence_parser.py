"""
Sequence parsing and validation module.

Handles FASTA file parsing and sequence validation.
"""

import re
from io import StringIO
from typing import Dict, List, Optional, Tuple, Union

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


# Valid nucleotide characters (including ambiguity codes)
VALID_NUCLEOTIDES = set("ATGCNatgcn")
STRICT_NUCLEOTIDES = set("ATGCatgc")


def parse_fasta(file_or_text: Union[str, bytes]) -> List[SeqRecord]:
    """
    Parse FASTA input from file content or raw text.

    Args:
        file_or_text: FASTA content as string or bytes

    Returns:
        List of SeqRecord objects

    Raises:
        ValueError: If no valid sequences found
    """
    if isinstance(file_or_text, bytes):
        file_or_text = file_or_text.decode("utf-8")

    # Handle raw sequence (no FASTA header)
    if not file_or_text.strip().startswith(">"):
        # Treat as raw sequence
        clean_seq = re.sub(r"\s+", "", file_or_text)
        if clean_seq:
            return [SeqRecord(Seq(clean_seq.upper()), id="input_sequence", description="User input")]
        raise ValueError("Empty sequence provided")

    # Parse as FASTA
    records = list(SeqIO.parse(StringIO(file_or_text), "fasta"))

    if not records:
        raise ValueError("No valid FASTA sequences found")

    return records


def validate_sequence(seq: str, strict: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate nucleotide sequence.

    Args:
        seq: Sequence string to validate
        strict: If True, only allow A, T, G, C (no N or ambiguity codes)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not seq:
        return False, "Empty sequence"

    if len(seq) < 50:
        return False, f"Sequence too short ({len(seq)} bp). Minimum 50 bp required for primer design."

    valid_chars = STRICT_NUCLEOTIDES if strict else VALID_NUCLEOTIDES
    invalid_chars = set(seq.upper()) - valid_chars

    if invalid_chars:
        return False, f"Invalid characters found: {', '.join(sorted(invalid_chars))}"

    # Check for excessive N content
    n_count = seq.upper().count("N")
    if n_count > len(seq) * 0.1:  # More than 10% N
        return False, f"Too many ambiguous bases (N): {n_count}/{len(seq)} ({n_count/len(seq)*100:.1f}%)"

    return True, None


def get_sequence_stats(seq: str) -> Dict[str, Union[int, float, str]]:
    """
    Calculate basic sequence statistics.

    Args:
        seq: Nucleotide sequence

    Returns:
        Dictionary with sequence statistics
    """
    seq = seq.upper()
    length = len(seq)

    if length == 0:
        return {
            "length": 0,
            "gc_percent": 0.0,
            "a_count": 0,
            "t_count": 0,
            "g_count": 0,
            "c_count": 0,
            "n_count": 0,
            "gc_content": "0.0%",
        }

    a_count = seq.count("A")
    t_count = seq.count("T")
    g_count = seq.count("G")
    c_count = seq.count("C")
    n_count = seq.count("N")

    gc_count = g_count + c_count
    gc_percent = (gc_count / length) * 100

    return {
        "length": length,
        "gc_percent": round(gc_percent, 2),
        "a_count": a_count,
        "t_count": t_count,
        "g_count": g_count,
        "c_count": c_count,
        "n_count": n_count,
        "gc_content": f"{gc_percent:.1f}%",
        "at_content": f"{((a_count + t_count) / length * 100):.1f}%",
    }


def format_sequence_display(seq: str, line_length: int = 60) -> str:
    """
    Format sequence for display with line breaks.

    Args:
        seq: Nucleotide sequence
        line_length: Characters per line

    Returns:
        Formatted sequence string
    """
    seq = seq.upper()
    lines = [seq[i : i + line_length] for i in range(0, len(seq), line_length)]
    return "\n".join(lines)
