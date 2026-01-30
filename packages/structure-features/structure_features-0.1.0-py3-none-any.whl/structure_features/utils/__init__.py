"""
In utils, this module provides core classes and functions that enable a registry-based approach 
to utilizing loss functions and model encapsulation classes, with the following functions: 
[add_entrypoint][structure_features.utils._registry], [_print_entrypoints][structure_features.utils._factory], 
and [_update_args][structure_features.utils._helper].
'_doc_from', 
'_create_via_registry',

Copyright (c) 2025 Sejik Park

---
"""

from structure_features.utils._registry import add_entrypoint
from structure_features.utils._factory import _create_via_registry, _print_entrypoints
from structure_features.utils._helper import _doc_from, _update_args