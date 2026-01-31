"""
Dropout layers.
"""

from __future__ import annotations

import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.tensor import Tensor


class Dropout(Module):
    """
    Randomly zeroes elements during training.

    Parameters
    ----------
    p : float, default=0.5
        Probability of an element being zeroed.
    inplace : bool, default=False
        Not used.

    Examples
    --------
    >>> dropout = nn.Dropout(0.5)
    >>> x = Tensor(np.ones(10))
    >>> model.train()
    >>> output = dropout(x)  # ~half elements zeroed
    """

    def __init__(self, p: float = 0.5, inplace: bool = False):
        super().__init__()
        if not 0 <= p < 1:
            raise ValueError(f"dropout probability has to be between 0 and 1, got {p}")
        self.p = p

    def forward(self, x: Tensor) -> Tensor:
        if not self.training or self.p == 0:
            return x

        # Generate mask
        mask = np.random.binomial(1, 1 - self.p, size=x.shape).astype(np.float32)

        # Scale by 1/(1-p) to maintain expected value
        scale = 1 / (1 - self.p)

        out = Tensor(
            x.data * mask * scale,
            requires_grad=x.requires_grad,
            _children=(x,),
            _op="dropout",
        )

        def _backward():
            if x.requires_grad:
                if x.grad is None:
                    x.grad = np.zeros_like(x.data)
                x.grad = x.grad + out.grad * mask * scale

        out._backward = _backward
        return out

    def __repr__(self) -> str:
        return f"Dropout(p={self.p})"


class Dropout2d(Module):
    """
    Randomly zeroes entire channels during training.

    Parameters
    ----------
    p : float, default=0.5
        Probability of a channel being zeroed.
    inplace : bool, default=False
        Not used.

    Examples
    --------
    >>> dropout = nn.Dropout2d(0.2)
    >>> x = Tensor(np.random.randn(8, 64, 28, 28))
    >>> output = dropout(x)
    """

    def __init__(self, p: float = 0.5, inplace: bool = False):
        super().__init__()
        if not 0 <= p < 1:
            raise ValueError(f"dropout probability has to be between 0 and 1, got {p}")
        self.p = p

    def forward(self, x: Tensor) -> Tensor:
        if not self.training or self.p == 0:
            return x

        # Generate channel-wise mask
        batch_size, channels = x.shape[:2]
        mask = np.random.binomial(1, 1 - self.p, size=(batch_size, channels)).astype(np.float32)

        # Expand mask to match spatial dimensions
        for _ in range(len(x.shape) - 2):
            mask = np.expand_dims(mask, -1)

        mask = np.broadcast_to(mask, x.shape)
        scale = 1 / (1 - self.p)

        out = Tensor(
            x.data * mask * scale,
            requires_grad=x.requires_grad,
            _children=(x,),
            _op="dropout2d",
        )

        def _backward():
            if x.requires_grad:
                if x.grad is None:
                    x.grad = np.zeros_like(x.data)
                x.grad = x.grad + out.grad * mask * scale

        out._backward = _backward
        return out

    def __repr__(self) -> str:
        return f"Dropout2d(p={self.p})"


class AlphaDropout(Module):
    """
    Alpha Dropout for SELU networks.

    Maintains the self-normalizing property of SELU.

    Parameters
    ----------
    p : float, default=0.5
        Dropout probability.
    """

    def __init__(self, p: float = 0.5):
        super().__init__()
        self.p = p
        # SELU parameters
        self.alpha = 1.6732632423543772848170429916717
        self.scale = 1.0507009873554804934193349852946

    def forward(self, x: Tensor) -> Tensor:
        if not self.training or self.p == 0:
            return x

        # Alpha dropout parameters
        alpha_p = -self.alpha * self.scale
        a = ((1 - self.p) * (1 + self.p * alpha_p ** 2)) ** -0.5
        b = -a * alpha_p * self.p

        # Generate mask
        mask = np.random.binomial(1, 1 - self.p, size=x.shape).astype(np.float32)

        # Apply alpha dropout
        out_data = a * (mask * x.data + (1 - mask) * alpha_p) + b

        out = Tensor(
            out_data,
            requires_grad=x.requires_grad,
            _children=(x,),
            _op="alpha_dropout",
        )

        def _backward():
            if x.requires_grad:
                if x.grad is None:
                    x.grad = np.zeros_like(x.data)
                x.grad = x.grad + out.grad * mask * a

        out._backward = _backward
        return out

    def __repr__(self) -> str:
        return f"AlphaDropout(p={self.p})"


class DropPath(Module):
    """
    Drop paths (stochastic depth) per sample.

    Used in Vision Transformers and other modern architectures.

    Parameters
    ----------
    p : float, default=0.0
        Probability of dropping a path.
    """

    def __init__(self, p: float = 0.0):
        super().__init__()
        self.p = p

    def forward(self, x: Tensor) -> Tensor:
        if not self.training or self.p == 0:
            return x

        # Sample-wise mask
        keep_prob = 1 - self.p
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)
        mask = np.random.binomial(1, keep_prob, size=shape).astype(np.float32)
        mask = np.broadcast_to(mask, x.shape)

        scale = 1 / keep_prob

        out = Tensor(
            x.data * mask * scale,
            requires_grad=x.requires_grad,
            _children=(x,),
            _op="droppath",
        )

        return out

    def __repr__(self) -> str:
        return f"DropPath(p={self.p})"
