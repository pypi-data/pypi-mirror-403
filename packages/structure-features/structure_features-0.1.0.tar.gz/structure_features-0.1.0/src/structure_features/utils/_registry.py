"""
These modules implement registry-based code management to facilitate extensibility and reuse of existing implementations, using the following functions:  
- `add_entrypoint`: This function registers a defined class into the registry, using its function name as the entry name along with a specific registry category (such as `model` or `loss`).

Copyright (c) 2025 Sejik Park

---
"""

# _registry.py
from __future__ import annotations
from typing import Callable, Dict, Optional, Iterable, Any

__all__ = ['add_entrypoint']

# Internal: registry name -> {entrypoint name -> factory function}
_REGISTRIES: Dict[str, Dict[str, Callable[..., Any]]] = {}


# ---- Registry -----------------------------------------------------

def add_registry(name: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("registry name must be a non-empty string")

    reg = name.strip()
    if reg in _REGISTRIES:
        raise ValueError(f"registry '{reg}' already exists")

    _REGISTRIES[reg] = {}


# ---- EntryPoint API ---------------------------------------------------------

def add_entrypoint(
    fn: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    registry: str,
) -> Callable[..., Any]:
    """
    Args: 
        fn:
            The factory/function to register as an entrypoint.  
            If omitted (None), the function works in decorator mode and
            returns a decorator that will register the decorated callable.
        name:
            Explicit entrypoint name to use in the registry.  
            If None, the callable’s `__name__` is used.
        registry:
            The name of the registry namespace to register the entrypoint (e.g., `"model"`, `"loss"`).
    """
    if registry not in _REGISTRIES:
        add_registry(registry)
        
    def _register(fn_: Callable[..., Any]) -> Callable[..., Any]:
        key = name or fn_.__name__
        if not isinstance(key, str) or not key.strip():
            raise ValueError("entrypoint name must be a non-empty string")
        if key in _REGISTRIES[registry]:
            raise ValueError(f"entrypoint '{key}' already exists in registry '{registry}'")
        _REGISTRIES[registry][key] = fn_
        return fn_

    if fn is None:
        # decorator mode
        return _register
    else:
        # direct registration
        return _register(fn)


# ---- Lookup API -------------------------------------------------------------

def is_fn(name: str, *, registry: str) -> bool:
    return name in _REGISTRIES.get(registry, {})


def fn_entrypoint(name: str, *, registry: str) -> Callable[..., Any]:
    try:
        return _REGISTRIES[registry][name]
    except KeyError as e:
        raise LookupError(f"Unknown entrypoint '{name}' in registry '{registry}'") from e


# ---- Utilities --------------------------------------------------------------

def list_entrypoints(*, registry: str) -> Iterable[str]:
    return tuple(_REGISTRIES.get(registry, {}).keys())
