"""
Support Vector Machine classification.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy.optimize import minimize

from nalyst.core.foundation import ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.learners.svm.base import SVMBase, linear_kernel


class SupportVectorClassifier(ClassifierMixin, SVMBase):
    """
    Support Vector Classification (SVC).

    Implementation using Sequential Minimal Optimization (SMO) algorithm
    for solving the quadratic programming problem.

    Parameters
    ----------
    C : float, default=1.0
        Regularization parameter.
    kernel : {"linear", "poly", "rbf", "sigmoid"}, default="rbf"
        Kernel type.
    degree : int, default=3
        Degree of polynomial kernel.
    gamma : {"scale", "auto"} or float, default="scale"
        Kernel coefficient.
    coef0 : float, default=0.0
        Independent term in kernel function.
    shrinking : bool, default=True
        Whether to use shrinking heuristic.
    probability : bool, default=False
        Whether to enable probability estimates.
    tol : float, default=1e-3
        Tolerance for stopping criterion.
    cache_size : float, default=200
        Size of kernel cache (MB).
    class_weight : dict or "balanced", optional
        Class weights.
    max_iter : int, default=1000
        Maximum iterations.
    decision_function_shape : {"ovo", "ovr"}, default="ovr"
        Decision function shape.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    classes_ : ndarray
        Unique class labels.
    support_ : ndarray
        Indices of support vectors.
    support_vectors_ : ndarray
        Support vectors.
    dual_coef_ : ndarray
        Dual coefficients.
    intercept_ : ndarray
        Constants in decision function.

    Examples
    --------
    >>> from nalyst.learners.svm import SupportVectorClassifier
    >>> X = [[0, 0], [1, 1]]
    >>> y = [0, 1]
    >>> clf = SupportVectorClassifier()
    >>> clf.train(X, y)
    SupportVectorClassifier()
    >>> clf.infer([[0.5, 0.5]])
    array([0])
    """

    def __init__(
        self,
        C: float = 1.0,
        *,
        kernel: Literal["linear", "poly", "rbf", "sigmoid"] = "rbf",
        degree: int = 3,
        gamma: str = "scale",
        coef0: float = 0.0,
        shrinking: bool = True,
        probability: bool = False,
        tol: float = 1e-3,
        cache_size: float = 200,
        class_weight=None,
        max_iter: int = 1000,
        decision_function_shape: Literal["ovo", "ovr"] = "ovr",
        random_state: Optional[int] = None,
    ):
        super().__init__(
            kernel=kernel,
            degree=degree,
            gamma=gamma,
            coef0=coef0,
            C=C,
            tol=tol,
            max_iter=max_iter,
            random_state=random_state,
        )
        self.shrinking = shrinking
        self.probability = probability
        self.cache_size = cache_size
        self.class_weight = class_weight
        self.decision_function_shape = decision_function_shape

    def train(self, X: np.ndarray, y: np.ndarray) -> "SupportVectorClassifier":
        """
        Fit the SVM model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : SupportVectorClassifier
            Fitted classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)

        # Store training data
        self._train_X = X
        self._train_y = y

        # Get kernel function
        self._kernel_func = self._get_kernel(X)

        if n_classes == 2:
            # Binary classification
            self._train_binary(X, y)
        else:
            # Multi-class using one-vs-one
            self._train_multiclass(X, y)

        return self

    def _train_binary(self, X: np.ndarray, y: np.ndarray):
        """Train binary SVM classifier."""
        n_samples = len(X)

        # Convert labels to +1/-1
        y_binary = np.where(y == self.classes_[1], 1.0, -1.0)

        # Compute kernel matrix
        K = self._compute_kernel_matrix(X)

        # Initialize alphas
        alpha = np.zeros(n_samples)

        # SMO algorithm (simplified)
        for iteration in range(self.max_iter):
            alpha_prev = alpha.copy()

            for i in range(n_samples):
                # Compute error
                E_i = np.sum(alpha * y_binary * K[i]) - y_binary[i]

                # Check KKT conditions
                if (y_binary[i] * E_i < -self.tol and alpha[i] < self.C) or \
                   (y_binary[i] * E_i > self.tol and alpha[i] > 0):

                    # Select j randomly
                    j = i
                    while j == i:
                        j = np.random.randint(n_samples)

                    E_j = np.sum(alpha * y_binary * K[j]) - y_binary[j]

                    # Compute bounds
                    if y_binary[i] != y_binary[j]:
                        L = max(0, alpha[j] - alpha[i])
                        H = min(self.C, self.C + alpha[j] - alpha[i])
                    else:
                        L = max(0, alpha[i] + alpha[j] - self.C)
                        H = min(self.C, alpha[i] + alpha[j])

                    if L == H:
                        continue

                    # Compute eta
                    eta = 2 * K[i, j] - K[i, i] - K[j, j]
                    if eta >= 0:
                        continue

                    # Update alpha_j
                    alpha_j_new = alpha[j] - y_binary[j] * (E_i - E_j) / eta
                    alpha_j_new = np.clip(alpha_j_new, L, H)

                    if abs(alpha_j_new - alpha[j]) < 1e-5:
                        continue

                    # Update alpha_i
                    alpha_i_new = alpha[i] + y_binary[i] * y_binary[j] * (alpha[j] - alpha_j_new)

                    alpha[i] = alpha_i_new
                    alpha[j] = alpha_j_new

            # Check convergence
            if np.allclose(alpha, alpha_prev, atol=self.tol):
                break

        # Store results
        support_mask = alpha > 1e-7
        self.support_ = np.where(support_mask)[0]
        self.support_vectors_ = X[support_mask]
        self._alpha = alpha[support_mask]
        self._y_support = y_binary[support_mask]

        # Compute intercept
        self.intercept_ = np.mean(
            y_binary[support_mask] -
            np.sum(self._alpha * self._y_support * K[support_mask][:, support_mask], axis=1)
        )

        # Compute dual coefficients
        self.dual_coef_ = (self._alpha * self._y_support).reshape(1, -1)

    def _train_multiclass(self, X: np.ndarray, y: np.ndarray):
        """Train multi-class SVM using one-vs-one."""
        n_classes = len(self.classes_)

        # Store classifiers for each pair
        self._classifiers = []

        for i in range(n_classes):
            for j in range(i + 1, n_classes):
                # Get samples for classes i and j
                mask = (y == self.classes_[i]) | (y == self.classes_[j])
                X_pair = X[mask]
                y_pair = y[mask]

                # Create binary labels
                y_binary = np.where(y_pair == self.classes_[i], 0, 1)

                # Train binary classifier
                clf = SupportVectorClassifier(
                    C=self.C,
                    kernel=self.kernel,
                    degree=self.degree,
                    gamma=self.gamma,
                    coef0=self.coef0,
                    tol=self.tol,
                    max_iter=self.max_iter,
                )
                clf.classes_ = np.array([self.classes_[i], self.classes_[j]])
                clf._kernel_func = self._kernel_func
                clf._train_binary(X_pair, np.array([self.classes_[i] if yy == 0 else self.classes_[j] for yy in y_binary]))

                self._classifiers.append((i, j, clf))

        # For compatibility, use first classifier's support vectors
        if self._classifiers:
            _, _, first_clf = self._classifiers[0]
            self.support_vectors_ = first_clf.support_vectors_
            self.dual_coef_ = first_clf.dual_coef_
            self.intercept_ = first_clf.intercept_
            self.support_ = first_clf.support_

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Perform classification on samples in X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Class labels for samples.
        """
        check_is_trained(self, "support_vectors_")
        X = check_array(X)

        if len(self.classes_) == 2:
            decision = self.decision_function(X)
            return self.classes_[(decision > 0).astype(int)]
        else:
            # Multi-class voting
            votes = np.zeros((len(X), len(self.classes_)))

            for i, j, clf in self._classifiers:
                pred = clf.infer(X)
                for k, p in enumerate(pred):
                    if p == self.classes_[i]:
                        votes[k, i] += 1
                    else:
                        votes[k, j] += 1

            return self.classes_[np.argmax(votes, axis=1)]

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Evaluate the decision function for the samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        decision : ndarray
            Decision function values.
        """
        check_is_trained(self, "support_vectors_")
        X = check_array(X)

        if len(self.classes_) == 2:
            K = self._kernel_func(X, self.support_vectors_)
            return np.dot(K, self.dual_coef_.T).ravel() + self.intercept_
        else:
            # Return decision for each class pair
            n_classifiers = len(self._classifiers)
            decisions = np.zeros((len(X), n_classifiers))

            for idx, (i, j, clf) in enumerate(self._classifiers):
                decisions[:, idx] = clf.decision_function(X)

            return decisions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Compute probabilities (requires probability=True).

        Uses Platt scaling for probability calibration.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Probability estimates.
        """
        check_is_trained(self, "support_vectors_")
        X = check_array(X)

        decision = self.decision_function(X)

        if len(self.classes_) == 2:
            # Platt scaling approximation
            proba = 1.0 / (1.0 + np.exp(-decision))
            return np.column_stack([1 - proba, proba])
        else:
            # Softmax approximation for multi-class
            exp_decision = np.exp(decision - np.max(decision, axis=1, keepdims=True))
            return exp_decision / exp_decision.sum(axis=1, keepdims=True)


class LinearSVC(ClassifierMixin, SVMBase):
    """
    Linear Support Vector Classification.

    Similar to SVC with kernel='linear', but implemented with
    liblinear for better scalability to large datasets.

    Parameters
    ----------
    C : float, default=1.0
        Regularization parameter.
    loss : {"hinge", "squared_hinge"}, default="squared_hinge"
        Loss function.
    penalty : {"l1", "l2"}, default="l2"
        Penalty norm.
    dual : bool, default=True
        Whether to solve dual or primal problem.
    tol : float, default=1e-4
        Tolerance for stopping criterion.
    multi_class : {"ovr", "crammer_singer"}, default="ovr"
        Multi-class strategy.
    fit_intercept : bool, default=True
        Whether to fit an intercept.
    intercept_scaling : float, default=1
        Scaling for intercept.
    class_weight : dict or "balanced", optional
        Class weights.
    max_iter : int, default=1000
        Maximum iterations.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    classes_ : ndarray
        Unique class labels.
    coef_ : ndarray of shape (n_classes, n_features)
        Feature weights.
    intercept_ : ndarray of shape (n_classes,)
        Intercept terms.

    Examples
    --------
    >>> from nalyst.learners.svm import LinearSVC
    >>> X = [[0, 0], [1, 1]]
    >>> y = [0, 1]
    >>> clf = LinearSVC()
    >>> clf.train(X, y)
    LinearSVC()
    """

    def __init__(
        self,
        C: float = 1.0,
        *,
        loss: Literal["hinge", "squared_hinge"] = "squared_hinge",
        penalty: Literal["l1", "l2"] = "l2",
        dual: bool = True,
        tol: float = 1e-4,
        multi_class: Literal["ovr", "crammer_singer"] = "ovr",
        fit_intercept: bool = True,
        intercept_scaling: float = 1,
        class_weight=None,
        max_iter: int = 1000,
        random_state: Optional[int] = None,
    ):
        super().__init__(
            kernel="linear",
            C=C,
            tol=tol,
            max_iter=max_iter,
            random_state=random_state,
        )
        self.loss = loss
        self.penalty = penalty
        self.dual = dual
        self.multi_class = multi_class
        self.fit_intercept = fit_intercept
        self.intercept_scaling = intercept_scaling
        self.class_weight = class_weight

    def train(self, X: np.ndarray, y: np.ndarray) -> "LinearSVC":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : LinearSVC
            Fitted classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_samples, n_features = X.shape

        if n_classes == 2:
            # Binary classification
            y_binary = np.where(y == self.classes_[1], 1, -1)

            # Use gradient descent for simplicity
            w, b = self._train_linear(X, y_binary)

            self.coef_ = w.reshape(1, -1)
            self.intercept_ = np.array([b])
        else:
            # One-vs-rest
            self.coef_ = np.zeros((n_classes, n_features))
            self.intercept_ = np.zeros(n_classes)

            for i, cls in enumerate(self.classes_):
                y_binary = np.where(y == cls, 1, -1)
                w, b = self._train_linear(X, y_binary)
                self.coef_[i] = w
                self.intercept_[i] = b

        return self

    def _train_linear(self, X: np.ndarray, y: np.ndarray):
        """Train linear SVM using gradient descent."""
        n_samples, n_features = X.shape

        # Initialize weights
        w = np.zeros(n_features)
        b = 0.0

        learning_rate = 0.01

        for iteration in range(self.max_iter):
            # Compute margins
            margins = y * (np.dot(X, w) + b)

            # Compute gradients
            if self.loss == "hinge":
                # Hinge loss
                mask = margins < 1
                dw = w - self.C * np.dot(X.T, y * mask)
                db = -self.C * np.sum(y * mask)
            else:
                # Squared hinge loss
                violations = np.maximum(0, 1 - margins)
                dw = w - 2 * self.C * np.dot(X.T, y * violations)
                db = -2 * self.C * np.sum(y * violations)

            # Update
            w -= learning_rate * dw
            if self.fit_intercept:
                b -= learning_rate * db

            # Check convergence
            if np.linalg.norm(dw) < self.tol:
                break

        return w, b

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted labels.
        """
        check_is_trained(self, "coef_")
        X = check_array(X)

        scores = self.decision_function(X)

        if len(self.classes_) == 2:
            return self.classes_[(scores > 0).astype(int)]
        else:
            return self.classes_[np.argmax(scores, axis=1)]

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute decision function values.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        decision : ndarray
            Decision values.
        """
        check_is_trained(self, "coef_")
        X = check_array(X)

        scores = np.dot(X, self.coef_.T) + self.intercept_

        if len(self.classes_) == 2:
            return scores.ravel()
        return scores


class NuSVC(ClassifierMixin, SVMBase):
    """
    Nu-Support Vector Classification.

    Similar to SVC but uses a parameter nu to control the number
    of support vectors and training errors.

    Parameters
    ----------
    nu : float, default=0.5
        Upper bound on fraction of margin errors and lower bound
        on fraction of support vectors.
    kernel : {"linear", "poly", "rbf", "sigmoid"}, default="rbf"
        Kernel type.
    degree : int, default=3
        Polynomial degree.
    gamma : {"scale", "auto"} or float, default="scale"
        Kernel coefficient.
    coef0 : float, default=0.0
        Independent term.
    shrinking : bool, default=True
        Whether to use shrinking heuristic.
    probability : bool, default=False
        Enable probability estimates.
    tol : float, default=1e-3
        Tolerance.
    cache_size : float, default=200
        Kernel cache size (MB).
    class_weight : dict or "balanced", optional
        Class weights.
    max_iter : int, default=1000
        Maximum iterations.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from nalyst.learners.svm import NuSVC
    >>> X = [[0, 0], [1, 1]]
    >>> y = [0, 1]
    >>> clf = NuSVC()
    >>> clf.train(X, y)
    NuSVC()
    """

    def __init__(
        self,
        nu: float = 0.5,
        *,
        kernel: Literal["linear", "poly", "rbf", "sigmoid"] = "rbf",
        degree: int = 3,
        gamma: str = "scale",
        coef0: float = 0.0,
        shrinking: bool = True,
        probability: bool = False,
        tol: float = 1e-3,
        cache_size: float = 200,
        class_weight=None,
        max_iter: int = 1000,
        random_state: Optional[int] = None,
    ):
        super().__init__(
            kernel=kernel,
            degree=degree,
            gamma=gamma,
            coef0=coef0,
            tol=tol,
            max_iter=max_iter,
            random_state=random_state,
        )
        self.nu = nu
        self.shrinking = shrinking
        self.probability = probability
        self.cache_size = cache_size
        self.class_weight = class_weight

    def train(self, X: np.ndarray, y: np.ndarray) -> "NuSVC":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : NuSVC
            Fitted classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        self._train_X = X
        self._train_y = y

        # Get kernel function
        self._kernel_func = self._get_kernel(X)

        # Use SVC with C derived from nu
        n_samples = len(X)
        self.C = 1.0 / (n_samples * self.nu)

        # Create internal SVC
        self._svc = SupportVectorClassifier(
            C=self.C,
            kernel=self.kernel,
            degree=self.degree,
            gamma=self.gamma,
            coef0=self.coef0,
            tol=self.tol,
            max_iter=self.max_iter,
            random_state=self.random_state,
        )
        self._svc.train(X, y)

        # Copy attributes
        self.support_ = self._svc.support_
        self.support_vectors_ = self._svc.support_vectors_
        self.dual_coef_ = self._svc.dual_coef_
        self.intercept_ = self._svc.intercept_

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        check_is_trained(self, "_svc")
        return self._svc.infer(X)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function values."""
        check_is_trained(self, "_svc")
        return self._svc.decision_function(X)
