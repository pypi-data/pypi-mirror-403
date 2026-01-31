from pathlib import Path
from stile.nodes import *


def identify_tissue_cores(adata):
    adata = assign_cells_hdbscan(adata, min_cluster_size=20, min_samples=7)
    adata = assign_cells_to_cores(adata, min_cells_per_center=10, max_x_peaks=6, max_y_peaks=6)
    adata, count = refine_core_labels(adata, k=50)
    return adata



if __name__ == "__main__":
    DATA_DIR = Path('/ihome/yufeihuang/has197/ix3harsh/11-100.github/14-spatial-ai/05-tma-dearraying/data/simulated/')
    for dataset in DATA_DIR.iterdir():
        print(f"Checking dataset: {dataset.name}")
        if dataset.is_dir():
            dataset_folder = dataset
            create_simulated_adata(dataset_folder)
            adata = sc.read_h5ad(f"{dataset_folder}/adata.h5ad")
            adata = identify_tissue_cores(adata)
            fig = plot_cores(adata, title='')
            save_image(fig, output_path=f"{dataset_folder}/predicted_cores.png", dpi=300)
            print(f"Processed dataset: {dataset_folder.name}")
            # break  # Remove this break to process all datasets

    create_simulated_adata(dataset_folder)

