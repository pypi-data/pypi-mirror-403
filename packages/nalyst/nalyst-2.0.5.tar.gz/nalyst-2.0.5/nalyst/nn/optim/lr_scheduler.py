"""
Learning rate schedulers.
"""

from __future__ import annotations

from typing import List, Optional, Union
import math


class LRScheduler:
    """
    Base class for learning rate schedulers.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    last_epoch : int, default=-1
        Index of last epoch.
    """

    def __init__(self, optimizer, last_epoch: int = -1):
        self.optimizer = optimizer
        self.last_epoch = last_epoch
        self.base_lrs = [group["lr"] for group in optimizer.param_groups]

        if last_epoch == -1:
            for group, lr in zip(optimizer.param_groups, self.base_lrs):
                group["lr"] = lr

    def get_lr(self) -> List[float]:
        """
        Compute learning rate.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def step(self, epoch: Optional[int] = None) -> None:
        """
        Update learning rate.

        Parameters
        ----------
        epoch : int, optional
            Current epoch. If None, increment last_epoch.
        """
        if epoch is None:
            self.last_epoch += 1
        else:
            self.last_epoch = epoch

        for group, lr in zip(self.optimizer.param_groups, self.get_lr()):
            group["lr"] = lr

    def state_dict(self):
        """Return scheduler state."""
        return {"last_epoch": self.last_epoch}

    def load_state_dict(self, state_dict):
        """Load scheduler state."""
        self.last_epoch = state_dict["last_epoch"]


class StepLR(LRScheduler):
    """
    Decay learning rate by gamma every step_size epochs.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    step_size : int
        Period of learning rate decay.
    gamma : float, default=0.1
        Multiplicative factor.
    last_epoch : int, default=-1
        Index of last epoch.

    Examples
    --------
    >>> scheduler = StepLR(optimizer, step_size=30, gamma=0.1)
    >>> for epoch in range(100):
    ...     train(...)
    ...     scheduler.step()
    """

    def __init__(
        self,
        optimizer,
        step_size: int,
        gamma: float = 0.1,
        last_epoch: int = -1,
    ):
        self.step_size = step_size
        self.gamma = gamma
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> List[float]:
        return [
            base_lr * (self.gamma ** (self.last_epoch // self.step_size))
            for base_lr in self.base_lrs
        ]


class MultiStepLR(LRScheduler):
    """
    Decay learning rate at specified milestones.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    milestones : list
        List of epoch indices for LR decay.
    gamma : float, default=0.1
        Multiplicative factor.
    last_epoch : int, default=-1
        Index of last epoch.

    Examples
    --------
    >>> scheduler = MultiStepLR(optimizer, milestones=[30, 80], gamma=0.1)
    """

    def __init__(
        self,
        optimizer,
        milestones: List[int],
        gamma: float = 0.1,
        last_epoch: int = -1,
    ):
        self.milestones = sorted(milestones)
        self.gamma = gamma
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> List[float]:
        num_decays = sum(1 for m in self.milestones if m <= self.last_epoch)
        return [base_lr * (self.gamma ** num_decays) for base_lr in self.base_lrs]


class ExponentialLR(LRScheduler):
    """
    Decay learning rate exponentially.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    gamma : float
        Multiplicative factor per epoch.
    last_epoch : int, default=-1
        Index of last epoch.
    """

    def __init__(
        self,
        optimizer,
        gamma: float,
        last_epoch: int = -1,
    ):
        self.gamma = gamma
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> List[float]:
        return [base_lr * (self.gamma ** self.last_epoch) for base_lr in self.base_lrs]


class CosineAnnealingLR(LRScheduler):
    """
    Cosine annealing learning rate schedule.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    T_max : int
        Maximum number of iterations.
    eta_min : float, default=0
        Minimum learning rate.
    last_epoch : int, default=-1
        Index of last epoch.

    Examples
    --------
    >>> scheduler = CosineAnnealingLR(optimizer, T_max=100)
    """

    def __init__(
        self,
        optimizer,
        T_max: int,
        eta_min: float = 0,
        last_epoch: int = -1,
    ):
        self.T_max = T_max
        self.eta_min = eta_min
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> List[float]:
        return [
            self.eta_min + (base_lr - self.eta_min) *
            (1 + math.cos(math.pi * self.last_epoch / self.T_max)) / 2
            for base_lr in self.base_lrs
        ]


class ReduceLROnPlateau:
    """
    Reduce learning rate when metric plateaus.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    mode : str, default='min'
        One of 'min' or 'max'.
    factor : float, default=0.1
        Factor to reduce LR.
    patience : int, default=10
        Epochs to wait before reducing.
    threshold : float, default=1e-4
        Threshold for measuring improvement.
    min_lr : float, default=0
        Minimum learning rate.

    Examples
    --------
    >>> scheduler = ReduceLROnPlateau(optimizer, patience=10)
    >>> for epoch in range(100):
    ...     train(...)
    ...     val_loss = validate(...)
    ...     scheduler.step(val_loss)
    """

    def __init__(
        self,
        optimizer,
        mode: str = 'min',
        factor: float = 0.1,
        patience: int = 10,
        threshold: float = 1e-4,
        min_lr: float = 0,
    ):
        self.optimizer = optimizer
        self.mode = mode
        self.factor = factor
        self.patience = patience
        self.threshold = threshold
        self.min_lr = min_lr

        self.best = float('inf') if mode == 'min' else float('-inf')
        self.num_bad_epochs = 0

    def step(self, metric: float) -> None:
        """
        Update learning rate based on metric.

        Parameters
        ----------
        metric : float
            Current metric value.
        """
        if self._is_better(metric):
            self.best = metric
            self.num_bad_epochs = 0
        else:
            self.num_bad_epochs += 1

        if self.num_bad_epochs >= self.patience:
            self._reduce_lr()
            self.num_bad_epochs = 0

    def _is_better(self, metric: float) -> bool:
        if self.mode == 'min':
            return metric < self.best - self.threshold
        else:
            return metric > self.best + self.threshold

    def _reduce_lr(self) -> None:
        for group in self.optimizer.param_groups:
            new_lr = max(group["lr"] * self.factor, self.min_lr)
            group["lr"] = new_lr


class WarmupLR(LRScheduler):
    """
    Linear warmup learning rate scheduler.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    warmup_epochs : int
        Number of warmup epochs.
    last_epoch : int, default=-1
        Index of last epoch.

    Examples
    --------
    >>> scheduler = WarmupLR(optimizer, warmup_epochs=5)
    """

    def __init__(
        self,
        optimizer,
        warmup_epochs: int,
        last_epoch: int = -1,
    ):
        self.warmup_epochs = warmup_epochs
        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> List[float]:
        if self.last_epoch < self.warmup_epochs:
            return [
                base_lr * (self.last_epoch + 1) / self.warmup_epochs
                for base_lr in self.base_lrs
            ]
        return self.base_lrs


class OneCycleLR(LRScheduler):
    """
    OneCycle learning rate policy.

    Parameters
    ----------
    optimizer : Optimizer
        Wrapped optimizer.
    max_lr : float
        Maximum learning rate.
    total_steps : int
        Total number of training steps.
    pct_start : float, default=0.3
        Percentage of cycle for increasing LR.
    div_factor : float, default=25
        Initial LR = max_lr / div_factor.
    final_div_factor : float, default=1e4
        Final LR = max_lr / final_div_factor.

    Examples
    --------
    >>> scheduler = OneCycleLR(optimizer, max_lr=0.1, total_steps=1000)
    """

    def __init__(
        self,
        optimizer,
        max_lr: float,
        total_steps: int,
        pct_start: float = 0.3,
        div_factor: float = 25,
        final_div_factor: float = 1e4,
        last_epoch: int = -1,
    ):
        self.max_lr = max_lr
        self.total_steps = total_steps
        self.pct_start = pct_start
        self.div_factor = div_factor
        self.final_div_factor = final_div_factor

        self.initial_lr = max_lr / div_factor
        self.final_lr = max_lr / final_div_factor

        super().__init__(optimizer, last_epoch)

    def get_lr(self) -> List[float]:
        step = self.last_epoch

        if step < self.total_steps * self.pct_start:
            # Warmup phase
            pct = step / (self.total_steps * self.pct_start)
            return [self.initial_lr + (self.max_lr - self.initial_lr) * pct]
        else:
            # Annealing phase
            pct = (step - self.total_steps * self.pct_start) / \
                  (self.total_steps * (1 - self.pct_start))
            return [self.max_lr + (self.final_lr - self.max_lr) * pct]
