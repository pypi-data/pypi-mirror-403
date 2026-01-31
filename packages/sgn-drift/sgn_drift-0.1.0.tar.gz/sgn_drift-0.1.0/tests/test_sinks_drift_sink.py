"""
Tests for DriftCSVSink.
"""

import csv
import os
import pytest
from sgn.apps import Pipeline
from sgn.base import SourceElement
from sgnts.base import EventFrame, EventBuffer, Offset
from sgndrift.sinks.drift_sink import DriftCSVSink
from sgndrift.transforms.drift import DriftEvent


class MockDriftSource(SourceElement):
    """
    A simple source element that outputs a predefined list of DriftEvents.
    Used for testing sink integration without full physics calculation.
    """

    def __init__(self, events, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = events
        self.idx = 0

    def new(self, pad):
        # Stop after all events are consumed
        if self.idx >= len(self.events):
            # Must return an EventFrame with EOS=True
            # Important: It must be an EventFrame to match the Sink's expectation
            return EventFrame(is_gap=True, EOS=True)

        event = self.events[self.idx]
        self.idx += 1

        # Create an EventBuffer/Frame for the event
        # Assuming 1s duration for simplicity
        ts = Offset.fromsec(event.epoch)
        te = Offset.fromsec(event.epoch + 1.0)
        buf = EventBuffer.from_span(ts, te, [event])
        return EventFrame(data=[buf])


class TestDriftCSVSink:
    """Unit tests for DriftCSVSink logic (manual execution)."""

    @pytest.fixture
    def sink_element(self, tmp_path):
        """Fixture providing a DriftCSVSink writing to a temp file."""
        output_file = tmp_path / "test_drift.csv"
        return DriftCSVSink(
            name="drift_sink", sink_pad_names=("in",), filename=str(output_file)
        )

    def _make_frame(self, events):
        ts = Offset.fromsec(events[0].epoch)
        te = Offset.fromsec(events[-1].epoch + 1.0)
        buf = EventBuffer.from_span(ts, te, events)
        return EventFrame(data=[buf])

    def test_csv_creation_and_content(self, sink_element):
        """Verify file creation and correct data writing."""
        file_path = sink_element.filename

        e1 = DriftEvent(epoch=100.0, data={"total": 0.5, "low": 0.1})
        e2 = DriftEvent(epoch=101.0, data={"total": 0.6, "low": 0.2})
        frame = self._make_frame([e1, e2])

        # Manually inject data into unaligned_data to simulate TimeSeriesMixin.pull()
        sink_pad = sink_element.sink_pads[0]
        sink_element.unaligned_data[sink_pad] = frame

        # Call internal() which triggers _align() and process()
        sink_element.internal()

        assert os.path.exists(file_path)
        with open(file_path, "r") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 2
        assert float(rows[0]["time"]) == 100.0
        assert float(rows[0]["total"]) == 0.5
        assert float(rows[0]["low"]) == 0.1

    def test_append_behavior(self, sink_element):
        """Verify multiple writes append correctly."""
        file_path = sink_element.filename
        sink_pad = sink_element.sink_pads[0]

        # Write first batch
        e1 = DriftEvent(epoch=10.0, data={"v": 1.0})
        sink_element.unaligned_data[sink_pad] = self._make_frame([e1])
        sink_element.internal()

        # Write second batch
        e2 = DriftEvent(epoch=20.0, data={"v": 2.0})
        sink_element.unaligned_data[sink_pad] = self._make_frame([e2])
        sink_element.internal()

        sink_element.cleanup()

        with open(file_path, "r") as f:
            lines = f.readlines()

        # Header + 2 data lines = 3 lines
        assert len(lines) == 3
        assert "10.0" in lines[1]
        assert "20.0" in lines[2]

    def test_ignore_invalid_data(self, sink_element):
        """Verify sink ignores gaps or malformed frames."""
        file_path = sink_element.filename
        sink_pad = sink_element.sink_pads[0]

        gap = EventFrame(is_gap=True)
        sink_element.unaligned_data[sink_pad] = gap
        sink_element.internal()

        # File should not exist (or be empty) if nothing valid was written
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                assert len(f.readlines()) == 0
        else:
            assert True


class TestDriftSinkPipeline:
    """Integration tests running DriftCSVSink in a full pipeline."""

    def test_pipeline_integration(self, tmp_path):
        """
        Verify DriftCSVSink works within a Pipeline with a MockSource.
        Checks if data flows from Source -> Sink and writes to disk.
        """
        output_file = tmp_path / "pipeline_output.csv"

        # 1. Prepare Events
        events = [
            DriftEvent(epoch=1000.0, data={"total": 0.1, "bandA": 0.01}),
            DriftEvent(epoch=1001.0, data={"total": 0.2, "bandA": 0.02}),
            DriftEvent(epoch=1002.0, data={"total": 0.3, "bandA": 0.03}),
        ]

        # 2. Setup Pipeline Elements
        source = MockDriftSource(
            name="mock_source", source_pad_names=("out",), events=events
        )

        sink = DriftCSVSink(
            name="csv_sink", sink_pad_names=("in",), filename=str(output_file)
        )

        # 3. Build and Run Pipeline
        pipe = Pipeline()
        pipe.insert(source, sink)
        pipe.link({sink.snks["in"]: source.srcs["out"]})

        pipe.run()

        # 4. Verify Output File
        assert output_file.exists(), "Output CSV was not created by pipeline run"

        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Verify Headers
        assert reader.fieldnames == ["time", "bandA", "total"]

        # Verify Rows
        assert len(rows) == 3

        # Check integrity of first and last row
        assert float(rows[0]["time"]) == 1000.0
        assert float(rows[0]["total"]) == 0.1

        assert float(rows[-1]["time"]) == 1002.0
        assert float(rows[-1]["bandA"]) == 0.03

    def test_pipeline_eos_handling(self, tmp_path):
        """
        Verify that the sink handles EOS cleanly (file is readable and complete).
        This test ensures the pipeline terminates.
        """
        output_file = tmp_path / "eos_test.csv"

        source = MockDriftSource(
            name="short_source",
            source_pad_names=("out",),
            events=[DriftEvent(epoch=1.0, data={"v": 1})],
        )
        sink = DriftCSVSink(
            name="sink", sink_pad_names=("in",), filename=str(output_file)
        )

        pipe = Pipeline()
        pipe.insert(source, sink)
        pipe.link({sink.snks["in"]: source.srcs["out"]})

        pipe.run()

        # Verify content
        assert output_file.exists()
        with open(output_file, "r") as f:
            lines = f.readlines()
        assert len(lines) == 2  # Header + 1 row
