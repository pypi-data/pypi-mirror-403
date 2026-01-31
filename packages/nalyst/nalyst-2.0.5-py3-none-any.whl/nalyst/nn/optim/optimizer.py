"""
Base optimizer class.
"""

from __future__ import annotations

from typing import List, Dict, Any, Iterable, Optional
import numpy as np


class Optimizer:
    """
    Base class for all optimizers.

    Parameters
    ----------
    params : iterable
        Parameters to optimize.
    defaults : dict
        Default optimizer options.

    Examples
    --------
    >>> optimizer = SGD(model.parameters(), lr=0.01)
    >>> optimizer.zero_grad()
    >>> loss.backward()
    >>> optimizer.step()
    """

    def __init__(self, params: Iterable, defaults: Dict[str, Any]):
        self.defaults = defaults
        self.state: Dict[int, Dict[str, Any]] = {}

        # Store parameter groups
        self.param_groups: List[Dict[str, Any]] = []

        # Convert params to list
        param_list = list(params)

        if len(param_list) == 0:
            raise ValueError("Optimizer received empty parameter list")

        # Handle parameter groups
        if isinstance(param_list[0], dict):
            for group in param_list:
                self.add_param_group(group)
        else:
            self.add_param_group({"params": param_list})

    def add_param_group(self, param_group: Dict[str, Any]) -> None:
        """
        Add a parameter group.

        Parameters
        ----------
        param_group : dict
            Parameter group with 'params' key and optional hyperparameters.
        """
        params = list(param_group["params"])

        # Create group with defaults
        group = {**self.defaults}
        for key, value in param_group.items():
            if key != "params":
                group[key] = value
        group["params"] = params

        self.param_groups.append(group)

    def zero_grad(self) -> None:
        """
        Reset gradients of all parameters to zero.
        """
        for group in self.param_groups:
            for p in group["params"]:
                if hasattr(p, "grad") and p.grad is not None:
                    p.grad = None

    def step(self) -> None:
        """
        Perform a single optimization step.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclass must implement step()")

    def state_dict(self) -> Dict[str, Any]:
        """
        Return optimizer state.

        Returns
        -------
        dict
            Optimizer state dictionary.
        """
        return {
            "state": self.state,
            "param_groups": [
                {k: v for k, v in group.items() if k != "params"}
                for group in self.param_groups
            ],
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """
        Load optimizer state.

        Parameters
        ----------
        state_dict : dict
            Optimizer state dictionary.
        """
        self.state = state_dict["state"]

        for group, saved_group in zip(self.param_groups, state_dict["param_groups"]):
            for key, value in saved_group.items():
                group[key] = value

    @property
    def learning_rate(self) -> float:
        """Get current learning rate."""
        return self.param_groups[0]["lr"]

    @learning_rate.setter
    def learning_rate(self, value: float) -> None:
        """Set learning rate for all groups."""
        for group in self.param_groups:
            group["lr"] = value

    def __repr__(self) -> str:
        group_str = ", ".join(
            f"lr={group['lr']}" for group in self.param_groups
        )
        return f"{self.__class__.__name__}({group_str})"
