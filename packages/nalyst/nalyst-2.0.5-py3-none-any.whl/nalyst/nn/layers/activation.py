"""
Activation layers.
"""

from __future__ import annotations

import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.tensor import Tensor


class ReLU(Module):
    """
    ReLU activation: max(0, x)

    Parameters
    ----------
    inplace : bool, default=False
        Not used, kept for API compatibility.

    Examples
    --------
    >>> relu = nn.ReLU()
    >>> x = Tensor([-1, 0, 1, 2])
    >>> output = relu(x)  # [0, 0, 1, 2]
    """

    def __init__(self, inplace: bool = False):
        super().__init__()
        self.inplace = inplace

    def forward(self, x: Tensor) -> Tensor:
        return x.relu()

    def __repr__(self) -> str:
        return "ReLU()"


class LeakyReLU(Module):
    """
    Leaky ReLU activation: max(negative_slope * x, x)

    Parameters
    ----------
    negative_slope : float, default=0.01
        Controls the angle of the negative slope.
    inplace : bool, default=False
        Not used.

    Examples
    --------
    >>> lrelu = nn.LeakyReLU(0.1)
    >>> x = Tensor([-1, 0, 1])
    >>> output = lrelu(x)  # [-0.1, 0, 1]
    """

    def __init__(self, negative_slope: float = 0.01, inplace: bool = False):
        super().__init__()
        self.negative_slope = negative_slope

    def forward(self, x: Tensor) -> Tensor:
        return x.leaky_relu(self.negative_slope)

    def __repr__(self) -> str:
        return f"LeakyReLU(negative_slope={self.negative_slope})"


class ELU(Module):
    """
    Exponential Linear Unit activation.

    ELU(x) = x if x > 0 else alpha * (exp(x) - 1)

    Parameters
    ----------
    alpha : float, default=1.0
        Scale for the negative part.
    inplace : bool, default=False
        Not used.
    """

    def __init__(self, alpha: float = 1.0, inplace: bool = False):
        super().__init__()
        self.alpha = alpha

    def forward(self, x: Tensor) -> Tensor:
        pos = np.maximum(0, x.data)
        neg = self.alpha * (np.exp(np.minimum(0, x.data)) - 1)

        out = Tensor(
            pos + neg,
            requires_grad=x.requires_grad,
            _children=(x,),
            _op="elu",
        )

        def _backward():
            if x.requires_grad:
                grad = np.where(x.data > 0, 1, out.data + self.alpha)
                if x.grad is None:
                    x.grad = np.zeros_like(x.data)
                x.grad = x.grad + out.grad * grad

        out._backward = _backward
        return out

    def __repr__(self) -> str:
        return f"ELU(alpha={self.alpha})"


class SELU(Module):
    """
    Scaled Exponential Linear Unit activation.

    Self-normalizing activation for neural networks.
    """

    def __init__(self, inplace: bool = False):
        super().__init__()
        self.alpha = 1.6732632423543772848170429916717
        self.scale = 1.0507009873554804934193349852946

    def forward(self, x: Tensor) -> Tensor:
        pos = np.maximum(0, x.data)
        neg = self.alpha * (np.exp(np.minimum(0, x.data)) - 1)

        out = Tensor(
            self.scale * (pos + neg),
            requires_grad=x.requires_grad,
            _children=(x,),
            _op="selu",
        )

        def _backward():
            if x.requires_grad:
                pos_grad = np.where(x.data > 0, self.scale, 0)
                neg_grad = np.where(x.data <= 0, self.scale * self.alpha * np.exp(x.data), 0)
                if x.grad is None:
                    x.grad = np.zeros_like(x.data)
                x.grad = x.grad + out.grad * (pos_grad + neg_grad)

        out._backward = _backward
        return out

    def __repr__(self) -> str:
        return "SELU()"


class GELU(Module):
    """
    Gaussian Error Linear Unit activation.

    Used in Transformer models.

    Parameters
    ----------
    approximate : str, default='none'
        If 'tanh', use tanh approximation.
    """

    def __init__(self, approximate: str = 'none'):
        super().__init__()
        self.approximate = approximate

    def forward(self, x: Tensor) -> Tensor:
        return x.gelu()

    def __repr__(self) -> str:
        return f"GELU(approximate='{self.approximate}')"


class Sigmoid(Module):
    """
    Sigmoid activation: 1 / (1 + exp(-x))

    Examples
    --------
    >>> sigmoid = nn.Sigmoid()
    >>> x = Tensor([0])
    >>> output = sigmoid(x)  # [0.5]
    """

    def forward(self, x: Tensor) -> Tensor:
        return x.sigmoid()

    def __repr__(self) -> str:
        return "Sigmoid()"


class Tanh(Module):
    """
    Tanh activation: (exp(x) - exp(-x)) / (exp(x) + exp(-x))

    Examples
    --------
    >>> tanh = nn.Tanh()
    >>> x = Tensor([0])
    >>> output = tanh(x)  # [0]
    """

    def forward(self, x: Tensor) -> Tensor:
        return x.tanh()

    def __repr__(self) -> str:
        return "Tanh()"


class Softmax(Module):
    """
    Softmax activation.

    Parameters
    ----------
    dim : int, default=-1
        Dimension along which to compute softmax.

    Examples
    --------
    >>> softmax = nn.Softmax(dim=1)
    >>> x = Tensor([[1, 2, 3]])
    >>> output = softmax(x)  # probabilities summing to 1
    """

    def __init__(self, dim: int = -1):
        super().__init__()
        self.dim = dim

    def forward(self, x: Tensor) -> Tensor:
        return x.softmax(axis=self.dim)

    def __repr__(self) -> str:
        return f"Softmax(dim={self.dim})"


class LogSoftmax(Module):
    """
    Log-Softmax activation.

    More numerically stable than log(softmax(x)).

    Parameters
    ----------
    dim : int, default=-1
        Dimension along which to compute.
    """

    def __init__(self, dim: int = -1):
        super().__init__()
        self.dim = dim

    def forward(self, x: Tensor) -> Tensor:
        return x.log_softmax(axis=self.dim)

    def __repr__(self) -> str:
        return f"LogSoftmax(dim={self.dim})"


class Swish(Module):
    """
    Swish activation: x * sigmoid(x)

    Also known as SiLU (Sigmoid Linear Unit).
    """

    def forward(self, x: Tensor) -> Tensor:
        return x * x.sigmoid()

    def __repr__(self) -> str:
        return "Swish()"


class Mish(Module):
    """
    Mish activation: x * tanh(softplus(x))

    Where softplus(x) = log(1 + exp(x))
    """

    def forward(self, x: Tensor) -> Tensor:
        # softplus = log(1 + exp(x))
        softplus = Tensor(np.log(1 + np.exp(x.data)), requires_grad=x.requires_grad)
        return x * softplus.tanh()

    def __repr__(self) -> str:
        return "Mish()"


class Hardswish(Module):
    """
    Hard Swish activation (efficient approximation of Swish).
    """

    def forward(self, x: Tensor) -> Tensor:
        relu6 = np.clip(x.data + 3, 0, 6)
        out_data = x.data * relu6 / 6

        out = Tensor(out_data, requires_grad=x.requires_grad, _children=(x,), _op="hardswish")

        def _backward():
            if x.requires_grad:
                grad = np.where(
                    x.data <= -3, 0,
                    np.where(x.data >= 3, 1, x.data / 3 + 0.5)
                )
                if x.grad is None:
                    x.grad = np.zeros_like(x.data)
                x.grad = x.grad + out.grad * grad

        out._backward = _backward
        return out

    def __repr__(self) -> str:
        return "Hardswish()"


class Hardsigmoid(Module):
    """
    Hard Sigmoid activation (efficient approximation of Sigmoid).
    """

    def forward(self, x: Tensor) -> Tensor:
        out_data = np.clip(x.data / 6 + 0.5, 0, 1)

        out = Tensor(out_data, requires_grad=x.requires_grad, _children=(x,), _op="hardsigmoid")

        def _backward():
            if x.requires_grad:
                grad = np.where((x.data > -3) & (x.data < 3), 1/6, 0)
                if x.grad is None:
                    x.grad = np.zeros_like(x.data)
                x.grad = x.grad + out.grad * grad

        out._backward = _backward
        return out

    def __repr__(self) -> str:
        return "Hardsigmoid()"


class PReLU(Module):
    """
    Parametric ReLU with learnable slope.

    Parameters
    ----------
    num_parameters : int, default=1
        Number of learnable parameters.
    init : float, default=0.25
        Initial value of the slope.
    """

    def __init__(self, num_parameters: int = 1, init: float = 0.25):
        super().__init__()
        from nalyst.nn.parameter import Parameter
        self.weight = Parameter(np.full(num_parameters, init))

    def forward(self, x: Tensor) -> Tensor:
        pos = np.maximum(0, x.data)
        neg = self.weight.data * np.minimum(0, x.data)

        out = Tensor(
            pos + neg,
            requires_grad=x.requires_grad,
            _children=(x,),
            _op="prelu",
        )

        return out

    def __repr__(self) -> str:
        return f"PReLU(num_parameters={self.weight.size})"
