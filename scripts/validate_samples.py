#!/usr/bin/env python3
"""
Validate sample sequences work end-to-end.

This script tests the complete pipeline:
1. Parse FASTA sequence
2. Validate sequence
3. Design primers with Primer3
4. Analyze QC metrics
5. Score and rank pairs
6. Export to DataFrame

Usage:
    python scripts/validate_samples.py
"""

import sys
sys.path.insert(0, '.')

from src.sequence_parser import parse_fasta, validate_sequence
from src.primer_designer import design_primers
from src.qc_analyzer import analyze_pair
from src.scorer import calculate_composite_score, rank_pairs
from src.exporter import to_dataframe
from src.models import DesignResult


def validate_sample(fasta_path: str) -> bool:
    """Validate a single sample file end-to-end."""
    print(f"\nValidating: {fasta_path}")
    print("-" * 50)

    try:
        # Parse FASTA
        with open(fasta_path, "r") as f:
            records = parse_fasta(f.read())

        seq = str(records[0].seq)
        seq_name = records[0].id
        print(f"Sequence: {seq_name}")
        print(f"Length: {len(seq)} bp")

        # Validate
        is_valid, error = validate_sequence(seq)
        print(f"Valid: {is_valid}")
        if error:
            print(f"Error: {error}")
            return False

        # Design primers
        pairs = design_primers(seq, num_return=5)
        print(f"Primer pairs generated: {len(pairs)}")

        if len(pairs) == 0:
            print("ERROR: No primer pairs generated")
            return False

        # Analyze and score
        for pair in pairs:
            analyze_pair(pair)
            pair.composite_score = calculate_composite_score(pair)

        # Rank
        ranked = rank_pairs(pairs)

        # Display top 3
        print("\nTop 3 Primer Pairs:")
        for p in ranked[:3]:
            print(f"  Rank {p.rank}: Score {p.composite_score:.1f}")
            print(f"    Fwd: {p.forward.sequence} (Tm={p.forward.tm:.1f}°C, GC={p.forward.gc_percent:.1f}%)")
            print(f"    Rev: {p.reverse.sequence} (Tm={p.reverse.tm:.1f}°C, GC={p.reverse.gc_percent:.1f}%)")
            print(f"    Product: {p.product_size} bp, Tm diff: {p.tm_difference:.1f}°C")

        # Test export
        result = DesignResult(
            target_name=seq_name,
            target_sequence=seq,
            primer_pairs=ranked
        )
        df = to_dataframe(result)
        print(f"\nExport DataFrame: {len(df)} rows, {len(df.columns)} columns")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    """Validate all sample sequences."""
    print("=" * 60)
    print("Sample Sequence End-to-End Validation")
    print("=" * 60)

    samples = [
        "data/sample_sequences/sars_cov2_spike.fasta",
        "data/sample_sequences/hiv_pol.fasta",
    ]

    results = []
    for sample in samples:
        success = validate_sample(sample)
        results.append((sample, success))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for sample, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {sample}")
        if not success:
            all_passed = False

    if all_passed:
        print("\n✓ All sample sequences validated successfully!")
        return 0
    else:
        print("\n✗ Some samples failed validation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
