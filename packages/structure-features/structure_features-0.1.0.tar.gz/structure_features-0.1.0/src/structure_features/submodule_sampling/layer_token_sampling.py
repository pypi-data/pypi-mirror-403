"""
The `layer_token_sampling` function samples selected dimensions of layers and tokens from those matching the given patterns for structure-related processes.  

In addition, the `layer_token_sampling_related_information` function is used for automatic hyperparameter detection.  

Copyright (c) 2025 Sejik Park

---
"""
import re
import numpy as np
from collections import defaultdict
from typing import Callable, List, Optional, Tuple

import torch
from torch import Tensor

__all__ = ["layer_token_sampling", "layer_token_sampling_related_information"]


def layer_token_sampling(
    model: torch.nn.Module,
    layer_dim: int,
    token_dim: int,
    patterns: str = r"", # blocks\.\d+"
    sampling_layer_dim: int = 3,
    sampling_token_dim: int = 3,
    fixed_sampling: bool = False,
    rng: Optional[np.random.Generator] = np.random.default_rng(42),
) -> Tuple[
    List[Optional[Tensor]],               # activations collected as a list in layer order
    Tuple[int, int],                      # layer_window (start, end)
    Tuple[int, int],                      # token_window (start, end)
    List[torch.utils.hooks.RemovableHandle],
]:
    """
    Args:
        model:
            Target model to be wrapped.
        layer_dim:
            Total number of available layers.
        token_dim:
            Total number of tokens.
        patterns:
            Regular expression used for submodule sampling.
        sampling_layer_dim:
            Layer dimension used for submodule sampling.  
            Determines how many consecutive layers are periodically sampled within the matched submodules.
        sampling_token_dim:
            Token dimension used for submodule sampling.  
            Determines how many consecutive tokens are periodically sampled within the matched submodules.
        fixed_sampling:
            Deterministic sampling option that samples dimensions starting from the first index.
        rng:
            Random number generator used for sampling windows.
            Defaults to a fixed seed.
    """

    if not (1 <= sampling_layer_dim <= layer_dim):
        raise ValueError(f"sampling_layer_dim must be in [1, {layer_dim}]")
    if not (1 <= sampling_token_dim <= token_dim):
        raise ValueError(f"sampling_token_dim must be in [1, {token_dim}]")

    # 1) Decide sampling windows first.
    max_layer_start = layer_dim - sampling_layer_dim
    max_token_start = token_dim - sampling_token_dim

    l0 = 0 if fixed_sampling else int(rng.integers(0, max_layer_start + 1))
    t0 = 0 if fixed_sampling else int(rng.integers(0, max_token_start + 1))
    layer_window: Tuple[int, int] = (l0, l0 + sampling_layer_dim)
    token_window: Tuple[int, int] = (t0, t0 + sampling_token_dim)

    # 2) Collect only modules that match the pattern AND fall inside the sampled layer window.
    name_regex = re.compile(patterns)
    digit_regex = re.compile(r"\d+")

    matched: List[Tuple[int, str, torch.nn.Module]] = []
    for name, module in model.named_modules():
        if name_regex.fullmatch(name):
            m = digit_regex.search(name)
            if not m:
                continue
            idx = int(m.group(0))
            if layer_window[0] <= idx < layer_window[1]:
                matched.append((idx, name, module))

    if not matched:
        raise ValueError(
            f"No modules within sampled layer_window {layer_window} matched pattern: {patterns}"
        )

    # 3) Sort by numeric layer index to define the collection order.
    matched.sort(key=lambda x: x[0])

    # 4) Prepare activations list (None placeholders) in the sorted order.
    sampled_L = len(matched)
    activations: List[Optional[Tensor]] = [None] * sampled_L

    # 5) Register hooks only on sampled layers, mapping each to its list slot.
    handles: List[torch.utils.hooks.RemovableHandle] = []
    for slot, (_idx, name, module) in enumerate(matched):
        # Optional: keep a readable name on the module for debugging.
        setattr(module, "_name", name)
        h = module.register_forward_hook(_make_indexed_hook(activations, slot))
        handles.append(h)

    return activations, handles, layer_window, token_window


def layer_token_sampling_related_information(
    model: torch.nn.Module,
    patterns: str = r"", # r"blocks\.\d+",
) -> Tuple[List[Optional[Tensor]], List[torch.utils.hooks.RemovableHandle]]:
    """
    Args:
        model:
            Target model to be wrapped.
        patterns:
            Regular expression used for submodule sampling.
    """
    if patterns == "":
        patterns = _best_indexed_pattern_from_named_modules(model)
    name_regex = re.compile(patterns)
    digit_regex = re.compile(r"\d+")

    matched: List[Tuple[int, str, torch.nn.Module]] = []
    for name, module in model.named_modules():
        if name_regex.fullmatch(name):
            m = digit_regex.search(name)
            if not m:
                continue
            idx = int(m.group(0))
            matched.append((idx, name, module))

    if not matched:
        raise ValueError(f"No modules matched pattern: {patterns}")

    matched.sort(key=lambda x: x[0])

    activations: List[Optional[Tensor]] = [None] * len(matched)
    handles: List[torch.utils.hooks.RemovableHandle] = []
    for slot, (_idx, name, module) in enumerate(matched):
        setattr(module, "_name", name)
        h = module.register_forward_hook(_make_indexed_hook(activations, slot))
        handles.append(h)

    return activations, handles, patterns


def _make_indexed_hook(collector: List[Optional[torch.Tensor]], slot: int) -> Callable:
    def hook_fn(module, _input, output):
        # Case 1: plain Tensor
        if isinstance(output, torch.Tensor):
            if output.dim() < 3:
                raise ValueError(
                    f"Expected at least 3D tensor [B, T, E], got shape: {tuple(output.shape)}"
                )
            collector[slot] = output

        # Case 2: list/tuple with a single element
        elif isinstance(output, (list, tuple)) and len(output) == 1:
            tensor = output[0]
            if not isinstance(tensor, torch.Tensor):
                raise TypeError(f"Expected Tensor inside list/tuple, got {type(tensor)}")
            if tensor.dim() < 3:
                raise ValueError(
                    f"Expected at least 3D tensor [B, T, E], got shape: {tuple(tensor.shape)}"
                )
            collector[slot] = tensor

        # Case 3: unsupported type
        else:
            raise TypeError(f"Expected tensor output from hooked module, got {type(output)}")

    return hook_fn


def _best_indexed_pattern_from_named_modules(model):
        pattern_to_indices = defaultdict(list)

        for name, _ in model.named_modules():
            if not name:  # skip root (empty string)
                continue
            tokens = name.split(".")

            # look for numeric tokens in the path
            for i, tok in enumerate(tokens):
                m = re.search(r"(\d+)", tok)
                if not m:
                    continue

                # numeric index value
                idx_val = int(m.group(1))

                # generalize this token: replace digits with (\d+)
                generalized_tok = re.sub(r"\d+", r"(\\d+)", tok)

                # pattern up to this token
                generalized_prefix = tokens[:i] + [generalized_tok]
                pattern = ".".join(generalized_prefix)

                pattern_to_indices[pattern].append(idx_val)

        if not pattern_to_indices:
            return None

        # compute max index and frequency for each pattern
        scored = []
        for pat, indices in pattern_to_indices.items():
            max_idx = max(indices)
            cnt = len(indices)
            scored.append((pat, max_idx, cnt))

        # sort by: max index (desc), count (desc), pattern length (asc)
        scored.sort(key=lambda x: (-x[1], -x[2], len(x[0])))

        print("Automatic pattern selection:")
        for pat, max_idx, cnt in scored:
            print(f"  {pat:40} -> max index {max_idx}, count {cnt}")

        print(f"Selected pattern: {scored[0][0]}")
        return scored[0][0]