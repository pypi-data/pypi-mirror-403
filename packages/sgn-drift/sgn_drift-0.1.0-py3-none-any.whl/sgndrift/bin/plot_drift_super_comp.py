"""
Double Super Drift Visualization Tool.

Generates a side-by-side comparison dashboard for TWO datasets.
Each side features:
1. Top: Phase Space Scatter Plot.
2. Bottom: Stacked Time-Series Strip Chart.

Crucially, this script locks the scales (X, Y, Color, and TS-Amplitude)
across both datasets to allow rigorous visual comparison of Laminar vs Turbulent regimes.

Usage:
    sgn-drift-plot-super-multi fileA.csv fileB.csv --label-a "Safe" --label-b "Scattering"
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
        print(f"Error: {filepath} must contain a 'time' column.")
        sys.exit(1)

    # Apply Time Filtering
    if start is not None:
        df = df[df["time"] >= start]
    if end is not None:
        df = df[df["time"] <= end]

    if df.empty:
        # Warn but return empty so we can plot "No Data" placeholder
        print(f"Warning: No data found in {filepath} for the specified time range.")

    return df


def get_color_values_and_meta(
        df: pd.DataFrame, color_col: Optional[str]
) -> Tuple[np.ndarray, str, str]:
    """
    Extracts raw values for coloring.
    Does NOT normalize (normalization happens globally later).
    """
    if df.empty or not color_col:
        return np.array([]), "", ""

    if color_col.lower() == "time":
        # Time is relative to the start of THIS dataset
        t_min = df["time"].min()
        values = (df["time"] - t_min).to_numpy()
        label = "Time (s from start)"
        cmap = "turbo"
    elif color_col in df.columns:
        # Bands: Log10 Transform
        raw = df[color_col].to_numpy().copy()
        # Mask <= 0
        raw[raw <= 0] = np.nan
        values = np.log10(raw)
        label = f"{color_col} Magnitude (Log10)"
        cmap = "plasma"
    else:
        print(f"Warning: Color column '{color_col}' not found.")
        return np.array([]), "", ""

    return values, label, cmap


def make_super_multi_plot(
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        label_a: str,
        label_b: str,
        x_col: str,
        y_col: str,
        ts_bands: List[str],
        output_path: str,
        color_col: Optional[str] = None,
        log_scale: bool = True,
        title: Optional[str] = None,
):
    """Generates the side-by-side dashboard."""

    # --- 1. Global Scale Calculations ---

    # A. Scatter Axis Limits (X/Y)
    concat_x = []
    concat_y = []
    if not df_a.empty:
        concat_x.append(df_a[x_col])
        concat_y.append(df_a[y_col])
    if not df_b.empty:
        concat_x.append(df_b[x_col])
        concat_y.append(df_b[y_col])

    all_x = pd.concat(concat_x) if concat_x else pd.Series(dtype=float)
    all_y = pd.concat(concat_y) if concat_y else pd.Series(dtype=float)

    if not all_x.empty:
        if log_scale:
            valid_x = all_x[all_x > 0]
            valid_y = all_y[all_y > 0]
            x_min = valid_x.min() if not valid_x.empty else 0.1
            x_max = valid_x.max() if not valid_x.empty else 10.0
            y_min = valid_y.min() if not valid_y.empty else 0.1
            y_max = valid_y.max() if not valid_y.empty else 10.0
        else:
            x_min, x_max = all_x.min(), all_x.max()
            y_min, y_max = all_y.min(), all_y.max()
    else:
        x_min, x_max, y_min, y_max = 0.1, 10, 0.1, 10

    # B. Color Normalization
    c_a, c_lbl, cmap = get_color_values_and_meta(df_a, color_col)
    c_b, _, _ = get_color_values_and_meta(df_b, color_col)

    norm = None
    if color_col:
        c_all = np.concatenate([c_a, c_b])
        # Filter NaNs (from Log10 <= 0)
        c_valid = c_all[~np.isnan(c_all)]
        if len(c_valid) > 0:
            if color_col.lower() == "time":
                # For time, we actually want independent scaling usually?
                # No, typically 0-3600s vs 0-3600s. Global norm works.
                norm = Normalize(vmin=c_valid.min(), vmax=c_valid.max())
            else:
                # Bands
                norm = Normalize(vmin=c_valid.min(), vmax=c_valid.max())
        else:
            norm = Normalize(vmin=0, vmax=1)

    # --- 2. Figure Layout ---
    fig = plt.figure(figsize=(20, 14))

    # Outer Grid: 1 Row, 2 Cols (Left Dataset, Right Dataset)
    gs_outer = fig.add_gridspec(1, 2, wspace=0.15)

    datasets = [(df_a, label_a, c_a), (df_b, label_b, c_b)]

    # Store axes for potential shared linking
    scatter_axes = []
    ts_axes_matrix = [] # Rows = bands, Cols = datasets

    for i, (df, label, c_vals) in enumerate(datasets):
        # Inner Grid: 2 Rows (Scatter, TimeSeries), Height Ratio 1.3:1
        gs_inner = gs_outer[i].subgridspec(2, 1, height_ratios=[1.3, 1.0], hspace=0.15)

        # --- Top: Scatter Plot ---
        ax_sc = fig.add_subplot(gs_inner[0])
        scatter_axes.append(ax_sc)

        if not df.empty:
            c_arg = c_vals if color_col else "tab:blue"
            sc = ax_sc.scatter(
                df[x_col],
                df[y_col],
                c=c_arg,
                cmap=cmap if color_col else None,
                norm=norm,
                s=15, alpha=0.6, edgecolors="none"
            )
        else:
            ax_sc.text(0.5, 0.5, "No Data", ha='center')

        ax_sc.set_title(f"{label}\nPhase Space ({x_col} vs {y_col})", fontweight='bold', fontsize=12)
        ax_sc.set_xlabel(f"{x_col} Drift", fontsize=10)
        if i == 0:
            ax_sc.set_ylabel(f"{y_col} Drift", fontsize=10)
        else:
            # Hide Y labels for the right plot to clean up, if they share axis
            # But we set limits manually, so maybe keep ticks but remove label?
            # Let's keep ticks for readability.
            pass

        if log_scale:
            ax_sc.set_xscale("log")
            ax_sc.set_yscale("log")

        ax_sc.grid(True, which="both", alpha=0.3)
        ax_sc.set_xlim(x_min, x_max)
        ax_sc.set_ylim(y_min, y_max)

        # --- Bottom: Stacked Time Series ---
        n_bands = len(ts_bands)
        gs_ts = gs_inner[1].subgridspec(n_bands, 1, hspace=0.0)

        # Calculate Relative Time
        if not df.empty:
            t0 = df["time"].min()
            t_rel = df["time"] - t0

            # Heuristic Units
            dur = t_rel.max()
            if dur > 3600:
                t_plot = t_rel / 3600.0
                t_unit = "Hours"
            elif dur > 60:
                t_plot = t_rel / 60.0
                t_unit = "Minutes"
            else:
                t_plot = t_rel
                t_unit = "Seconds"
        else:
            t_plot = []
            t_unit = "Seconds"

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

        current_col_ts_axes = []

        for b_idx, band in enumerate(ts_bands):
            ax_ts = fig.add_subplot(gs_ts[b_idx])
            current_col_ts_axes.append(ax_ts)

            if not df.empty and band in df.columns:
                col = colors[b_idx % len(colors)]
                ax_ts.plot(t_plot, df[band], color=col, linewidth=1.2)

                # In-plot label
                ax_ts.text(0.01, 0.8, band, transform=ax_ts.transAxes,
                           fontweight='bold', fontsize=9,
                           bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

            if log_scale:
                ax_ts.set_yscale("log")

            ax_ts.grid(True, which="both", alpha=0.3)

            # Formatting
            if i == 0:
                ax_ts.set_ylabel(r"$\|\Omega\|$", fontsize=9)

            if b_idx < n_bands - 1:
                ax_ts.set_xticklabels([])
            else:
                ax_ts.set_xlabel(f"Time ({t_unit} from start)", fontsize=10)

        ts_axes_matrix.append(current_col_ts_axes)

    # --- 3. Link TS Y-Axes across columns ---
    # Row 0 Left linked to Row 0 Right, etc.
    # ts_axes_matrix has 2 lists (Left Col Axes, Right Col Axes)
    if len(ts_axes_matrix) == 2:
        left_ts = ts_axes_matrix[0]
        right_ts = ts_axes_matrix[1]
        for ax_l, ax_r in zip(left_ts, right_ts):
            # Share Y limits
            # We explicitly get limits from both and set the max
            # (Matplotlib sharey might hide ticks on the right, we want visible ticks but locked scale)
            yl_l = ax_l.get_ylim()
            yl_r = ax_r.get_ylim()

            # For log scale, be careful with 0 or infinites
            if log_scale:
                # Just let sharey handle it or manually compute?
                # sharey is easiest
                ax_l.sharey(ax_r)
            else:
                new_min = min(yl_l[0], yl_r[0])
                new_max = max(yl_l[1], yl_r[1])
                ax_l.set_ylim(new_min, new_max)
                ax_r.set_ylim(new_min, new_max)

    # --- 4. Shared Colorbar (if applicable) ---
    if color_col and norm:
        # Create a dummy ScalarMappable
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])

        # Place colorbar on the far right
        fig.subplots_adjust(right=0.9)
        cbar_ax = fig.add_axes([0.92, 0.55, 0.015, 0.3]) # Positioned next to Scatter plots
        fig.colorbar(sm, cax=cbar_ax, label=c_lbl)

    if title:
        fig.suptitle(title, fontsize=18, y=0.95)

    try:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Double Super Plot saved to: {output_path}")
    except Exception as e:
        print(f"Error saving plot: {e}")


def parse_args():
    parser = argparse.ArgumentParser(description="Double Super Drift Visualization.")

    parser.add_argument("file_a", type=str, help="First CSV file")
    parser.add_argument("file_b", type=str, help="Second CSV file")

    parser.add_argument("--label-a", type=str, default="Dataset A", help="Label for Left")
    parser.add_argument("--label-b", type=str, default="Dataset B", help="Label for Right")

    # Zoom Options - Independent for A and B
    parser.add_argument("--start-a", type=float, default=None, help="Start GPS for File A")
    parser.add_argument("--end-a", type=float, default=None, help="End GPS for File A")
    parser.add_argument("--start-b", type=float, default=None, help="Start GPS for File B")
    parser.add_argument("--end-b", type=float, default=None, help="End GPS for File B")

    # Plotting Options
    parser.add_argument("--x-band", type=str, default="v_low", help="Scatter X")
    parser.add_argument("--y-band", type=str, default="v_mid", help="Scatter Y")
    parser.add_argument("--ts-bands", type=str, default="v_low,v_mid,v_high,total", help="TS bands list")

    parser.add_argument(
        "--color-by", type=str, default="time",
        help="Column to color Scatter by (default: time)"
    )

    parser.add_argument("-o", "--output", type=str, default="drift_super_multi.png", help="Output filename")
    parser.add_argument("--linear", action="store_true", help="Use linear scales")
    parser.add_argument("--title", type=str, default=None, help="Global Title")

    return parser.parse_args()


def main():
    args = parse_args()

    df_a = load_data(args.file_a, start=args.start_a, end=args.end_a)
    df_b = load_data(args.file_b, start=args.start_b, end=args.end_b)

    ts_bands_list = [b.strip() for b in args.ts_bands.split(",")]

    make_super_multi_plot(
        df_a, df_b,
        label_a=args.label_a,
        label_b=args.label_b,
        x_col=args.x_band,
        y_col=args.y_band,
        ts_bands=ts_bands_list,
        output_path=args.output,
        color_col=args.color_by,
        log_scale=not args.linear,
        title=args.title
    )


if __name__ == "__main__":
    main()
