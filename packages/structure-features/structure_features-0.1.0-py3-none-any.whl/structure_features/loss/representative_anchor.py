"""
<span style="color:red">Not implemented (work in progress)</span>

The `RepresentativeAnchorLoss` computes an anchor-wise distillation loss where, within each node cluster, the first node acts as the anchor feature and the remaining nodes are distilled from it.

It also includes stabilization mechanisms, e.g. keeping only terms that are smaller than a provided main loss, and supports standard PyTorch-style reductions.

Copyright (c) 2025 Sejik Park

---
"""
from typing import List, Optional, Sequence, Union

import torch
import torch.nn as nn

from structure_features.utils import add_entrypoint, _doc_from, _update_args


__all__ = [""] # ["RepresentativeAnchorLoss"]


class RepresentativeAnchorLoss:
    def __init__(
        self,
        require_less_than_main: bool = True,
        reduction: str = "mean",
    ):
        """
        Args:
            require_less_than_main: ??
                If True and `main_loss` is provided, keep only
                individual losses that are strictly smaller than the main loss scalar.
            reduction: ??
                One of {"mean", "sum", "none"} applied across all kept terms.
        """
        if reduction not in {"mean", "sum", "none"}:
            raise ValueError(f"Invalid reduction: {reduction}")
        self.require_less_than_main = require_less_than_main
        self.reduction = reduction
        self.mse = nn.MSELoss(reduction="mean")

    def __call__(
        self,
        model_features_list: Sequence[torch.Tensor],
        clusters: Sequence[Sequence[Sequence[int]]],
        main_loss: Optional[Union[float, torch.Tensor]] = None,
    ) -> Union[torch.Tensor, List[torch.Tensor]]:
        """
        Args:
            model_features_list: ??
                Sequence of feature tensors. Each tensor is expected to
                be shaped like [B, N, ...] where N indexes nodes; the loss uses the
                second dimension for node selection (i.e., advanced indexing with node ids).
            clusters: ??
                For each feature tensor, a sequence of clusters; each cluster is
                a sequence of integer node indices (first index is the anchor).
            main_loss: ??
                Optional scalar (float or 0-dim tensor). If provided and
                `require_less_than_main=True`, per-term losses greater-or-equal to this
                value are discarded.
        """
        main_loss_scalar: Optional[float] = None
        if main_loss is not None:
            main_loss_scalar = float(torch.as_tensor(main_loss).detach().item())

        kept_losses: List[torch.Tensor] = []

        for features, clusters_for_feat in zip(model_features_list, clusters):
            if features.ndim < 2:
                raise ValueError(
                    f"Expected features with at least 2 dims [B, N, ...], got shape {tuple(features.shape)}"
                )

            for nodes in clusters_for_feat:
                if nodes is None or len(nodes) < 2:
                    continue

                anchor_idx = nodes[0]
                other_idxs = nodes[1:]

                anchor_feat = features[:, anchor_idx].detach()
                other_feat = features[:, other_idxs]
                other_feat_mean = other_feat.mean(dim=1)

                loss_val = self.mse(anchor_feat, other_feat_mean)

                if self.require_less_than_main and (main_loss_scalar is not None):
                    if loss_val.item() < main_loss_scalar:
                        kept_losses.append(loss_val)
                else:
                    kept_losses.append(loss_val)

        if not kept_losses:
            if self.reduction == "none":
                return []
            device = (
                model_features_list[0].device
                if len(model_features_list) > 0
                else torch.device("cpu")
            )
            return torch.tensor(0.0, device=device)

        if self.reduction == "none":
            return kept_losses
        stacked = torch.stack(kept_losses)
        if self.reduction == "sum":
            return stacked.sum()
        return stacked.mean()


# ----- entrypoint (include args) -----

# TODO
@_doc_from(RepresentativeAnchorLoss)
@add_entrypoint(registry="loss")
def representative_anchor_default(cfg):
    default_args = dict(
        require_less_than_main=True,
        reduction="mean",
    )
    updated_args = _update_args(default_args, cfg)
    return RepresentativeAnchorLoss(**updated_args)
