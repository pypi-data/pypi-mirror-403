"""
Multi-Layer Perceptron implementations.

Provides feedforward neural networks for classification and regression
with various activation functions, solvers, and regularization options.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Union, Literal
import warnings

import numpy as np
from scipy.special import expit as sigmoid

from nalyst.core.foundation import (
    BaseLearner,
    ClassifierMixin,
    RegressorMixin,
)
from nalyst.core.validation import (
    check_X_y,
    check_array,
    check_is_trained,
    check_random_state,
)
from nalyst.core.tags import (
    LearnerTags,
    TargetTags,
    ClassifierTags,
    RegressorTags,
)
from nalyst.exceptions import ConvergenceWarning


def _softmax(X: np.ndarray) -> np.ndarray:
    """Compute softmax activation."""
    exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))
    return exp_X / np.sum(exp_X, axis=1, keepdims=True)


def _relu(X: np.ndarray) -> np.ndarray:
    """Rectified Linear Unit activation."""
    return np.maximum(0, X)


def _relu_derivative(X: np.ndarray) -> np.ndarray:
    """Derivative of ReLU."""
    return (X > 0).astype(float)


def _tanh(X: np.ndarray) -> np.ndarray:
    """Hyperbolic tangent activation."""
    return np.tanh(X)


def _tanh_derivative(X: np.ndarray) -> np.ndarray:
    """Derivative of tanh."""
    return 1 - np.tanh(X) ** 2


def _logistic(X: np.ndarray) -> np.ndarray:
    """Logistic (sigmoid) activation."""
    return sigmoid(X)


def _logistic_derivative(X: np.ndarray) -> np.ndarray:
    """Derivative of sigmoid."""
    s = sigmoid(X)
    return s * (1 - s)


def _identity(X: np.ndarray) -> np.ndarray:
    """Identity activation (no change)."""
    return X


def _identity_derivative(X: np.ndarray) -> np.ndarray:
    """Derivative of identity."""
    return np.ones_like(X)


def _leaky_relu(X: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """Leaky ReLU activation."""
    return np.where(X > 0, X, alpha * X)


def _leaky_relu_derivative(X: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """Derivative of Leaky ReLU."""
    return np.where(X > 0, 1, alpha)


ACTIVATIONS = {
    "relu": _relu,
    "tanh": _tanh,
    "logistic": _logistic,
    "identity": _identity,
    "leaky_relu": _leaky_relu,
}

ACTIVATION_DERIVATIVES = {
    "relu": _relu_derivative,
    "tanh": _tanh_derivative,
    "logistic": _logistic_derivative,
    "identity": _identity_derivative,
    "leaky_relu": _leaky_relu_derivative,
}


class BaseMultiLayerPerceptron(BaseLearner):
    """
    Base class for multi-layer perceptron neural networks.

    Parameters
    ----------
    hidden_layer_sizes : tuple, default=(100,)
        Number of neurons in each hidden layer.
    activation : str, default="relu"
        Activation function: "relu", "tanh", "logistic", "identity".
    solver : str, default="adam"
        Optimizer: "sgd", "adam", "lbfgs".
    alpha : float, default=0.0001
        L2 regularization strength.
    batch_size : int or "auto", default="auto"
        Mini-batch size.
    learning_rate : str, default="constant"
        Learning rate schedule: "constant", "invscaling", "adaptive".
    learning_rate_init : float, default=0.001
        Initial learning rate.
    power_t : float, default=0.5
        Exponent for inverse scaling.
    max_iter : int, default=200
        Maximum iterations.
    shuffle : bool, default=True
        Shuffle samples each iteration.
    random_state : int, optional
        Random seed.
    tol : float, default=1e-4
        Convergence tolerance.
    verbose : bool, default=False
        Print progress.
    warm_start : bool, default=False
        Reuse previous solution.
    momentum : float, default=0.9
        Momentum for SGD.
    nesterovs_momentum : bool, default=True
        Use Nesterov's momentum.
    early_stopping : bool, default=False
        Use early stopping.
    validation_fraction : float, default=0.1
        Validation set fraction.
    beta_1 : float, default=0.9
        Adam decay rate for first moment.
    beta_2 : float, default=0.999
        Adam decay rate for second moment.
    epsilon : float, default=1e-8
        Numerical stability constant.
    n_iter_no_change : int, default=10
        Iterations without improvement for early stopping.
    max_fun : int, default=15000
        Max function evaluations for L-BFGS.
    """

    def __init__(
        self,
        hidden_layer_sizes: Tuple[int, ...] = (100,),
        activation: Literal["relu", "tanh", "logistic", "identity"] = "relu",
        *,
        solver: Literal["sgd", "adam", "lbfgs"] = "adam",
        alpha: float = 0.0001,
        batch_size: Union[int, str] = "auto",
        learning_rate: Literal["constant", "invscaling", "adaptive"] = "constant",
        learning_rate_init: float = 0.001,
        power_t: float = 0.5,
        max_iter: int = 200,
        shuffle: bool = True,
        random_state: Optional[int] = None,
        tol: float = 1e-4,
        verbose: bool = False,
        warm_start: bool = False,
        momentum: float = 0.9,
        nesterovs_momentum: bool = True,
        early_stopping: bool = False,
        validation_fraction: float = 0.1,
        beta_1: float = 0.9,
        beta_2: float = 0.999,
        epsilon: float = 1e-8,
        n_iter_no_change: int = 10,
        max_fun: int = 15000,
    ):
        self.hidden_layer_sizes = hidden_layer_sizes
        self.activation = activation
        self.solver = solver
        self.alpha = alpha
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.learning_rate_init = learning_rate_init
        self.power_t = power_t
        self.max_iter = max_iter
        self.shuffle = shuffle
        self.random_state = random_state
        self.tol = tol
        self.verbose = verbose
        self.warm_start = warm_start
        self.momentum = momentum
        self.nesterovs_momentum = nesterovs_momentum
        self.early_stopping = early_stopping
        self.validation_fraction = validation_fraction
        self.beta_1 = beta_1
        self.beta_2 = beta_2
        self.epsilon = epsilon
        self.n_iter_no_change = n_iter_no_change
        self.max_fun = max_fun

    def _initialize_weights(
        self,
        layer_sizes: List[int],
        rng: np.random.RandomState,
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Initialize weights using Xavier/Glorot initialization."""
        weights = []
        biases = []

        for i in range(len(layer_sizes) - 1):
            fan_in = layer_sizes[i]
            fan_out = layer_sizes[i + 1]

            # Xavier initialization
            bound = np.sqrt(6.0 / (fan_in + fan_out))
            W = rng.uniform(-bound, bound, size=(fan_in, fan_out))
            b = np.zeros(fan_out)

            weights.append(W)
            biases.append(b)

        return weights, biases

    def _forward_pass(
        self,
        X: np.ndarray,
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Perform forward propagation.

        Returns activations and pre-activations for each layer.
        """
        activation_fn = ACTIVATIONS[self.activation]

        activations = [X]
        pre_activations = [None]

        layer_input = X

        for i, (W, b) in enumerate(zip(self.weights_, self.biases_)):
            z = layer_input @ W + b
            pre_activations.append(z)

            # Apply activation (output layer uses different activation)
            if i < len(self.weights_) - 1:
                a = activation_fn(z)
            else:
                a = self._output_activation(z)

            activations.append(a)
            layer_input = a

        return activations, pre_activations

    def _output_activation(self, z: np.ndarray) -> np.ndarray:
        """Apply output layer activation."""
        raise NotImplementedError

    def _compute_loss(
        self,
        y: np.ndarray,
        y_pred: np.ndarray,
    ) -> float:
        """Compute loss function value."""
        raise NotImplementedError

    def _backward_pass(
        self,
        y: np.ndarray,
        activations: List[np.ndarray],
        pre_activations: List[np.ndarray],
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Perform backpropagation.

        Returns gradients for weights and biases.
        """
        n_samples = y.shape[0]
        n_layers = len(self.weights_)

        activation_derivative = ACTIVATION_DERIVATIVES[self.activation]

        grad_weights = []
        grad_biases = []

        # Output layer error
        delta = self._output_error(y, activations[-1])

        # Backpropagate through layers
        for i in range(n_layers - 1, -1, -1):
            # Gradients
            dW = activations[i].T @ delta / n_samples
            db = np.mean(delta, axis=0)

            # Add L2 regularization
            dW += self.alpha * self.weights_[i]

            grad_weights.insert(0, dW)
            grad_biases.insert(0, db)

            # Propagate error (if not at first hidden layer)
            if i > 0:
                delta = (delta @ self.weights_[i].T) * activation_derivative(
                    pre_activations[i]
                )

        return grad_weights, grad_biases

    def _output_error(
        self,
        y: np.ndarray,
        y_pred: np.ndarray,
    ) -> np.ndarray:
        """Compute output layer error."""
        raise NotImplementedError

    def _update_weights_sgd(
        self,
        grad_weights: List[np.ndarray],
        grad_biases: List[np.ndarray],
        iteration: int,
    ):
        """Update weights using SGD with momentum."""
        lr = self._get_learning_rate(iteration)

        for i in range(len(self.weights_)):
            # Velocity update
            self.velocity_weights_[i] = (
                self.momentum * self.velocity_weights_[i]
                - lr * grad_weights[i]
            )
            self.velocity_biases_[i] = (
                self.momentum * self.velocity_biases_[i]
                - lr * grad_biases[i]
            )

            # Weight update
            self.weights_[i] += self.velocity_weights_[i]
            self.biases_[i] += self.velocity_biases_[i]

    def _update_weights_adam(
        self,
        grad_weights: List[np.ndarray],
        grad_biases: List[np.ndarray],
        iteration: int,
    ):
        """Update weights using Adam optimizer."""
        t = iteration + 1

        for i in range(len(self.weights_)):
            # Update biased first moment estimate
            self.m_weights_[i] = (
                self.beta_1 * self.m_weights_[i]
                + (1 - self.beta_1) * grad_weights[i]
            )
            self.m_biases_[i] = (
                self.beta_1 * self.m_biases_[i]
                + (1 - self.beta_1) * grad_biases[i]
            )

            # Update biased second moment estimate
            self.v_weights_[i] = (
                self.beta_2 * self.v_weights_[i]
                + (1 - self.beta_2) * grad_weights[i] ** 2
            )
            self.v_biases_[i] = (
                self.beta_2 * self.v_biases_[i]
                + (1 - self.beta_2) * grad_biases[i] ** 2
            )

            # Bias correction
            m_hat_w = self.m_weights_[i] / (1 - self.beta_1 ** t)
            m_hat_b = self.m_biases_[i] / (1 - self.beta_1 ** t)
            v_hat_w = self.v_weights_[i] / (1 - self.beta_2 ** t)
            v_hat_b = self.v_biases_[i] / (1 - self.beta_2 ** t)

            # Update weights
            self.weights_[i] -= (
                self.learning_rate_init * m_hat_w
                / (np.sqrt(v_hat_w) + self.epsilon)
            )
            self.biases_[i] -= (
                self.learning_rate_init * m_hat_b
                / (np.sqrt(v_hat_b) + self.epsilon)
            )

    def _get_learning_rate(self, iteration: int) -> float:
        """Get learning rate for current iteration."""
        if self.learning_rate == "constant":
            return self.learning_rate_init
        elif self.learning_rate == "invscaling":
            return self.learning_rate_init / (iteration + 1) ** self.power_t
        else:  # adaptive
            return self._current_lr

    def _get_batch_size(self, n_samples: int) -> int:
        """Determine batch size."""
        if self.batch_size == "auto":
            return min(200, n_samples)
        return min(self.batch_size, n_samples)

    def _train_sgd(
        self,
        X: np.ndarray,
        y: np.ndarray,
        layer_sizes: List[int],
    ):
        """Train using stochastic gradient descent."""
        rng = check_random_state(self.random_state)
        n_samples = X.shape[0]
        batch_size = self._get_batch_size(n_samples)

        # Initialize velocity for momentum
        self.velocity_weights_ = [np.zeros_like(W) for W in self.weights_]
        self.velocity_biases_ = [np.zeros_like(b) for b in self.biases_]

        # Track loss
        self.loss_curve_ = []
        best_loss = np.inf
        no_improvement_count = 0
        self._current_lr = self.learning_rate_init

        # Validation set for early stopping
        if self.early_stopping:
            val_size = int(n_samples * self.validation_fraction)
            indices = rng.permutation(n_samples)
            val_idx = indices[:val_size]
            train_idx = indices[val_size:]
            X_train, y_train = X[train_idx], y[train_idx]
            X_val, y_val = X[val_idx], y[val_idx]
        else:
            X_train, y_train = X, y

        n_train = X_train.shape[0]

        for iteration in range(self.max_iter):
            # Shuffle training data
            if self.shuffle:
                idx = rng.permutation(n_train)
                X_train = X_train[idx]
                y_train = y_train[idx]

            # Mini-batch training
            for start in range(0, n_train, batch_size):
                end = min(start + batch_size, n_train)
                X_batch = X_train[start:end]
                y_batch = y_train[start:end]

                # Forward pass
                activations, pre_activations = self._forward_pass(X_batch)

                # Backward pass
                grad_weights, grad_biases = self._backward_pass(
                    y_batch, activations, pre_activations
                )

                # Update weights
                self._update_weights_sgd(grad_weights, grad_biases, iteration)

            # Compute loss
            activations, _ = self._forward_pass(X_train)
            loss = self._compute_loss(y_train, activations[-1])
            self.loss_curve_.append(loss)

            if self.verbose:
                print(f"Iteration {iteration + 1}, loss = {loss:.8f}")

            # Check convergence
            if self.early_stopping:
                val_activations, _ = self._forward_pass(X_val)
                val_loss = self._compute_loss(y_val, val_activations[-1])

                if val_loss < best_loss - self.tol:
                    best_loss = val_loss
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
            else:
                if loss < best_loss - self.tol:
                    best_loss = loss
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1

            if no_improvement_count >= self.n_iter_no_change:
                if self.learning_rate == "adaptive":
                    self._current_lr /= 5
                    if self._current_lr < 1e-6:
                        if self.verbose:
                            print("Converged!")
                        break
                    no_improvement_count = 0
                else:
                    if self.verbose:
                        print("Converged!")
                    break

        self.n_iter_ = iteration + 1

    def _train_adam(
        self,
        X: np.ndarray,
        y: np.ndarray,
        layer_sizes: List[int],
    ):
        """Train using Adam optimizer."""
        rng = check_random_state(self.random_state)
        n_samples = X.shape[0]
        batch_size = self._get_batch_size(n_samples)

        # Initialize Adam moment estimates
        self.m_weights_ = [np.zeros_like(W) for W in self.weights_]
        self.m_biases_ = [np.zeros_like(b) for b in self.biases_]
        self.v_weights_ = [np.zeros_like(W) for W in self.weights_]
        self.v_biases_ = [np.zeros_like(b) for b in self.biases_]

        # Track loss
        self.loss_curve_ = []
        best_loss = np.inf
        no_improvement_count = 0

        # Validation set for early stopping
        if self.early_stopping:
            val_size = int(n_samples * self.validation_fraction)
            indices = rng.permutation(n_samples)
            val_idx = indices[:val_size]
            train_idx = indices[val_size:]
            X_train, y_train = X[train_idx], y[train_idx]
            X_val, y_val = X[val_idx], y[val_idx]
        else:
            X_train, y_train = X, y

        n_train = X_train.shape[0]

        for iteration in range(self.max_iter):
            # Shuffle training data
            if self.shuffle:
                idx = rng.permutation(n_train)
                X_train = X_train[idx]
                y_train = y_train[idx]

            # Mini-batch training
            for start in range(0, n_train, batch_size):
                end = min(start + batch_size, n_train)
                X_batch = X_train[start:end]
                y_batch = y_train[start:end]

                # Forward pass
                activations, pre_activations = self._forward_pass(X_batch)

                # Backward pass
                grad_weights, grad_biases = self._backward_pass(
                    y_batch, activations, pre_activations
                )

                # Update weights
                self._update_weights_adam(grad_weights, grad_biases, iteration)

            # Compute loss
            activations, _ = self._forward_pass(X_train)
            loss = self._compute_loss(y_train, activations[-1])
            self.loss_curve_.append(loss)

            if self.verbose:
                print(f"Iteration {iteration + 1}, loss = {loss:.8f}")

            # Check convergence
            if self.early_stopping:
                val_activations, _ = self._forward_pass(X_val)
                val_loss = self._compute_loss(y_val, val_activations[-1])

                if val_loss < best_loss - self.tol:
                    best_loss = val_loss
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1
            else:
                if loss < best_loss - self.tol:
                    best_loss = loss
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1

            if no_improvement_count >= self.n_iter_no_change:
                if self.verbose:
                    print("Converged!")
                break

        self.n_iter_ = iteration + 1


class MLPClassifier(ClassifierMixin, BaseMultiLayerPerceptron):
    """
    Multi-Layer Perceptron classifier.

    A feedforward neural network that trains using backpropagation.

    Parameters
    ----------
    hidden_layer_sizes : tuple, default=(100,)
        Number of neurons in each hidden layer.
    activation : str, default="relu"
        Activation function: "relu", "tanh", "logistic", "identity".
    solver : str, default="adam"
        Optimizer: "sgd", "adam".
    alpha : float, default=0.0001
        L2 regularization strength.
    batch_size : int or "auto", default="auto"
        Mini-batch size.
    learning_rate : str, default="constant"
        Learning rate schedule: "constant", "invscaling", "adaptive".
    learning_rate_init : float, default=0.001
        Initial learning rate.
    max_iter : int, default=200
        Maximum iterations.
    random_state : int, optional
        Random seed.
    tol : float, default=1e-4
        Convergence tolerance.
    verbose : bool, default=False
        Print progress.
    early_stopping : bool, default=False
        Use early stopping.
    validation_fraction : float, default=0.1
        Validation set fraction.

    Attributes
    ----------
    classes_ : ndarray
        Class labels.
    n_features_in_ : int
        Number of input features.
    n_layers_ : int
        Number of layers.
    weights_ : list of ndarray
        Weight matrices.
    biases_ : list of ndarray
        Bias vectors.
    loss_curve_ : list
        Loss at each iteration.
    n_iter_ : int
        Number of iterations run.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.neural import MLPClassifier
    >>> X = np.array([[0, 0], [1, 0], [0, 1], [1, 1]])
    >>> y = np.array([0, 1, 1, 0])  # XOR
    >>> clf = MLPClassifier(hidden_layer_sizes=(4,), max_iter=1000, random_state=42)
    >>> clf.train(X, y)
    MLPClassifier(hidden_layer_sizes=(4,), max_iter=1000, random_state=42)
    >>> clf.infer([[0, 0], [1, 1]])
    array([0, 0])
    """

    def _output_activation(self, z: np.ndarray) -> np.ndarray:
        """Softmax for multi-class, sigmoid for binary."""
        if self.n_classes_ == 2:
            return sigmoid(z)
        return _softmax(z)

    def _compute_loss(
        self,
        y: np.ndarray,
        y_pred: np.ndarray,
    ) -> float:
        """Cross-entropy loss."""
        eps = 1e-15
        y_pred = np.clip(y_pred, eps, 1 - eps)

        if self.n_classes_ == 2:
            # Binary cross-entropy
            loss = -np.mean(
                y.ravel() * np.log(y_pred.ravel())
                + (1 - y.ravel()) * np.log(1 - y_pred.ravel())
            )
        else:
            # Categorical cross-entropy
            loss = -np.mean(np.sum(y * np.log(y_pred), axis=1))

        # Add L2 regularization
        l2_term = 0.5 * self.alpha * sum(
            np.sum(W ** 2) for W in self.weights_
        )

        return loss + l2_term

    def _output_error(
        self,
        y: np.ndarray,
        y_pred: np.ndarray,
    ) -> np.ndarray:
        """Output layer error for cross-entropy loss."""
        return y_pred - y

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> "MLPClassifier":
        """
        Fit the MLP classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target class labels.

        Returns
        -------
        self : MLPClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]

        # Encode targets
        if self.n_classes_ == 2:
            y_encoded = (y == self.classes_[1]).astype(float).reshape(-1, 1)
            n_outputs = 1
        else:
            # One-hot encoding
            y_encoded = np.zeros((len(y), self.n_classes_))
            for i, cls in enumerate(self.classes_):
                y_encoded[y == cls, i] = 1
            n_outputs = self.n_classes_

        # Define layer sizes
        layer_sizes = [
            self.n_features_in_,
            *self.hidden_layer_sizes,
            n_outputs,
        ]
        self.n_layers_ = len(layer_sizes)

        # Initialize weights
        rng = check_random_state(self.random_state)
        if not self.warm_start or not hasattr(self, "weights_"):
            self.weights_, self.biases_ = self._initialize_weights(
                layer_sizes, rng
            )

        # Train
        if self.solver == "sgd":
            self._train_sgd(X, y_encoded, layer_sizes)
        else:  # adam
            self._train_adam(X, y_encoded, layer_sizes)

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
            Predicted class labels.
        """
        check_is_trained(self)
        X = check_array(X)

        activations, _ = self._forward_pass(X)
        y_pred = activations[-1]

        if self.n_classes_ == 2:
            return self.classes_[(y_pred.ravel() > 0.5).astype(int)]
        return self.classes_[np.argmax(y_pred, axis=1)]

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

        activations, _ = self._forward_pass(X)
        y_pred = activations[-1]

        if self.n_classes_ == 2:
            proba = np.column_stack([1 - y_pred, y_pred])
        else:
            proba = y_pred

        return proba

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="classifier",
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(
                binary=True,
                multiclass=True,
                predict_proba=True,
            ),
        )


class MLPRegressor(RegressorMixin, BaseMultiLayerPerceptron):
    """
    Multi-Layer Perceptron regressor.

    A feedforward neural network for regression tasks.

    Parameters
    ----------
    hidden_layer_sizes : tuple, default=(100,)
        Number of neurons in each hidden layer.
    activation : str, default="relu"
        Activation function: "relu", "tanh", "logistic", "identity".
    solver : str, default="adam"
        Optimizer: "sgd", "adam".
    alpha : float, default=0.0001
        L2 regularization strength.
    batch_size : int or "auto", default="auto"
        Mini-batch size.
    learning_rate : str, default="constant"
        Learning rate schedule: "constant", "invscaling", "adaptive".
    learning_rate_init : float, default=0.001
        Initial learning rate.
    max_iter : int, default=200
        Maximum iterations.
    random_state : int, optional
        Random seed.
    tol : float, default=1e-4
        Convergence tolerance.
    verbose : bool, default=False
        Print progress.
    early_stopping : bool, default=False
        Use early stopping.
    validation_fraction : float, default=0.1
        Validation set fraction.

    Attributes
    ----------
    n_features_in_ : int
        Number of input features.
    n_outputs_ : int
        Number of outputs.
    n_layers_ : int
        Number of layers.
    weights_ : list of ndarray
        Weight matrices.
    biases_ : list of ndarray
        Bias vectors.
    loss_curve_ : list
        Loss at each iteration.
    n_iter_ : int
        Number of iterations run.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.neural import MLPRegressor
    >>> X = np.array([[0], [1], [2], [3], [4]])
    >>> y = np.array([0.0, 1.0, 4.0, 9.0, 16.0])  # y = x^2
    >>> reg = MLPRegressor(hidden_layer_sizes=(10,), max_iter=500, random_state=42)
    >>> reg.train(X, y)
    MLPRegressor(hidden_layer_sizes=(10,), max_iter=500, random_state=42)
    """

    def _output_activation(self, z: np.ndarray) -> np.ndarray:
        """Identity activation for regression."""
        return z

    def _compute_loss(
        self,
        y: np.ndarray,
        y_pred: np.ndarray,
    ) -> float:
        """Mean squared error loss."""
        mse = np.mean((y - y_pred) ** 2)

        # Add L2 regularization
        l2_term = 0.5 * self.alpha * sum(
            np.sum(W ** 2) for W in self.weights_
        )

        return mse + l2_term

    def _output_error(
        self,
        y: np.ndarray,
        y_pred: np.ndarray,
    ) -> np.ndarray:
        """Output layer error for MSE loss."""
        return y_pred - y

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> "MLPRegressor":
        """
        Fit the MLP regressor.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,) or (n_samples, n_outputs)
            Target values.

        Returns
        -------
        self : MLPRegressor
        """
        X, y = check_X_y(X, y, y_numeric=True)

        self.n_features_in_ = X.shape[1]

        # Handle output shape
        if y.ndim == 1:
            y = y.reshape(-1, 1)
        self.n_outputs_ = y.shape[1]

        # Define layer sizes
        layer_sizes = [
            self.n_features_in_,
            *self.hidden_layer_sizes,
            self.n_outputs_,
        ]
        self.n_layers_ = len(layer_sizes)

        # Initialize weights
        rng = check_random_state(self.random_state)
        if not self.warm_start or not hasattr(self, "weights_"):
            self.weights_, self.biases_ = self._initialize_weights(
                layer_sizes, rng
            )

        # Train
        if self.solver == "sgd":
            self._train_sgd(X, y, layer_sizes)
        else:  # adam
            self._train_adam(X, y, layer_sizes)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,) or (n_samples, n_outputs)
            Predicted values.
        """
        check_is_trained(self)
        X = check_array(X)

        activations, _ = self._forward_pass(X)
        y_pred = activations[-1]

        if self.n_outputs_ == 1:
            return y_pred.ravel()
        return y_pred

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(
                multi_output=True,
            ),
        )
