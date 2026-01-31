"""
Drift Time-Series Visualization Tool.

Generates a multi-panel "Strip Chart" of drift velocities over time.
Useful for correlating glitches across different frequency bands.

Features:
- Default: Stacked subplots (one per band) with shared X-axis.
- Optional: Overlay mode (all bands on one plot) via --overlay.
- Zoom: --start and --end filters.
"""

import argparse
import sys
from typing import Optional, List

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def load_data(
    filepath: str, start: Optional[float] = None, end: Optional[float] = None
) -> pd.DataFrame:
    """Loads drift data from CSV and applies time filtering."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    df.columns = df.columns.str.strip()

    if "time" not in df.columns:
        print("Error: CSV must contain a 'time' column.")
        sys.exit(1)

    # --- Apply Time Filtering (Zoom) ---
    if start is not None:
        df = df[df["time"] >= start]
    if end is not None:
        df = df[df["time"] <= end]

    if df.empty:
        print(f"Warning: No data found in {filepath} for the specified time range.")
        sys.exit(1)

    return df


def make_timeseries_plot(
    df: pd.DataFrame,
    bands: List[str],
    output_path: str,
    overlay: bool = False,
    log_scale: bool = True,
    title: Optional[str] = None,
):
    """
    Generates the time-series plot.

    Args:
        overlay (bool): If False (Default), creates stacked subplots (separate axes).
                        If True, plots all bands on a single axis.
    """
    # Validate bands
    valid_bands = [b for b in bands if b in df.columns]
    if not valid_bands:
        print(f"Error: None of the requested bands {bands} found in CSV.")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    # Prepare Time Axis relative to the zoomed window
    t0 = df["time"].min()
    duration = df["time"].max() - t0

    # Smart Time Units
    if duration > 172800:  # > 2 days
        t_data = (df["time"] - t0) / 86400.0
        t_unit = "Days"
    elif duration > 3600:  # > 1 hour
        t_data = (df["time"] - t0) / 3600.0
        t_unit = "Hours"
    elif duration > 60:
        t_data = (df["time"] - t0) / 60.0
        t_unit = "Minutes"
    else:
        t_data = df["time"] - t0
        t_unit = "Seconds"

    # --- Plot Setup ---
    if overlay:
        # Single Axis Mode
        fig, ax = plt.subplots(figsize=(12, 6))
        axes = [ax] * len(valid_bands)
    else:
        # Stacked Subplots Mode (Default)
        # sharex=True locks the time axis zoom for all plots
        fig, axes = plt.subplots(
            nrows=len(valid_bands),
            ncols=1,
            figsize=(12, 3 * len(valid_bands)),
            sharex=True,
            constrained_layout=True,
        )
        # Handle single band case where subplots returns an Ax object, not list
        if len(valid_bands) == 1:
            axes = [axes]

    # Standard colors cycle
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    for i, (ax, band) in enumerate(zip(axes, valid_bands)):
        color = colors[i % len(colors)]

        ax.plot(t_data, df[band], label=band, color=color, linewidth=1.5, alpha=0.9)

        if log_scale:
            ax.set_yscale("log")

        ax.grid(True, which="both", alpha=0.3)

        # In stacked mode, give each plot its own legend and label
        if not overlay:
            ax.set_ylabel(r"$\|\Omega\|$")
            ax.legend(loc="upper right", frameon=True)
            ax.set_title(f"Band: {band}", fontsize=10, loc="left", pad=2)

    # --- Final Formatting ---
    if overlay:
        axes[0].set_ylabel(r"Drift Velocity $\|\Omega\|$")
        axes[0].set_xlabel(f"Time ({t_unit} from GPS {t0:.1f})")
        axes[0].legend(loc="upper right")
    else:
        # Only label the bottom X-axis in stacked mode
        axes[-1].set_xlabel(f"Time ({t_unit} from GPS {t0:.1f})")

    if title:
        fig.suptitle(title, fontsize=16)

    try:
        plt.savefig(output_path, dpi=150)
        print(f"Time-series plot saved to: {output_path}")
    except Exception as e:
        print(f"Error saving plot: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize Geometric Drift Time-Series."
    )

    parser.add_argument("input_file", type=str, help="Path to input CSV file")

    parser.add_argument(
        "--bands",
        type=str,
        default="v_low,v_mid,v_high",
        help="Comma-separated list of bands to plot (default: v_low,v_mid,v_high)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="drift_timeseries.png",
        help="Output filename",
    )

    # Zoom Options
    parser.add_argument(
        "--start", type=float, default=None, help="Start GPS Time (Zoom)"
    )
    parser.add_argument("--end", type=float, default=None, help="End GPS Time (Zoom)")

    parser.add_argument(
        "--overlay",
        action="store_true",
        help="Plot all bands on one axis (Default is Stacked)",
    )
    parser.add_argument(
        "--linear", action="store_true", help="Use linear Y-scale (Default is Log)"
    )
    parser.add_argument("--title", type=str, default=None, help="Custom plot title")

    return parser.parse_args()


def main():
    args = parse_args()

    bands_list = [b.strip() for b in args.bands.split(",")]

    df = load_data(args.input_file, start=args.start, end=args.end)

    make_timeseries_plot(
        df,
        bands=bands_list,
        output_path=args.output,
        overlay=args.overlay,
        log_scale=not args.linear,
        title=args.title,
    )


if __name__ == "__main__":
    main()
