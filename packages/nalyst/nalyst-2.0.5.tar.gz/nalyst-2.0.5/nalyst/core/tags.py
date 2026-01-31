"""
Tags system for describing learner capabilities.

Tags provide machine-readable metadata about learners that can be
used for:
- Automated testing
- Capability discovery
- Feature negotiation
- Pipeline validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Set, Type, Union


@dataclass
class InputTags:
    """
    Tags describing input data requirements.

    Attributes
    ----------
    one_d_array : bool
        Whether 1D arrays are accepted (vs 2D only).
    two_d_array : bool
        Whether 2D arrays are accepted.
    three_d_array : bool
        Whether 3D+ arrays are accepted.
    sparse : bool
        Whether sparse matrices are accepted.
    categorical : bool
        Whether categorical features are natively supported.
    string : bool
        Whether string features are accepted.
    dict : bool
        Whether dict inputs are accepted.
    positive_only : bool
        Whether only positive values are accepted.
    allow_nan : bool
        Whether NaN values are handled.
    pairwise : bool
        Whether input is expected in pairwise format.
    """

    one_d_array: bool = True
    two_d_array: bool = True
    three_d_array: bool = False
    sparse: bool = False
    categorical: bool = False
    string: bool = False
    dict: bool = False
    positive_only: bool = False
    allow_nan: bool = False
    pairwise: bool = False


@dataclass
class TargetTags:
    """
    Tags describing target (y) requirements.

    Attributes
    ----------
    required : bool
        Whether y is required for training.
    one_d_labels : bool
        Whether 1D labels are supported.
    two_d_labels : bool
        Whether 2D labels are supported (multi-output).
    positive_only : bool
        Whether only positive targets are valid.
    multi_output : bool
        Whether multi-output is supported.
    single_output : bool
        Whether single output is supported.
    """

    required: bool = True
    one_d_labels: bool = True
    two_d_labels: bool = False
    positive_only: bool = False
    multi_output: bool = False
    single_output: bool = True


@dataclass
class ClassifierTags:
    """
    Tags specific to classification learners.

    Attributes
    ----------
    binary : bool
        Whether binary classification is supported.
    multiclass : bool
        Whether multiclass classification is supported.
    multilabel : bool
        Whether multilabel classification is supported.
    multiclass_multioutput : bool
        Whether multiclass-multioutput is supported.
    decision_function : bool
        Whether decision_function is available.
    predict_proba : bool
        Whether predict_proba is available.
    poor_score : bool
        Whether the classifier might have poor default scores
        (useful for testing).
    """

    binary: bool = True
    multiclass: bool = True
    multilabel: bool = False
    multiclass_multioutput: bool = False
    decision_function: bool = False
    predict_proba: bool = False
    poor_score: bool = False


@dataclass
class RegressorTags:
    """
    Tags specific to regression learners.

    Attributes
    ----------
    multi_target : bool
        Whether multi-target regression is supported.
    poor_score : bool
        Whether the regressor might have poor default scores.
    """

    multi_target: bool = False
    poor_score: bool = False


@dataclass
class TransformerTags:
    """
    Tags specific to transformers.

    Attributes
    ----------
    preserves_dtype : List[type]
        Data types that are preserved through transformation.
    """

    preserves_dtype: List[type] = field(default_factory=list)


@dataclass
class LearnerTags:
    """
    Complete tag set for a learner.

    Attributes
    ----------
    learner_type : str or None
        One of: 'classifier', 'regressor', 'clusterer',
        'transformer', 'density_estimator', 'outlier_detector'.
    input_tags : InputTags
        Tags describing input requirements.
    target_tags : TargetTags
        Tags describing target requirements.
    classifier_tags : ClassifierTags or None
        Additional tags for classifiers.
    regressor_tags : RegressorTags or None
        Additional tags for regressors.
    transformer_tags : TransformerTags or None
        Additional tags for transformers.
    non_deterministic : bool
        Whether the learner produces non-deterministic results.
    requires_train : bool
        Whether train() must be called before infer/transform.
    requires_positive_X : bool
        Whether X must contain only positive values.
    requires_positive_y : bool
        Whether y must contain only positive values.
    X_types : List[str]
        Supported input types: '2darray', 'sparse', 'categorical', etc.
    _xfail_checks : Dict[str, str]
        Checks expected to fail with reasons.
    """

    learner_type: Optional[str] = None
    input_tags: InputTags = field(default_factory=InputTags)
    target_tags: TargetTags = field(default_factory=TargetTags)
    classifier_tags: Optional[ClassifierTags] = None
    regressor_tags: Optional[RegressorTags] = None
    transformer_tags: Optional[TransformerTags] = None
    non_deterministic: bool = False
    requires_train: bool = True
    requires_positive_X: bool = False
    requires_positive_y: bool = False
    preserves_dtype: List[type] = field(default_factory=list)
    X_types: List[str] = field(
        default_factory=lambda: ["2darray"]
    )
    _xfail_checks: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate tags after initialization."""
        valid_types = {
            "classifier", "regressor", "clusterer", "transformer",
            "density_estimator", "outlier_detector", None
        }
        if self.learner_type not in valid_types:
            raise ValueError(
                f"Invalid learner_type: {self.learner_type}. "
                f"Must be one of {valid_types}"
            )


def get_tags(learner: Any) -> LearnerTags:
    """
    Get tags for a learner instance or class.

    Parameters
    ----------
    learner : object or type
        Learner instance or class.

    Returns
    -------
    tags : LearnerTags
        The learner's capability tags.

    Examples
    --------
    >>> from nalyst.learners.linear import LogisticLearner
    >>> tags = get_tags(LogisticLearner())
    >>> tags.learner_type
    'classifier'
    >>> tags.classifier_tags.predict_proba
    True
    """
    if hasattr(learner, "__nalyst_tags__"):
        return learner.__nalyst_tags__()
    else:
        # Return default tags for unknown objects
        return LearnerTags()


def _safe_tags(learner: Any, key: Optional[str] = None) -> Any:
    """
    Safely get a specific tag value or all tags.

    Parameters
    ----------
    learner : object
        Learner to get tags from.
    key : str, optional
        Specific tag to retrieve. If None, returns all tags.

    Returns
    -------
    value : Any
        Tag value or LearnerTags object.
    """
    tags = get_tags(learner)

    if key is None:
        return tags

    # Handle nested keys like "classifier_tags.predict_proba"
    parts = key.split(".")
    value = tags
    for part in parts:
        if hasattr(value, part):
            value = getattr(value, part)
        else:
            return None

    return value


class Tags:
    """
    Namespace for tag-related utilities.

    Examples
    --------
    >>> from nalyst.core.tags import Tags
    >>> Tags.is_classifier(some_learner)
    True
    """

    @staticmethod
    def is_classifier(learner: Any) -> bool:
        """Check if learner is a classifier."""
        return get_tags(learner).learner_type == "classifier"

    @staticmethod
    def is_regressor(learner: Any) -> bool:
        """Check if learner is a regressor."""
        return get_tags(learner).learner_type == "regressor"

    @staticmethod
    def is_clusterer(learner: Any) -> bool:
        """Check if learner is a clusterer."""
        return get_tags(learner).learner_type == "clusterer"

    @staticmethod
    def is_transformer(learner: Any) -> bool:
        """Check if learner has transformer tags."""
        return get_tags(learner).transformer_tags is not None

    @staticmethod
    def supports_sparse(learner: Any) -> bool:
        """Check if learner supports sparse input."""
        return get_tags(learner).input_tags.sparse

    @staticmethod
    def requires_y(learner: Any) -> bool:
        """Check if learner requires target values."""
        return get_tags(learner).target_tags.required

    @staticmethod
    def supports_multioutput(learner: Any) -> bool:
        """Check if learner supports multi-output."""
        return get_tags(learner).target_tags.multi_output

    @staticmethod
    def has_predict_proba(learner: Any) -> bool:
        """Check if classifier has predict_proba."""
        tags = get_tags(learner)
        if tags.classifier_tags:
            return tags.classifier_tags.predict_proba
        return False


def make_tags(
    learner_type: Optional[str] = None,
    *,
    sparse_input: bool = False,
    allows_nan: bool = False,
    requires_y: bool = True,
    multi_output: bool = False,
    binary: bool = True,
    multiclass: bool = True,
    predict_proba: bool = False,
    non_deterministic: bool = False,
    **kwargs
) -> LearnerTags:
    """
    Convenience function to create LearnerTags.

    Parameters
    ----------
    learner_type : str, optional
        Type of learner.
    sparse_input : bool
        Support sparse input.
    allows_nan : bool
        Allow NaN values.
    requires_y : bool
        Require target values.
    multi_output : bool
        Support multi-output.
    binary : bool
        Support binary classification.
    multiclass : bool
        Support multiclass.
    predict_proba : bool
        Has probability predictions.
    non_deterministic : bool
        Results may vary.
    **kwargs
        Additional tag values.

    Returns
    -------
    tags : LearnerTags
    """
    input_tags = InputTags(
        sparse=sparse_input,
        allow_nan=allows_nan,
    )

    target_tags = TargetTags(
        required=requires_y,
        multi_output=multi_output,
    )

    classifier_tags = None
    regressor_tags = None

    if learner_type == "classifier":
        classifier_tags = ClassifierTags(
            binary=binary,
            multiclass=multiclass,
            predict_proba=predict_proba,
        )
    elif learner_type == "regressor":
        regressor_tags = RegressorTags(
            multi_target=multi_output,
        )

    return LearnerTags(
        learner_type=learner_type,
        input_tags=input_tags,
        target_tags=target_tags,
        classifier_tags=classifier_tags,
        regressor_tags=regressor_tags,
        non_deterministic=non_deterministic,
        **kwargs
    )
