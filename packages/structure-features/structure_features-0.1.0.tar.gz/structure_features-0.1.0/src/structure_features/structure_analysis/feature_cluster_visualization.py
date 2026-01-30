"""
These modules visualize features and clusters in the model using the following functions:  
- `feature_cluster_visualization`: Executes both layerwise_visualization and model_visualization.  
- `layerwise_visualization`: For each layer, the visualization arranges features with tokens as rows and embedding dimensions as columns. Certain structures are highlighted with colored boundaries.  
- `model_visualization`: Across multiple layers, the visualization arranges features with layers as rows and selected feature indices as columns. Certain structures are highlighted with colored boundaries.  

The results are saved under the output_directory as follows:  
- `layerwise_visualization/layer_*_*_*.png`: A set of per-layer visualizations in the subfolder "layerwise_visualization/"  
  &nbsp;&nbsp; (e.g., layer_0_r000_c000.png, layer_0_r000_c001.png, ...).  
- `model_feature_structure_visualization.png`: A single model-level visualization file.

Copyright (c) 2025 Sejik Park

---
"""

import os
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
from tqdm import tqdm
from typing import List
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap

__all__ = ['feature_cluster_visualization', 'layerwise_visualization', 'model_visualization']


def feature_cluster_visualization(
    features: np.ndarray,
    output_directory: str,
    labels: np.ndarray,
    visualization_indices: List[int],
    label_threshold: int = 20,
):
    """
    Args:
        features:
            Features as 4D array of shape (batch size, layer dimension, token dimension, embedding dimension).
        output_directory:
            Base directory where visualizations will be saved.
        labels: 
            Indices of structure groups assigned to each feature, as 3D array of shape
            (layer dimension, token dimension, embedding dimension).
        visualization_indices:
            Flat indices selecting specific units to display across layers.
        label_threshold:
            Maximum label index to be highlighted. Only features with label index 
            below this threshold are outlined for clearer color separation.
    """
    B = features.shape[0]
    sqrt_n = math.ceil(math.sqrt(B))
    required = sqrt_n * sqrt_n

    # Pad with zeros if necessary
    if B < required:
        pad_width = ((0, required - B), (0, 0), (0, 0), (0, 0))  # pad batch dim only
        features = np.pad(features, pad_width, mode="constant", constant_values=0)

    x1, x2 = np.meshgrid(
        np.linspace(0.0, 1.0, sqrt_n),
        np.linspace(0.0, 1.0, sqrt_n)
    )
    cmap = matplotlib.colormaps.get_cmap('tab20')

    layerwise_visualization(
        features, output_directory, labels, x1, x2, cmap,
        label_threshold=label_threshold
    )

    embedding_dim = features.shape[-1]
    model_visualization(
        features, output_directory, visualization_indices, embedding_dim,
        labels, x1, x2, cmap,
        label_threshold=label_threshold
    )


def layerwise_visualization(
    features: np.ndarray,
    output_directory: str,
    labels: np.ndarray,
    x1: np.ndarray,
    x2: np.ndarray,
    cmap: Colormap,
    label_threshold: int = 20,
    rows_per_page: int = 6, 
    cols_per_page: int = 12,
):
    """
    Args:
        features: 
            Features to visualize.
        output_directory:
            Base directory where visualizations will be saved.
        labels: 
            Indices of structure groups assigned to each feature.
        x1: 
            2D array of X-coordinates used for rendering each feature as a 2D map.
        x2: 
            2D array of Y-coordinates used for rendering each feature as a 2D map.
        cmap: 
            A Matplotlib colormap used to color boundaries based on labels.
        label_threshold:
            Maximum label index to be highlighted. Only features with label index 
            below this threshold are outlined for clearer color separation.
        rows_per_page:
            Number of token rows per saved figure.
            Used to manage visualization when layers contain many features.
        cols_per_page:
            Number of embedding columns per saved figure.
            Used to manage visualization when layers contain many features.
    """
    save_dir = os.path.join(output_directory, "layerwise_visualization")
    os.makedirs(save_dir)

    T, E = features.shape[2], features.shape[3]
    t_pages = math.ceil(T / rows_per_page)
    e_pages = math.ceil(E / cols_per_page)

    # tqdm now tracks layers
    for l in tqdm(range(features.shape[1]), desc="Layers"):
        for ri in range(t_pages):
            t_start = ri * rows_per_page
            t_end = min(T, (ri + 1) * rows_per_page)
            nrows = t_end - t_start

            for ci in range(e_pages):
                e_start = ci * cols_per_page
                e_end = min(E, (ci + 1) * cols_per_page)
                ncols = e_end - e_start

                fig, axs = plt.subplots(nrows, ncols, figsize=(ncols, nrows))
                axs = np.array(axs, ndmin=2).reshape(nrows, ncols)

                for ti, t in enumerate(range(t_start, t_end)):
                    for ej, e in enumerate(range(e_start, e_end)):
                        ax = axs[ti, ej]
                        Z = features[:, l, t, e].reshape(x1.shape)
                        ax.contourf(x1, x2, Z, alpha=0.7)
                        ax.set_xticks([])
                        ax.set_yticks([])
                        ax.set_xlim(0.0, 1.0)
                        ax.set_ylim(0.0, 1.0)

                        if labels[l, t, e] < label_threshold:
                            for spine in ax.spines.values():
                                spine.set_edgecolor(cmap.colors[int(labels[l, t, e])])
                                spine.set_linewidth(3.0)

                out_path = os.path.join(
                    save_dir,
                    f"layer_{l}_r{ri:03d}_c{ci:03d}.png"
                )
                plt.tight_layout()
                plt.savefig(out_path, dpi=300, bbox_inches="tight")
                plt.close(fig)


def model_visualization(
    features: np.ndarray,
    output_directory: str,
    visualization_indices: List[int],
    embedding_dim: int,
    labels: np.ndarray,
    x1: np.ndarray,
    x2: np.ndarray,
    cmap: Colormap,
    label_threshold: int = 20,
):
    """
    Args:
        features: 
            Features to visualize.
        output_directory:
            Base directory where visualizations will be saved.
        visualization_indices:
            Flat indices selecting specific units to display across layers.
        embedding_dim: 
            The embedding dimension size used to decode flat indices in visualizaion indices.
        labels: 
            Indices of structure groups assigned to each feature.
        x1: 
            2D array of X-coordinates used for rendering each feature as a 2D map.
        x2: 
            2D array of Y-coordinates used for rendering each feature as a 2D map.
        cmap: 
            A Matplotlib colormap used to color boundaries based on labels.
        label_threshold:
            Maximum label index to be highlighted. Only features with label index 
            below this threshold are outlined for clearer color separation.
    """
    L = features.shape[1]
    fig, axs = plt.subplots(L, len(visualization_indices), figsize=(len(visualization_indices), L))
    axs = np.atleast_2d(axs)

    for l in range(L):  # per layer
        for col_idx, i in enumerate(visualization_indices):
            t = i // embedding_dim
            e = i % embedding_dim
            ax = axs[l, col_idx]
            Z = features[:, l, t, e].reshape(x1.shape)
            ax.contourf(x1, x2, Z, alpha=0.7)
            ax.set_xticks([])
            ax.set_yticks([])

            if labels[l, t, e] < label_threshold:
                for spine in ax.spines.values():
                    spine.set_edgecolor(cmap.colors[int(labels[l, t, e])])
                    spine.set_linewidth(5.0)

    out_path = os.path.join(output_directory, "model_feature_structure_visualization.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)