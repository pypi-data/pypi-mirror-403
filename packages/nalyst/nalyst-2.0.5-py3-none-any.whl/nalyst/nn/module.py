"""
Module base class for neural networks.

Provides the foundation for building neural network architectures.
"""

from __future__ import annotations

from typing import Optional, Iterator, Dict, List, Tuple, Callable, Any, Set
from collections import OrderedDict
import numpy as np

from nalyst.nn.tensor import Tensor
from nalyst.nn.parameter import Parameter


class Module:
    """
    Base class for all neural network modules.

    Your models should subclass this class. Modules can contain other Modules,
    allowing you to nest them in a tree structure. You can assign submodules
    as regular attributes.

    Examples
    --------
    >>> import nalyst.nn as nn
    >>>
    >>> class MyModel(nn.Module):
    ...     def __init__(self):
    ...         super().__init__()
    ...         self.fc1 = nn.Linear(10, 5)
    ...         self.fc2 = nn.Linear(5, 2)
    ...
    ...     def forward(self, x):
    ...         x = nn.functional.relu(self.fc1(x))
    ...         return self.fc2(x)
    >>>
    >>> model = MyModel()
    >>> output = model(input_tensor)
    """

    _version: int = 1
    training: bool

    def __init__(self):
        self._parameters: Dict[str, Optional[Parameter]] = OrderedDict()
        self._modules: Dict[str, Optional["Module"]] = OrderedDict()
        self._buffers: Dict[str, Optional[Tensor]] = OrderedDict()
        self.training = True

    def forward(self, *args, **kwargs) -> Tensor:
        """
        Define the computation performed at every call.

        Should be overridden by all subclasses.
        """
        raise NotImplementedError(
            f"Module [{type(self).__name__}] is missing the required 'forward' method"
        )

    def __call__(self, *args, **kwargs) -> Tensor:
        """Make the module callable."""
        return self.forward(*args, **kwargs)

    def __setattr__(self, name: str, value: Any) -> None:
        """Automatically register Parameters and Modules."""
        if isinstance(value, Parameter):
            if "_parameters" not in self.__dict__:
                raise AttributeError(
                    "cannot assign parameters before Module.__init__() call"
                )
            self._parameters[name] = value
        elif isinstance(value, Module):
            if "_modules" not in self.__dict__:
                raise AttributeError(
                    "cannot assign modules before Module.__init__() call"
                )
            self._modules[name] = value
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Any:
        """Get parameters and modules by name."""
        if "_parameters" in self.__dict__:
            if name in self._parameters:
                return self._parameters[name]
        if "_modules" in self.__dict__:
            if name in self._modules:
                return self._modules[name]
        if "_buffers" in self.__dict__:
            if name in self._buffers:
                return self._buffers[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __delattr__(self, name: str) -> None:
        """Delete attributes."""
        if name in self._parameters:
            del self._parameters[name]
        elif name in self._modules:
            del self._modules[name]
        elif name in self._buffers:
            del self._buffers[name]
        else:
            super().__delattr__(name)

    def register_parameter(self, name: str, param: Optional[Parameter]) -> None:
        """
        Add a parameter to the module.

        Parameters
        ----------
        name : str
            Name of the parameter.
        param : Parameter or None
            The parameter to register.
        """
        if param is None:
            self._parameters[name] = None
        elif not isinstance(param, Parameter):
            raise TypeError(f"Expected Parameter, got {type(param)}")
        else:
            self._parameters[name] = param

    def register_buffer(self, name: str, tensor: Optional[Tensor]) -> None:
        """
        Add a buffer to the module.

        Buffers are tensors that should be saved/loaded with the model
        but don't require gradients.

        Parameters
        ----------
        name : str
            Name of the buffer.
        tensor : Tensor or None
            The buffer tensor.
        """
        self._buffers[name] = tensor

    def add_module(self, name: str, module: Optional["Module"]) -> None:
        """
        Add a child module.

        Parameters
        ----------
        name : str
            Name of the child module.
        module : Module or None
            The child module.
        """
        if module is not None and not isinstance(module, Module):
            raise TypeError(f"Expected Module, got {type(module)}")
        self._modules[name] = module

    def parameters(self, recurse: bool = True) -> Iterator[Parameter]:
        """
        Return an iterator over module parameters.

        Parameters
        ----------
        recurse : bool
            If True, yields parameters of this module and all submodules.

        Yields
        ------
        Parameter
            Module parameters.
        """
        memo: Set[Parameter] = set()
        for name, param in self.named_parameters(recurse=recurse):
            if param is not None and param not in memo:
                memo.add(param)
                yield param

    def named_parameters(
        self,
        prefix: str = "",
        recurse: bool = True,
    ) -> Iterator[Tuple[str, Parameter]]:
        """
        Return an iterator over module parameters, yielding name and parameter.

        Parameters
        ----------
        prefix : str
            Prefix for parameter names.
        recurse : bool
            If True, yields parameters of submodules.

        Yields
        ------
        Tuple[str, Parameter]
            Name and parameter pairs.
        """
        memo: Set[Parameter] = set()

        for name, param in self._parameters.items():
            if param is not None and param not in memo:
                memo.add(param)
                full_name = f"{prefix}.{name}" if prefix else name
                yield full_name, param

        if recurse:
            for module_name, module in self._modules.items():
                if module is not None:
                    submodule_prefix = f"{prefix}.{module_name}" if prefix else module_name
                    for name, param in module.named_parameters(
                        prefix=submodule_prefix, recurse=True
                    ):
                        if param not in memo:
                            memo.add(param)
                            yield name, param

    def buffers(self, recurse: bool = True) -> Iterator[Tensor]:
        """
        Return an iterator over module buffers.

        Parameters
        ----------
        recurse : bool
            If True, yields buffers of all submodules.

        Yields
        ------
        Tensor
            Buffer tensors.
        """
        for name, buf in self.named_buffers(recurse=recurse):
            yield buf

    def named_buffers(
        self,
        prefix: str = "",
        recurse: bool = True,
    ) -> Iterator[Tuple[str, Tensor]]:
        """Return an iterator over module buffers, yielding name and buffer."""
        for name, buf in self._buffers.items():
            if buf is not None:
                full_name = f"{prefix}.{name}" if prefix else name
                yield full_name, buf

        if recurse:
            for module_name, module in self._modules.items():
                if module is not None:
                    submodule_prefix = f"{prefix}.{module_name}" if prefix else module_name
                    yield from module.named_buffers(prefix=submodule_prefix, recurse=True)

    def children(self) -> Iterator["Module"]:
        """Return an iterator over immediate children modules."""
        for name, module in self._modules.items():
            if module is not None:
                yield module

    def named_children(self) -> Iterator[Tuple[str, "Module"]]:
        """Return an iterator over immediate children modules, yielding name and module."""
        for name, module in self._modules.items():
            if module is not None:
                yield name, module

    def modules(self) -> Iterator["Module"]:
        """Return an iterator over all modules in the network."""
        yield self
        for name, module in self._modules.items():
            if module is not None:
                yield from module.modules()

    def named_modules(self, prefix: str = "") -> Iterator[Tuple[str, "Module"]]:
        """Return an iterator over all modules, yielding name and module."""
        yield prefix, self
        for name, module in self._modules.items():
            if module is not None:
                submodule_prefix = f"{prefix}.{name}" if prefix else name
                yield from module.named_modules(prefix=submodule_prefix)

    def train(self, mode: bool = True) -> "Module":
        """
        Set the module in training mode.

        Parameters
        ----------
        mode : bool
            Whether to set training mode (True) or evaluation mode (False).

        Returns
        -------
        Module
            self
        """
        self.training = mode
        for module in self.children():
            module.train(mode)
        return self

    def eval(self) -> "Module":
        """
        Set the module in evaluation mode.

        Equivalent to self.train(False).

        Returns
        -------
        Module
            self
        """
        return self.train(False)

    def zero_grad(self) -> None:
        """Zero out the gradients of all parameters."""
        for param in self.parameters():
            param.zero_grad()

    def requires_grad_(self, requires_grad: bool = True) -> "Module":
        """
        Change if autograd should record operations on parameters.

        Parameters
        ----------
        requires_grad : bool
            Whether to require gradients.

        Returns
        -------
        Module
            self
        """
        for param in self.parameters():
            param.requires_grad = requires_grad
        return self

    def state_dict(self) -> Dict[str, np.ndarray]:
        """
        Return a dictionary containing a whole state of the module.

        Both parameters and buffers are included.

        Returns
        -------
        dict
            State dictionary.
        """
        state = OrderedDict()

        for name, param in self.named_parameters():
            state[name] = param.data.copy()

        for name, buf in self.named_buffers():
            state[name] = buf.data.copy()

        return state

    def load_state_dict(self, state_dict: Dict[str, np.ndarray], strict: bool = True) -> None:
        """
        Copy parameters and buffers from state_dict into this module.

        Parameters
        ----------
        state_dict : dict
            State dictionary.
        strict : bool
            Whether to strictly enforce that the keys match.
        """
        own_state = self.state_dict()

        if strict:
            missing = set(own_state.keys()) - set(state_dict.keys())
            unexpected = set(state_dict.keys()) - set(own_state.keys())

            if missing:
                raise KeyError(f"Missing keys: {missing}")
            if unexpected:
                raise KeyError(f"Unexpected keys: {unexpected}")

        for name, param in self.named_parameters():
            if name in state_dict:
                param.data = state_dict[name].copy()

        for name, buf in self.named_buffers():
            if name in state_dict:
                buf.data = state_dict[name].copy()

    def num_parameters(self, only_trainable: bool = False) -> int:
        """
        Count the number of parameters.

        Parameters
        ----------
        only_trainable : bool
            If True, only count parameters that require gradients.

        Returns
        -------
        int
            Number of parameters.
        """
        total = 0
        for param in self.parameters():
            if only_trainable and not param.requires_grad:
                continue
            total += param.size
        return total

    def apply(self, fn: Callable[["Module"], None]) -> "Module":
        """
        Apply a function to every submodule.

        Parameters
        ----------
        fn : callable
            Function to apply.

        Returns
        -------
        Module
            self
        """
        for module in self.children():
            module.apply(fn)
        fn(self)
        return self

    def __repr__(self) -> str:
        """String representation of the module."""
        lines = [self.__class__.__name__ + "("]
        for name, module in self._modules.items():
            mod_str = repr(module).replace("\n", "\n  ")
            lines.append(f"  ({name}): {mod_str}")
        lines.append(")")
        return "\n".join(lines)

    def extra_repr(self) -> str:
        """Extra representation for subclasses to override."""
        return ""


class Sequential(Module):
    """
    A sequential container.

    Modules will be added to it in the order they are passed.

    Examples
    --------
    >>> model = nn.Sequential(
    ...     nn.Linear(10, 20),
    ...     nn.ReLU(),
    ...     nn.Linear(20, 5),
    ... )
    >>> output = model(x)
    """

    def __init__(self, *args):
        super().__init__()
        for idx, module in enumerate(args):
            self.add_module(str(idx), module)

    def forward(self, x: Tensor) -> Tensor:
        """Pass input through all modules sequentially."""
        for module in self._modules.values():
            x = module(x)
        return x

    def __getitem__(self, idx: int) -> Module:
        """Get module by index."""
        return list(self._modules.values())[idx]

    def __len__(self) -> int:
        """Return number of modules."""
        return len(self._modules)

    def __iter__(self):
        """Iterate over modules."""
        return iter(self._modules.values())

    def append(self, module: Module) -> "Sequential":
        """Append a module to the end."""
        self.add_module(str(len(self)), module)
        return self


class ModuleList(Module):
    """
    Holds submodules in a list.

    ModuleList can be indexed like a regular Python list, but modules
    it contains are properly registered.

    Examples
    --------
    >>> layers = nn.ModuleList([nn.Linear(10, 10) for _ in range(5)])
    >>> for layer in layers:
    ...     x = layer(x)
    """

    def __init__(self, modules: Optional[List[Module]] = None):
        super().__init__()
        if modules is not None:
            for idx, module in enumerate(modules):
                self.add_module(str(idx), module)

    def __getitem__(self, idx: int) -> Module:
        """Get module by index."""
        if idx < 0:
            idx = len(self) + idx
        return list(self._modules.values())[idx]

    def __setitem__(self, idx: int, module: Module) -> None:
        """Set module by index."""
        if idx < 0:
            idx = len(self) + idx
        key = list(self._modules.keys())[idx]
        self._modules[key] = module

    def __len__(self) -> int:
        """Return number of modules."""
        return len(self._modules)

    def __iter__(self):
        """Iterate over modules."""
        return iter(self._modules.values())

    def append(self, module: Module) -> "ModuleList":
        """Append a module to the end."""
        self.add_module(str(len(self)), module)
        return self

    def extend(self, modules: List[Module]) -> "ModuleList":
        """Extend the list with modules."""
        for module in modules:
            self.append(module)
        return self

    def insert(self, idx: int, module: Module) -> None:
        """Insert a module at the given index."""
        # Rebuild the OrderedDict with the new module inserted
        new_modules = OrderedDict()
        items = list(self._modules.items())

        for i, (key, mod) in enumerate(items[:idx]):
            new_modules[str(i)] = mod

        new_modules[str(idx)] = module

        for i, (key, mod) in enumerate(items[idx:], start=idx + 1):
            new_modules[str(i)] = mod

        self._modules = new_modules


class ModuleDict(Module):
    """
    Holds submodules in a dictionary.

    Examples
    --------
    >>> layers = nn.ModuleDict({
    ...     'conv': nn.Conv2d(3, 64, 3),
    ...     'pool': nn.MaxPool2d(2),
    ... })
    >>> x = layers['conv'](x)
    >>> x = layers['pool'](x)
    """

    def __init__(self, modules: Optional[Dict[str, Module]] = None):
        super().__init__()
        if modules is not None:
            for key, module in modules.items():
                self.add_module(key, module)

    def __getitem__(self, key: str) -> Module:
        """Get module by key."""
        return self._modules[key]

    def __setitem__(self, key: str, module: Module) -> None:
        """Set module by key."""
        self.add_module(key, module)

    def __delitem__(self, key: str) -> None:
        """Delete module by key."""
        del self._modules[key]

    def __len__(self) -> int:
        """Return number of modules."""
        return len(self._modules)

    def __iter__(self):
        """Iterate over keys."""
        return iter(self._modules.keys())

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._modules

    def keys(self):
        """Return keys."""
        return self._modules.keys()

    def values(self):
        """Return modules."""
        return self._modules.values()

    def items(self):
        """Return key-module pairs."""
        return self._modules.items()

    def update(self, modules: Dict[str, Module]) -> None:
        """Update with modules from another dict."""
        for key, module in modules.items():
            self.add_module(key, module)
