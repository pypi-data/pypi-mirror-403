"""
These modules display which entrypoints exist, using the following functions:  
- `_print_entrypoints`: It shows what kinds of entrypoints exist in the registry and how to use them. Entrypoints are managed by grouping them according to the registry name (e.g., `model`, `loss`) that was used when registering them.

Copyright (c) 2025 Sejik Park

---
"""
import inspect
import textwrap
from typing import Any, Dict, Tuple

from structure_features.utils._registry import is_fn, fn_entrypoint, list_entrypoints
from structure_features.utils._registry import list_entrypoints as list_eps, fn_entrypoint as get_ep

__all__ = ['_create_via_registry', '_print_entrypoints']


def _create_via_registry(
    model: Any = None, cfg: Dict[str, Any] = None, expects_model: bool = False, registry: str = None
) -> Tuple[Any, Any]:
    """
    Args:
        model:
            Target model to be wrapped, passed only if the entrypoint
            requires a model. Used when `expects_model=True`.
        cfg:
            Configuration dictionary passed to the entrypoint.
            `"name"` key that specifies which entrypoint to use. 
        expects_model:
            Whether the entrypoint requires a `model` argument.  
            If True, the entrypoint is called as `create_fn(model=model, cfg=cfg)`.  
            If False, it is called as `create_fn(cfg=cfg)`.
        registry:
            The name of the registry namespace to search in (e.g., `"model"`, `"loss"`).
    """
    name = cfg.pop("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("cfg['name'] must be a non-empty string.")

    if not is_fn(name, registry=registry):
        available = ", ".join(list_entrypoints(registry=registry)) or "<empty>"
        raise LookupError(
            f"Unknown entrypoint {name!r} in registry {registry!r}. "
            f"Available: {available}"
        )

    create_fn = fn_entrypoint(name, registry=registry)
    if not callable(create_fn):
        raise TypeError(f"Entrypoint {name!r} in {registry!r} is not callable: {create_fn!r}")

    try:
        if expects_model:
            result = create_fn(model=model, cfg=cfg)
            return result
        else:
            obj = create_fn(cfg=cfg)
            return obj
    except TypeError as e:
        # Common pitfall: wrong factory signature
        raise TypeError(
            f"Error calling factory {name!r} in {registry!r}: {e}"
        ) from e


def _print_entrypoints(registry: str, *, with_docs: bool = False) -> None:
    """
    Args:
        registry:
            The name of the registry namespace to search in (e.g., `"model"`, `"loss"`).
        with_docs:
            If True, print the entrypoint’s docstring (such as from a class
            `__init__` or `__call__`) indented beneath its name.  
            If False, only print the entrypoint names.
    """
    try:
        names = tuple(list_eps(registry=registry))
    except Exception as e:
        print(f"[entrypoints:{registry}] error: {e}")
        return

    if not names:
        print(f"[entrypoints:{registry}] <empty>")
        return

    print(f"[entrypoints:{registry}]")
    for n in sorted(names):
        if not with_docs:
            print(f"  - {n}")
            continue

        try:
            doc = inspect.getdoc(get_ep(n, registry=registry)) or ""
        except Exception:
            print(f"  - {n} (<doc unavailable>)")
            continue

        # 1) print the name by itself
        print(f"  - {n}")

        # 2) indent the whole doc block under the name
        if doc:
            indented = textwrap.indent(doc.strip("\n"), "    ", predicate=lambda _l: True)
            print(indented)
        else:
            print("    <no docs>")

        # 3) spacer between entries (optional)
        print()
