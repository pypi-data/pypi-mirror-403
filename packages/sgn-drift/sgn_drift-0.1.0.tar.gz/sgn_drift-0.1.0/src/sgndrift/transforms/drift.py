"""
Geometric Diagnostics: Elements for tracking the manifold velocity of detector noise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, Tuple

import numpy as np

from sgn.base import SourcePad
from sgndrift.transforms.psd import PSDEvent
from sgndrift.psd.drift import calculate_fisher_velocity
from sgnts.base import EventBuffer, EventFrame, TSTransform


@dataclass
class DriftEvent:
    """
    Container for Fisher Information Velocity (Drift) data.
    """

    epoch: float
    data: Dict[str, float]


@dataclass
class FisherVelocity(TSTransform):
    """
    Computes Fisher Information Velocity (Geometric Drift) between consecutive PSDs.

    Wraps sgndrift.psd.drift.calculate_fisher_velocity.

    Inputs:
        EventFrame containing PSDEvent objects.

    Outputs:
        EventFrame containing DriftEvent objects.
    """

    # Mark 'in' as unaligned to prevent TimeSeriesMixin from creating an Audioadapter.
    static_unaligned_sink_pads: ClassVar[list[str]] = ["in"]

    bands: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    _prev_data: np.ndarray = field(init=False, repr=False, default=None)
    _prev_epoch: float = field(init=False, repr=False, default=None)

    def configure(self) -> None:
        """Configure element-specific attributes."""
        # Inform the element that it handles EventFrames
        for name in self.sink_pad_names:
            self.input_frame_types[name] = EventFrame
        for name in self.source_pad_names:
            self.output_frame_types[name] = EventFrame

    @property
    def min_latest(self) -> int:
        if not self.inbufs:
            latest_offsets = []
            for pad in self.unaligned_sink_pads:
                frame = self.unaligned_data.get(pad)
                if frame and frame.data:
                    latest_offsets.append(frame.data[-1].noffset)
            return max(latest_offsets) if latest_offsets else 0
        return super().min_latest

    @property
    def earliest(self) -> int:
        if not self.inbufs:
            earliest_offsets = []
            for pad in self.unaligned_sink_pads:
                frame = self.unaligned_data.get(pad)
                if frame and frame.data:
                    earliest_offsets.append(frame.data[0].offset)
            return min(earliest_offsets) if earliest_offsets else 0
        return super().earliest

    def _align(self) -> None:
        sink_pad = self.sink_pads[0]
        if self.unaligned_data.get(sink_pad) is not None:
            self._is_aligned = True
        else:
            self._is_aligned = False

    def new(self, pad: SourcePad) -> EventFrame:
        sink_pad = self.sink_pads[0]
        in_frame = self.unaligned_data.get(sink_pad)
        self.unaligned_data[sink_pad] = None

        if in_frame is None or in_frame.is_gap:
            return EventFrame(is_gap=True, EOS=in_frame.EOS if in_frame else False)

        if not hasattr(in_frame, "data") or not in_frame.data:
            return EventFrame(is_gap=True, EOS=in_frame.EOS)
        if not in_frame.data[0].data:
            return EventFrame(is_gap=True, EOS=in_frame.EOS)

        psd_event = in_frame.data[0].data[0]

        if not isinstance(psd_event, PSDEvent):
            return EventFrame(is_gap=True, EOS=in_frame.EOS)

        current_data = psd_event.data
        current_epoch = psd_event.epoch
        freqs = psd_event.frequencies
        df = psd_event.delta_f

        drift_results = {}

        # Only calculate if we have history
        if self._prev_data is not None:
            dt = current_epoch - self._prev_epoch
            if dt > 0:
                drift_results = calculate_fisher_velocity(
                    current_psd=current_data,
                    previous_psd=self._prev_data,
                    dt=dt,
                    frequencies=freqs,
                    delta_f=df,
                    bands=self.bands,
                )

        # Update History
        self._prev_data = current_data.copy()
        self._prev_epoch = current_epoch

        # Handle startup transient (return zeros instead of empty)
        if not drift_results:
            bands_keys = self.bands.keys() if self.bands else ["total"]
            drift_results = {k: 0.0 for k in bands_keys}

        out_event = DriftEvent(epoch=current_epoch, data=drift_results)

        buf = in_frame.data[0]
        ts = buf.offset
        dur = (
            buf.duration if hasattr(buf, "duration") and buf.duration else 1_000_000_000
        )
        te = ts + dur

        out_buf = EventBuffer.from_span(ts, te, [out_event])

        return EventFrame(data=[out_buf], EOS=in_frame.EOS)
