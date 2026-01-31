"""
Drift Visualization Tool.

Generates 2D scatter plots (Phase Space projections) of Geometric Drift data.

Features:
- Scatter plot of Band X vs Band Y.
- Coloring:
    - Time: Linear scale (Seconds from start).
    - Bands: Explicit Log10 scale (Log10 of magnitude) for better contrast.
"""

import argparse
import sys
from typing import Optional

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

    if start is not None:
        df = df[df["time"] >= start]
    if end is not None:
        df = df[df["time"] <= end]

    if df.empty:
        print("Error: No data found in the specified time range.")
        sys.exit(1)

    return df


def make_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    color_col: Optional[str] = None,
    log_scale: bool = True,
    title: Optional[str] = None,
):
    """Generates and saves the scatter plot."""
    if x_col not in df.columns or y_col not in df.columns:
        print(f"Error: Columns '{x_col}' or '{y_col}' not found.")
        print(f"Available: {list(df.columns)}")
        sys.exit(1)

    x_data = df[x_col]
    y_data = df[y_col]

    # --- Coloring Logic ---
    c_data = None
    c_label = None
    cmap = None

    if color_col:
        if color_col.lower() == "time":
            # Linear Scale for Time
            c_data = df["time"] - df["time"].min()
            c_label = "Time (seconds from start)"
            cmap = "turbo"
        elif color_col in df.columns:
            # Explicit Log10 Transform for Bands
            raw_data = df[color_col].copy()

            # Mask zeros/negative values to avoid -inf
            raw_data[raw_data <= 0] = np.nan
            c_data = np.log10(raw_data)

            c_label = f"Log10({color_col} Magnitude)"
            cmap = "plasma"  # High contrast
        else:
            print(f"Warning: Color column '{color_col}' not found. Using solid color.")

    # --- Plotting ---
    plt.figure(figsize=(10, 8))

    sc = plt.scatter(
        x_data,
        y_data,
        c=c_data if c_data is not None else "tab:blue",
        cmap=cmap,
        s=15,
        alpha=0.6,
        edgecolors="none",
    )

    if c_data is not None:
        plt.colorbar(sc, label=c_label)

    plt.xlabel(f"{x_col} Drift Velocity")
    plt.ylabel(f"{y_col} Drift Velocity")

    if log_scale:
        plt.xscale("log")
        plt.yscale("log")
        plt.grid(True, which="both", alpha=0.2)
    else:
        plt.grid(True, alpha=0.3)

    if title:
        plt.title(title)
    else:
        plt.title(f"Geometric Drift: {x_col} vs {y_col}")

    try:
        plt.savefig(output_path, dpi=150)
        print(f"Plot saved to: {output_path}")
    except Exception as e:
        print(f"Error saving plot: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize Geometric Drift Phase Space."
    )
    parser.add_argument("input_file", type=str, help="Path to input CSV file")
    parser.add_argument("--x-band", type=str, default="v_low", help="X-axis column")
    parser.add_argument("--y-band", type=str, default="v_mid", help="Y-axis column")
    parser.add_argument(
        "-o", "--output", type=str, default="drift_plot.png", help="Output filename"
    )

    parser.add_argument("--start", type=float, default=None, help="Start GPS")
    parser.add_argument("--end", type=float, default=None, help="End GPS")

    parser.add_argument(
        "--color-by",
        type=str,
        default=None,
        help="Column to color by (e.g. 'time', 'v_high'). Default: No color.",
    )

    parser.add_argument(
        "--linear", action="store_true", help="Use linear scale (Default: Log)"
    )
    parser.add_argument("--title", type=str, default=None, help="Custom plot title")

    return parser.parse_args()


def main():
    args = parse_args()
    df = load_data(args.input_file, start=args.start, end=args.end)
    make_plot(
        df,
        x_col=args.x_band,
        y_col=args.y_band,
        output_path=args.output,
        color_col=args.color_by,
        log_scale=not args.linear,
        title=args.title,
    )


if __name__ == "__main__":
    main()
