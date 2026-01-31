"""
Convolutional layers.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.parameter import Parameter
from nalyst.nn.tensor import Tensor


def _pair(x):
    """Convert x to a tuple of 2 elements."""
    if isinstance(x, (tuple, list)):
        return tuple(x)
    return (x, x)


def _triple(x):
    """Convert x to a tuple of 3 elements."""
    if isinstance(x, (tuple, list)):
        return tuple(x)
    return (x, x, x)


class Conv1d(Module):
    """
    1D convolution over an input signal.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int
        Size of the convolving kernel.
    stride : int, default=1
        Stride of the convolution.
    padding : int, default=0
        Zero-padding added to both sides.
    dilation : int, default=1
        Spacing between kernel elements.
    groups : int, default=1
        Number of blocked connections from input to output channels.
    bias : bool, default=True
        If True, adds a learnable bias.

    Examples
    --------
    >>> conv = nn.Conv1d(16, 33, 3)
    >>> x = Tensor(np.random.randn(20, 16, 50))  # (batch, channels, length)
    >>> output = conv(x)
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1,
        groups: int = 1,
        bias: bool = True,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.groups = groups

        # Initialize weights
        k = groups / (in_channels * kernel_size)
        self.weight = Parameter(
            np.random.uniform(
                -np.sqrt(k), np.sqrt(k),
                (out_channels, in_channels // groups, kernel_size)
            )
        )

        if bias:
            self.bias = Parameter(
                np.random.uniform(-np.sqrt(k), np.sqrt(k), (out_channels,))
            )
        else:
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        """
        Apply 1D convolution.

        Parameters
        ----------
        x : Tensor
            Input of shape (batch, in_channels, length).

        Returns
        -------
        Tensor
            Output of shape (batch, out_channels, out_length).
        """
        batch_size, in_channels, in_length = x.shape

        # Apply padding
        if self.padding > 0:
            x_padded = np.pad(
                x.data,
                ((0, 0), (0, 0), (self.padding, self.padding)),
                mode='constant'
            )
        else:
            x_padded = x.data

        # Calculate output size
        out_length = (in_length + 2 * self.padding - self.dilation * (self.kernel_size - 1) - 1) // self.stride + 1

        # Perform convolution
        output = np.zeros((batch_size, self.out_channels, out_length), dtype=np.float32)

        for b in range(batch_size):
            for oc in range(self.out_channels):
                for ol in range(out_length):
                    l_start = ol * self.stride

                    # Sum over input channels and kernel
                    for ic in range(in_channels // self.groups):
                        for k in range(self.kernel_size):
                            l_idx = l_start + k * self.dilation
                            output[b, oc, ol] += (
                                x_padded[b, ic, l_idx] *
                                self.weight.data[oc, ic, k]
                            )

        result = Tensor(output, requires_grad=x.requires_grad)

        if self.bias is not None:
            result = result + self.bias.reshape(1, -1, 1)

        return result

    def __repr__(self) -> str:
        return (f"Conv1d({self.in_channels}, {self.out_channels}, "
                f"kernel_size={self.kernel_size}, stride={self.stride})")


class Conv2d(Module):
    """
    2D convolution over an input image.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int or tuple
        Size of the convolving kernel.
    stride : int or tuple, default=1
        Stride of the convolution.
    padding : int or tuple, default=0
        Zero-padding added to both sides.
    dilation : int or tuple, default=1
        Spacing between kernel elements.
    groups : int, default=1
        Number of blocked connections.
    bias : bool, default=True
        If True, adds a learnable bias.

    Examples
    --------
    >>> conv = nn.Conv2d(3, 64, kernel_size=3, padding=1)
    >>> x = Tensor(np.random.randn(32, 3, 224, 224))
    >>> output = conv(x)  # (32, 64, 224, 224)
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Union[int, Tuple[int, int]],
        stride: Union[int, Tuple[int, int]] = 1,
        padding: Union[int, Tuple[int, int]] = 0,
        dilation: Union[int, Tuple[int, int]] = 1,
        groups: int = 1,
        bias: bool = True,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = _pair(kernel_size)
        self.stride = _pair(stride)
        self.padding = _pair(padding)
        self.dilation = _pair(dilation)
        self.groups = groups

        # Initialize weights (Kaiming initialization)
        k = groups / (in_channels * self.kernel_size[0] * self.kernel_size[1])
        self.weight = Parameter(
            np.random.uniform(
                -np.sqrt(k), np.sqrt(k),
                (out_channels, in_channels // groups, self.kernel_size[0], self.kernel_size[1])
            )
        )

        if bias:
            self.bias = Parameter(
                np.random.uniform(-np.sqrt(k), np.sqrt(k), (out_channels,))
            )
        else:
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        """
        Apply 2D convolution.

        Parameters
        ----------
        x : Tensor
            Input of shape (batch, in_channels, height, width).

        Returns
        -------
        Tensor
            Output of shape (batch, out_channels, out_height, out_width).
        """
        batch_size, in_channels, in_h, in_w = x.shape
        kh, kw = self.kernel_size
        sh, sw = self.stride
        ph, pw = self.padding
        dh, dw = self.dilation

        # Apply padding
        if ph > 0 or pw > 0:
            x_padded = np.pad(
                x.data,
                ((0, 0), (0, 0), (ph, ph), (pw, pw)),
                mode='constant'
            )
        else:
            x_padded = x.data

        # Calculate output size
        out_h = (in_h + 2 * ph - dh * (kh - 1) - 1) // sh + 1
        out_w = (in_w + 2 * pw - dw * (kw - 1) - 1) // sw + 1

        # Use im2col for efficient convolution
        output = self._conv2d_im2col(x_padded, out_h, out_w, batch_size)

        result = Tensor(output, requires_grad=x.requires_grad)

        if self.bias is not None:
            result = result + self.bias.reshape(1, -1, 1, 1)

        return result

    def _conv2d_im2col(self, x_padded, out_h, out_w, batch_size):
        """Efficient convolution using im2col."""
        kh, kw = self.kernel_size
        sh, sw = self.stride
        dh, dw = self.dilation

        # Create column matrix from input
        in_ch = self.in_channels // self.groups

        # Output array
        output = np.zeros((batch_size, self.out_channels, out_h, out_w), dtype=np.float32)

        # Reshape weight for matrix multiplication
        weight_reshaped = self.weight.data.reshape(self.out_channels, -1)

        for b in range(batch_size):
            # Create patches
            patches = np.zeros((in_ch * kh * kw, out_h * out_w), dtype=np.float32)

            for oh in range(out_h):
                for ow in range(out_w):
                    h_start = oh * sh
                    w_start = ow * sw

                    patch = []
                    for c in range(in_ch):
                        for i in range(kh):
                            for j in range(kw):
                                h_idx = h_start + i * dh
                                w_idx = w_start + j * dw
                                patch.append(x_padded[b, c, h_idx, w_idx])

                    patches[:, oh * out_w + ow] = patch

            # Matrix multiplication
            out_flat = weight_reshaped @ patches
            output[b] = out_flat.reshape(self.out_channels, out_h, out_w)

        return output

    def __repr__(self) -> str:
        return (f"Conv2d({self.in_channels}, {self.out_channels}, "
                f"kernel_size={self.kernel_size}, stride={self.stride}, "
                f"padding={self.padding})")


class Conv3d(Module):
    """
    3D convolution over an input volume.

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int or tuple
        Size of the convolving kernel.
    stride : int or tuple, default=1
        Stride of the convolution.
    padding : int or tuple, default=0
        Zero-padding added to all sides.
    bias : bool, default=True
        If True, adds a learnable bias.

    Examples
    --------
    >>> conv = nn.Conv3d(3, 64, kernel_size=3)
    >>> x = Tensor(np.random.randn(2, 3, 16, 224, 224))
    >>> output = conv(x)
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Union[int, Tuple[int, int, int]],
        stride: Union[int, Tuple[int, int, int]] = 1,
        padding: Union[int, Tuple[int, int, int]] = 0,
        bias: bool = True,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = _triple(kernel_size)
        self.stride = _triple(stride)
        self.padding = _triple(padding)

        k = 1 / (in_channels * np.prod(self.kernel_size))
        self.weight = Parameter(
            np.random.uniform(
                -np.sqrt(k), np.sqrt(k),
                (out_channels, in_channels, *self.kernel_size)
            )
        )

        if bias:
            self.bias = Parameter(np.zeros(out_channels))
        else:
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        """Apply 3D convolution."""
        batch_size, in_ch, in_d, in_h, in_w = x.shape
        kd, kh, kw = self.kernel_size
        sd, sh, sw = self.stride
        pd, ph, pw = self.padding

        # Apply padding
        if pd > 0 or ph > 0 or pw > 0:
            x_padded = np.pad(
                x.data,
                ((0, 0), (0, 0), (pd, pd), (ph, ph), (pw, pw)),
                mode='constant'
            )
        else:
            x_padded = x.data

        # Calculate output size
        out_d = (in_d + 2 * pd - kd) // sd + 1
        out_h = (in_h + 2 * ph - kh) // sh + 1
        out_w = (in_w + 2 * pw - kw) // sw + 1

        # Simple convolution
        output = np.zeros((batch_size, self.out_channels, out_d, out_h, out_w), dtype=np.float32)

        for b in range(batch_size):
            for oc in range(self.out_channels):
                for od in range(out_d):
                    for oh in range(out_h):
                        for ow in range(out_w):
                            d_start = od * sd
                            h_start = oh * sh
                            w_start = ow * sw

                            patch = x_padded[b, :, d_start:d_start+kd, h_start:h_start+kh, w_start:w_start+kw]
                            output[b, oc, od, oh, ow] = np.sum(patch * self.weight.data[oc])

        result = Tensor(output, requires_grad=x.requires_grad)

        if self.bias is not None:
            result = result + self.bias.reshape(1, -1, 1, 1, 1)

        return result

    def __repr__(self) -> str:
        return f"Conv3d({self.in_channels}, {self.out_channels}, kernel_size={self.kernel_size})"


class ConvTranspose1d(Module):
    """
    1D transposed convolution (deconvolution).

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int
        Size of the kernel.
    stride : int, default=1
        Stride of the convolution.
    padding : int, default=0
        Padding.
    output_padding : int, default=0
        Additional size added to output.
    bias : bool, default=True
        If True, adds a learnable bias.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int = 1,
        padding: int = 0,
        output_padding: int = 0,
        bias: bool = True,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.output_padding = output_padding

        k = 1 / (in_channels * kernel_size)
        self.weight = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (in_channels, out_channels, kernel_size))
        )

        if bias:
            self.bias = Parameter(np.zeros(out_channels))
        else:
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        """Apply transposed 1D convolution."""
        batch_size, in_ch, in_len = x.shape

        # Output length
        out_len = (in_len - 1) * self.stride - 2 * self.padding + self.kernel_size + self.output_padding

        output = np.zeros((batch_size, self.out_channels, out_len), dtype=np.float32)

        for b in range(batch_size):
            for ic in range(in_ch):
                for il in range(in_len):
                    for oc in range(self.out_channels):
                        for k in range(self.kernel_size):
                            ol = il * self.stride + k - self.padding
                            if 0 <= ol < out_len:
                                output[b, oc, ol] += x.data[b, ic, il] * self.weight.data[ic, oc, k]

        result = Tensor(output, requires_grad=x.requires_grad)

        if self.bias is not None:
            result = result + self.bias.reshape(1, -1, 1)

        return result

    def __repr__(self) -> str:
        return f"ConvTranspose1d({self.in_channels}, {self.out_channels}, kernel_size={self.kernel_size})"


class ConvTranspose2d(Module):
    """
    2D transposed convolution (deconvolution).

    Parameters
    ----------
    in_channels : int
        Number of input channels.
    out_channels : int
        Number of output channels.
    kernel_size : int or tuple
        Size of the kernel.
    stride : int or tuple, default=1
        Stride of the convolution.
    padding : int or tuple, default=0
        Padding.
    output_padding : int or tuple, default=0
        Additional size added to output.
    bias : bool, default=True
        If True, adds a learnable bias.

    Examples
    --------
    >>> conv_t = nn.ConvTranspose2d(64, 32, 4, stride=2, padding=1)
    >>> x = Tensor(np.random.randn(1, 64, 14, 14))
    >>> output = conv_t(x)  # (1, 32, 28, 28)
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Union[int, Tuple[int, int]],
        stride: Union[int, Tuple[int, int]] = 1,
        padding: Union[int, Tuple[int, int]] = 0,
        output_padding: Union[int, Tuple[int, int]] = 0,
        bias: bool = True,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = _pair(kernel_size)
        self.stride = _pair(stride)
        self.padding = _pair(padding)
        self.output_padding = _pair(output_padding)

        kh, kw = self.kernel_size
        k = 1 / (in_channels * kh * kw)
        self.weight = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (in_channels, out_channels, kh, kw))
        )

        if bias:
            self.bias = Parameter(np.zeros(out_channels))
        else:
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        """Apply transposed 2D convolution."""
        batch_size, in_ch, in_h, in_w = x.shape
        kh, kw = self.kernel_size
        sh, sw = self.stride
        ph, pw = self.padding
        oph, opw = self.output_padding

        # Output size
        out_h = (in_h - 1) * sh - 2 * ph + kh + oph
        out_w = (in_w - 1) * sw - 2 * pw + kw + opw

        output = np.zeros((batch_size, self.out_channels, out_h, out_w), dtype=np.float32)

        for b in range(batch_size):
            for ic in range(in_ch):
                for ih in range(in_h):
                    for iw in range(in_w):
                        for oc in range(self.out_channels):
                            for khi in range(kh):
                                for kwi in range(kw):
                                    oh = ih * sh + khi - ph
                                    ow = iw * sw + kwi - pw
                                    if 0 <= oh < out_h and 0 <= ow < out_w:
                                        output[b, oc, oh, ow] += (
                                            x.data[b, ic, ih, iw] *
                                            self.weight.data[ic, oc, khi, kwi]
                                        )

        result = Tensor(output, requires_grad=x.requires_grad)

        if self.bias is not None:
            result = result + self.bias.reshape(1, -1, 1, 1)

        return result

    def __repr__(self) -> str:
        return (f"ConvTranspose2d({self.in_channels}, {self.out_channels}, "
                f"kernel_size={self.kernel_size}, stride={self.stride})")
