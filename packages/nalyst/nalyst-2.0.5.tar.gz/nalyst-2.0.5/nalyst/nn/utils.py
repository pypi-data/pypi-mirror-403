"""
Utility functions for neural networks.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, Union, List, Tuple
import os
import pickle
import numpy as np

from nalyst.nn.tensor import Tensor
from nalyst.nn.module import Module


def save_model(
    model: Module,
    path: str,
    optimizer: Optional[Any] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save model and optionally optimizer state.

    Parameters
    ----------
    model : Module
        Model to save.
    path : str
        Path to save file.
    optimizer : Optimizer, optional
        Optimizer to save.
    extra : dict, optional
        Extra data to save.

    Examples
    --------
    >>> save_model(model, 'checkpoint.pkl', optimizer=optimizer)
    """
    checkpoint = {
        'model_state_dict': model.state_dict(),
    }

    if optimizer is not None:
        checkpoint['optimizer_state_dict'] = optimizer.state_dict()

    if extra is not None:
        checkpoint.update(extra)

    with open(path, 'wb') as f:
        pickle.dump(checkpoint, f)


def load_model(
    model: Module,
    path: str,
    optimizer: Optional[Any] = None,
    strict: bool = True,
) -> Dict[str, Any]:
    """
    Load model and optionally optimizer state.

    Parameters
    ----------
    model : Module
        Model to load into.
    path : str
        Path to checkpoint file.
    optimizer : Optimizer, optional
        Optimizer to load into.
    strict : bool, default=True
        Strictly enforce state dict matching.

    Returns
    -------
    dict
        Loaded checkpoint (for accessing extra data).

    Examples
    --------
    >>> checkpoint = load_model(model, 'checkpoint.pkl', optimizer=optimizer)
    >>> epoch = checkpoint.get('epoch', 0)
    """
    with open(path, 'rb') as f:
        checkpoint = pickle.load(f)

    model.load_state_dict(checkpoint['model_state_dict'])

    if optimizer is not None and 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    return checkpoint


def save_state_dict(state_dict: Dict[str, Any], path: str) -> None:
    """
    Save state dict to file.

    Parameters
    ----------
    state_dict : dict
        State dictionary to save.
    path : str
        Path to save file.
    """
    with open(path, 'wb') as f:
        pickle.dump(state_dict, f)


def load_state_dict(path: str) -> Dict[str, Any]:
    """
    Load state dict from file.

    Parameters
    ----------
    path : str
        Path to checkpoint file.

    Returns
    -------
    dict
        Loaded state dictionary.
    """
    with open(path, 'rb') as f:
        return pickle.load(f)


def clip_grad_norm_(
    parameters,
    max_norm: float,
    norm_type: float = 2.0,
) -> float:
    """
    Clip gradient norm of parameters.

    Parameters
    ----------
    parameters : iterable
        Parameters with gradients.
    max_norm : float
        Maximum gradient norm.
    norm_type : float, default=2.0
        Type of norm to use.

    Returns
    -------
    float
        Total gradient norm before clipping.

    Examples
    --------
    >>> total_norm = clip_grad_norm_(model.parameters(), max_norm=1.0)
    """
    parameters = list(parameters)

    if norm_type == float('inf'):
        norms = [np.abs(p.grad).max() for p in parameters if p.grad is not None]
        total_norm = max(norms) if norms else 0.0
    else:
        total_norm = 0.0
        for p in parameters:
            if p.grad is not None:
                param_norm = np.linalg.norm(p.grad.flatten(), ord=norm_type)
                total_norm += param_norm ** norm_type
        total_norm = total_norm ** (1.0 / norm_type)

    clip_coef = max_norm / (total_norm + 1e-6)

    if clip_coef < 1:
        for p in parameters:
            if p.grad is not None:
                p.grad = p.grad * clip_coef

    return float(total_norm)


def clip_grad_value_(
    parameters,
    clip_value: float,
) -> None:
    """
    Clip gradient values of parameters.

    Parameters
    ----------
    parameters : iterable
        Parameters with gradients.
    clip_value : float
        Maximum absolute gradient value.
    """
    for p in parameters:
        if p.grad is not None:
            p.grad = np.clip(p.grad, -clip_value, clip_value)


def count_parameters(model: Module, trainable_only: bool = True) -> int:
    """
    Count number of parameters in model.

    Parameters
    ----------
    model : Module
        Model to count parameters of.
    trainable_only : bool, default=True
        Count only trainable parameters.

    Returns
    -------
    int
        Number of parameters.
    """
    if trainable_only:
        return sum(p.data.size for p in model.parameters() if p.requires_grad)
    else:
        return sum(p.data.size for p in model.parameters())


def model_summary(model: Module, input_shape: Optional[Tuple[int, ...]] = None) -> str:
    """
    Generate model summary.

    Parameters
    ----------
    model : Module
        Model to summarize.
    input_shape : tuple, optional
        Input shape (without batch dimension).

    Returns
    -------
    str
        Model summary string.
    """
    lines = []
    lines.append("=" * 70)
    lines.append(f"Model: {model.__class__.__name__}")
    lines.append("=" * 70)
    lines.append(f"{'Layer':<30} {'Output Shape':<20} {'Params':<15}")
    lines.append("-" * 70)

    total_params = 0
    trainable_params = 0

    for name, module in model.named_modules():
        if name == "":
            continue

        params = sum(p.data.size for p in module.parameters(recurse=False))
        trainable = sum(p.data.size for p in module.parameters(recurse=False) if p.requires_grad)

        total_params += params
        trainable_params += trainable

        layer_name = f"{name} ({module.__class__.__name__})"
        if len(layer_name) > 28:
            layer_name = layer_name[:25] + "..."

        lines.append(f"{layer_name:<30} {'-':<20} {params:>15,}")

    lines.append("=" * 70)
    lines.append(f"Total params: {total_params:,}")
    lines.append(f"Trainable params: {trainable_params:,}")
    lines.append(f"Non-trainable params: {total_params - trainable_params:,}")
    lines.append("=" * 70)

    return "\n".join(lines)


def freeze(model: Module) -> None:
    """
    Freeze all parameters in model.

    Parameters
    ----------
    model : Module
        Model to freeze.
    """
    for p in model.parameters():
        p.requires_grad = False


def unfreeze(model: Module) -> None:
    """
    Unfreeze all parameters in model.

    Parameters
    ----------
    model : Module
        Model to unfreeze.
    """
    for p in model.parameters():
        p.requires_grad = True


def set_requires_grad(model: Module, requires_grad: bool) -> None:
    """
    Set requires_grad for all parameters.

    Parameters
    ----------
    model : Module
        Model to modify.
    requires_grad : bool
        Value for requires_grad.
    """
    for p in model.parameters():
        p.requires_grad = requires_grad


class EarlyStopping:
    """
    Early stopping to stop training when validation loss doesn't improve.

    Parameters
    ----------
    patience : int, default=7
        Number of epochs to wait before stopping.
    min_delta : float, default=0.0
        Minimum change to qualify as improvement.
    mode : str, default='min'
        'min' or 'max'.

    Examples
    --------
    >>> early_stopping = EarlyStopping(patience=10)
    >>> for epoch in range(epochs):
    ...     train(...)
    ...     val_loss = validate(...)
    ...     if early_stopping(val_loss):
    ...         print("Early stopping triggered")
    ...         break
    """

    def __init__(
        self,
        patience: int = 7,
        min_delta: float = 0.0,
        mode: str = 'min',
    ):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.early_stop = False

    def __call__(self, score: float) -> bool:
        """
        Check if training should stop.

        Parameters
        ----------
        score : float
            Current score (e.g., validation loss).

        Returns
        -------
        bool
            True if training should stop.
        """
        if self.mode == 'min':
            is_improvement = self.best_score is None or score < self.best_score - self.min_delta
        else:
            is_improvement = self.best_score is None or score > self.best_score + self.min_delta

        if is_improvement:
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True

        return self.early_stop


class ModelCheckpoint:
    """
    Save model checkpoint when validation metric improves.

    Parameters
    ----------
    path : str
        Path to save checkpoint.
    monitor : str, default='val_loss'
        Metric to monitor.
    mode : str, default='min'
        'min' or 'max'.
    save_best_only : bool, default=True
        Only save when metric improves.

    Examples
    --------
    >>> checkpoint = ModelCheckpoint('best_model.pkl', mode='min')
    >>> for epoch in range(epochs):
    ...     train(...)
    ...     val_loss = validate(...)
    ...     checkpoint(model, val_loss)
    """

    def __init__(
        self,
        path: str,
        monitor: str = 'val_loss',
        mode: str = 'min',
        save_best_only: bool = True,
    ):
        self.path = path
        self.monitor = monitor
        self.mode = mode
        self.save_best_only = save_best_only
        self.best = float('inf') if mode == 'min' else float('-inf')

    def __call__(
        self,
        model: Module,
        current: float,
        optimizer: Optional[Any] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Save checkpoint if metric improved.

        Returns
        -------
        bool
            True if checkpoint was saved.
        """
        if self.mode == 'min':
            is_improvement = current < self.best
        else:
            is_improvement = current > self.best

        if is_improvement or not self.save_best_only:
            self.best = current
            save_model(model, self.path, optimizer=optimizer, extra=extra)
            return True

        return False


def get_device() -> str:
    """
    Get available device.

    Returns
    -------
    str
        'cpu' (GPU support can be added later).
    """
    return 'cpu'


def set_seed(seed: int) -> None:
    """
    Set random seed for reproducibility.

    Parameters
    ----------
    seed : int
        Random seed.
    """
    np.random.seed(seed)


def print_model(model: Module) -> None:
    """
    Print model architecture.

    Parameters
    ----------
    model : Module
        Model to print.
    """
    print(model)
    print(f"\nTotal parameters: {count_parameters(model):,}")


def exponential_moving_average(
    model: Module,
    ema_model: Module,
    decay: float = 0.999,
) -> None:
    """
    Update EMA model parameters.

    Parameters
    ----------
    model : Module
        Source model.
    ema_model : Module
        EMA model to update.
    decay : float, default=0.999
        Decay rate.
    """
    with_name = list(zip(model.parameters(), ema_model.parameters()))
    for p, ema_p in with_name:
        ema_p.data = decay * ema_p.data + (1 - decay) * p.data
