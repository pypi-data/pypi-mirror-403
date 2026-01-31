"""
Pooling layers.
"""

from __future__ import annotations

from typing import Union, Tuple
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.tensor import Tensor


def _pair(x):
    if isinstance(x, (tuple, list)):
        return tuple(x)
    return (x, x)


class MaxPool1d(Module):
    """
    1D max pooling.

    Parameters
    ----------
    kernel_size : int
        Size of the pooling window.
    stride : int, optional
        Stride. Defaults to kernel_size.
    padding : int, default=0
        Zero-padding.

    Examples
    --------
    >>> pool = nn.MaxPool1d(2)
    >>> x = Tensor(np.random.randn(1, 16, 50))
    >>> output = pool(x)  # (1, 16, 25)
    """

    def __init__(
        self,
        kernel_size: int,
        stride: int = None,
        padding: int = 0,
    ):
        super().__init__()
        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size
        self.padding = padding

    def forward(self, x: Tensor) -> Tensor:
        batch_size, channels, length = x.shape

        # Padding
        if self.padding > 0:
            x_padded = np.pad(
                x.data,
                ((0, 0), (0, 0), (self.padding, self.padding)),
                mode='constant',
                constant_values=-np.inf
            )
        else:
            x_padded = x.data

        out_len = (length + 2 * self.padding - self.kernel_size) // self.stride + 1
        output = np.zeros((batch_size, channels, out_len), dtype=np.float32)

        for i in range(out_len):
            start = i * self.stride
            end = start + self.kernel_size
            output[:, :, i] = np.max(x_padded[:, :, start:end], axis=2)

        return Tensor(output, requires_grad=x.requires_grad)

    def __repr__(self) -> str:
        return f"MaxPool1d(kernel_size={self.kernel_size}, stride={self.stride})"


class MaxPool2d(Module):
    """
    2D max pooling.

    Parameters
    ----------
    kernel_size : int or tuple
        Size of the pooling window.
    stride : int or tuple, optional
        Stride. Defaults to kernel_size.
    padding : int or tuple, default=0
        Zero-padding.

    Examples
    --------
    >>> pool = nn.MaxPool2d(2)
    >>> x = Tensor(np.random.randn(1, 64, 32, 32))
    >>> output = pool(x)  # (1, 64, 16, 16)
    """

    def __init__(
        self,
        kernel_size: Union[int, Tuple[int, int]],
        stride: Union[int, Tuple[int, int]] = None,
        padding: Union[int, Tuple[int, int]] = 0,
    ):
        super().__init__()
        self.kernel_size = _pair(kernel_size)
        self.stride = _pair(stride) if stride is not None else self.kernel_size
        self.padding = _pair(padding)

    def forward(self, x: Tensor) -> Tensor:
        batch_size, channels, in_h, in_w = x.shape
        kh, kw = self.kernel_size
        sh, sw = self.stride
        ph, pw = self.padding

        # Padding
        if ph > 0 or pw > 0:
            x_padded = np.pad(
                x.data,
                ((0, 0), (0, 0), (ph, ph), (pw, pw)),
                mode='constant',
                constant_values=-np.inf
            )
        else:
            x_padded = x.data

        out_h = (in_h + 2 * ph - kh) // sh + 1
        out_w = (in_w + 2 * pw - kw) // sw + 1

        output = np.zeros((batch_size, channels, out_h, out_w), dtype=np.float32)

        for i in range(out_h):
            for j in range(out_w):
                h_start = i * sh
                w_start = j * sw
                window = x_padded[:, :, h_start:h_start+kh, w_start:w_start+kw]
                output[:, :, i, j] = np.max(window, axis=(2, 3))

        return Tensor(output, requires_grad=x.requires_grad)

    def __repr__(self) -> str:
        return f"MaxPool2d(kernel_size={self.kernel_size}, stride={self.stride})"


class AvgPool1d(Module):
    """
    1D average pooling.

    Parameters
    ----------
    kernel_size : int
        Size of the pooling window.
    stride : int, optional
        Stride. Defaults to kernel_size.
    padding : int, default=0
        Zero-padding.
    """

    def __init__(
        self,
        kernel_size: int,
        stride: int = None,
        padding: int = 0,
    ):
        super().__init__()
        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size
        self.padding = padding

    def forward(self, x: Tensor) -> Tensor:
        batch_size, channels, length = x.shape

        if self.padding > 0:
            x_padded = np.pad(
                x.data,
                ((0, 0), (0, 0), (self.padding, self.padding)),
                mode='constant'
            )
        else:
            x_padded = x.data

        out_len = (length + 2 * self.padding - self.kernel_size) // self.stride + 1
        output = np.zeros((batch_size, channels, out_len), dtype=np.float32)

        for i in range(out_len):
            start = i * self.stride
            end = start + self.kernel_size
            output[:, :, i] = np.mean(x_padded[:, :, start:end], axis=2)

        return Tensor(output, requires_grad=x.requires_grad)

    def __repr__(self) -> str:
        return f"AvgPool1d(kernel_size={self.kernel_size}, stride={self.stride})"


class AvgPool2d(Module):
    """
    2D average pooling.

    Parameters
    ----------
    kernel_size : int or tuple
        Size of the pooling window.
    stride : int or tuple, optional
        Stride. Defaults to kernel_size.
    padding : int or tuple, default=0
        Zero-padding.
    """

    def __init__(
        self,
        kernel_size: Union[int, Tuple[int, int]],
        stride: Union[int, Tuple[int, int]] = None,
        padding: Union[int, Tuple[int, int]] = 0,
    ):
        super().__init__()
        self.kernel_size = _pair(kernel_size)
        self.stride = _pair(stride) if stride is not None else self.kernel_size
        self.padding = _pair(padding)

    def forward(self, x: Tensor) -> Tensor:
        batch_size, channels, in_h, in_w = x.shape
        kh, kw = self.kernel_size
        sh, sw = self.stride
        ph, pw = self.padding

        if ph > 0 or pw > 0:
            x_padded = np.pad(
                x.data,
                ((0, 0), (0, 0), (ph, ph), (pw, pw)),
                mode='constant'
            )
        else:
            x_padded = x.data

        out_h = (in_h + 2 * ph - kh) // sh + 1
        out_w = (in_w + 2 * pw - kw) // sw + 1

        output = np.zeros((batch_size, channels, out_h, out_w), dtype=np.float32)

        for i in range(out_h):
            for j in range(out_w):
                h_start = i * sh
                w_start = j * sw
                window = x_padded[:, :, h_start:h_start+kh, w_start:w_start+kw]
                output[:, :, i, j] = np.mean(window, axis=(2, 3))

        return Tensor(output, requires_grad=x.requires_grad)

    def __repr__(self) -> str:
        return f"AvgPool2d(kernel_size={self.kernel_size}, stride={self.stride})"


class AdaptiveAvgPool1d(Module):
    """
    1D adaptive average pooling.

    Parameters
    ----------
    output_size : int
        The target output size.
    """

    def __init__(self, output_size: int):
        super().__init__()
        self.output_size = output_size

    def forward(self, x: Tensor) -> Tensor:
        batch_size, channels, length = x.shape

        output = np.zeros((batch_size, channels, self.output_size), dtype=np.float32)

        for i in range(self.output_size):
            start = int(i * length / self.output_size)
            end = int((i + 1) * length / self.output_size)
            output[:, :, i] = np.mean(x.data[:, :, start:end], axis=2)

        return Tensor(output, requires_grad=x.requires_grad)

    def __repr__(self) -> str:
        return f"AdaptiveAvgPool1d(output_size={self.output_size})"


class AdaptiveAvgPool2d(Module):
    """
    2D adaptive average pooling.

    Parameters
    ----------
    output_size : int or tuple
        The target output size (H, W).

    Examples
    --------
    >>> pool = nn.AdaptiveAvgPool2d((1, 1))
    >>> x = Tensor(np.random.randn(1, 512, 7, 7))
    >>> output = pool(x)  # (1, 512, 1, 1)
    """

    def __init__(self, output_size: Union[int, Tuple[int, int]]):
        super().__init__()
        self.output_size = _pair(output_size)

    def forward(self, x: Tensor) -> Tensor:
        batch_size, channels, in_h, in_w = x.shape
        out_h, out_w = self.output_size

        output = np.zeros((batch_size, channels, out_h, out_w), dtype=np.float32)

        for i in range(out_h):
            for j in range(out_w):
                h_start = int(i * in_h / out_h)
                h_end = int((i + 1) * in_h / out_h)
                w_start = int(j * in_w / out_w)
                w_end = int((j + 1) * in_w / out_w)

                output[:, :, i, j] = np.mean(
                    x.data[:, :, h_start:h_end, w_start:w_end],
                    axis=(2, 3)
                )

        return Tensor(output, requires_grad=x.requires_grad)

    def __repr__(self) -> str:
        return f"AdaptiveAvgPool2d(output_size={self.output_size})"


class GlobalAvgPool2d(Module):
    """
    Global average pooling over spatial dimensions.

    Equivalent to AdaptiveAvgPool2d((1, 1)).

    Examples
    --------
    >>> pool = nn.GlobalAvgPool2d()
    >>> x = Tensor(np.random.randn(1, 512, 7, 7))
    >>> output = pool(x)  # (1, 512, 1, 1)
    """

    def __init__(self):
        super().__init__()
        self.pool = AdaptiveAvgPool2d((1, 1))

    def forward(self, x: Tensor) -> Tensor:
        return self.pool(x)

    def __repr__(self) -> str:
        return "GlobalAvgPool2d()"
