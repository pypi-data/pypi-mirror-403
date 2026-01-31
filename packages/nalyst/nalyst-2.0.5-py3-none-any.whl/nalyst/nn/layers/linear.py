"""
Linear (fully connected) layers.
"""

from __future__ import annotations

from typing import Optional
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.parameter import Parameter
from nalyst.nn.tensor import Tensor


class Linear(Module):
    """
    Applies a linear transformation: y = xW^T + b

    Parameters
    ----------
    in_features : int
        Size of each input sample.
    out_features : int
        Size of each output sample.
    bias : bool, default=True
        If True, adds a learnable bias.

    Attributes
    ----------
    weight : Parameter
        The learnable weights of shape (out_features, in_features).
    bias : Parameter or None
        The learnable bias of shape (out_features,).

    Examples
    --------
    >>> layer = nn.Linear(20, 10)
    >>> x = Tensor(np.random.randn(32, 20))
    >>> output = layer(x)  # shape: (32, 10)
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        # Kaiming/He initialization
        k = 1 / in_features
        self.weight = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (out_features, in_features))
        )

        if bias:
            self.bias = Parameter(
                np.random.uniform(-np.sqrt(k), np.sqrt(k), (out_features,))
            )
        else:
            self.register_parameter("bias", None)

    def forward(self, x: Tensor) -> Tensor:
        """
        Apply linear transformation.

        Parameters
        ----------
        x : Tensor
            Input of shape (*, in_features).

        Returns
        -------
        Tensor
            Output of shape (*, out_features).
        """
        # x @ W^T + b
        output = x.matmul(self.weight.transpose())

        if self.bias is not None:
            output = output + self.bias

        return output

    def extra_repr(self) -> str:
        return f"in_features={self.in_features}, out_features={self.out_features}, bias={self.bias is not None}"

    def __repr__(self) -> str:
        return f"Linear({self.extra_repr()})"


class Bilinear(Module):
    """
    Applies a bilinear transformation: y = x1^T A x2 + b

    Parameters
    ----------
    in1_features : int
        Size of first input.
    in2_features : int
        Size of second input.
    out_features : int
        Size of output.
    bias : bool, default=True
        If True, adds a learnable bias.

    Examples
    --------
    >>> layer = nn.Bilinear(10, 20, 5)
    >>> x1 = Tensor(np.random.randn(32, 10))
    >>> x2 = Tensor(np.random.randn(32, 20))
    >>> output = layer(x1, x2)  # shape: (32, 5)
    """

    def __init__(
        self,
        in1_features: int,
        in2_features: int,
        out_features: int,
        bias: bool = True,
    ):
        super().__init__()
        self.in1_features = in1_features
        self.in2_features = in2_features
        self.out_features = out_features

        k = 1 / in1_features
        self.weight = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (out_features, in1_features, in2_features))
        )

        if bias:
            self.bias = Parameter(np.zeros(out_features))
        else:
            self.register_parameter("bias", None)

    def forward(self, x1: Tensor, x2: Tensor) -> Tensor:
        """
        Apply bilinear transformation.

        Parameters
        ----------
        x1 : Tensor
            First input of shape (batch, in1_features).
        x2 : Tensor
            Second input of shape (batch, in2_features).

        Returns
        -------
        Tensor
            Output of shape (batch, out_features).
        """
        batch_size = x1.shape[0]
        output_data = np.zeros((batch_size, self.out_features), dtype=np.float32)

        # y_k = x1^T W_k x2 for each output feature k
        for k in range(self.out_features):
            # x1 @ W_k @ x2.T diagonal
            Wk = self.weight.data[k]  # (in1, in2)
            # (batch, in1) @ (in1, in2) = (batch, in2)
            temp = x1.data @ Wk
            # element-wise multiply with x2 and sum
            output_data[:, k] = np.sum(temp * x2.data, axis=1)

        output = Tensor(output_data, requires_grad=x1.requires_grad or x2.requires_grad)

        if self.bias is not None:
            output = output + self.bias

        return output

    def __repr__(self) -> str:
        return f"Bilinear(in1_features={self.in1_features}, in2_features={self.in2_features}, out_features={self.out_features})"
