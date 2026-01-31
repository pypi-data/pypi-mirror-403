"""
Adam and AdamW optimizers.
"""

from __future__ import annotations

from typing import Iterable, Tuple
import numpy as np

from nalyst.nn.optim.optimizer import Optimizer


class Adam(Optimizer):
    """
    Adam optimizer.

    Parameters
    ----------
    params : iterable
        Parameters to optimize.
    lr : float, default=0.001
        Learning rate.
    betas : tuple, default=(0.9, 0.999)
        Coefficients for computing running averages.
    eps : float, default=1e-8
        Term for numerical stability.
    weight_decay : float, default=0
        L2 regularization coefficient.
    amsgrad : bool, default=False
        Use AMSGrad variant.

    Examples
    --------
    >>> optimizer = Adam(model.parameters(), lr=0.001)
    >>> optimizer.zero_grad()
    >>> loss.backward()
    >>> optimizer.step()
    """

    def __init__(
        self,
        params: Iterable,
        lr: float = 0.001,
        betas: Tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.0,
        amsgrad: bool = False,
    ):
        if lr < 0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError(f"Invalid beta1: {betas[0]}")
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError(f"Invalid beta2: {betas[1]}")
        if eps < 0:
            raise ValueError(f"Invalid eps: {eps}")
        if weight_decay < 0:
            raise ValueError(f"Invalid weight_decay: {weight_decay}")

        defaults = {
            "lr": lr,
            "betas": betas,
            "eps": eps,
            "weight_decay": weight_decay,
            "amsgrad": amsgrad,
        }
        super().__init__(params, defaults)

    def step(self) -> None:
        """
        Perform a single optimization step.
        """
        for group in self.param_groups:
            beta1, beta2 = group["betas"]
            eps = group["eps"]
            weight_decay = group["weight_decay"]
            amsgrad = group["amsgrad"]
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
                        "step": 0,
                        "exp_avg": np.zeros_like(p.data),
                        "exp_avg_sq": np.zeros_like(p.data),
                    }
                    if amsgrad:
                        self.state[param_id]["max_exp_avg_sq"] = np.zeros_like(p.data)

                state = self.state[param_id]
                state["step"] += 1

                exp_avg = state["exp_avg"]
                exp_avg_sq = state["exp_avg_sq"]

                # Update biased first moment estimate
                exp_avg *= beta1
                exp_avg += (1 - beta1) * grad

                # Update biased second moment estimate
                exp_avg_sq *= beta2
                exp_avg_sq += (1 - beta2) * (grad ** 2)

                # Bias correction
                bias_correction1 = 1 - beta1 ** state["step"]
                bias_correction2 = 1 - beta2 ** state["step"]

                if amsgrad:
                    max_exp_avg_sq = state["max_exp_avg_sq"]
                    np.maximum(max_exp_avg_sq, exp_avg_sq, out=max_exp_avg_sq)
                    denom = (np.sqrt(max_exp_avg_sq) / np.sqrt(bias_correction2)) + eps
                else:
                    denom = (np.sqrt(exp_avg_sq) / np.sqrt(bias_correction2)) + eps

                step_size = lr / bias_correction1

                # Update parameters
                p.data -= step_size * (exp_avg / denom)


class AdamW(Optimizer):
    """
    AdamW optimizer with decoupled weight decay.

    Parameters
    ----------
    params : iterable
        Parameters to optimize.
    lr : float, default=0.001
        Learning rate.
    betas : tuple, default=(0.9, 0.999)
        Coefficients for computing running averages.
    eps : float, default=1e-8
        Term for numerical stability.
    weight_decay : float, default=0.01
        Weight decay coefficient (decoupled).
    amsgrad : bool, default=False
        Use AMSGrad variant.

    Examples
    --------
    >>> optimizer = AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
    >>> optimizer.zero_grad()
    >>> loss.backward()
    >>> optimizer.step()
    """

    def __init__(
        self,
        params: Iterable,
        lr: float = 0.001,
        betas: Tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.01,
        amsgrad: bool = False,
    ):
        if lr < 0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError(f"Invalid beta1: {betas[0]}")
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError(f"Invalid beta2: {betas[1]}")
        if eps < 0:
            raise ValueError(f"Invalid eps: {eps}")
        if weight_decay < 0:
            raise ValueError(f"Invalid weight_decay: {weight_decay}")

        defaults = {
            "lr": lr,
            "betas": betas,
            "eps": eps,
            "weight_decay": weight_decay,
            "amsgrad": amsgrad,
        }
        super().__init__(params, defaults)

    def step(self) -> None:
        """
        Perform a single optimization step.
        """
        for group in self.param_groups:
            beta1, beta2 = group["betas"]
            eps = group["eps"]
            weight_decay = group["weight_decay"]
            amsgrad = group["amsgrad"]
            lr = group["lr"]

            for p in group["params"]:
                if p.grad is None:
                    continue

                grad = p.grad
                param_id = id(p)

                if param_id not in self.state:
                    self.state[param_id] = {
                        "step": 0,
                        "exp_avg": np.zeros_like(p.data),
                        "exp_avg_sq": np.zeros_like(p.data),
                    }
                    if amsgrad:
                        self.state[param_id]["max_exp_avg_sq"] = np.zeros_like(p.data)

                state = self.state[param_id]
                state["step"] += 1

                exp_avg = state["exp_avg"]
                exp_avg_sq = state["exp_avg_sq"]

                # Update biased first moment estimate
                exp_avg *= beta1
                exp_avg += (1 - beta1) * grad

                # Update biased second moment estimate
                exp_avg_sq *= beta2
                exp_avg_sq += (1 - beta2) * (grad ** 2)

                # Bias correction
                bias_correction1 = 1 - beta1 ** state["step"]
                bias_correction2 = 1 - beta2 ** state["step"]

                if amsgrad:
                    max_exp_avg_sq = state["max_exp_avg_sq"]
                    np.maximum(max_exp_avg_sq, exp_avg_sq, out=max_exp_avg_sq)
                    denom = (np.sqrt(max_exp_avg_sq) / np.sqrt(bias_correction2)) + eps
                else:
                    denom = (np.sqrt(exp_avg_sq) / np.sqrt(bias_correction2)) + eps

                step_size = lr / bias_correction1

                # Decoupled weight decay
                p.data *= (1 - lr * weight_decay)

                # Update parameters
                p.data -= step_size * (exp_avg / denom)
