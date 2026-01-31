from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

import anndata as ad
import pandas as pd
import scanpy as sc


def _pick_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    """Return the first matching column name from candidates (case-insensitive)."""
    lookup = {col.lower(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _find_file(base: Path, patterns: Iterable[str]) -> Path:
    """Find the first existing path matching any of the patterns inside base."""
    for pattern in patterns:
        candidate = base / pattern
        if candidate.exists():
            return candidate
        matches = list(base.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"Could not find any of {patterns} in {base}")


def _read_counts_csv(path: Path) -> pd.DataFrame:
    """Read a counts CSV where the first column is either genes or cell IDs."""
    counts_df = pd.read_csv(path)
    if counts_df.shape[1] < 2:
        raise ValueError(f"Counts file {path} does not contain enough columns to build a matrix.")

    first_col = counts_df.columns[0]
    if first_col.lower() in {"gene", "target", "target_name", "targetname", "feature"}:
        counts_df = counts_df.rename(columns={first_col: "gene"}).set_index("gene")
        counts_df = counts_df.T
    else:
        counts_df = counts_df.set_index(first_col)

    counts_df.index = counts_df.index.astype(str)
    counts_df.columns = counts_df.columns.astype(str)
    return counts_df


def _prepare_metadata(
    metadata_df: pd.DataFrame,
    cell_candidates: Iterable[str],
    x_candidates: Iterable[str],
    y_candidates: Iterable[str],
) -> pd.DataFrame:
    """Normalize metadata to contain cell_id, x_centroid, and y_centroid columns."""
    cell_col = _pick_column(metadata_df.columns, cell_candidates)
    if cell_col is None:
        raise ValueError("Could not find a cell identifier column in metadata.")
    x_col = _pick_column(metadata_df.columns, x_candidates)
    y_col = _pick_column(metadata_df.columns, y_candidates)
    if x_col is None or y_col is None:
        raise ValueError("Could not find centroid columns in metadata.")

    normalized = metadata_df.rename(
        columns={
            cell_col: "cell_id",
            x_col: "x_centroid",
            y_col: "y_centroid",
        }
    )
    normalized["cell_id"] = normalized["cell_id"].astype(str)
    return normalized[["cell_id", "x_centroid", "y_centroid"]]


def _load_vizgen(input_dir: Path) -> ad.AnnData:
    counts_path = _find_file(input_dir, ["cell_by_gene.csv", "cell_by_gene.csv.gz", "cell_by_gene*.csv"])
    metadata_path = _find_file(input_dir, ["cell_metadata.csv", "cell_metadata.csv.gz", "cell_metadata*.csv"])

    counts_df = _read_counts_csv(counts_path)
    metadata_df = pd.read_csv(metadata_path)
    metadata_df = _prepare_metadata(
        metadata_df,
        cell_candidates=["cell_id", "cell", "id", "cellid"],
        x_candidates=["x_centroid", "center_x", "x", "xc", "x_px"],
        y_candidates=["y_centroid", "center_y", "y", "yc", "y_px"],
    ).set_index("cell_id")

    common_cells = counts_df.index.intersection(metadata_df.index)
    if common_cells.empty:
        raise ValueError("No overlapping cell IDs between counts and metadata for Vizgen input.")

    counts_df = counts_df.loc[common_cells]
    metadata_df = metadata_df.loc[common_cells]
    adata = ad.AnnData(counts_df)
    adata.obs = metadata_df.copy()
    adata.obs["cell_id"] = adata.obs.index
    return adata


def _load_xenium(input_dir: Path) -> ad.AnnData:
    counts_path = _find_file(
        input_dir,
        [
            "cell_feature_matrix.h5",
            "cell_feature_matrix/cell_feature_matrix.h5",
            "cell_feature_matrix*.h5",
        ],
    )
    metadata_path = _find_file(
        input_dir,
        ["cells.csv", "cells.csv.gz", "cell_metadata.csv", "cell_metadata.csv.gz", "cells*.csv"],
    )

    adata = sc.read_10x_h5(counts_path)
    adata.var_names_make_unique()

    metadata_df = pd.read_csv(metadata_path)
    metadata_df = _prepare_metadata(
        metadata_df,
        cell_candidates=["cell_id", "barcode", "cell", "id"],
        x_candidates=["x_centroid", "x", "x_global_px", "x_local_px", "x_um", "px_x"],
        y_candidates=["y_centroid", "y", "y_global_px", "y_local_px", "y_um", "px_y"],
    )
    metadata_df = metadata_df.set_index("cell_id")

    common_cells = adata.obs_names.intersection(metadata_df.index)
    if common_cells.empty:
        raise ValueError("No overlapping cell IDs between Xenium counts and metadata.")

    adata = adata[common_cells].copy()
    adata.obs = metadata_df.loc[common_cells].copy()
    adata.obs["cell_id"] = adata.obs.index
    return adata


def _load_cosmx(input_dir: Path) -> ad.AnnData:
    counts_path = _find_file(
        input_dir,
        ["exprMat_file.csv", "exprMat_file.csv.gz", "cell_by_gene.csv", "cell_by_gene.csv.gz"],
    )
    metadata_path = _find_file(
        input_dir,
        ["cell_metadata.csv", "cell_metadata_file.csv", "cell_metadata.csv.gz", "cell_metadata_file.csv.gz"],
    )

    counts_df = _read_counts_csv(counts_path)
    metadata_df = pd.read_csv(metadata_path)
    metadata_df = _prepare_metadata(
        metadata_df,
        cell_candidates=["cell_id", "CellID", "cell", "id"],
        x_candidates=["x_centroid", "center_x", "x", "nucleus_x", "px_x"],
        y_candidates=["y_centroid", "center_y", "y", "nucleus_y", "px_y"],
    ).set_index("cell_id")

    common_cells = counts_df.index.intersection(metadata_df.index)
    if common_cells.empty:
        raise ValueError("No overlapping cell IDs between counts and metadata for CosMx input.")

    counts_df = counts_df.loc[common_cells]
    metadata_df = metadata_df.loc[common_cells]
    adata = ad.AnnData(counts_df)
    adata.obs = metadata_df.copy()
    adata.obs["cell_id"] = adata.obs.index
    return adata


def export_platform_outputs(
    platform: str,
    input_path: str | Path,
    output_dir: str | Path,
    *,
    anndata_filename: str | None = None,
    csv_filename: str | None = None,
) -> Tuple[ad.AnnData, Path, Path]:
    """Create AnnData and centroid CSV files from Vizgen, Xenium, or CosMx outputs.

    Parameters
    ----------
    platform : str
        One of {"vizgen", "xenium", "cosmx"} (case-insensitive).
    input_path : str or Path
        Directory containing the platform-specific output files.
    output_dir : str or Path
        Directory where the .h5ad file and centroid CSV will be written.
    anndata_filename : str, optional
        Custom filename for the saved AnnData object (defaults to "<platform>.h5ad").
    csv_filename : str, optional
        Custom filename for the centroid CSV (defaults to "<platform>_centroids.csv").

    Returns
    -------
    AnnData
        The loaded AnnData object.
    Path
        Path to the saved .h5ad file.
    Path
        Path to the saved centroid CSV file containing cell_id, x_centroid, and y_centroid.
    """
    platform_key = platform.lower()
    loaders = {
        "vizgen": _load_vizgen,
        "xenium": _load_xenium,
        "cosmx": _load_cosmx,
    }
    if platform_key not in loaders:
        raise ValueError(f"Unsupported platform '{platform}'. Expected one of {tuple(loaders)}.")

    input_dir = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    adata = loaders[platform_key](input_dir)

    anndata_path = output_dir / (anndata_filename or f"{platform_key}.h5ad")
    csv_path = output_dir / (csv_filename or f"{platform_key}_centroids.csv")

    adata.write_h5ad(anndata_path)
    adata.obs[["cell_id", "x_centroid", "y_centroid"]].to_csv(csv_path, index=False)

    return adata, anndata_path, csv_path
