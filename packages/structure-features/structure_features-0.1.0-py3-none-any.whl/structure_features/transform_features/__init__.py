"""
In `transform_features`, it define preprocessing methods which transform features for improved structure extraction.  
This mechanism helps reduce the sensitivity of feature comparisons to absolute magnitude differences and noise during structure extraction.  
Detailed usage of each function can be found in the corresponding function definitions.

Copyright (c) 2025 Sejik Park

---
"""

from .group_rank import accumulate_features
from .group_rank import group_rank
from .raw import raw