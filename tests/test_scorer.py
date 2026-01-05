"""
Unit tests for scorer module.

Tests the composite scoring algorithm for primer pairs.
"""

import pytest

from src.scorer import (
    calculate_tm_score,
    calculate_gc_score,
    calculate_structure_score,
    calculate_3prime_score,
    calculate_product_score,
    calculate_probe_score,
    calculate_composite_score,
    score_pairs,
    rank_pairs,
    get_score_breakdown,
)
from src.models import Primer, PrimerPair, Probe, QCThresholds


def create_test_primer(
    sequence: str = "ATGCGATCGATCGATCGATC",
    tm: float = 60.0,
    gc_percent: float = 50.0,
    hairpin_dg: float = 0.0,
    self_dimer_dg: float = -5.0,
    three_prime_base: str = "C",
) -> Primer:
    """Create a test primer with specified properties."""
    return Primer(
        sequence=sequence,
        start=0,
        end=len(sequence),
        length=len(sequence),
        tm=tm,
        gc_percent=gc_percent,
        hairpin_dg=hairpin_dg,
        self_dimer_dg=self_dimer_dg,
        three_prime_base=three_prime_base,
    )


def create_test_pair(
    fwd_tm: float = 60.0,
    rev_tm: float = 60.0,
    fwd_gc: float = 50.0,
    rev_gc: float = 50.0,
    cross_dimer_dg: float = -5.0,
    product_size: int = 100,
    fwd_3prime: str = "C",
    rev_3prime: str = "G",
    with_probe: bool = False,
) -> PrimerPair:
    """Create a test primer pair with specified properties."""
    forward = create_test_primer(tm=fwd_tm, gc_percent=fwd_gc, three_prime_base=fwd_3prime)
    reverse = create_test_primer(tm=rev_tm, gc_percent=rev_gc, three_prime_base=rev_3prime)

    pair = PrimerPair(
        forward=forward,
        reverse=reverse,
        product_size=product_size,
        cross_dimer_dg=cross_dimer_dg,
    )
    pair.tm_difference = abs(fwd_tm - rev_tm)

    if with_probe:
        probe = Probe(
            sequence="AC" * 10,
            start=forward.end + 2,
            end=forward.end + 22,
            length=20,
            tm=69.0,
            gc_percent=50.0,
        )
        pair.probe = probe

    return pair


class TestCalculateTmScore:
    """Tests for calculate_tm_score function."""

    def test_optimal_tm_max_score(self):
        """Test that optimal Tm gets high score."""
        pair = create_test_pair(fwd_tm=60.0, rev_tm=60.0)
        thresholds = QCThresholds(tm_optimal=60.0)

        score = calculate_tm_score(pair, thresholds)

        # Perfect Tm should get close to max (25)
        assert score > 20

    def test_suboptimal_tm_lower_score(self):
        """Test that suboptimal Tm gets lower score."""
        pair = create_test_pair(fwd_tm=55.0, rev_tm=55.0)
        thresholds = QCThresholds(tm_optimal=60.0)

        score = calculate_tm_score(pair, thresholds)

        # 5°C from optimal should reduce score
        assert score < 25

    def test_tm_mismatch_penalty(self):
        """Test that Tm mismatch between primers reduces score."""
        pair_matched = create_test_pair(fwd_tm=60.0, rev_tm=60.0)
        pair_mismatched = create_test_pair(fwd_tm=58.0, rev_tm=62.0)
        thresholds = QCThresholds()

        score_matched = calculate_tm_score(pair_matched, thresholds)
        score_mismatched = calculate_tm_score(pair_mismatched, thresholds)

        # Mismatched should score lower
        assert score_matched > score_mismatched


class TestCalculateGcScore:
    """Tests for calculate_gc_score function."""

    def test_optimal_gc_max_score(self):
        """Test that optimal GC gets high score."""
        pair = create_test_pair(fwd_gc=50.0, rev_gc=50.0)
        thresholds = QCThresholds()  # gc_optimal = 50.0

        score = calculate_gc_score(pair, thresholds)

        # Perfect GC should get close to max (15)
        assert score > 13

    def test_suboptimal_gc_lower_score(self):
        """Test that suboptimal GC gets lower score."""
        pair = create_test_pair(fwd_gc=70.0, rev_gc=70.0)
        thresholds = QCThresholds()

        score = calculate_gc_score(pair, thresholds)

        # 20% from optimal should reduce score significantly
        assert score < 15


class TestCalculateStructureScore:
    """Tests for calculate_structure_score function."""

    def test_no_structures_max_score(self):
        """Test that no secondary structures gets max score."""
        forward = create_test_primer(hairpin_dg=0.0, self_dimer_dg=0.0)
        reverse = create_test_primer(hairpin_dg=0.0, self_dimer_dg=0.0)
        pair = PrimerPair(forward=forward, reverse=reverse, product_size=100, cross_dimer_dg=0.0)
        pair.tm_difference = 0

        score = calculate_structure_score(pair, QCThresholds())

        # No structures should get close to max (20)
        assert score >= 18

    def test_strong_hairpin_reduces_score(self):
        """Test that strong hairpin reduces score."""
        forward = create_test_primer(hairpin_dg=-5.0)  # Strong hairpin
        reverse = create_test_primer(hairpin_dg=0.0)
        pair = PrimerPair(forward=forward, reverse=reverse, product_size=100, cross_dimer_dg=0.0)
        pair.tm_difference = 0

        score = calculate_structure_score(pair, QCThresholds())

        # Hairpin fail should zero out structure score
        assert score == 0.0


class TestCalculate3PrimeScore:
    """Tests for calculate_3prime_score function."""

    def test_gc_at_3prime_max_score(self):
        """Test that G/C at 3' end gets max score."""
        pair = create_test_pair(fwd_3prime="G", rev_3prime="C")

        score = calculate_3prime_score(pair, QCThresholds())

        # G and C at 3' should get max (10)
        assert score == 10

    def test_t_at_3prime_low_score(self):
        """Test that T at 3' end gets low score."""
        pair = create_test_pair(fwd_3prime="T", rev_3prime="T")

        score = calculate_3prime_score(pair, QCThresholds())

        # T at both 3' ends should get low score
        assert score == 2  # (2 + 2) * 0.5

    def test_a_at_3prime_medium_score(self):
        """Test that A at 3' end gets medium score."""
        pair = create_test_pair(fwd_3prime="A", rev_3prime="A")

        score = calculate_3prime_score(pair, QCThresholds())

        # A at both 3' ends should get medium score
        assert score == 7  # (7 + 7) * 0.5


class TestCalculateProductScore:
    """Tests for calculate_product_score function."""

    def test_optimal_size_max_score(self):
        """Test that optimal product size gets max score."""
        pair = create_test_pair(product_size=100)
        thresholds = QCThresholds(product_optimal=100)

        score = calculate_product_score(pair, thresholds)

        # Optimal size should get max (5)
        assert score == 5

    def test_size_outside_range_penalty(self):
        """Test that size outside range gets penalty."""
        pair = create_test_pair(product_size=500)  # Way outside typical range
        thresholds = QCThresholds(product_min=70, product_max=200)

        score = calculate_product_score(pair, thresholds)

        # Outside range should have significant penalty
        assert score < 2.5


class TestCalculateProbeScore:
    """Tests for calculate_probe_score function."""

    def test_valid_probe_scores_high(self):
        """Probe meeting rules should score high."""
        pair = create_test_pair(with_probe=True)
        score = calculate_probe_score(pair)

        assert score >= 20

    def test_missing_probe_scores_zero(self):
        """Missing probe should score zero."""
        pair = create_test_pair(with_probe=False)
        score = calculate_probe_score(pair)

        assert score == 0.0

    def test_probe_tm_delta_fail_zeroes_score(self):
        """Failing probe Tm delta should zero out probe score."""
        pair = create_test_pair(with_probe=True)
        pair.probe.tm = pair.primer_avg_tm + 2.0

        score = calculate_probe_score(pair)

        assert score == 0.0


class TestCalculateCompositeScore:
    """Tests for calculate_composite_score function."""

    def test_perfect_primer_high_score(self):
        """Test that 'perfect' primer pair gets high score."""
        pair = create_test_pair(
            fwd_tm=60.0,
            rev_tm=60.0,
            fwd_gc=50.0,
            rev_gc=50.0,
            cross_dimer_dg=0.0,
            product_size=100,
            fwd_3prime="G",
            rev_3prime="C",
            with_probe=True,
        )

        score = calculate_composite_score(pair)

        # Perfect pair should score > 80
        assert score > 80

    def test_score_range(self):
        """Test that score is within 0-100 range."""
        pair = create_test_pair()

        score = calculate_composite_score(pair)

        assert 0 <= score <= 100

    def test_default_thresholds_used(self):
        """Test that default thresholds are used when None."""
        pair = create_test_pair()

        score = calculate_composite_score(pair, None)

        assert isinstance(score, float)


class TestScorePairs:
    """Tests for score_pairs function."""

    def test_scores_all_pairs(self):
        """Test that all pairs get scored."""
        pairs = [create_test_pair() for _ in range(3)]

        scored = score_pairs(pairs)

        assert len(scored) == 3
        assert all(p.composite_score > 0 for p in scored)


class TestRankPairs:
    """Tests for rank_pairs function."""

    def test_ranks_by_score_descending(self):
        """Test that pairs are ranked by score (highest first)."""
        pair1 = create_test_pair()
        pair1.composite_score = 80.0
        pair2 = create_test_pair()
        pair2.composite_score = 90.0
        pair3 = create_test_pair()
        pair3.composite_score = 70.0

        ranked = rank_pairs([pair1, pair2, pair3])

        assert ranked[0].composite_score == 90.0
        assert ranked[0].rank == 1
        assert ranked[1].composite_score == 80.0
        assert ranked[1].rank == 2
        assert ranked[2].composite_score == 70.0
        assert ranked[2].rank == 3


class TestGetScoreBreakdown:
    """Tests for get_score_breakdown function."""

    def test_returns_all_components(self):
        """Test that breakdown includes all score components."""
        pair = create_test_pair()

        breakdown = get_score_breakdown(pair)

        assert "tm_score" in breakdown
        assert "gc_score" in breakdown
        assert "structure_score" in breakdown
        assert "three_prime_score" in breakdown
        assert "product_score" in breakdown
        assert "probe_score" in breakdown
        assert "total" in breakdown
        assert "weights" in breakdown

    def test_components_sum_to_total(self):
        """Test that component scores sum to total (approximately)."""
        pair = create_test_pair()

        breakdown = get_score_breakdown(pair)

        component_sum = (
            breakdown["tm_score"]
            + breakdown["gc_score"]
            + breakdown["structure_score"]
            + breakdown["three_prime_score"]
            + breakdown["product_score"]
            + breakdown["probe_score"]
        )

        # Allow small rounding differences
        assert abs(component_sum - breakdown["total"]) < 1.0
