import streamlit as st
from pathlib import Path
import scanpy as sc

# Import your functions from stile
from stile.nodes import (
    assign_cells_hdbscan,
    assign_cells_to_cores,
    refine_core_labels,
    plot_cores,
)


# ----------------------------
# Streamlit Page Setup
# ----------------------------
st.set_page_config(page_title="STiLE Core Identifier", page_icon="🧬", layout="wide")
st.title("🧬 STiLE: Identify Tissue Cores")
st.caption("Interactive UI equivalent of the `identify_tissue_cores` CLI command.")

# ----------------------------
# Dataset Parameters
# ----------------------------
st.sidebar.header("Dataset Selection")
# seed23_pitch325_rj0.10_rb0.20_mf0.50
# drop down for selecting random seed in a list
seed = 23
pitch = st.sidebar.selectbox("Select pitch", options=[325, 375, 425, 475], index=0)
rj = st.sidebar.number_input("Select random jitter", min_value=0.0, max_value=1.0, step=0.1, value=0.1)
rb = st.sidebar.number_input("Select random bias", min_value=0.0, max_value=1., step=0.2, value=0.0)
mf = st.sidebar.number_input("Select missing fraction", min_value=0.0, max_value=0.5, step=0.1, value=0.5)
parent_dir = Path('/ihome/yufeihuang/has197/ix3harsh/11-100.github/14-spatial-ai/05-tma-dearraying/data/simulated')
data_filename = f"seed{seed}_pitch{pitch}_rj{rj:.2f}_rb{rb:.2f}_mf{mf:.2f}"
adata_folder = parent_dir / data_filename
adata_path_str = adata_folder/'adata.h5ad'

# ----------------------------
# Sidebar Parameters
# ----------------------------
st.sidebar.header("Parameters")

# adata_path_str = st.sidebar.text_input("Path to AnnData (.h5ad)", value="data/sample.h5ad")
min_cluster_size = st.sidebar.number_input("min_cluster_size", min_value=2, value=20)
min_samples = st.sidebar.number_input("min_samples", min_value=1, value=7)
min_cells_per_center = st.sidebar.number_input("min_cells_per_center", min_value=1, value=10)
num_rows = st.sidebar.number_input("num_rows (y peaks)", min_value=1, value=7)
num_cols = st.sidebar.number_input("num_cols (x peaks)", min_value=1, value=7)
refine_k = st.sidebar.number_input("refine_k", min_value=1, value=50)
x_col = st.sidebar.text_input("x_col", value="x_centroid")
y_col = st.sidebar.text_input("y_col", value="y_centroid")
peak_prominence = st.sidebar.number_input("peak_prominence", min_value=1, value=50)
peak_distance = st.sidebar.number_input("peak_distance", min_value=1, value=50)
density_bins = st.sidebar.number_input("density_bins", min_value=10, value=1000, step=10)
preliminary_cluster_col = st.sidebar.text_input("preliminary_cluster_col", value="hdbscan_cluster")
core_label_col = st.sidebar.text_input("core_label_col", value="path_block_core")
save_intermediate = st.sidebar.checkbox("Save & preview intermediate cluster plot", value=False)


# ----------------------------
# Run Button
# ----------------------------
st.subheader("1️⃣ Run Analysis")
# st.write("Enter the path to your `.h5ad` file and click below to process tissue cores.")

run_btn = st.button("▶️ Run identify_tissue_cores")

# ----------------------------
# Main Logic
# ----------------------------
if run_btn:
    adata_path = Path(adata_path_str)
    if not adata_path.exists():
        st.error(f"The specified file does not exist: `{adata_path}`")
        st.stop()
    output_image = adata_folder / "adata_cores.png"
    if output_image.exists():
        st.warning(f"Output image already exists and will be overwritten: `{output_image}`")
    try:
        progress = st.progress(0)
        st.info(f"Loading AnnData from `{adata_path}` …")
        adata = sc.read_h5ad(adata_path)
        progress.progress(10)

        # Step 1 — HDBSCAN clustering
        st.write("🔹 Assigning preliminary HDBSCAN clusters …")
        adata = assign_cells_hdbscan(
            adata,
            x_col=x_col,
            y_col=y_col,
            cluster_label_col=preliminary_cluster_col,
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
        )
        progress.progress(35)

        if save_intermediate:
            st.write("📊 Generating intermediate cluster plot …")
            fig_temp = plot_cores(
                adata,
                x_col=x_col,
                y_col=y_col,
                core_label_col=preliminary_cluster_col,
            )
            st.pyplot(fig_temp)
            output_temp = adata_path.parent / f"{adata_path.stem}_temp_assignments.png"
            fig_temp.savefig(output_temp, dpi=100)
            st.success(f"Intermediate plot saved to: `{output_temp}`")
        progress.progress(50)

        # Step 2 — Assign cells to cores
        st.write("🔹 Assigning cells to spatial cores …")
        adata = assign_cells_to_cores(
            adata,
            max_x_peaks=num_cols,
            max_y_peaks=num_rows,
            x_col=x_col,
            y_col=y_col,
            peak_prominence=peak_prominence,
            peak_distance=peak_distance,
            core_label_col=core_label_col,
            density_bins=density_bins,
            min_cells_per_center=min_cells_per_center,
            preliminary_cluster_col=preliminary_cluster_col,
        )
        progress.progress(75)

        # Step 3 — Refine labels
        st.write("🔹 Refining core labels (kNN smoothing) …")
        adata, count = refine_core_labels(
            adata,
            k=refine_k,
            core_label_col=core_label_col,
            x_col=x_col,
            y_col=y_col,
        )
        progress.progress(80)

        # Step 4 — Final plot
        st.write("📊 Generating final tissue core plot …")
        fig_final = plot_cores(
            adata, x_col=x_col, y_col=y_col, core_label_col=core_label_col
        )
        st.pyplot(fig_final)

        output_final = adata_path.parent / f"{adata_path.stem}_cores.png"
        fig_final.savefig(output_final, dpi=300)
        st.success(f"✅ Final tissue core plot saved to: `{output_final}`")

        # Save updated AnnData
        output_adata = adata_path.parent / f"{adata_path.stem}_with_cores.h5ad"
        adata.write_h5ad(output_adata)
        st.success(f"✅ Updated AnnData saved to: `{output_adata}`")
        progress.progress(90)
        # Save chosen parameters
        params_output = adata_path.parent / 'hyperparameters_used.json'
        params = {
            "min_cluster_size": min_cluster_size,
            "min_samples": min_samples,
            "min_cells_per_center": min_cells_per_center,
            "num_rows": num_rows,
            "num_cols": num_cols,
            "refine_k": refine_k,
            "x_col": x_col,
            "y_col": y_col,
            "peak_prominence": peak_prominence,
            "peak_distance": peak_distance,
            "density_bins": density_bins,
            "preliminary_cluster_col": preliminary_cluster_col,
            "core_label_col": core_label_col,
        }
        import json
        with open(params_output, 'w') as f:
            json.dump(params, f, indent=4)
        st.success(f"✅ Hyperparameters saved to: `{params_output}`")
        progress.progress(100)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.stop()


# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.caption("This Streamlit UI runs the same workflow as your CLI command `identify_tissue_cores`.")
