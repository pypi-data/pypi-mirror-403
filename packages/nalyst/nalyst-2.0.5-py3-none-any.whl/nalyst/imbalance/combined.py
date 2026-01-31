"""
Combined over- and under-sampling techniques.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union
import numpy as np

from nalyst.imbalance.oversampling import BaseSampler, SMOTE
from nalyst.imbalance.undersampling import TomekLinks, EditedNearestNeighbors


class SMOTETomek(BaseSampler):
    """
    SMOTE + Tomek Links.

    Applies SMOTE over-sampling followed by Tomek links under-sampling
    to clean the dataset.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        Sampling strategy for SMOTE.
    k_neighbors : int, default=5
        Number of neighbors for SMOTE.
    random_state : int, optional
        Random seed.

    References
    ----------
    Batista, G. E., et al. "A Study of the Behavior of Several Methods
    for Balancing Machine Learning Training Data." ACM SIGKDD (2004).

    Examples
    --------
    >>> smotetomek = SMOTETomek(k_neighbors=5, random_state=42)
    >>> X_resampled, y_resampled = smotetomek.resample(X, y)
    """

    def __init__(
        self,
        sampling_strategy: Union[float, str] = 'auto',
        k_neighbors: int = 5,
        random_state: Optional[int] = None,
    ):
        super().__init__(random_state)
        self.sampling_strategy = sampling_strategy
        self.k_neighbors = k_neighbors

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resample using SMOTE + Tomek Links.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature matrix.
        y : ndarray of shape (n_samples,)
            Target labels.

        Returns
        -------
        X_resampled : ndarray
            Resampled feature matrix.
        y_resampled : ndarray
            Resampled labels.
        """
        X, y = self._check_input(X, y)

        # Step 1: Apply SMOTE
        smote = SMOTE(
            sampling_strategy=self.sampling_strategy,
            k_neighbors=self.k_neighbors,
            random_state=self.random_state,
        )
        X_smote, y_smote = smote.resample(X, y)

        # Step 2: Apply Tomek Links
        tomek = TomekLinks(random_state=self.random_state)
        X_final, y_final = tomek.resample(X_smote, y_smote)

        return X_final, y_final


class SMOTEENN(BaseSampler):
    """
    SMOTE + Edited Nearest Neighbors.

    Applies SMOTE over-sampling followed by ENN under-sampling
    to remove noisy samples.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        Sampling strategy for SMOTE.
    k_neighbors_smote : int, default=5
        Number of neighbors for SMOTE.
    n_neighbors_enn : int, default=3
        Number of neighbors for ENN.
    random_state : int, optional
        Random seed.

    References
    ----------
    Batista, G. E., et al. "A Study of the Behavior of Several Methods
    for Balancing Machine Learning Training Data." ACM SIGKDD (2004).

    Examples
    --------
    >>> smoteenn = SMOTEENN(k_neighbors_smote=5, random_state=42)
    >>> X_resampled, y_resampled = smoteenn.resample(X, y)
    """

    def __init__(
        self,
        sampling_strategy: Union[float, str] = 'auto',
        k_neighbors_smote: int = 5,
        n_neighbors_enn: int = 3,
        random_state: Optional[int] = None,
    ):
        super().__init__(random_state)
        self.sampling_strategy = sampling_strategy
        self.k_neighbors_smote = k_neighbors_smote
        self.n_neighbors_enn = n_neighbors_enn

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resample using SMOTE + ENN.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature matrix.
        y : ndarray of shape (n_samples,)
            Target labels.

        Returns
        -------
        X_resampled : ndarray
            Resampled feature matrix.
        y_resampled : ndarray
            Resampled labels.
        """
        X, y = self._check_input(X, y)

        # Step 1: Apply SMOTE
        smote = SMOTE(
            sampling_strategy=self.sampling_strategy,
            k_neighbors=self.k_neighbors_smote,
            random_state=self.random_state,
        )
        X_smote, y_smote = smote.resample(X, y)

        # Step 2: Apply ENN
        enn = EditedNearestNeighbors(
            n_neighbors=self.n_neighbors_enn,
            random_state=self.random_state,
        )
        X_final, y_final = enn.resample(X_smote, y_smote)

        return X_final, y_final
