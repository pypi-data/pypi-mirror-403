"""
Normalization layers.
"""

from __future__ import annotations

from typing import Optional, Union, Tuple, List
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.parameter import Parameter
from nalyst.nn.tensor import Tensor


class BatchNorm1d(Module):
    """
    Batch Normalization over 2D or 3D input.

    Parameters
    ----------
    num_features : int
        Number of features/channels.
    eps : float, default=1e-5
        Small constant for numerical stability.
    momentum : float, default=0.1
        Momentum for running statistics.
    affine : bool, default=True
        If True, learn scale and shift parameters.
    track_running_stats : bool, default=True
        If True, track running mean and variance.

    Examples
    --------
    >>> bn = nn.BatchNorm1d(100)
    >>> x = Tensor(np.random.randn(32, 100))
    >>> output = bn(x)
    """

    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        momentum: float = 0.1,
        affine: bool = True,
        track_running_stats: bool = True,
    ):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats

        if affine:
            self.weight = Parameter(np.ones(num_features))
            self.bias = Parameter(np.zeros(num_features))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

        if track_running_stats:
            self.register_buffer("running_mean", Tensor(np.zeros(num_features)))
            self.register_buffer("running_var", Tensor(np.ones(num_features)))
            self.num_batches_tracked = 0
        else:
            self.running_mean = None
            self.running_var = None

    def forward(self, x: Tensor) -> Tensor:
        if self.training:
            # Compute batch statistics
            if x.ndim == 2:
                mean = x.data.mean(axis=0)
                var = x.data.var(axis=0)
            else:  # 3D: (batch, features, length)
                mean = x.data.mean(axis=(0, 2))
                var = x.data.var(axis=(0, 2))

            # Update running statistics
            if self.track_running_stats:
                self.running_mean.data = (
                    (1 - self.momentum) * self.running_mean.data +
                    self.momentum * mean
                )
                self.running_var.data = (
                    (1 - self.momentum) * self.running_var.data +
                    self.momentum * var
                )
                self.num_batches_tracked += 1
        else:
            mean = self.running_mean.data
            var = self.running_var.data

        # Normalize
        if x.ndim == 2:
            x_norm = (x.data - mean) / np.sqrt(var + self.eps)
        else:
            x_norm = (x.data - mean[None, :, None]) / np.sqrt(var[None, :, None] + self.eps)

        output = Tensor(x_norm, requires_grad=x.requires_grad)

        # Apply affine transformation
        if self.affine:
            if x.ndim == 2:
                output = output * self.weight + self.bias
            else:
                output = output * self.weight.reshape(1, -1, 1) + self.bias.reshape(1, -1, 1)

        return output

    def __repr__(self) -> str:
        return f"BatchNorm1d({self.num_features}, eps={self.eps}, momentum={self.momentum})"


class BatchNorm2d(Module):
    """
    Batch Normalization over 4D input (batch, channels, height, width).

    Parameters
    ----------
    num_features : int
        Number of channels.
    eps : float, default=1e-5
        Small constant for numerical stability.
    momentum : float, default=0.1
        Momentum for running statistics.
    affine : bool, default=True
        If True, learn scale and shift parameters.
    track_running_stats : bool, default=True
        If True, track running mean and variance.

    Examples
    --------
    >>> bn = nn.BatchNorm2d(64)
    >>> x = Tensor(np.random.randn(32, 64, 28, 28))
    >>> output = bn(x)
    """

    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        momentum: float = 0.1,
        affine: bool = True,
        track_running_stats: bool = True,
    ):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats

        if affine:
            self.weight = Parameter(np.ones(num_features))
            self.bias = Parameter(np.zeros(num_features))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

        if track_running_stats:
            self.register_buffer("running_mean", Tensor(np.zeros(num_features)))
            self.register_buffer("running_var", Tensor(np.ones(num_features)))
            self.num_batches_tracked = 0
        else:
            self.running_mean = None
            self.running_var = None

    def forward(self, x: Tensor) -> Tensor:
        if self.training:
            # Compute batch statistics (over N, H, W)
            mean = x.data.mean(axis=(0, 2, 3))
            var = x.data.var(axis=(0, 2, 3))

            if self.track_running_stats:
                self.running_mean.data = (
                    (1 - self.momentum) * self.running_mean.data +
                    self.momentum * mean
                )
                self.running_var.data = (
                    (1 - self.momentum) * self.running_var.data +
                    self.momentum * var
                )
                self.num_batches_tracked += 1
        else:
            mean = self.running_mean.data
            var = self.running_var.data

        # Normalize
        x_norm = (x.data - mean[None, :, None, None]) / np.sqrt(var[None, :, None, None] + self.eps)

        output = Tensor(x_norm, requires_grad=x.requires_grad)

        if self.affine:
            output = (output * self.weight.reshape(1, -1, 1, 1) +
                     self.bias.reshape(1, -1, 1, 1))

        return output

    def __repr__(self) -> str:
        return f"BatchNorm2d({self.num_features}, eps={self.eps}, momentum={self.momentum})"


class LayerNorm(Module):
    """
    Layer Normalization.

    Parameters
    ----------
    normalized_shape : int or tuple
        Shape to normalize over.
    eps : float, default=1e-5
        Small constant for numerical stability.
    elementwise_affine : bool, default=True
        If True, learn scale and shift parameters.

    Examples
    --------
    >>> ln = nn.LayerNorm(512)
    >>> x = Tensor(np.random.randn(32, 10, 512))
    >>> output = ln(x)
    """

    def __init__(
        self,
        normalized_shape: Union[int, Tuple[int, ...], List[int]],
        eps: float = 1e-5,
        elementwise_affine: bool = True,
    ):
        super().__init__()
        if isinstance(normalized_shape, int):
            normalized_shape = (normalized_shape,)
        self.normalized_shape = tuple(normalized_shape)
        self.eps = eps
        self.elementwise_affine = elementwise_affine

        if elementwise_affine:
            self.weight = Parameter(np.ones(normalized_shape))
            self.bias = Parameter(np.zeros(normalized_shape))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        # Normalize over last len(normalized_shape) dimensions
        axes = tuple(range(-len(self.normalized_shape), 0))

        mean = x.data.mean(axis=axes, keepdims=True)
        var = x.data.var(axis=axes, keepdims=True)

        x_norm = (x.data - mean) / np.sqrt(var + self.eps)

        output = Tensor(x_norm, requires_grad=x.requires_grad)

        if self.elementwise_affine:
            output = output * self.weight + self.bias

        return output

    def __repr__(self) -> str:
        return f"LayerNorm({self.normalized_shape}, eps={self.eps})"


class GroupNorm(Module):
    """
    Group Normalization.

    Parameters
    ----------
    num_groups : int
        Number of groups to separate channels into.
    num_channels : int
        Number of channels.
    eps : float, default=1e-5
        Small constant for numerical stability.
    affine : bool, default=True
        If True, learn scale and shift parameters.

    Examples
    --------
    >>> gn = nn.GroupNorm(32, 256)  # 32 groups, 256 channels
    >>> x = Tensor(np.random.randn(32, 256, 14, 14))
    >>> output = gn(x)
    """

    def __init__(
        self,
        num_groups: int,
        num_channels: int,
        eps: float = 1e-5,
        affine: bool = True,
    ):
        super().__init__()
        if num_channels % num_groups != 0:
            raise ValueError("num_channels must be divisible by num_groups")

        self.num_groups = num_groups
        self.num_channels = num_channels
        self.eps = eps
        self.affine = affine

        if affine:
            self.weight = Parameter(np.ones(num_channels))
            self.bias = Parameter(np.zeros(num_channels))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        batch_size, channels = x.shape[:2]
        spatial_shape = x.shape[2:]

        # Reshape to (N, G, C//G, *spatial)
        x_grouped = x.data.reshape(batch_size, self.num_groups, -1)

        # Normalize within each group
        mean = x_grouped.mean(axis=2, keepdims=True)
        var = x_grouped.var(axis=2, keepdims=True)

        x_norm = (x_grouped - mean) / np.sqrt(var + self.eps)
        x_norm = x_norm.reshape(x.shape)

        output = Tensor(x_norm, requires_grad=x.requires_grad)

        if self.affine:
            shape = [1, -1] + [1] * len(spatial_shape)
            output = output * self.weight.reshape(*shape) + self.bias.reshape(*shape)

        return output

    def __repr__(self) -> str:
        return f"GroupNorm({self.num_groups}, {self.num_channels}, eps={self.eps})"


class InstanceNorm1d(Module):
    """
    Instance Normalization for 1D inputs.

    Parameters
    ----------
    num_features : int
        Number of features/channels.
    eps : float, default=1e-5
        Small constant for numerical stability.
    affine : bool, default=False
        If True, learn scale and shift parameters.
    """

    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        affine: bool = False,
    ):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.affine = affine

        if affine:
            self.weight = Parameter(np.ones(num_features))
            self.bias = Parameter(np.zeros(num_features))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        # Normalize over length dimension
        mean = x.data.mean(axis=2, keepdims=True)
        var = x.data.var(axis=2, keepdims=True)

        x_norm = (x.data - mean) / np.sqrt(var + self.eps)

        output = Tensor(x_norm, requires_grad=x.requires_grad)

        if self.affine:
            output = output * self.weight.reshape(1, -1, 1) + self.bias.reshape(1, -1, 1)

        return output

    def __repr__(self) -> str:
        return f"InstanceNorm1d({self.num_features}, eps={self.eps})"


class InstanceNorm2d(Module):
    """
    Instance Normalization for 2D inputs.

    Parameters
    ----------
    num_features : int
        Number of features/channels.
    eps : float, default=1e-5
        Small constant for numerical stability.
    affine : bool, default=False
        If True, learn scale and shift parameters.

    Examples
    --------
    >>> norm = nn.InstanceNorm2d(64)
    >>> x = Tensor(np.random.randn(8, 64, 32, 32))
    >>> output = norm(x)
    """

    def __init__(
        self,
        num_features: int,
        eps: float = 1e-5,
        affine: bool = False,
    ):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.affine = affine

        if affine:
            self.weight = Parameter(np.ones(num_features))
            self.bias = Parameter(np.zeros(num_features))
        else:
            self.register_parameter("weight", None)
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        # Normalize over spatial dimensions (H, W)
        mean = x.data.mean(axis=(2, 3), keepdims=True)
        var = x.data.var(axis=(2, 3), keepdims=True)

        x_norm = (x.data - mean) / np.sqrt(var + self.eps)

        output = Tensor(x_norm, requires_grad=x.requires_grad)

        if self.affine:
            output = output * self.weight.reshape(1, -1, 1, 1) + self.bias.reshape(1, -1, 1, 1)

        return output

    def __repr__(self) -> str:
        return f"InstanceNorm2d({self.num_features}, eps={self.eps})"
