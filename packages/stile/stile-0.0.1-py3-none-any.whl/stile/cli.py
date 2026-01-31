"""Console script for stile."""

import typer
from rich.console import Console
import subprocess
import sys

from stile import utils
from stile.nodes import assign_cells_hdbscan, assign_cells_to_cores, refine_core_labels, plot_cores
from stile.io import export_platform_outputs
import scanpy as sc
from pathlib import Path


app = typer.Typer()
console = Console()


@app.command()
def identify_tissue_cores(adata_path: str, 
                            min_cluster_size:int = 20, 
                            min_samples:int = 7,
                            min_cells_per_center:int = 10,
                            num_rows: int = 7,
                            num_cols: int = 7,
                            refine_k: int = 50,
                            x_col: str = "x_centroid",
                            y_col: str = "y_centroid",
                            peak_prominence: int = 50,
                            peak_distance: int = 50,
                            density_bins: int = 1000,
                            preliminary_cluster_col: str = "hdbscan_cluster",
                            core_label_col: str = "path_block_core",
                            save_intermediate: bool = False,
                        ):
    adata_path = Path(adata_path)
    if not adata_path.exists():
        console.print(f"[red]Error:[/red] The specified adata file does not exist: {adata_path}")
        raise typer.Exit(code=1)
    adata = sc.read_h5ad(adata_path)
    adata = assign_cells_hdbscan(adata, 
                                x_col=x_col,
                                y_col=y_col,
                                cluster_label_col=preliminary_cluster_col,
                                min_cluster_size=min_cluster_size, 
                                min_samples=min_samples)
    if save_intermediate:
        fig = plot_cores(adata, x_col=x_col, y_col=y_col, core_label_col=preliminary_cluster_col)
        output_path=adata_path.parent / f"{adata_path.stem}_temp_assignments.png"
        fig.savefig(output_path, dpi=300)
        # console.print(f"[green]Tissue core plot saved to:[/green] {output_path}")
    adata = assign_cells_to_cores(adata, 
                                    max_x_peaks=num_cols, 
                                    max_y_peaks=num_rows,
                                    x_col=x_col,
                                    y_col=y_col,
                                    peak_prominence=peak_prominence,
                                    peak_distance=peak_distance,
                                    core_label_col=core_label_col,
                                    density_bins=density_bins,
                                    min_cells_per_center=min_cells_per_center,
                                    preliminary_cluster_col=preliminary_cluster_col)
    adata, count = refine_core_labels(adata, k=refine_k,
                                    core_label_col=core_label_col,
                                    x_col=x_col,
                                    y_col=y_col)
    fig = plot_cores(adata, x_col=x_col, y_col=y_col, core_label_col=core_label_col)
    output_path=adata_path.parent / f"{adata_path.stem}_cores.png"
    fig.savefig(output_path, dpi=300)
    console.print(f"[green]Tissue core plot saved to:[/green] {output_path}")
    return adata


@app.command()
def prepare_data(
    platform: str = typer.Argument(..., help="Platform name: vizgen, xenium, or cosmx"),
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Directory containing the raw platform outputs",
    ),
    output_dir: Path = typer.Argument(
        ...,
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
        help="Directory where the .h5ad and centroid CSV will be written",
    ),
    anndata_filename: str = typer.Option(
        None,
        "--anndata-filename",
        "-a",
        help="Custom filename for the saved AnnData file (defaults to <platform>.h5ad)",
    ),
    csv_filename: str = typer.Option(
        None,
        "--csv-filename",
        "-c",
        help="Custom filename for the centroid CSV (defaults to <platform>_centroids.csv)",
    ),
):
    """Generate AnnData and centroid CSV files from platform outputs."""
    try:
        _, adata_path, csv_path = export_platform_outputs(
            platform=platform,
            input_path=input_path,
            output_dir=output_dir,
            anndata_filename=anndata_filename,
            csv_filename=csv_filename,
        )
    except Exception as exc:  # pragma: no cover - CLI reporting only
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    console.print(f"[green]Saved AnnData:[/green] {adata_path}")
    console.print(f"[green]Saved centroids CSV:[/green] {csv_path}")


@app.command()
def run():
    """Launch the Streamlit UI (same workflow as identify_tissue_cores)."""
    app_path = Path(__file__).with_name("app.py")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    result = subprocess.run(cmd)
    if result.returncode != 0:  # pragma: no cover - CLI passthrough
        raise typer.Exit(code=result.returncode)


if __name__ == "__main__":
    app()
