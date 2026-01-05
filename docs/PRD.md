# Product Requirements Document (PRD)
# Primer Design Automation Pipeline

**Version:** 1.0
**Author:** Raymond Luo
**Date:** December 2024
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Purpose
Build a demonstration application that automates PCR primer and probe design from target sequences. This project showcases technical competencies directly aligned with the Senior Data Scientist – Genomics/Bioinformatics (AI/ML) role at Thermo Fisher Scientific.

### 1.2 Problem Statement
Manual PCR assay design is:
- **Time-consuming**: Scientists manually check Tm, GC%, secondary structures for each candidate
- **Error-prone**: Easy to miss problematic designs (hairpins, dimers, off-targets)
- **Not scalable**: Designing hundreds of assays requires automation

### 1.3 Solution
An end-to-end pipeline that:
1. Accepts target sequences (FASTA format)
2. Generates primer/probe candidates using Primer3
3. Performs quality control checks (Tm, GC%, secondary structures)
4. Ranks candidates by composite score
5. Outputs actionable recommendations via web interface

### 1.4 Success Metrics
- **Demo-ready** in 2-3 days
- Generates **valid primer pairs** that pass standard QC thresholds
- **Interview talking point**: Demonstrates automation, bioinformatics knowledge, and software engineering skills

---

## 2. Target Users

| User | Need | How This Helps |
|------|------|----------------|
| **Technical Interviewers** | Assess candidate's skills | Demonstrates end-to-end pipeline building, bioinformatics domain knowledge, ML readiness |
| **Assay Development Scientists** | Design primers quickly | Automates tedious manual checks, ranks candidates objectively |
| **Bioinformatics Teams** | Scalable design workflow | Batch processing, reproducible outputs, API-ready architecture |

---

## 3. Functional Requirements

### 3.1 MVP Features (Must Have - 2-3 Days)

#### F1: Sequence Input
| ID | Requirement | Details |
|----|-------------|---------|
| F1.1 | Accept FASTA file upload | Single or multi-sequence FASTA |
| F1.2 | Accept raw sequence paste | Text input with auto-detection |
| F1.3 | Validate input | Check for valid nucleotides (A, T, G, C, N) |
| F1.4 | Display sequence stats | Length, GC%, basic info |

#### F2: Primer Design Engine
| ID | Requirement | Details |
|----|-------------|---------|
| F2.1 | Integrate Primer3 | Use primer3-py library |
| F2.2 | Configure design parameters | Product size, Tm range, primer length |
| F2.3 | Generate primer pairs | Forward + Reverse primers |
| F2.4 | Support custom constraints | User-adjustable Tm, GC%, length ranges |

#### F3: Quality Control Analysis
| ID | Requirement | Details |
|----|-------------|---------|
| F3.1 | Calculate Tm | Nearest-neighbor method (Primer3 default) |
| F3.2 | Calculate GC content | Percentage of G+C bases |
| F3.3 | Check hairpin formation | ΔG calculation, flag if < -2 kcal/mol |
| F3.4 | Check self-dimer | ΔG calculation, flag if < -9 kcal/mol |
| F3.5 | Check cross-dimer | Forward-Reverse complementarity |
| F3.6 | Validate 3' end | Check for G/C clamp, avoid T terminus |

#### F4: Scoring & Ranking
| ID | Requirement | Details |
|----|-------------|---------|
| F4.1 | Composite scoring | Weighted score from QC metrics (includes probe quality if available) |
| F4.2 | Rank primer pairs | Best to worst by composite score |
| F4.3 | Visual indicators | Green/Yellow/Red for pass/warn/fail |
| F4.4 | Top-N output | Show top 5 candidates by default |

#### F5: User Interface
| ID | Requirement | Details |
|----|-------------|---------|
| F5.1 | Streamlit web app | Simple, interactive UI |
| F5.2 | Input panel | Sequence upload + parameter config |
| F5.3 | Results table | Sortable, filterable primer list |
| F5.4 | Detail view | Click to see full QC breakdown |
| F5.5 | Export results | Download as CSV |

---

### 3.2 Extended Features (Nice to Have - If Time Permits)

#### F6: TaqMan Probe Design
| ID | Requirement | Details |
|----|-------------|---------|
| F6.1 | Generate probe candidates | Position between primers |
| F6.2 | Probe Tm validation | 8-10°C higher than primers (target ~68-70°C if primers are ~58-60°C) |
| F6.3 | 5' base check | Never start with G (quenches reporters) |
| F6.4 | Probe sequence sanity | Length 20-30 bp; GC 30-80%; avoid runs of 4+ identical bases |
| F6.5 | Placement preference | No overlap with primer 3' end; prefer closer to forward primer |
| F6.6 | Primer3 internal oligo | Use Primer3 internal oligo selection when available; fallback to rule-based design |

#### F7: Specificity Check (Simulated)
| ID | Requirement | Details |
|----|-------------|---------|
| F7.1 | Local BLAST simulation | Check against small reference DB |
| F7.2 | Off-target flagging | Warn on 3' end matches |

#### F8: Batch Processing
| ID | Requirement | Details |
|----|-------------|---------|
| F8.1 | Multi-target input | Process multiple sequences |
| F8.2 | Parallel execution | Speed up batch jobs |
| F8.3 | Batch export | Single CSV with all results |

#### F9: ML Enhancement (Future)
| ID | Requirement | Details |
|----|-------------|---------|
| F9.1 | Success prediction | Train model on historical data |
| F9.2 | Feature importance | Show which QC metrics matter most |

---

## 4. Technical Architecture

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Sequence     │  │ Parameters   │  │ Results Dashboard    │   │
│  │ Input        │  │ Config       │  │ (Table + Details)    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CORE ENGINE (Python)                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Sequence     │  │ Primer       │  │ QC                   │   │
│  │ Parser       │  │ Designer     │  │ Analyzer             │   │
│  │ (Biopython)  │  │ (Primer3)    │  │ (Thermodynamics)     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Scorer       │  │ Ranker       │  │ Exporter             │   │
│  │              │  │              │  │ (CSV/JSON)           │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **UI** | Streamlit | Rapid prototyping, interactive, Python-native |
| **Primer Design** | primer3-py | Industry standard, well-documented |
| **Sequence Handling** | Biopython | Robust FASTA parsing, sequence manipulation |
| **Data Processing** | Pandas | Tabular data, easy export |
| **Visualization** | Plotly | Interactive charts (optional) |
| **Testing** | pytest | Unit tests for core logic |

### 4.3 Project Structure

```
primer-design-automation/
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup (optional)
├── .gitignore
│
├── app.py                      # Streamlit main entry point
│
├── src/
│   ├── __init__.py
│   ├── models.py               # Data classes (Primer, PrimerPair, QCResult)
│   ├── sequence_parser.py      # FASTA parsing, validation
│   ├── primer_designer.py      # Primer3 wrapper
│   ├── qc_analyzer.py          # Thermodynamic calculations
│   ├── scorer.py               # Composite scoring algorithm
│   ├── ranker.py               # Sorting and filtering
│   └── exporter.py             # CSV/JSON export
│
├── config/
│   └── defaults.yaml           # Default parameters
│
├── data/
│   └── sample_sequences/       # Test FASTA files
│       ├── sars_cov2_spike.fasta
│       └── hiv_pol.fasta
│
├── tests/
│   ├── __init__.py
│   ├── test_sequence_parser.py
│   ├── test_primer_designer.py
│   ├── test_qc_analyzer.py
│   └── test_scorer.py
│
└── docs/
    ├── PRD.md                  # This document
    └── ARCHITECTURE.md         # Technical deep-dive
```

---

## 5. Data Models

### 5.1 Core Classes

```python
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

class QCStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"

@dataclass
class Primer:
    """Single primer oligo"""
    sequence: str
    start: int                    # Position in target
    end: int
    length: int
    tm: float                     # Melting temperature (°C)
    gc_percent: float             # GC content (%)
    hairpin_dg: float             # Hairpin ΔG (kcal/mol)
    self_dimer_dg: float          # Self-dimer ΔG (kcal/mol)
    three_prime_base: str         # Last base at 3' end

    @property
    def tm_status(self) -> QCStatus:
        if 58 <= self.tm <= 62:
            return QCStatus.PASS
        elif 55 <= self.tm <= 65:
            return QCStatus.WARN
        return QCStatus.FAIL

    @property
    def gc_status(self) -> QCStatus:
        if 40 <= self.gc_percent <= 60:
            return QCStatus.PASS
        elif 30 <= self.gc_percent <= 70:
            return QCStatus.WARN
        return QCStatus.FAIL

@dataclass
class PrimerPair:
    """Forward + Reverse primer pair"""
    forward: Primer
    reverse: Primer
    product_size: int             # Amplicon length
    tm_difference: float          # |Tm_F - Tm_R|
    cross_dimer_dg: float         # Cross-dimer ΔG (kcal/mol)

    # Scoring
    composite_score: float = 0.0
    rank: int = 0

@dataclass
class Probe:
    """TaqMan probe (optional)"""
    sequence: str
    start: int
    end: int
    length: int
    tm: float
    gc_percent: float
    five_prime_base: str          # First base at 5' end (avoid G)

@dataclass
class DesignResult:
    """Complete design output"""
    target_name: str
    target_sequence: str
    primer_pairs: List[PrimerPair]
    probe: Optional[Probe] = None
```

### 5.2 QC Thresholds Configuration

```python
@dataclass
class QCThresholds:
    """Configurable QC thresholds"""
    # Primer Tm
    tm_optimal: float = 60.0
    tm_min: float = 58.0
    tm_max: float = 62.0
    tm_warn_min: float = 55.0
    tm_warn_max: float = 65.0

    # Tm difference between primers
    tm_diff_max: float = 2.0
    tm_diff_warn: float = 3.0

    # GC content
    gc_min: float = 40.0
    gc_max: float = 60.0
    gc_warn_min: float = 30.0
    gc_warn_max: float = 70.0

    # Primer length
    length_min: int = 18
    length_max: int = 25
    length_optimal: int = 20

    # Secondary structures (ΔG thresholds, kcal/mol)
    hairpin_dg_max: float = -2.0   # Less negative = OK
    self_dimer_dg_max: float = -9.0
    cross_dimer_dg_max: float = -9.0

    # 3' end
    preferred_3prime: List[str] = ("G", "C")
    avoid_3prime: List[str] = ("T",)

    # Product size
    product_min: int = 70
    product_max: int = 200
    product_optimal: int = 100
```

---

## 6. Algorithm Details

### 6.1 Composite Scoring Algorithm

```python
def calculate_composite_score(pair: PrimerPair, thresholds: QCThresholds) -> float:
    """
    Calculate composite score (0-100) for primer pair.
    Higher = better.

    Weights reflect importance for PCR success:
    - Tm matching: 25% (critical for annealing)
    - GC content: 15% (affects stability)
    - Secondary structures: 20% (dimers kill efficiency)
    - 3' end quality: 10% (specificity)
    - Product size: 5% (practical consideration)
    - Probe quality: 25% (signal generation)
    """
    score = 0.0

    # 1. Tm Score (25 points)
    tm_avg = (pair.forward.tm + pair.reverse.tm) / 2
    tm_score = 25 * (1 - abs(tm_avg - thresholds.tm_optimal) / 10)
    tm_score -= 5 * (pair.tm_difference / thresholds.tm_diff_warn)  # Penalty for mismatch
    score += max(0, tm_score)

    # 2. GC Score (15 points)
    gc_avg = (pair.forward.gc_percent + pair.reverse.gc_percent) / 2
    gc_optimal = 50.0
    gc_score = 15 * (1 - abs(gc_avg - gc_optimal) / 30)
    score += max(0, gc_score)

    # 3. Secondary Structure Score (20 points)
    structure_score = 30
    # Hairpin penalty
    hairpin_worst = min(pair.forward.hairpin_dg, pair.reverse.hairpin_dg)
    if hairpin_worst < -4.0:  # fail threshold
        structure_score = 0
    elif hairpin_worst < thresholds.hairpin_dg_max:
        structure_score -= 10
    # Self-dimer penalty
    dimer_worst = min(pair.forward.self_dimer_dg, pair.reverse.self_dimer_dg)
    if dimer_worst < thresholds.self_dimer_dg_max:
        structure_score -= 10
    # Cross-dimer penalty
    if pair.cross_dimer_dg < thresholds.cross_dimer_dg_max:
        structure_score -= 10
    score += max(0, structure_score) * (20 / 30)

    # 4. 3' End Score (10 points)
    three_prime_score = 0
    for primer in [pair.forward, pair.reverse]:
        if primer.three_prime_base in thresholds.preferred_3prime:
            three_prime_score += 10
        elif primer.three_prime_base in thresholds.avoid_3prime:
            three_prime_score -= 5
        else:
            three_prime_score += 5
    score += three_prime_score * 0.5

    # 5. Product Size Score (5 points)
    size_diff = abs(pair.product_size - thresholds.product_optimal)
    size_score = 5 * (1 - size_diff / 100)
    score += max(0, size_score)

    # 6. Probe Score (25 points)
    if pair.probe:
        tm_delta = pair.probe.tm - pair.primer_avg_tm
        if tm_delta < 6 or tm_delta > 12:
            probe_score = 0
        else:
            probe_score = 25  # Full points if probe meets Tm/GC/5' base/length rules
        score += probe_score

    return max(0, min(100, score))
```

### 6.2 Primer3 Configuration

```python
PRIMER3_SETTINGS = {
    'PRIMER_OPT_SIZE': 20,
    'PRIMER_MIN_SIZE': 18,
    'PRIMER_MAX_SIZE': 25,
    'PRIMER_OPT_TM': 60.0,
    'PRIMER_MIN_TM': 58.0,
    'PRIMER_MAX_TM': 62.0,
    'PRIMER_MIN_GC': 40.0,
    'PRIMER_MAX_GC': 60.0,
    'PRIMER_MAX_POLY_X': 4,              # Max homopolymer run
    'PRIMER_MAX_SELF_ANY': 8,            # Self-complementarity
    'PRIMER_MAX_SELF_END': 3,            # 3' self-complementarity
    'PRIMER_PAIR_MAX_COMPL_ANY': 8,      # Cross-complementarity
    'PRIMER_PAIR_MAX_COMPL_END': 3,      # 3' cross-complementarity
    'PRIMER_PRODUCT_SIZE_RANGE': [[70, 200]],
    'PRIMER_NUM_RETURN': 10,             # Number of candidates
    'PRIMER_THERMODYNAMIC_OLIGO_ALIGNMENT': 1,
    'PRIMER_THERMODYNAMIC_TEMPLATE_ALIGNMENT': 0,
}
```

---

## 7. User Interface Design

### 7.1 Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🧬 Primer Design Automation Pipeline                           │
│  Automated PCR primer design with quality scoring               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ SIDEBAR ──────────────┐  ┌─ MAIN AREA ─────────────────────┐│
│  │                        │  │                                  ││
│  │  📁 Upload FASTA       │  │  TARGET SEQUENCE INFO            ││
│  │  [Choose file...]      │  │  ┌────────────────────────────┐  ││
│  │                        │  │  │ Name: SARS-CoV-2 Spike     │  ││
│  │  --- OR ---            │  │  │ Length: 500 bp             │  ││
│  │                        │  │  │ GC: 42.3%                  │  ││
│  │  📝 Paste sequence:    │  │  └────────────────────────────┘  ││
│  │  ┌──────────────────┐  │  │                                  ││
│  │  │ ATGCGATCGATCG... │  │  │  DESIGN RESULTS                  ││
│  │  └──────────────────┘  │  │  ┌────────────────────────────┐  ││
│  │                        │  │  │ Rank│Score│Fwd Tm│Rev Tm│...│  ││
│  │  ⚙️ PARAMETERS         │  │  │  1  │ 92  │ 60.1 │ 59.8 │...│  ││
│  │  ────────────────      │  │  │  2  │ 87  │ 61.2 │ 60.5 │...│  ││
│  │  Tm range: [58-62]     │  │  │  3  │ 84  │ 59.5 │ 60.1 │...│  ││
│  │  GC range: [40-60]     │  │  │  ...                       │  ││
│  │  Product size: [70-200]│  │  └────────────────────────────┘  ││
│  │  Num results: [5]      │  │                                  ││
│  │                        │  │  SELECTED PAIR DETAILS           ││
│  │  [🚀 Design Primers]   │  │  ┌────────────────────────────┐  ││
│  │                        │  │  │ Forward: ATGCGATCGATCGATCG │  ││
│  │  [📥 Export CSV]       │  │  │ Tm: 60.1°C  GC: 52.3%      │  ││
│  │                        │  │  │ Hairpin ΔG: -1.2 ✅         │  ││
│  └────────────────────────┘  │  │ Self-dimer ΔG: -5.4 ✅      │  ││
│                              │  │                              │  ││
│                              │  │ Reverse: TCGATCGATCGATCGAT │  ││
│                              │  │ Tm: 59.8°C  GC: 48.1%      │  ││
│                              │  │ ...                         │  ││
│                              │  └────────────────────────────┘  ││
│                              └──────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Color Coding

| Status | Color | Meaning |
|--------|-------|---------|
| ✅ PASS | Green (#28a745) | Within optimal range |
| ⚠️ WARN | Yellow (#ffc107) | Acceptable but not optimal |
| ❌ FAIL | Red (#dc3545) | Outside acceptable range |

---

## 8. API Specification (Internal)

### 8.1 Core Functions

```python
# sequence_parser.py
def parse_fasta(file_or_text: Union[str, IO]) -> List[SeqRecord]:
    """Parse FASTA input, return list of sequence records."""

def validate_sequence(seq: str) -> Tuple[bool, Optional[str]]:
    """Validate nucleotide sequence, return (is_valid, error_message)."""

# primer_designer.py
def design_primers(
    sequence: str,
    settings: Optional[Dict] = None
) -> List[PrimerPair]:
    """Run Primer3, return list of primer pair candidates."""

# qc_analyzer.py
def analyze_primer(primer: Primer) -> Primer:
    """Calculate thermodynamic properties for single primer."""

def analyze_pair(pair: PrimerPair) -> PrimerPair:
    """Calculate cross-dimer and pair-level QC metrics."""

# scorer.py
def score_pair(pair: PrimerPair, thresholds: QCThresholds) -> float:
    """Calculate composite score for primer pair."""

# ranker.py
def rank_pairs(pairs: List[PrimerPair]) -> List[PrimerPair]:
    """Sort pairs by composite score, assign ranks."""

# exporter.py
def export_csv(results: DesignResult, filepath: str) -> None:
    """Export results to CSV file."""

def export_json(results: DesignResult, filepath: str) -> None:
    """Export results to JSON file."""
```

---

## 9. Test Plan

### 9.1 Unit Tests

| Module | Test Case | Expected Result |
|--------|-----------|-----------------|
| `sequence_parser` | Valid FASTA | Parses correctly |
| `sequence_parser` | Invalid nucleotides | Returns validation error |
| `primer_designer` | Known sequence | Returns expected primers |
| `qc_analyzer` | Primer with hairpin | Correct ΔG calculation |
| `scorer` | Perfect primer pair | Score near 100 |
| `scorer` | Pair with dimer issues | Score reduced |

### 9.2 Integration Tests

| Test | Input | Expected |
|------|-------|----------|
| End-to-end design | Sample FASTA | Ranked primer list |
| Export functionality | Design results | Valid CSV file |

### 9.3 Sample Test Sequences

```
>SARS-CoV-2_Spike_Fragment
ATGTTTGTTTTTCTTGTTTTATTGCCACTAGTCTCTAGTCAGTGTGTTAATCTTACAACC
AGAACTCAATTACCCCCTGCATACACTAATTCTTTCACACGTGGTGTTTATTACCCTGAC
AAAGTTTTCAGATCCTCAGTTTTACATTCAACTCAGGACTTGTTCTTACCTTTCTTTTCC

>HIV1_POL_Fragment
CCTCAGGTCACTCTTTGGCAACGACCCCTCGTCACAATAAAGATAGGGGGGCAACTAAAG
GAAGCTCTATTAGATACAGGAGCAGATGATACAGTATTAGAAGAAATGAGTTTGCCAGGA
```

---

## 10. Development Timeline

### Phase 1: Foundation (Day 1)
- [ ] Set up project structure
- [ ] Implement sequence parser
- [ ] Implement Primer3 wrapper
- [ ] Basic Streamlit UI (input only)

### Phase 2: Core Features (Day 2)
- [ ] Implement QC analyzer
- [ ] Implement scoring algorithm
- [ ] Complete results display
- [ ] Add export functionality

### Phase 3: Polish (Day 3)
- [ ] Add parameter configuration UI
- [ ] Improve visual design
- [ ] Write unit tests
- [ ] Create sample data
- [ ] Documentation

### Phase 4: Extended (If Time Permits)
- [ ] TaqMan probe design
- [ ] Batch processing
- [ ] Additional visualizations

### Phase 5: AWS Cloud Deployment (Optional)
- [ ] Containerize app with Docker
- [ ] Set up AWS account and configure credentials
- [ ] Deploy to AWS App Runner
- [ ] Configure custom domain (optional)
- [ ] Set up CI/CD with AWS CodeBuild

---

## 11. AWS Deployment Architecture (Optional)

### 11.1 Why AWS App Runner?

| Benefit | Description |
|---------|-------------|
| **Serverless** | No infrastructure management, auto-scaling |
| **Pay-per-use** | Only charged when app is running |
| **Container-based** | Docker packaging, portable |
| **Easy HTTPS** | Automatic SSL certificates |
| **Fast deployment** | Suitable for demo/interview |
| **AWS Integration** | Native integration with ECR, CodeBuild, CloudWatch |

### 11.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS APP RUNNER                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Container Instance                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │  │
│  │  │  Streamlit  │  │   Primer3   │  │    Biopython    │    │  │
│  │  │     App     │  │   Engine    │  │    + Pandas     │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Auto-scaling: 0 → N instances based on traffic                 │
│  Memory: 1-2 GB (sufficient for Primer3)                        │
│  CPU: 1-2 vCPU                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                AMAZON ELASTIC CONTAINER REGISTRY (ECR)           │
│                    (stores Docker image)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 11.3 Required Files

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies for primer3
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8080

# App Runner uses PORT env variable (default 8080)
ENV PORT=8080

# Run Streamlit
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
```

**.dockerignore:**
```
.git
.gitignore
__pycache__
*.pyc
.pytest_cache
.env
venv/
docs/
tests/
*.md
```

**buildspec.yml** (CI/CD with AWS CodeBuild):
```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/primer-design
      - IMAGE_TAG=${CODEBUILD_RESOLVED_SOURCE_VERSION:0:7}
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:latest .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{"name":"primer-design","imageUri":"%s"}]' $REPOSITORY_URI:$IMAGE_TAG > imagedefinitions.json
artifacts:
  files: imagedefinitions.json
```

### 11.4 Deployment Commands

```bash
# 1. Configure AWS CLI
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region: ap-southeast-1

# 2. Create ECR repository
aws ecr create-repository \
    --repository-name primer-design \
    --region ap-southeast-1

# 3. Build and push Docker image
# Get ECR login token
aws ecr get-login-password --region ap-southeast-1 | \
    docker login --username AWS --password-stdin \
    <AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com

# Build Docker image
docker build -t primer-design .

# Tag image
docker tag primer-design:latest \
    <AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/primer-design:latest

# Push to ECR
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/primer-design:latest

# 4. Deploy to App Runner (via AWS Console or CLI)
# Using AWS Console is recommended for first deployment
# Or via CLI:
aws apprunner create-service \
    --service-name primer-design \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "<AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/primer-design:latest",
            "ImageRepositoryType": "ECR",
            "ImageConfiguration": {
                "Port": "8080"
            }
        },
        "AutoDeploymentsEnabled": true
    }' \
    --instance-configuration '{
        "Cpu": "1 vCPU",
        "Memory": "2 GB"
    }' \
    --region ap-southeast-1

# 5. Get the deployed URL
aws apprunner list-services --region ap-southeast-1
```

### 11.5 Cost Estimate

| Resource | Free Tier | Estimated Cost |
|----------|-----------|----------------|
| App Runner | 450,000 vCPU-seconds + 8.75 GB-hours/month free | ~$0 for demo |
| ECR | 500 MB storage/month free | ~$0 for demo |
| CodeBuild | 100 build minutes/month free | ~$0 for demo |
| **Total** | | **Free for demo usage** |

### 11.6 Interview Talking Points (AWS)

> "I deployed the app to AWS App Runner—serverless, auto-scaling, pay-per-use. It demonstrates my experience with cloud-based deployment on AWS, which is listed as a preferred qualification in the JD. The architecture is production-ready: containerized with ECR, CI/CD pipeline with CodeBuild, infrastructure-as-code approach, and integrated with CloudWatch for monitoring."

---

## 12. Out of Scope (v1.0)

| Feature | Reason |
|---------|--------|
| Real BLAST integration | Requires external DB setup, slow |
| Multiplex design | Complex constraint satisfaction |
| ML-based prediction | Requires training data |
| User authentication | Demo app, not production |
| Database storage | File-based for simplicity |

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Primer3 installation issues | Blocks core functionality | Test early, have fallback calculations |
| Complex UI taking too long | Delays completion | Start with minimal UI, enhance later |
| Scoring algorithm edge cases | Poor rankings | Test with known good/bad primers |
| Interview timing | Demo not ready | Prioritize MVP, cut extended features |

---

## 14. Interview Talking Points

When demonstrating this project:

1. **Architecture**: "I designed this as a modular pipeline—each component (parsing, design, QC, scoring) is separate and testable."

2. **Domain Knowledge**: "The scoring algorithm weights Tm matching and secondary structures heavily because those are the primary causes of PCR failure."

3. **Extensibility**: "This architecture supports future ML integration—I could train a model on historical assay success data using these QC features."

4. **Practical Tradeoffs**: "I simulated BLAST rather than integrating it fully—real implementation would use Primer-BLAST API or local database."

5. **Automation Value**: "This replaces hours of manual checking with seconds of computation, and ensures consistent, reproducible designs."

---

## 15. References

- Primer3 Documentation: https://primer3.org/manual.html
- primer3-py: https://libnano.github.io/primer3-py/
- Biopython: https://biopython.org/
- Thermo Fisher Primer Design Guide
- IDT OligoAnalyzer: https://www.idtdna.com/pages/tools

---

## Appendix A: Installation Requirements

```txt
# requirements.txt
streamlit>=1.28.0
primer3-py>=0.6.1
biopython>=1.81
pandas>=2.0.0
plotly>=5.18.0
pytest>=7.4.0
pyyaml>=6.0.1
```

---

## Appendix B: Quick Start

```bash
# Clone and setup
git clone <repo>
cd primer-design-automation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run app
streamlit run app.py

# Run tests
pytest tests/
```
