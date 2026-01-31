import warnings
from itertools import product
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import seaborn as sns
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
from scipy.spatial import cKDTree
from tqdm import tqdm
import hdbscan
from sklearn.cluster import DBSCAN

def assign_cells_hdbscan(
    adata,
    x_col="x_centroid",
    y_col="y_centroid",
    cluster_label_col="hdbscan_cluster",
    min_cluster_size=10,
    min_samples=None,
    **kwargs
):
    """
    Assign cells to clusters using HDBSCAN based on x and y coordinates.

    Parameters
    ----------
    adata : AnnData
        AnnData object with adata.obs containing x_col and y_col.
    x_col, y_col : str
        Column names for x and y centroid coordinates.
    cluster_label_col : str
        Name of the new column in adata.obs for assigned cluster labels.
    min_cluster_size : int
        The minimum size of clusters; single linkage splits that contain fewer points than this will be considered points "falling out" of a cluster rather than a cluster splitting into two new clusters.
    min_samples : int or None
        The number of samples in a neighbourhood for a point to be considered a core point. Defaults to the value of min_cluster_size.
    **kwargs : dict
        Additional keyword arguments passed to hdbscan.HDBSCAN.

    Returns
    -------
    AnnData (modifies adata.obs in place, adding a column with cluster assignments)
    """
    x = adata.obs[x_col].values
    y = adata.obs[y_col].values
    coords = np.stack([x, y], axis=1)
    print(min_cluster_size, min_samples)
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, 
                                min_samples=min_samples,
                                cluster_selection_method='leaf',
                                 **kwargs)
    labels = clusterer.fit_predict(coords)
    adata.obs[cluster_label_col] = labels
    return adata

def refine_each_row(adata, x_peaks, y_peaks, x_col="x_centroid", y_col="y_centroid", core_label_col="path_block_core"):
    """
    For each row (y_peak), fit a line at the mean y of the row, project assigned cells to this line,
    find gaps using a negative histogram, and update cluster assignments to be restricted between gaps.

    Parameters
    ----------
    adata : AnnData
        AnnData object with adata.obs containing x_col and y_col.
    x_peaks : array-like
        Array of x peak positions (bin centers).
    y_peaks : array-like
        Array of y peak positions (bin centers).
    x_col, y_col : str
        Column names for x and y centroid coordinates.
    core_label_col : str
        Name of the column in adata.obs for core labels.

    Returns
    -------
    AnnData (modifies adata.obs in place, updating core_label_col)
    """
    obs = adata.obs
    x = obs[x_col].values
    y = obs[y_col].values

    # For each row (y_peak band)
    for i, y_peak in enumerate(y_peaks):
        # Define a band around the y_peak (e.g., halfway to next/prev peak)
        if i == 0:
            y_min = y_peak - (y_peaks[1] - y_peak) / 2 if len(y_peaks) > 1 else y_peak - 50
        else:
            y_min = (y_peaks[i-1] + y_peak) / 2
        if i == len(y_peaks) - 1:
            y_max = y_peak + (y_peak - y_peaks[i-1]) / 2 if i > 0 else y_peak + 50
        else:
            y_max = (y_peak + y_peaks[i+1]) / 2

        # Select cells in this row band
        row_mask = (y >= y_min) & (y < y_max)
        row_x = x[row_mask]
        row_indices = np.where(row_mask)[0]

        if len(row_x) == 0:
            continue

        # Project to line y = mean(y) (horizontal line)
        projected_x = row_x  # projection is just x coordinate

        # Find gaps using negative histogram (valleys)
        hist, bin_edges = np.histogram(projected_x, bins=100)
        # Invert histogram to find valleys as peaks
        inv_hist = np.max(hist) - hist
        gap_indices, _ = find_peaks(inv_hist, prominence=2)

        # Bin edges for gaps
        gap_bins = bin_edges[gap_indices]

        # Assign clusters between gaps
        # Start/end bins
        cluster_bins = np.concatenate(([bin_edges[0]], gap_bins, [bin_edges[-1]]))
        cluster_ids = np.full(len(row_x), -1, dtype=int)
        for j in range(len(cluster_bins) - 1):
            in_bin = (projected_x >= cluster_bins[j]) & (projected_x < cluster_bins[j+1])
            cluster_ids[in_bin] = j

        # Update core_label_col for these cells
        for idx, cid in zip(row_indices, cluster_ids):
            obs.at[obs.index[idx], core_label_col] = f"row{i}_cluster{cid}" if cid >= 0 else f"row{i}_unassigned"

    return adata


def assign_cells_to_cores(
    adata,
    x_col="x_centroid",
    y_col="y_centroid",
    peak_prominence=100,
    peak_distance=50,
    core_label_col="path_block_core",
    density_bins=1000,
    max_x_peaks=4,
    max_y_peaks=6,
    min_cells_per_center=100,
    preliminary_cluster_col="hdbscan_cluster"
):
    """
    Assign each cell to the closest TMA core using grid centers, local density shifting, and watershed segmentation.

    Steps:
    1. Project all x and y coordinates onto their respective axes.
    2. Find peaks in the 1D histograms of x and y using scipy.signal.find_peaks.
    3. The peaks represent preliminary grid centers (core centers).
    4. Build a 2D density map of cell centroids.
    5. For each grid center, shift it to the nearest local maximum in the density map.
    6. Use the shifted centers as seeds for watershed segmentation on the density map.
    7. Assign each cell to the core region defined by the watershed.

    Parameters
    ----------
    adata : AnnData
        AnnData object with adata.obs containing x_col and y_col.
    x_col, y_col : str
        Column names for x and y centroid coordinates.
    peak_prominence : float
        Prominence parameter for find_peaks (controls peak detection sensitivity).
    peak_distance : int
        Minimum distance between peaks for find_peaks.
    core_label_col : str
        Name of the new column in adata.obs for assigned core labels.
    density_bandwidth : float
        Bandwidth for density estimation (used in gaussian smoothing).
    density_bins : int
        Number of bins for density map in each dimension.

    Returns
    -------
    None (modifies adata.obs in place, adding a column with core assignments)
    """
    if x_col not in adata.obs.columns or y_col not in adata.obs.columns:
        raise ValueError(f"{x_col} or {y_col} not found in adata.obs")
    
    if max_x_peaks < 1 or max_y_peaks < 1:
        raise ValueError("x_peaks and y_peaks must be at least 1")
    
    if min_cells_per_center < 1:
        raise ValueError("min_cells_per_center must be at least 1")
    
    if preliminary_cluster_col not in adata.obs.columns:
        raise ValueError(f"{preliminary_cluster_col} not found in adata.obs. Try running assign_cells_hdbscan first.")
    
    if density_bins < 10:
        raise ValueError("density_bins must be at least 10")
    
    

    x = adata.obs[x_col].values
    y = adata.obs[y_col].values

    # Project onto x and y axes, create histograms
    x_hist, x_edges = np.histogram(x, bins=density_bins)
    y_hist, y_edges = np.histogram(y, bins=density_bins)

    # Find peaks in the histograms
    x_peaks_idx, x_props = find_peaks(x_hist, prominence=peak_prominence, distance=peak_distance)
    y_peaks_idx, y_props = find_peaks(y_hist, prominence=peak_prominence, distance=peak_distance)
    if x_peaks_idx.size == 0:
        raise ValueError("No peaks found in x axis. Try lowering peak_prominence or peak_distance.")
    if y_peaks_idx.size == 0:
        raise ValueError("No peaks found in y axis. Try lowering peak_prominence or peak_distance.")

    # Optionally limit the number of peaks by prominence (or height)
    if max_x_peaks is not None and len(x_peaks_idx) > max_x_peaks:
        # Sort by prominence, then by peak height
        sort_idx = np.lexsort((-x_hist[x_peaks_idx], -x_props["prominences"]))
        x_peaks_idx = x_peaks_idx[sort_idx[:max_x_peaks]]
    if max_y_peaks is not None and len(y_peaks_idx) > max_y_peaks:
        sort_idx = np.lexsort((-y_hist[y_peaks_idx], -y_props["prominences"]))
        y_peaks_idx = y_peaks_idx[sort_idx[:max_y_peaks]]

    # Convert peak indices to coordinate values (bin centers)
    x_peaks = (x_edges[x_peaks_idx] + x_edges[x_peaks_idx + 1]) / 2
    y_peaks = (y_edges[y_peaks_idx] + y_edges[y_peaks_idx + 1]) / 2

    # Check for no peaks found
    if len(x_peaks) == 0 or len(y_peaks) == 0:
        raise ValueError(
            f"No peaks found in {'x' if len(x_peaks)==0 else 'y'} axis. "
            "Try lowering peak_prominence or peak_distance, or check input data."
        )

    # All possible grid centers (core centers)
    core_centers = np.array(list(product(x_peaks, y_peaks)))

    # Assign cells to cores based on circle of radius_threshold around each center
    cell_coords = np.stack([x, y], axis=1)
    n_centers = core_centers.shape[0]
    n_cells = cell_coords.shape[0]

    # --- Modified assignment: assign by cluster in preliminary_cluster_col ---
    cluster_labels = adata.obs[preliminary_cluster_col].values
    unique_clusters = np.unique(cluster_labels)
    filtered_centers = core_centers  # keep filtering logic below if needed

    # Optionally, filter out centers with too few assigned cells (keep as before)
    # We'll count after assignment below

    # Prepare output arrays
    assigned_core_idx = np.full(n_cells, -1, dtype=int)

    for cluster in unique_clusters:
        if cluster == -1:
            # Leave as unassigned
            assigned_core_idx[cluster_labels == cluster] = -1
            continue
        # Get indices of cells in this cluster
        cluster_mask = (cluster_labels == cluster)
        cluster_coords = cell_coords[cluster_mask]
        if len(cluster_coords) == 0:
            continue
        # Compute centroid of the cluster
        centroid = cluster_coords.mean(axis=0)
        # Find nearest core center
        dists_to_centers = np.linalg.norm(filtered_centers - centroid, axis=1)
        nearest_center = np.argmin(dists_to_centers)
        # Assign all cells in this cluster to this core
        assigned_core_idx[cluster_mask] = nearest_center

    # Optionally, filter out centers with too few assigned cells
    counts = np.bincount(assigned_core_idx[assigned_core_idx >= 0], minlength=filtered_centers.shape[0])
    keep_mask = counts >= min_cells_per_center
    filtered_centers = filtered_centers[keep_mask]

    # Reassign clusters: for each cluster, assign to nearest among filtered centers (skip -1)
    final_core_idx = np.full(n_cells, -1, dtype=int)
    for cluster in unique_clusters:
        if cluster == -1:
            final_core_idx[cluster_labels == cluster] = -1
            continue
        cluster_mask = (cluster_labels == cluster)
        cluster_coords = cell_coords[cluster_mask]
        if len(cluster_coords) == 0:
            continue
        centroid = cluster_coords.mean(axis=0)
        dists_to_centers = np.linalg.norm(filtered_centers - centroid, axis=1)
        if len(dists_to_centers) == 0:
            final_core_idx[cluster_mask] = -1
            continue
        nearest_center = np.argmin(dists_to_centers)
        final_core_idx[cluster_mask] = nearest_center

    # Assign core labels
    unique_core_ids = [
        f"core_{int(round(filtered_centers[idx, 0]))}_{int(round(filtered_centers[idx, 1]))}"
        if idx >= 0 else "unassigned"
        for idx in final_core_idx
    ]
    adata.obs[core_label_col] = unique_core_ids

    # Optionally, also store the actual filtered core center coordinates
    adata.obs[core_label_col + "_x"] = [
        filtered_centers[idx, 0] if idx >= 0 else np.nan for idx in final_core_idx
    ]
    adata.obs[core_label_col + "_y"] = [
        filtered_centers[idx, 1] if idx >= 0 else np.nan for idx in final_core_idx
    ]
    return adata

def refine_core_labels(
    adata, k=500, x_col="x_centroid", y_col="y_centroid", core_label_col="path_block_core"
):
    """
    For each unassigned cell, find its k nearest assigned neighbors and assign the majority label among those neighbors to the cell.
    The kNN tree is built only from already assigned cells.

    Parameters
    ----------
    adata : AnnData
        AnnData object with adata.obs containing x_col and y_col.
    k : int
        Number of nearest neighbors to consider.
    x_col, y_col : str
        Column names for x and y centroid coordinates.
    core_label_col : str
        Name of the column in adata.obs for core labels.

    Returns
    -------
    AnnData (modifies adata.obs in place, updating core_label_col)
    """
    if x_col not in adata.obs.columns or y_col not in adata.obs.columns:
        raise ValueError(f"{x_col} or {y_col} not found in adata.obs")
    if core_label_col not in adata.obs.columns:
        raise ValueError(f"{core_label_col} not found in adata.obs")

    coords = adata.obs[[x_col, y_col]].values
    labels = adata.obs[core_label_col].values.copy()

    assigned_mask = labels != "unassigned"
    unassigned_mask = labels == "unassigned"

    assigned_coords = coords[assigned_mask]
    assigned_labels = labels[assigned_mask]
    unassigned_coords = coords[unassigned_mask]
    unassigned_indices = np.where(unassigned_mask)[0]

    if len(assigned_coords) == 0 or len(unassigned_coords) == 0:
        # Nothing to refine
        return adata, 0

    tree = cKDTree(assigned_coords)
    # Query k nearest assigned neighbors for each unassigned cell
    k_eff = min(k, len(assigned_coords))
    dists, idxs = tree.query(unassigned_coords, k=k_eff)

    # If k==1, idxs shape is (n_unassigned,), else (n_unassigned, k)
    if k_eff == 1:
        idxs = idxs[:, None]

    new_labels = labels.copy()
    change_count = 0
    for i, neighbors in enumerate(idxs):
        neighbor_labels = assigned_labels[neighbors]
        vals, counts = np.unique(neighbor_labels, return_counts=True)
        max_count = counts.max()
        major_labels = vals[counts == max_count]
        if len(major_labels) == 1:
            new_label = major_labels[0]
        else:
            # Tie: keep as unassigned
            new_label = "unassigned"
        if new_label != "unassigned":
            change_count += 1
        new_labels[unassigned_indices[i]] = new_label

    adata.obs[core_label_col] = new_labels
    return adata, change_count

def plot_cores(adata, x_col="x_centroid", y_col="y_centroid", core_label_col="path_block_core", title="Sample", skip_cluster=[-1], invert_yaxis=True):
    """Plot cells colored by their assigned core and annotate each core with its name."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    if core_label_col not in adata.obs.columns:
        raise ValueError(f"{core_label_col} not found in adata.obs")

    if x_col not in adata.obs.columns or y_col not in adata.obs.columns:
        raise ValueError(f"{x_col} or {y_col} not found in adata.obs")

    
    adata_sub = adata[~adata.obs[core_label_col].isin(skip_cluster)] if len(skip_cluster) >= 0 else adata
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.scatterplot(
        x=adata_sub.obs[x_col],
        y=adata_sub.obs[y_col],
        hue=adata_sub.obs[core_label_col],
        palette="tab20",
        s=1,
        alpha=0.7,
        edgecolor=None,
        ax=ax
    )
    # Annotate each unique core with its name at the mean position of its cells
    core_labels = adata_sub.obs[core_label_col].unique()
    for core in core_labels:
        core_cells = adata_sub.obs[adata_sub.obs[core_label_col] == core]
        mean_x = core_cells[x_col].mean()
        mean_y = core_cells[y_col].mean()
        ax.text(mean_x, mean_y + 20, str(core), ha='center', va='bottom', fontsize=7,
                 color='black', bbox=dict(facecolor='white', alpha=0.7,
                                           edgecolor='none', boxstyle='round,pad=0.2'))
    plt.title(f"{title} - Cells Colored by Assigned Core")
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    # Equal aspect ratio
    ax.set_aspect("equal", adjustable="box")
    # Remove legend if there was one
    if invert_yaxis:
        ax.invert_yaxis()
    ax.legend().remove() if ax.get_legend() else None
    # Hide axis lines, ticks, and labels
    ax.axis("off")

    return fig

def save_image(fig, output_path, dpi=300):
    """Save the given figure to the specified filepath."""
    output_path = Path(output_path)
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')