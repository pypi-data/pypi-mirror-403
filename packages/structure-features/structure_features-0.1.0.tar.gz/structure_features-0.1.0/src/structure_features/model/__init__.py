"""
### Usage
The `model` can be encapsulated to extract features and structures during the forward pass.
Available encapsulation methods can be listed with `print_model_entrypoints()`.
Encapsulation is applied in the form `create_model(model, cfg)`.
If cfg is omitted, the default settings are used.

### Development
The [base structure][structure_features.model._base] specifies the additional processes required.  
By inheriting from it, you can implement a custom encapsulating class.  
Next, define it with the necessary arguments and register it as an entrypoint with [add_entrypoint][structure_features.utils._registry].  

Usage example:

```python
# Develop encapsulation
from ._base import StructureModel
class ExampleStructure(StructureModel):
    ...

# Develop calling function for registry
from structure_features.utils import add_entrypoint, _update_args
@add_entrypoint(registry="model")
def example_structure_default(model, cfg):
    default_args = dict(
        ...
    )
    updated_args = _update_args(default_args, cfg)
    return ExampleStructure(model, **updated_args)
```

Copyright (c) 2025 Sejik Park

---
"""

# Run registration
from structure_features.model.simple_structure import *
from structure_features.model.simple_structure_raw import *

from structure_features.model._factory import create_model, print_model_entrypoints

__all__ = ["create_model",
           "print_model_entrypoints"]