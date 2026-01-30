"""
The `l1_threshold_graph` function extracts structures based on feature differences across units.
First, it computes pairwise L1 distances between the transformed features.
Using these distances, it constructs a binary adjacency matrix with a difference threshold.
The threshold is defined as a ratio relative to the batch size, which corresponds to allowing at most an average group-rank difference of 1 per sample.
From the adjacency matrix, it builds an undirected graph and identifies connected components, which are then used as the structures.

Copyright (c) 2025 Sejik Park

---
"""
from typing import List
import scipy.sparse
import scipy.sparse.csgraph

import numpy as np
import torch


__all__ = ['l1_threshold_graph'] 


def l1_threshold_graph(
    features: torch.Tensor,
    scaling_threshold: float,
) -> List[List[int]]:
    """
    Args:
        features:
            Features as 4D array of shape (batch size, layer dimension, token dimension, embedding dimension).
        scaling_threshold:
            The effective distance threshold is computed as: threshold = batch_size * scaling_threshold.
            Two units are in the same structure if their L1 distance is smaller than this threshold.
    """
    if not isinstance(features, torch.Tensor):
        raise TypeError("features must be a torch.Tensor")
    if features.dim() < 1:
        raise ValueError("features must have batch dimension at dim 0")
    if scaling_threshold < 0:
        raise ValueError("scaling_threshold must be non-negative")

    B = features.shape[0]
    if B == 0:
        return []

    # Flatten per-sample: [B, -1]
    flat = features.reshape(B, -1).T.float()

    # Pairwise L1 distances across batch items: [units, units]
    # Keep computation on the same device, then move to CPU for graph ops.
    with torch.no_grad():
        dist = torch.cdist(flat, flat, p=1)

    # Threshold and build adjacency (boolean) on CPU
    threshold = B * float(scaling_threshold)
    adjacency = (dist < threshold).to("cpu").numpy()  # shape [units, units], dtype=bool

    # Ensure symmetry (numerical safety) and self-connectivity
    np.fill_diagonal(adjacency, True)
    if not np.all(adjacency == adjacency.T):
        adjacency = np.logical_or(adjacency, adjacency.T)

    sparse_adj = scipy.sparse.csr_matrix(adjacency)
    num_stuctures, labels = scipy.sparse.csgraph.connected_components(
        sparse_adj, directed=False
    )

    stuctures: List[List[int]] = [
        np.where(labels == i)[0].tolist() for i in range(num_stuctures)
    ]

    return stuctures, dist, labels