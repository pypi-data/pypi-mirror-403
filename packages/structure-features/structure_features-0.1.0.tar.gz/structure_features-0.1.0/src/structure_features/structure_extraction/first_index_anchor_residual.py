"""
The `first_index_anchor_residual` function extracts detailed structures related to residual connections.
To obtain these structures when the cluster includes more than two layers, the unit at the first index of each structure is designated as the representative anchor unit.
It then retrieves the residual connection positions across the layers within the cluster.

Copyright (c) 2025 Sejik Park

---
"""
from typing import List, Tuple

__all__ = ["first_index_anchor_residual"]


def first_index_anchor_residual(
    structures: List[List[int]],
    layer_dim: int = 3,
    token_dim: int = 3,
    embedding_dim: int = 256,
) -> List[List[Tuple[int, int, int]]]:
    """
    Args:
        structures:
            A list of structures, where each structure is represented as a list of flat 
            indices. Each flat index corresponds to a unit in the feature space, which can 
            be decoded into (layer, token, embedding) coordinates.
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
    aligned_node_groups: List[List[Tuple[int, int, int]]] = []

    for structure in structures:
        layer_indices = {node // per_layer for node in structure}
        if len(layer_indices) <= 1:
            continue  # skip structures in a single layer

        min_layer = min(layer_indices)
        max_layer = max(layer_indices)

        first_node = structure[0]
        relative_index = first_node - min_layer * per_layer
        token_index = relative_index // embedding_dim
        embedding_index = relative_index % embedding_dim

        aligned_nodes = [
            (layer, token_index, embedding_index)
            for layer in range(min_layer, max_layer + 1)
        ]
        aligned_node_groups.append(aligned_nodes)

    return aligned_node_groups