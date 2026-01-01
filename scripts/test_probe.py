#!/usr/bin/env python3
"""Test script for TaqMan probe design and analysis."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.qc_analyzer import analyze_probe, calculate_tm, calculate_gc
from src.primer_designer import design_probe, design_probes_for_pairs, design_primers
from src.models import Probe, PrimerPair, Primer


def test_probe_analysis():
    """Test probe QC analysis function."""
    print("=" * 60)
    print("Testing Probe Analysis")
    print("=" * 60)

    probe = Probe(
        sequence='ACGTACGTACGTACGTACGTACGT',
        start=50,
        end=74,
        length=24,
        tm=0,  # Should be calculated
        gc_percent=0  # Should be calculated
    )

    result = analyze_probe(probe)
    print(f"Probe sequence: {result.sequence}")
    print(f"Tm: {result.tm:.1f}°C")
    print(f"GC%: {result.gc_percent:.1f}%")
    print(f"5' base: {result.five_prime_base}")
    print(f"5' status: {result.five_prime_status}")
    print(f"GC status: {result.gc_status}")
    print()


def test_probe_design():
    """Test probe design for a primer pair."""
    print("=" * 60)
    print("Testing Probe Design")
    print("=" * 60)

    # Sample sequence (200 bp)
    sequence = (
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
        "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCA"
        "TACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT"
    )

    # Design primers first
    pairs = design_primers(sequence, num_return=3)
    print(f"Designed {len(pairs)} primer pairs")

    if pairs:
        pair = pairs[0]
        print(f"\nPrimer Pair 1:")
        print(f"  Forward: {pair.forward.sequence} (Tm: {pair.forward.tm:.1f}°C)")
        print(f"  Reverse: {pair.reverse.sequence} (Tm: {pair.reverse.tm:.1f}°C)")
        print(f"  Product size: {pair.product_size} bp")
        print(f"  Primer avg Tm: {pair.primer_avg_tm:.1f}°C")

        # Design probe
        probe = design_probe(sequence, pair)
        if probe:
            print(f"\nTaqMan Probe:")
            print(f"  Sequence: {probe.sequence}")
            print(f"  Position: {probe.start}-{probe.end}")
            print(f"  Length: {probe.length} bp")
            print(f"  Tm: {probe.tm:.1f}°C")
            print(f"  Tm delta: {probe.tm - pair.primer_avg_tm:.1f}°C (target: 8-10°C)")
            print(f"  GC%: {probe.gc_percent:.1f}%")
            print(f"  5' base: {probe.five_prime_base} ({'PASS' if probe.five_prime_base != 'G' else 'FAIL - avoid G'})")
        else:
            print("\nNo suitable probe found (region too small)")
    print()


def test_probe_for_all_pairs():
    """Test probe design for multiple primer pairs."""
    print("=" * 60)
    print("Testing Probe Design for Multiple Pairs")
    print("=" * 60)

    # Longer sequence for more probe options
    sequence = (
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
        "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCA"
        "TACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT"
        "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
    )

    # Design primers
    pairs = design_primers(sequence, num_return=5)
    print(f"Designed {len(pairs)} primer pairs\n")

    # Design probes for all pairs
    pairs_with_probes = design_probes_for_pairs(sequence, pairs)

    probes_found = 0
    for i, pair in enumerate(pairs_with_probes, 1):
        probe_info = "No probe" if pair.probe is None else f"Probe Tm: {pair.probe.tm:.1f}°C"
        if pair.probe:
            probes_found += 1
        print(f"Pair {i}: Product {pair.product_size}bp | {probe_info}")

    print(f"\nProbes designed: {probes_found}/{len(pairs)}")


if __name__ == "__main__":
    test_probe_analysis()
    test_probe_design()
    test_probe_for_all_pairs()
