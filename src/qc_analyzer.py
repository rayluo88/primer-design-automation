"""
Quality control analyzer for primers.

Calculates thermodynamic properties and QC metrics.
"""

from typing import Tuple

import primer3

from .models import Primer, PrimerPair, Probe


def calculate_tm(sequence: str, mv_conc: float = 50.0, dv_conc: float = 1.5, dntp_conc: float = 0.2, dna_conc: float = 250.0) -> float:
    """
    Calculate melting temperature using nearest-neighbor method.

    Args:
        sequence: Primer sequence
        mv_conc: Monovalent cation concentration (mM)
        dv_conc: Divalent cation concentration (mM)
        dntp_conc: dNTP concentration (mM)
        dna_conc: DNA concentration (nM)

    Returns:
        Melting temperature in °C
    """
    if not sequence:
        return 0.0

    try:
        tm = primer3.calc_tm(
            sequence.upper(),
            mv_conc=mv_conc,
            dv_conc=dv_conc,
            dntp_conc=dntp_conc,
            dna_conc=dna_conc,
        )
        return round(tm, 2)
    except Exception:
        # Fallback to basic calculation
        return _basic_tm(sequence)


def _basic_tm(sequence: str) -> float:
    """
    Basic Tm calculation (Wallace rule for short oligos, adjusted for longer).

    For primers < 14 bp: Tm = 2(A+T) + 4(G+C)
    For primers >= 14 bp: Tm = 64.9 + 41*(G+C-16.4)/(A+T+G+C)
    """
    seq = sequence.upper()
    a = seq.count("A")
    t = seq.count("T")
    g = seq.count("G")
    c = seq.count("C")
    length = len(seq)

    if length < 14:
        return float(2 * (a + t) + 4 * (g + c))
    else:
        gc = g + c
        return round(64.9 + 41 * (gc - 16.4) / length, 2)


def calculate_gc(sequence: str) -> float:
    """
    Calculate GC content percentage.

    Args:
        sequence: Nucleotide sequence

    Returns:
        GC percentage (0-100)
    """
    if not sequence:
        return 0.0

    seq = sequence.upper()
    gc_count = seq.count("G") + seq.count("C")
    return round((gc_count / len(seq)) * 100, 2)


def calculate_hairpin_dg(sequence: str) -> float:
    """
    Calculate hairpin formation ΔG.

    Args:
        sequence: Primer sequence

    Returns:
        ΔG in kcal/mol (more negative = stronger hairpin)
    """
    if not sequence or len(sequence) < 4:
        return 0.0

    try:
        result = primer3.calc_hairpin(sequence.upper())
        return round(result.dg / 1000, 2)  # Convert cal/mol to kcal/mol
    except Exception:
        return 0.0


def calculate_self_dimer_dg(sequence: str) -> float:
    """
    Calculate self-dimer formation ΔG.

    Args:
        sequence: Primer sequence

    Returns:
        ΔG in kcal/mol (more negative = stronger dimer)
    """
    if not sequence or len(sequence) < 4:
        return 0.0

    try:
        result = primer3.calc_homodimer(sequence.upper())
        return round(result.dg / 1000, 2)  # Convert cal/mol to kcal/mol
    except Exception:
        return 0.0


def calculate_cross_dimer_dg(seq1: str, seq2: str) -> float:
    """
    Calculate cross-dimer (heterodimer) formation ΔG.

    Args:
        seq1: First primer sequence
        seq2: Second primer sequence

    Returns:
        ΔG in kcal/mol (more negative = stronger dimer)
    """
    if not seq1 or not seq2:
        return 0.0

    try:
        result = primer3.calc_heterodimer(seq1.upper(), seq2.upper())
        return round(result.dg / 1000, 2)  # Convert cal/mol to kcal/mol
    except Exception:
        return 0.0


def analyze_primer(primer: Primer) -> Primer:
    """
    Calculate all thermodynamic properties for a primer.

    Args:
        primer: Primer object with sequence

    Returns:
        Primer object with populated QC fields
    """
    primer.tm = calculate_tm(primer.sequence)
    primer.gc_percent = calculate_gc(primer.sequence)
    primer.hairpin_dg = calculate_hairpin_dg(primer.sequence)
    primer.self_dimer_dg = calculate_self_dimer_dg(primer.sequence)
    primer.three_prime_base = primer.sequence[-1].upper() if primer.sequence else ""

    return primer


def analyze_pair(pair: PrimerPair) -> PrimerPair:
    """
    Calculate pair-level QC metrics.

    Args:
        pair: PrimerPair object

    Returns:
        PrimerPair with updated cross-dimer and tm_difference
    """
    # Analyze individual primers if not already done
    if pair.forward.tm == 0:
        analyze_primer(pair.forward)
    if pair.reverse.tm == 0:
        analyze_primer(pair.reverse)

    # Calculate pair-level metrics
    pair.tm_difference = abs(pair.forward.tm - pair.reverse.tm)
    pair.cross_dimer_dg = calculate_cross_dimer_dg(pair.forward.sequence, pair.reverse.sequence)

    # Analyze probe if present
    if pair.probe:
        analyze_probe(pair.probe)

    return pair


def analyze_probe(probe: Probe) -> Probe:
    """
    Calculate QC metrics for a TaqMan probe.

    Args:
        probe: Probe object with sequence

    Returns:
        Probe object with populated QC fields
    """
    if not probe or not probe.sequence:
        return probe

    # Recalculate Tm and GC if needed
    if probe.tm == 0:
        probe.tm = calculate_tm(probe.sequence)
    if probe.gc_percent == 0:
        probe.gc_percent = calculate_gc(probe.sequence)

    # Set 5' base if not already set
    if not probe.five_prime_base:
        probe.five_prime_base = probe.sequence[0].upper()

    return probe


def get_3prime_end(sequence: str, length: int = 5) -> str:
    """
    Get the 3' end of a sequence.

    Args:
        sequence: Primer sequence
        length: Number of bases to return

    Returns:
        3' end sequence
    """
    if not sequence:
        return ""
    return sequence[-length:].upper()


def check_gc_clamp(sequence: str) -> Tuple[bool, str]:
    """
    Check for GC clamp at 3' end (1-2 G/C in last 5 bases).

    Args:
        sequence: Primer sequence

    Returns:
        Tuple of (has_clamp, description)
    """
    if not sequence:
        return False, "No sequence"

    last_5 = sequence[-5:].upper()
    gc_count = last_5.count("G") + last_5.count("C")

    if gc_count == 0:
        return False, "No GC clamp (0 G/C in last 5 bases)"
    elif gc_count <= 2:
        return True, f"Good GC clamp ({gc_count} G/C in last 5 bases)"
    elif gc_count <= 3:
        return True, f"Moderate GC clamp ({gc_count} G/C in last 5 bases)"
    else:
        return False, f"Too strong GC clamp ({gc_count} G/C in last 5 bases)"
