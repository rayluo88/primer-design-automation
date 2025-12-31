"""
Primer Design Automation Pipeline - Streamlit Application

A production-grade web interface for automated PCR primer design with
comprehensive QC analysis and scoring.
"""

import streamlit as st
import pandas as pd
from typing import Optional

from src.sequence_parser import parse_fasta, validate_sequence, get_sequence_stats
from src.primer_designer import design_primers, get_primer3_settings_from_thresholds
from src.qc_analyzer import analyze_pair
from src.scorer import score_pairs, rank_pairs, get_score_breakdown
from src.exporter import to_summary_dataframe, export_csv_bytes
from src.models import QCThresholds, DesignResult, QCStatus, PrimerPair


# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Primer Design Automation",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Custom CSS for Professional Styling
# -----------------------------------------------------------------------------

st.markdown("""
<style>
    /* Main container spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header styling */
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }

    .sub-header {
        font-size: 1.1rem;
        color: #5a6c7d;
        margin-bottom: 2rem;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
    }

    /* Status indicators */
    .status-pass {
        color: #059669;
        background-color: #d1fae5;
        padding: 0.125rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-warn {
        color: #d97706;
        background-color: #fef3c7;
        padding: 0.125rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-fail {
        color: #dc2626;
        background-color: #fee2e2;
        padding: 0.125rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Primer sequence display */
    .primer-seq {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.9rem;
        background-color: #f8fafc;
        padding: 0.5rem 0.75rem;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        color: #334155;
        word-break: break-all;
    }

    /* Section dividers */
    .section-divider {
        border-top: 1px solid #e2e8f0;
        margin: 1.5rem 0;
    }

    /* QC metric rows */
    .qc-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f1f5f9;
    }

    .qc-metric-name {
        font-size: 0.875rem;
        color: #475569;
    }

    .qc-metric-value {
        font-size: 0.875rem;
        font-weight: 500;
        color: #1e293b;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8fafc;
    }

    /* Button styling overrides */
    .stButton > button[kind="primary"] {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        padding: 0.5rem 2rem;
        border-radius: 6px;
    }

    /* Results table styling */
    .dataframe {
        font-size: 0.85rem;
    }

    /* Info box styling */
    .info-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }

    /* Score badge */
    .score-badge {
        display: inline-block;
        font-size: 1.25rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
    }

    .score-high {
        background-color: #d1fae5;
        color: #059669;
    }

    .score-medium {
        background-color: #fef3c7;
        color: #d97706;
    }

    .score-low {
        background-color: #fee2e2;
        color: #dc2626;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def get_status_html(status: QCStatus) -> str:
    """Generate HTML for status indicator."""
    if status == QCStatus.PASS:
        return '<span class="status-pass">PASS</span>'
    elif status == QCStatus.WARN:
        return '<span class="status-warn">WARN</span>'
    else:
        return '<span class="status-fail">FAIL</span>'


def get_status_icon(status: QCStatus) -> str:
    """Get emoji icon for status."""
    if status == QCStatus.PASS:
        return "●"  # Green circle
    elif status == QCStatus.WARN:
        return "●"  # Yellow circle
    else:
        return "●"  # Red circle


def get_status_color(status: QCStatus) -> str:
    """Get color for status."""
    if status == QCStatus.PASS:
        return "#059669"
    elif status == QCStatus.WARN:
        return "#d97706"
    else:
        return "#dc2626"


def get_score_class(score: float) -> str:
    """Get CSS class based on score."""
    if score >= 70:
        return "score-high"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"


def format_dg(value: float) -> str:
    """Format delta G value."""
    return f"{value:.1f} kcal/mol"


def initialize_session_state():
    """Initialize session state variables."""
    # Handle reset flag FIRST (must happen before any other initialization)
    if st.session_state.get("_reset_requested", False):
        st.session_state._reset_requested = False
        st.session_state._do_reset = True
        st.rerun()

    # Perform the actual reset on the fresh run
    if st.session_state.get("_do_reset", False):
        st.session_state._do_reset = False
        # Delete all widget keys so they reinitialize with defaults
        for key in ["tm_min", "tm_optimal", "tm_max", "gc_min", "gc_max",
                    "product_min", "product_max", "num_results"]:
            if key in st.session_state:
                del st.session_state[key]
        # Clear any derived state so the UI and results fully reset
        st.session_state.design_result = None
        st.session_state.selected_pair_idx = 0
        st.session_state.thresholds = QCThresholds()

    if "design_result" not in st.session_state:
        st.session_state.design_result = None
    if "selected_pair_idx" not in st.session_state:
        st.session_state.selected_pair_idx = 0
    if "sequence_input" not in st.session_state:
        st.session_state.sequence_input = ""
    if "thresholds" not in st.session_state:
        st.session_state.thresholds = QCThresholds()


def request_reset():
    """Callback to request parameter reset (called by Reset button)."""
    st.session_state._reset_requested = True


def clear_for_new_design():
    """Clear sequence inputs and results for a new design session."""
    # Clear file uploader by incrementing its key suffix
    st.session_state._file_uploader_key = st.session_state.get("_file_uploader_key", 0) + 1
    # Clear text area
    st.session_state.raw_sequence_input = ""
    # Clear design results
    st.session_state.design_result = None
    st.session_state.selected_pair_idx = 0


# -----------------------------------------------------------------------------
# Sidebar - Input Panel
# -----------------------------------------------------------------------------

def render_sidebar() -> tuple[Optional[str], Optional[str], QCThresholds, int]:
    """Render the sidebar input panel."""

    with st.sidebar:
        # New Design button at top
        if st.button("🔄 New Design", use_container_width=True, help="Clear current sequence and start fresh"):
            clear_for_new_design()
            st.rerun()

        st.markdown("---")
        st.markdown("### Input Sequence")

        # FASTA file uploader (key changes when cleared)
        file_key = f"file_uploader_{st.session_state.get('_file_uploader_key', 0)}"
        uploaded_file = st.file_uploader(
            "Upload FASTA file",
            type=["fasta", "fa", "fna", "txt"],
            help="Upload a FASTA file containing the target sequence",
            key=file_key,
        )

        st.markdown("**OR**")

        # Raw sequence text area (with key for clearing)
        raw_sequence = st.text_area(
            "Paste sequence",
            height=120,
            placeholder="ATGCGATCGATCGATCG...",
            help="Paste a raw nucleotide sequence or FASTA-formatted text",
            key="raw_sequence_input",
        )

        st.markdown("---")
        st.markdown("### Design Parameters")

        # Tm range configuration
        st.markdown("**Melting Temperature (Tm)**")

        col1, col2 = st.columns(2)
        with col1:
            tm_min = st.slider(
                "Min Tm",
                min_value=50.0,
                max_value=65.0,
                value=st.session_state.get("tm_min", 58.0),
                step=0.5,
                key="tm_min",
                help="Minimum acceptable Tm for primers",
            )
        with col2:
            tm_max = st.slider(
                "Max Tm",
                min_value=55.0,
                max_value=70.0,
                value=st.session_state.get("tm_max", 62.0),
                step=0.5,
                key="tm_max",
                help="Maximum acceptable Tm for primers",
            )

        tm_optimal = st.slider(
            "Optimal Tm",
            min_value=tm_min,
            max_value=tm_max,
            value=min(max(st.session_state.get("tm_optimal", 60.0), tm_min), tm_max),
            step=0.5,
            key="tm_optimal",
            help="Target optimal Tm for primer design",
        )

        st.markdown("---")

        # GC content configuration
        st.markdown("**GC Content (%)**")

        col1, col2 = st.columns(2)
        with col1:
            gc_min = st.slider(
                "Min GC%",
                min_value=20.0,
                max_value=60.0,
                value=st.session_state.get("gc_min", 40.0),
                step=1.0,
                key="gc_min",
                help="Minimum acceptable GC content",
            )
        with col2:
            gc_max = st.slider(
                "Max GC%",
                min_value=40.0,
                max_value=80.0,
                value=st.session_state.get("gc_max", 60.0),
                step=1.0,
                key="gc_max",
                help="Maximum acceptable GC content",
            )

        st.markdown("---")

        # Product size configuration
        st.markdown("**Product Size (bp)**")

        col1, col2 = st.columns(2)
        with col1:
            product_min = st.slider(
                "Min Size",
                min_value=50,
                max_value=150,
                value=st.session_state.get("product_min", 70),
                step=5,
                key="product_min",
                help="Minimum amplicon size",
            )
        with col2:
            product_max = st.slider(
                "Max Size",
                min_value=100,
                max_value=500,
                value=st.session_state.get("product_max", 200),
                step=10,
                key="product_max",
                help="Maximum amplicon size",
            )

        st.markdown("---")

        # Number of results
        num_results = st.slider(
            "Number of primer pairs",
            min_value=1,
            max_value=20,
            value=st.session_state.get("num_results", 5),
            key="num_results",
            help="Number of top-ranked primer pairs to return",
        )

        st.markdown("---")

        # Action buttons
        col1, col2 = st.columns([2, 1])
        with col1:
            design_clicked = st.button(
                "Design Primers",
                type="primary",
                use_container_width=True,
            )
        with col2:
            st.button(
                "Reset",
                use_container_width=True,
                on_click=request_reset,
            )

        # Build thresholds object
        thresholds = QCThresholds(
            tm_min=tm_min,
            tm_optimal=tm_optimal,
            tm_max=tm_max,
            gc_min=gc_min,
            gc_max=gc_max,
            product_min=product_min,
            product_max=product_max,
        )

        # Determine sequence source
        sequence_text = None
        sequence_name = None

        if uploaded_file is not None:
            try:
                file_content = uploaded_file.read().decode("utf-8")
                records = parse_fasta(file_content)
                if records:
                    sequence_text = str(records[0].seq)
                    sequence_name = records[0].id
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        elif raw_sequence.strip():
            try:
                records = parse_fasta(raw_sequence)
                if records:
                    sequence_text = str(records[0].seq)
                    sequence_name = records[0].id if records[0].id != "input_sequence" else "User Input"
            except Exception as e:
                st.error(f"Error parsing sequence: {str(e)}")

        return sequence_text, sequence_name, thresholds, num_results, design_clicked


# -----------------------------------------------------------------------------
# Main Content Area
# -----------------------------------------------------------------------------

def render_header():
    """Render the main header."""
    st.markdown('<h1 class="main-header">Primer Design Automation</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Automated PCR primer design with thermodynamic QC analysis '
        'and composite scoring for qPCR applications.</p>',
        unsafe_allow_html=True
    )


def render_sequence_stats(sequence: str, name: str, is_valid: bool, error_msg: Optional[str]):
    """Render sequence statistics panel."""

    st.markdown("### Target Sequence")

    stats = get_sequence_stats(sequence)

    # Validation status
    if is_valid:
        status_html = '<span class="status-pass">VALID</span>'
    else:
        status_html = f'<span class="status-fail">INVALID</span>'

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sequence Name</div>
            <div class="metric-value" style="font-size: 1.1rem;">{name}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Length</div>
            <div class="metric-value">{stats['length']:,} bp</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">GC Content</div>
            <div class="metric-value">{stats['gc_content']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Validation</div>
            <div class="metric-value">{status_html}</div>
        </div>
        """, unsafe_allow_html=True)

    if not is_valid and error_msg:
        st.error(f"Validation Error: {error_msg}")

    # Expandable sequence view
    with st.expander("View Sequence"):
        # Format sequence with line numbers
        seq_display = sequence.upper()
        lines = [seq_display[i:i+60] for i in range(0, len(seq_display), 60)]
        formatted = ""
        for i, line in enumerate(lines):
            pos = i * 60 + 1
            formatted += f"{pos:>6}  {line}\n"
        st.code(formatted, language=None)


def render_results_table(result: DesignResult, thresholds: QCThresholds):
    """Render the results table with primer pairs."""

    st.markdown("### Design Results")

    if not result.primer_pairs:
        st.warning("No primer pairs could be designed for this sequence. Try adjusting the parameters.")
        return None

    st.markdown(f"Found **{len(result.primer_pairs)}** primer pairs ranked by composite score.")

    # Build display dataframe
    rows = []
    for pair in result.primer_pairs:
        # Determine overall status based on key metrics
        statuses = [
            pair.forward.tm_status,
            pair.reverse.tm_status,
            pair.tm_match_status,
            pair.forward.gc_status,
            pair.reverse.gc_status,
            pair.product_size_status,
        ]

        if any(s == QCStatus.FAIL for s in statuses):
            overall = "FAIL"
            status_color = "#dc2626"
        elif any(s == QCStatus.WARN for s in statuses):
            overall = "WARN"
            status_color = "#d97706"
        else:
            overall = "PASS"
            status_color = "#059669"

        rows.append({
            "Rank": pair.rank,
            "Score": pair.composite_score,
            "Fwd Tm": f"{pair.forward.tm:.1f}°C",
            "Rev Tm": f"{pair.reverse.tm:.1f}°C",
            "ΔTm": f"{pair.tm_difference:.1f}°C",
            "Product": f"{pair.product_size} bp",
            "Status": overall,
        })

    df = pd.DataFrame(rows)

    # Style the dataframe
    def color_status(val):
        if val == "PASS":
            return "background-color: #d1fae5; color: #059669; font-weight: 600"
        elif val == "WARN":
            return "background-color: #fef3c7; color: #d97706; font-weight: 600"
        else:
            return "background-color: #fee2e2; color: #dc2626; font-weight: 600"

    def color_score(val):
        if val >= 70:
            return "background-color: #d1fae5; color: #059669; font-weight: 600"
        elif val >= 50:
            return "background-color: #fef3c7; color: #d97706; font-weight: 600"
        else:
            return "background-color: #fee2e2; color: #dc2626; font-weight: 600"

    styled_df = df.style.applymap(
        color_status, subset=["Status"]
    ).applymap(
        color_score, subset=["Score"]
    )

    # Row selection
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
    )

    # Selection dropdown
    pair_options = [f"Pair {p.rank}: Score {p.composite_score}" for p in result.primer_pairs]
    selected_idx = st.selectbox(
        "Select pair for detailed QC analysis",
        range(len(pair_options)),
        format_func=lambda x: pair_options[x],
    )

    return selected_idx


def render_pair_details(pair: PrimerPair, thresholds: QCThresholds):
    """Render detailed view for selected primer pair."""

    st.markdown("### Selected Primer Pair Details")

    # Score breakdown
    breakdown = get_score_breakdown(pair, thresholds)

    # Header with score
    score_class = get_score_class(pair.composite_score)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Composite Score</div>
            <div class="metric-value">
                <span class="score-badge {score_class}">{pair.composite_score}</span>
                <span style="font-size: 0.9rem; color: #64748b;"> / 100</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Rank</div>
            <div class="metric-value">#{pair.rank}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Product Size</div>
            <div class="metric-value">{pair.product_size} bp</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Primer sequences
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Forward Primer**")
        st.markdown(f'<div class="primer-seq">5\' - {pair.forward.sequence} - 3\'</div>', unsafe_allow_html=True)
        st.caption(f"Length: {pair.forward.length} bp | Position: {pair.forward.start}-{pair.forward.end}")

    with col2:
        st.markdown("**Reverse Primer**")
        st.markdown(f'<div class="primer-seq">5\' - {pair.reverse.sequence} - 3\'</div>', unsafe_allow_html=True)
        st.caption(f"Length: {pair.reverse.length} bp | Position: {pair.reverse.start}-{pair.reverse.end}")

    st.markdown("---")

    # QC Metrics breakdown
    st.markdown("### QC Metrics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Forward Primer QC**")

        metrics_fwd = [
            ("Melting Temperature", f"{pair.forward.tm:.1f}°C", pair.forward.tm_status, "Optimal: 58-62°C"),
            ("GC Content", f"{pair.forward.gc_percent:.1f}%", pair.forward.gc_status, "Optimal: 40-60%"),
            ("Hairpin ΔG", format_dg(pair.forward.hairpin_dg), pair.forward.hairpin_status, "Should be > -2.0 kcal/mol"),
            ("Self-Dimer ΔG", format_dg(pair.forward.self_dimer_dg), pair.forward.self_dimer_status, "Should be > -9.0 kcal/mol"),
            ("3' Terminal Base", pair.forward.three_prime_base, pair.forward.three_prime_status, "G or C preferred"),
        ]

        for name, value, status, tooltip in metrics_fwd:
            color = get_status_color(status)
            icon = get_status_icon(status)
            st.markdown(
                f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; '
                f'border-bottom: 1px solid #f1f5f9;">'
                f'<span style="color: #475569;" title="{tooltip}">{name}</span>'
                f'<span><span style="color: {color}; margin-right: 0.5rem;">{icon}</span>'
                f'<span style="font-weight: 500;">{value}</span></span></div>',
                unsafe_allow_html=True
            )

    with col2:
        st.markdown("**Reverse Primer QC**")

        metrics_rev = [
            ("Melting Temperature", f"{pair.reverse.tm:.1f}°C", pair.reverse.tm_status, "Optimal: 58-62°C"),
            ("GC Content", f"{pair.reverse.gc_percent:.1f}%", pair.reverse.gc_status, "Optimal: 40-60%"),
            ("Hairpin ΔG", format_dg(pair.reverse.hairpin_dg), pair.reverse.hairpin_status, "Should be > -2.0 kcal/mol"),
            ("Self-Dimer ΔG", format_dg(pair.reverse.self_dimer_dg), pair.reverse.self_dimer_status, "Should be > -9.0 kcal/mol"),
            ("3' Terminal Base", pair.reverse.three_prime_base, pair.reverse.three_prime_status, "G or C preferred"),
        ]

        for name, value, status, tooltip in metrics_rev:
            color = get_status_color(status)
            icon = get_status_icon(status)
            st.markdown(
                f'<div style="display: flex; justify-content: space-between; padding: 0.4rem 0; '
                f'border-bottom: 1px solid #f1f5f9;">'
                f'<span style="color: #475569;" title="{tooltip}">{name}</span>'
                f'<span><span style="color: {color}; margin-right: 0.5rem;">{icon}</span>'
                f'<span style="font-weight: 500;">{value}</span></span></div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    # Pair-level metrics
    st.markdown("**Pair-Level Metrics**")

    col1, col2, col3 = st.columns(3)

    with col1:
        color = get_status_color(pair.tm_match_status)
        icon = get_status_icon(pair.tm_match_status)
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Tm Difference</div>'
            f'<div class="metric-value"><span style="color: {color}; margin-right: 0.5rem;">{icon}</span>'
            f'{pair.tm_difference:.1f}°C</div>'
            f'<div style="font-size: 0.75rem; color: #94a3b8;">Should be &lt; 2°C</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col2:
        color = get_status_color(pair.cross_dimer_status)
        icon = get_status_icon(pair.cross_dimer_status)
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Cross-Dimer ΔG</div>'
            f'<div class="metric-value"><span style="color: {color}; margin-right: 0.5rem;">{icon}</span>'
            f'{pair.cross_dimer_dg:.1f} kcal/mol</div>'
            f'<div style="font-size: 0.75rem; color: #94a3b8;">Should be &gt; -9.0 kcal/mol</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col3:
        color = get_status_color(pair.product_size_status)
        icon = get_status_icon(pair.product_size_status)
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">Product Size</div>'
            f'<div class="metric-value"><span style="color: {color}; margin-right: 0.5rem;">{icon}</span>'
            f'{pair.product_size} bp</div>'
            f'<div style="font-size: 0.75rem; color: #94a3b8;">Optimal: 70-200 bp for qPCR</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Score breakdown
    st.markdown("**Score Breakdown**")

    score_components = [
        ("Tm Score", breakdown["tm_score"], 25, "Melting temperature optimization"),
        ("GC Score", breakdown["gc_score"], 15, "GC content balance"),
        ("Structure Score", breakdown["structure_score"], 30, "Secondary structure avoidance"),
        ("3' End Score", breakdown["three_prime_score"], 20, "3' terminal base quality"),
        ("Product Score", breakdown["product_score"], 10, "Amplicon size optimization"),
    ]

    for name, score, max_score, description in score_components:
        pct = (score / max_score) * 100
        if pct >= 70:
            bar_color = "#059669"
        elif pct >= 50:
            bar_color = "#d97706"
        else:
            bar_color = "#dc2626"

        st.markdown(
            f'<div style="margin-bottom: 0.75rem;">'
            f'<div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">'
            f'<span style="font-size: 0.875rem; color: #475569;" title="{description}">{name}</span>'
            f'<span style="font-size: 0.875rem; font-weight: 500;">{score:.1f} / {max_score}</span>'
            f'</div>'
            f'<div style="background-color: #e2e8f0; border-radius: 4px; height: 8px; overflow: hidden;">'
            f'<div style="background-color: {bar_color}; width: {pct}%; height: 100%;"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )


def render_export_section(result: DesignResult):
    """Render export controls."""

    st.markdown("### Export Results")

    col1, col2 = st.columns([1, 3])

    with col1:
        csv_bytes = export_csv_bytes(result)
        st.download_button(
            label="Download CSV",
            data=csv_bytes,
            file_name=f"primer_design_{result.target_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        st.caption(
            "Export includes all primer pairs with full QC metrics. "
            "CSV format is compatible with Excel and other analysis tools."
        )


def render_welcome_message():
    """Render welcome message when no sequence is loaded."""

    st.markdown("""
    <div class="info-box">
        <h4 style="margin-top: 0; color: #1e40af;">Getting Started</h4>
        <p style="margin-bottom: 0.5rem;">To design primers for your target sequence:</p>
        <ol style="margin-bottom: 0; padding-left: 1.5rem;">
            <li>Upload a FASTA file or paste your sequence in the sidebar</li>
            <li>Adjust design parameters if needed (Tm, GC%, product size)</li>
            <li>Click <strong>Design Primers</strong> to generate ranked primer pairs</li>
            <li>Review QC metrics and export results</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # Example sequence for testing
    with st.expander("Load Example Sequence"):
        example_seq = (
            ">SARS-CoV-2_Spike_Fragment\n"
            "ATGTTTGTTTTTCTTGTTTTATTGCCACTAGTCTCTAGTCAGTGTGTTAATCTTACAACCAGAACTCAATTACCCCCTGCAT"
            "ACACTAATTCTTTCACACGTGGTGTTTATTACCCTGACAAAGTTTTCAGATCCTCAGTTTTACATTCAACTCAGGACTTGTT"
            "CTTACCTTTCTTTTCCAATGTTACTTGGTTCCATGCTATACATGTCTCTGGGACCAATGGTACTAAGAGGTTTGATAACCCT"
            "GTCCTACCATTTAATGATGGTGTTTATTTTGCTTCCACTGAGAAGTCTAACATAATAAGAGGCTGGATTTTTGGTACTACTT"
            "TAGATTCGAAGACCCAGTCCCTACTTATTGTTAATAACGCTACTAATGTTGTTATTAAAGTCTGTGAATTTCAATTTTGTAA"
        )

        if st.button("Use Example Sequence"):
            st.session_state.example_loaded = True
            st.session_state.example_seq = example_seq
            st.rerun()


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

def main():
    """Main application entry point."""

    initialize_session_state()

    # Render sidebar and get inputs
    sequence_text, sequence_name, thresholds, num_results, design_clicked = render_sidebar()

    # Check for example sequence
    if st.session_state.get("example_loaded"):
        try:
            records = parse_fasta(st.session_state.example_seq)
            if records:
                sequence_text = str(records[0].seq)
                sequence_name = records[0].id
        except Exception:
            pass

    # Render main content
    render_header()

    if sequence_text is None:
        render_welcome_message()
        return

    # Validate sequence
    is_valid, error_msg = validate_sequence(sequence_text)

    # Show sequence stats
    render_sequence_stats(sequence_text, sequence_name or "Unknown", is_valid, error_msg)

    if not is_valid:
        return

    # Design primers when button clicked
    if design_clicked:
        with st.spinner("Designing primers..."):
            try:
                # Get Primer3 settings from thresholds
                settings = get_primer3_settings_from_thresholds(thresholds)

                # Design primers
                pairs = design_primers(
                    sequence_text,
                    settings=settings,
                    num_return=num_results * 2,  # Request extra to filter
                )

                if not pairs:
                    st.warning(
                        "No primer pairs could be designed with the current parameters. "
                        "Try relaxing the constraints (wider Tm range, larger product size range)."
                    )
                    return

                # Analyze pairs
                for pair in pairs:
                    analyze_pair(pair)

                # Score and rank
                scored_pairs = score_pairs(pairs, thresholds)
                ranked_pairs = rank_pairs(scored_pairs)

                # Limit to requested number
                final_pairs = ranked_pairs[:num_results]

                # Create result object
                result = DesignResult(
                    target_name=sequence_name or "input_sequence",
                    target_sequence=sequence_text,
                    primer_pairs=final_pairs,
                )

                st.session_state.design_result = result

            except Exception as e:
                st.error(f"Error during primer design: {str(e)}")
                return

    # Display results if available
    if st.session_state.design_result is not None:
        result = st.session_state.design_result

        st.markdown("---")

        # Results table with selection
        selected_idx = render_results_table(result, thresholds)

        if selected_idx is not None and result.primer_pairs:
            st.markdown("---")

            # Detailed pair view
            selected_pair = result.primer_pairs[selected_idx]
            render_pair_details(selected_pair, thresholds)

            st.markdown("---")

            # Export section
            render_export_section(result)


if __name__ == "__main__":
    main()
