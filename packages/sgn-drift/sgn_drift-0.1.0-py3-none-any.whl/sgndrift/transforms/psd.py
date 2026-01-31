"""
SGN Elements for PSD Estimation.
wraps sgnligo.psd.estimators logic into TSTransform elements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import scipy.signal
from sgn.base import SourcePad
from sgnts.base import (
    AdapterConfig,
    EventBuffer,
    EventFrame,
    Offset,
    TSTransform,
)

from sgndrift.psd.estimators import BaseEstimator, MGMEstimator, RecursiveEstimator

# Optional LAL import for conversion methods
try:
    import lal
except ImportError:
    lal = None


@dataclass
class PSDEvent:
    """
    Container for a PSD estimate event (Pure Python/NumPy).
    Decoupled from LAL to ensure stability in non-LAL environments.
    """

    data: np.ndarray
    frequencies: np.ndarray
    epoch: float
    delta_f: float

    def to_lal(self) -> Optional[object]:
        """
        Convert to LAL REAL8FrequencySeries if LAL is available.
        Uses standard 'strain^2 s' unit definition.
        """
        if lal is None:
            return None

        try:
            # Standard unit construction used in sgnligo.psd.psd
            unit = lal.Unit("strain^2 s")

            series = lal.CreateREAL8FrequencySeries(
                "psd",
                lal.LIGOTimeGPS(self.epoch),
                0.0,
                self.delta_f,
                unit,
                len(self.data),
            )
            series.data.data = self.data
            return series
        except Exception:
            return None


@dataclass
class PSDEstimator(TSTransform):
    """
    Base TSTransform for PSD Estimation.
    Outputs EventFrame containing PSDEvent objects.
    """

    fft_length: float = 4.0
    overlap: float = 0.5
    sample_rate: int = 16384
    window_type: str = "hann"

    # Internal state
    _estimator: BaseEstimator = field(init=False, repr=False, default=None)
    _window: np.ndarray = field(init=False, repr=False, default=None)
    _freqs: np.ndarray = field(init=False, repr=False, default=None)
    _norm_factor: float = field(init=False, repr=False, default=1.0)
    _delta_f: float = field(init=False, repr=False, default=0.0)

    def __post_init__(self):
        n_samples = int(self.fft_length * self.sample_rate)
        stride = int(n_samples * (1 - self.overlap))
        overlap_samples = n_samples - stride

        self.adapter_config = AdapterConfig()
        self.adapter_config.stride = Offset.fromsamples(stride, self.sample_rate)
        self.adapter_config.overlap = (
            0,
            Offset.fromsamples(overlap_samples, self.sample_rate),
        )
        self.adapter_config.skip_gaps = True

        super().__post_init__()

        self._window = scipy.signal.get_window(self.window_type, n_samples)
        s2 = np.sum(self._window**2)
        self._norm_factor = 2.0 / (self.sample_rate * s2)

        self._freqs = np.fft.rfftfreq(n_samples, d=1 / self.sample_rate)
        self._delta_f = self._freqs[1] - self._freqs[0]

        self._init_estimator(len(self._freqs))

    def _init_estimator(self, size: int):
        raise NotImplementedError

    def new(self, pad: SourcePad) -> EventFrame:
        in_frame = self.preparedframes[self.sink_pads[0]]

        if in_frame.is_gap or not in_frame.buffers:
            return EventFrame(is_gap=True, EOS=in_frame.EOS)

        buf = in_frame.buffers[0]
        data = buf.data

        if len(data) != len(self._window):
            return EventFrame(is_gap=True, EOS=in_frame.EOS)

        # 1. Compute FFT
        windowed = data * self._window
        fft_data = np.fft.rfft(windowed)

        # 2. Update Estimator
        self._estimator.update(fft_data)
        psd_data = self._estimator.get_psd().copy()

        # 3. Create Output Event
        # Calculate timestamps in nanoseconds for EventBuffer
        ts = Offset.tons(buf.offset)
        # Duration is derived from buffer length
        duration_samples = len(data)
        duration_offset = Offset.fromsamples(duration_samples, self.sample_rate)
        te = Offset.tons(buf.offset + duration_offset)

        # Epoch for PSD metadata (start of window)
        epoch = Offset.tosec(buf.offset)

        event = PSDEvent(
            data=psd_data, frequencies=self._freqs, epoch=epoch, delta_f=self._delta_f
        )

        # Use factory method to avoid constructor signature issues
        out_buf = EventBuffer.from_span(ts, te, [event])

        meta = in_frame.metadata.copy() if in_frame.metadata else {}

        lal_obj = event.to_lal()
        if lal_obj:
            meta["psd"] = lal_obj

        meta["psd_numpy"] = psd_data
        meta["psd_freqs"] = self._freqs

        return EventFrame(data=[out_buf], metadata=meta, EOS=in_frame.EOS)


@dataclass
class RecursivePSD(PSDEstimator):
    """Fast, Low-Latency PSD Estimator."""

    alpha: float = 0.1

    def _init_estimator(self, size: int):
        self._estimator = RecursiveEstimator(
            size=size, normalization=self._norm_factor, alpha=self.alpha
        )


@dataclass
class MGMPSD(PSDEstimator):
    """Standard Median-Geometric-Mean PSD Estimator."""

    n_median: int = 7
    n_average: int = 64

    def _init_estimator(self, size: int):
        self._estimator = MGMEstimator(
            size=size,
            normalization=self._norm_factor,
            n_median=self.n_median,
            n_average=self.n_average,
        )
