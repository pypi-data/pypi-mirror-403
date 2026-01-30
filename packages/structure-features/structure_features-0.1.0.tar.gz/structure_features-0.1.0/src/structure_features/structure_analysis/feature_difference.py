"""
These modules analyze the differences between units, which are calculated during structure extraction, using the following functions:  
- `feature_difference`: This function normalizes the given difference matrix to the range 0–255, saves it as a grayscale image, and stores the layer-wise difference values by computing the average for each layer.  

The results are saved under the output_directory as follows:  
- `unitwise_difference.png`: grayscale image of the normalized unitwise difference matrix.  
- `layerwise_difference.csv`: CSV file containing the mean difference value per layer.

Copyright (c) 2025 Sejik Park

---
"""
import os
import numpy as np
import pandas as pd
from PIL import Image

__all__ = ['feature_difference']


def feature_difference(
    diff: np.ndarray,
    output_directory: str,
    layer_dim: int,
    ):
    """
    Args:
        diff:
            A 2D tensor/array of shape [units, units] representing pairwise 
            differences between features. Typically computed during 
            structure extraction.
        output_directory:
            Base directory where the analysis outputs will be saved. 
        layer_dim:
            The layer dimension size used to reshape the unitwise difference matrix into layerwise form.
    """
    diff = _normalize_difference(diff)
    _unitwise_difference(diff, output_directory)
    _layerwise_difference(diff, output_directory, layer_dim)


def _normalize_difference(diff) -> None:
    min_val = diff.min()
    max_val = diff.max()

    if max_val - min_val == 0:
        return np.zeros_like(diff.cpu().numpy(), dtype=np.uint8)

    image_diff = ((diff - min_val) / (max_val - min_val) * 255).cpu().numpy().astype(np.uint8)
    return image_diff


def _unitwise_difference(diff, output_directory):
    image = Image.fromarray(diff)
    output_path = os.path.join(output_directory, "unitwise_difference.png")
    image.save(output_path)


def _layerwise_difference(diff, output_directory, layer_dim) -> None:
    matrix = np.asarray(diff)
    reshaped = matrix.reshape(layer_dim, -1)  # shape: [L, N]
    compressed = reshaped.mean(axis=1)        # shape: [L]

    # Save to CSV
    out_path = os.path.join(output_directory, "layerwise_difference.csv")
    df = pd.DataFrame(compressed, columns=["mean_difference"])
    df.to_csv(out_path, index_label="layer")