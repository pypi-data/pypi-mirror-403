"""
Input validation utilities for Nalyst.

This module provides functions to validate and convert input data
to ensure consistent, safe operation across all learners.
"""

from __future__ import annotations

import numbers
import warnings
from typing import (
    Any, Dict, List, Literal, Optional, Sequence, Tuple, Type, Union
)

import numpy as np
from scipy import sparse

from nalyst.core.settings import get_settings


# Type aliases
ArrayLike = Union[np.ndarray, List, Tuple, "pd.DataFrame", "pd.Series"]
SparseMatrix = Union[sparse.csr_matrix, sparse.csc_matrix, sparse.coo_matrix]


def check_random_state(seed: Optional[Union[int, np.random.RandomState]] = None):
    """
    Convert input to a numpy RandomState instance.

    Parameters
    ----------
    seed : int, RandomState, or None
        If int, creates new RandomState with that seed.
        If RandomState, returns it unchanged.
        If None, returns the global RandomState.

    Returns
    -------
    np.random.RandomState
        A valid RandomState instance.

    Examples
    --------
    >>> rng = check_random_state(42)
    >>> rng.randint(0, 10)
    1
    """
    if seed is None or seed is np.random:
        return np.random.mtrand._rand
    if isinstance(seed, numbers.Integral):
        return np.random.RandomState(seed)
    if isinstance(seed, np.random.RandomState):
        return seed
    if isinstance(seed, np.random.Generator):
        return seed
    raise ValueError(
        f"seed must be int, RandomState, Generator, or None, got {type(seed)}"
    )


def check_array(
    array: Any,
    *,
    accept_sparse: Union[bool, str, Sequence[str]] = False,
    accept_large_sparse: bool = True,
    dtype: Optional[Union[type, str, List[type]]] = "numeric",
    order: Optional[Literal["C", "F"]] = None,
    copy: bool = False,
    force_writeable: bool = False,
    force_all_finite: Union[bool, Literal["allow-nan", "allow-inf"]] = True,
    ensure_2d: bool = True,
    allow_nd: bool = False,
    ensure_min_samples: int = 1,
    ensure_min_features: int = 1,
    estimator: Optional[Any] = None,
    input_name: str = "X",
) -> np.ndarray:
    """
    Validate and convert input array.

    Parameters
    ----------
    array : array-like
        Input to convert.
    accept_sparse : bool, str, or sequence of str
        String[s] specifying allowed sparse matrix format(s).
    accept_large_sparse : bool
        Whether to allow 64-bit indices.
    dtype : type, str, list of types, or None
        Data type(s) that are acceptable. "numeric" accepts floats and ints.
    order : {"C", "F"} or None
        Memory layout. None preserves input order.
    copy : bool
        Force a copy of the input.
    force_writeable : bool
        Ensure output array is writeable.
    force_all_finite : bool or "allow-nan" or "allow-inf"
        How to handle NaN and Inf values.
    ensure_2d : bool
        Require 2D array.
    allow_nd : bool
        Allow arrays with >2 dimensions.
    ensure_min_samples : int
        Minimum number of samples required.
    ensure_min_features : int
        Minimum number of features required.
    estimator : object or str
        Learner instance for error messages.
    input_name : str
        Name of the input for error messages.

    Returns
    -------
    array_converted : ndarray
        The converted array.

    Raises
    ------
    ValueError
        If the array fails validation.
    """
    settings = get_settings()

    # Handle sparse matrices
    is_sparse = sparse.issparse(array)

    if is_sparse:
        return _check_sparse_array(
            array,
            accept_sparse=accept_sparse,
            accept_large_sparse=accept_large_sparse,
            dtype=dtype,
            copy=copy,
            force_all_finite=force_all_finite,
            estimator=estimator,
            input_name=input_name,
        )

    # Convert to numpy array
    if hasattr(array, "__array__"):
        array = np.asarray(array)
    else:
        array = np.array(array)

    # Handle dtype
    if dtype == "numeric":
        if np.issubdtype(array.dtype, np.object_):
            dtype = np.float64
        elif not np.issubdtype(array.dtype, np.number):
            dtype = np.float64
        else:
            dtype = None

    if dtype is not None:
        if isinstance(dtype, (list, tuple)):
            if array.dtype not in dtype:
                array = array.astype(dtype[0])
        elif array.dtype != dtype:
            array = array.astype(dtype)

    # Handle order and copy
    if copy:
        array = array.copy()

    if order is not None:
        array = np.asarray(array, order=order)

    if force_writeable and not array.flags.writeable:
        array = array.copy()

    # Validate dimensions
    if array.ndim == 0:
        raise ValueError(
            f"Expected array-like input for {input_name}, got scalar {array!r}"
        )

    if ensure_2d:
        if array.ndim == 1:
            warnings.warn(
                f"Passing 1D array for {input_name}; reshaping to (n_samples, 1). "
                "This will raise an error in future versions.",
                FutureWarning
            )
            array = array.reshape(-1, 1)
        elif array.ndim != 2:
            raise ValueError(
                f"Expected 2D array for {input_name}, got {array.ndim}D"
            )

    if not allow_nd and array.ndim > 2:
        raise ValueError(
            f"Expected <=2D array for {input_name}, got {array.ndim}D"
        )

    # Validate size
    if ensure_2d or array.ndim >= 2:
        n_samples, n_features = array.shape[0], array.shape[-1]
    else:
        n_samples = array.shape[0]
        n_features = 1

    if n_samples < ensure_min_samples:
        raise ValueError(
            f"{input_name} requires at least {ensure_min_samples} samples, "
            f"got {n_samples}"
        )

    if ensure_2d and n_features < ensure_min_features:
        raise ValueError(
            f"{input_name} requires at least {ensure_min_features} features, "
            f"got {n_features}"
        )

    # Validate finite values
    if not settings.get("assume_finite", False):
        _check_finite(array, force_all_finite, input_name)

    return array


def _check_sparse_array(
    array: SparseMatrix,
    *,
    accept_sparse: Union[bool, str, Sequence[str]],
    accept_large_sparse: bool,
    dtype: Optional[Any],
    copy: bool,
    force_all_finite: Union[bool, str],
    estimator: Optional[Any],
    input_name: str,
) -> SparseMatrix:
    """Validate sparse matrix input."""
    if accept_sparse is False:
        raise TypeError(
            f"Sparse matrix not supported for {input_name}. "
            "Convert to dense array first."
        )

    if accept_sparse is True:
        accept_sparse = ["csr", "csc", "coo"]
    elif isinstance(accept_sparse, str):
        accept_sparse = [accept_sparse]

    # Convert format if needed
    sparse_format = array.format
    if sparse_format not in accept_sparse:
        array = array.asformat(accept_sparse[0])

    if dtype == "numeric":
        dtype = None

    if dtype is not None and array.dtype != dtype:
        array = array.astype(dtype)

    if copy:
        array = array.copy()

    # Check for large sparse indices
    if not accept_large_sparse:
        if hasattr(array, "indices"):
            if array.indices.dtype != np.int32:
                warnings.warn(
                    "Large sparse matrix with 64-bit indices detected. "
                    "This may be slow.",
                    UserWarning
                )

    # Validate finite values
    if force_all_finite:
        _check_finite(array.data, force_all_finite, input_name)

    return array


def _check_finite(
    array: np.ndarray,
    force_all_finite: Union[bool, str],
    input_name: str,
) -> None:
    """Check for NaN and Inf values."""
    if force_all_finite is True:
        if np.any(np.isnan(array)) or np.any(np.isinf(array)):
            raise ValueError(
                f"{input_name} contains NaN or Inf values. "
                "Use force_all_finite='allow-nan' or 'allow-inf' if needed."
            )
    elif force_all_finite == "allow-nan":
        if np.any(np.isinf(array)):
            raise ValueError(f"{input_name} contains Inf values.")
    elif force_all_finite == "allow-inf":
        if np.any(np.isnan(array)):
            raise ValueError(f"{input_name} contains NaN values.")


def check_X_y(
    X: Any,
    y: Any,
    *,
    accept_sparse: Union[bool, str, Sequence[str]] = False,
    accept_large_sparse: bool = True,
    dtype: Optional[Union[type, str, List[type]]] = "numeric",
    order: Optional[Literal["C", "F"]] = None,
    copy: bool = False,
    force_all_finite: Union[bool, str] = True,
    ensure_2d: bool = True,
    allow_nd: bool = False,
    multi_output: bool = False,
    ensure_min_samples: int = 1,
    ensure_min_features: int = 1,
    y_numeric: bool = False,
    estimator: Optional[Any] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validate X and y arrays for supervised learning.

    Parameters
    ----------
    X : array-like
        Input features.
    y : array-like
        Target values.
    accept_sparse : bool, str, or sequence of str
        Allowed sparse formats for X.
    accept_large_sparse : bool
        Allow 64-bit indices.
    dtype : type, str, list of types, or None
        Acceptable data type(s) for X.
    order : {"C", "F"} or None
        Memory layout.
    copy : bool
        Force copies.
    force_all_finite : bool or str
        How to handle NaN/Inf.
    ensure_2d : bool
        Require 2D X.
    allow_nd : bool
        Allow >2D arrays.
    multi_output : bool
        Allow 2D y for multi-output.
    ensure_min_samples : int
        Minimum samples required.
    ensure_min_features : int
        Minimum features required.
    y_numeric : bool
        Force y to be numeric.
    estimator : object or str
        For error messages.

    Returns
    -------
    X_converted : ndarray
    y_converted : ndarray
    """
    X = check_array(
        X,
        accept_sparse=accept_sparse,
        accept_large_sparse=accept_large_sparse,
        dtype=dtype,
        order=order,
        copy=copy,
        force_all_finite=force_all_finite,
        ensure_2d=ensure_2d,
        allow_nd=allow_nd,
        ensure_min_samples=ensure_min_samples,
        ensure_min_features=ensure_min_features,
        estimator=estimator,
        input_name="X",
    )

    # Validate y
    y = check_array(
        y,
        accept_sparse=False,
        dtype="numeric" if y_numeric else None,
        order=None,
        copy=False,
        force_all_finite=force_all_finite,
        ensure_2d=False,
        allow_nd=False,
        ensure_min_samples=1,
        ensure_min_features=1,
        estimator=estimator,
        input_name="y",
    )

    if not multi_output and y.ndim == 2 and y.shape[1] != 1:
        raise ValueError(
            f"y has shape {y.shape} but multi_output=False. "
            "Set multi_output=True for multi-target problems."
        )

    if y.ndim == 2 and y.shape[1] == 1:
        y = y.ravel()

    # Check matching lengths
    if X.shape[0] != y.shape[0]:
        raise ValueError(
            f"X and y have inconsistent sample counts: "
            f"{X.shape[0]} vs {y.shape[0]}"
        )

    return X, y


def check_is_trained(
    learner: Any,
    attributes: Optional[Union[str, List[str]]] = None,
    *,
    msg: Optional[str] = None,
) -> None:
    """
    Check if a learner has been trained.

    Parameters
    ----------
    learner : object
        Learner to check.
    attributes : str or list of str, optional
        Specific attributes to check for. If None, checks for any
        attribute ending with '_'.
    msg : str, optional
        Custom error message.

    Raises
    ------
    NotTrainedError
        If the learner is not trained.

    Examples
    --------
    >>> from nalyst.learners.linear import LogisticLearner
    >>> model = LogisticLearner()
    >>> check_is_trained(model)
    Traceback (most recent call last):
        ...
    NotTrainedError: LogisticLearner is not trained...
    """
    if attributes is None:
        # Look for any fitted attribute (ending with _)
        fitted_attrs = [
            attr for attr in dir(learner)
            if attr.endswith("_") and not attr.startswith("__")
            and not callable(getattr(learner, attr, None))
        ]
        is_trained = len(fitted_attrs) > 0
    else:
        if isinstance(attributes, str):
            attributes = [attributes]
        is_trained = all(hasattr(learner, attr) for attr in attributes)

    if not is_trained:
        if msg is None:
            learner_name = type(learner).__name__
            msg = (
                f"{learner_name} is not trained. "
                f"Call 'train()' before using this method."
            )
        from nalyst.exceptions import NotTrainedError
        raise NotTrainedError(msg)


def validate_input(
    X: Any,
    *,
    accept_sparse: Union[bool, str, Sequence[str]] = True,
    reset: bool = True,
    learner: Optional[Any] = None,
) -> np.ndarray:
    """
    Validate input for a trained learner.

    Parameters
    ----------
    X : array-like
        Input data.
    accept_sparse : bool, str, or sequence of str
        Allowed sparse formats.
    reset : bool
        If True, reset the n_features_in_ attribute.
    learner : object, optional
        The learner instance for feature count validation.

    Returns
    -------
    X_validated : ndarray
    """
    X = check_array(X, accept_sparse=accept_sparse)

    if learner is not None:
        if reset:
            learner.n_features_in_ = X.shape[1]
            if hasattr(X, "columns"):
                learner.feature_names_in_ = np.asarray(X.columns)
        else:
            if hasattr(learner, "n_features_in_"):
                if X.shape[1] != learner.n_features_in_:
                    raise ValueError(
                        f"X has {X.shape[1]} features but {type(learner).__name__} "
                        f"expects {learner.n_features_in_} features."
                    )

    return X


def check_consistent_length(*arrays) -> None:
    """
    Check that all arrays have consistent first dimension.

    Parameters
    ----------
    *arrays : list of arrays
        Arrays to check.

    Raises
    ------
    ValueError
        If arrays have inconsistent lengths.
    """
    lengths = []
    for arr in arrays:
        if arr is None:
            continue
        if hasattr(arr, "shape"):
            lengths.append(arr.shape[0])
        elif hasattr(arr, "__len__"):
            lengths.append(len(arr))
        else:
            raise TypeError(f"Expected array-like, got {type(arr)}")

    unique_lengths = set(lengths)
    if len(unique_lengths) > 1:
        raise ValueError(
            f"Found arrays with inconsistent lengths: {sorted(unique_lengths)}"
        )


def column_or_1d(y: np.ndarray, *, warn: bool = False) -> np.ndarray:
    """
    Convert column vector or 1D array to 1D array.

    Parameters
    ----------
    y : array-like
        Input array.
    warn : bool
        Warn if column vector is passed.

    Returns
    -------
    y : ndarray of shape (n_samples,)
    """
    y = np.asarray(y)

    if y.ndim == 2 and y.shape[1] == 1:
        if warn:
            warnings.warn(
                "Column vector passed; converting to 1D array",
                UserWarning
            )
        return y.ravel()
    elif y.ndim == 1:
        return y
    else:
        raise ValueError(
            f"Expected column vector or 1D array, got shape {y.shape}"
        )


def validate_constraints(
    constraints: Dict[str, Any],
    params: Dict[str, Any],
    *,
    caller: str = "",
) -> None:
    """
    Validate parameters against constraints.

    Parameters
    ----------
    constraints : dict
        Mapping of parameter names to constraint specifications.
    params : dict
        Actual parameter values.
    caller : str
        Name of the calling class for error messages.
    """
    from nalyst.core.constraints import validate_parameter

    for param_name, constraint in constraints.items():
        if param_name in params:
            validate_parameter(
                constraint,
                params[param_name],
                param_name=param_name,
                caller=caller,
            )
