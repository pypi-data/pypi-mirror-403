"""
### Usage
Defines a structure `loss` based on extracted features and structures.
To list the available loss methods, use `print_loss_entrypoints()`.
A loss function can be created with `create_loss(cfg)`.
If `cfg` is omitted, the default settings are applied.

### Development
Each loss should be implemented as a class so that it can be called directly.  
Then, define a factory function with the required arguments and register it as an entrypoint using `add_entrypoint`.

??? example "Examples (Usage)"
    ```python
    from structure_features import create_loss
    cfg = {
        "name": entrypoint_name,
        ... # other cfg in loss
    }
    structure_loss = create_loss(cfg)
    loss = structure_loss(features, structures)  # features, structures from model output
    ```

??? example "Examples (Help)"
    ```python
    from structure_features import print_loss_entrypoints
    print_loss_entrypoints(with_docs=True)  # with_docs: print inputs of init and call
    ``` 

??? example "Examples (Development)"
    ```python
    # TODO: implement the omitted parts (...)
    # Develop calling function for registry
    from structure_features.utils import add_entrypoint, _doc_from, _update_args
    class ExampleLoss:
        def __init__(
            self,
            ...
        ):
            ...
        def __call__(
            self, 
            features: torch.Tensor,
            structures: List[List[Tuple[int, int, int]]],
            ...
        )
            ...

    @_doc_from(ExampleLoss)
    @add_entrypoint(registry="loss")
    def example_structure_default(cfg):
        default_args = dict(
            ...
        )
        updated_args = _update_args(default_args, cfg)
        return ExampleLoss(**updated_args)
    ```

Copyright (c) 2025 Sejik Park

---
"""
# from structure_features.loss.representative_anchor import *
from structure_features.loss.residual_anchor_identity import *

from structure_features.loss._factory import create_loss, print_loss_entrypoints

__all__ = ["create_loss",
           "print_loss_entrypoints"]