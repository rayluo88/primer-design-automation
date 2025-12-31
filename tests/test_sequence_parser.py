"""
Unit tests for sequence_parser module.
"""

import pytest
from Bio.SeqRecord import SeqRecord

from src.sequence_parser import (
    parse_fasta,
    validate_sequence,
    get_sequence_stats,
    format_sequence_display,
)


class TestParseFasta:
    """Tests for parse_fasta function."""

    def test_parse_valid_fasta(self):
        """Test parsing valid FASTA format."""
        fasta = ">test_seq\nATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        records = parse_fasta(fasta)

        assert len(records) == 1
        assert records[0].id == "test_seq"
        assert str(records[0].seq) == "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"

    def test_parse_multi_sequence_fasta(self):
        """Test parsing multi-sequence FASTA."""
        fasta = """>seq1
ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
>seq2
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"""
        records = parse_fasta(fasta)

        assert len(records) == 2
        assert records[0].id == "seq1"
        assert records[1].id == "seq2"

    def test_parse_raw_sequence(self):
        """Test parsing raw sequence without FASTA header."""
        raw_seq = "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        records = parse_fasta(raw_seq)

        assert len(records) == 1
        assert records[0].id == "input_sequence"
        assert str(records[0].seq) == raw_seq.upper()

    def test_parse_bytes_input(self):
        """Test parsing bytes input."""
        fasta_bytes = b">test\nATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        records = parse_fasta(fasta_bytes)

        assert len(records) == 1

    def test_parse_empty_raises_error(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="Empty sequence"):
            parse_fasta("")

    def test_parse_whitespace_only_raises_error(self):
        """Test that whitespace-only input raises ValueError."""
        with pytest.raises(ValueError, match="Empty sequence"):
            parse_fasta("   \n\t  ")


class TestValidateSequence:
    """Tests for validate_sequence function."""

    def test_valid_sequence(self):
        """Test validation of valid sequence."""
        seq = "ATGC" * 20  # 80 bp
        is_valid, error = validate_sequence(seq)

        assert is_valid is True
        assert error is None

    def test_empty_sequence(self):
        """Test validation of empty sequence."""
        is_valid, error = validate_sequence("")

        assert is_valid is False
        assert "Empty sequence" in error

    def test_short_sequence(self):
        """Test validation of too-short sequence."""
        is_valid, error = validate_sequence("ATGC" * 10)  # 40 bp

        assert is_valid is False
        assert "too short" in error.lower()

    def test_invalid_characters(self):
        """Test validation with invalid characters."""
        seq = "ATGCXYZ" + "A" * 50
        is_valid, error = validate_sequence(seq)

        assert is_valid is False
        assert "Invalid characters" in error

    def test_strict_mode_rejects_n(self):
        """Test strict mode rejects N characters."""
        seq = "ATGCN" * 20  # Contains N
        is_valid, error = validate_sequence(seq, strict=True)

        assert is_valid is False
        assert "Invalid characters" in error

    def test_non_strict_allows_n(self):
        """Test non-strict mode allows N characters."""
        seq = "ATGCN" + "ATGC" * 20  # Contains N but < 10%
        is_valid, error = validate_sequence(seq, strict=False)

        assert is_valid is True

    def test_excessive_n_content(self):
        """Test rejection of sequences with >10% N content."""
        seq = "N" * 20 + "ATGC" * 10  # 50% N
        is_valid, error = validate_sequence(seq)

        assert is_valid is False
        assert "ambiguous" in error.lower()


class TestGetSequenceStats:
    """Tests for get_sequence_stats function."""

    def test_basic_stats(self):
        """Test basic sequence statistics."""
        seq = "AATTGGCC" * 10  # 80 bp, 50% GC
        stats = get_sequence_stats(seq)

        assert stats["length"] == 80
        assert stats["a_count"] == 20
        assert stats["t_count"] == 20
        assert stats["g_count"] == 20
        assert stats["c_count"] == 20
        assert stats["gc_percent"] == 50.0

    def test_empty_sequence_stats(self):
        """Test stats for empty sequence."""
        stats = get_sequence_stats("")

        assert stats["length"] == 0
        assert stats["gc_percent"] == 0.0

    def test_gc_content_calculation(self):
        """Test GC content calculation."""
        # 100% GC
        stats = get_sequence_stats("GGCC" * 20)
        assert stats["gc_percent"] == 100.0

        # 0% GC
        stats = get_sequence_stats("AATT" * 20)
        assert stats["gc_percent"] == 0.0

    def test_lowercase_handling(self):
        """Test that lowercase is handled correctly."""
        stats = get_sequence_stats("atgc" * 20)

        assert stats["length"] == 80
        assert stats["a_count"] == 20


class TestFormatSequenceDisplay:
    """Tests for format_sequence_display function."""

    def test_short_sequence_no_break(self):
        """Test short sequence doesn't get line breaks."""
        seq = "ATGC" * 10  # 40 chars
        formatted = format_sequence_display(seq, line_length=60)

        assert "\n" not in formatted

    def test_long_sequence_line_breaks(self):
        """Test long sequence gets line breaks."""
        seq = "ATGC" * 30  # 120 chars
        formatted = format_sequence_display(seq, line_length=60)

        lines = formatted.split("\n")
        assert len(lines) == 2
        assert len(lines[0]) == 60

    def test_uppercase_conversion(self):
        """Test lowercase is converted to uppercase."""
        formatted = format_sequence_display("atgc")

        assert formatted == "ATGC"
