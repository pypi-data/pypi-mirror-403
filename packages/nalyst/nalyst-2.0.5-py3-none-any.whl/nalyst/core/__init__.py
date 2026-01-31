"""
Core module for Nalyst - Foundation classes and infrastructure.
"""

from nalyst.core.foundation import (
    BaseLearner,
    ClassifierMixin,
    RegressorMixin,
    TransformerMixin,
    ClusterMixin,
    SelectorMixin,
    MetaLearnerMixin,
    DensityMixin,
    OutlierMixin,
    duplicate,
    is_classifier,
    is_regressor,
    is_clusterer,
)

from nalyst.core.settings import (
    get_settings,
    set_settings,
    settings_context,
)

from nalyst.core.validation import (
    check_array,
    check_X_y,
    check_is_trained,
    validate_input,
)

from nalyst.core.tags import (
    LearnerTags,
    InputTags,
    TargetTags,
    get_tags,
)

__all__ = [
    # Foundation classes
    "BaseLearner",
    "ClassifierMixin",
    "RegressorMixin",
    "TransformerMixin",
    "ClusterMixin",
    "SelectorMixin",
    "MetaLearnerMixin",
    "DensityMixin",
    "OutlierMixin",
    # Utility functions
    "duplicate",
    "is_classifier",
    "is_regressor",
    "is_clusterer",
    # Settings
    "get_settings",
    "set_settings",
    "settings_context",
    # Validation
    "check_array",
    "check_X_y",
    "check_is_trained",
    "validate_input",
    # Tags
    "LearnerTags",
    "InputTags",
    "TargetTags",
    "get_tags",
]
