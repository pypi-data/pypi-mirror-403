"""
Linear classification models.
"""

from __future__ import annotations

import warnings
from typing import Any, Literal, Optional, Union

import numpy as np
from scipy import linalg
from scipy.special import expit, softmax

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_X_y, check_array, check_is_trained, check_random_state
from nalyst.core.tags import LearnerTags, TargetTags, ClassifierTags, InputTags
from nalyst.learners.linear.base import LinearModel


class LogisticLearner(ClassifierMixin, LinearModel):
    """
    Logistic regression classifier.

    Uses the logistic function to model the probability of the
    positive class. Supports binary and multiclass classification
    via one-vs-rest or multinomial approaches.

    Parameters
    ----------
    penalty : {"l1", "l2", "elasticnet", None}, default="l2"
        Regularization penalty type.
    dual : bool, default=False
        Dual formulation (only for L2 with liblinear).
    tol : float, default=1e-4
        Tolerance for stopping criterion.
    C : float, default=1.0
        Inverse of regularization strength. Smaller = stronger.
    fit_intercept : bool, default=True
        Whether to include intercept.
    intercept_scaling : float, default=1.0
        Intercept scaling for liblinear solver.
    class_weight : dict or "balanced", optional
        Weights associated with classes.
    random_state : int, RandomState, or None
        Random state for reproducibility.
    solver : {"lbfgs", "liblinear", "newton-cg", "sag", "saga"}, default="lbfgs"
        Optimization algorithm.
    max_iter : int, default=100
        Maximum iterations.
    multi_class : {"auto", "ovr", "multinomial"}, default="auto"
        Multiclass strategy.
    verbose : int, default=0
        Verbosity level.
    warm_start : bool, default=False
        Reuse previous solution.
    n_jobs : int, optional
        Parallel jobs for OvR.
    l1_ratio : float, optional
        Elastic net mixing (0-1).

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Unique class labels.
    coef_ : ndarray of shape (1, n_features) or (n_classes, n_features)
        Coefficients of the model.
    intercept_ : ndarray of shape (1,) or (n_classes,)
        Intercept (bias) terms.
    n_iter_ : int
        Number of iterations.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.linear import LogisticLearner
    >>> X = np.array([[0, 0], [1, 1], [2, 2]])
    >>> y = np.array([0, 1, 1])
    >>> clf = LogisticLearner()
    >>> clf.train(X, y)
    LogisticLearner()
    >>> clf.infer([[1.5, 1.5]])
    array([1])
    >>> clf.infer_proba([[1.5, 1.5]])
    array([[0.18..., 0.81...]])
    """

    def __init__(
        self,
        *,
        penalty: Optional[Literal["l1", "l2", "elasticnet"]] = "l2",
        dual: bool = False,
        tol: float = 1e-4,
        C: float = 1.0,
        fit_intercept: bool = True,
        intercept_scaling: float = 1.0,
        class_weight: Optional[Union[dict, str]] = None,
        random_state: Optional[int] = None,
        solver: Literal["lbfgs", "liblinear", "newton-cg", "sag", "saga"] = "lbfgs",
        max_iter: int = 100,
        multi_class: Literal["auto", "ovr", "multinomial"] = "auto",
        verbose: int = 0,
        warm_start: bool = False,
        n_jobs: Optional[int] = None,
        l1_ratio: Optional[float] = None,
    ):
        self.penalty = penalty
        self.dual = dual
        self.tol = tol
        self.C = C
        self.fit_intercept = fit_intercept
        self.intercept_scaling = intercept_scaling
        self.class_weight = class_weight
        self.random_state = random_state
        self.solver = solver
        self.max_iter = max_iter
        self.multi_class = multi_class
        self.verbose = verbose
        self.warm_start = warm_start
        self.n_jobs = n_jobs
        self.l1_ratio = l1_ratio

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "LogisticLearner":
        """
        Fit logistic regression model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target labels.
        sample_weight : array-like of shape (n_samples,), optional
            Sample weights.

        Returns
        -------
        self : LogisticLearner
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        # Encode labels to 0, 1, ...
        label_encoder = {c: i for i, c in enumerate(self.classes_)}
        y_encoded = np.array([label_encoder[yi] for yi in y])

        # Compute class weights if needed
        if self.class_weight == "balanced":
            class_counts = np.bincount(y_encoded)
            weights = n_samples / (n_classes * class_counts)
            sample_weight_from_class = weights[y_encoded]
            if sample_weight is not None:
                sample_weight = sample_weight * sample_weight_from_class
            else:
                sample_weight = sample_weight_from_class
        elif isinstance(self.class_weight, dict):
            weights = np.array([self.class_weight.get(c, 1.0) for c in self.classes_])
            sample_weight_from_class = weights[y_encoded]
            if sample_weight is not None:
                sample_weight = sample_weight * sample_weight_from_class
            else:
                sample_weight = sample_weight_from_class

        # Determine multiclass strategy
        if self.multi_class == "auto":
            if n_classes > 2:
                multi_class = "multinomial" if self.solver in ("lbfgs", "sag", "saga", "newton-cg") else "ovr"
            else:
                multi_class = "ovr"
        else:
            multi_class = self.multi_class

        # Initialize coefficients
        if self.warm_start and hasattr(self, "coef_"):
            coef = self.coef_.copy()
            intercept = self.intercept_.copy() if self.fit_intercept else None
        else:
            if multi_class == "multinomial" or n_classes > 2:
                coef = np.zeros((n_classes, n_features))
                intercept = np.zeros(n_classes) if self.fit_intercept else None
            else:
                coef = np.zeros((1, n_features))
                intercept = np.zeros(1) if self.fit_intercept else None

        # Fit using gradient descent
        rng = check_random_state(self.random_state)

        if multi_class == "multinomial" and n_classes > 2:
            coef, intercept, n_iter = self._fit_multinomial(
                X, y_encoded, coef, intercept, sample_weight, rng
            )
        else:
            coef, intercept, n_iter = self._fit_binary(
                X, y_encoded, coef, intercept, sample_weight, rng
            )

        self.coef_ = coef
        self.intercept_ = intercept if intercept is not None else np.zeros(coef.shape[0])
        self.n_iter_ = n_iter

        return self

    def _fit_binary(
        self,
        X: np.ndarray,
        y: np.ndarray,
        coef: np.ndarray,
        intercept: Optional[np.ndarray],
        sample_weight: Optional[np.ndarray],
        rng: np.random.RandomState,
    ) -> tuple:
        """Fit binary logistic regression."""
        n_samples, n_features = X.shape

        # L-BFGS-B optimization
        from scipy.optimize import minimize

        def loss_and_grad(w):
            if self.fit_intercept:
                coef = w[:-1].reshape(1, -1)
                intercept = w[-1:]
            else:
                coef = w.reshape(1, -1)
                intercept = np.zeros(1)

            # Linear predictor
            z = X @ coef.T + intercept
            z = z.ravel()

            # Probabilities
            p = expit(z)

            # Loss
            eps = 1e-15
            p = np.clip(p, eps, 1 - eps)
            loss = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

            # Add regularization
            if self.penalty == "l2":
                loss += 0.5 / self.C * np.sum(coef ** 2)
            elif self.penalty == "l1":
                loss += 1.0 / self.C * np.sum(np.abs(coef))

            # Gradient
            error = p - y
            if sample_weight is not None:
                error = error * sample_weight

            grad_coef = X.T @ error / n_samples

            if self.penalty == "l2":
                grad_coef += coef.ravel() / self.C

            if self.fit_intercept:
                grad_intercept = np.mean(error)
                grad = np.concatenate([grad_coef, [grad_intercept]])
            else:
                grad = grad_coef

            return loss, grad

        # Initial weights
        if self.fit_intercept:
            w0 = np.concatenate([coef.ravel(), intercept])
        else:
            w0 = coef.ravel()

        result = minimize(
            loss_and_grad,
            w0,
            method="L-BFGS-B",
            jac=True,
            options={"maxiter": self.max_iter, "gtol": self.tol},
        )

        if self.fit_intercept:
            coef = result.x[:-1].reshape(1, -1)
            intercept = result.x[-1:]
        else:
            coef = result.x.reshape(1, -1)
            intercept = None

        return coef, intercept, result.nit

    def _fit_multinomial(
        self,
        X: np.ndarray,
        y: np.ndarray,
        coef: np.ndarray,
        intercept: Optional[np.ndarray],
        sample_weight: Optional[np.ndarray],
        rng: np.random.RandomState,
    ) -> tuple:
        """Fit multinomial logistic regression."""
        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))

        from scipy.optimize import minimize

        # One-hot encode y
        y_onehot = np.zeros((n_samples, n_classes))
        y_onehot[np.arange(n_samples), y] = 1

        def loss_and_grad(w):
            if self.fit_intercept:
                coef = w[:-n_classes].reshape(n_classes, n_features)
                intercept = w[-n_classes:]
            else:
                coef = w.reshape(n_classes, n_features)
                intercept = np.zeros(n_classes)

            # Linear predictor
            z = X @ coef.T + intercept

            # Softmax probabilities
            p = softmax(z, axis=1)

            # Cross-entropy loss
            eps = 1e-15
            p = np.clip(p, eps, 1 - eps)
            loss = -np.mean(np.sum(y_onehot * np.log(p), axis=1))

            # Regularization
            if self.penalty == "l2":
                loss += 0.5 / self.C * np.sum(coef ** 2)

            # Gradient
            error = p - y_onehot
            if sample_weight is not None:
                error = error * sample_weight[:, np.newaxis]

            grad_coef = error.T @ X / n_samples

            if self.penalty == "l2":
                grad_coef += coef / self.C

            if self.fit_intercept:
                grad_intercept = np.mean(error, axis=0)
                grad = np.concatenate([grad_coef.ravel(), grad_intercept])
            else:
                grad = grad_coef.ravel()

            return loss, grad

        # Initial weights
        if self.fit_intercept:
            w0 = np.concatenate([coef.ravel(), intercept])
        else:
            w0 = coef.ravel()

        result = minimize(
            loss_and_grad,
            w0,
            method="L-BFGS-B",
            jac=True,
            options={"maxiter": self.max_iter, "gtol": self.tol},
        )

        if self.fit_intercept:
            coef = result.x[:-n_classes].reshape(n_classes, n_features)
            intercept = result.x[-n_classes:]
        else:
            coef = result.x.reshape(n_classes, n_features)
            intercept = None

        return coef, intercept, result.nit

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels.
        """
        check_is_trained(self)

        proba = self.infer_proba(X)
        indices = np.argmax(proba, axis=1)
        return self.classes_[indices]

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Class probabilities.
        """
        check_is_trained(self)
        X = check_array(X)

        decision = self._decision_function(X)

        if len(self.classes_) == 2:
            proba_1 = expit(decision).ravel()
            return np.column_stack([1 - proba_1, proba_1])
        else:
            return softmax(decision, axis=1)

    def infer_log_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict log-probabilities.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        log_proba : ndarray of shape (n_samples, n_classes)
            Log-probabilities.
        """
        return np.log(self.infer_proba(X))

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Compute decision function.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        decision : ndarray
            Decision function values.
        """
        return self._decision_function(X)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="classifier",
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(
                binary=True,
                multiclass=True,
                predict_proba=True,
                decision_function=True,
            ),
            input_tags=InputTags(sparse=True),
        )


class RidgeClassifier(ClassifierMixin, LinearModel):
    """
    Classifier using Ridge regression.

    Converts classification to regression using label encoding
    and applies Ridge regression. Decision boundary is at 0.5.

    Parameters
    ----------
    alpha : float, default=1.0
        Regularization strength.
    fit_intercept : bool, default=True
        Whether to calculate intercept.
    copy_X : bool, default=True
        Whether to copy X.
    max_iter : int, optional
        Maximum iterations for sparse solver.
    tol : float, default=1e-4
        Precision of solution.
    class_weight : dict or "balanced", optional
        Class weights.
    solver : {"auto", "svd", "cholesky", "lsqr", "sparse_cg", "sag", "saga", "lbfgs"}
        Solver to use.
    positive : bool, default=False
        Force positive coefficients.
    random_state : int, optional
        Random state.

    Attributes
    ----------
    classes_ : ndarray
        Class labels.
    coef_ : ndarray
        Coefficients.
    intercept_ : ndarray
        Intercepts.
    n_features_in_ : int
        Number of features.
    """

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        fit_intercept: bool = True,
        copy_X: bool = True,
        max_iter: Optional[int] = None,
        tol: float = 1e-4,
        class_weight: Optional[Union[dict, str]] = None,
        solver: str = "auto",
        positive: bool = False,
        random_state: Optional[int] = None,
    ):
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.copy_X = copy_X
        self.max_iter = max_iter
        self.tol = tol
        self.class_weight = class_weight
        self.solver = solver
        self.positive = positive
        self.random_state = random_state

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "RidgeClassifier":
        """
        Fit Ridge classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target labels.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : RidgeClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_samples = X.shape[0]
        self.n_features_in_ = X.shape[1]

        # Convert to binary or one-hot
        if n_classes == 2:
            Y = np.where(y == self.classes_[1], 1.0, -1.0)
        else:
            Y = np.zeros((n_samples, n_classes))
            for i, c in enumerate(self.classes_):
                Y[y == c, i] = 1.0

        # Apply class weights
        if self.class_weight == "balanced":
            class_counts = np.bincount(
                np.searchsorted(self.classes_, y)
            )
            weights = n_samples / (n_classes * class_counts)
            label_indices = np.searchsorted(self.classes_, y)
            sample_weight_from_class = weights[label_indices]
            if sample_weight is not None:
                sample_weight = sample_weight * sample_weight_from_class
            else:
                sample_weight = sample_weight_from_class

        # Use RidgeRegressor internally
        from nalyst.learners.linear.regression import RidgeRegressor

        ridge = RidgeRegressor(
            alpha=self.alpha,
            fit_intercept=self.fit_intercept,
            copy_X=self.copy_X,
            max_iter=self.max_iter,
            tol=self.tol,
            solver=self.solver,
            positive=self.positive,
            random_state=self.random_state,
        )

        ridge.train(X, Y, sample_weight=sample_weight)

        self.coef_ = ridge.coef_
        self.intercept_ = ridge.intercept_

        if n_classes == 2:
            self.coef_ = self.coef_.reshape(1, -1)
            self.intercept_ = np.atleast_1d(self.intercept_)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted labels.
        """
        check_is_trained(self)

        scores = self._decision_function(X)

        if len(self.classes_) == 2:
            indices = (scores > 0).astype(int).ravel()
        else:
            indices = np.argmax(scores, axis=1)

        return self.classes_[indices]

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function values."""
        return self._decision_function(X)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="classifier",
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(
                binary=True,
                multiclass=True,
                decision_function=True,
                predict_proba=False,
            ),
        )


class SGDLearner(ClassifierMixin, LinearModel):
    """
    Stochastic Gradient Descent classifier.

    Supports various loss functions and regularization options
    for efficient large-scale learning.

    Parameters
    ----------
    loss : {"hinge", "log_loss", "modified_huber", "squared_hinge", "perceptron"}
        Loss function. "hinge" = linear SVM, "log_loss" = logistic regression.
    penalty : {"l2", "l1", "elasticnet"}, default="l2"
        Regularization type.
    alpha : float, default=0.0001
        Regularization parameter.
    l1_ratio : float, default=0.15
        Elastic net mixing (only for elasticnet penalty).
    fit_intercept : bool, default=True
        Whether to include intercept.
    max_iter : int, default=1000
        Maximum passes over data.
    tol : float, default=1e-3
        Stopping criterion.
    shuffle : bool, default=True
        Shuffle data each epoch.
    verbose : int, default=0
        Verbosity level.
    epsilon : float, default=0.1
        Epsilon for epsilon-insensitive losses.
    n_jobs : int, optional
        Parallel jobs.
    random_state : int, optional
        Random state.
    learning_rate : {"constant", "optimal", "invscaling", "adaptive"}
        Learning rate schedule.
    eta0 : float, default=0.0
        Initial learning rate.
    power_t : float, default=0.5
        Exponent for inverse scaling.
    early_stopping : bool, default=False
        Use early stopping.
    validation_fraction : float, default=0.1
        Fraction for validation if early stopping.
    n_iter_no_change : int, default=5
        Iterations with no improvement before stopping.
    class_weight : dict or "balanced", optional
        Class weights.
    warm_start : bool, default=False
        Reuse previous solution.
    average : bool or int, default=False
        Compute averaged weights.

    Attributes
    ----------
    classes_ : ndarray
        Class labels.
    coef_ : ndarray
        Coefficients.
    intercept_ : ndarray
        Intercepts.
    n_iter_ : int
        Iterations run.
    t_ : int
        Total samples seen.
    n_features_in_ : int
        Number of features.
    """

    def __init__(
        self,
        *,
        loss: Literal["hinge", "log_loss", "modified_huber", "squared_hinge", "perceptron"] = "hinge",
        penalty: Literal["l2", "l1", "elasticnet"] = "l2",
        alpha: float = 0.0001,
        l1_ratio: float = 0.15,
        fit_intercept: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-3,
        shuffle: bool = True,
        verbose: int = 0,
        epsilon: float = 0.1,
        n_jobs: Optional[int] = None,
        random_state: Optional[int] = None,
        learning_rate: str = "optimal",
        eta0: float = 0.0,
        power_t: float = 0.5,
        early_stopping: bool = False,
        validation_fraction: float = 0.1,
        n_iter_no_change: int = 5,
        class_weight: Optional[Union[dict, str]] = None,
        warm_start: bool = False,
        average: Union[bool, int] = False,
    ):
        self.loss = loss
        self.penalty = penalty
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self.tol = tol
        self.shuffle = shuffle
        self.verbose = verbose
        self.epsilon = epsilon
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.learning_rate = learning_rate
        self.eta0 = eta0
        self.power_t = power_t
        self.early_stopping = early_stopping
        self.validation_fraction = validation_fraction
        self.n_iter_no_change = n_iter_no_change
        self.class_weight = class_weight
        self.warm_start = warm_start
        self.average = average

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "SGDLearner":
        """
        Fit SGD classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target labels.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : SGDLearner
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        rng = check_random_state(self.random_state)

        # Encode labels
        label_encoder = {c: i for i, c in enumerate(self.classes_)}
        y_encoded = np.array([label_encoder[yi] for yi in y])

        # For binary, use -1/+1
        if n_classes == 2:
            y_binary = np.where(y_encoded == 1, 1.0, -1.0)
            n_classifiers = 1
        else:
            n_classifiers = n_classes

        # Initialize weights
        if self.warm_start and hasattr(self, "coef_"):
            coef = self.coef_.copy()
            intercept = self.intercept_.copy()
        else:
            coef = np.zeros((n_classifiers, n_features))
            intercept = np.zeros(n_classifiers)

        # Determine learning rate
        if self.learning_rate == "optimal":
            eta0 = 1.0 / (self.alpha * n_samples)
        elif self.learning_rate == "constant":
            eta0 = self.eta0 if self.eta0 > 0 else 0.01
        else:
            eta0 = self.eta0 if self.eta0 > 0 else 0.01

        t = 0
        no_improvement_count = 0
        best_loss = np.inf

        for epoch in range(self.max_iter):
            # Shuffle data
            if self.shuffle:
                perm = rng.permutation(n_samples)
                X_shuffled = X[perm]
                if n_classes == 2:
                    y_shuffled = y_binary[perm]
                else:
                    y_shuffled = y_encoded[perm]
            else:
                X_shuffled = X
                y_shuffled = y_binary if n_classes == 2 else y_encoded

            for i in range(n_samples):
                t += 1
                xi = X_shuffled[i:i+1]
                yi = y_shuffled[i]

                # Compute learning rate
                if self.learning_rate == "optimal":
                    eta = 1.0 / (self.alpha * t)
                elif self.learning_rate == "invscaling":
                    eta = eta0 / (t ** self.power_t)
                else:
                    eta = eta0

                if n_classes == 2:
                    # Binary classification
                    score = xi @ coef[0] + intercept[0]

                    # Compute gradient based on loss
                    if self.loss == "hinge":
                        if yi * score < 1:
                            dloss = -yi
                        else:
                            dloss = 0
                    elif self.loss == "log_loss":
                        p = expit(yi * score)
                        dloss = -yi * (1 - p)
                    elif self.loss == "perceptron":
                        if yi * score <= 0:
                            dloss = -yi
                        else:
                            dloss = 0
                    else:
                        dloss = -yi * max(0, 1 - yi * score)

                    # Update weights
                    if dloss != 0:
                        coef[0] -= eta * (dloss * xi.ravel() + self.alpha * coef[0])
                        if self.fit_intercept:
                            intercept[0] -= eta * dloss
                    else:
                        coef[0] *= (1 - eta * self.alpha)
                else:
                    # Multiclass: one-vs-all
                    for k in range(n_classes):
                        target = 1.0 if yi == k else -1.0
                        score = xi @ coef[k] + intercept[k]

                        if self.loss == "hinge":
                            if target * score < 1:
                                dloss = -target
                            else:
                                dloss = 0
                        elif self.loss == "log_loss":
                            p = expit(target * score)
                            dloss = -target * (1 - p)
                        else:
                            if target * score <= 0:
                                dloss = -target
                            else:
                                dloss = 0

                        if dloss != 0:
                            coef[k] -= eta * (dloss * xi.ravel() + self.alpha * coef[k])
                            if self.fit_intercept:
                                intercept[k] -= eta * dloss
                        else:
                            coef[k] *= (1 - eta * self.alpha)

            # Check convergence
            if self.tol is not None:
                # Compute loss on full data
                scores = X @ coef.T + intercept
                if n_classes == 2:
                    loss = np.mean(np.maximum(0, 1 - y_binary * scores.ravel()))
                else:
                    loss = 0
                    for k in range(n_classes):
                        target = np.where(y_encoded == k, 1.0, -1.0)
                        loss += np.mean(np.maximum(0, 1 - target * scores[:, k]))
                    loss /= n_classes

                if loss > best_loss - self.tol:
                    no_improvement_count += 1
                else:
                    no_improvement_count = 0
                    best_loss = loss

                if no_improvement_count >= self.n_iter_no_change:
                    break

        self.coef_ = coef
        self.intercept_ = intercept
        self.n_iter_ = epoch + 1
        self.t_ = t

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted labels.
        """
        check_is_trained(self)

        scores = self._decision_function(X)

        if len(self.classes_) == 2:
            indices = (scores > 0).astype(int).ravel()
        else:
            indices = np.argmax(scores, axis=1)

        return self.classes_[indices]

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function values."""
        return self._decision_function(X)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="classifier",
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(
                binary=True,
                multiclass=True,
                decision_function=True,
                predict_proba=(self.loss == "log_loss"),
            ),
            input_tags=InputTags(sparse=True),
        )


class PerceptronLearner(SGDLearner):
    """
    Perceptron linear classifier.

    Simple linear classifier that makes a binary decision based on
    a linear predictor function. Equivalent to SGD with hinge loss
    and no regularization.

    Parameters
    ----------
    penalty : {"l2", "l1", "elasticnet", None}, default=None
        Regularization type.
    alpha : float, default=0.0001
        Regularization strength.
    l1_ratio : float, default=0.15
        Elastic net mixing.
    fit_intercept : bool, default=True
        Whether to include intercept.
    max_iter : int, default=1000
        Maximum iterations.
    tol : float, default=1e-3
        Stopping criterion.
    shuffle : bool, default=True
        Shuffle data each epoch.
    verbose : int, default=0
        Verbosity.
    eta0 : float, default=1.0
        Constant learning rate.
    n_jobs : int, optional
        Parallel jobs.
    random_state : int, optional
        Random state.
    early_stopping : bool, default=False
        Use early stopping.
    validation_fraction : float, default=0.1
        Validation set fraction.
    n_iter_no_change : int, default=5
        Iterations before stopping.
    class_weight : dict or "balanced", optional
        Class weights.
    warm_start : bool, default=False
        Reuse previous solution.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.linear import PerceptronLearner
    >>> X = np.array([[0, 0], [1, 1], [2, 2]])
    >>> y = np.array([0, 0, 1])
    >>> clf = PerceptronLearner()
    >>> clf.train(X, y)
    PerceptronLearner()
    >>> clf.infer([[1.5, 1.5]])
    array([1])
    """

    def __init__(
        self,
        *,
        penalty: Optional[Literal["l2", "l1", "elasticnet"]] = None,
        alpha: float = 0.0001,
        l1_ratio: float = 0.15,
        fit_intercept: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-3,
        shuffle: bool = True,
        verbose: int = 0,
        eta0: float = 1.0,
        n_jobs: Optional[int] = None,
        random_state: Optional[int] = None,
        early_stopping: bool = False,
        validation_fraction: float = 0.1,
        n_iter_no_change: int = 5,
        class_weight: Optional[Union[dict, str]] = None,
        warm_start: bool = False,
    ):
        super().__init__(
            loss="perceptron",
            penalty=penalty if penalty is not None else "l2",
            alpha=alpha if penalty is not None else 0.0,
            l1_ratio=l1_ratio,
            fit_intercept=fit_intercept,
            max_iter=max_iter,
            tol=tol,
            shuffle=shuffle,
            verbose=verbose,
            random_state=random_state,
            learning_rate="constant",
            eta0=eta0,
            early_stopping=early_stopping,
            validation_fraction=validation_fraction,
            n_iter_no_change=n_iter_no_change,
            class_weight=class_weight,
            warm_start=warm_start,
        )
        self.penalty = penalty
