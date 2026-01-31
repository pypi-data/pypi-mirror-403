"""
Parameter class for trainable tensors in neural networks.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np

from nalyst.nn.tensor import Tensor


class Parameter(Tensor):
    """
    A Tensor that is automatically registered as a parameter when assigned
    as an attribute of a Module.

    Parameters are tensors that require gradients by default and are meant
    to be optimized during training.

    Parameters
    ----------
    data : array-like or Tensor
        The parameter data.
    requires_grad : bool, default=True
        Whether to track gradients.

    Examples
    --------
    >>> from nalyst.nn import Parameter
    >>> weight = Parameter(np.random.randn(10, 5))
    >>> weight.requires_grad
    True
    """

    def __init__(
        self,
        data: Tensor | np.ndarray | list,
        requires_grad: bool = True,
    ):
        if isinstance(data, Tensor):
            data = data.data
        super().__init__(data, requires_grad=requires_grad)

    def __repr__(self) -> str:
        return f"Parameter containing:\n{super().__repr__()}"


def register_parameter(module: "Module", name: str, param: Optional[Parameter]) -> None:
    """
    Register a parameter with a module.

    Parameters
    ----------
    module : Module
        The module to register with.
    name : str
        The parameter name.
    param : Parameter or None
        The parameter to register.
    """
    if param is None:
        module._parameters[name] = None
    elif not isinstance(param, Parameter):
        raise TypeError(f"Expected Parameter, got {type(param)}")
    else:
        module._parameters[name] = param
