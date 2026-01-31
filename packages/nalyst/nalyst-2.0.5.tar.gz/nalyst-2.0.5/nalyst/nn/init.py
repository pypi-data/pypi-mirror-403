"""
Weight initialization utilities.
"""

from __future__ import annotations

from typing import Optional, Union
import math
import numpy as np

from nalyst.nn.tensor import Tensor
from nalyst.nn.parameter import Parameter


def calculate_fan_in_and_fan_out(tensor: Union[Tensor, Parameter]) -> tuple:
    """
    Calculate fan_in and fan_out for a tensor.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Weight tensor.

    Returns
    -------
    tuple
        (fan_in, fan_out)
    """
    dimensions = tensor.data.ndim

    if dimensions < 2:
        raise ValueError("Fan in and fan out can not be computed for tensor with fewer than 2 dimensions")

    num_input_fmaps = tensor.shape[1]
    num_output_fmaps = tensor.shape[0]

    if dimensions > 2:
        receptive_field_size = np.prod(tensor.shape[2:])
    else:
        receptive_field_size = 1

    fan_in = num_input_fmaps * receptive_field_size
    fan_out = num_output_fmaps * receptive_field_size

    return fan_in, fan_out


def calculate_gain(nonlinearity: str, param: Optional[float] = None) -> float:
    """
    Calculate recommended gain value for given nonlinearity.

    Parameters
    ----------
    nonlinearity : str
        Name of nonlinearity function.
    param : float, optional
        Parameter for some nonlinearities.

    Returns
    -------
    float
        Recommended gain.
    """
    linear_fns = ['linear', 'conv1d', 'conv2d', 'conv3d', 'conv_transpose1d',
                  'conv_transpose2d', 'conv_transpose3d']

    if nonlinearity in linear_fns or nonlinearity == 'sigmoid':
        return 1
    elif nonlinearity == 'tanh':
        return 5.0 / 3
    elif nonlinearity == 'relu':
        return math.sqrt(2.0)
    elif nonlinearity == 'leaky_relu':
        if param is None:
            negative_slope = 0.01
        else:
            negative_slope = param
        return math.sqrt(2.0 / (1 + negative_slope ** 2))
    elif nonlinearity == 'selu':
        return 3.0 / 4
    else:
        raise ValueError(f"Unsupported nonlinearity: {nonlinearity}")


def uniform_(
    tensor: Union[Tensor, Parameter],
    a: float = 0.0,
    b: float = 1.0,
) -> Union[Tensor, Parameter]:
    """
    Fill tensor with values from uniform distribution U(a, b).

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    a : float, default=0.0
        Lower bound.
    b : float, default=1.0
        Upper bound.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    tensor.data = np.random.uniform(a, b, tensor.shape)
    return tensor


def normal_(
    tensor: Union[Tensor, Parameter],
    mean: float = 0.0,
    std: float = 1.0,
) -> Union[Tensor, Parameter]:
    """
    Fill tensor with values from normal distribution N(mean, std^2).

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    mean : float, default=0.0
        Mean of distribution.
    std : float, default=1.0
        Standard deviation.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    tensor.data = np.random.normal(mean, std, tensor.shape)
    return tensor


def constant_(
    tensor: Union[Tensor, Parameter],
    value: float,
) -> Union[Tensor, Parameter]:
    """
    Fill tensor with constant value.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    value : float
        Value to fill with.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    tensor.data.fill(value)
    return tensor


def ones_(tensor: Union[Tensor, Parameter]) -> Union[Tensor, Parameter]:
    """Fill tensor with ones."""
    return constant_(tensor, 1.0)


def zeros_(tensor: Union[Tensor, Parameter]) -> Union[Tensor, Parameter]:
    """Fill tensor with zeros."""
    return constant_(tensor, 0.0)


def eye_(tensor: Union[Tensor, Parameter]) -> Union[Tensor, Parameter]:
    """
    Fill 2D tensor with identity matrix.
    """
    if tensor.data.ndim != 2:
        raise ValueError("eye_ requires 2D tensor")

    tensor.data = np.eye(tensor.shape[0], tensor.shape[1])
    return tensor


def dirac_(
    tensor: Union[Tensor, Parameter],
    groups: int = 1,
) -> Union[Tensor, Parameter]:
    """
    Fill {3, 4, 5}D tensor with Dirac delta function.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill (must be {3, 4, 5}D).
    groups : int, default=1
        Number of groups for grouped convolution.
    """
    dimensions = tensor.data.ndim
    if dimensions not in [3, 4, 5]:
        raise ValueError("Only 3D, 4D and 5D tensors are supported")

    sizes = tensor.shape
    out_chans_per_grp = sizes[0] // groups
    min_dim = min(out_chans_per_grp, sizes[1])

    tensor.data = np.zeros(sizes)

    for g in range(groups):
        for d in range(min_dim):
            if dimensions == 3:
                tensor.data[g * out_chans_per_grp + d, d, sizes[2] // 2] = 1
            elif dimensions == 4:
                tensor.data[g * out_chans_per_grp + d, d, sizes[2] // 2, sizes[3] // 2] = 1
            elif dimensions == 5:
                tensor.data[g * out_chans_per_grp + d, d, sizes[2] // 2, sizes[3] // 2, sizes[4] // 2] = 1

    return tensor


def xavier_uniform_(
    tensor: Union[Tensor, Parameter],
    gain: float = 1.0,
) -> Union[Tensor, Parameter]:
    """
    Xavier uniform initialization.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    gain : float, default=1.0
        Scaling factor.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.

    Examples
    --------
    >>> w = Parameter(np.empty((64, 128)))
    >>> xavier_uniform_(w)
    """
    fan_in, fan_out = calculate_fan_in_and_fan_out(tensor)
    std = gain * math.sqrt(2.0 / (fan_in + fan_out))
    a = math.sqrt(3.0) * std
    return uniform_(tensor, -a, a)


def xavier_normal_(
    tensor: Union[Tensor, Parameter],
    gain: float = 1.0,
) -> Union[Tensor, Parameter]:
    """
    Xavier normal initialization.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    gain : float, default=1.0
        Scaling factor.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    fan_in, fan_out = calculate_fan_in_and_fan_out(tensor)
    std = gain * math.sqrt(2.0 / (fan_in + fan_out))
    return normal_(tensor, 0.0, std)


def kaiming_uniform_(
    tensor: Union[Tensor, Parameter],
    a: float = 0,
    mode: str = 'fan_in',
    nonlinearity: str = 'leaky_relu',
) -> Union[Tensor, Parameter]:
    """
    Kaiming uniform initialization.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    a : float, default=0
        Negative slope (for leaky_relu).
    mode : str, default='fan_in'
        'fan_in' or 'fan_out'.
    nonlinearity : str, default='leaky_relu'
        Nonlinearity function name.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.

    Examples
    --------
    >>> w = Parameter(np.empty((64, 3, 3, 3)))
    >>> kaiming_uniform_(w, mode='fan_out', nonlinearity='relu')
    """
    fan_in, fan_out = calculate_fan_in_and_fan_out(tensor)
    fan = fan_in if mode == 'fan_in' else fan_out

    gain = calculate_gain(nonlinearity, a)
    std = gain / math.sqrt(fan)
    bound = math.sqrt(3.0) * std

    return uniform_(tensor, -bound, bound)


def kaiming_normal_(
    tensor: Union[Tensor, Parameter],
    a: float = 0,
    mode: str = 'fan_in',
    nonlinearity: str = 'leaky_relu',
) -> Union[Tensor, Parameter]:
    """
    Kaiming normal initialization.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    a : float, default=0
        Negative slope (for leaky_relu).
    mode : str, default='fan_in'
        'fan_in' or 'fan_out'.
    nonlinearity : str, default='leaky_relu'
        Nonlinearity function name.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    fan_in, fan_out = calculate_fan_in_and_fan_out(tensor)
    fan = fan_in if mode == 'fan_in' else fan_out

    gain = calculate_gain(nonlinearity, a)
    std = gain / math.sqrt(fan)

    return normal_(tensor, 0.0, std)


def orthogonal_(
    tensor: Union[Tensor, Parameter],
    gain: float = 1.0,
) -> Union[Tensor, Parameter]:
    """
    Orthogonal initialization.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    gain : float, default=1.0
        Scaling factor.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    if tensor.data.ndim < 2:
        raise ValueError("Only 2D+ tensors are supported")

    rows = tensor.shape[0]
    cols = np.prod(tensor.shape[1:])

    flattened = np.random.normal(0, 1, (rows, cols))

    if rows < cols:
        flattened = flattened.T

    # QR decomposition
    q, r = np.linalg.qr(flattened)
    d = np.diag(r)
    ph = np.sign(d)
    q *= ph

    if rows < cols:
        q = q.T

    tensor.data = gain * q.reshape(tensor.shape)
    return tensor


def sparse_(
    tensor: Union[Tensor, Parameter],
    sparsity: float,
    std: float = 0.01,
) -> Union[Tensor, Parameter]:
    """
    Sparse initialization.

    Parameters
    ----------
    tensor : Tensor or Parameter
        2D tensor to fill.
    sparsity : float
        Fraction of elements to set to zero.
    std : float, default=0.01
        Standard deviation of non-zero elements.

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    if tensor.data.ndim != 2:
        raise ValueError("Only 2D tensors are supported")

    rows, cols = tensor.shape
    num_zeros = int(math.ceil(sparsity * rows))

    tensor.data = np.random.normal(0, std, (rows, cols))

    for col_idx in range(cols):
        row_indices = np.random.choice(rows, num_zeros, replace=False)
        tensor.data[row_indices, col_idx] = 0

    return tensor


def trunc_normal_(
    tensor: Union[Tensor, Parameter],
    mean: float = 0.0,
    std: float = 1.0,
    a: float = -2.0,
    b: float = 2.0,
) -> Union[Tensor, Parameter]:
    """
    Truncated normal initialization.

    Parameters
    ----------
    tensor : Tensor or Parameter
        Tensor to fill.
    mean : float, default=0.0
        Mean of distribution.
    std : float, default=1.0
        Standard deviation.
    a : float, default=-2.0
        Lower bound (in std units).
    b : float, default=2.0
        Upper bound (in std units).

    Returns
    -------
    Tensor or Parameter
        Modified tensor.
    """
    from scipy import stats

    # Use scipy if available, otherwise use rejection sampling
    try:
        lower = (a - mean) / std
        upper = (b - mean) / std
        samples = stats.truncnorm.rvs(lower, upper, loc=mean, scale=std, size=tensor.shape)
        tensor.data = samples
    except ImportError:
        # Fallback to rejection sampling
        tensor.data = np.random.normal(mean, std, tensor.shape)
        tensor.data = np.clip(tensor.data, a * std + mean, b * std + mean)

    return tensor


# Convenient aliases
glorot_uniform_ = xavier_uniform_
glorot_normal_ = xavier_normal_
he_uniform_ = kaiming_uniform_
he_normal_ = kaiming_normal_
