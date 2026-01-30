"""
The `group_rank` function performs a transformation designed to mitigate the sensitivity of feature comparisons to absolute magnitude differences and feature noise.
It applies a grouped rank transformation to each hidden unit. For a hidden unit represented by the feature vector, it sorts activation values across the batch samples and divide them into a fixed number of bins.
Each bin corresponds to a rank range, and all values within the same bin share a rank index.
This transformation standardizes activation scales while preserving the relative ordering of activations across samples.

In addition, the `accumulate_features` function is used to accumulate activations collected by hook.

Copyright (c) 2025 Sejik Park

---
"""
import torch
from torch import Tensor
from typing import List, Optional, Tuple


__all__ = ['group_rank', 'accumulate_features'] 


def group_rank(
    accumulated_features: Tensor,
    n_bins: int,
    structure_batch_size: int,
) -> Tensor:
    """
    Args:
        accumulated_features:
            Accumulated features as 4D array of shape (batch size, layer dimension, token dimension, embedding dimension).
        n_bins:
            Number of bins used for transform features.  
            Determines how many groups are formed when converting features using group rank.
        structure_batch_size:
            Number of accumulated samples required before structure extraction is performed.  
            Rounded up to align with the actual batch size.
    """
    if n_bins <= 0:
        raise ValueError("n_bins must be a positive integer.")

    device = accumulated_features.device
    B = accumulated_features.shape[0]
    dtype_out = torch.long

    # If not enough batch elements, return -1 (no grouping) with same shape
    if B < structure_batch_size:
        return accumulated_features

    # Stable sort along batch dimension for every (l, t, e) column
    _, sorted_indices = torch.sort(accumulated_features, dim=0, stable=True)

    # Ceil-balanced chunk sizes per bin
    n_per_bin = (B + n_bins - 1) // n_bins  # ceil(B / n_bins)

    # Base bin ids shaped for broadcasting: [B, 1, 1, 1] -> expand to [B, L, T, E]
    base = (
        torch.arange(n_bins, device=device)
        .repeat_interleave(n_per_bin)[:B]                 # (B,)
        .view(B, *([1] * (accumulated_features.dim() - 1)))  # (B, 1, 1, 1)
        .to(dtype_out)
    )
    grouped_indices = base.expand_as(accumulated_features)    # (B, L, T, E)

    # Scatter bin ids back to original batch order for each column
    transformed_accumulated_features = torch.empty_like(accumulated_features, dtype=dtype_out, device=device)
    transformed_accumulated_features.scatter_(0, sorted_indices, grouped_indices)

    return transformed_accumulated_features


def accumulate_features(
    accumulated_features: Tensor,
    activations: List[Optional[Tensor]],
    token_window: Tuple[int, int],
) -> Tuple[Tensor, Tensor]:
    """
    Args:
        accumulated_features:
            Previously accumulated features across multiple forward passes.  
            Shape is (batch size, layer dimension, token dimension, embedding dimension).
        activations:
            List of per-layer activation tensors collected in the current forward pass.  
            Each tensor has shape of (batch size, token dimension, embedding dimension).
        token_window:
            The sampled token index range (start, end) to be extracted from each activation tensor.
    """
    t0, t1 = token_window
    features = torch.stack([a for a in activations], dim=1)[:, :, t0:t1, :]  # [B, L, T_win, E]
    if accumulated_features is None:
        accumulated_features = features.detach()
    else:
        accumulated_features = torch.cat([accumulated_features, features.detach()], dim=0)
    return features, accumulated_features