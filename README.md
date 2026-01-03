# Primer Design Automation Pipeline

Automated PCR primer design with comprehensive QC analysis, TaqMan probe design, and batch processing for qPCR applications.

**🚀 Live Demo:** https://pcrprimer.streamlit.app/

## Features

- **FASTA Input**: Upload files or paste sequences directly
- **Batch Processing**: Design primers for multiple sequences in one run
- **Primer3 Integration**: Industry-standard primer design engine
- **TaqMan Probe Design**: Automatic probe generation with optimal Tm delta
- **QC Analysis**: Tm, GC%, hairpin, self-dimer, cross-dimer checks
- **Composite Scoring**: Weighted scoring algorithm for optimal primer selection
- **Export**: Download results as CSV with full probe data

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
├── scripts/                    # Utility scripts
├── tests/                      # Unit tests (87 tests)
└── docs/
    └── PRD.md                  # Product requirements
```

## TaqMan Probe Design

The pipeline automatically designs TaqMan probes for real-time qPCR detection:

- **Position**: Between forward and reverse primers
- **Tm**: 8-10°C higher than primer average for optimal hybridization
- **5' Base**: Avoids G (quenches FAM reporter dye)
- **GC Content**: 40-60% for stable binding

### Probe QC Thresholds

| Metric | Pass | Warn | Fail |
|--------|------|------|------|
| Tm Delta | +8 to +10°C | +6 to +12°C | Outside range |
| GC% | 40-60% | 30-70% | <30 or >70% |
| 5' Base | A, T, C | - | G (quenches FAM) |
| Length | 20-30 bp | - | Outside range |

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

## Deployments

- **Streamlit Cloud:** https://pcrprimer.streamlit.app/ (Primary demo)
- **AWS Elastic Beanstalk:** http://primer-design-env.eba-ak2qz6v5.ap-southeast-1.elasticbeanstalk.com (Self-hosted)

The application is containerized with Docker and deployed to AWS Elastic Beanstalk.

### Quick Deploy

```bash
# 1. Push Docker image to ECR
./deploy-to-aws.sh

# 2. Deploy to Elastic Beanstalk
eb init -p docker -r ap-southeast-1 primer-design
eb create primer-design-env --instance-type t2.micro

# 3. Cleanup after demo
eb terminate primer-design-env
```

### Documentation

- **[AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)** - Complete AWS Elastic Beanstalk deployment guide
- **[DEPLOYMENT_SCRIPTS.md](DEPLOYMENT_SCRIPTS.md)** - Deployment automation scripts

### Cost

- **t2.micro instance:** FREE (750 hours/month for 12 months)
- **After free tier:** ~$23/month
- **Total deployment time:** ~10 minutes

## Docker

```bash
# Build locally
docker build -t primer-design .

# Run locally
docker run -p 8080:8080 primer-design

# Access at http://localhost:8080
```

## License

MIT
