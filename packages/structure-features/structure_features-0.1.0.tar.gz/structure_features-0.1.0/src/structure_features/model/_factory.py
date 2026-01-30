"""
This module provides a simple factory for creating models using a registry-based approach.

Copyright (c) 2025 Sejik Park

---
"""

from typing import Any, Dict, Tuple

from structure_features.utils import _create_via_registry, _print_entrypoints

__all__ = ['create_model', 'print_model_entrypoints']


# ---- create ---------------------------------------------------

def create_model(model: Any, cfg: Dict[str, Any] = None) -> Tuple[Any, Any]:
    if cfg is None:
        cfg = {}
    cfg.setdefault('name', 'simple_structure_default')
    
    return _create_via_registry(model=model, cfg=cfg, expects_model=True, registry='model')

# ---- print ---------------------------------------------------

def print_model_entrypoints(with_docs:bool = False) -> None:
    _print_entrypoints("model", with_docs=with_docs)