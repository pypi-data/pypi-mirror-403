"""
Drift Estimation Application Logic (Robust & Modular).

This script orchestrates the SGN pipeline to estimate Geometric Spectral Drift.
It includes logic to:
1. Identify valid science segments (handling both Internal and Public data).
2. Construct the pipeline dynamically for each segment.
3. Handle data gaps gracefully without crashing the entire job.
"""

import os
import argparse
from typing import Optional, Dict, Tuple, List

# GW Imports
from gwpy.segments import DataQualityFlag

try:
    from gwosc.timeline import get_segments as get_gwosc_segments
except ImportError:
    get_gwosc_segments = None

# SGN Imports
from sgn.apps import Pipeline
from sgn.base import SourceElement
from sgnligo.sources.gwosc import GWOSCSource

from sgndrift.transforms.psd import RecursivePSD
from sgndrift.transforms.drift import FisherVelocity
from sgndrift.sinks.drift_sink import DriftCSVSink


def get_science_segments(
    detector: str, start: float, end: float, verbose: bool = False
) -> List[Tuple[float, float]]:
    """
    Queries valid science segments.
    1. Tries internal LIGO DQSegDB (requires grid cert).
    2. Falls back to Public GWOSC Timeline (open data).
    3. If both fail/empty, returns full window (Force Mode).
    """
    # Method A: Internal LIGO Database
    flag_name = f"{detector}:DMT-ANALYSIS_READY:1"
    if verbose:
        print(f"Querying segments for {flag_name} [{start} ... {end}]")

    try:
        flags = DataQualityFlag.query(flag_name, start, end)
        if not flags.active:
            raise ValueError("No segments found in internal DB.")
        return [(float(seg.start), float(seg.end)) for seg in flags.active]

    except Exception as e:
        if verbose:
            print(f"Internal segment query failed/empty ({e}). Checking GWOSC...")

        segments = []
        if get_gwosc_segments:
            try:
                # Method B: Public GWOSC
                segments = get_gwosc_segments(detector, int(start), int(end))
            except Exception as e2:
                print(f"Warning: GWOSC segment query error: {e2}")
        else:
            print("Warning: 'gwosc' library not installed.")

        if segments:
            if verbose:
                print(f"Found {len(segments)} valid segments in GWOSC.")
            return segments
        else:
            print(f"Warning: No known science segments found for {detector}.")
            print("Defaulting to full window (Pipeline will skip if data is missing).")
            return [(start, end)]


def build_pipeline(
    start: float,
    end: float,
    detector: str,
    output_drift: str,
    alpha: float = 0.1,
    fft_length: float = 1.0,
    overlap: float = 0.5,
    sample_rate: int = 4096,
    bands: Optional[Dict[str, Tuple[float, float]]] = None,
    source_element: Optional[SourceElement] = None,
    verbose: bool = False,
) -> Pipeline:
    """
    Constructs the SGN pipeline for Drift Estimation.
    """
    # 1. Setup Source (if not provided)
    if source_element is None:
        source_name = f"gwosc_{detector}_{int(start)}"
        source_element = GWOSCSource(
            name=source_name,
            start=start,
            end=end,
            detectors=[detector],
            sample_rate=sample_rate,
            cache_data=True,
            verbose=verbose,
        )
        source_pad_name = detector
    else:
        source_pad_name = detector

    # 2. Pipeline Container
    pipe = Pipeline()

    # 3. PSD Estimator
    psd_est = RecursivePSD(
        name=f"psd_{detector}_{int(start)}",
        sink_pad_names=("in",),
        source_pad_names=("out",),
        fft_length=fft_length,
        overlap=overlap,
        sample_rate=sample_rate,
        alpha=alpha,
    )

    # 4. Fisher Velocity
    fisher = FisherVelocity(
        name=f"fisher_{detector}_{int(start)}",
        sink_pad_names=("in",),
        source_pad_names=("out",),
        bands=bands or {},
    )
    fisher.configure()

    # 5. Sink (Appends to CSV)
    sink = DriftCSVSink(
        name=f"sink_{detector}_{int(start)}",
        sink_pad_names=("in",),
        filename=output_drift,
    )
    sink.configure()

    # 6. Build & Link
    pipe.insert(source_element, psd_est, fisher, sink)

    pipe.link({psd_est.snks["in"]: source_element.srcs[source_pad_name]})
    pipe.link({fisher.snks["in"]: psd_est.srcs["out"]})
    pipe.link({sink.snks["in"]: fisher.srcs["out"]})

    return pipe


def estimate_drift(
    start: float,
    end: float,
    detector: str = "H1",
    output_drift: str = "drift.csv",
    source_element: Optional[SourceElement] = None,
    method: str = "recursive",
    alpha: float = 0.1,
    fft_length: float = 1.0,
    overlap: float = 0.5,
    sample_rate: float = 16384.0,
    bands: Optional[Dict[str, Tuple[float, float]]] = None,
    force: bool = False,
    verbose: bool = False,
):
    """
    High-level Orchestrator.
    Handles Gap Checks -> Segment Loops -> Pipeline Build -> Pipeline Run.
    """
    # 1. Clear output file (if starting fresh CLI run)
    if source_element is None and os.path.exists(output_drift):
        if verbose:
            print(f"Clearing previous output: {output_drift}")
        os.remove(output_drift)

    # 2. Determine Segments
    segments = []
    if force:
        if verbose:
            print("Force Mode: Skipping segment check. Using full window.")
        segments = [(start, end)]
    elif source_element is None:
        segments = get_science_segments(detector, start, end, verbose)
    else:
        # If custom source provided, trust the user
        segments = [(start, end)]

    if not segments:
        print("No valid segments found. Use --force to attempt anyway.")
        return

    # 3. Process Each Segment
    for seg_start, seg_end in segments:
        duration = seg_end - seg_start
        # Skip tiny segments
        if duration < (fft_length * 8):
            continue

        if verbose:
            print(f"Processing segment: {seg_start:.1f} - {seg_end:.1f}")

        try:
            # A. BUILD
            pipe = build_pipeline(
                start=seg_start,
                end=seg_end,
                detector=detector,
                output_drift=output_drift,
                alpha=alpha,
                fft_length=fft_length,
                overlap=overlap,
                sample_rate=int(sample_rate),
                bands=bands,
                source_element=source_element if source_element else None,
                verbose=verbose,
            )

            # B. RUN
            pipe.run()

        except RuntimeError as e:
            # Handle GWOSC "No Data" errors gracefully
            err_str = str(e)
            if "Cannot find a GWOSC dataset" in err_str or "No data found" in err_str:
                print(f"[Gap] No data available for {seg_start}-{seg_end}. Skipping.")
            else:
                print(f"[Error] Pipeline Runtime Error: {e}")
            continue

        except Exception as e:
            print(f"[Error] Critical failure in segment {seg_start}-{seg_end}: {e}")
            continue

    if verbose:
        print(f"Analysis complete. Results in {output_drift}")


def parse_args():
    parser = argparse.ArgumentParser(description="Estimate Geometric Spectral Drift.")
    parser.add_argument("--detector", type=str, default="H1", help="Detector ID")
    parser.add_argument("--start", type=float, required=True, help="GPS Start")
    parser.add_argument("--end", type=float, required=True, help="GPS End")
    parser.add_argument("--output", type=str, default="drift.csv", help="Output CSV")
    parser.add_argument("--alpha", type=float, default=0.1, help="Filter decay")
    parser.add_argument("--fft-length", type=float, default=1.0, help="FFT sec")
    parser.add_argument("--sample-rate", type=float, default=4096.0, help="Hz")
    parser.add_argument("--bands", type=str, default=None, help="name:min:max,...")
    parser.add_argument("--force", action="store_true", help="Ignore segment checks")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    return parser.parse_args()


def main():
    args = parse_args()

    # Parse band string
    bands_dict = {}
    if args.bands:
        for item in args.bands.split(","):
            parts = item.split(":")
            if len(parts) == 3:
                bands_dict[parts[0]] = (float(parts[1]), float(parts[2]))

    estimate_drift(
        start=args.start,
        end=args.end,
        detector=args.detector,
        output_drift=args.output,
        alpha=args.alpha,
        fft_length=args.fft_length,
        sample_rate=args.sample_rate,
        bands=bands_dict if bands_dict else None,
        force=args.force,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
