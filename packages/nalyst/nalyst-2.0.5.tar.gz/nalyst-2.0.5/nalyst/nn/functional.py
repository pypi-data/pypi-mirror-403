"""
Functional API for neural network operations.
"""

from __future__ import annotations

from typing import Optional, Tuple, List, Union
import numpy as np

from nalyst.nn.tensor import Tensor


# Activation Functions

def relu(x: Tensor, inplace: bool = False) -> Tensor:
    """
    Rectified Linear Unit activation.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    inplace : bool, default=False
        Modify input in place (ignored, for API compatibility).

    Returns
    -------
    Tensor
        Output tensor.
    """
    return x.relu()


def leaky_relu(x: Tensor, negative_slope: float = 0.01) -> Tensor:
    """
    Leaky ReLU activation.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    negative_slope : float, default=0.01
        Slope for negative values.
    """
    return x.leaky_relu(negative_slope)


def elu(x: Tensor, alpha: float = 1.0) -> Tensor:
    """
    Exponential Linear Unit activation.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    alpha : float, default=1.0
        Scale for negative values.
    """
    output_data = np.where(x.data > 0, x.data, alpha * (np.exp(x.data) - 1))

    output = Tensor(
        output_data,
        requires_grad=x.requires_grad,
        _children=(x,),
        _op="elu",
    )

    def _backward():
        if x.requires_grad and output.grad is not None:
            grad = np.where(x.data > 0, 1, output_data + alpha)
            if x.grad is None:
                x.grad = np.zeros_like(x.data)
            x.grad += grad * output.grad

    output._backward = _backward
    return output


def selu(x: Tensor) -> Tensor:
    """
    Scaled Exponential Linear Unit activation.
    """
    alpha = 1.6732632423543772
    scale = 1.0507009873554805
    return scale * elu(x, alpha)


def gelu(x: Tensor, approximate: str = 'none') -> Tensor:
    """
    Gaussian Error Linear Unit activation.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    approximate : str, default='none'
        'tanh' for tanh approximation, 'none' for exact.
    """
    return x.gelu()


def sigmoid(x: Tensor) -> Tensor:
    """Sigmoid activation."""
    return x.sigmoid()


def tanh(x: Tensor) -> Tensor:
    """Tanh activation."""
    return x.tanh()


def softmax(x: Tensor, dim: int = -1) -> Tensor:
    """
    Softmax activation.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    dim : int, default=-1
        Dimension to apply softmax.
    """
    return x.softmax(dim)


def log_softmax(x: Tensor, dim: int = -1) -> Tensor:
    """
    Log Softmax activation.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    dim : int, default=-1
        Dimension to apply log softmax.
    """
    return x.log_softmax(dim)


def swish(x: Tensor) -> Tensor:
    """Swish activation (x * sigmoid(x))."""
    return x * x.sigmoid()


def mish(x: Tensor) -> Tensor:
    """Mish activation (x * tanh(softplus(x)))."""
    softplus = Tensor(np.log1p(np.exp(x.data)))
    return x * softplus.tanh()


def hardswish(x: Tensor) -> Tensor:
    """Hard Swish activation."""
    return x * Tensor(np.clip(x.data + 3, 0, 6)) / 6


def hardsigmoid(x: Tensor) -> Tensor:
    """Hard Sigmoid activation."""
    return Tensor(np.clip(x.data / 6 + 0.5, 0, 1))


# Dropout Functions

def dropout(
    x: Tensor,
    p: float = 0.5,
    training: bool = True,
    inplace: bool = False,
) -> Tensor:
    """
    Apply dropout.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    p : float, default=0.5
        Dropout probability.
    training : bool, default=True
        Apply dropout only during training.
    """
    if not training or p == 0:
        return x

    mask = np.random.binomial(1, 1 - p, x.shape) / (1 - p)
    return x * Tensor(mask)


def dropout2d(
    x: Tensor,
    p: float = 0.5,
    training: bool = True,
) -> Tensor:
    """
    Apply 2D channel-wise dropout.

    Parameters
    ----------
    x : Tensor
        Input tensor of shape (N, C, H, W).
    p : float, default=0.5
        Dropout probability.
    """
    if not training or p == 0:
        return x

    # Drop entire channels
    mask_shape = (x.shape[0], x.shape[1], 1, 1)
    mask = np.random.binomial(1, 1 - p, mask_shape) / (1 - p)
    return x * Tensor(mask)


# Normalization Functions

def batch_norm(
    x: Tensor,
    running_mean: Optional[np.ndarray],
    running_var: Optional[np.ndarray],
    weight: Optional[Tensor] = None,
    bias: Optional[Tensor] = None,
    training: bool = True,
    momentum: float = 0.1,
    eps: float = 1e-5,
) -> Tensor:
    """
    Apply batch normalization.
    """
    if training:
        if x.data.ndim == 4:
            mean = x.data.mean(axis=(0, 2, 3), keepdims=True)
            var = x.data.var(axis=(0, 2, 3), keepdims=True)
        else:
            mean = x.data.mean(axis=0, keepdims=True)
            var = x.data.var(axis=0, keepdims=True)

        if running_mean is not None:
            running_mean *= (1 - momentum)
            running_mean += momentum * mean.squeeze()
        if running_var is not None:
            running_var *= (1 - momentum)
            running_var += momentum * var.squeeze()
    else:
        mean = running_mean
        var = running_var
        if x.data.ndim == 4:
            mean = mean.reshape(1, -1, 1, 1)
            var = var.reshape(1, -1, 1, 1)

    x_norm = (x.data - mean) / np.sqrt(var + eps)

    if weight is not None:
        if x.data.ndim == 4:
            x_norm = x_norm * weight.data.reshape(1, -1, 1, 1)
        else:
            x_norm = x_norm * weight.data

    if bias is not None:
        if x.data.ndim == 4:
            x_norm = x_norm + bias.data.reshape(1, -1, 1, 1)
        else:
            x_norm = x_norm + bias.data

    return Tensor(x_norm, requires_grad=x.requires_grad)


def layer_norm(
    x: Tensor,
    normalized_shape: Tuple[int, ...],
    weight: Optional[Tensor] = None,
    bias: Optional[Tensor] = None,
    eps: float = 1e-5,
) -> Tensor:
    """
    Apply layer normalization.
    """
    dims = tuple(range(-len(normalized_shape), 0))
    mean = x.data.mean(axis=dims, keepdims=True)
    var = x.data.var(axis=dims, keepdims=True)

    x_norm = (x.data - mean) / np.sqrt(var + eps)

    if weight is not None:
        x_norm = x_norm * weight.data
    if bias is not None:
        x_norm = x_norm + bias.data

    return Tensor(x_norm, requires_grad=x.requires_grad)


def group_norm(
    x: Tensor,
    num_groups: int,
    weight: Optional[Tensor] = None,
    bias: Optional[Tensor] = None,
    eps: float = 1e-5,
) -> Tensor:
    """
    Apply group normalization.
    """
    N, C = x.shape[:2]
    spatial = x.shape[2:]

    x_reshaped = x.data.reshape(N, num_groups, C // num_groups, *spatial)
    mean = x_reshaped.mean(axis=tuple(range(2, x_reshaped.ndim)), keepdims=True)
    var = x_reshaped.var(axis=tuple(range(2, x_reshaped.ndim)), keepdims=True)

    x_norm = (x_reshaped - mean) / np.sqrt(var + eps)
    x_norm = x_norm.reshape(N, C, *spatial)

    if weight is not None:
        x_norm = x_norm * weight.data.reshape(1, C, *([1] * len(spatial)))
    if bias is not None:
        x_norm = x_norm + bias.data.reshape(1, C, *([1] * len(spatial)))

    return Tensor(x_norm, requires_grad=x.requires_grad)


# Convolution Functions

def conv2d(
    x: Tensor,
    weight: Tensor,
    bias: Optional[Tensor] = None,
    stride: int = 1,
    padding: int = 0,
) -> Tensor:
    """
    Apply 2D convolution.

    Parameters
    ----------
    x : Tensor
        Input of shape (N, C_in, H, W).
    weight : Tensor
        Filters of shape (C_out, C_in, kH, kW).
    bias : Tensor, optional
        Bias of shape (C_out,).
    stride : int, default=1
        Convolution stride.
    padding : int, default=0
        Zero-padding.
    """
    N, C_in, H, W = x.shape
    C_out, _, kH, kW = weight.shape

    # Apply padding
    if padding > 0:
        x_padded = np.pad(
            x.data,
            ((0, 0), (0, 0), (padding, padding), (padding, padding)),
            mode='constant'
        )
    else:
        x_padded = x.data

    H_out = (H + 2 * padding - kH) // stride + 1
    W_out = (W + 2 * padding - kW) // stride + 1

    # im2col
    col = np.zeros((N, C_in, kH, kW, H_out, W_out))
    for i in range(kH):
        i_max = i + stride * H_out
        for j in range(kW):
            j_max = j + stride * W_out
            col[:, :, i, j, :, :] = x_padded[:, :, i:i_max:stride, j:j_max:stride]

    col = col.reshape(N, C_in * kH * kW, H_out * W_out)
    w_col = weight.data.reshape(C_out, -1)

    output = w_col @ col.transpose(0, 2, 1).reshape(-1, C_in * kH * kW).T
    output = output.reshape(C_out, N, H_out, W_out).transpose(1, 0, 2, 3)

    if bias is not None:
        output = output + bias.data.reshape(1, -1, 1, 1)

    return Tensor(output, requires_grad=x.requires_grad or weight.requires_grad)


def max_pool2d(
    x: Tensor,
    kernel_size: int,
    stride: Optional[int] = None,
    padding: int = 0,
) -> Tensor:
    """
    Apply 2D max pooling.
    """
    if stride is None:
        stride = kernel_size

    N, C, H, W = x.shape

    if padding > 0:
        x_padded = np.pad(
            x.data,
            ((0, 0), (0, 0), (padding, padding), (padding, padding)),
            mode='constant',
            constant_values=-np.inf
        )
    else:
        x_padded = x.data

    H_out = (H + 2 * padding - kernel_size) // stride + 1
    W_out = (W + 2 * padding - kernel_size) // stride + 1

    output = np.zeros((N, C, H_out, W_out))

    for i in range(H_out):
        for j in range(W_out):
            h_start = i * stride
            w_start = j * stride
            window = x_padded[:, :, h_start:h_start+kernel_size, w_start:w_start+kernel_size]
            output[:, :, i, j] = window.max(axis=(2, 3))

    return Tensor(output, requires_grad=x.requires_grad)


def avg_pool2d(
    x: Tensor,
    kernel_size: int,
    stride: Optional[int] = None,
    padding: int = 0,
) -> Tensor:
    """
    Apply 2D average pooling.
    """
    if stride is None:
        stride = kernel_size

    N, C, H, W = x.shape

    if padding > 0:
        x_padded = np.pad(
            x.data,
            ((0, 0), (0, 0), (padding, padding), (padding, padding)),
            mode='constant'
        )
    else:
        x_padded = x.data

    H_out = (H + 2 * padding - kernel_size) // stride + 1
    W_out = (W + 2 * padding - kernel_size) // stride + 1

    output = np.zeros((N, C, H_out, W_out))

    for i in range(H_out):
        for j in range(W_out):
            h_start = i * stride
            w_start = j * stride
            window = x_padded[:, :, h_start:h_start+kernel_size, w_start:w_start+kernel_size]
            output[:, :, i, j] = window.mean(axis=(2, 3))

    return Tensor(output, requires_grad=x.requires_grad)


def adaptive_avg_pool2d(x: Tensor, output_size: Tuple[int, int]) -> Tensor:
    """
    Apply 2D adaptive average pooling.
    """
    N, C, H, W = x.shape
    H_out, W_out = output_size

    output = np.zeros((N, C, H_out, W_out))

    for i in range(H_out):
        h_start = int(i * H / H_out)
        h_end = int((i + 1) * H / H_out)
        for j in range(W_out):
            w_start = int(j * W / W_out)
            w_end = int((j + 1) * W / W_out)
            output[:, :, i, j] = x.data[:, :, h_start:h_end, w_start:w_end].mean(axis=(2, 3))

    return Tensor(output, requires_grad=x.requires_grad)


# Loss Functions

def mse_loss(
    input: Tensor,
    target: Tensor,
    reduction: str = 'mean',
) -> Tensor:
    """
    Mean squared error loss.
    """
    diff = input - target
    loss = diff * diff

    if reduction == 'mean':
        return loss.mean()
    elif reduction == 'sum':
        return loss.sum()
    return loss


def cross_entropy(
    input: Tensor,
    target: Tensor,
    reduction: str = 'mean',
) -> Tensor:
    """
    Cross entropy loss.

    Parameters
    ----------
    input : Tensor
        Logits of shape (N, C).
    target : Tensor
        Target indices of shape (N,).
    """
    log_probs = input.log_softmax(dim=-1)

    num_samples = input.shape[0]
    target_flat = target.data.flatten().astype(np.int64)

    nll = -log_probs.data[np.arange(num_samples), target_flat]

    loss = Tensor(nll, requires_grad=input.requires_grad)

    if reduction == 'mean':
        return loss.mean()
    elif reduction == 'sum':
        return loss.sum()
    return loss


def binary_cross_entropy(
    input: Tensor,
    target: Tensor,
    reduction: str = 'mean',
) -> Tensor:
    """
    Binary cross entropy loss.
    """
    eps = 1e-7
    input_clamped = np.clip(input.data, eps, 1 - eps)

    bce = -(target.data * np.log(input_clamped) +
            (1 - target.data) * np.log(1 - input_clamped))

    loss = Tensor(bce, requires_grad=input.requires_grad)

    if reduction == 'mean':
        return loss.mean()
    elif reduction == 'sum':
        return loss.sum()
    return loss


def binary_cross_entropy_with_logits(
    input: Tensor,
    target: Tensor,
    reduction: str = 'mean',
) -> Tensor:
    """
    Binary cross entropy with logits (numerically stable).
    """
    x = input.data
    z = target.data

    bce = np.maximum(x, 0) - x * z + np.log1p(np.exp(-np.abs(x)))

    loss = Tensor(bce, requires_grad=input.requires_grad)

    if reduction == 'mean':
        return loss.mean()
    elif reduction == 'sum':
        return loss.sum()
    return loss


def nll_loss(
    input: Tensor,
    target: Tensor,
    reduction: str = 'mean',
) -> Tensor:
    """
    Negative log likelihood loss.
    """
    num_samples = input.shape[0]
    target_flat = target.data.flatten().astype(np.int64)

    nll = -input.data[np.arange(num_samples), target_flat]

    loss = Tensor(nll, requires_grad=input.requires_grad)

    if reduction == 'mean':
        return loss.mean()
    elif reduction == 'sum':
        return loss.sum()
    return loss


# Utility Functions

def linear(
    x: Tensor,
    weight: Tensor,
    bias: Optional[Tensor] = None,
) -> Tensor:
    """
    Apply linear transformation.
    """
    output = x @ weight.transpose()
    if bias is not None:
        output = output + bias
    return output


def embedding(
    input: Tensor,
    weight: Tensor,
    padding_idx: Optional[int] = None,
) -> Tensor:
    """
    Look up embeddings.
    """
    indices = input.data.astype(np.int64)
    output = weight.data[indices]
    return Tensor(output, requires_grad=weight.requires_grad)


def pad(
    x: Tensor,
    pad: Tuple[int, ...],
    mode: str = 'constant',
    value: float = 0,
) -> Tensor:
    """
    Pad tensor.

    Parameters
    ----------
    x : Tensor
        Input tensor.
    pad : tuple
        Padding sizes (left, right, top, bottom, ...).
    mode : str, default='constant'
        Padding mode.
    value : float, default=0
        Constant padding value.
    """
    # Convert (left, right, top, bottom) to numpy format
    ndim = x.data.ndim
    pad_width = [(0, 0)] * ndim

    # Pad from last dimension
    for i, (p1, p2) in enumerate(zip(pad[::2], pad[1::2])):
        dim = ndim - 1 - i
        pad_width[dim] = (p1, p2)

    padded = np.pad(x.data, pad_width, mode=mode, constant_values=value)
    return Tensor(padded, requires_grad=x.requires_grad)


def interpolate(
    x: Tensor,
    size: Optional[Tuple[int, ...]] = None,
    scale_factor: Optional[float] = None,
    mode: str = 'nearest',
) -> Tensor:
    """
    Upsample or downsample tensor.

    Parameters
    ----------
    x : Tensor
        Input tensor of shape (N, C, *spatial).
    size : tuple, optional
        Output spatial size.
    scale_factor : float, optional
        Scale factor.
    mode : str, default='nearest'
        Interpolation mode ('nearest', 'bilinear').
    """
    if x.data.ndim != 4:
        raise ValueError("interpolate only supports 4D tensors")

    N, C, H, W = x.shape

    if size is not None:
        H_out, W_out = size
    elif scale_factor is not None:
        H_out = int(H * scale_factor)
        W_out = int(W * scale_factor)
    else:
        raise ValueError("Either size or scale_factor must be provided")

    if mode == 'nearest':
        # Nearest neighbor interpolation
        row_indices = (np.arange(H_out) * H / H_out).astype(int)
        col_indices = (np.arange(W_out) * W / W_out).astype(int)
        output = x.data[:, :, row_indices, :][:, :, :, col_indices]

    elif mode == 'bilinear':
        # Bilinear interpolation
        output = np.zeros((N, C, H_out, W_out))

        for i in range(H_out):
            for j in range(W_out):
                h = i * (H - 1) / max(H_out - 1, 1)
                w = j * (W - 1) / max(W_out - 1, 1)

                h0, w0 = int(h), int(w)
                h1, w1 = min(h0 + 1, H - 1), min(w0 + 1, W - 1)

                hf, wf = h - h0, w - w0

                output[:, :, i, j] = (
                    (1 - hf) * (1 - wf) * x.data[:, :, h0, w0] +
                    (1 - hf) * wf * x.data[:, :, h0, w1] +
                    hf * (1 - wf) * x.data[:, :, h1, w0] +
                    hf * wf * x.data[:, :, h1, w1]
                )
    else:
        raise ValueError(f"Unknown interpolation mode: {mode}")

    return Tensor(output, requires_grad=x.requires_grad)
