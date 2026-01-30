"""
This library provides functions related to structure features.

Details can be accessed through [create_model][structure_features.model] and [create_loss][structure_features.loss].  
Each function is managed through the registry system using [add_entrypoint][structure_features.utils.add_entrypoint].

Copyright (c) 2025 Sejik Park

---
"""

from structure_features.utils import add_entrypoint
from structure_features.model import create_model, print_model_entrypoints
from structure_features.loss import create_loss, print_loss_entrypoints

__all__ = ["add_entrypoint",
           "create_model", "print_model_entrypoints",
           "create_loss", "print_loss_entrypoints"]