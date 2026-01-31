"""
Sinks for Drift Events.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Any, ClassVar, Optional, TextIO

from sgn.base import SinkPad
from sgnts.base import EventFrame, TSFrame, TSSink
from sgndrift.transforms.drift import DriftEvent


@dataclass
class DriftCSVSink(TSSink):
    """
    Writes DriftEvent data to a CSV file.
    Inherits from TSSink to integrate with sgn-ts pipelines.
    """

    filename: str = "drift.csv"

    # Mark 'in' as unaligned to prevent Audioadapter creation for discrete events
    static_unaligned_sink_pads: ClassVar[list[str]] = ["in"]

    # Internal state
    _file: Optional[TextIO] = field(init=False, repr=False, default=None)
    _writer: Any = field(init=False, repr=False, default=None)

    def __post_init__(self):
        # Force all input pads to be unaligned to prevent Audioadapter creation.
        # This is necessary because EventFrames are discrete and lack sample rates.
        # We set this before super().__post_init__() so TimeSeriesMixin uses it.
        self.unaligned = list(self.sink_pad_names)
        super().__post_init__()

    def configure(self) -> None:
        """Configure input frame types to expect EventFrame."""
        for name in self.sink_pad_names:
            self.input_frame_types[name] = EventFrame

    @property
    def min_latest(self) -> int:
        """
        Override min_latest to handle the case where all inputs are unaligned.
        Base implementation crashes if self.inbufs is empty.
        """
        if not self.inbufs:
            latest_offsets = []
            for pad in self.unaligned_sink_pads:
                frame = self.unaligned_data.get(pad)
                if frame and hasattr(frame, "data") and frame.data:
                    # Assuming frame.data is list of buffers
                    latest_offsets.append(frame.data[-1].noffset)
            return max(latest_offsets) if latest_offsets else 0
        return super().min_latest

    @property
    def earliest(self) -> int:
        """
        Override earliest to handle the case where all inputs are unaligned.
        """
        if not self.inbufs:
            earliest_offsets = []
            for pad in self.unaligned_sink_pads:
                frame = self.unaligned_data.get(pad)
                if frame and hasattr(frame, "data") and frame.data:
                    earliest_offsets.append(frame.data[0].offset)
            return min(earliest_offsets) if earliest_offsets else 0
        return super().earliest

    def _align(self) -> None:
        """
        Override alignment logic.
        Since input is unaligned, base class _align() would fail.
        We simply check if unaligned data is present.
        """
        # Assume alignment is satisfied if we have data on the first pad
        # For multiple pads, we might want to check all, but TSSink usually has one.
        if not self.sink_pads:
            self._is_aligned = False
            return

        sink_pad = self.sink_pads[0]
        if self.unaligned_data.get(sink_pad) is not None:
            self._is_aligned = True
        else:
            self._is_aligned = False

    def process(self, input_frames: dict[SinkPad, TSFrame]) -> None:
        """
        Process incoming frames and write to CSV.
        TSSink.internal() calls this method with frames collected from all pads.
        """
        # We assume a single sink pad named "in"
        # Since we configured the pad to expect EventFrame, input_frames contains EventFrames.
        if not self.sink_pads:
            return

        sink_pad = self.sink_pads[0]
        frame = input_frames.get(sink_pad)

        if frame is None:
            return

        if frame.EOS:
            self.mark_eos(sink_pad)

        if frame.is_gap:
            return

        # Check for data
        if not hasattr(frame, "data") or not frame.data:
            return

        for buf in frame.data:
            if not hasattr(buf, "data") or not buf.data:
                continue

            for event in buf.data:
                if not isinstance(event, DriftEvent):
                    continue

                row = {"time": event.epoch}
                row.update(event.data)

                if self._file is None:
                    self._open_file(row.keys())

                self._writer.writerow(row)

        if self._file:
            self._file.flush()

    def _open_file(self, keys):
        exists = os.path.exists(self.filename)
        self._file = open(self.filename, "a", newline="")
        # Ensure deterministic column order with 'time' first
        data_keys = sorted([k for k in keys if k != "time"])
        fieldnames = ["time"] + data_keys
        self._writer = csv.DictWriter(self._file, fieldnames=fieldnames)
        if not exists:
            self._writer.writeheader()

    def cleanup(self):
        if self._file:
            self._file.close()
            self._file = None

    def __del__(self):
        self.cleanup()
