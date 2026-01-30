"""
These modules perform frequency-related analysis of structures using the following functions:  
- `structure_related_frequency`: Executes both structure_size_frequency and n_structure_per_layer.  
- `structure_size_frequency`: Plots a histogram of structure sizes.  
- `n_structure_per_layer`: Counts the number of unique structure labels per layer.  

The results are saved under the output_directory as follows:  
- `structure_size_frequency_histogram.png`: histogram plot showing the distribution of structure sizes.  
- `n_structures_per_layer.csv`: CSV file containing the number of unique structure labels per layer.  


Copyright (c) 2025 Sejik Park

---
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from typing import List, Union, Tuple

__all__ = ['structure_related_frequency', 'structure_size_frequency', 'n_structure_per_layer']


def structure_related_frequency(
    structures: List[List[int]],
    output_directory: Union[str, Path],
    labels: np.ndarray
) -> None:
    """
    Args:
        structures: 
            A list of structures, where each structure is represented as a list of flattened 
            unit indices.
        output_directory:
            Base directory where the analysis outputs will be saved. 
        labels: 
            Indices of structure groups assigned to each feature, as 3D array of shape
            (layer dimension, token dimension, embedding dimension).
    """
    structure_size_frequency(structures, output_directory)
    n_structure_per_layer(labels, output_directory)


def structure_size_frequency(
    structures: List[List[int]],
    output_directory: Union[str, Path],
    bins: Tuple[int, int, int] = (0, 200, 10),
    ylim: int = 10**4
) -> None:
    """
    Args:
        structures:
            A list of structures, where each structure is represented as a list of flatted 
            unit indices.
        output_directory:
            Base directory where the analysis outputs will be saved. 
        bins:
            (start, end, step) for histogram bin edges.
        ylim:
            Upper limit of the y-axis.
    """
    sizes = [len(structure) for structure in structures]
    bin_range = list(range(*bins))

    fig, ax = plt.subplots()
    ax.hist(sizes, bins=bin_range, edgecolor='black')
    ax.set_yscale('log')
    ax.set_ylim(1, ylim)
    ax.set_xlabel("Structure Size")
    ax.set_ylabel("Frequency (log)")
    ax.set_title(f"Structure Size Frequency (max size: {max(sizes)})")

    png_path = os.path.join(output_directory, "structure_size_frequency_histogram.png")
    plt.tight_layout()
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.close(fig)


def n_structure_per_layer(
    labels: np.ndarray,
    output_directory: Union[str, Path]
) -> None:
    """
    Args:
        labels:
            Indices of structure groups assigned to each feature
        output_directory:
            Base directory where the analysis outputs will be saved. 
    """
    layer_dim = labels.shape[0]
    results = []

    for layer_idx in range(layer_dim):
        layer_labels = labels[layer_idx]  # shape: [token_dim, embedding_dim]
        unique_labels = np.unique(layer_labels)
        n_structures = len(unique_labels)
        results.append((layer_idx, n_structures))

    df = pd.DataFrame(results, columns=["layer", "n_structures"])

    Path(output_directory).mkdir(parents=True, exist_ok=True)
    csv_path = Path(output_directory) / "n_structures_per_layer.csv"
    df.to_csv(csv_path, index=False)