"""
Primer design engine using Primer3.

Wraps primer3-py library for primer pair generation.
"""

from typing import Any, Dict, List, Optional

import primer3

from .models import Primer, PrimerPair, Probe, QCThresholds


# Default Primer3 settings optimized for qPCR
DEFAULT_PRIMER3_SETTINGS: Dict[str, Any] = {
    "PRIMER_OPT_SIZE": 20,
    "PRIMER_MIN_SIZE": 18,
    "PRIMER_MAX_SIZE": 25,
    "PRIMER_OPT_TM": 60.0,
    "PRIMER_MIN_TM": 58.0,
    "PRIMER_MAX_TM": 62.0,
    "PRIMER_MIN_GC": 40.0,
    "PRIMER_MAX_GC": 60.0,
    "PRIMER_MAX_POLY_X": 4,
    "PRIMER_MAX_SELF_ANY": 8,
    "PRIMER_MAX_SELF_END": 3,
    "PRIMER_PAIR_MAX_COMPL_ANY": 8,
    "PRIMER_PAIR_MAX_COMPL_END": 3,
    "PRIMER_PRODUCT_SIZE_RANGE": [[70, 200]],
    "PRIMER_NUM_RETURN": 10,
    "PRIMER_THERMODYNAMIC_OLIGO_ALIGNMENT": 1,
    "PRIMER_THERMODYNAMIC_TEMPLATE_ALIGNMENT": 0,
}


def design_primers(
    sequence: str,
    settings: Optional[Dict[str, Any]] = None,
    num_return: int = 10,
) -> List[PrimerPair]:
    """
    Design primer pairs for a target sequence using Primer3.

    Args:
        sequence: Target nucleotide sequence
        settings: Optional Primer3 settings override
        num_return: Number of primer pairs to return

    Returns:
        List of PrimerPair objects

    Raises:
        ValueError: If sequence is too short or invalid
    """
    if len(sequence) < 50:
        raise ValueError(f"Sequence too short ({len(sequence)} bp). Minimum 50 bp required.")

    # Merge settings with defaults
    primer3_settings = DEFAULT_PRIMER3_SETTINGS.copy()
    if settings:
        primer3_settings.update(settings)
    primer3_settings["PRIMER_NUM_RETURN"] = num_return

    # Prepare sequence input
    seq_args = {
        "SEQUENCE_ID": "target",
        "SEQUENCE_TEMPLATE": sequence.upper(),
    }

    # Run Primer3
    try:
        result = primer3.bindings.design_primers(seq_args, primer3_settings)
    except Exception as e:
        raise ValueError(f"Primer3 error: {str(e)}")

    # Parse results into PrimerPair objects
    primer_pairs = _parse_primer3_results(result)

    return primer_pairs


def _parse_primer3_results(result: Dict[str, Any]) -> List[PrimerPair]:
    """
    Parse Primer3 output into PrimerPair objects.

    Args:
        result: Raw Primer3 result dictionary

    Returns:
        List of PrimerPair objects
    """
    pairs = []
    num_returned = result.get("PRIMER_PAIR_NUM_RETURNED", 0)

    for i in range(num_returned):
        try:
            # Extract forward primer data
            fwd_seq = result.get(f"PRIMER_LEFT_{i}_SEQUENCE", "")
            fwd_pos = result.get(f"PRIMER_LEFT_{i}", (0, 0))
            fwd_tm = result.get(f"PRIMER_LEFT_{i}_TM", 0.0)
            fwd_gc = result.get(f"PRIMER_LEFT_{i}_GC_PERCENT", 0.0)
            fwd_hairpin = result.get(f"PRIMER_LEFT_{i}_HAIRPIN_TH", 0.0)
            fwd_self_any = result.get(f"PRIMER_LEFT_{i}_SELF_ANY_TH", 0.0)

            forward = Primer(
                sequence=fwd_seq,
                start=fwd_pos[0],
                end=fwd_pos[0] + fwd_pos[1],
                length=fwd_pos[1],
                tm=fwd_tm,
                gc_percent=fwd_gc,
                hairpin_dg=_th_to_dg(fwd_hairpin),
                self_dimer_dg=_th_to_dg(fwd_self_any),
            )

            # Extract reverse primer data
            rev_seq = result.get(f"PRIMER_RIGHT_{i}_SEQUENCE", "")
            rev_pos = result.get(f"PRIMER_RIGHT_{i}", (0, 0))
            rev_tm = result.get(f"PRIMER_RIGHT_{i}_TM", 0.0)
            rev_gc = result.get(f"PRIMER_RIGHT_{i}_GC_PERCENT", 0.0)
            rev_hairpin = result.get(f"PRIMER_RIGHT_{i}_HAIRPIN_TH", 0.0)
            rev_self_any = result.get(f"PRIMER_RIGHT_{i}_SELF_ANY_TH", 0.0)

            reverse = Primer(
                sequence=rev_seq,
                start=rev_pos[0] - rev_pos[1] + 1,
                end=rev_pos[0] + 1,
                length=rev_pos[1],
                tm=rev_tm,
                gc_percent=rev_gc,
                hairpin_dg=_th_to_dg(rev_hairpin),
                self_dimer_dg=_th_to_dg(rev_self_any),
            )

            # Extract pair-level data
            product_size = result.get(f"PRIMER_PAIR_{i}_PRODUCT_SIZE", 0)
            pair_compl = result.get(f"PRIMER_PAIR_{i}_COMPL_ANY_TH", 0.0)

            pair = PrimerPair(
                forward=forward,
                reverse=reverse,
                product_size=product_size,
                cross_dimer_dg=_th_to_dg(pair_compl),
            )

            pairs.append(pair)

        except (KeyError, IndexError, TypeError):
            continue

    return pairs


def _th_to_dg(th_value: float) -> float:
    """
    Convert Primer3 thermodynamic score to approximate ΔG.

    Primer3 returns Tm values for secondary structures.
    We approximate ΔG using: ΔG ≈ -(Tm - 25) * 0.3

    This is a rough approximation for ranking purposes.
    """
    if th_value <= 0:
        return 0.0
    # Higher Tm = more stable structure = more negative ΔG
    return -((th_value - 25) * 0.3)


def get_primer3_settings_from_thresholds(thresholds: QCThresholds) -> Dict[str, Any]:
    """
    Convert QCThresholds to Primer3 settings.

    Args:
        thresholds: QCThresholds object

    Returns:
        Dictionary of Primer3 settings
    """
    return {
        "PRIMER_OPT_SIZE": thresholds.length_optimal,
        "PRIMER_MIN_SIZE": thresholds.length_min,
        "PRIMER_MAX_SIZE": thresholds.length_max,
        "PRIMER_OPT_TM": thresholds.tm_optimal,
        "PRIMER_MIN_TM": thresholds.tm_min,
        "PRIMER_MAX_TM": thresholds.tm_max,
        "PRIMER_MIN_GC": thresholds.gc_min,
        "PRIMER_MAX_GC": thresholds.gc_max,
        "PRIMER_PRODUCT_SIZE_RANGE": [[thresholds.product_min, thresholds.product_max]],
    }


# -----------------------------------------------------------------------------
# TaqMan Probe Design
# -----------------------------------------------------------------------------

def design_probe(
    sequence: str,
    pair: PrimerPair,
    min_length: int = 20,
    max_length: int = 30,
    target_tm_delta: float = 9.0,
) -> Optional[Probe]:
    """
    Design a TaqMan probe for a primer pair.

    The probe should:
    - Be positioned between forward and reverse primers
    - Have Tm 8-10°C higher than primer average
    - Preferably not start with G (quenches FAM)
    - Have GC content 40-60%

    Args:
        sequence: Full target sequence
        pair: PrimerPair containing forward and reverse primers
        min_length: Minimum probe length (default 20)
        max_length: Maximum probe length (default 30)
        target_tm_delta: Target Tm above primer average (default 9°C)

    Returns:
        Best Probe candidate, or None if no suitable probe found
    """
    # Define the probe search region (between primers, with margin)
    fwd_end = pair.forward.end
    rev_start = pair.reverse.start

    # Ensure there's room for a probe
    if rev_start - fwd_end < min_length + 4:
        return None

    # Search region with small margins
    search_start = fwd_end + 2
    search_end = rev_start - 2

    target_tm = pair.primer_avg_tm + target_tm_delta
    candidates: List[tuple] = []  # (score, probe)

    # Try different probe lengths and positions
    for length in range(min_length, min(max_length + 1, search_end - search_start + 1)):
        for start in range(search_start, search_end - length + 1):
            probe_seq = sequence[start:start + length].upper()

            # Skip if contains N
            if "N" in probe_seq:
                continue

            # Calculate Tm using Primer3
            try:
                tm = primer3.calc_tm(probe_seq)
            except Exception:
                continue

            # Calculate GC content
            gc_count = probe_seq.count("G") + probe_seq.count("C")
            gc_percent = (gc_count / length) * 100

            # Score the probe candidate
            score = _score_probe_candidate(
                tm=tm,
                gc_percent=gc_percent,
                five_prime_base=probe_seq[0],
                target_tm=target_tm,
            )

            probe = Probe(
                sequence=probe_seq,
                start=start,
                end=start + length,
                length=length,
                tm=tm,
                gc_percent=gc_percent,
            )

            candidates.append((score, probe))

    if not candidates:
        return None

    # Return the best probe (highest score)
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _score_probe_candidate(
    tm: float,
    gc_percent: float,
    five_prime_base: str,
    target_tm: float,
) -> float:
    """
    Score a probe candidate (higher = better).

    Args:
        tm: Probe melting temperature
        gc_percent: GC content percentage
        five_prime_base: First base of probe
        target_tm: Target Tm (primer avg + 8-10°C)

    Returns:
        Score value (0-100)
    """
    score = 50.0  # Base score

    # Tm scoring (target is primer_avg + 8-10°C)
    tm_diff = abs(tm - target_tm)
    if tm_diff <= 1.0:
        score += 25
    elif tm_diff <= 2.0:
        score += 15
    elif tm_diff <= 4.0:
        score += 5
    else:
        score -= 10

    # GC scoring (optimal 45-55%)
    gc_optimal = 50.0
    gc_diff = abs(gc_percent - gc_optimal)
    if gc_diff <= 5:
        score += 15
    elif gc_diff <= 10:
        score += 10
    elif gc_diff <= 15:
        score += 5

    # 5' base scoring (avoid G)
    if five_prime_base == "G":
        score -= 20  # Penalize G at 5' end
    elif five_prime_base in ("A", "C"):
        score += 10  # Prefer A or C

    return score


def design_probes_for_pairs(
    sequence: str,
    pairs: List[PrimerPair],
) -> List[PrimerPair]:
    """
    Design probes for all primer pairs.

    Args:
        sequence: Full target sequence
        pairs: List of PrimerPair objects

    Returns:
        Same list with probe field populated where possible
    """
    for pair in pairs:
        probe = design_probe(sequence, pair)
        pair.probe = probe
    return pairs
