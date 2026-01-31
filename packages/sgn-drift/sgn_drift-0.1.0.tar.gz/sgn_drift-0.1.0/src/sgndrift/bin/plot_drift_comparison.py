"""
Multi-Dataset Drift Visualization Tool.

Generates side-by-side comparison plots of Geometric Drift data from two sources.
Locks X, Y, and Color axes to shared ranges.
Uses explicit Log10 transformation for band coloring to maximize contrast.
"""

import argparse
import sys
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def load_data(filepath: str) -> pd.DataFrame:
    """Loads drift data from CSV."""
    try:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        if "time" not in df.columns:
            print(f"Error: {filepath} must contain a 'time' column.")
            sys.exit(1)
        return df
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        sys.exit(1)


def get_color_data(
    df: pd.DataFrame, color_col: Optional[str]
) -> Tuple[np.ndarray, str, str]:
    """
    Extracts color data. Applies Log10 transform if the column is a band (not time).
    Returns: (values, label, cmap_name)
    """
    if not color_col:
        return np.zeros(len(df)), "", ""

    if color_col.lower() == "time":
        # Linear: Seconds from start
        values = (df["time"] - df["time"].min()).to_numpy()
        label = "Time (s from start)"
        cmap = "turbo"
    elif color_col in df.columns:
        # Log10 Transform
        raw_values = df[color_col].to_numpy().copy()

        # Handle non-positives
        # We use NaN so matplotlib ignores them or leaves them uncolored
        raw_values[raw_values <= 0] = np.nan
        values = np.log10(raw_values)

        label = f"Log10({color_col} Magnitude)"
        cmap = "plasma"
    else:
        print(f"Warning: Color column '{color_col}' not found. Using default.")
        return np.zeros(len(df)), "", ""

    return values, label, cmap


def make_comparison_plot(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    label_a: str,
    label_b: str,
    x_col: str,
    y_col: str,
    output_path: str,
    color_col: Optional[str] = None,
    log_scale: bool = True,
    title: Optional[str] = None,
):
    """Generates the side-by-side plot with shared scales."""

    # 1. Validation
    for df, lbl in [(df_a, label_a), (df_b, label_b)]:
        if x_col not in df.columns or y_col not in df.columns:
            print(f"Error: Columns '{x_col}' or '{y_col}' not found in {lbl}.")
            sys.exit(1)

    # 2. Determine Global Axis Limits
    all_x = pd.concat([df_a[x_col], df_b[x_col]])
    all_y = pd.concat([df_a[y_col], df_b[y_col]])

    x_min, x_max = all_x.min(), all_x.max()
    y_min, y_max = all_y.min(), all_y.max()

    if log_scale:
         # Filter strictly positive for log axes
         valid_x = all_x[all_x > 0]
         valid_y = all_y[all_y > 0]
         x_min = valid_x.min() if not valid_x.empty else 1e-5
         y_min = valid_y.min() if not valid_y.empty else 1e-5

    # 3. Determine Global Color Limits (Linear range of the Log values)
    c_a, c_label, cmap_name = get_color_data(df_a, color_col)
    c_b, _, _ = get_color_data(df_b, color_col)

    vmin, vmax = None, None
    if color_col:
        # Concatenate and ignore NaNs (from <=0 values)
        c_all = np.concatenate([c_a, c_b])
        vmin = np.nanmin(c_all)
        vmax = np.nanmax(c_all)

    # 4. Plotting
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True, sharex=True)

    datasets = [(df_a, label_a, c_a), (df_b, label_b, c_b)]

    for ax, (df, label, c_vals) in zip(axes, datasets):

        c_arg = c_vals if color_col else "tab:blue"

        sc = ax.scatter(
            df[x_col],
            df[y_col],
            c=c_arg,
            cmap=cmap_name if color_col else None,
            vmin=vmin,
            vmax=vmax,
            s=15,
            alpha=0.6,
            edgecolors="none",
        )

        ax.set_title(label, fontsize=14, fontweight='bold')
        ax.set_xlabel(f"{x_col} Drift Velocity")
        if ax == axes[0]:
            ax.set_ylabel(f"{y_col} Drift Velocity")

        ax.grid(True, which="both", alpha=0.3)

        if log_scale:
            ax.set_xscale("log")
            ax.set_yscale("log")

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

    # 5. Shared Colorbar
    if color_col:
        fig.subplots_adjust(right=0.85)
        cbar_ax = fig.add_axes([0.88, 0.15, 0.02, 0.7])
        fig.colorbar(sc, cax=cbar_ax, label=c_label)
    else:
        fig.subplots_adjust(right=0.95)

    if title:
        fig.suptitle(title, fontsize=16)
    else:
        fig.suptitle(f"Drift Comparison: {x_col} vs {y_col}", fontsize=16)

    try:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Comparison plot saved to: {output_path}")
    except Exception as e:
        print(f"Error saving plot: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Multi-Dataset Drift Comparison.")

    parser.add_argument("file_a", type=str, help="First CSV file")
    parser.add_argument("file_b", type=str, help="Second CSV file")

    parser.add_argument("--label-a", type=str, default="Dataset A", help="Label for first plot")
    parser.add_argument("--label-b", type=str, default="Dataset B", help="Label for second plot")

    parser.add_argument("--x-band", type=str, default="v_low", help="X-axis column")
    parser.add_argument("--y-band", type=str, default="v_mid", help="Y-axis column")

    parser.add_argument(
        "--color-by",
        type=str,
        default=None,
        help="Column to color by (e.g. 'time', 'v_high'). Default: None."
    )

    parser.add_argument("-o", "--output", type=str, default="drift_comparison.png", help="Output filename")
    parser.add_argument("--linear", action="store_true", help="Use linear scale (Default: Log)")
    parser.add_argument("--title", type=str, default=None, help="Global plot title")

    return parser.parse_args()


def main():
    args = parse_args()

    df_a = load_data(args.file_a)
    df_b = load_data(args.file_b)

    make_comparison_plot(
        df_a, df_b,
        label_a=args.label_a,
        label_b=args.label_b,
        x_col=args.x_band,
        y_col=args.y_band,
        output_path=args.output,
        color_col=args.color_by,
        log_scale=not args.linear,
        title=args.title
    )


if __name__ == "__main__":
    main()
