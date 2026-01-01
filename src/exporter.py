"""
Export functionality for primer design results.

Supports CSV and JSON export formats.
"""

import json
from io import StringIO
from typing import Any, Dict, List

import pandas as pd

from .models import DesignResult, PrimerPair


def to_dataframe(result: DesignResult) -> pd.DataFrame:
    """
    Convert DesignResult to pandas DataFrame.

    Args:
        result: DesignResult object

    Returns:
        DataFrame with primer pair data
    """
    rows = []

    for pair in result.primer_pairs:
        row = {
            "Rank": pair.rank,
            "Score": pair.composite_score,
            "Forward_Seq": pair.forward.sequence,
            "Forward_Tm": pair.forward.tm,
            "Forward_GC%": pair.forward.gc_percent,
            "Forward_Hairpin_dG": pair.forward.hairpin_dg,
            "Forward_SelfDimer_dG": pair.forward.self_dimer_dg,
            "Forward_3prime": pair.forward.three_prime_base,
            "Forward_Start": pair.forward.start,
            "Forward_End": pair.forward.end,
            "Reverse_Seq": pair.reverse.sequence,
            "Reverse_Tm": pair.reverse.tm,
            "Reverse_GC%": pair.reverse.gc_percent,
            "Reverse_Hairpin_dG": pair.reverse.hairpin_dg,
            "Reverse_SelfDimer_dG": pair.reverse.self_dimer_dg,
            "Reverse_3prime": pair.reverse.three_prime_base,
            "Reverse_Start": pair.reverse.start,
            "Reverse_End": pair.reverse.end,
            "Product_Size": pair.product_size,
            "Tm_Difference": pair.tm_difference,
            "CrossDimer_dG": pair.cross_dimer_dg,
            "Probe_Seq": pair.probe.sequence if pair.probe else "",
            "Probe_Tm": pair.probe.tm if pair.probe else None,
            "Probe_GC%": pair.probe.gc_percent if pair.probe else None,
            "Probe_5prime": pair.probe.five_prime_base if pair.probe else "",
            "Probe_Start": pair.probe.start if pair.probe else None,
            "Probe_End": pair.probe.end if pair.probe else None,
            "Target": result.target_name,
        }
        rows.append(row)

    return pd.DataFrame(rows)


def to_summary_dataframe(result: DesignResult) -> pd.DataFrame:
    """
    Convert DesignResult to a simplified summary DataFrame.

    Args:
        result: DesignResult object

    Returns:
        DataFrame with key metrics only
    """
    rows = []

    for pair in result.primer_pairs:
        row = {
            "Rank": pair.rank,
            "Score": pair.composite_score,
            "Forward": pair.forward.sequence,
            "Fwd_Tm": f"{pair.forward.tm:.1f}°C",
            "Fwd_GC": f"{pair.forward.gc_percent:.1f}%",
            "Reverse": pair.reverse.sequence,
            "Rev_Tm": f"{pair.reverse.tm:.1f}°C",
            "Rev_GC": f"{pair.reverse.gc_percent:.1f}%",
            "Product": f"{pair.product_size} bp",
            "ΔTm": f"{pair.tm_difference:.1f}°C",
            "Probe_Tm": f"{pair.probe.tm:.1f}°C" if pair.probe else "—",
        }
        rows.append(row)

    return pd.DataFrame(rows)


def export_csv(result: DesignResult, filepath: str = None) -> str:
    """
    Export results to CSV format.

    Args:
        result: DesignResult object
        filepath: Optional file path to write to

    Returns:
        CSV string (also writes to file if filepath provided)
    """
    df = to_dataframe(result)
    csv_string = df.to_csv(index=False)

    if filepath:
        df.to_csv(filepath, index=False)

    return csv_string


def export_csv_bytes(result: DesignResult) -> bytes:
    """
    Export results to CSV as bytes (for Streamlit download).

    Args:
        result: DesignResult object

    Returns:
        CSV as bytes
    """
    csv_string = export_csv(result)
    return csv_string.encode("utf-8")


def export_json(result: DesignResult, filepath: str = None, indent: int = 2) -> str:
    """
    Export results to JSON format.

    Args:
        result: DesignResult object
        filepath: Optional file path to write to
        indent: JSON indentation

    Returns:
        JSON string (also writes to file if filepath provided)
    """
    data = result_to_dict(result)
    json_string = json.dumps(data, indent=indent)

    if filepath:
        with open(filepath, "w") as f:
            f.write(json_string)

    return json_string


def result_to_dict(result: DesignResult) -> Dict[str, Any]:
    """
    Convert DesignResult to dictionary.

    Args:
        result: DesignResult object

    Returns:
        Dictionary representation
    """
    return {
        "target_name": result.target_name,
        "target_sequence": result.target_sequence,
        "num_pairs": result.num_pairs,
        "primer_pairs": [pair_to_dict(p) for p in result.primer_pairs],
    }


def pair_to_dict(pair: PrimerPair) -> Dict[str, Any]:
    """
    Convert PrimerPair to dictionary.

    Args:
        pair: PrimerPair object

    Returns:
        Dictionary representation
    """
    return {
        "rank": pair.rank,
        "composite_score": pair.composite_score,
        "product_size": pair.product_size,
        "tm_difference": pair.tm_difference,
        "cross_dimer_dg": pair.cross_dimer_dg,
        "forward": {
            "sequence": pair.forward.sequence,
            "start": pair.forward.start,
            "end": pair.forward.end,
            "length": pair.forward.length,
            "tm": pair.forward.tm,
            "gc_percent": pair.forward.gc_percent,
            "hairpin_dg": pair.forward.hairpin_dg,
            "self_dimer_dg": pair.forward.self_dimer_dg,
            "three_prime_base": pair.forward.three_prime_base,
        },
        "reverse": {
            "sequence": pair.reverse.sequence,
            "start": pair.reverse.start,
            "end": pair.reverse.end,
            "length": pair.reverse.length,
            "tm": pair.reverse.tm,
            "gc_percent": pair.reverse.gc_percent,
            "hairpin_dg": pair.reverse.hairpin_dg,
            "self_dimer_dg": pair.reverse.self_dimer_dg,
            "three_prime_base": pair.reverse.three_prime_base,
        },
        "probe": {
            "sequence": pair.probe.sequence,
            "start": pair.probe.start,
            "end": pair.probe.end,
            "length": pair.probe.length,
            "tm": pair.probe.tm,
            "gc_percent": pair.probe.gc_percent,
            "five_prime_base": pair.probe.five_prime_base,
        } if pair.probe else None,
    }


# -----------------------------------------------------------------------------
# Batch Export Functions
# -----------------------------------------------------------------------------


def batch_to_dataframe(results: List[DesignResult]) -> pd.DataFrame:
    """
    Convert multiple DesignResults to a single DataFrame.

    Args:
        results: List of DesignResult objects

    Returns:
        Combined DataFrame with all primer pairs
    """
    all_dfs = [to_dataframe(result) for result in results if result.primer_pairs]
    if not all_dfs:
        return pd.DataFrame()
    return pd.concat(all_dfs, ignore_index=True)


def batch_to_summary_dataframe(results: List[DesignResult]) -> pd.DataFrame:
    """
    Convert multiple DesignResults to a summary DataFrame.

    Shows only the top-ranked primer for each target.

    Args:
        results: List of DesignResult objects

    Returns:
        Summary DataFrame with best primer per target
    """
    rows = []
    for result in results:
        if result.primer_pairs:
            pair = result.primer_pairs[0]  # Top-ranked
            rows.append({
                "Target": result.target_name,
                "Seq_Length": len(result.target_sequence),
                "Score": pair.composite_score,
                "Forward": pair.forward.sequence,
                "Fwd_Tm": f"{pair.forward.tm:.1f}°C",
                "Reverse": pair.reverse.sequence,
                "Rev_Tm": f"{pair.reverse.tm:.1f}°C",
                "Probe_Tm": f"{pair.probe.tm:.1f}°C" if pair.probe else "—",
                "Product": f"{pair.product_size} bp",
            })
        else:
            rows.append({
                "Target": result.target_name,
                "Seq_Length": len(result.target_sequence),
                "Score": None,
                "Forward": "No primers found",
                "Fwd_Tm": "-",
                "Reverse": "-",
                "Rev_Tm": "-",
                "Probe_Tm": "-",
                "Product": "-",
            })
    return pd.DataFrame(rows)


def batch_export_csv_bytes(results: List[DesignResult]) -> bytes:
    """
    Export batch results to CSV as bytes (for Streamlit download).

    Args:
        results: List of DesignResult objects

    Returns:
        CSV as bytes
    """
    df = batch_to_dataframe(results)
    return df.to_csv(index=False).encode("utf-8")
