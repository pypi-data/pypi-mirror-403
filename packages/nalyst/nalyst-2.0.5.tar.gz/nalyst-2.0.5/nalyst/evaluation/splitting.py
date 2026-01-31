"""
Data splitting utilities.

Provides methods for splitting datasets into training
and testing sets for model evaluation.
"""

from __future__ import annotations

from typing import Optional, List, Tuple, Union, Iterator

import numpy as np

from nalyst.core.validation import check_random_state


def train_test_split(
    *arrays,
    test_size: Optional[Union[float, int]] = None,
    train_size: Optional[Union[float, int]] = None,
    random_state: Optional[int] = None,
    shuffle: bool = True,
    stratify: Optional[np.ndarray] = None,
) -> List[np.ndarray]:
    """
    Split arrays into train and test subsets.

    Parameters
    ----------
    *arrays : sequence of arrays
        Arrays to split. Must have same first dimension.
    test_size : float or int, optional
        Test set size. Float for proportion, int for absolute.
        Default is 0.25 if train_size is None.
    train_size : float or int, optional
        Train set size. Float for proportion, int for absolute.
    random_state : int, optional
        Random seed for reproducibility.
    shuffle : bool, default=True
        Whether to shuffle before splitting.
    stratify : array-like, optional
        Labels for stratified splitting.

    Returns
    -------
    splitting : list of arrays
        Train-test split of inputs.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import train_test_split
    >>> X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    >>> y = np.array([0, 0, 1, 1])
    >>> X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)
    >>> X_train
    array([[5, 6],
           [3, 4]])
    """
    if len(arrays) == 0:
        raise ValueError("At least one array required")

    # Check arrays have same length
    n_samples = len(arrays[0])
    for arr in arrays[1:]:
        if len(arr) != n_samples:
            raise ValueError("All arrays must have the same first dimension")

    # Determine split sizes
    if test_size is None and train_size is None:
        test_size = 0.25

    if isinstance(test_size, float):
        n_test = int(n_samples * test_size)
    elif isinstance(test_size, int):
        n_test = test_size
    elif train_size is not None:
        if isinstance(train_size, float):
            n_test = n_samples - int(n_samples * train_size)
        else:
            n_test = n_samples - train_size
    else:
        n_test = int(n_samples * 0.25)

    n_train = n_samples - n_test

    rng = check_random_state(random_state)

    if stratify is not None:
        # Stratified split
        stratify = np.asarray(stratify)
        classes, class_indices = np.unique(stratify, return_inverse=True)

        train_indices = []
        test_indices = []

        for cls_idx, cls in enumerate(classes):
            cls_mask = class_indices == cls_idx
            cls_indices_arr = np.where(cls_mask)[0]

            if shuffle:
                rng.shuffle(cls_indices_arr)

            n_cls = len(cls_indices_arr)
            n_cls_test = int(n_cls * n_test / n_samples)

            test_indices.extend(cls_indices_arr[:n_cls_test])
            train_indices.extend(cls_indices_arr[n_cls_test:])

        train_indices = np.array(train_indices)
        test_indices = np.array(test_indices)

        if shuffle:
            rng.shuffle(train_indices)
            rng.shuffle(test_indices)

    else:
        indices = np.arange(n_samples)

        if shuffle:
            rng.shuffle(indices)

        test_indices = indices[:n_test]
        train_indices = indices[n_test:]

    result = []
    for arr in arrays:
        arr = np.asarray(arr)
        result.append(arr[train_indices])
        result.append(arr[test_indices])

    return result


class BaseCrossValidator:
    """Base class for cross-validators."""

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Return number of splits."""
        raise NotImplementedError

    def split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        groups: Optional[np.ndarray] = None,
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """Generate train/test indices."""
        raise NotImplementedError


class KFold(BaseCrossValidator):
    """
    K-Fold cross-validator.

    Divides data into k consecutive folds, using each
    as a test set once.

    Parameters
    ----------
    n_splits : int, default=5
        Number of folds.
    shuffle : bool, default=False
        Shuffle data before splitting.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import KFold
    >>> X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    >>> kfold = KFold(n_splits=2)
    >>> for train_idx, test_idx in kfold.split(X):
    ...     print(f"Train: {train_idx}, Test: {test_idx}")
    Train: [2 3], Test: [0 1]
    Train: [0 1], Test: [2 3]
    """

    def __init__(
        self,
        n_splits: int = 5,
        *,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Return number of splits."""
        return self.n_splits

    def split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        groups: Optional[np.ndarray] = None,
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate train/test indices for each fold.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like, optional
            Target variable (ignored for non-stratified).
        groups : array-like, optional
            Group labels (ignored).

        Yields
        ------
        train : ndarray
            Training set indices.
        test : ndarray
            Test set indices.
        """
        X = np.asarray(X)
        n_samples = X.shape[0]
        indices = np.arange(n_samples)

        if self.shuffle:
            rng = check_random_state(self.random_state)
            rng.shuffle(indices)

        fold_sizes = np.full(self.n_splits, n_samples // self.n_splits)
        fold_sizes[:n_samples % self.n_splits] += 1

        current = 0
        for fold_size in fold_sizes:
            start = current
            stop = current + fold_size
            test_indices = indices[start:stop]
            train_indices = np.concatenate([indices[:start], indices[stop:]])
            yield train_indices, test_indices
            current = stop


class StratifiedKFold(BaseCrossValidator):
    """
    Stratified K-Fold cross-validator.

    Ensures each fold has approximately the same class distribution.

    Parameters
    ----------
    n_splits : int, default=5
        Number of folds.
    shuffle : bool, default=False
        Shuffle data before splitting.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import StratifiedKFold
    >>> X = np.array([[1], [2], [3], [4], [5], [6]])
    >>> y = np.array([0, 0, 0, 1, 1, 1])
    >>> skf = StratifiedKFold(n_splits=3)
    >>> for train_idx, test_idx in skf.split(X, y):
    ...     print(f"Train: {train_idx}, Test: {test_idx}")
    """

    def __init__(
        self,
        n_splits: int = 5,
        *,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Return number of splits."""
        return self.n_splits

    def split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        groups: Optional[np.ndarray] = None,
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate stratified train/test indices.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target labels for stratification.
        groups : array-like, optional
            Group labels (ignored).

        Yields
        ------
        train : ndarray
            Training set indices.
        test : ndarray
            Test set indices.
        """
        X = np.asarray(X)
        y = np.asarray(y)
        n_samples = X.shape[0]

        classes, y_indices = np.unique(y, return_inverse=True)
        n_classes = len(classes)

        rng = check_random_state(self.random_state)

        # Organize indices by class
        class_indices = [np.where(y_indices == k)[0] for k in range(n_classes)]

        if self.shuffle:
            for cls_idx in class_indices:
                rng.shuffle(cls_idx)

        # Create folds ensuring stratification
        test_folds = np.zeros(n_samples, dtype=int)

        for cls_idx in class_indices:
            n_cls = len(cls_idx)
            fold_sizes = np.full(self.n_splits, n_cls // self.n_splits)
            fold_sizes[:n_cls % self.n_splits] += 1

            current = 0
            for fold_idx, fold_size in enumerate(fold_sizes):
                test_folds[cls_idx[current:current + fold_size]] = fold_idx
                current += fold_size

        for fold_idx in range(self.n_splits):
            test_indices = np.where(test_folds == fold_idx)[0]
            train_indices = np.where(test_folds != fold_idx)[0]
            yield train_indices, test_indices


class LeaveOneOut(BaseCrossValidator):
    """
    Leave-One-Out cross-validator.

    Each sample is used once as test set.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import LeaveOneOut
    >>> X = np.array([[1], [2], [3]])
    >>> loo = LeaveOneOut()
    >>> for train_idx, test_idx in loo.split(X):
    ...     print(f"Train: {train_idx}, Test: {test_idx}")
    Train: [1 2], Test: [0]
    Train: [0 2], Test: [1]
    Train: [0 1], Test: [2]
    """

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Return number of splits."""
        if X is None:
            raise ValueError("X is required")
        return len(np.asarray(X))

    def split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        groups: Optional[np.ndarray] = None,
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate leave-one-out train/test indices.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like, optional
            Target variable (ignored).
        groups : array-like, optional
            Group labels (ignored).

        Yields
        ------
        train : ndarray
            Training set indices.
        test : ndarray
            Test set indices.
        """
        X = np.asarray(X)
        n_samples = X.shape[0]
        indices = np.arange(n_samples)

        for i in range(n_samples):
            test_indices = np.array([i])
            train_indices = np.concatenate([indices[:i], indices[i + 1:]])
            yield train_indices, test_indices


class ShuffleSplit(BaseCrossValidator):
    """
    Random permutation cross-validator.

    Generates random train/test splits.

    Parameters
    ----------
    n_splits : int, default=10
        Number of re-shuffling & splitting iterations.
    test_size : float or int, optional
        Test set size.
    train_size : float or int, optional
        Train set size.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import ShuffleSplit
    >>> X = np.array([[1], [2], [3], [4], [5]])
    >>> ss = ShuffleSplit(n_splits=3, test_size=0.4, random_state=42)
    >>> for train_idx, test_idx in ss.split(X):
    ...     print(f"Train: {train_idx}, Test: {test_idx}")
    """

    def __init__(
        self,
        n_splits: int = 10,
        *,
        test_size: Optional[Union[float, int]] = None,
        train_size: Optional[Union[float, int]] = None,
        random_state: Optional[int] = None,
    ):
        self.n_splits = n_splits
        self.test_size = test_size
        self.train_size = train_size
        self.random_state = random_state

    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Return number of splits."""
        return self.n_splits

    def split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        groups: Optional[np.ndarray] = None,
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generate random train/test indices.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like, optional
            Target variable (ignored).
        groups : array-like, optional
            Group labels (ignored).

        Yields
        ------
        train : ndarray
            Training set indices.
        test : ndarray
            Test set indices.
        """
        X = np.asarray(X)
        n_samples = X.shape[0]

        # Determine sizes
        if self.test_size is None and self.train_size is None:
            test_size = 0.1
        else:
            test_size = self.test_size

        if isinstance(test_size, float):
            n_test = int(n_samples * test_size)
        elif isinstance(test_size, int):
            n_test = test_size
        else:
            if isinstance(self.train_size, float):
                n_test = n_samples - int(n_samples * self.train_size)
            else:
                n_test = n_samples - self.train_size

        rng = check_random_state(self.random_state)

        for _ in range(self.n_splits):
            permutation = rng.permutation(n_samples)
            test_indices = permutation[:n_test]
            train_indices = permutation[n_test:]
            yield train_indices, test_indices
