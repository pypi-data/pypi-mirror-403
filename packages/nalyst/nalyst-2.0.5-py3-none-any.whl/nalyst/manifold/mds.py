"""
Multidimensional Scaling (MDS).
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy.spatial.distance import pdist, squareform

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


class MDS(BaseLearner):
    """
    Multidimensional Scaling.

    Parameters
    ----------
    n_components : int, default=2
        Number of dimensions in which to immerse the dissimilarities.
    metric : bool, default=True
        If True, perform metric MDS; otherwise, non-metric MDS.
    n_init : int, default=4
        Number of initializations.
    max_iter : int, default=300
        Maximum number of iterations for SMACOF algorithm.
    eps : float, default=1e-3
        Convergence tolerance.
    dissimilarity : {"euclidean", "precomputed"}, default="euclidean"
        Dissimilarity type.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    embedding_ : ndarray of shape (n_samples, n_components)
        Stores the embedding.
    stress_ : float
        Final value of the stress.
    dissimilarity_matrix_ : ndarray of shape (n_samples, n_samples)
        Pairwise dissimilarities.
    n_iter_ : int
        Number of iterations.

    Examples
    --------
    >>> from nalyst.manifold import MDS
    >>> X = np.random.randn(100, 10)
    >>> mds = MDS(n_components=2)
    >>> X_embedded = mds.train_apply(X)
    """

    def __init__(
        self,
        n_components: int = 2,
        *,
        metric: bool = True,
        n_init: int = 4,
        max_iter: int = 300,
        eps: float = 1e-3,
        dissimilarity: Literal["euclidean", "precomputed"] = "euclidean",
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.metric = metric
        self.n_init = n_init
        self.max_iter = max_iter
        self.eps = eps
        self.dissimilarity = dissimilarity
        self.random_state = random_state

    def train_apply(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit and transform X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features) or (n_samples, n_samples)
            Input data or precomputed dissimilarity matrix.
        y : ignored

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Embedding.
        """
        X = check_array(X)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Compute dissimilarity matrix
        if self.dissimilarity == "precomputed":
            self.dissimilarity_matrix_ = X
        else:
            self.dissimilarity_matrix_ = squareform(pdist(X))

        n_samples = self.dissimilarity_matrix_.shape[0]

        best_stress = float('inf')
        best_embedding = None

        for _ in range(self.n_init):
            # Initialize
            embedding = np.random.randn(n_samples, self.n_components)

            if self.metric:
                embedding, stress, n_iter = self._smacof_single(
                    self.dissimilarity_matrix_, embedding
                )
            else:
                embedding, stress, n_iter = self._smacof_nonmetric(
                    self.dissimilarity_matrix_, embedding
                )

            if stress < best_stress:
                best_stress = stress
                best_embedding = embedding
                self.n_iter_ = n_iter

        self.embedding_ = best_embedding
        self.stress_ = best_stress

        return self.embedding_

    def _smacof_single(
        self,
        dissimilarities: np.ndarray,
        X: np.ndarray,
    ) -> tuple:
        """SMACOF algorithm for metric MDS."""
        n_samples = dissimilarities.shape[0]

        old_stress = None

        for n_iter in range(self.max_iter):
            # Compute distances in embedding space
            distances = squareform(pdist(X))

            # Compute stress
            stress = np.sum((dissimilarities - distances) ** 2)

            if old_stress is not None:
                if abs(old_stress - stress) < self.eps:
                    break
            old_stress = stress

            # Compute ratio
            with np.errstate(divide='ignore', invalid='ignore'):
                ratio = dissimilarities / (distances + 1e-10)
            ratio[np.isnan(ratio)] = 0

            # Update positions
            B = -ratio
            B[np.arange(n_samples), np.arange(n_samples)] = -B.sum(axis=1)

            X = np.dot(B, X) / n_samples

        return X, stress, n_iter + 1

    def _smacof_nonmetric(
        self,
        dissimilarities: np.ndarray,
        X: np.ndarray,
    ) -> tuple:
        """Non-metric MDS using isotonic regression."""
        n_samples = dissimilarities.shape[0]

        # Flatten and sort dissimilarities
        triu_idx = np.triu_indices(n_samples, k=1)
        dissim_flat = dissimilarities[triu_idx]
        sort_idx = np.argsort(dissim_flat)

        old_stress = None

        for n_iter in range(self.max_iter):
            # Compute distances in embedding space
            distances = squareform(pdist(X))
            dist_flat = distances[triu_idx]

            # Isotonic regression (PAVA algorithm)
            disparities = self._isotonic_regression(dissim_flat[sort_idx], dist_flat[sort_idx])

            # Unsort
            disparities_unsorted = np.zeros_like(disparities)
            disparities_unsorted[sort_idx] = disparities

            # Reconstruct matrix
            D = np.zeros((n_samples, n_samples))
            D[triu_idx] = disparities_unsorted
            D = D + D.T

            # Compute stress
            stress = np.sum((D - distances) ** 2)

            if old_stress is not None:
                if abs(old_stress - stress) < self.eps:
                    break
            old_stress = stress

            # Update positions
            with np.errstate(divide='ignore', invalid='ignore'):
                ratio = D / (distances + 1e-10)
            ratio[np.isnan(ratio)] = 0

            B = -ratio
            B[np.arange(n_samples), np.arange(n_samples)] = -B.sum(axis=1)

            X = np.dot(B, X) / n_samples

        return X, stress, n_iter + 1

    def _isotonic_regression(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Pool Adjacent Violators Algorithm (PAVA)."""
        n = len(y)
        result = y.copy()

        while True:
            changed = False
            i = 0
            while i < n - 1:
                if result[i] > result[i + 1]:
                    # Pool blocks
                    j = i + 1
                    while j < n and result[i] > result[j]:
                        j += 1

                    # Replace with mean
                    pool_mean = np.mean(result[i:j])
                    result[i:j] = pool_mean
                    changed = True
                    i = j
                else:
                    i += 1

            if not changed:
                break

        return result

    def train(self, X: np.ndarray, y=None) -> "MDS":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.
        y : ignored

        Returns
        -------
        self : MDS
            Fitted estimator.
        """
        self.train_apply(X)
        return self
