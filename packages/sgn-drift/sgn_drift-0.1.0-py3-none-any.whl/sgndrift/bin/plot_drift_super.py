"""
Super Drift Visualization Tool.

Generates a combined dashboard image for a single dataset:
1. Top: Phase Space Scatter Plot (e.g., Low vs Mid).
2. Bottom: Stacked Time-Series Strip Chart (evolution of all bands).

This allows simultaneous analysis of geometric correlation and temporal evolution.
"""

import argparse
import sys
from typing import Optional, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
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

    # Apply Time Filtering
    if start is not None:
        df = df[df["time"] >= start]
    if end is not None:
        df = df[df["time"] <= end]

    if df.empty:
        print(f"Warning: No data found in {filepath} for the specified time range.")
        sys.exit(1)

    return df


def get_color_data(
    df: pd.DataFrame, color_col: Optional[str]
) -> Tuple[np.ndarray, str, str, Optional[Normalize]]:
    """
    Extracts color data and determines the appropriate normalization.
    Returns: (values, label, cmap_name, norm)
    """
    if not color_col:
        return np.zeros(len(df)), "", "", None

    if color_col.lower() == "time":
        # Linear: Seconds from start
        t_min = df["time"].min()
        values = (df["time"] - t_min).to_numpy()
        label = "Time (s from start)"
        cmap = "turbo"
        norm = Normalize(vmin=values.min(), vmax=values.max())
    elif color_col in df.columns:
        # Log10 Transform for Bands
        raw_values = df[color_col].to_numpy().copy()

        # Filter strictly positive for LogNorm
        valid_mask = raw_values > 0
        if not np.any(valid_mask):
            return np.zeros(len(df)), "Invalid Data", "gray", None

        # We pass raw values to LogNorm, it handles the log math
        values = raw_values
        label = f"{color_col} Magnitude (Log)"
        cmap = "plasma"
        norm = LogNorm(vmin=values[valid_mask].min(), vmax=values[valid_mask].max())
    else:
        print(f"Warning: Color column '{color_col}' not found. Using default.")
        return np.zeros(len(df)), "", "", None

    return values, label, cmap, norm


def make_super_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    ts_bands: List[str],
    output_path: str,
    color_col: Optional[str] = None,
    log_scale: bool = True,
    title: Optional[str] = None,
):
    """Generates the combined dashboard plot."""

    # --- 1. Validation ---
    req_cols = [x_col, y_col] + [b for b in ts_bands]
    for c in req_cols:
        if c not in df.columns:
            print(f"Error: Column '{c}' not found in CSV.")
            sys.exit(1)

    # --- 2. Setup Figure Grid ---
    # Height ratios: 1.3 for Scatter, 1.0 for Time Series area
    fig = plt.figure(figsize=(12, 14))
    gs_main = fig.add_gridspec(2, 1, height_ratios=[1.3, 1.0], hspace=0.15)

    # --- 3. Top Plot: Phase Space Scatter ---
    ax_scatter = fig.add_subplot(gs_main[0])

    # Get Color Info
    c_vals, c_label, cmap, norm = get_color_data(df, color_col)
    c_arg = c_vals if color_col else "tab:blue"

    sc = ax_scatter.scatter(
        df[x_col],
        df[y_col],
        c=c_arg,
        cmap=cmap,
        norm=norm,
        s=15,
        alpha=0.6,
        edgecolors="none",
    )

    ax_scatter.set_xlabel(f"{x_col} Drift Velocity", fontsize=11)
    ax_scatter.set_ylabel(f"{y_col} Drift Velocity", fontsize=11)
    ax_scatter.set_title(
        f"Phase Space Correlation: {x_col} vs {y_col}", fontweight="bold"
    )

    if log_scale:
        ax_scatter.set_xscale("log")
        ax_scatter.set_yscale("log")

    ax_scatter.grid(True, which="both", alpha=0.3)

    # Colorbar for Scatter (attached to scatter axis)
    if color_col:
        fig.colorbar(sc, ax=ax_scatter, label=c_label)

    # --- 4. Bottom Plot: Stacked Time Series ---
    # Create sub-grid for bands
    gs_ts = gs_main[1].subgridspec(len(ts_bands), 1, hspace=0.0)
    axes_ts = [fig.add_subplot(gs_ts[i]) for i in range(len(ts_bands))]

    # Prepare Time Axis
    t0 = df["time"].min()
    t_data = df["time"] - t0
    t_unit = "Seconds from Start"

    # Heuristic for time units
    duration = t_data.max()
    if duration > 3600:
        t_data /= 3600.0
        t_unit = f"Hours from GPS {t0:.0f}"
    elif duration > 60:
        t_data /= 60.0
        t_unit = f"Minutes from GPS {t0:.0f}"
    else:
        t_unit = f"Seconds from GPS {t0:.0f}"

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    for i, (ax, band) in enumerate(zip(axes_ts, ts_bands)):
        col = colors[i % len(colors)]

        ax.plot(t_data, df[band], color=col, linewidth=1.2)

        if log_scale:
            ax.set_yscale("log")

        ax.grid(True, which="both", alpha=0.3)

        # Labeling (Inside the plot to save space)
        ax.text(
            0.01,
            0.85,
            f"Band: {band}",
            transform=ax.transAxes,
            fontweight="bold",
            fontsize=9,
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
        )

        # Y-Label on the right or simplified
        ax.set_ylabel(r"$\|\Omega\|$", fontsize=9)

        # Remove x-ticks for all but bottom
        if i < len(ts_bands) - 1:
            ax.set_xticklabels([])
        else:
            ax.set_xlabel(t_unit, fontsize=11)

    # --- 5. Finalizing ---
    if title:
        fig.suptitle(title, fontsize=16, y=0.92)

    try:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Super plot saved to: {output_path}")
    except Exception as e:
        print(f"Error saving plot: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Super Drift Visualization (Scatter + TimeSeries)."
    )

    parser.add_argument("input_file", type=str, help="Path to input CSV file")

    # Scatter Options
    parser.add_argument("--x-band", type=str, default="v_low", help="Scatter X-axis")
    parser.add_argument("--y-band", type=str, default="v_mid", help="Scatter Y-axis")
    parser.add_argument(
        "--color-by",
        type=str,
        default="time",
        help="Column to color Scatter by (default: time)",
    )

    # Time Series Options
    parser.add_argument(
        "--ts-bands",
        type=str,
        default="v_low,v_mid,v_high,total",
        help="Comma-separated bands for strip chart",
    )

    # General Options
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="drift_super_dashboard.png",
        help="Output filename",
    )
    parser.add_argument("--start", type=float, default=None, help="Start GPS (Zoom)")
    parser.add_argument("--end", type=float, default=None, help="End GPS (Zoom)")
    parser.add_argument("--linear", action="store_true", help="Use linear scales")
    parser.add_argument("--title", type=str, default=None, help="Global Title")

    return parser.parse_args()


def main():
    args = parse_args()

    df = load_data(args.input_file, start=args.start, end=args.end)
    ts_bands_list = [b.strip() for b in args.ts_bands.split(",")]

    make_super_plot(
        df,
        x_col=args.x_band,
        y_col=args.y_band,
        ts_bands=ts_bands_list,
        output_path=args.output,
        color_col=args.color_by,
        log_scale=not args.linear,
        title=args.title,
    )


if __name__ == "__main__":
    main()
