# Primer Design Automation Pipeline

Automated PCR primer design with quality scoring and ranking.

## Features

- **FASTA Input**: Upload files or paste sequences directly
- **Primer3 Integration**: Industry-standard primer design engine
- **QC Analysis**: Tm, GC%, hairpin, self-dimer, cross-dimer checks
- **Composite Scoring**: Weighted scoring algorithm for optimal primer selection
- **Export**: Download results as CSV

## Quick Start

```bash
# Clone and setup
git clone <repo>
cd primer-design-automation
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run app
streamlit run app.py

# Run tests
pytest tests/
```

## Project Structure

```
primer-design-automation/
├── app.py                      # Streamlit entry point
├── requirements.txt            # Python dependencies
├── src/
│   ├── models.py               # Data classes
│   ├── sequence_parser.py      # FASTA parsing
│   ├── primer_designer.py      # Primer3 wrapper
│   ├── qc_analyzer.py          # Thermodynamic calculations
│   ├── scorer.py               # Composite scoring
│   └── exporter.py             # CSV/JSON export
├── config/
│   └── defaults.yaml           # Default parameters
├── data/sample_sequences/      # Test sequences
├── tests/                      # Unit tests
└── docs/
    └── PRD.md                  # Product requirements
```

## Scoring Algorithm

Primers are scored 0-100 based on:

| Component | Weight | Description |
|-----------|--------|-------------|
| Tm Matching | 25% | Distance from 60°C optimal, primer pair matching |
| GC Content | 15% | Distance from 50% optimal |
| Secondary Structures | 30% | Hairpin, self-dimer, cross-dimer penalties |
| 3' End Quality | 20% | G/C preferred, T avoided at 3' end |
| Product Size | 10% | Distance from optimal (100 bp for qPCR) |

## QC Thresholds

| Metric | Pass | Warn | Fail |
|--------|------|------|------|
| Tm | 58-62°C | 55-65°C | <55 or >65°C |
| GC% | 40-60% | 30-70% | <30 or >70% |
| Hairpin ΔG | > -2 kcal/mol | -2 to -4 | < -4 kcal/mol |
| Self-dimer ΔG | > -9 kcal/mol | -9 to -12 | < -12 kcal/mol |
| Product Size | 70-200 bp | 50-300 bp | Outside range |

## License

MIT
