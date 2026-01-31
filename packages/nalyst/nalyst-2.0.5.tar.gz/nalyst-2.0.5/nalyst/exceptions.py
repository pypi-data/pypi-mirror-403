"""
Custom exceptions for Nalyst.

This module defines all custom exceptions used throughout the library.
"""

from __future__ import annotations


class NalystError(Exception):
    """Base exception for all Nalyst-specific errors."""
    pass


class NotTrainedError(NalystError, ValueError):
    """
    Exception raised when a learner is used before training.

    This error is raised when attempting to use methods that require
    a trained learner (like `infer()` or `transform()`) before the
    `train()` method has been called.

    Examples
    --------
    >>> from nalyst.learners.linear import LogisticLearner
    >>> model = LogisticLearner()
    >>> model.infer([[1, 2]])  # doctest: +SKIP
    Traceback (most recent call last):
        ...
    NotTrainedError: LogisticLearner is not trained...
    """
    pass


class ConvergenceWarning(NalystError, UserWarning):
    """
    Warning raised when an algorithm fails to converge.

    This is raised by iterative algorithms when they reach their
    maximum number of iterations without meeting convergence criteria.
    """
    pass


class DataConversionWarning(NalystError, UserWarning):
    """
    Warning raised when data is converted to a different type.

    This is raised when input data is automatically converted
    (e.g., from int to float) in a potentially lossy way.
    """
    pass


class ValidationError(NalystError, ValueError):
    """
    Exception raised for invalid input validation.

    This is raised when input data fails validation checks,
    such as having the wrong shape, containing invalid values,
    or missing required features.
    """
    pass


class DimensionalityError(ValidationError):
    """
    Exception raised for dimension mismatches.

    This is raised when arrays have incompatible shapes
    for the requested operation.
    """
    pass


class ParameterError(NalystError, ValueError):
    """
    Exception raised for invalid parameter values.

    This is raised when a learner receives parameter values
    that are outside the acceptable range or invalid type.
    """
    pass


class FeatureNameWarning(NalystError, UserWarning):
    """
    Warning raised for feature name issues.

    This is raised when feature names are inconsistent between
    training and inference, or when names contain invalid characters.
    """
    pass


class InconsistentVersionWarning(NalystError, UserWarning):
    """
    Warning raised when unpickling from a different version.

    This is raised when loading a serialized learner that was
    saved with a different version of Nalyst.
    """
    pass


class PositiveSpectrumWarning(NalystError, UserWarning):
    """
    Warning raised when eigenvalues are adjusted.

    This is raised when a covariance or kernel matrix has
    negative eigenvalues that must be clipped or adjusted.
    """
    pass


class UndefinedMetricWarning(NalystError, UserWarning):
    """
    Warning raised when a metric is undefined.

    This is raised when computing a metric that is undefined
    for the given input (e.g., precision with no positive predictions).
    """
    pass


class EfficiencyWarning(NalystError, UserWarning):
    """
    Warning raised for potentially inefficient operations.

    This is raised when an operation might be slow or memory-intensive,
    suggesting a more efficient alternative.
    """
    pass


class InferenceInternalError(NalystError, RuntimeError):
    """
    Exception raised for internal inference errors.

    This is raised when an unexpected error occurs during
    inference that indicates a bug in the library.
    """
    pass


class WorkflowError(NalystError, ValueError):
    """
    Exception raised for workflow/pipeline configuration errors.

    This is raised when a workflow is incorrectly configured,
    such as having incompatible steps or missing required components.
    """
    pass


# Convenience function for deprecation warnings
def _deprecation_warning(
    message: str,
    *,
    version: str = "1.0",
    stacklevel: int = 2,
) -> None:
    """
    Issue a deprecation warning.

    Parameters
    ----------
    message : str
        The deprecation message.
    version : str
        Version when the feature will be removed.
    stacklevel : int
        Stack level for the warning.
    """
    import warnings
    full_message = f"{message} This will be removed in version {version}."
    warnings.warn(full_message, FutureWarning, stacklevel=stacklevel + 1)


# Convenience function for future warnings
def _future_warning(
    message: str,
    *,
    version: str = "1.0",
    stacklevel: int = 2,
) -> None:
    """
    Issue a future behavior warning.

    Parameters
    ----------
    message : str
        The warning message.
    version : str
        Version when the behavior will change.
    stacklevel : int
        Stack level for the warning.
    """
    import warnings
    full_message = f"{message} Behavior will change in version {version}."
    warnings.warn(full_message, FutureWarning, stacklevel=stacklevel + 1)
