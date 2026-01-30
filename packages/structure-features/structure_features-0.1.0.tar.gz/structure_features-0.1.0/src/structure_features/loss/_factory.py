"""
This module provides a simple factory for creating loss using a registry-based approach.
    
Copyright (c) 2025 Sejik Park

---
"""

from typing import Any, Dict, Tuple

from structure_features.utils import _create_via_registry, _print_entrypoints

__all__ = ['create_loss', 'print_loss_entrypoints']


# ---- create ---------------------------------------------------

def create_loss(cfg: Dict[str, Any] = None) -> Tuple[Any, Any]:
    if cfg is None:
        cfg = {}
    cfg.setdefault('name', 'residual_anchor_identity_default')

    return _create_via_registry(cfg=cfg, registry='loss')


# ---- print ---------------------------------------------------

def print_loss_entrypoints(with_docs:bool = False) -> None:
    _print_entrypoints("loss", with_docs=with_docs)