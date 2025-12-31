"""
Composite scoring algorithm for primer pairs.

Weights reflect importance for PCR success:
- Tm matching: 25% (critical for annealing)
- GC content: 15% (affects stability)
- Secondary structures: 30% (dimers kill efficiency)
- 3' end quality: 20% (specificity)
- Product size: 10% (practical consideration)
"""

from typing import List

from .models import PrimerPair, QCThresholds


def calculate_tm_score(pair: PrimerPair, thresholds: QCThresholds) -> float:
    """
    Calculate Tm score component (max 25 points).

    Scores based on:
    - Average Tm distance from optimal
    - Tm difference between primers (penalty)
    """
    tm_avg = (pair.forward.tm + pair.reverse.tm) / 2

    # Distance from optimal (closer = better)
    tm_distance = abs(tm_avg - thresholds.tm_optimal)
    base_score = 25 * max(0, 1 - tm_distance / 10)

    # Penalty for Tm mismatch between primers
    mismatch_penalty = 5 * min(1, pair.tm_difference / thresholds.tm_diff_warn)

    return max(0, base_score - mismatch_penalty)


def calculate_gc_score(pair: PrimerPair, thresholds: QCThresholds) -> float:
    """
    Calculate GC content score component (max 15 points).

    Scores based on average GC distance from optimal (50%).
    """
    gc_avg = (pair.forward.gc_percent + pair.reverse.gc_percent) / 2
    gc_optimal = thresholds.gc_optimal

    # Distance from optimal (closer = better)
    gc_distance = abs(gc_avg - gc_optimal)
    score = 15 * max(0, 1 - gc_distance / 30)

    return score


def calculate_structure_score(pair: PrimerPair, thresholds: QCThresholds) -> float:
    """
    Calculate secondary structure score component (max 30 points).

    Penalizes:
    - Hairpin formation
    - Self-dimer formation
    - Cross-dimer formation
    """
    score = 30.0

    # Hairpin penalties (10 points max penalty)
    fwd_hairpin = pair.forward.hairpin_dg
    rev_hairpin = pair.reverse.hairpin_dg
    worst_hairpin = min(fwd_hairpin, rev_hairpin)

    if worst_hairpin < thresholds.hairpin_dg_max:
        # More negative = worse
        penalty = min(10, abs(worst_hairpin - thresholds.hairpin_dg_max) * 2)
        score -= penalty

    # Self-dimer penalties (10 points max penalty)
    fwd_self = pair.forward.self_dimer_dg
    rev_self = pair.reverse.self_dimer_dg
    worst_self = min(fwd_self, rev_self)

    if worst_self < thresholds.self_dimer_dg_max:
        penalty = min(10, abs(worst_self - thresholds.self_dimer_dg_max) * 1)
        score -= penalty

    # Cross-dimer penalty (10 points max penalty)
    if pair.cross_dimer_dg < thresholds.cross_dimer_dg_max:
        penalty = min(10, abs(pair.cross_dimer_dg - thresholds.cross_dimer_dg_max) * 1)
        score -= penalty

    return max(0, score)


def calculate_3prime_score(pair: PrimerPair, thresholds: QCThresholds) -> float:
    """
    Calculate 3' end quality score component (max 20 points).

    Rewards G/C at 3' end, penalizes T.
    """
    score = 0.0

    for primer in [pair.forward, pair.reverse]:
        base = primer.three_prime_base.upper()
        if base in thresholds.preferred_3prime:
            score += 10  # G or C at 3' = full points
        elif base in thresholds.avoid_3prime:
            score += 2  # T at 3' = minimal points
        else:
            score += 7  # A at 3' = partial points

    return score


def calculate_product_score(pair: PrimerPair, thresholds: QCThresholds) -> float:
    """
    Calculate product size score component (max 10 points).

    Scores based on distance from optimal product size.
    """
    size = pair.product_size
    optimal = thresholds.product_optimal

    # Distance from optimal
    size_diff = abs(size - optimal)

    # Normalize by range
    range_size = max(thresholds.product_max - thresholds.product_min, 1)
    score = 10 * max(0, 1 - size_diff / range_size)

    # Penalty if outside acceptable range
    if size < thresholds.product_min or size > thresholds.product_max:
        score *= 0.5

    return score


def calculate_composite_score(pair: PrimerPair, thresholds: QCThresholds = None) -> float:
    """
    Calculate composite score (0-100) for primer pair.

    Higher = better.

    Args:
        pair: PrimerPair to score
        thresholds: QC thresholds (uses defaults if None)

    Returns:
        Composite score (0-100)
    """
    if thresholds is None:
        thresholds = QCThresholds()

    tm_score = calculate_tm_score(pair, thresholds)
    gc_score = calculate_gc_score(pair, thresholds)
    structure_score = calculate_structure_score(pair, thresholds)
    three_prime_score = calculate_3prime_score(pair, thresholds)
    product_score = calculate_product_score(pair, thresholds)

    total = tm_score + gc_score + structure_score + three_prime_score + product_score

    return float(round(max(0, min(100, total)), 1))


def score_pairs(pairs: List[PrimerPair], thresholds: QCThresholds = None) -> List[PrimerPair]:
    """
    Score all primer pairs.

    Args:
        pairs: List of PrimerPair objects
        thresholds: QC thresholds (uses defaults if None)

    Returns:
        List of PrimerPair with composite_score populated
    """
    if thresholds is None:
        thresholds = QCThresholds()

    for pair in pairs:
        pair.composite_score = calculate_composite_score(pair, thresholds)

    return pairs


def rank_pairs(pairs: List[PrimerPair]) -> List[PrimerPair]:
    """
    Sort and rank primer pairs by composite score.

    Args:
        pairs: List of scored PrimerPair objects

    Returns:
        List sorted by score (descending) with rank assigned
    """
    # Sort by score (highest first)
    sorted_pairs = sorted(pairs, key=lambda p: p.composite_score, reverse=True)

    # Assign ranks
    for i, pair in enumerate(sorted_pairs, start=1):
        pair.rank = i

    return sorted_pairs


def get_score_breakdown(pair: PrimerPair, thresholds: QCThresholds = None) -> dict:
    """
    Get detailed score breakdown for a primer pair.

    Args:
        pair: PrimerPair to analyze
        thresholds: QC thresholds

    Returns:
        Dictionary with score components
    """
    if thresholds is None:
        thresholds = QCThresholds()

    return {
        "tm_score": round(calculate_tm_score(pair, thresholds), 1),
        "gc_score": round(calculate_gc_score(pair, thresholds), 1),
        "structure_score": round(calculate_structure_score(pair, thresholds), 1),
        "three_prime_score": round(calculate_3prime_score(pair, thresholds), 1),
        "product_score": round(calculate_product_score(pair, thresholds), 1),
        "total": round(calculate_composite_score(pair, thresholds), 1),
        "max_possible": 100,
        "weights": {
            "tm": "25%",
            "gc": "15%",
            "structure": "30%",
            "three_prime": "20%",
            "product": "10%",
        },
    }
