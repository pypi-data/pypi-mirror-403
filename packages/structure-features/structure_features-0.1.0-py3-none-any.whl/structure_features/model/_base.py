"""
The `StructureModel` serves as the base architecture, encapsulating a backbone model designed to provide structure-related processing capabilities.
It extends the standard forward pass with four main pipelines, along with their related attributes:  
- [submodule_sampling][structure_features.submodule_sampling]: self.activations, self.handles, self.layer_window, self.token_window  
- [transform_features][structure_features.transform_features]: self.features, self.accumulated_features  
- [structure_extraction][structure_features.structure_extraction]: self.structures  
- [structure_analysis][structure_features.structure_analysis]: self.features, self.structures  
For implementation convenience, get_submodule_information is included to enable automatic hyperparameter settings.

Copyright (c) 2025 Sejik Park

---
"""
import torch.nn as nn


__all__ = ['StructureModel']


class StructureModel(nn.Module):
    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model

        # feature stores
        self.activations = {}
        self.handles = []
        self.layer_window, self.token_window = None, None
        self.features = None
        self.accumulated_features = None
        self.structures = {}

    def get_submodule_information(self, *args, **kwargs):
        pass

    def submodule_sampling(self):
        pass
    
    def transform_feature(self):
        pass
    
    def structure_extraction(self):
        pass
    
    def structure_analysis(self):
        pass

    def forward(self, *args, **kwargs):
        self.get_submodule_information(*args, **kwargs)
        self.submodule_sampling()
        output = self.model(*args, **kwargs)
        self.transform_feature()
        self.structure_extraction()

        return output, self.features, self.structures