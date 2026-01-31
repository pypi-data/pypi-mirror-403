"""
Adagrad optimizer.
"""

from __future__ import annotations

from typing import Iterable
import numpy as np

from nalyst.nn.optim.optimizer import Optimizer


class Adagrad(Optimizer):
    """
    Adagrad optimizer.

    Parameters
    ----------
    params : iterable
        Parameters to optimize.
    lr : float, default=0.01
        Learning rate.
    lr_decay : float, default=0
        Learning rate decay.
    weight_decay : float, default=0
        L2 regularization coefficient.
    eps : float, default=1e-10
        Term for numerical stability.

    Examples
    --------
    >>> optimizer = Adagrad(model.parameters(), lr=0.01)
    >>> optimizer.zero_grad()
    >>> loss.backward()
    >>> optimizer.step()
    """

    def __init__(
        self,
        params: Iterable,
        lr: float = 0.01,
        lr_decay: float = 0.0,
        weight_decay: float = 0.0,
        eps: float = 1e-10,
    ):
        if lr < 0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if lr_decay < 0:
            raise ValueError(f"Invalid lr_decay: {lr_decay}")
        if weight_decay < 0:
            raise ValueError(f"Invalid weight_decay: {weight_decay}")
        if eps < 0:
            raise ValueError(f"Invalid eps: {eps}")

        defaults = {
            "lr": lr,
            "lr_decay": lr_decay,
            "weight_decay": weight_decay,
            "eps": eps,
        }
        super().__init__(params, defaults)

    def step(self) -> None:
        """
        Perform a single optimization step.
        """
        for group in self.param_groups:
            lr_decay = group["lr_decay"]
            weight_decay = group["weight_decay"]
            eps = group["eps"]
            lr = group["lr"]

            for p in group["params"]:
                if p.grad is None:
                    continue

                grad = p.grad

                param_id = id(p)

                if param_id not in self.state:
                    self.state[param_id] = {
                        "step": 0,
                        "sum": np.zeros_like(p.data),
                    }

                state = self.state[param_id]
                state["step"] += 1

                # L2 regularization
                if weight_decay != 0:
                    grad = grad + weight_decay * p.data

                # Compute effective learning rate
                clr = lr / (1 + (state["step"] - 1) * lr_decay)

                # Accumulate squared gradients
                state["sum"] += grad ** 2

                # Update parameters
                p.data -= clr * grad / (np.sqrt(state["sum"]) + eps)
