"""
LIME-style model explanations.

Local Interpretable Model-agnostic Explanations.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Callable, Union
import numpy as np


class LimeTabularExplainer:
    """
    LIME explainer for tabular data.

    Explains predictions of any classifier/regressor by fitting
    a local interpretable model around the prediction.

    Parameters
    ----------
    training_data : ndarray of shape (n_samples, n_features)
        Training data for computing statistics.
    mode : str, default='classification'
        'classification' or 'regression'.
    feature_names : list of str, optional
        Names of features.
    categorical_features : list of int, optional
        Indices of categorical features.
    kernel_width : float, optional
        Width of exponential kernel. Default: sqrt(n_features) * 0.75.

    Examples
    --------
    >>> from nalyst.explainability import LimeTabularExplainer
    >>> explainer = LimeTabularExplainer(X_train, mode='classification')
    >>> explanation = explainer.explain_instance(x, model.predict_proba)
    """

    def __init__(
        self,
        training_data: np.ndarray,
        mode: str = 'classification',
        feature_names: Optional[List[str]] = None,
        categorical_features: Optional[List[int]] = None,
        kernel_width: Optional[float] = None,
    ):
        self.training_data = np.asarray(training_data)
        self.mode = mode

        n_features = self.training_data.shape[1]

        if feature_names is None:
            self.feature_names = [f"Feature {i}" for i in range(n_features)]
        else:
            self.feature_names = feature_names

        self.categorical_features = categorical_features or []

        if kernel_width is None:
            self.kernel_width = np.sqrt(n_features) * 0.75
        else:
            self.kernel_width = kernel_width

        # Compute statistics
        self.mean = np.mean(self.training_data, axis=0)
        self.std = np.std(self.training_data, axis=0) + 1e-10

        # For categorical features, compute unique values
        self.categorical_values = {}
        for idx in self.categorical_features:
            self.categorical_values[idx] = np.unique(self.training_data[:, idx])

    def explain_instance(
        self,
        instance: np.ndarray,
        predict_fn: Callable,
        num_features: int = 10,
        num_samples: int = 5000,
        labels: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Explain a single prediction.

        Parameters
        ----------
        instance : ndarray of shape (n_features,)
            Instance to explain.
        predict_fn : callable
            Prediction function. Should return probabilities for
            classification or predictions for regression.
        num_features : int, default=10
            Maximum number of features in explanation.
        num_samples : int, default=5000
            Number of samples for local approximation.
        labels : list of int, optional
            Labels to explain (for classification).

        Returns
        -------
        explanation : dict
            Explanation containing feature weights and local fidelity.
        """
        instance = np.asarray(instance).flatten()
        n_features = len(instance)

        # Generate perturbed samples
        perturbed = self._generate_samples(instance, num_samples)

        # Get predictions
        predictions = predict_fn(perturbed)

        if self.mode == 'classification':
            if predictions.ndim == 1:
                predictions = np.column_stack([1 - predictions, predictions])

            if labels is None:
                # Explain the predicted class
                orig_pred = predict_fn(instance.reshape(1, -1))
                if orig_pred.ndim > 1:
                    labels = [np.argmax(orig_pred[0])]
                else:
                    labels = [1 if orig_pred[0] > 0.5 else 0]
        else:
            predictions = predictions.reshape(-1, 1)
            labels = [0]

        # Compute distances and weights
        distances = self._compute_distances(perturbed, instance)
        weights = self._kernel(distances)

        # Create binary representation
        binary = self._to_binary(perturbed, instance)

        # Fit local linear model for each label
        explanations = {}

        for label in labels:
            y = predictions[:, label] if predictions.ndim > 1 else predictions.flatten()

            # Weighted ridge regression
            coef = self._fit_weighted_ridge(binary, y, weights)

            # Get top features
            abs_coef = np.abs(coef)
            top_indices = np.argsort(abs_coef)[::-1][:num_features]

            feature_weights = [
                (self.feature_names[i], coef[i], instance[i])
                for i in top_indices
            ]

            # Compute local fidelity (R)
            y_pred = binary @ coef
            ss_res = np.sum(weights * (y - y_pred) ** 2)
            ss_tot = np.sum(weights * (y - np.average(y, weights=weights)) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            explanations[label] = {
                'feature_weights': feature_weights,
                'local_r2': r2,
                'prediction': predictions[0, label] if predictions.ndim > 1 else predictions[0],
            }

        return {
            'instance': instance,
            'explanations': explanations,
            'mode': self.mode,
        }

    def _generate_samples(
        self,
        instance: np.ndarray,
        num_samples: int,
    ) -> np.ndarray:
        """Generate perturbed samples around instance."""
        n_features = len(instance)

        # Sample from normal distribution centered at instance
        samples = np.random.normal(0, 1, size=(num_samples, n_features))
        samples = samples * self.std + instance

        # Include original instance
        samples[0] = instance

        # Handle categorical features
        for idx in self.categorical_features:
            values = self.categorical_values[idx]
            samples[:, idx] = np.random.choice(values, num_samples)
            samples[0, idx] = instance[idx]

        return samples

    def _compute_distances(
        self,
        perturbed: np.ndarray,
        instance: np.ndarray,
    ) -> np.ndarray:
        """Compute scaled Euclidean distances."""
        scaled = (perturbed - instance) / self.std
        distances = np.sqrt(np.sum(scaled ** 2, axis=1))
        return distances

    def _kernel(self, distances: np.ndarray) -> np.ndarray:
        """Exponential kernel."""
        return np.exp(-(distances ** 2) / (2 * self.kernel_width ** 2))

    def _to_binary(
        self,
        perturbed: np.ndarray,
        instance: np.ndarray,
    ) -> np.ndarray:
        """Convert to binary representation (feature on/off)."""
        n_samples, n_features = perturbed.shape
        binary = np.zeros((n_samples, n_features))

        for j in range(n_features):
            if j in self.categorical_features:
                binary[:, j] = (perturbed[:, j] == instance[j]).astype(float)
            else:
                # Within 1 std of instance value
                threshold = self.std[j]
                binary[:, j] = (np.abs(perturbed[:, j] - instance[j]) < threshold).astype(float)

        return binary

    def _fit_weighted_ridge(
        self,
        X: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
        alpha: float = 1.0,
    ) -> np.ndarray:
        """Fit weighted ridge regression."""
        n_samples, n_features = X.shape

        W = np.diag(np.sqrt(weights))
        X_w = W @ X
        y_w = W @ y

        # Ridge regression
        XtX = X_w.T @ X_w + alpha * np.eye(n_features)
        Xty = X_w.T @ y_w

        try:
            coef = np.linalg.solve(XtX, Xty)
        except np.linalg.LinAlgError:
            coef = np.zeros(n_features)

        return coef


class LimeTextExplainer:
    """
    LIME explainer for text data.

    Explains predictions by identifying important words.

    Parameters
    ----------
    class_names : list of str, optional
        Names of classes.
    kernel_width : int, default=25
        Kernel width for word distance.

    Examples
    --------
    >>> from nalyst.explainability import LimeTextExplainer
    >>> explainer = LimeTextExplainer(class_names=['negative', 'positive'])
    >>> explanation = explainer.explain_instance(text, model.predict_proba)
    """

    def __init__(
        self,
        class_names: Optional[List[str]] = None,
        kernel_width: int = 25,
    ):
        self.class_names = class_names
        self.kernel_width = kernel_width

    def explain_instance(
        self,
        text: str,
        predict_fn: Callable,
        num_features: int = 10,
        num_samples: int = 5000,
        labels: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Explain a text prediction.

        Parameters
        ----------
        text : str
            Text to explain.
        predict_fn : callable
            Prediction function that takes list of texts.
        num_features : int, default=10
            Number of top features to return.
        num_samples : int, default=5000
            Number of samples.
        labels : list of int, optional
            Labels to explain.

        Returns
        -------
        explanation : dict
            Word importance explanation.
        """
        # Tokenize
        words = text.split()
        n_words = len(words)

        if n_words == 0:
            return {'error': 'Empty text'}

        # Generate samples by masking words
        binary = np.ones((num_samples, n_words))

        for i in range(1, num_samples):
            n_mask = np.random.randint(1, max(2, n_words))
            mask_idx = np.random.choice(n_words, n_mask, replace=False)
            binary[i, mask_idx] = 0

        # Create masked texts
        masked_texts = []
        for i in range(num_samples):
            masked = [w for j, w in enumerate(words) if binary[i, j] == 1]
            masked_texts.append(' '.join(masked) if masked else text)

        # Get predictions
        predictions = predict_fn(masked_texts)

        if predictions.ndim == 1:
            predictions = np.column_stack([1 - predictions, predictions])

        if labels is None:
            labels = [np.argmax(predictions[0])]

        # Compute weights (number of words present)
        n_present = np.sum(binary, axis=1)
        distances = (n_words - n_present) / n_words
        weights = np.exp(-(distances ** 2) / (2 * self.kernel_width ** 2))

        explanations = {}

        for label in labels:
            y = predictions[:, label]

            # Weighted ridge regression
            coef = self._fit_weighted_ridge(binary, y, weights)

            # Get top words
            abs_coef = np.abs(coef)
            top_indices = np.argsort(abs_coef)[::-1][:num_features]

            word_weights = [
                (words[i], coef[i])
                for i in top_indices
            ]

            label_name = self.class_names[label] if self.class_names else str(label)
            explanations[label_name] = {
                'word_weights': word_weights,
                'prediction': predictions[0, label],
            }

        return {
            'text': text,
            'explanations': explanations,
        }

    def _fit_weighted_ridge(
        self,
        X: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
        alpha: float = 1.0,
    ) -> np.ndarray:
        """Fit weighted ridge regression."""
        n_samples, n_features = X.shape

        W = np.diag(np.sqrt(weights))
        X_w = W @ X
        y_w = W @ y

        XtX = X_w.T @ X_w + alpha * np.eye(n_features)
        Xty = X_w.T @ y_w

        try:
            coef = np.linalg.solve(XtX, Xty)
        except np.linalg.LinAlgError:
            coef = np.zeros(n_features)

        return coef
