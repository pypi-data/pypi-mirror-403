"""
Unit tests for the Geometric Drift calculation utility.
Target: src/sgndrift/psd/drift.py
"""

import pytest
import numpy as np
from sgndrift.psd.drift import calculate_fisher_velocity


class TestFisherVelocityBasics:
    """Tests basic input/output behavior and identity properties."""

    @pytest.fixture
    def basic_setup(self):
        """Standard fixture: 5 frequency bins, dt=1.0, flat PSD."""
        freqs = np.array([10, 20, 30, 40, 50], dtype=float)
        df = 10.0
        psd_prev = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        return freqs, df, psd_prev

    def test_static_psd_zero_drift(self, basic_setup):
        """Identity: If the PSD does not change, velocity must be zero."""
        freqs, df, psd = basic_setup
        res = calculate_fisher_velocity(
            current_psd=psd, previous_psd=psd, dt=1.0, frequencies=freqs, delta_f=df
        )
        assert res["total"] == 0.0

    def test_dt_scaling(self, basic_setup):
        """
        Scaling: Velocity is inversely proportional to dt.
        v ~ dS/dt. If dt doubles, the rate of change halves.
        """
        freqs, df, psd_prev = basic_setup
        psd_curr = psd_prev * 2.0  # Constant change across all bins

        # Case 1: dt = 1.0
        res1 = calculate_fisher_velocity(
            psd_curr, psd_prev, dt=1.0, frequencies=freqs, delta_f=df
        )

        # Case 2: dt = 2.0
        res2 = calculate_fisher_velocity(
            psd_curr, psd_prev, dt=2.0, frequencies=freqs, delta_f=df
        )

        # The calculated velocity should be exactly half
        assert np.isclose(res1["total"], res2["total"] * 2.0)


class TestFisherVelocityMath:
    """Tests the numerical correctness of the geometric formula."""

    def test_manual_calculation(self):
        """
        Verify against a hand-calculated example to ensure the integral is correct.

        Formula: Integral [ ((S_new - S_old) / (dt * S_new))^2 ] df

        Setup:
            dt = 0.5, df = 100, Freqs = [100, 200] (2 bins)

            Bin 1: S_old=2, S_new=4
                   S_dot = (4 - 2)/0.5 = 4
                   Term = (4 / 4)^2 = 1

            Bin 2: S_old=4, S_new=2
                   S_dot = (2 - 4)/0.5 = -4
                   Term = (-4 / 2)^2 = (-2)^2 = 4

            Integral = (1 + 4) * df = 500
            Velocity = sqrt(500) approx 22.3606
        """
        freqs = np.array([100, 200])
        df = 100.0
        dt = 0.5

        psd_prev = np.array([2.0, 4.0])
        psd_curr = np.array([4.0, 2.0])

        res = calculate_fisher_velocity(
            psd_curr, psd_prev, dt=dt, frequencies=freqs, delta_f=df
        )

        expected_velocity = np.sqrt(500)
        assert np.isclose(res["total"], expected_velocity)

    def test_zero_handling(self):
        """Ensure the code does not crash on PSD=0 (singularities)."""
        freqs = np.array([10.0])
        psd_prev = np.array([1.0])
        psd_curr = np.array([0.0])  # Current PSD is 0, metric singularity

        # The implementation should safely handle or mask this
        res = calculate_fisher_velocity(
            psd_curr, psd_prev, dt=1.0, frequencies=freqs, delta_f=1.0
        )
        # Should return 0.0 or finite value, not NaN/Inf
        assert np.isfinite(res["total"])
        assert res["total"] == 0.0


class TestFisherVelocityBands:
    """Tests the frequency masking and band integration logic."""

    @pytest.fixture
    def spectral_data(self):
        # Freqs: 10, 20, 30, 40
        freqs = np.array([10, 20, 30, 40], dtype=float)
        df = 1.0
        dt = 1.0

        # Setup constant drift contribution:
        # S_prev=1, S_curr=2 => diff=1 => ratio=0.5 => sq=0.25
        # Every active bin adds 0.25 to the integral sum
        psd_prev = np.ones_like(freqs)
        psd_curr = np.ones_like(freqs) * 2.0
        return freqs, df, dt, psd_curr, psd_prev

    def test_band_isolation(self, spectral_data):
        """Verify that bands calculate drift ONLY for their specific bins."""
        freqs, df, dt, psd_curr, psd_prev = spectral_data

        bands = {
            "low": (5, 25),  # Covers 10, 20 (2 bins) -> sum=0.5 -> v=sqrt(0.5)
            "high": (25, 45),  # Covers 30, 40 (2 bins) -> sum=0.5 -> v=sqrt(0.5)
            "empty": (100, 200),  # Covers nothing -> 0
        }

        res = calculate_fisher_velocity(
            psd_curr,
            psd_prev,
            dt=dt,
            frequencies=freqs,
            delta_f=df,
            bands=bands,
        )

        assert np.isclose(res["low"], np.sqrt(0.5))
        assert np.isclose(res["high"], np.sqrt(0.5))
        assert res["empty"] == 0.0
        # If bands are provided, 'total' should not be auto-generated
        assert "total" not in res

    def test_band_boundaries(self, spectral_data):
        """Test inclusive/exclusive logic (min <= f < max)."""
        freqs, df, dt, psd_curr, psd_prev = spectral_data
        # Freqs are [10, 20, 30, 40]

        # Band [10, 20) should include 10, exclude 20.
        bands = {"test": (10, 20)}

        res = calculate_fisher_velocity(
            psd_curr, psd_prev, dt=dt, frequencies=freqs, delta_f=df, bands=bands
        )

        # 1 bin (10Hz) * 0.25 contribution = 0.25 integral
        assert np.isclose(res["test"], np.sqrt(0.25))


class TestFisherVelocityErrors:
    """Tests error handling for invalid inputs."""

    def test_invalid_dt(self):
        """dt must be positive to define a derivative."""
        psd = np.array([1.0])
        freqs = np.array([1.0])

        with pytest.raises(ValueError, match="must be positive"):
            calculate_fisher_velocity(psd, psd, dt=0, frequencies=freqs, delta_f=1)

        with pytest.raises(ValueError, match="must be positive"):
            calculate_fisher_velocity(psd, psd, dt=-1.0, frequencies=freqs, delta_f=1)
