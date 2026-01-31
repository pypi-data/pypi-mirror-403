"""
Reshape and utility layers.
"""

from __future__ import annotations

from typing import Tuple, Union, List
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.tensor import Tensor


class Flatten(Module):
    """
    Flatten tensor dimensions.

    Parameters
    ----------
    start_dim : int, default=1
        First dimension to flatten.
    end_dim : int, default=-1
        Last dimension to flatten.

    Examples
    --------
    >>> flatten = nn.Flatten()
    >>> x = Tensor(np.random.randn(32, 3, 28, 28))
    >>> output = flatten(x)  # (32, 2352)
    """

    def __init__(self, start_dim: int = 1, end_dim: int = -1):
        super().__init__()
        self.start_dim = start_dim
        self.end_dim = end_dim

    def forward(self, x: Tensor) -> Tensor:
        return x.flatten(self.start_dim, self.end_dim)

    def __repr__(self) -> str:
        return f"Flatten(start_dim={self.start_dim}, end_dim={self.end_dim})"


class Unflatten(Module):
    """
    Unflatten a tensor dimension.

    Parameters
    ----------
    dim : int
        Dimension to unflatten.
    unflattened_size : tuple
        New shape for the unflattened dimension.

    Examples
    --------
    >>> unflatten = nn.Unflatten(1, (3, 28, 28))
    >>> x = Tensor(np.random.randn(32, 2352))
    >>> output = unflatten(x)  # (32, 3, 28, 28)
    """

    def __init__(self, dim: int, unflattened_size: Tuple[int, ...]):
        super().__init__()
        self.dim = dim
        self.unflattened_size = unflattened_size

    def forward(self, x: Tensor) -> Tensor:
        shape = list(x.shape)
        new_shape = shape[:self.dim] + list(self.unflattened_size) + shape[self.dim + 1:]
        return x.reshape(*new_shape)

    def __repr__(self) -> str:
        return f"Unflatten(dim={self.dim}, unflattened_size={self.unflattened_size})"


class Reshape(Module):
    """
    Reshape tensor to specified shape.

    Parameters
    ----------
    shape : tuple
        Target shape. Use -1 for inferred dimension.

    Examples
    --------
    >>> reshape = nn.Reshape((3, -1))
    >>> x = Tensor(np.random.randn(32, 6, 10))
    >>> output = reshape(x)  # (32, 3, 20)
    """

    def __init__(self, shape: Tuple[int, ...]):
        super().__init__()
        self.shape = shape

    def forward(self, x: Tensor) -> Tensor:
        # Handle batch dimension
        batch_size = x.shape[0]
        new_shape = (batch_size,) + self.shape
        return x.reshape(*new_shape)

    def __repr__(self) -> str:
        return f"Reshape({self.shape})"


class Squeeze(Module):
    """
    Remove dimension of size 1.

    Parameters
    ----------
    dim : int, optional
        Dimension to squeeze. If None, squeeze all.
    """

    def __init__(self, dim: int = None):
        super().__init__()
        self.dim = dim

    def forward(self, x: Tensor) -> Tensor:
        return x.squeeze(self.dim)

    def __repr__(self) -> str:
        return f"Squeeze(dim={self.dim})"


class Unsqueeze(Module):
    """
    Add dimension of size 1.

    Parameters
    ----------
    dim : int
        Position to add new dimension.
    """

    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, x: Tensor) -> Tensor:
        return x.unsqueeze(self.dim)

    def __repr__(self) -> str:
        return f"Unsqueeze(dim={self.dim})"


class Permute(Module):
    """
    Permute tensor dimensions.

    Parameters
    ----------
    dims : tuple
        New dimension order.

    Examples
    --------
    >>> permute = nn.Permute((0, 2, 1))
    >>> x = Tensor(np.random.randn(32, 10, 20))
    >>> output = permute(x)  # (32, 20, 10)
    """

    def __init__(self, dims: Tuple[int, ...]):
        super().__init__()
        self.dims = dims

    def forward(self, x: Tensor) -> Tensor:
        return x.permute(self.dims)

    def __repr__(self) -> str:
        return f"Permute({self.dims})"


class Identity(Module):
    """
    Identity layer that returns input unchanged.

    Useful as a placeholder or for residual connections.
    """

    def forward(self, x: Tensor) -> Tensor:
        return x

    def __repr__(self) -> str:
        return "Identity()"


class Lambda(Module):
    """
    Apply a custom function.

    Parameters
    ----------
    fn : callable
        Function to apply.

    Examples
    --------
    >>> layer = nn.Lambda(lambda x: x * 2)
    >>> output = layer(x)
    """

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def forward(self, x: Tensor) -> Tensor:
        return self.fn(x)

    def __repr__(self) -> str:
        return f"Lambda({self.fn.__name__ if hasattr(self.fn, '__name__') else 'fn'})"
