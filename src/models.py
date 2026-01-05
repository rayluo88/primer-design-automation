"""
Data models for Primer Design Automation Pipeline.

Defines core dataclasses for primers, primer pairs, QC results, and thresholds.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class QCStatus(Enum):
    """Quality control status indicators."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class Primer:
    """Single primer oligonucleotide with QC metrics."""
    sequence: str
    start: int
    end: int
    length: int
    tm: float
    gc_percent: float
    hairpin_dg: float = 0.0
    self_dimer_dg: float = 0.0
    three_prime_base: str = ""

    def __post_init__(self):
        if not self.three_prime_base and self.sequence:
            self.three_prime_base = self.sequence[-1].upper()

    @property
    def tm_status(self) -> QCStatus:
        """Evaluate Tm against standard thresholds."""
        if 58.0 <= self.tm <= 62.0:
            return QCStatus.PASS
        elif 55.0 <= self.tm <= 65.0:
            return QCStatus.WARN
        return QCStatus.FAIL

    @property
    def gc_status(self) -> QCStatus:
        """Evaluate GC% against standard thresholds."""
        if 40.0 <= self.gc_percent <= 60.0:
            return QCStatus.PASS
        elif 30.0 <= self.gc_percent <= 70.0:
            return QCStatus.WARN
        return QCStatus.FAIL

    @property
    def hairpin_status(self) -> QCStatus:
        """Evaluate hairpin ΔG (more negative = worse)."""
        if self.hairpin_dg > -2.0:
            return QCStatus.PASS
        elif self.hairpin_dg > -4.0:
            return QCStatus.WARN
        return QCStatus.FAIL

    @property
    def self_dimer_status(self) -> QCStatus:
        """Evaluate self-dimer ΔG (more negative = worse)."""
        if self.self_dimer_dg > -9.0:
            return QCStatus.PASS
        elif self.self_dimer_dg > -12.0:
            return QCStatus.WARN
        return QCStatus.FAIL

    @property
    def three_prime_status(self) -> QCStatus:
        """Evaluate 3' end base preference."""
        if self.three_prime_base in ("G", "C"):
            return QCStatus.PASS
        elif self.three_prime_base == "T":
            return QCStatus.WARN
        return QCStatus.PASS  # A is acceptable


@dataclass
class PrimerPair:
    """Forward and reverse primer pair with combined QC metrics."""
    forward: Primer
    reverse: Primer
    product_size: int
    tm_difference: float = 0.0
    cross_dimer_dg: float = 0.0
    composite_score: float = 0.0
    rank: int = 0
    probe: Optional["Probe"] = None

    def __post_init__(self):
        if self.tm_difference == 0.0:
            self.tm_difference = abs(self.forward.tm - self.reverse.tm)

    @property
    def primer_avg_tm(self) -> float:
        """Average Tm of forward and reverse primers."""
        return (self.forward.tm + self.reverse.tm) / 2

    @property
    def tm_match_status(self) -> QCStatus:
        """Evaluate Tm matching between primers."""
        if self.tm_difference <= 2.0:
            return QCStatus.PASS
        elif self.tm_difference <= 4.0:
            return QCStatus.WARN
        return QCStatus.FAIL

    @property
    def cross_dimer_status(self) -> QCStatus:
        """Evaluate cross-dimer ΔG."""
        if self.cross_dimer_dg > -9.0:
            return QCStatus.PASS
        elif self.cross_dimer_dg > -12.0:
            return QCStatus.WARN
        return QCStatus.FAIL

    @property
    def product_size_status(self) -> QCStatus:
        """Evaluate product size for qPCR (70-200 bp optimal)."""
        if 70 <= self.product_size <= 200:
            return QCStatus.PASS
        elif 50 <= self.product_size <= 300:
            return QCStatus.WARN
        return QCStatus.FAIL


@dataclass
class Probe:
    """TaqMan probe for real-time qPCR detection."""
    sequence: str
    start: int
    end: int
    length: int
    tm: float
    gc_percent: float
    five_prime_base: str = ""

    def __post_init__(self):
        if not self.five_prime_base and self.sequence:
            self.five_prime_base = self.sequence[0].upper()

    @property
    def five_prime_status(self) -> QCStatus:
        """5' should not start with G (quenches FAM reporter)."""
        if self.five_prime_base == "G":
            return QCStatus.FAIL
        return QCStatus.PASS

    @property
    def gc_status(self) -> QCStatus:
        """Evaluate GC% against standard thresholds (30-80%)."""
        if 30.0 <= self.gc_percent <= 80.0:
            return QCStatus.PASS
        elif 25.0 <= self.gc_percent <= 85.0:
            return QCStatus.WARN
        return QCStatus.FAIL

    def tm_delta_status(self, primer_avg_tm: float) -> QCStatus:
        """Evaluate Tm relative to primer average (should be 8-10°C higher)."""
        delta = self.tm - primer_avg_tm
        if 8.0 <= delta <= 10.0:
            return QCStatus.PASS
        elif 6.0 <= delta <= 12.0:
            return QCStatus.WARN
        return QCStatus.FAIL


@dataclass
class QCThresholds:
    """Configurable QC thresholds for primer evaluation."""
    # Primer Tm
    tm_optimal: float = 60.0
    tm_min: float = 58.0
    tm_max: float = 62.0
    tm_warn_min: float = 55.0
    tm_warn_max: float = 65.0

    # Tm difference between primers
    tm_diff_max: float = 2.0
    tm_diff_warn: float = 4.0

    # GC content
    gc_optimal: float = 50.0
    gc_min: float = 40.0
    gc_max: float = 60.0
    gc_warn_min: float = 30.0
    gc_warn_max: float = 70.0

    # Primer length
    length_min: int = 18
    length_max: int = 25
    length_optimal: int = 20

    # Secondary structures (ΔG thresholds, kcal/mol)
    hairpin_dg_max: float = -2.0
    self_dimer_dg_max: float = -9.0
    cross_dimer_dg_max: float = -9.0

    # 3' end preferences
    preferred_3prime: tuple = ("G", "C")
    avoid_3prime: tuple = ("T",)

    # Product size (for qPCR)
    product_min: int = 70
    product_max: int = 200
    product_optimal: int = 100


@dataclass
class DesignResult:
    """Complete design output for a target sequence."""
    target_name: str
    target_sequence: str
    primer_pairs: List[PrimerPair] = field(default_factory=list)
    probe: Optional[Probe] = None

    @property
    def best_pair(self) -> Optional[PrimerPair]:
        """Return the highest-ranked primer pair."""
        if not self.primer_pairs:
            return None
        return min(self.primer_pairs, key=lambda p: p.rank) if self.primer_pairs[0].rank > 0 else self.primer_pairs[0]

    @property
    def num_pairs(self) -> int:
        """Number of primer pairs generated."""
        return len(self.primer_pairs)
