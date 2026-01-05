"""
Unit tests for qc_analyzer module.

Tests thermodynamic calculations: Tm, GC%, hairpin ΔG, dimer ΔG.
"""

import pytest

pytest.importorskip("primer3")

from src.qc_analyzer import (
    calculate_tm,
    calculate_gc,
    calculate_hairpin_dg,
    calculate_self_dimer_dg,
    calculate_cross_dimer_dg,
    analyze_primer,
    analyze_pair,
    get_3prime_end,
    check_gc_clamp,
)
from src.models import Primer, PrimerPair


class TestCalculateTm:
    """Tests for calculate_tm function."""

    def test_empty_sequence(self):
        """Test Tm calculation for empty sequence."""
        assert calculate_tm("") == 0.0

    def test_typical_primer_tm(self):
        """Test Tm for typical 20-mer primer."""
        # 50% GC, 20-mer: expect Tm around 55-65°C
        seq = "ATGCGATCGATCGATCGATC"  # 20 bp, 50% GC
        tm = calculate_tm(seq)

        assert 50.0 < tm < 70.0

    def test_high_gc_primer(self):
        """Test Tm for high GC primer."""
        seq = "GCGCGCGCGCGCGCGCGCGC"  # 100% GC
        tm = calculate_tm(seq)

        # High GC should have higher Tm
        assert tm > 60.0

    def test_low_gc_primer(self):
        """Test Tm for low GC primer."""
        seq = "ATATATATATATATATATATAT"  # 0% GC
        tm = calculate_tm(seq)

        # Low GC should have lower Tm
        assert tm < 55.0

    def test_tm_returns_float(self):
        """Test that Tm is returned as float."""
        tm = calculate_tm("ATGCGATCGATCGATCGATC")
        assert isinstance(tm, float)


class TestCalculateGc:
    """Tests for calculate_gc function."""

    def test_empty_sequence(self):
        """Test GC calculation for empty sequence."""
        assert calculate_gc("") == 0.0

    def test_50_percent_gc(self):
        """Test 50% GC content."""
        seq = "AATTGGCC"  # 50% GC
        gc = calculate_gc(seq)

        assert gc == 50.0

    def test_100_percent_gc(self):
        """Test 100% GC content."""
        gc = calculate_gc("GGCC")

        assert gc == 100.0

    def test_0_percent_gc(self):
        """Test 0% GC content."""
        gc = calculate_gc("AATT")

        assert gc == 0.0

    def test_lowercase_handling(self):
        """Test that lowercase is handled."""
        gc = calculate_gc("ggcc")

        assert gc == 100.0


class TestCalculateHairpinDg:
    """Tests for calculate_hairpin_dg function."""

    def test_empty_sequence(self):
        """Test hairpin ΔG for empty sequence."""
        assert calculate_hairpin_dg("") == 0.0

    def test_short_sequence(self):
        """Test hairpin ΔG for sequence < 4 bp."""
        assert calculate_hairpin_dg("ATG") == 0.0

    def test_hairpin_forming_sequence(self):
        """Test sequence likely to form hairpin."""
        # Self-complementary sequence
        seq = "GCGCGCGCGC"
        dg = calculate_hairpin_dg(seq)

        # Should return a ΔG value (likely negative for hairpin)
        assert isinstance(dg, float)

    def test_non_hairpin_sequence(self):
        """Test sequence unlikely to form hairpin."""
        seq = "ATATATATATATAT"
        dg = calculate_hairpin_dg(seq)

        # AT-rich sequences form weaker structures
        assert isinstance(dg, float)


class TestCalculateSelfDimerDg:
    """Tests for calculate_self_dimer_dg function."""

    def test_empty_sequence(self):
        """Test self-dimer ΔG for empty sequence."""
        assert calculate_self_dimer_dg("") == 0.0

    def test_self_complementary_sequence(self):
        """Test self-complementary sequence."""
        # Palindromic sequence likely to self-dimerize
        seq = "GCGCGCGCGC"
        dg = calculate_self_dimer_dg(seq)

        # Self-complementary should have negative ΔG
        assert dg < 0


class TestCalculateCrossDimerDg:
    """Tests for calculate_cross_dimer_dg function."""

    def test_empty_sequences(self):
        """Test cross-dimer with empty sequences."""
        assert calculate_cross_dimer_dg("", "ATGC") == 0.0
        assert calculate_cross_dimer_dg("ATGC", "") == 0.0

    def test_complementary_sequences(self):
        """Test complementary sequences."""
        seq1 = "ATGCATGCATGC"
        seq2 = "GCATGCATGCAT"
        dg = calculate_cross_dimer_dg(seq1, seq2)

        # Should return ΔG value
        assert isinstance(dg, float)


class TestAnalyzePrimer:
    """Tests for analyze_primer function."""

    def test_analyze_populates_fields(self):
        """Test that analyze_primer populates all QC fields."""
        primer = Primer(
            sequence="ATGCGATCGATCGATCGATC",
            start=0,
            end=20,
            length=20,
            tm=0.0,  # Will be calculated by analyze_primer
            gc_percent=0.0,  # Will be calculated by analyze_primer
        )

        analyzed = analyze_primer(primer)

        assert analyzed.tm > 0
        assert 0 <= analyzed.gc_percent <= 100
        assert isinstance(analyzed.hairpin_dg, float)
        assert isinstance(analyzed.self_dimer_dg, float)
        assert analyzed.three_prime_base == "C"


class TestAnalyzePair:
    """Tests for analyze_pair function."""

    def test_analyze_pair_calculates_metrics(self):
        """Test that analyze_pair calculates pair metrics."""
        forward = Primer(
            sequence="ATGCGATCGATCGATCGATC",
            start=0,
            end=20,
            length=20,
            tm=0.0,  # Will be calculated by analyze_pair
            gc_percent=0.0,
        )
        reverse = Primer(
            sequence="GCTAGCTAGCTAGCTAGCTA",
            start=100,
            end=120,
            length=20,
            tm=0.0,  # Will be calculated by analyze_pair
            gc_percent=0.0,
        )
        pair = PrimerPair(
            forward=forward,
            reverse=reverse,
            product_size=100,
        )

        analyzed = analyze_pair(pair)

        assert analyzed.tm_difference >= 0
        assert isinstance(analyzed.cross_dimer_dg, float)


class TestGet3PrimeEnd:
    """Tests for get_3prime_end function."""

    def test_empty_sequence(self):
        """Test 3' end of empty sequence."""
        assert get_3prime_end("") == ""

    def test_default_length(self):
        """Test default 5 bp 3' end."""
        result = get_3prime_end("ATGCGATCGATC")

        assert result == "CGATC"  # Last 5 chars of "ATGCGATCGATC"
        assert len(result) == 5

    def test_custom_length(self):
        """Test custom length 3' end."""
        result = get_3prime_end("ATGCGATCGATC", length=3)

        assert len(result) == 3

    def test_uppercase_conversion(self):
        """Test lowercase to uppercase conversion."""
        result = get_3prime_end("atgcgatc")

        assert result == result.upper()


class TestCheckGcClamp:
    """Tests for check_gc_clamp function."""

    def test_empty_sequence(self):
        """Test GC clamp check for empty sequence."""
        has_clamp, _ = check_gc_clamp("")

        assert has_clamp is False

    def test_good_gc_clamp(self):
        """Test sequence with good GC clamp (1-2 G/C in last 5)."""
        has_clamp, desc = check_gc_clamp("ATATATATATG")  # 1 G/C in last 5

        assert has_clamp is True
        assert "Good" in desc or "good" in desc.lower()

    def test_no_gc_clamp(self):
        """Test sequence with no GC clamp."""
        has_clamp, desc = check_gc_clamp("ATATATAT")  # 0 G/C in last 5

        assert has_clamp is False
        assert "No GC clamp" in desc or "no" in desc.lower()

    def test_strong_gc_clamp(self):
        """Test sequence with too strong GC clamp."""
        has_clamp, desc = check_gc_clamp("GCGCGCGCGC")  # 5 G/C in last 5

        assert has_clamp is False
        assert "strong" in desc.lower()
