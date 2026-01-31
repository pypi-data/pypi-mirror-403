"""
RMSprop optimizer.
"""

from __future__ import annotations

from typing import Iterable
import numpy as np

from nalyst.nn.optim.optimizer import Optimizer


class RMSprop(Optimizer):
    """
    RMSprop optimizer.

    Parameters
    ----------
    params : iterable
        Parameters to optimize.
    lr : float, default=0.01
        Learning rate.
    alpha : float, default=0.99
        Smoothing constant.
    eps : float, default=1e-8
        Term for numerical stability.
    weight_decay : float, default=0
        L2 regularization coefficient.
    momentum : float, default=0
        Momentum factor.
    centered : bool, default=False
        Compute centered RMSprop.

    Examples
    --------
    >>> optimizer = RMSprop(model.parameters(), lr=0.01)
    >>> optimizer.zero_grad()
    >>> loss.backward()
    >>> optimizer.step()
    """

    def __init__(
        self,
        params: Iterable,
        lr: float = 0.01,
        alpha: float = 0.99,
        eps: float = 1e-8,
        weight_decay: float = 0.0,
        momentum: float = 0.0,
        centered: bool = False,
    ):
        if lr < 0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if alpha < 0 or alpha >= 1:
            raise ValueError(f"Invalid alpha: {alpha}")
        if eps < 0:
            raise ValueError(f"Invalid eps: {eps}")
        if weight_decay < 0:
            raise ValueError(f"Invalid weight_decay: {weight_decay}")
        if momentum < 0:
            raise ValueError(f"Invalid momentum: {momentum}")

        defaults = {
            "lr": lr,
            "alpha": alpha,
            "eps": eps,
            "weight_decay": weight_decay,
            "momentum": momentum,
            "centered": centered,
        }
        super().__init__(params, defaults)

    def step(self) -> None:
        """
        Perform a single optimization step.
        """
        for group in self.param_groups:
            alpha = group["alpha"]
            eps = group["eps"]
            weight_decay = group["weight_decay"]
            momentum = group["momentum"]
            centered = group["centered"]
            lr = group["lr"]

            for p in group["params"]:
                if p.grad is None:
                    continue

                grad = p.grad

                # L2 regularization
                if weight_decay != 0:
                    grad = grad + weight_decay * p.data

                param_id = id(p)

                if param_id not in self.state:
                    self.state[param_id] = {
                        "square_avg": np.zeros_like(p.data),
                    }
                    if momentum > 0:
                        self.state[param_id]["momentum_buffer"] = np.zeros_like(p.data)
                    if centered:
                        self.state[param_id]["grad_avg"] = np.zeros_like(p.data)

                state = self.state[param_id]
                square_avg = state["square_avg"]

                # Update running average of squared gradients
                square_avg *= alpha
                square_avg += (1 - alpha) * (grad ** 2)

                if centered:
                    grad_avg = state["grad_avg"]
                    grad_avg *= alpha
                    grad_avg += (1 - alpha) * grad
                    avg = np.sqrt(square_avg - grad_avg ** 2 + eps)
                else:
                    avg = np.sqrt(square_avg) + eps

                if momentum > 0:
                    buf = state["momentum_buffer"]
                    buf *= momentum
                    buf += grad / avg
                    p.data -= lr * buf
                else:
                    p.data -= lr * grad / avg
