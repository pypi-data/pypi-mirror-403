"""
Over-sampling techniques for imbalanced datasets.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
import numpy as np


class BaseSampler(ABC):
    """Base class for all samplers."""

    def __init__(self, random_state: Optional[int] = None):
        self.random_state = random_state

    @abstractmethod
    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Resample the dataset."""
        pass

    def _check_input(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Validate input."""
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        if len(X) != len(y):
            raise ValueError("X and y must have same number of samples")

        return X, y


class RandomOverSampler(BaseSampler):
    """
    Random over-sampling of minority class.

    Randomly duplicates samples from minority class to balance dataset.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        If float, ratio of minority to majority after resampling.
        If 'auto', balance all classes to majority class size.
    random_state : int, optional
        Random seed for reproducibility.

    Examples
    --------
    >>> ros = RandomOverSampler(random_state=42)
    >>> X_resampled, y_resampled = ros.resample(X, y)
    """

    def __init__(
        self,
        sampling_strategy: Union[float, str] = 'auto',
        random_state: Optional[int] = None,
    ):
        super().__init__(random_state)
        self.sampling_strategy = sampling_strategy

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resample the dataset.

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

        if self.random_state is not None:
            np.random.seed(self.random_state)

        classes, counts = np.unique(y, return_counts=True)
        max_count = np.max(counts)

        X_resampled = [X]
        y_resampled = [y]

        for cls, count in zip(classes, counts):
            if count < max_count:
                # Number to generate
                if self.sampling_strategy == 'auto':
                    n_samples = max_count - count
                else:
                    target_count = int(max_count * self.sampling_strategy)
                    n_samples = max(0, target_count - count)

                # Sample with replacement
                class_indices = np.where(y == cls)[0]
                sampled_indices = np.random.choice(
                    class_indices, size=n_samples, replace=True
                )

                X_resampled.append(X[sampled_indices])
                y_resampled.append(np.full(n_samples, cls))

        return np.vstack(X_resampled), np.concatenate(y_resampled)


class SMOTE(BaseSampler):
    """
    Synthetic Minority Over-sampling Technique (SMOTE).

    Generates synthetic samples by interpolating between minority
    class samples and their k-nearest neighbors.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        Sampling strategy.
    k_neighbors : int, default=5
        Number of nearest neighbors to use.
    random_state : int, optional
        Random seed.

    References
    ----------
    Chawla, N. V., et al. "SMOTE: Synthetic Minority Over-sampling
    Technique." JAIR 16 (2002): 321-357.

    Examples
    --------
    >>> smote = SMOTE(k_neighbors=5, random_state=42)
    >>> X_resampled, y_resampled = smote.resample(X, y)
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
        Resample using SMOTE.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature matrix.
        y : ndarray of shape (n_samples,)
            Target labels.

        Returns
        -------
        X_resampled : ndarray
            Resampled feature matrix with synthetic samples.
        y_resampled : ndarray
            Resampled labels.
        """
        X, y = self._check_input(X, y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        classes, counts = np.unique(y, return_counts=True)
        max_count = np.max(counts)

        X_resampled = [X]
        y_resampled = [y]

        for cls, count in zip(classes, counts):
            if count < max_count:
                n_samples = max_count - count

                # Get minority class samples
                minority_indices = np.where(y == cls)[0]
                minority_X = X[minority_indices]

                # Generate synthetic samples
                synthetic = self._generate_synthetic(
                    minority_X, n_samples
                )

                X_resampled.append(synthetic)
                y_resampled.append(np.full(n_samples, cls))

        return np.vstack(X_resampled), np.concatenate(y_resampled)

    def _generate_synthetic(
        self,
        minority_X: np.ndarray,
        n_samples: int,
    ) -> np.ndarray:
        """Generate synthetic samples using SMOTE."""
        n_minority = len(minority_X)
        k = min(self.k_neighbors, n_minority - 1)

        if k < 1:
            # Not enough neighbors, use random oversampling
            indices = np.random.choice(n_minority, size=n_samples, replace=True)
            return minority_X[indices]

        synthetic = []

        for _ in range(n_samples):
            # Select random minority sample
            idx = np.random.randint(0, n_minority)
            sample = minority_X[idx]

            # Find k-nearest neighbors
            distances = np.linalg.norm(minority_X - sample, axis=1)
            neighbor_indices = np.argsort(distances)[1:k+1]

            # Select random neighbor
            neighbor_idx = np.random.choice(neighbor_indices)
            neighbor = minority_X[neighbor_idx]

            # Generate synthetic sample between sample and neighbor
            alpha = np.random.random()
            new_sample = sample + alpha * (neighbor - sample)
            synthetic.append(new_sample)

        return np.array(synthetic)


class ADASYN(BaseSampler):
    """
    Adaptive Synthetic Sampling (ADASYN).

    Similar to SMOTE but generates more synthetic samples in regions
    where minority class density is low.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        Sampling strategy.
    k_neighbors : int, default=5
        Number of nearest neighbors.
    random_state : int, optional
        Random seed.

    References
    ----------
    He, H., et al. "ADASYN: Adaptive Synthetic Sampling Approach for
    Imbalanced Learning." IEEE IJCNN (2008).

    Examples
    --------
    >>> adasyn = ADASYN(k_neighbors=5, random_state=42)
    >>> X_resampled, y_resampled = adasyn.resample(X, y)
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
        Resample using ADASYN.
        """
        X, y = self._check_input(X, y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        classes, counts = np.unique(y, return_counts=True)
        max_count = np.max(counts)
        minority_class = classes[np.argmin(counts)]

        minority_indices = np.where(y == minority_class)[0]
        minority_X = X[minority_indices]
        n_minority = len(minority_X)

        n_generate = max_count - n_minority

        if n_generate <= 0:
            return X, y

        k = min(self.k_neighbors, len(X) - 1)

        # Calculate density ratio for each minority sample
        ratios = []
        for i, sample in enumerate(minority_X):
            distances = np.linalg.norm(X - sample, axis=1)
            neighbor_indices = np.argsort(distances)[1:k+1]

            # Ratio of majority class neighbors
            n_majority_neighbors = np.sum(y[neighbor_indices] != minority_class)
            ratios.append(n_majority_neighbors / k)

        ratios = np.array(ratios)

        # Normalize ratios to get distribution
        if np.sum(ratios) > 0:
            probs = ratios / np.sum(ratios)
        else:
            probs = np.ones(n_minority) / n_minority

        # Generate samples based on distribution
        samples_per_point = np.round(probs * n_generate).astype(int)

        # Adjust to match exact count
        diff = n_generate - np.sum(samples_per_point)
        if diff > 0:
            for _ in range(diff):
                idx = np.random.choice(n_minority)
                samples_per_point[idx] += 1
        elif diff < 0:
            for _ in range(-diff):
                pos = samples_per_point > 0
                if np.any(pos):
                    idx = np.random.choice(np.where(pos)[0])
                    samples_per_point[idx] -= 1

        # Generate synthetic samples
        synthetic = []
        for i, n_samples in enumerate(samples_per_point):
            if n_samples <= 0:
                continue

            sample = minority_X[i]

            # Find k-nearest minority neighbors
            distances = np.linalg.norm(minority_X - sample, axis=1)
            neighbor_indices = np.argsort(distances)[1:min(k+1, n_minority)]

            if len(neighbor_indices) == 0:
                continue

            for _ in range(n_samples):
                neighbor_idx = np.random.choice(neighbor_indices)
                neighbor = minority_X[neighbor_idx]

                alpha = np.random.random()
                new_sample = sample + alpha * (neighbor - sample)
                synthetic.append(new_sample)

        if synthetic:
            synthetic = np.array(synthetic)
            X_resampled = np.vstack([X, synthetic])
            y_resampled = np.concatenate([y, np.full(len(synthetic), minority_class)])
        else:
            X_resampled, y_resampled = X, y

        return X_resampled, y_resampled


class BorderlineSMOTE(BaseSampler):
    """
    Borderline-SMOTE.

    Only generates synthetic samples from minority samples that are
    near the decision boundary.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        Sampling strategy.
    k_neighbors : int, default=5
        Number of nearest neighbors.
    m_neighbors : int, default=10
        Number of neighbors to determine if borderline.
    random_state : int, optional
        Random seed.

    References
    ----------
    Han, H., et al. "Borderline-SMOTE: A New Over-Sampling Method in
    Imbalanced Data Sets Learning." ICIC (2005).

    Examples
    --------
    >>> bsmote = BorderlineSMOTE(k_neighbors=5, random_state=42)
    >>> X_resampled, y_resampled = bsmote.resample(X, y)
    """

    def __init__(
        self,
        sampling_strategy: Union[float, str] = 'auto',
        k_neighbors: int = 5,
        m_neighbors: int = 10,
        random_state: Optional[int] = None,
    ):
        super().__init__(random_state)
        self.sampling_strategy = sampling_strategy
        self.k_neighbors = k_neighbors
        self.m_neighbors = m_neighbors

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resample using Borderline-SMOTE.
        """
        X, y = self._check_input(X, y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        classes, counts = np.unique(y, return_counts=True)
        max_count = np.max(counts)
        minority_class = classes[np.argmin(counts)]

        minority_indices = np.where(y == minority_class)[0]
        minority_X = X[minority_indices]
        n_minority = len(minority_X)

        n_generate = max_count - n_minority

        if n_generate <= 0:
            return X, y

        m = min(self.m_neighbors, len(X) - 1)

        # Find borderline samples
        borderline_indices = []
        for i, sample in enumerate(minority_X):
            distances = np.linalg.norm(X - sample, axis=1)
            neighbor_indices = np.argsort(distances)[1:m+1]

            n_majority = np.sum(y[neighbor_indices] != minority_class)

            # Borderline if half or more neighbors are majority
            if m / 2 <= n_majority < m:
                borderline_indices.append(i)

        if len(borderline_indices) == 0:
            # Fall back to regular SMOTE
            smote = SMOTE(
                k_neighbors=self.k_neighbors,
                random_state=self.random_state
            )
            return smote.resample(X, y)

        borderline_X = minority_X[borderline_indices]

        # Generate from borderline samples only
        k = min(self.k_neighbors, n_minority - 1)

        synthetic = []
        samples_per_point = n_generate // len(borderline_indices)
        extra = n_generate % len(borderline_indices)

        for i, sample in enumerate(borderline_X):
            n_samples = samples_per_point + (1 if i < extra else 0)

            # Find k-nearest minority neighbors
            distances = np.linalg.norm(minority_X - sample, axis=1)
            neighbor_indices = np.argsort(distances)[1:k+1]

            for _ in range(n_samples):
                neighbor_idx = np.random.choice(neighbor_indices)
                neighbor = minority_X[neighbor_idx]

                alpha = np.random.random()
                new_sample = sample + alpha * (neighbor - sample)
                synthetic.append(new_sample)

        synthetic = np.array(synthetic)
        X_resampled = np.vstack([X, synthetic])
        y_resampled = np.concatenate([y, np.full(len(synthetic), minority_class)])

        return X_resampled, y_resampled
