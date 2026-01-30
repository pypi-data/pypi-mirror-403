"""
These modules analyze non-contiguous layers using the following function:  
- `noncontiguous_structure`: Counts the number of structures that span non-contiguous layers.  

The results are saved under the output_directory as follows:  
- `noncontiguous_structure_indices.csv`: CSV file containing the indices of 
  structures that span non-contiguous layers.

Copyright (c) 2025 Sejik Park

---
"""
import os
import csv
from typing import List

__all__ = ['noncontiguous_structure']


def noncontiguous_structure(
    structures: List[List[int]],
    output_directory: str,
    layer_dim: int,
    token_dim: int,
    embedding_dim: int
) -> List[int]:
    """
    Args:
        structures:
            A list of structures, where each structure is represented as a list of flat 
            indices. Each flat index corresponds to a unit in the feature space, which can 
            be decoded into (layer, token, embedding) coordinates.
        output_directory:
            Base directory where the analysis outputs will be saved. 
        layer_dim:
            The layer dimension size used to decode flat indices in structures.
        token_dim:
            The token dimension size used to decode flat indices in structures.
        embedding_dim:
            The embedding dimension size used to decode flat indices in structures.
    """
    if token_dim <= 0 or embedding_dim <= 0 or layer_dim <= 0:
        raise ValueError("All dims must be positive integers.")

    per_layer = token_dim * embedding_dim
    noncontiguous_structure_idxs: List[int] = []

    for structure_idx, structure in enumerate(structures):
        layer_indices = {node // per_layer for node in structure}
        if len(layer_indices) <= 1:
            continue  # single-layer structures are trivially contiguous

        min_layer = min(layer_indices)
        max_layer = max(layer_indices)

        if len(layer_indices) != (max_layer - min_layer + 1): 
            noncontiguous_structure_idxs.append(structure_idx)

    # Save result as CSV
    out_path = os.path.join(output_directory, "noncontiguous_structure_indices.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"structure_index (n: {len(noncontiguous_structure_idxs)})"])
        for idx in noncontiguous_structure_idxs:
            writer.writerow([idx])