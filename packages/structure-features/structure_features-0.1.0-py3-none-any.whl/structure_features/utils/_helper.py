"""
These modules implement helper functions that define conventions for how code should utilize entrypoints, using the following function:  
- `_doc_from`: This function allows the automatic extraction of argument descriptions from the `__init__` and `__call__` methods of a class through a decorator for entrypoints.  
- `_update_args`: This function manages arguments by handling the relationship between default arguments and updated arguments when defining entrypoints.  

Copyright (c) 2025 Sejik Park

---
"""
import inspect
import textwrap

__all__ = ['_doc_from', '_update_args']


def _doc_from(cls: type):
    """
    Args:
        cls:
            A class object whose `__init__` and `__call__` method docstrings
            are extracted and attached to the decorated entrypoint function.
    """
    def deco(f):
        f.__doc__ = _build_doc_from_class(cls) or ""
        return f
    return deco


def _update_args(default_args: dict, change_args: dict | None) -> dict:
    """
    Args:
        default_args:
            A dictionary containing the baseline/default arguments for the entrypoint.
        change_args:
            A dictionary of updated arguments that override or extend the defaults.
    """
    if change_args is None:
        return dict(default_args)  # return a copy

    updated = dict(default_args)  # copy defaults
    updated.update(change_args)   # apply overrides
    return updated


def _build_doc_from_class(cls) -> str:
    parts = []

    # __init__
    init = getattr(cls, "__init__", None)
    if init and callable(init):
        try:
            init_sig = str(inspect.signature(init))
        except (ValueError, TypeError):
            init_sig = "(...)"
        init_doc = textwrap.dedent(inspect.getdoc(init) or "").rstrip("\n")
        if init_doc:
            parts.append(f"\n[__init__]{init_sig}\n{textwrap.indent(init_doc, '    ')}")

    # __call__
    call = getattr(cls, "__call__", None)
    if call and callable(call):
        try:
            call_sig = str(inspect.signature(call))
        except (ValueError, TypeError):
            call_sig = "(...)"
        call_doc = textwrap.dedent(inspect.getdoc(call) or "").rstrip("\n")
        if call_doc:
            parts.append(f"\n[__call__]{call_sig}\n{textwrap.indent(call_doc, '    ')}")

    return "".join(parts).strip()