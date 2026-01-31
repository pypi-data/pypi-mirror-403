"""
Nearest neighbors regression.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import RegressorMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.learners.neighbors.base import (
    NeighborsBase,
    KNeighborsMixin,
    RadiusNeighborsMixin,
)


class KNeighborsRegressor(KNeighborsMixin, RegressorMixin, NeighborsBase):
    """
    K-Nearest Neighbors Regressor.

    Predicts target based on the mean (or weighted mean) of k nearest neighbors.

    Parameters
    ----------
    n_neighbors : int, default=5
        Number of neighbors to use.
    weights : {"uniform", "distance"}, default="uniform"
        Weight function used in prediction.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm used to compute nearest neighbors.
    leaf_size : int, default=30
        Leaf size for tree algorithms.
    p : int, default=2
        Power parameter for Minkowski metric.
    metric : str, default="minkowski"
        Distance metric.
    n_jobs : int, optional
        Number of parallel jobs.

    Attributes
    ----------
    n_samples_fit_ : int
        Number of samples in the fitted data.

    Examples
    --------
    >>> from nalyst.learners.neighbors import KNeighborsRegressor
    >>> X = [[0, 0], [1, 1], [2, 2], [3, 3]]
    >>> y = [0, 1, 2, 3]
    >>> reg = KNeighborsRegressor(n_neighbors=2)
    >>> reg.train(X, y)
    KNeighborsRegressor(n_neighbors=2)
    >>> reg.infer([[1.5, 1.5]])
    array([1.5])
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        *,
        weights: Literal["uniform", "distance"] = "uniform",
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        p: int = 2,
        metric: str = "minkowski",
        n_jobs: Optional[int] = None,
    ):
        super().__init__(
            n_neighbors=n_neighbors,
            algorithm=algorithm,
            leaf_size=leaf_size,
            p=p,
            metric=metric,
            n_jobs=n_jobs,
        )
        self.weights = weights

    def train(self, X: np.ndarray, y: np.ndarray) -> "KNeighborsRegressor":
        """
        Fit the k-nearest neighbors regressor.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,) or (n_samples, n_outputs)
            Target values.

        Returns
        -------
        self : KNeighborsRegressor
            Fitted regressor.
        """
        X, y = self._validate_data(X, y)

        self._train_X = X
        self._train_y = np.asarray(y)
        self.n_samples_fit_ = len(X)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values for the provided data.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Test samples.

        Returns
        -------
        y : ndarray of shape (n_queries,) or (n_queries, n_outputs)
            Predicted values.
        """
        check_is_trained(self, "_train_X")
        X = check_array(X)

        neigh_dist, neigh_ind = self._kneighbors(X, self.n_neighbors, return_distance=True)

        if self._train_y.ndim == 1:
            y_pred = np.zeros(len(X))
        else:
            y_pred = np.zeros((len(X), self._train_y.shape[1]))

        for i in range(len(X)):
            neighbor_values = self._train_y[neigh_ind[i]]

            if self.weights == "uniform":
                y_pred[i] = np.mean(neighbor_values, axis=0)
            else:
                weights = 1.0 / (neigh_dist[i] + 1e-10)
                weights = weights / weights.sum()
                if neighbor_values.ndim == 1:
                    y_pred[i] = np.sum(weights * neighbor_values)
                else:
                    y_pred[i] = np.sum(weights[:, np.newaxis] * neighbor_values, axis=0)

        return y_pred


class RadiusNeighborsRegressor(RadiusNeighborsMixin, RegressorMixin, NeighborsBase):
    """
    Radius-based Neighbors Regressor.

    Predicts based on neighbors within a fixed radius.

    Parameters
    ----------
    radius : float, default=1.0
        Range of parameter space.
    weights : {"uniform", "distance"}, default="uniform"
        Weight function.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm for nearest neighbors.
    leaf_size : int, default=30
        Leaf size for tree algorithms.
    p : int, default=2
        Power parameter for Minkowski metric.
    metric : str, default="minkowski"
        Distance metric.
    n_jobs : int, optional
        Number of parallel jobs.

    Examples
    --------
    >>> from nalyst.learners.neighbors import RadiusNeighborsRegressor
    >>> X = [[0, 0], [1, 1], [2, 2]]
    >>> y = [0, 1, 2]
    >>> reg = RadiusNeighborsRegressor(radius=1.5)
    >>> reg.train(X, y)
    RadiusNeighborsRegressor(radius=1.5)
    """

    def __init__(
        self,
        radius: float = 1.0,
        *,
        weights: Literal["uniform", "distance"] = "uniform",
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        p: int = 2,
        metric: str = "minkowski",
        n_jobs: Optional[int] = None,
    ):
        super().__init__(
            radius=radius,
            algorithm=algorithm,
            leaf_size=leaf_size,
            p=p,
            metric=metric,
            n_jobs=n_jobs,
        )
        self.weights = weights

    def train(self, X: np.ndarray, y: np.ndarray) -> "RadiusNeighborsRegressor":
        """
        Fit the radius neighbors regressor.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,) or (n_samples, n_outputs)
            Target values.

        Returns
        -------
        self : RadiusNeighborsRegressor
            Fitted regressor.
        """
        X, y = self._validate_data(X, y)

        self._train_X = X
        self._train_y = np.asarray(y)
        self.n_samples_fit_ = len(X)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Test samples.

        Returns
        -------
        y : ndarray
            Predicted values.
        """
        check_is_trained(self, "_train_X")
        X = check_array(X)

        neigh_dist, neigh_ind = self._radius_neighbors(X, self.radius, return_distance=True)

        if self._train_y.ndim == 1:
            y_pred = np.zeros(len(X))
        else:
            y_pred = np.zeros((len(X), self._train_y.shape[1]))

        for i in range(len(X)):
            if len(neigh_ind[i]) == 0:
                y_pred[i] = np.nan
                continue

            neighbor_values = self._train_y[neigh_ind[i]]

            if self.weights == "uniform":
                y_pred[i] = np.mean(neighbor_values, axis=0)
            else:
                weights = 1.0 / (neigh_dist[i] + 1e-10)
                weights = weights / weights.sum()
                if neighbor_values.ndim == 1:
                    y_pred[i] = np.sum(weights * neighbor_values)
                else:
                    y_pred[i] = np.sum(weights[:, np.newaxis] * neighbor_values, axis=0)

        return y_pred
