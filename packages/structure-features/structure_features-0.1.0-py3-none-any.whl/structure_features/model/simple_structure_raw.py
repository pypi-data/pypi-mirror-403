"""
The `SimpleStructureRaw` encapsulates the model to extract features and structures during the forward pass, following the approach described in *"Structuring Hidden Features via Clustering of Unit-Level Activation Patterns" (Sejik Park, 2025).*
Unlike the standard SimpleStructure, this variant uses raw activation inputs instead of the group_rank transformation.
The [four main pipelines][structure_features.model._base] are organized as follows:  
- **submodule_sampling**: [layer_token_sampling][structure_features.submodule_sampling.layer_token_sampling]  
- **transform_feature**: [raw][structure_features.transform_features.raw]  
- **structure_extraction**: [l1_threshold_graph][structure_features.structure_extraction.l1_threshold_graph], [first_index_anchor_residual][structure_features.structure_extraction.first_index_anchor_residual]  
- **structure_analysis**: [feature_cluster_visualization][structure_features.structure_analysis.feature_cluster_visualization], [feature_difference][structure_features.structure_analysis.feature_difference], [structure_related_frequency][structure_features.structure_analysis.structure_related_frequency], [noncontiguous_structure][structure_features.structure_analysis.noncontiguous_structure]   

For implementation convenience, an additional pipeline is provided for automatic hyperparameter detection:  
- **get_submodule_information**: [layer_token_sampling][structure_features.submodule_sampling.layer_token_sampling]  

??? example "Examples (Usage)"
    ```python
    from structure_features import create_model

    cfg = {
        "name": "simple_structure_default",
        "patterns": r"blocks\\.\\d+",, 
        "sampling_layer_dim": 3,
        "sampling_token_dim": 3,
        "n_bins": 100, 
        "structure_batch_size": 15360,
        "scaling_threshold": 1.0,
        "output_directory": "output/",
        "visualization_indexes": [0, 1, 2, 3, 4, 5, 6],
    }
    
    structure_model = create_model(model, cfg)
    y, features, structures = structure_model(x)  # original: y = model(x)

    # analysis
    structure_model.structure_analysis()
    ```

??? example "Examples (Help)"
    ```python
    from structure_features import print_model_entrypoints

    print_model_entrypoints(with_docs=True)  # with_docs: print inputs of init
    ```

Copyright (c) 2025 Sejik Park

---
"""
import os
import torch.nn as nn

from structure_features.submodule_sampling import layer_token_sampling_related_information, layer_token_sampling
from structure_features.transform_features import accumulate_features, raw
from structure_features.structure_extraction import l1_threshold_graph, first_index_anchor_residual
from structure_features.structure_analysis import feature_cluster_visualization, feature_difference, structure_related_frequency, noncontiguous_structure

from ._base import StructureModel
from structure_features.utils import add_entrypoint, _doc_from, _update_args

__all__ = ['SimpleStructureRaw']


class SimpleStructureRaw(StructureModel):
    def __init__(self, model: nn.Module, 
            patterns: str = r"", # r"blocks\.\d+", 
            sampling_layer_dim: int = 3,
            sampling_token_dim: int = 3,
            normalization: bool = False,
            structure_batch_size: int = 15360,
            scaling_threshold: float = 1.0,
            output_directory: str = 'output/',
            visualization_indexes: list[int] = [0,1,2,3,4,5,6],
            mkdir: bool = False,
        ):

        """
        Args:
            model:
                Target model to be wrapped.
            patterns:
                Regular expression used for submodule sampling.  
                If left empty, repeated structural patterns are automatically detected.
            sampling_layer_dim:
                Layer dimension used for submodule sampling.  
                Determines how many consecutive layers are periodically sampled within the matched submodules.
            sampling_token_dim:
                Token dimension used for submodule sampling.  
                Determines how many consecutive tokens are periodically sampled within the matched submodules.
            normalization:
                Normalization option for transform features.  
                If enabled, features are normalized across the batch dimension for structure extraction.
            structure_batch_size:
                Number of accumulated samples required before structure extraction is performed.  
                Rounded up to align with the actual batch size.
            scaling_threshold:
                Scaling ratio applied during structure extraction.  
                Adjusts the threshold relative to the structure batch size,
                where 1.0 means features with an average difference of 1
                across samples are grouped together.
            output_directory:
                Directory where structure analysis results (visualizations, statistics, etc.) will be saved.
            visualization_indexes:
                List of unit indices for structure analysis.  
                Specifies which units are included in feature and cluster visualizations.
            mkdir:
                Whether to automatically create the output directory if it does not exist.
        """
        super().__init__(model)

        # model information (initialized with the first forward)
        self.layer_dim = None
        self.token_dim = None
        self.embedding_dim = None

        # submodule sampling
        self.patterns = patterns
        self.sampling_layer_dim = sampling_layer_dim
        self.sampling_token_dim = sampling_token_dim

        # transform features
        self.normalization = normalization
        self.structure_batch_size = structure_batch_size

        # structure extraction
        self.scaling_threshold = scaling_threshold
        self.dist = None
        self.labels = None
        self.structures['l1_threshold_graph'] = []
        self.structures['first_index_anchor_residual'] = []

        # structure_analysis
        self.output_directory = output_directory
        self.visualization_indexes = visualization_indexes 
        if mkdir:
            os.makedirs(output_directory)

    def get_submodule_information(self, *args, **kwargs):
        if self.layer_dim is None:
            self.activations, self.handles, self.patterns = layer_token_sampling_related_information(
                self.model, 
                self.patterns
            )
            _ = self.model(*args, **kwargs)
            self.layer_dim = len(self.activations)
            exemplar = next(a for a in self.activations if a is not None)
            exemplar = exemplar.detach()
            self.token_dim = int(exemplar.shape[-2])
            self.embedding_dim = int(exemplar.shape[-1])
            for h in self.handles:
                h.remove()
            self.activations = {}
            
            if self.sampling_layer_dim == -1:
                self.sampling_layer_dim = self.layer_dim
            if self.sampling_token_dim == -1:
                self.sampling_token_dim = self.token_dim
        else:
            pass

    def submodule_sampling(self):
        if self.accumulated_features is not None and \
                self.accumulated_features.shape[0] >= self.structure_batch_size:
            for h in self.handles:
                h.remove()
            self.accumulated_features = None
        if self.accumulated_features is None:
            self.activations, self.handles, self.layer_window, self.token_window = \
                layer_token_sampling(self.model, 
                                    self.layer_dim, self.token_dim,
                                    self.patterns,
                                    self.sampling_layer_dim, self.sampling_token_dim)
    
    def transform_feature(self):
        self.features, self.accumulated_features = \
            accumulate_features(self.accumulated_features, self.activations, self.token_window)
        self.accumulated_features = \
            raw(self.accumulated_features, self.normalization, self.structure_batch_size)
    
    def structure_extraction(self):
        if self.accumulated_features.shape[0] >= self.structure_batch_size:
            self.structures['l1_threshold_graph'], self.dist, self.labels = \
                l1_threshold_graph(self.accumulated_features, self.scaling_threshold)
            self.structures['first_index_anchor_residual'] = \
                first_index_anchor_residual(self.structures['l1_threshold_graph'], self.sampling_layer_dim, self.sampling_token_dim, self.embedding_dim)
    
    def structure_analysis(self):
        features = self.features.cpu().numpy()
        labels = self.labels.reshape(self.sampling_layer_dim, self.sampling_token_dim, self.embedding_dim)
        feature_cluster_visualization(features, self.output_directory,
                                      labels, self.visualization_indexes)
        feature_difference(self.dist, self.output_directory, self.sampling_layer_dim)
        structure_related_frequency(self.structures['l1_threshold_graph'], self.output_directory,
                                    labels)
        noncontiguous_structure(self.structures['l1_threshold_graph'], self.output_directory,
                                self.sampling_layer_dim, self.sampling_token_dim, self.embedding_dim)


# ----- entrypoint (include args) -----

@_doc_from(SimpleStructureRaw)
@add_entrypoint(registry="model")
def simple_structure_raw_default(model, cfg={}):
    default_args = dict(
        patterns = r"", # r"blocks\.\d+", 
        sampling_layer_dim = 3,
        sampling_token_dim = 3,
        normalization = False, 
        structure_batch_size = 15360,
        scaling_threshold = 1.0,
    )
    updated_args = _update_args(default_args, cfg)
    return SimpleStructureRaw(model, **updated_args)
