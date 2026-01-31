"""
Generate plots showing how tuned dearraying hyperparameters vary across simulated dataset characteristics.

This script expects simulated datasets stored under a directory with names like:
  seed23_pitch325_rj0.00_rb0.20_mf0.50/

and a tuned parameter file inside each directory:
  hyperparameters_used.json

It produces:
  - A CSV table of dataset factors + tuned hyperparameters
  - Heatmaps (rb vs rj) faceted by pitch (rows) and mf (columns)
  - Marginal trend plots for each hyperparameter vs each factor
  - Optional delta heatmaps relative to a baseline (rj=min, rb=min, mf=min) within each pitch
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FOLDER_RE = re.compile(
    r"^seed(?P<seed>\d+)_pitch(?P<pitch>\d+)_rj(?P<rj>\d+(?:\.\d+)?)_rb(?P<rb>\d+(?:\.\d+)?)_mf(?P<mf>\d+(?:\.\d+)?)$"
)


@dataclass(frozen=True)
class Factors:
    seed: int
    pitch: int
    rj: float
    rb: float
    mf: float


def _parse_factors(folder_name: str) -> Factors | None:
    match = FOLDER_RE.match(folder_name)
    if match is None:
        return None
    groups = match.groupdict()
    return Factors(
        seed=int(groups["seed"]),
        pitch=int(groups["pitch"]),
        rj=float(groups["rj"]),
        rb=float(groups["rb"]),
        mf=float(groups["mf"]),
    )


def load_hyperparameter_table(sim_dir: Path) -> pd.DataFrame:
    rows: list[dict] = []
    for hp_path in sorted(sim_dir.glob("*/hyperparameters_used.json")):
        factors = _parse_factors(hp_path.parent.name)
        if factors is None:
            continue
        try:
            with hp_path.open() as f:
                params = json.load(f)
        except json.JSONDecodeError:
            continue

        row: dict = {
            "dataset_dir": str(hp_path.parent),
            "seed": factors.seed,
            "pitch": factors.pitch,
            "rj": factors.rj,
            "rb": factors.rb,
            "mf": factors.mf,
        }
        row.update(params)
        rows.append(row)

    if not rows:
        raise FileNotFoundError(
            f"No tuned hyperparameter files found under {sim_dir} (expected */hyperparameters_used.json)."
        )
    df = pd.DataFrame(rows)
    return df


def _numeric_hyperparameters(df: pd.DataFrame, factors: Iterable[str]) -> list[str]:
    ignore = set(factors) | {"dataset_dir"}
    candidates = [c for c in df.columns if c not in ignore]
    numeric = []
    for c in candidates:
        if pd.api.types.is_numeric_dtype(df[c]):
            numeric.append(c)
    return sorted(numeric)


def _sorted_unique(values: pd.Series) -> list:
    return sorted(pd.unique(values))


def _heatmap_axes(
    ax: plt.Axes,
    matrix: np.ndarray,
    row_labels: list[str],
    col_labels: list[str],
    *,
    cmap: str,
    vmin: float,
    vmax: float,
    title: str,
) -> None:
    m = np.array(matrix, dtype=float)
    mask = np.isnan(m)
    m = np.ma.masked_array(m, mask=mask)

    cm = plt.get_cmap(cmap).copy()
    cm.set_bad(color="white")

    im = ax.imshow(m, aspect="auto", origin="lower", cmap=cm, vmin=vmin, vmax=vmax)
    ax.set_title(title, fontsize=9)
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels, rotation=90, fontsize=7)
    ax.set_yticklabels(row_labels, fontsize=7)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return im


def plot_heatmaps(
    df: pd.DataFrame,
    outdir: Path,
    param: str,
    *,
    deltas: bool = False,
    baseline_by_pitch: dict[int, float] | None = None,
) -> Path:
    pitches = _sorted_unique(df["pitch"])
    mfs = _sorted_unique(df["mf"])
    rjs = _sorted_unique(df["rj"])
    rbs = _sorted_unique(df["rb"])

    row_labels = [f"{v:.2f}" for v in rjs]
    col_labels = [f"{v:.2f}" for v in rbs]

    if deltas:
        if baseline_by_pitch is None:
            raise ValueError("baseline_by_pitch must be provided when deltas=True")
        values = []
        for pitch in pitches:
            base = baseline_by_pitch.get(pitch)
            if base is None or np.isnan(base):
                continue
            values.append(df.loc[df["pitch"] == pitch, param] - base)
        if values:
            vlim = float(np.nanmax(np.abs(pd.concat(values, ignore_index=True))))
        else:
            vlim = 1.0
        vmin, vmax = -vlim, vlim
        cmap = "coolwarm"
        label = f"Δ{param}"
        suffix = "delta"
    else:
        vmin = float(np.nanmin(df[param]))
        vmax = float(np.nanmax(df[param]))
        if vmin == vmax:
            vmax = vmin + 1.0
        cmap = "viridis"
        label = param
        suffix = "heatmap"

    fig_w = max(10, 1.6 * len(mfs))
    fig_h = max(6, 1.6 * len(pitches))
    fig, axes = plt.subplots(
        nrows=len(pitches),
        ncols=len(mfs),
        figsize=(fig_w, fig_h),
        squeeze=False,
        constrained_layout=True,
    )

    last_im = None
    for i, pitch in enumerate(pitches):
        for j, mf in enumerate(mfs):
            ax = axes[i][j]
            sub = df[(df["pitch"] == pitch) & (df["mf"] == mf)]
            if sub.empty:
                ax.axis("off")
                continue
            pivot = (
                sub.pivot_table(index="rj", columns="rb", values=param, aggfunc="mean")
                .reindex(index=rjs, columns=rbs)
                .to_numpy()
            )
            if deltas:
                base = baseline_by_pitch.get(pitch)
                if base is None or np.isnan(base):
                    ax.axis("off")
                    continue
                pivot = pivot - base
            title = f"pitch={pitch}, mf={mf:.2f}"
            last_im = _heatmap_axes(
                ax,
                pivot,
                row_labels,
                col_labels,
                cmap=cmap,
                vmin=vmin,
                vmax=vmax,
                title=title,
            )
            if i == len(pitches) - 1:
                ax.set_xlabel("rb", fontsize=8)
            if j == 0:
                ax.set_ylabel("rj", fontsize=8)

    if last_im is not None:
        cbar = fig.colorbar(last_im, ax=axes, shrink=0.7, location="right")
        cbar.set_label(label, fontsize=9)

    outpath = outdir / f"{suffix}_{param}.png"
    fig.savefig(outpath, dpi=300)
    plt.close(fig)
    return outpath


def plot_marginals(df: pd.DataFrame, outdir: Path, param: str) -> Path:
    factors = ["pitch", "rj", "rb", "mf"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    axes = axes.ravel()

    for ax, factor in zip(axes, factors, strict=True):
        stats = (
            df.groupby(factor, dropna=False)[param]
            .agg(["mean", "std", "count"])
            .reset_index()
            .sort_values(factor)
        )
        x = stats[factor].to_numpy()
        y = stats["mean"].to_numpy()
        yerr = stats["std"].to_numpy()

        ax.errorbar(x, y, yerr=yerr, fmt="-o", linewidth=1.2, markersize=3, capsize=2)
        ax.set_title(f"{param} vs {factor}", fontsize=10)
        ax.set_xlabel(factor)
        ax.set_ylabel(param)
        ax.grid(True, alpha=0.25)

    outpath = outdir / f"marginal_{param}.png"
    fig.savefig(outpath, dpi=300)
    plt.close(fig)
    return outpath


def baseline_by_pitch(df: pd.DataFrame, param: str) -> dict[int, float]:
    min_rj = float(df["rj"].min())
    min_rb = float(df["rb"].min())
    min_mf = float(df["mf"].min())
    base = df[(df["rj"] == min_rj) & (df["rb"] == min_rb) & (df["mf"] == min_mf)]

    out: dict[int, float] = {}
    for pitch in _sorted_unique(df["pitch"]):
        vals = base.loc[base["pitch"] == pitch, param]
        out[int(pitch)] = float(vals.median()) if not vals.empty else float("nan")
    return out


def plot_correlation_matrix(df: pd.DataFrame, outdir: Path, params: list[str]) -> Path:
    cols = ["pitch", "rj", "rb", "mf"] + params
    corr = df[cols].corr(method="spearman", numeric_only=True)

    fig, ax = plt.subplots(figsize=(0.5 * len(cols) + 4, 0.5 * len(cols) + 4), constrained_layout=True)
    im = ax.imshow(corr.to_numpy(), cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(np.arange(len(cols)))
    ax.set_yticks(np.arange(len(cols)))
    ax.set_xticklabels(cols, rotation=90, fontsize=8)
    ax.set_yticklabels(cols, fontsize=8)
    ax.set_title("Spearman correlation (simulation factors vs hyperparameters)", fontsize=11)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Spearman ρ", fontsize=9)

    outpath = outdir / "correlation_matrix_spearman.png"
    fig.savefig(outpath, dpi=300)
    plt.close(fig)
    return outpath


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sim-dir",
        type=Path,
        default=Path("data/simulated"),
        help="Directory containing simulated dataset folders (default: data/simulated).",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("plots/hyperparameter_sweep"),
        help="Output directory for plots and tables (default: plots/hyperparameter_sweep).",
    )
    parser.add_argument(
        "--params",
        type=str,
        default="",
        help="Comma-separated list of hyperparameters to plot (default: all numeric hyperparameters found).",
    )
    parser.add_argument(
        "--no-deltas",
        action="store_true",
        help="Disable delta heatmaps (otherwise compute Δ relative to baseline within each pitch).",
    )
    args = parser.parse_args()

    df = load_hyperparameter_table(args.sim_dir)
    args.outdir.mkdir(parents=True, exist_ok=True)

    factor_cols = ["seed", "pitch", "rj", "rb", "mf"]
    numeric_params = _numeric_hyperparameters(df, factor_cols)
    if args.params.strip():
        requested = [p.strip() for p in args.params.split(",") if p.strip()]
        missing = [p for p in requested if p not in df.columns]
        if missing:
            raise SystemExit(f"Unknown hyperparameter columns: {missing}")
        params = requested
    else:
        params = numeric_params

    # Save table for downstream use
    table_path = args.outdir / "hyperparameters_vs_simulation.csv"
    df.sort_values(["pitch", "mf", "rb", "rj"]).to_csv(table_path, index=False)

    # Correlation overview
    plot_correlation_matrix(df, args.outdir, params=params)

    # Per-parameter plots
    for param in params:
        plot_marginals(df, args.outdir, param)
        plot_heatmaps(df, args.outdir, param, deltas=False)
        if not args.no_deltas:
            base = baseline_by_pitch(df, param)
            plot_heatmaps(df, args.outdir, param, deltas=True, baseline_by_pitch=base)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

