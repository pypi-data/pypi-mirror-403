"""
The `raw` function returns accumulated features without applying any transformation or normalization across data samples.

The `raw' function is used together with the `accumulate_features` function in `group_rank` to accumulate activations collected by hook.

Copyright (c) 2025 Sejik Park

---
"""
import torch
from torch import Tensor
from typing import List, Optional, Tuple


__all__ = ['raw'] 


def raw(
    accumulated_features: Tensor,
    normalization: bool,
    structure_batch_size: int,
) -> Tensor:
    """
    Args:
        accumulated_features:
            Accumulated features as 4D array of shape (batch size, layer dimension, token dimension, embedding dimension).
        normalization:
            Apply batch-wise normalization if True.
        structure_batch_size:
            Number of accumulated samples required before structure extraction is performed.  
            Rounded up to align with the actual batch size.
    """
    B = accumulated_features.shape[0]

    # If not enough batch elements, return -1 (no grouping) with same shape
    if B < structure_batch_size:
        return accumulated_features

    # If normalization is disabled, return raw features
    if not normalization:
        return accumulated_features
    
    # Normalize features across batch dimension (dim=0).
    # Each (L, T, E) position is normalized independently.
    mean = accumulated_features.mean(dim=0, keepdim=True)
    std = accumulated_features.std(dim=0, keepdim=True, unbiased=False)

    eps = torch.finfo(accumulated_features.dtype).eps
    normalized_features = (accumulated_features - mean) / (std + eps)

    return normalized_features