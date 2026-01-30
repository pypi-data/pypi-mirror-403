"""
The `ResidualAnchorIdentityLoss` computes a loss where the first unit of each structure serves as the anchor feature, and the remaining features are distilled from it,
as described in *"Structuring Hidden Features via Clustering of Unit-Level Activation Patterns" (Sejik Park, 2025).*

It includes stabilization mechanisms, such as using only the smaller value when compared with the main loss.

??? example "Examples (Usage)"
    ```python
    from structure_features import create_loss
    cfg = {
        "name": "residual_anchor_identity_default",
        "require_less_than_main": True,
        "reduction": "mean",
    }
    structure_loss = create_loss(cfg)
    loss = structure_loss(features, structures, main_loss)  # features, structures from model output
    ```

??? example "Examples (Help)"
    ```python
    from structure_features import print_loss_entrypoints
    print_loss_entrypoints(with_docs=True)  # with_docs: print inputs of init and call
    ```

Copyright (c) 2025 Sejik Park

---
"""
import torch
import torch.nn as nn
from typing import List, Tuple, Optional, Union

from structure_features.utils import add_entrypoint, _doc_from, _update_args

__all__ = ['ResidualAnchorIdentityLoss']


class ResidualAnchorIdentityLoss:
    def __init__(
        self,
        require_less_than_main: bool = True,
        reduction: str = "mean",
    ):
        """
        Args:
            require_less_than_main:
                Filter out losses which above main_loss, if provided.
            reduction:
                Reduction method for losses. One of:  
                - "mean": average the losses  
                - "sum": sum the losses  
                - "none": no reduction
        """
        self.require_less_than_main = require_less_than_main
        self.reduction = reduction
        self.mse = nn.MSELoss(reduction="mean")

    def __call__(
        self,
        features: torch.Tensor,
        structures: List[List[Tuple[int, int, int]]],
        main_loss: Optional[Union[float, torch.Tensor]] = None,
    ) -> Union[torch.Tensor, List[torch.Tensor]]:
        """
        Args:
            features:
                Activation tensor of shape [batch, layer, token, embedding]
            structures:
                List of units, where each unit is represented as 
                (layer_idx, token_idx, embedding_idx), grouped per structure.
            main_loss:
                Optional scalar for comparison gating
        """
        losses: List[torch.Tensor] = []

        # Main loss scalar (for filtering)
        main_loss_scalar: Optional[float] = None
        if main_loss is not None:
            main_loss_scalar = float(main_loss.detach().item())

        # For each aligned structure
        for structure in structures:
            first_layer, first_token, first_embedding = structure[0]
            anchor_feature = features[:, first_layer, first_token, first_embedding].detach()

            for layer, token, embedding in structure[1:]:
                identity_position_feature = features[:, layer, token, embedding]
                loss = self.mse(identity_position_feature, anchor_feature)

                if self.require_less_than_main and (main_loss_scalar is not None):
                    if loss.item() < main_loss_scalar:
                        losses.append(loss)
                else:
                    losses.append(loss)

        # Handle reduction
        if not losses:
            if self.reduction == "none":
                return []
            device = features.device
            return torch.tensor(0.0, device=device)

        if self.reduction == "none":
            return losses
        elif self.reduction == "sum":
            return torch.stack(losses).sum()
        else:  # "mean"
            return torch.stack(losses).mean()
        

# ----- entrypoint (include args) -----

@_doc_from(ResidualAnchorIdentityLoss)
@add_entrypoint(registry="loss")
def residual_anchor_identity_default(cfg):
    default_args = dict(
        require_less_than_main = True,
        reduction = 'mean'
    )
    updated_args = _update_args(default_args, cfg)
    return ResidualAnchorIdentityLoss(**updated_args)
