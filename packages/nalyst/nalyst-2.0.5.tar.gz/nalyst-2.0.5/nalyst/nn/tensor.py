"""
Tensor class with automatic differentiation.

The core data structure for deep learning computations.
"""

from __future__ import annotations

from typing import Optional, Union, Tuple, List, Callable, Any
import numpy as np


class Tensor:
    """
    A multi-dimensional array with automatic differentiation support.

    Tensors track computational graphs for gradient computation during
    backpropagation. Operations on tensors create a directed acyclic graph
    (DAG) that enables automatic gradient calculation.

    Parameters
    ----------
    data : array-like
        The tensor data.
    requires_grad : bool, default=False
        Whether to track gradients for this tensor.
    dtype : numpy dtype, optional
        Data type. Defaults to float32.

    Attributes
    ----------
    data : ndarray
        The underlying data.
    grad : Tensor or None
        Accumulated gradient.
    requires_grad : bool
        Whether gradients are tracked.

    Examples
    --------
    >>> x = Tensor([[1, 2], [3, 4]], requires_grad=True)
    >>> y = x * 2
    >>> z = y.sum()
    >>> z.backward()
    >>> print(x.grad)
    """

    def __init__(
        self,
        data: Union[np.ndarray, list, float, int],
        requires_grad: bool = False,
        dtype: Optional[np.dtype] = None,
        _children: Tuple["Tensor", ...] = (),
        _op: str = "",
        _backward: Optional[Callable] = None,
    ):
        if isinstance(data, Tensor):
            data = data.data

        if dtype is None:
            dtype = np.float32

        self.data = np.array(data, dtype=dtype)
        self.requires_grad = requires_grad
        self.grad: Optional[np.ndarray] = None

        # Computational graph tracking
        self._children = _children
        self._op = _op
        self._backward = _backward if _backward else lambda: None

        # For gradient accumulation
        self._grad_fn = None

    @property
    def shape(self) -> Tuple[int, ...]:
        """Return tensor shape."""
        return self.data.shape

    @property
    def ndim(self) -> int:
        """Return number of dimensions."""
        return self.data.ndim

    @property
    def size(self) -> int:
        """Return total number of elements."""
        return self.data.size

    @property
    def dtype(self) -> np.dtype:
        """Return data type."""
        return self.data.dtype

    @property
    def T(self) -> "Tensor":
        """Return transposed tensor."""
        return self.transpose()

    def numpy(self) -> np.ndarray:
        """Convert to numpy array."""
        return self.data.copy()

    def item(self) -> float:
        """Return scalar value."""
        return self.data.item()

    def tolist(self) -> list:
        """Convert to Python list."""
        return self.data.tolist()

    def detach(self) -> "Tensor":
        """Create a tensor that shares data but doesn't track gradients."""
        return Tensor(self.data, requires_grad=False)

    def clone(self) -> "Tensor":
        """Create a copy of the tensor."""
        return Tensor(self.data.copy(), requires_grad=self.requires_grad)

    def zero_grad(self) -> None:
        """Zero out the gradient."""
        self.grad = None

    def backward(self, gradient: Optional["Tensor"] = None) -> None:
        """
        Compute gradients via backpropagation.

        Parameters
        ----------
        gradient : Tensor, optional
            Gradient of the loss with respect to this tensor.
            Defaults to 1.0 for scalar tensors.
        """
        if not self.requires_grad:
            return

        if gradient is None:
            if self.data.size != 1:
                raise RuntimeError(
                    "grad must be specified for non-scalar tensors"
                )
            gradient = Tensor(np.ones_like(self.data))

        # Initialize gradient
        if self.grad is None:
            self.grad = np.zeros_like(self.data)

        self.grad = self.grad + gradient.data

        # Topological sort for correct backward order
        topo_order = []
        visited = set()

        def build_topo(tensor: Tensor):
            if tensor not in visited:
                visited.add(tensor)
                for child in tensor._children:
                    build_topo(child)
                topo_order.append(tensor)

        build_topo(self)

        # Backward pass
        for tensor in reversed(topo_order):
            if tensor._backward:
                tensor._backward()


    def __add__(self, other: Union["Tensor", float, int]) -> "Tensor":
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data + other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op="+",
        )

        def _backward():
            if self.requires_grad:
                grad = out.grad
                # Handle broadcasting
                if self.shape != out.shape:
                    grad = _sum_to_shape(grad, self.shape)
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + grad

            if other.requires_grad:
                grad = out.grad
                if other.shape != out.shape:
                    grad = _sum_to_shape(grad, other.shape)
                if other.grad is None:
                    other.grad = np.zeros_like(other.data)
                other.grad = other.grad + grad

        out._backward = _backward
        return out

    def __radd__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return self.__add__(other)

    def __neg__(self) -> "Tensor":
        return self * -1

    def __sub__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return self + (-other if isinstance(other, Tensor) else -other)

    def __rsub__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return (-self) + other

    def __mul__(self, other: Union["Tensor", float, int]) -> "Tensor":
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data * other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op="*",
        )

        def _backward():
            if self.requires_grad:
                grad = out.grad * other.data
                if self.shape != out.shape:
                    grad = _sum_to_shape(grad, self.shape)
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + grad

            if other.requires_grad:
                grad = out.grad * self.data
                if other.shape != out.shape:
                    grad = _sum_to_shape(grad, other.shape)
                if other.grad is None:
                    other.grad = np.zeros_like(other.data)
                other.grad = other.grad + grad

        out._backward = _backward
        return out

    def __rmul__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return self.__mul__(other)

    def __truediv__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return self * (other ** -1 if isinstance(other, Tensor) else 1.0 / other)

    def __rtruediv__(self, other: Union["Tensor", float, int]) -> "Tensor":
        return other * (self ** -1)

    def __pow__(self, power: Union[float, int]) -> "Tensor":
        out = Tensor(
            self.data ** power,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op=f"**{power}",
        )

        def _backward():
            if self.requires_grad:
                grad = out.grad * power * (self.data ** (power - 1))
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + grad

        out._backward = _backward
        return out

    def __matmul__(self, other: "Tensor") -> "Tensor":
        """Matrix multiplication."""
        return self.matmul(other)

    def matmul(self, other: "Tensor") -> "Tensor":
        """Matrix multiplication with gradient support."""
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data @ other.data,
            requires_grad=self.requires_grad or other.requires_grad,
            _children=(self, other),
            _op="@",
        )

        def _backward():
            if self.requires_grad:
                if self.ndim == 1 and other.ndim == 1:
                    grad = np.outer(out.grad, other.data)
                elif self.ndim == 1:
                    grad = out.grad @ other.data.T
                elif other.ndim == 1:
                    grad = np.outer(out.grad, other.data)
                else:
                    grad = out.grad @ other.data.swapaxes(-1, -2)

                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + grad.reshape(self.shape)

            if other.requires_grad:
                if self.ndim == 1 and other.ndim == 1:
                    grad = np.outer(self.data, out.grad)
                elif self.ndim == 1:
                    grad = np.outer(self.data, out.grad)
                elif other.ndim == 1:
                    grad = self.data.T @ out.grad
                else:
                    grad = self.data.swapaxes(-1, -2) @ out.grad

                if other.grad is None:
                    other.grad = np.zeros_like(other.data)
                other.grad = other.grad + grad.reshape(other.shape)

        out._backward = _backward
        return out


    def sum(self, axis: Optional[Union[int, Tuple[int, ...]]] = None, keepdims: bool = False) -> "Tensor":
        """Sum reduction."""
        out = Tensor(
            self.data.sum(axis=axis, keepdims=keepdims),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="sum",
        )

        def _backward():
            if self.requires_grad:
                grad = out.grad
                if not keepdims and axis is not None:
                    # Expand dims back
                    if isinstance(axis, int):
                        grad = np.expand_dims(grad, axis)
                    else:
                        for ax in sorted(axis):
                            grad = np.expand_dims(grad, ax)
                grad = np.broadcast_to(grad, self.shape)
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + grad

        out._backward = _backward
        return out

    def mean(self, axis: Optional[Union[int, Tuple[int, ...]]] = None, keepdims: bool = False) -> "Tensor":
        """Mean reduction."""
        n = self.data.size if axis is None else np.prod([self.shape[i] for i in (axis if isinstance(axis, tuple) else (axis,))])
        return self.sum(axis=axis, keepdims=keepdims) / n

    def var(self, axis: Optional[Union[int, Tuple[int, ...]]] = None, keepdims: bool = False, unbiased: bool = True) -> "Tensor":
        """Variance."""
        mean = self.mean(axis=axis, keepdims=True)
        diff = self - mean
        sq_diff = diff ** 2
        n = self.data.size if axis is None else np.prod([self.shape[i] for i in (axis if isinstance(axis, tuple) else (axis,))])
        if unbiased and n > 1:
            n = n - 1
        return sq_diff.sum(axis=axis, keepdims=keepdims) / n

    def std(self, axis: Optional[Union[int, Tuple[int, ...]]] = None, keepdims: bool = False, unbiased: bool = True) -> "Tensor":
        """Standard deviation."""
        return (self.var(axis=axis, keepdims=keepdims, unbiased=unbiased) + 1e-8) ** 0.5

    def max(self, axis: Optional[int] = None, keepdims: bool = False) -> "Tensor":
        """Maximum value."""
        out = Tensor(
            self.data.max(axis=axis, keepdims=keepdims),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="max",
        )

        def _backward():
            if self.requires_grad:
                if axis is None:
                    mask = (self.data == self.data.max()).astype(float)
                else:
                    max_vals = self.data.max(axis=axis, keepdims=True)
                    mask = (self.data == max_vals).astype(float)

                grad = out.grad
                if not keepdims and axis is not None:
                    grad = np.expand_dims(grad, axis)
                grad = np.broadcast_to(grad, self.shape) * mask
                # Normalize when multiple max values
                grad = grad / (mask.sum(axis=axis, keepdims=True) + 1e-8)

                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + grad

        out._backward = _backward
        return out

    def min(self, axis: Optional[int] = None, keepdims: bool = False) -> "Tensor":
        """Minimum value."""
        return (-self).max(axis=axis, keepdims=keepdims) * -1


    def reshape(self, *shape: int) -> "Tensor":
        """Reshape tensor."""
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            shape = tuple(shape[0])

        out = Tensor(
            self.data.reshape(shape),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="reshape",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad.reshape(self.shape)

        out._backward = _backward
        return out

    def view(self, *shape: int) -> "Tensor":
        """View tensor with different shape (alias for reshape)."""
        return self.reshape(*shape)

    def flatten(self, start_dim: int = 0, end_dim: int = -1) -> "Tensor":
        """Flatten tensor."""
        if end_dim < 0:
            end_dim = self.ndim + end_dim

        new_shape = (
            self.shape[:start_dim] +
            (np.prod(self.shape[start_dim:end_dim + 1]),) +
            self.shape[end_dim + 1:]
        )
        return self.reshape(*new_shape)

    def squeeze(self, axis: Optional[int] = None) -> "Tensor":
        """Remove dimensions of size 1."""
        out = Tensor(
            self.data.squeeze(axis=axis),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="squeeze",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad.reshape(self.shape)

        out._backward = _backward
        return out

    def unsqueeze(self, axis: int) -> "Tensor":
        """Add a dimension of size 1."""
        out = Tensor(
            np.expand_dims(self.data, axis),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="unsqueeze",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad.squeeze(axis)

        out._backward = _backward
        return out

    def transpose(self, dim0: int = -2, dim1: int = -1) -> "Tensor":
        """Transpose two dimensions."""
        axes = list(range(self.ndim))
        axes[dim0], axes[dim1] = axes[dim1], axes[dim0]

        out = Tensor(
            self.data.transpose(axes),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="transpose",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                # Reverse transpose
                self.grad = self.grad + out.grad.transpose(axes)

        out._backward = _backward
        return out

    def permute(self, *dims: int) -> "Tensor":
        """Permute tensor dimensions."""
        if len(dims) == 1 and isinstance(dims[0], (tuple, list)):
            dims = tuple(dims[0])

        out = Tensor(
            self.data.transpose(dims),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="permute",
        )

        def _backward():
            if self.requires_grad:
                # Inverse permutation
                inv_dims = [0] * len(dims)
                for i, d in enumerate(dims):
                    inv_dims[d] = i

                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad.transpose(inv_dims)

        out._backward = _backward
        return out

    def contiguous(self) -> "Tensor":
        """Return contiguous tensor."""
        return Tensor(
            np.ascontiguousarray(self.data),
            requires_grad=self.requires_grad,
        )


    def relu(self) -> "Tensor":
        """ReLU activation."""
        out = Tensor(
            np.maximum(0, self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="relu",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * (self.data > 0)

        out._backward = _backward
        return out

    def leaky_relu(self, negative_slope: float = 0.01) -> "Tensor":
        """Leaky ReLU activation."""
        out = Tensor(
            np.where(self.data > 0, self.data, negative_slope * self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="leaky_relu",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * np.where(self.data > 0, 1, negative_slope)

        out._backward = _backward
        return out

    def sigmoid(self) -> "Tensor":
        """Sigmoid activation."""
        sig = 1 / (1 + np.exp(-np.clip(self.data, -500, 500)))
        out = Tensor(
            sig,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="sigmoid",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * sig * (1 - sig)

        out._backward = _backward
        return out

    def tanh(self) -> "Tensor":
        """Tanh activation."""
        t = np.tanh(self.data)
        out = Tensor(
            t,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="tanh",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * (1 - t ** 2)

        out._backward = _backward
        return out

    def softmax(self, axis: int = -1) -> "Tensor":
        """Softmax activation."""
        exp_x = np.exp(self.data - self.data.max(axis=axis, keepdims=True))
        sm = exp_x / exp_x.sum(axis=axis, keepdims=True)

        out = Tensor(
            sm,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="softmax",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                # Softmax gradient
                grad = out.grad * sm
                sum_grad = grad.sum(axis=axis, keepdims=True)
                self.grad = self.grad + grad - sm * sum_grad

        out._backward = _backward
        return out

    def log_softmax(self, axis: int = -1) -> "Tensor":
        """Log-softmax activation."""
        x_max = self.data.max(axis=axis, keepdims=True)
        log_sum_exp = np.log(np.exp(self.data - x_max).sum(axis=axis, keepdims=True))
        lsm = self.data - x_max - log_sum_exp

        out = Tensor(
            lsm,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="log_softmax",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                sm = np.exp(lsm)
                self.grad = self.grad + out.grad - sm * out.grad.sum(axis=axis, keepdims=True)

        out._backward = _backward
        return out

    def gelu(self) -> "Tensor":
        """GELU activation."""
        # Approximate GELU
        out_data = 0.5 * self.data * (1 + np.tanh(
            np.sqrt(2 / np.pi) * (self.data + 0.044715 * self.data ** 3)
        ))

        out = Tensor(
            out_data,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="gelu",
        )

        def _backward():
            if self.requires_grad:
                # Approximate GELU derivative
                x = self.data
                tanh_arg = np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)
                tanh_val = np.tanh(tanh_arg)
                sech2 = 1 - tanh_val ** 2
                grad = 0.5 * (1 + tanh_val) + 0.5 * x * sech2 * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x ** 2)

                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * grad

        out._backward = _backward
        return out


    def exp(self) -> "Tensor":
        """Exponential."""
        out = Tensor(
            np.exp(self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="exp",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * out.data

        out._backward = _backward
        return out

    def log(self) -> "Tensor":
        """Natural logarithm."""
        out = Tensor(
            np.log(self.data + 1e-8),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="log",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad / (self.data + 1e-8)

        out._backward = _backward
        return out

    def sqrt(self) -> "Tensor":
        """Square root."""
        return self ** 0.5

    def abs(self) -> "Tensor":
        """Absolute value."""
        out = Tensor(
            np.abs(self.data),
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="abs",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * np.sign(self.data)

        out._backward = _backward
        return out

    def clamp(self, min_val: Optional[float] = None, max_val: Optional[float] = None) -> "Tensor":
        """Clamp values to range."""
        data = self.data.copy()
        if min_val is not None:
            data = np.maximum(data, min_val)
        if max_val is not None:
            data = np.minimum(data, max_val)

        out = Tensor(
            data,
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="clamp",
        )

        def _backward():
            if self.requires_grad:
                mask = np.ones_like(self.data)
                if min_val is not None:
                    mask = mask * (self.data >= min_val)
                if max_val is not None:
                    mask = mask * (self.data <= max_val)

                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                self.grad = self.grad + out.grad * mask

        out._backward = _backward
        return out


    def __eq__(self, other) -> "Tensor":
        other = other.data if isinstance(other, Tensor) else other
        return Tensor(self.data == other)

    def __ne__(self, other) -> "Tensor":
        other = other.data if isinstance(other, Tensor) else other
        return Tensor(self.data != other)

    def __lt__(self, other) -> "Tensor":
        other = other.data if isinstance(other, Tensor) else other
        return Tensor(self.data < other)

    def __le__(self, other) -> "Tensor":
        other = other.data if isinstance(other, Tensor) else other
        return Tensor(self.data <= other)

    def __gt__(self, other) -> "Tensor":
        other = other.data if isinstance(other, Tensor) else other
        return Tensor(self.data > other)

    def __ge__(self, other) -> "Tensor":
        other = other.data if isinstance(other, Tensor) else other
        return Tensor(self.data >= other)


    def __getitem__(self, key) -> "Tensor":
        out = Tensor(
            self.data[key],
            requires_grad=self.requires_grad,
            _children=(self,),
            _op="getitem",
        )

        def _backward():
            if self.requires_grad:
                if self.grad is None:
                    self.grad = np.zeros_like(self.data)
                np.add.at(self.grad, key, out.grad)

        out._backward = _backward
        return out

    def __setitem__(self, key, value):
        if isinstance(value, Tensor):
            value = value.data
        self.data[key] = value

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


    def __repr__(self) -> str:
        grad_str = ", requires_grad=True" if self.requires_grad else ""
        return f"Tensor({self.data}{grad_str})"

    def __str__(self) -> str:
        return str(self.data)



def _sum_to_shape(grad: np.ndarray, shape: Tuple[int, ...]) -> np.ndarray:
    """Sum gradient to match target shape (handle broadcasting)."""
    # First, sum over extra leading dimensions
    while grad.ndim > len(shape):
        grad = grad.sum(axis=0)

    # Then, sum over broadcasted dimensions
    for i, (g, s) in enumerate(zip(grad.shape, shape)):
        if s == 1 and g > 1:
            grad = grad.sum(axis=i, keepdims=True)

    return grad



def zeros(*shape, requires_grad: bool = False, dtype=np.float32) -> Tensor:
    """Create tensor of zeros."""
    if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
        shape = tuple(shape[0])
    return Tensor(np.zeros(shape, dtype=dtype), requires_grad=requires_grad)


def ones(*shape, requires_grad: bool = False, dtype=np.float32) -> Tensor:
    """Create tensor of ones."""
    if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
        shape = tuple(shape[0])
    return Tensor(np.ones(shape, dtype=dtype), requires_grad=requires_grad)


def randn(*shape, requires_grad: bool = False, dtype=np.float32) -> Tensor:
    """Create tensor with standard normal values."""
    if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
        shape = tuple(shape[0])
    return Tensor(np.random.randn(*shape).astype(dtype), requires_grad=requires_grad)


def rand(*shape, requires_grad: bool = False, dtype=np.float32) -> Tensor:
    """Create tensor with uniform [0, 1) values."""
    if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
        shape = tuple(shape[0])
    return Tensor(np.random.rand(*shape).astype(dtype), requires_grad=requires_grad)


def randint(low: int, high: int, size: Tuple[int, ...], dtype=np.int64) -> Tensor:
    """Create tensor with random integers."""
    return Tensor(np.random.randint(low, high, size=size, dtype=dtype))


def arange(start: float, stop: Optional[float] = None, step: float = 1, requires_grad: bool = False) -> Tensor:
    """Create tensor with evenly spaced values."""
    if stop is None:
        stop = start
        start = 0
    return Tensor(np.arange(start, stop, step, dtype=np.float32), requires_grad=requires_grad)


def linspace(start: float, stop: float, num: int, requires_grad: bool = False) -> Tensor:
    """Create tensor with evenly spaced values."""
    return Tensor(np.linspace(start, stop, num, dtype=np.float32), requires_grad=requires_grad)


def eye(n: int, m: Optional[int] = None, requires_grad: bool = False) -> Tensor:
    """Create identity matrix."""
    return Tensor(np.eye(n, m, dtype=np.float32), requires_grad=requires_grad)


def from_numpy(array: np.ndarray, requires_grad: bool = False) -> Tensor:
    """Create tensor from numpy array."""
    return Tensor(array, requires_grad=requires_grad)


def stack(tensors: List[Tensor], axis: int = 0) -> Tensor:
    """Stack tensors along a new dimension."""
    requires_grad = any(t.requires_grad for t in tensors)
    out = Tensor(
        np.stack([t.data for t in tensors], axis=axis),
        requires_grad=requires_grad,
        _children=tuple(tensors),
        _op="stack",
    )

    def _backward():
        grads = np.split(out.grad, len(tensors), axis=axis)
        for t, g in zip(tensors, grads):
            if t.requires_grad:
                if t.grad is None:
                    t.grad = np.zeros_like(t.data)
                t.grad = t.grad + g.squeeze(axis)

    out._backward = _backward
    return out


def cat(tensors: List[Tensor], axis: int = 0) -> Tensor:
    """Concatenate tensors along an existing dimension."""
    requires_grad = any(t.requires_grad for t in tensors)
    out = Tensor(
        np.concatenate([t.data for t in tensors], axis=axis),
        requires_grad=requires_grad,
        _children=tuple(tensors),
        _op="cat",
    )

    def _backward():
        sizes = [t.shape[axis] for t in tensors]
        indices = np.cumsum([0] + sizes)

        for i, t in enumerate(tensors):
            if t.requires_grad:
                slices = [slice(None)] * out.ndim
                slices[axis] = slice(indices[i], indices[i + 1])

                if t.grad is None:
                    t.grad = np.zeros_like(t.data)
                t.grad = t.grad + out.grad[tuple(slices)]

    out._backward = _backward
    return out


def concat(tensors: List[Tensor], axis: int = 0) -> Tensor:
    """Alias for cat."""
    return cat(tensors, axis)


def split(tensor: Tensor, split_size: int, axis: int = 0) -> List[Tensor]:
    """Split tensor into chunks."""
    n_splits = tensor.shape[axis] // split_size
    arrays = np.array_split(tensor.data, n_splits, axis=axis)
    return [Tensor(arr, requires_grad=tensor.requires_grad) for arr in arrays]


def chunk(tensor: Tensor, chunks: int, axis: int = 0) -> List[Tensor]:
    """Split tensor into specified number of chunks."""
    arrays = np.array_split(tensor.data, chunks, axis=axis)
    return [Tensor(arr, requires_grad=tensor.requires_grad) for arr in arrays]
