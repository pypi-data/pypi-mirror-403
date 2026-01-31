"""
Unit tests for Geometric Diagnostics (Fisher Velocity).
"""

import pytest
import numpy as np
from sgnts.base import EventFrame, EventBuffer, Offset
from sgndrift.transforms.drift import FisherVelocity, DriftEvent
from sgndrift.transforms.psd import PSDEvent

# Integration test imports
from sgn.apps import Pipeline
from sgn.sinks import CollectSink
from sgnligo.sources.gwdata_noise_source import GWDataNoiseSource
from sgndrift.transforms.psd import RecursivePSD


class TestFisherVelocityInitialization:
    def test_default_init(self):
        el = FisherVelocity(
            name="test", sink_pad_names=("in",), source_pad_names=("out",)
        )
        assert el.bands == {}
        assert el._prev_data is None

        # Check pad names in the unaligned list
        unaligned_names = [p.name for p in el.unaligned_sink_pads]
        assert "test:snk:in" in unaligned_names

        assert el.input_frame_types["in"] == EventFrame

    def test_custom_bands(self):
        bands = {"low": (10, 50), "high": (100, 200)}
        el = FisherVelocity(
            name="test",
            sink_pad_names=("in",),
            source_pad_names=("out",),
            bands=bands,
        )
        assert el.bands == bands


class TestFisherVelocityProcessing:
    @pytest.fixture
    def element(self):
        return FisherVelocity(
            name="fisher", sink_pad_names=("in",), source_pad_names=("out",)
        )

    def _make_frame(self, data, epoch, freqs, delta_f=1.0):
        event = PSDEvent(
            data=np.array(data, dtype=float),
            frequencies=np.array(freqs, dtype=float),
            epoch=float(epoch),
            delta_f=float(delta_f),
        )

        ts = Offset.fromsec(epoch)
        dur = Offset.fromsec(1.0)
        te = ts + dur

        buf = EventBuffer.from_span(ts, te, [event])
        return EventFrame(data=[buf])

    def test_gap_handling(self, element):
        gap_frame = EventFrame(is_gap=True)
        # Populate unaligned_data to simulate behavior for unaligned pads
        element.unaligned_data = {element.sink_pads[0]: gap_frame}
        res = element.new(element.source_pads[0])
        assert res.is_gap

    def test_startup_transient(self, element):
        freqs = np.linspace(0, 100, 101)
        data = np.ones_like(freqs)

        frame = self._make_frame(data, 0.0, freqs)
        element.unaligned_data = {element.sink_pads[0]: frame}

        res = element.new(element.source_pads[0])

        assert not res.is_gap
        event = res.data[0].data[0]
        assert isinstance(event, DriftEvent)
        assert event.data["total"] == 0.0
        assert np.array_equal(element._prev_data, data)

    def test_step_change_math(self, element):
        bins = 4
        df = 1.0
        freqs = np.arange(bins) * df

        data0 = np.ones(bins)
        element.unaligned_data = {
            element.sink_pads[0]: self._make_frame(data0, 0.0, freqs, df)
        }
        element.new(element.source_pads[0])

        data1 = np.full(bins, 2.0)
        element.unaligned_data = {
            element.sink_pads[0]: self._make_frame(data1, 1.0, freqs, df)
        }
        res = element.new(element.source_pads[0])

        event = res.data[0].data[0]
        expected_velocity = 1.0
        np.testing.assert_allclose(event.data["total"], expected_velocity)


class TestFisherVelocityPipeline:
    def test_multiband_drift_analysis(self):
        src = GWDataNoiseSource(
            name="source",
            channel_dict={"H1": "H1:FAKE-STRAIN"},
            duration=4.0,
            t0=1000000000,
        )
        rate = src.channel_info["H1"]["rate"]

        psd_est = RecursivePSD(
            name="psd",
            sink_pad_names=("in",),
            source_pad_names=("out",),
            fft_length=1.0,
            overlap=0.5,
            sample_rate=rate,
            alpha=0.2,
        )

        bands = {"seismic": (10, 50), "bucket": (100, 300)}
        fisher = FisherVelocity(
            name="fisher",
            sink_pad_names=("in",),
            source_pad_names=("out",),
            bands=bands,
        )

        # Use extract_data=False to get full frames
        sink = CollectSink(name="sink", sink_pad_names=("in",), extract_data=False)

        pipe = Pipeline()
        pipe.insert(src, psd_est, fisher, sink)
        pipe.link(
            {
                psd_est.snks["in"]: src.srcs["H1:FAKE-STRAIN"],
                fisher.snks["in"]: psd_est.srcs["out"],
                sink.snks["in"]: fisher.srcs["out"],
            }
        )
        pipe.run()

        frames = sink.collects["in"]
        assert len(frames) > 3

        # Verify output structure
        event = frames[-1].data[0].data[0]
        assert isinstance(event, DriftEvent)
        assert "seismic" in event.data
        assert "bucket" in event.data
        assert event.data["seismic"] >= 0.0

    def test_pipeline_without_bands(self):
        src = GWDataNoiseSource(
            name="source",
            channel_dict={"H1": "H1:FAKE-STRAIN"},
            duration=2.0,
            t0=1000000000,
        )
        rate = src.channel_info["H1"]["rate"]

        psd_est = RecursivePSD(
            name="psd",
            sink_pad_names=("in",),
            source_pad_names=("out",),
            fft_length=1.0,
            overlap=0.5,
            sample_rate=rate,
        )

        fisher = FisherVelocity(
            name="fisher",
            sink_pad_names=("in",),
            source_pad_names=("out",),
        )

        sink = CollectSink(name="sink", sink_pad_names=("in",), extract_data=False)

        pipe = Pipeline()
        pipe.insert(src, psd_est, fisher, sink)
        pipe.link(
            {
                psd_est.snks["in"]: src.srcs["H1:FAKE-STRAIN"],
                fisher.snks["in"]: psd_est.srcs["out"],
                sink.snks["in"]: fisher.srcs["out"],
            }
        )
        pipe.run()

        frames = sink.collects["in"]
        assert len(frames) > 0
        event = frames[-1].data[0].data[0]
        assert "total" in event.data


class TestFisherVelocityScience:
    """
    Scientific validation of the Fisher Velocity metric with analytic checks.
    """

    def _calculate_drift(self, s1, s2, t1, t2, freqs, bands=None):
        """Helper to compute drift between two PSD snapshots."""
        delta_f = freqs[1] - freqs[0]

        # Setup Element
        el = FisherVelocity(
            name="fisher",
            sink_pad_names=("in",),
            source_pad_names=("out",),
            bands=bands or {},
        )
        el.configure()

        # Frame 1
        event1 = PSDEvent(data=s1, frequencies=freqs, epoch=t1, delta_f=delta_f)
        ts1 = Offset.fromsec(t1)
        te1 = Offset.fromsec(t1 + 1.0)
        buf1 = EventBuffer.from_span(ts1, te1, [event1])
        frame1 = EventFrame(data=[buf1])

        el.unaligned_data = {el.sink_pads[0]: frame1}
        el.new(el.source_pads[0])  # Initialize state

        # Frame 2
        event2 = PSDEvent(data=s2, frequencies=freqs, epoch=t2, delta_f=delta_f)
        ts2 = Offset.fromsec(t2)
        te2 = Offset.fromsec(t2 + 1.0)
        buf2 = EventBuffer.from_span(ts2, te2, [event2])
        frame2 = EventFrame(data=[buf2])

        el.unaligned_data = {el.sink_pads[0]: frame2}
        out = el.new(el.source_pads[0])

        return out.data[0].data[0].data

    def test_amplitude_scaling_law(self):
        """
        Verify that a global amplitude scaling S2 = alpha * S1 results in
        drift v = (|alpha - 1| / (alpha * dt)) * sqrt(BW).
        This result is independent of the spectral shape S1.
        """
        # Setup: 400 bins of 0.25 Hz -> 100 Hz BW
        df = 0.25
        freqs = np.arange(0, 100, df)

        # Define an arbitrary spectral shape (e.g. 1/f decay)
        # Avoid div by zero at f=0 by adding offset
        s1 = 1.0 / (freqs + 1.0)

        # Constants
        alpha = 1.5
        dt = 2.0

        s2 = alpha * s1

        # Execute
        res = self._calculate_drift(s1, s2, 0.0, dt, freqs)

        # Analytic Expectation derivation:
        # S_dot = (S2 - S1)/dt = (alpha - 1)S1 / dt
        # Integrand = (S_dot / S2)^2 = [ (alpha-1)S1 / (dt * alpha * S1) ]^2
        #           = [ (alpha-1) / (alpha * dt) ]^2  <-- Constant!
        # Velocity = sqrt( Sum(Integrand) * df )
        #          = sqrt( Integrand * BW )
        #          = | (alpha-1)/(alpha*dt) | * sqrt(BW)

        bw = len(freqs) * df  # Bandwidth
        term = abs(alpha - 1) / (alpha * dt)
        expected = term * np.sqrt(bw)

        np.testing.assert_allclose(res["total"], expected, rtol=1e-5)

    def test_time_step_dependence(self):
        """
        Verify velocity scales inversely with dt for a fixed PSD change.
        v ~ 1/dt.
        """
        freqs = np.linspace(0, 10, 11)  # 1Hz bins
        s1 = np.ones_like(freqs)
        s2 = 2.0 * s1  # Step to 2.0

        # Case A: dt = 1.0
        res_a = self._calculate_drift(s1, s2, 0.0, 1.0, freqs)

        # Case B: dt = 0.5 (Twice as fast)
        res_b = self._calculate_drift(s1, s2, 0.0, 0.5, freqs)

        # Since v ~ dS/dt, halving dt doubles v.
        assert np.isclose(res_b["total"], 2.0 * res_a["total"])

    def test_band_isolation(self):
        """
        Verify that changes restricted to a specific band do not affect others.
        """
        freqs = np.linspace(0, 100, 101)  # 0 to 100 Hz, df=1.0
        bands = {"low": (0, 50), "high": (50, 100)}

        s1 = np.ones_like(freqs)
        s2 = np.ones_like(freqs)

        # Perturb only high frequency (indices 50 to 100)
        # Note: Band 'high' is [50, 100). Indices 50..99.
        s2[50:] = 2.0

        res = self._calculate_drift(s1, s2, 0.0, 1.0, freqs, bands)

        # Low band (0-50) should be 0 drift (S1=1, S2=1)
        assert res["low"] == 0.0

        # High band (50-100) should be non-zero
        assert res["high"] > 0.0

        # Verify analytic for High band:
        # S1=1, S2=2, dt=1.
        # Integrand = ((2-1)/2)^2 = 0.25.
        # Bandwidth = 50 bins * 1.0 = 50.0.
        # Expected = sqrt(0.25 * 50) = sqrt(12.5) ~ 3.535
        expected = np.sqrt(0.25 * 50.0)
        np.testing.assert_allclose(res["high"], expected)
