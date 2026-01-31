"""
Synthetic data generators.

Provides functions to generate synthetic datasets
for testing and experimentation.
"""

from __future__ import annotations

from typing import Optional, Tuple, List, Union
import numpy as np


def make_classification(
    n_samples: int = 100,
    n_features: int = 20,
    *,
    n_informative: int = 2,
    n_redundant: int = 2,
    n_repeated: int = 0,
    n_classes: int = 2,
    n_clusters_per_class: int = 2,
    weights: Optional[List[float]] = None,
    flip_y: float = 0.01,
    class_sep: float = 1.0,
    hypercube: bool = True,
    shift: float = 0.0,
    scale: float = 1.0,
    shuffle: bool = True,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a random n-class classification problem.

    Parameters
    ----------
    n_samples : int, default=100
        Number of samples.
    n_features : int, default=20
        Total number of features.
    n_informative : int, default=2
        Number of informative features.
    n_redundant : int, default=2
        Number of redundant (linear combinations) features.
    n_repeated : int, default=0
        Number of duplicated features.
    n_classes : int, default=2
        Number of classes.
    n_clusters_per_class : int, default=2
        Number of clusters per class.
    weights : list of float, optional
        Proportions of samples per class.
    flip_y : float, default=0.01
        Fraction of labels to flip.
    class_sep : float, default=1.0
        Factor multiplying class separation.
    hypercube : bool, default=True
        Place cluster centers on a hypercube.
    shift : float, default=0.0
        Shift features by specified value.
    scale : float, default=1.0
        Scale features by specified value.
    shuffle : bool, default=True
        Shuffle samples and features.
    random_state : int, optional
        Random seed for reproducibility.

    Returns
    -------
    X : ndarray of shape (n_samples, n_features)
        Generated samples.
    y : ndarray of shape (n_samples,)
        Integer labels for class membership.

    Examples
    --------
    >>> from nalyst.datasets import make_classification
    >>> X, y = make_classification(n_samples=100, n_features=4, n_classes=2)
    >>> X.shape
    (100, 4)
    """
    rng = np.random.RandomState(random_state)

    n_useless = n_features - n_informative - n_redundant - n_repeated

    # Generate informative features
    X = np.zeros((n_samples, n_features))
    y = np.zeros(n_samples, dtype=int)

    # Assign samples to classes
    if weights is None:
        weights = [1.0 / n_classes] * n_classes

    weights = np.array(weights)
    weights = weights / weights.sum()

    n_samples_per_class = (weights * n_samples).astype(int)
    n_samples_per_class[-1] = n_samples - n_samples_per_class[:-1].sum()

    # Generate class centers
    n_clusters = n_classes * n_clusters_per_class

    if hypercube:
        # Place centers on vertices of a hypercube
        centroids = rng.choice([-class_sep, class_sep], size=(n_clusters, n_informative))
    else:
        centroids = rng.randn(n_clusters, n_informative) * class_sep

    # Generate samples around centroids
    idx = 0
    for cls, n_cls in enumerate(n_samples_per_class):
        for i in range(n_cls):
            cluster_idx = cls * n_clusters_per_class + i % n_clusters_per_class
            X[idx, :n_informative] = centroids[cluster_idx] + rng.randn(n_informative)
            y[idx] = cls
            idx += 1

    # Generate redundant features as linear combinations
    if n_redundant > 0:
        B = rng.randn(n_informative, n_redundant)
        X[:, n_informative:n_informative + n_redundant] = np.dot(X[:, :n_informative], B)

    # Generate repeated features
    if n_repeated > 0:
        start = n_informative + n_redundant
        indices = rng.choice(n_informative, n_repeated, replace=True)
        X[:, start:start + n_repeated] = X[:, indices]

    # Generate useless features (noise)
    start = n_informative + n_redundant + n_repeated
    X[:, start:] = rng.randn(n_samples, n_useless)

    # Flip labels
    if flip_y > 0:
        flip_idx = rng.choice(n_samples, int(flip_y * n_samples), replace=False)
        y[flip_idx] = rng.randint(0, n_classes, len(flip_idx))

    # Apply shift and scale
    X = X * scale + shift

    # Shuffle
    if shuffle:
        idx = rng.permutation(n_samples)
        X = X[idx]
        y = y[idx]

        feature_idx = rng.permutation(n_features)
        X = X[:, feature_idx]

    return X, y


def make_regression(
    n_samples: int = 100,
    n_features: int = 100,
    *,
    n_informative: int = 10,
    n_targets: int = 1,
    bias: float = 0.0,
    effective_rank: Optional[int] = None,
    tail_strength: float = 0.5,
    noise: float = 0.0,
    shuffle: bool = True,
    coef: bool = False,
    random_state: Optional[int] = None,
) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Generate a random regression problem.

    Parameters
    ----------
    n_samples : int, default=100
        Number of samples.
    n_features : int, default=100
        Number of features.
    n_informative : int, default=10
        Number of informative features.
    n_targets : int, default=1
        Number of regression targets.
    bias : float, default=0.0
        Bias term in the underlying linear model.
    effective_rank : int, optional
        Approximate rank of the input matrix.
    tail_strength : float, default=0.5
        Strength of the tail in singular values.
    noise : float, default=0.0
        Standard deviation of Gaussian noise.
    shuffle : bool, default=True
        Shuffle samples and features.
    coef : bool, default=False
        If True, return the coefficients.
    random_state : int, optional
        Random seed for reproducibility.

    Returns
    -------
    X : ndarray of shape (n_samples, n_features)
        Input samples.
    y : ndarray of shape (n_samples,) or (n_samples, n_targets)
        Target values.
    coef : ndarray of shape (n_features,) or (n_features, n_targets)
        Coefficients (only if coef=True).

    Examples
    --------
    >>> from nalyst.datasets import make_regression
    >>> X, y = make_regression(n_samples=100, n_features=10, n_informative=5)
    >>> X.shape
    (100, 10)
    """
    rng = np.random.RandomState(random_state)

    n_informative = min(n_informative, n_features)

    # Generate input matrix
    if effective_rank is None:
        X = rng.randn(n_samples, n_features)
    else:
        # Generate low-rank matrix
        U = rng.randn(n_samples, effective_rank)
        V = rng.randn(effective_rank, n_features)

        # Generate singular values with tail
        s = np.linspace(1, tail_strength, effective_rank)

        X = np.dot(U * s, V)

    # Generate ground truth coefficients
    ground_truth = np.zeros((n_features, n_targets))
    ground_truth[:n_informative, :] = rng.randn(n_informative, n_targets) * 100

    # Generate target
    y = np.dot(X, ground_truth) + bias

    if noise > 0:
        y += rng.randn(n_samples, n_targets) * noise

    # Flatten if single target
    if n_targets == 1:
        y = y.ravel()
        ground_truth = ground_truth.ravel()

    # Shuffle
    if shuffle:
        idx = rng.permutation(n_samples)
        X = X[idx]
        y = y[idx]

    if coef:
        return X, y, ground_truth

    return X, y


def make_blobs(
    n_samples: int = 100,
    n_features: int = 2,
    *,
    centers: Optional[Union[int, np.ndarray]] = None,
    cluster_std: Union[float, List[float]] = 1.0,
    center_box: Tuple[float, float] = (-10.0, 10.0),
    shuffle: bool = True,
    random_state: Optional[int] = None,
    return_centers: bool = False,
) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Generate isotropic Gaussian blobs for clustering.

    Parameters
    ----------
    n_samples : int, default=100
        Total number of points.
    n_features : int, default=2
        Number of features.
    centers : int or array-like, optional
        Number of centers or explicit center locations.
    cluster_std : float or list of float, default=1.0
        Standard deviation of clusters.
    center_box : tuple, default=(-10.0, 10.0)
        Bounding box for random cluster centers.
    shuffle : bool, default=True
        Shuffle the samples.
    random_state : int, optional
        Random seed.
    return_centers : bool, default=False
        Return cluster centers.

    Returns
    -------
    X : ndarray of shape (n_samples, n_features)
        Generated samples.
    y : ndarray of shape (n_samples,)
        Integer labels for cluster membership.
    centers : ndarray of shape (n_centers, n_features)
        Centers (only if return_centers=True).

    Examples
    --------
    >>> from nalyst.datasets import make_blobs
    >>> X, y = make_blobs(n_samples=100, centers=3)
    >>> X.shape
    (100, 2)
    """
    rng = np.random.RandomState(random_state)

    if centers is None:
        centers = 3

    if isinstance(centers, int):
        n_centers = centers
        centers = rng.uniform(
            center_box[0], center_box[1],
            size=(n_centers, n_features)
        )
    else:
        centers = np.array(centers)
        n_centers = centers.shape[0]

    if isinstance(cluster_std, (int, float)):
        cluster_std = [cluster_std] * n_centers

    n_samples_per_center = [n_samples // n_centers] * n_centers
    for i in range(n_samples % n_centers):
        n_samples_per_center[i] += 1

    X = []
    y = []

    for i, (n, std) in enumerate(zip(n_samples_per_center, cluster_std)):
        X.append(centers[i] + rng.randn(n, n_features) * std)
        y.extend([i] * n)

    X = np.vstack(X)
    y = np.array(y)

    if shuffle:
        idx = rng.permutation(n_samples)
        X = X[idx]
        y = y[idx]

    if return_centers:
        return X, y, centers

    return X, y


def make_circles(
    n_samples: int = 100,
    *,
    shuffle: bool = True,
    noise: Optional[float] = None,
    random_state: Optional[int] = None,
    factor: float = 0.8,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a dataset with large and small circle.

    Useful for testing non-linear classifiers.

    Parameters
    ----------
    n_samples : int, default=100
        Total number of points.
    shuffle : bool, default=True
        Shuffle the samples.
    noise : float, optional
        Standard deviation of Gaussian noise.
    random_state : int, optional
        Random seed.
    factor : float, default=0.8
        Scale factor between inner and outer circle.

    Returns
    -------
    X : ndarray of shape (n_samples, 2)
        Generated 2D samples.
    y : ndarray of shape (n_samples,)
        Integer labels (0 for outer, 1 for inner).

    Examples
    --------
    >>> from nalyst.datasets import make_circles
    >>> X, y = make_circles(n_samples=100)
    >>> X.shape
    (100, 2)
    """
    rng = np.random.RandomState(random_state)

    n_samples_out = n_samples // 2
    n_samples_in = n_samples - n_samples_out

    # Generate outer circle
    linspace_out = np.linspace(0, 2 * np.pi, n_samples_out, endpoint=False)
    outer_circ_x = np.cos(linspace_out)
    outer_circ_y = np.sin(linspace_out)

    # Generate inner circle
    linspace_in = np.linspace(0, 2 * np.pi, n_samples_in, endpoint=False)
    inner_circ_x = np.cos(linspace_in) * factor
    inner_circ_y = np.sin(linspace_in) * factor

    X = np.vstack([
        np.column_stack([outer_circ_x, outer_circ_y]),
        np.column_stack([inner_circ_x, inner_circ_y])
    ])
    y = np.hstack([np.zeros(n_samples_out), np.ones(n_samples_in)]).astype(int)

    if noise is not None:
        X += rng.randn(n_samples, 2) * noise

    if shuffle:
        idx = rng.permutation(n_samples)
        X = X[idx]
        y = y[idx]

    return X, y


def make_moons(
    n_samples: int = 100,
    *,
    shuffle: bool = True,
    noise: Optional[float] = None,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two interleaving half circles.

    Useful for testing non-linear classifiers.

    Parameters
    ----------
    n_samples : int, default=100
        Total number of points.
    shuffle : bool, default=True
        Shuffle the samples.
    noise : float, optional
        Standard deviation of Gaussian noise.
    random_state : int, optional
        Random seed.

    Returns
    -------
    X : ndarray of shape (n_samples, 2)
        Generated 2D samples.
    y : ndarray of shape (n_samples,)
        Integer labels (0 for top, 1 for bottom).

    Examples
    --------
    >>> from nalyst.datasets import make_moons
    >>> X, y = make_moons(n_samples=100, noise=0.1)
    >>> X.shape
    (100, 2)
    """
    rng = np.random.RandomState(random_state)

    n_samples_out = n_samples // 2
    n_samples_in = n_samples - n_samples_out

    # Generate upper moon
    outer_circ_x = np.cos(np.linspace(0, np.pi, n_samples_out))
    outer_circ_y = np.sin(np.linspace(0, np.pi, n_samples_out))

    # Generate lower moon
    inner_circ_x = 1 - np.cos(np.linspace(0, np.pi, n_samples_in))
    inner_circ_y = 1 - np.sin(np.linspace(0, np.pi, n_samples_in)) - 0.5

    X = np.vstack([
        np.column_stack([outer_circ_x, outer_circ_y]),
        np.column_stack([inner_circ_x, inner_circ_y])
    ])
    y = np.hstack([np.zeros(n_samples_out), np.ones(n_samples_in)]).astype(int)

    if noise is not None:
        X += rng.randn(n_samples, 2) * noise

    if shuffle:
        idx = rng.permutation(n_samples)
        X = X[idx]
        y = y[idx]

    return X, y


def make_gaussian_quantiles(
    *,
    mean: Optional[np.ndarray] = None,
    cov: float = 1.0,
    n_samples: int = 100,
    n_features: int = 2,
    n_classes: int = 3,
    shuffle: bool = True,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate isotropic Gaussian and label by quantile.

    Samples are drawn from a single Gaussian distribution,
    then labels are assigned based on distance from origin.

    Parameters
    ----------
    mean : array-like, optional
        Mean of the distribution.
    cov : float, default=1.0
        Covariance.
    n_samples : int, default=100
        Number of samples.
    n_features : int, default=2
        Number of features.
    n_classes : int, default=3
        Number of classes.
    shuffle : bool, default=True
        Shuffle the samples.
    random_state : int, optional
        Random seed.

    Returns
    -------
    X : ndarray of shape (n_samples, n_features)
        Generated samples.
    y : ndarray of shape (n_samples,)
        Integer labels.

    Examples
    --------
    >>> from nalyst.datasets import make_gaussian_quantiles
    >>> X, y = make_gaussian_quantiles(n_samples=100, n_classes=3)
    >>> X.shape
    (100, 2)
    """
    rng = np.random.RandomState(random_state)

    if mean is None:
        mean = np.zeros(n_features)

    mean = np.array(mean)

    X = rng.multivariate_normal(
        mean,
        np.eye(n_features) * cov,
        n_samples
    )

    # Compute distances from mean
    distances = np.sqrt(np.sum((X - mean) ** 2, axis=1))

    # Assign labels based on quantiles
    quantiles = np.percentile(distances, np.linspace(0, 100, n_classes + 1)[1:-1])
    y = np.digitize(distances, quantiles)

    if shuffle:
        idx = rng.permutation(n_samples)
        X = X[idx]
        y = y[idx]

    return X, y


def make_sparse_coded_signal(
    n_samples: int = 100,
    *,
    n_components: int = 512,
    n_features: int = 100,
    n_nonzero_coefs: int = 17,
    random_state: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a signal as a sparse combination of dictionary elements.

    Parameters
    ----------
    n_samples : int, default=100
        Number of samples.
    n_components : int, default=512
        Number of dictionary elements.
    n_features : int, default=100
        Number of features per sample.
    n_nonzero_coefs : int, default=17
        Number of non-zero coefficients.
    random_state : int, optional
        Random seed.

    Returns
    -------
    data : ndarray of shape (n_samples, n_features)
        Generated signal.
    dictionary : ndarray of shape (n_components, n_features)
        Dictionary used to generate the signal.
    code : ndarray of shape (n_samples, n_components)
        Sparse code.

    Examples
    --------
    >>> from nalyst.datasets import make_sparse_coded_signal
    >>> data, dictionary, code = make_sparse_coded_signal(n_samples=10)
    >>> data.shape
    (10, 100)
    """
    rng = np.random.RandomState(random_state)

    # Generate random dictionary
    dictionary = rng.randn(n_components, n_features)
    dictionary /= np.linalg.norm(dictionary, axis=1, keepdims=True)

    # Generate sparse codes
    code = np.zeros((n_samples, n_components))

    for i in range(n_samples):
        idx = rng.choice(n_components, n_nonzero_coefs, replace=False)
        code[i, idx] = rng.randn(n_nonzero_coefs)

    # Generate signal
    data = np.dot(code, dictionary)

    return data, dictionary, code
