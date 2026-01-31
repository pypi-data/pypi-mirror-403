# TMA de-arraying for spatial transcriptomics

STile helps segment tissue microarray (TMA) cores from single-cell spatial transcriptomics data and prepare platform-specific outputs for downstream analysis.

## What it does

- Detects tissue cores by clustering cell centroids with HDBSCAN and refining core labels for Vizgen, Xenium, and CosMx outputs.

## Main entry points

- `stile identify_tissue_cores`: Load a `.h5ad`, cluster cells, assign cores, and save core plots.
- `stile prepare_data`: Convert Vizgen/Xenium/CosMx output directories into an `.h5ad` plus `cell_id`, `x_centroid`, `y_centroid` CSV for further processing.

## Quickstart

```bash
# Build AnnData and centroid CSV from a platform run directory
stile prepare_data xenium path/to/xenium/output path/to/save
stile run
```
