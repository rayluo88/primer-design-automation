"""
Unit tests for primer_designer module.

Tests Primer3 wrapper functionality and primer pair generation.
"""

import pytest

from src.primer_designer import (
    design_primers,
    get_primer3_settings_from_thresholds,
    DEFAULT_PRIMER3_SETTINGS,
    _th_to_dg,
)
from src.models import PrimerPair, QCThresholds


# Test sequence - synthetic 200bp sequence with balanced GC content
TEST_SEQUENCE = (
    "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
    "GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
    "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCA"
    "TACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT"
)


class TestDesignPrimers:
    """Tests for design_primers function."""

    def test_generates_primer_pairs(self):
        """Test that primer pairs are generated for valid sequence."""
        pairs = design_primers(TEST_SEQUENCE)

        assert len(pairs) > 0
        assert all(isinstance(p, PrimerPair) for p in pairs)

    def test_primer_pair_structure(self):
        """Test that primer pairs have required fields."""
        pairs = design_primers(TEST_SEQUENCE, num_return=1)

        if len(pairs) > 0:
            pair = pairs[0]
            assert pair.forward is not None
            assert pair.reverse is not None
            assert pair.forward.sequence != ""
            assert pair.reverse.sequence != ""
            assert pair.product_size > 0

    def test_primer_tm_in_range(self):
        """Test that generated primers have Tm in expected range."""
        pairs = design_primers(TEST_SEQUENCE)

        for pair in pairs:
            # Default Tm range is 58-62
            assert 50.0 < pair.forward.tm < 70.0
            assert 50.0 < pair.reverse.tm < 70.0

    def test_primer_gc_in_range(self):
        """Test that generated primers have GC% in expected range."""
        pairs = design_primers(TEST_SEQUENCE)

        for pair in pairs:
            # Default GC range is 40-60%
            assert 30.0 < pair.forward.gc_percent < 70.0
            assert 30.0 < pair.reverse.gc_percent < 70.0

    def test_num_return_limits_results(self):
        """Test that num_return parameter limits results."""
        pairs_5 = design_primers(TEST_SEQUENCE, num_return=5)
        pairs_2 = design_primers(TEST_SEQUENCE, num_return=2)

        assert len(pairs_2) <= 2
        assert len(pairs_5) <= 5

    def test_custom_settings_applied(self):
        """Test that custom settings are applied."""
        custom_settings = {
            "PRIMER_OPT_TM": 65.0,
            "PRIMER_MIN_TM": 63.0,
            "PRIMER_MAX_TM": 67.0,
        }

        pairs = design_primers(TEST_SEQUENCE, settings=custom_settings, num_return=3)

        # Primers should have higher Tm with these settings
        for pair in pairs:
            assert pair.forward.tm >= 60.0  # Should be in higher range
            assert pair.reverse.tm >= 60.0

    def test_short_sequence_raises_error(self):
        """Test that too-short sequence raises ValueError."""
        short_seq = "ATGCGATCGATC"  # 12 bp, below 50 bp minimum

        with pytest.raises(ValueError, match="too short"):
            design_primers(short_seq)

    def test_exactly_50bp_sequence(self):
        """Test behavior at minimum length boundary."""
        min_seq = "A" * 50

        # Should not raise, though may not find good primers
        try:
            pairs = design_primers(min_seq)
            # May return 0 pairs due to poor sequence, but shouldn't error
            assert isinstance(pairs, list)
        except ValueError as e:
            # Also acceptable if Primer3 rejects the sequence
            assert "Primer3 error" in str(e) or "too short" in str(e)

    def test_lowercase_handled(self):
        """Test that lowercase sequences are handled."""
        lowercase_seq = TEST_SEQUENCE.lower()

        pairs = design_primers(lowercase_seq)

        assert len(pairs) > 0

    def test_returns_empty_for_difficult_sequence(self):
        """Test behavior for sequence where no primers can be designed."""
        # Sequence with too many Ns
        difficult_seq = "N" * 200

        # Should either raise error or return empty list
        try:
            pairs = design_primers(difficult_seq)
            assert isinstance(pairs, list)
        except ValueError:
            pass  # Expected for invalid sequence


class TestGetPrimer3SettingsFromThresholds:
    """Tests for get_primer3_settings_from_thresholds function."""

    def test_converts_thresholds_to_settings(self):
        """Test that thresholds are converted to Primer3 settings."""
        thresholds = QCThresholds(
            tm_min=55.0,
            tm_optimal=58.0,
            tm_max=61.0,
            gc_min=35.0,
            gc_max=65.0,
            product_min=80,
            product_max=250,
        )

        settings = get_primer3_settings_from_thresholds(thresholds)

        assert settings["PRIMER_MIN_TM"] == 55.0
        assert settings["PRIMER_OPT_TM"] == 58.0
        assert settings["PRIMER_MAX_TM"] == 61.0
        assert settings["PRIMER_MIN_GC"] == 35.0
        assert settings["PRIMER_MAX_GC"] == 65.0
        assert settings["PRIMER_PRODUCT_SIZE_RANGE"] == [[80, 250]]

    def test_default_thresholds_conversion(self):
        """Test conversion of default thresholds."""
        thresholds = QCThresholds()

        settings = get_primer3_settings_from_thresholds(thresholds)

        assert "PRIMER_MIN_TM" in settings
        assert "PRIMER_MAX_TM" in settings
        assert "PRIMER_MIN_GC" in settings
        assert "PRIMER_MAX_GC" in settings


class TestThToDg:
    """Tests for _th_to_dg helper function."""

    def test_zero_th_returns_zero(self):
        """Test that zero Th returns zero ΔG."""
        assert _th_to_dg(0.0) == 0.0

    def test_negative_th_returns_zero(self):
        """Test that negative Th returns zero ΔG."""
        assert _th_to_dg(-10.0) == 0.0

    def test_positive_th_returns_negative_dg(self):
        """Test that positive Th returns negative ΔG."""
        dg = _th_to_dg(50.0)

        # Higher Tm = more stable = more negative ΔG
        assert dg < 0

    def test_higher_th_gives_more_negative_dg(self):
        """Test that higher Th gives more negative ΔG."""
        dg_low = _th_to_dg(30.0)
        dg_high = _th_to_dg(60.0)

        # Higher Th should give more negative ΔG
        assert dg_high < dg_low

    def test_expected_approximation(self):
        """Test the approximation formula: ΔG ≈ -(Tm - 25) * 0.3."""
        th = 50.0
        expected_dg = -((50.0 - 25) * 0.3)  # -7.5

        assert _th_to_dg(th) == expected_dg


class TestDefaultSettings:
    """Tests for DEFAULT_PRIMER3_SETTINGS."""

    def test_default_settings_exist(self):
        """Test that default settings are defined."""
        assert DEFAULT_PRIMER3_SETTINGS is not None
        assert isinstance(DEFAULT_PRIMER3_SETTINGS, dict)

    def test_essential_keys_present(self):
        """Test that essential Primer3 keys are present."""
        essential_keys = [
            "PRIMER_OPT_SIZE",
            "PRIMER_MIN_SIZE",
            "PRIMER_MAX_SIZE",
            "PRIMER_OPT_TM",
            "PRIMER_MIN_TM",
            "PRIMER_MAX_TM",
            "PRIMER_MIN_GC",
            "PRIMER_MAX_GC",
            "PRIMER_NUM_RETURN",
        ]

        for key in essential_keys:
            assert key in DEFAULT_PRIMER3_SETTINGS

    def test_default_values_sensible(self):
        """Test that default values are sensible for qPCR."""
        settings = DEFAULT_PRIMER3_SETTINGS

        # Size should be around 20 bp
        assert 15 <= settings["PRIMER_OPT_SIZE"] <= 25

        # Tm should be around 60°C
        assert 55.0 <= settings["PRIMER_OPT_TM"] <= 65.0

        # GC should be 40-60%
        assert settings["PRIMER_MIN_GC"] >= 30.0
        assert settings["PRIMER_MAX_GC"] <= 70.0
