"""
Stochastic Gradient Descent optimizer.
"""

from __future__ import annotations

from typing import Iterable, Optional
import numpy as np

from nalyst.nn.optim.optimizer import Optimizer


class SGD(Optimizer):
    """
    Stochastic Gradient Descent with momentum.

    Parameters
    ----------
    params : iterable
        Parameters to optimize.
    lr : float
        Learning rate.
    momentum : float, default=0
        Momentum factor.
    weight_decay : float, default=0
        L2 regularization coefficient.
    dampening : float, default=0
        Dampening for momentum.
    nesterov : bool, default=False
        Enable Nesterov momentum.

    Examples
    --------
    >>> optimizer = SGD(model.parameters(), lr=0.01, momentum=0.9)
    >>> for epoch in range(epochs):
    ...     optimizer.zero_grad()
    ...     loss = criterion(model(x), y)
    ...     loss.backward()
    ...     optimizer.step()
    """

    def __init__(
        self,
        params: Iterable,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        dampening: float = 0.0,
        nesterov: bool = False,
    ):
        if lr < 0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if momentum < 0:
            raise ValueError(f"Invalid momentum: {momentum}")
        if weight_decay < 0:
            raise ValueError(f"Invalid weight_decay: {weight_decay}")
        if nesterov and (momentum <= 0 or dampening != 0):
            raise ValueError("Nesterov requires momentum > 0 and dampening = 0")

        defaults = {
            "lr": lr,
            "momentum": momentum,
            "weight_decay": weight_decay,
            "dampening": dampening,
            "nesterov": nesterov,
        }
        super().__init__(params, defaults)

    def step(self) -> None:
        """
        Perform a single optimization step.
        """
        for group in self.param_groups:
            momentum = group["momentum"]
            weight_decay = group["weight_decay"]
            dampening = group["dampening"]
            nesterov = group["nesterov"]
            lr = group["lr"]

            for p in group["params"]:
                if p.grad is None:
                    continue

                grad = p.grad

                # Add weight decay
                if weight_decay != 0:
                    grad = grad + weight_decay * p.data

                # Apply momentum
                if momentum != 0:
                    param_id = id(p)

                    if param_id not in self.state:
                        self.state[param_id] = {}

                    state = self.state[param_id]

                    if "momentum_buffer" not in state:
                        buf = state["momentum_buffer"] = grad.copy()
                    else:
                        buf = state["momentum_buffer"]
                        buf *= momentum
                        buf += (1 - dampening) * grad

                    if nesterov:
                        grad = grad + momentum * buf
                    else:
                        grad = buf

                # Update parameters
                p.data -= lr * grad
