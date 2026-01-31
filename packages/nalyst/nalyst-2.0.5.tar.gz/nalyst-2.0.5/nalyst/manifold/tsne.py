"""
t-Distributed Stochastic Neighbor Embedding (t-SNE).
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy.spatial.distance import pdist, squareform

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array


class TSNE(BaseLearner):
    """
    t-Distributed Stochastic Neighbor Embedding.

    Non-linear dimensionality reduction suitable for visualization.

    Parameters
    ----------
    n_components : int, default=2
        Dimension of the embedded space.
    perplexity : float, default=30.0
        Related to the number of nearest neighbors.
    early_exaggeration : float, default=12.0
        Controls tightness of clusters in early iterations.
    learning_rate : float, default=200.0
        Learning rate for optimization.
    n_iter : int, default=1000
        Maximum number of iterations.
    n_iter_without_progress : int, default=300
        Early stopping threshold.
    min_grad_norm : float, default=1e-7
        Minimum gradient norm for convergence.
    metric : str, default="euclidean"
        Distance metric.
    init : {"random", "pca"}, default="random"
        Initialization method.
    random_state : int, optional
        Random seed.
    method : {"barnes_hut", "exact"}, default="barnes_hut"
        Gradient computation method.
    angle : float, default=0.5
        Trade-off for Barnes-Hut approximation.

    Attributes
    ----------
    embedding_ : ndarray of shape (n_samples, n_components)
        Stores the embedding vectors.
    kl_divergence_ : float
        Kullback-Leibler divergence after optimization.
    n_iter_ : int
        Number of iterations run.

    Examples
    --------
    >>> from nalyst.manifold import TSNE
    >>> X = np.random.randn(100, 10)
    >>> tsne = TSNE(n_components=2)
    >>> X_embedded = tsne.train_apply(X)
    >>> X_embedded.shape
    (100, 2)
    """

    def __init__(
        self,
        n_components: int = 2,
        *,
        perplexity: float = 30.0,
        early_exaggeration: float = 12.0,
        learning_rate: float = 200.0,
        n_iter: int = 1000,
        n_iter_without_progress: int = 300,
        min_grad_norm: float = 1e-7,
        metric: str = "euclidean",
        init: Literal["random", "pca"] = "random",
        random_state: Optional[int] = None,
        method: Literal["barnes_hut", "exact"] = "exact",
        angle: float = 0.5,
    ):
        self.n_components = n_components
        self.perplexity = perplexity
        self.early_exaggeration = early_exaggeration
        self.learning_rate = learning_rate
        self.n_iter = n_iter
        self.n_iter_without_progress = n_iter_without_progress
        self.min_grad_norm = min_grad_norm
        self.metric = metric
        self.init = init
        self.random_state = random_state
        self.method = method
        self.angle = angle

    def _compute_joint_probabilities(self, distances: np.ndarray) -> np.ndarray:
        """Compute joint probabilities p_ij from distances."""
        n_samples = distances.shape[0]

        # Compute conditional probabilities using binary search for sigma
        P = np.zeros((n_samples, n_samples))
        target_entropy = np.log(self.perplexity)

        for i in range(n_samples):
            # Binary search for sigma
            sigma_min, sigma_max = 1e-10, 1e10
            sigma = 1.0

            for _ in range(50):  # Max iterations for binary search
                # Compute probabilities
                exp_dist = np.exp(-distances[i] / (2 * sigma ** 2))
                exp_dist[i] = 0
                sum_exp = np.sum(exp_dist)

                if sum_exp < 1e-10:
                    p_i = np.zeros(n_samples)
                else:
                    p_i = exp_dist / sum_exp

                # Compute entropy
                entropy = -np.sum(p_i * np.log(p_i + 1e-10))

                if abs(entropy - target_entropy) < 1e-5:
                    break

                if entropy > target_entropy:
                    sigma_max = sigma
                else:
                    sigma_min = sigma

                sigma = (sigma_min + sigma_max) / 2

            P[i] = p_i

        # Make symmetric and normalize
        P = (P + P.T) / (2 * n_samples)
        P = np.maximum(P, 1e-12)

        return P

    def _compute_gradient(self, Y: np.ndarray, P: np.ndarray, Q: np.ndarray) -> np.ndarray:
        """Compute t-SNE gradient."""
        n_samples = Y.shape[0]

        # Compute pairwise affinities
        pq_diff = P - Q

        # Compute distances in low-dim space
        Y_diff = Y[:, np.newaxis, :] - Y[np.newaxis, :, :]
        dist_sq = np.sum(Y_diff ** 2, axis=2)

        # Gradient
        inv_dist = 1.0 / (1.0 + dist_sq)
        grad = 4 * np.sum(
            (pq_diff * inv_dist)[:, :, np.newaxis] * Y_diff, axis=1
        )

        return grad

    def train_apply(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit X into an embedded space and return that embedding.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.
        y : ignored

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Embedding of X.
        """
        X = check_array(X)
        n_samples = X.shape[0]

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Compute pairwise distances
        distances = squareform(pdist(X, metric=self.metric)) ** 2

        # Compute joint probabilities
        P = self._compute_joint_probabilities(distances)

        # Initialize embedding
        if self.init == "pca":
            # Simple PCA initialization
            X_centered = X - np.mean(X, axis=0)
            _, _, Vt = np.linalg.svd(X_centered, full_matrices=False)
            Y = np.dot(X_centered, Vt[:self.n_components].T)
            Y = Y * 0.0001
        else:
            Y = np.random.randn(n_samples, self.n_components) * 0.0001

        # Optimization
        velocity = np.zeros_like(Y)
        gains = np.ones_like(Y)

        best_error = float('inf')
        best_iter = 0

        for iteration in range(self.n_iter):
            # Early exaggeration
            if iteration < 250:
                P_used = P * self.early_exaggeration
            else:
                P_used = P

            # Compute low-dimensional affinities (Student-t with df=1)
            Y_diff = Y[:, np.newaxis, :] - Y[np.newaxis, :, :]
            dist_sq = np.sum(Y_diff ** 2, axis=2)
            Q = 1.0 / (1.0 + dist_sq)
            np.fill_diagonal(Q, 0)
            Q = Q / np.sum(Q)
            Q = np.maximum(Q, 1e-12)

            # Compute gradient
            grad = self._compute_gradient(Y, P_used, Q)

            # Update gains (adaptive learning rate)
            gains = (gains + 0.2) * ((grad > 0) != (velocity > 0)) + \
                    gains * 0.8 * ((grad > 0) == (velocity > 0))
            gains = np.maximum(gains, 0.01)

            # Update velocity and position
            velocity = 0.8 * velocity - self.learning_rate * gains * grad
            Y = Y + velocity

            # Center embedding
            Y = Y - np.mean(Y, axis=0)

            # Compute KL divergence
            error = np.sum(P_used * np.log(P_used / Q))

            if error < best_error:
                best_error = error
                best_iter = iteration
            elif iteration - best_iter > self.n_iter_without_progress:
                break

            if np.linalg.norm(grad) < self.min_grad_norm:
                break

        self.embedding_ = Y
        self.kl_divergence_ = error
        self.n_iter_ = iteration + 1

        return self.embedding_

    def train(self, X: np.ndarray, y=None) -> "TSNE":
        """
        Fit the model with X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.
        y : ignored

        Returns
        -------
        self : TSNE
            Fitted estimator.
        """
        self.train_apply(X)
        return self
