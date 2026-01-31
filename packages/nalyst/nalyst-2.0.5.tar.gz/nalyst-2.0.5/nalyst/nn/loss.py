"""
Loss functions for neural networks.
"""

from __future__ import annotations

from typing import Optional
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.tensor import Tensor


class Loss(Module):
    """Base class for loss functions."""

    def __init__(self, reduction: str = 'mean'):
        super().__init__()
        if reduction not in ('none', 'mean', 'sum'):
            raise ValueError(f"Invalid reduction: {reduction}")
        self.reduction = reduction

    def _reduce(self, loss: Tensor) -> Tensor:
        """Apply reduction to loss."""
        if self.reduction == 'none':
            return loss
        elif self.reduction == 'mean':
            return loss.mean()
        else:
            return loss.sum()


class MSELoss(Loss):
    """
    Mean Squared Error loss.

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').

    Examples
    --------
    >>> loss_fn = nn.MSELoss()
    >>> loss = loss_fn(predictions, targets)
    """

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        diff = input - target
        loss = diff * diff
        return self._reduce(loss)


class L1Loss(Loss):
    """
    Mean Absolute Error loss.

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').
    """

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        loss = (input - target).abs()
        return self._reduce(loss)


class SmoothL1Loss(Loss):
    """
    Smooth L1 Loss (Huber Loss).

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').
    beta : float, default=1.0
        Threshold for smooth transition.
    """

    def __init__(self, reduction: str = 'mean', beta: float = 1.0):
        super().__init__(reduction)
        self.beta = beta

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        diff = input - target
        abs_diff = diff.abs()

        # Quadratic when abs_diff < beta, linear otherwise
        loss_data = np.where(
            abs_diff.data < self.beta,
            0.5 * diff.data ** 2 / self.beta,
            abs_diff.data - 0.5 * self.beta
        )

        loss = Tensor(
            loss_data,
            requires_grad=input.requires_grad or target.requires_grad,
            _children=(input, target),
            _op="smooth_l1",
        )

        def _backward():
            if loss.grad is None:
                return

            grad = np.where(
                np.abs(diff.data) < self.beta,
                diff.data / self.beta,
                np.sign(diff.data)
            ) * loss.grad

            if input.requires_grad:
                if input.grad is None:
                    input.grad = np.zeros_like(input.data)
                input.grad += grad

            if target.requires_grad:
                if target.grad is None:
                    target.grad = np.zeros_like(target.data)
                target.grad -= grad

        loss._backward = _backward
        return self._reduce(loss)


class CrossEntropyLoss(Loss):
    """
    Cross Entropy Loss (combines LogSoftmax and NLLLoss).

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').
    weight : Tensor, optional
        Class weights.
    ignore_index : int, default=-100
        Index to ignore.
    label_smoothing : float, default=0.0
        Label smoothing factor.

    Examples
    --------
    >>> loss_fn = nn.CrossEntropyLoss()
    >>> logits = model(x)  # (batch, num_classes)
    >>> loss = loss_fn(logits, labels)  # labels: (batch,)
    """

    def __init__(
        self,
        reduction: str = 'mean',
        weight: Optional[Tensor] = None,
        ignore_index: int = -100,
        label_smoothing: float = 0.0,
    ):
        super().__init__(reduction)
        self.weight = weight
        self.ignore_index = ignore_index
        self.label_smoothing = label_smoothing

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        """
        Compute cross entropy loss.

        Parameters
        ----------
        input : Tensor
            Logits of shape (N, C) or (N, C, ...).
        target : Tensor
            Target indices of shape (N,) or (N, ...).

        Returns
        -------
        Tensor
            Loss value.
        """
        # Reshape if needed (N, C, ...) -> (N*..., C)
        if input.data.ndim > 2:
            N, C = input.shape[0], input.shape[1]
            input_reshaped = input.data.reshape(N, C, -1).transpose(0, 2, 1).reshape(-1, C)
            target_flat = target.data.flatten()
        else:
            input_reshaped = input.data
            target_flat = target.data.flatten().astype(np.int64)

        num_samples = input_reshaped.shape[0]
        num_classes = input_reshaped.shape[1]

        # Log softmax
        max_val = np.max(input_reshaped, axis=-1, keepdims=True)
        exp_x = np.exp(input_reshaped - max_val)
        log_sum_exp = np.log(np.sum(exp_x, axis=-1, keepdims=True))
        log_probs = input_reshaped - max_val - log_sum_exp

        # Gather log probs for targets
        valid_mask = target_flat != self.ignore_index
        target_flat = np.clip(target_flat, 0, num_classes - 1)

        nll = -log_probs[np.arange(num_samples), target_flat]

        # Apply label smoothing
        if self.label_smoothing > 0:
            smooth_loss = -log_probs.sum(axis=-1) / num_classes
            nll = (1 - self.label_smoothing) * nll + self.label_smoothing * smooth_loss

        # Apply class weights
        if self.weight is not None:
            nll = nll * self.weight.data[target_flat]

        # Mask ignored indices
        nll = np.where(valid_mask, nll, 0.0)

        loss = Tensor(
            nll,
            requires_grad=input.requires_grad,
            _children=(input,),
            _op="cross_entropy",
        )

        def _backward():
            if not input.requires_grad or loss.grad is None:
                return

            # Gradient of cross entropy = softmax - one_hot(target)
            probs = np.exp(log_probs)
            grad = probs.copy()
            grad[np.arange(num_samples), target_flat] -= 1

            if self.label_smoothing > 0:
                grad = (1 - self.label_smoothing) * grad + \
                       self.label_smoothing * (probs - 1 / num_classes)

            if self.weight is not None:
                grad = grad * self.weight.data[target_flat][:, np.newaxis]

            grad = grad * valid_mask[:, np.newaxis]

            # Handle reduction gradient
            if self.reduction == 'mean':
                grad = grad / valid_mask.sum()

            if input.data.ndim > 2:
                N, C = input.shape[0], input.shape[1]
                spatial = input.shape[2:]
                grad = grad.reshape(N, -1, C).transpose(0, 2, 1).reshape(input.shape)

            if input.grad is None:
                input.grad = np.zeros_like(input.data)
            input.grad += grad * (loss.grad if np.isscalar(loss.grad) else np.ones_like(nll))

        loss._backward = _backward
        return self._reduce(loss)


class NLLLoss(Loss):
    """
    Negative Log Likelihood Loss.

    Expects log probabilities as input.

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').
    weight : Tensor, optional
        Class weights.
    ignore_index : int, default=-100
        Index to ignore.
    """

    def __init__(
        self,
        reduction: str = 'mean',
        weight: Optional[Tensor] = None,
        ignore_index: int = -100,
    ):
        super().__init__(reduction)
        self.weight = weight
        self.ignore_index = ignore_index

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        """
        Compute NLL loss.

        Parameters
        ----------
        input : Tensor
            Log probabilities of shape (N, C).
        target : Tensor
            Target indices of shape (N,).
        """
        num_samples = input.shape[0]
        target_flat = target.data.flatten().astype(np.int64)

        valid_mask = target_flat != self.ignore_index
        target_flat = np.clip(target_flat, 0, input.shape[1] - 1)

        nll = -input.data[np.arange(num_samples), target_flat]

        if self.weight is not None:
            nll = nll * self.weight.data[target_flat]

        nll = np.where(valid_mask, nll, 0.0)

        loss = Tensor(
            nll,
            requires_grad=input.requires_grad,
            _children=(input,),
            _op="nll",
        )

        return self._reduce(loss)


class BCELoss(Loss):
    """
    Binary Cross Entropy Loss.

    Expects probabilities as input.

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').
    weight : Tensor, optional
        Sample weights.

    Examples
    --------
    >>> loss_fn = nn.BCELoss()
    >>> probs = model(x).sigmoid()
    >>> loss = loss_fn(probs, labels)
    """

    def __init__(
        self,
        reduction: str = 'mean',
        weight: Optional[Tensor] = None,
    ):
        super().__init__(reduction)
        self.weight = weight

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        eps = 1e-7
        input_clamped = np.clip(input.data, eps, 1 - eps)

        bce = -(target.data * np.log(input_clamped) +
                (1 - target.data) * np.log(1 - input_clamped))

        if self.weight is not None:
            bce = bce * self.weight.data

        loss = Tensor(
            bce,
            requires_grad=input.requires_grad,
            _children=(input, target),
            _op="bce",
        )

        def _backward():
            if not input.requires_grad or loss.grad is None:
                return

            grad = (input_clamped - target.data) / (input_clamped * (1 - input_clamped) + eps)

            if self.weight is not None:
                grad = grad * self.weight.data

            if input.grad is None:
                input.grad = np.zeros_like(input.data)
            input.grad += grad * loss.grad

        loss._backward = _backward
        return self._reduce(loss)


class BCEWithLogitsLoss(Loss):
    """
    Binary Cross Entropy with Logits (numerically stable).

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').
    weight : Tensor, optional
        Sample weights.
    pos_weight : Tensor, optional
        Positive class weight.

    Examples
    --------
    >>> loss_fn = nn.BCEWithLogitsLoss()
    >>> logits = model(x)
    >>> loss = loss_fn(logits, labels)
    """

    def __init__(
        self,
        reduction: str = 'mean',
        weight: Optional[Tensor] = None,
        pos_weight: Optional[Tensor] = None,
    ):
        super().__init__(reduction)
        self.weight = weight
        self.pos_weight = pos_weight

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        # Numerically stable BCE with logits
        # max(x, 0) - x * z + log(1 + exp(-|x|))
        x = input.data
        z = target.data

        if self.pos_weight is not None:
            p = self.pos_weight.data
            log_weight = 1 + (p - 1) * z
            bce = (1 - z) * x + log_weight * (np.log1p(np.exp(-np.abs(x))) + np.maximum(-x, 0))
        else:
            bce = np.maximum(x, 0) - x * z + np.log1p(np.exp(-np.abs(x)))

        if self.weight is not None:
            bce = bce * self.weight.data

        loss = Tensor(
            bce,
            requires_grad=input.requires_grad,
            _children=(input, target),
            _op="bce_logits",
        )

        def _backward():
            if not input.requires_grad or loss.grad is None:
                return

            sigmoid_x = 1 / (1 + np.exp(-x))

            if self.pos_weight is not None:
                p = self.pos_weight.data
                grad = (1 - z) + ((p - 1) * z + 1) * sigmoid_x - p * z
            else:
                grad = sigmoid_x - z

            if self.weight is not None:
                grad = grad * self.weight.data

            if input.grad is None:
                input.grad = np.zeros_like(input.data)
            input.grad += grad * loss.grad

        loss._backward = _backward
        return self._reduce(loss)


class HuberLoss(SmoothL1Loss):
    """
    Huber Loss (alias for SmoothL1Loss).

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum').
    delta : float, default=1.0
        Threshold.
    """

    def __init__(self, reduction: str = 'mean', delta: float = 1.0):
        super().__init__(reduction, beta=delta)


class KLDivLoss(Loss):
    """
    Kullback-Leibler Divergence Loss.

    Parameters
    ----------
    reduction : str, default='mean'
        Reduction mode ('none', 'mean', 'sum', 'batchmean').
    log_target : bool, default=False
        Whether target is in log space.
    """

    def __init__(
        self,
        reduction: str = 'mean',
        log_target: bool = False,
    ):
        if reduction == 'batchmean':
            super().__init__('sum')
            self._batchmean = True
        else:
            super().__init__(reduction)
            self._batchmean = False
        self.log_target = log_target

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        """
        Compute KL divergence.

        Parameters
        ----------
        input : Tensor
            Log probabilities.
        target : Tensor
            Target probabilities or log probabilities.
        """
        if self.log_target:
            kl = np.exp(target.data) * (target.data - input.data)
        else:
            kl = target.data * (np.log(target.data + 1e-8) - input.data)

        loss = Tensor(
            kl,
            requires_grad=input.requires_grad,
            _children=(input, target),
            _op="kl_div",
        )

        result = self._reduce(loss)

        if self._batchmean:
            return result / input.shape[0]
        return result


class CosineEmbeddingLoss(Loss):
    """
    Cosine Embedding Loss.

    Parameters
    ----------
    margin : float, default=0.0
        Margin value.
    reduction : str, default='mean'
        Reduction mode.
    """

    def __init__(self, margin: float = 0.0, reduction: str = 'mean'):
        super().__init__(reduction)
        self.margin = margin

    def forward(self, x1: Tensor, x2: Tensor, target: Tensor) -> Tensor:
        """
        Compute cosine embedding loss.

        Parameters
        ----------
        x1, x2 : Tensor
            Input embeddings.
        target : Tensor
            Labels (+1 or -1).
        """
        # Cosine similarity
        norm1 = np.linalg.norm(x1.data, axis=-1, keepdims=True)
        norm2 = np.linalg.norm(x2.data, axis=-1, keepdims=True)
        cos_sim = np.sum(x1.data * x2.data, axis=-1) / (norm1.squeeze() * norm2.squeeze() + 1e-8)

        y = target.data

        # Loss: 1 - cos(x1, x2) if y == 1
        #       max(0, cos(x1, x2) - margin) if y == -1
        loss_data = np.where(
            y == 1,
            1 - cos_sim,
            np.maximum(0, cos_sim - self.margin)
        )

        loss = Tensor(loss_data, requires_grad=x1.requires_grad or x2.requires_grad)
        return self._reduce(loss)


class TripletMarginLoss(Loss):
    """
    Triplet Margin Loss.

    Parameters
    ----------
    margin : float, default=1.0
        Margin value.
    p : int, default=2
        Norm degree.
    reduction : str, default='mean'
        Reduction mode.
    """

    def __init__(
        self,
        margin: float = 1.0,
        p: int = 2,
        reduction: str = 'mean',
    ):
        super().__init__(reduction)
        self.margin = margin
        self.p = p

    def forward(self, anchor: Tensor, positive: Tensor, negative: Tensor) -> Tensor:
        """
        Compute triplet margin loss.

        Parameters
        ----------
        anchor : Tensor
            Anchor samples.
        positive : Tensor
            Positive samples.
        negative : Tensor
            Negative samples.
        """
        d_pos = np.linalg.norm(anchor.data - positive.data, ord=self.p, axis=-1)
        d_neg = np.linalg.norm(anchor.data - negative.data, ord=self.p, axis=-1)

        loss_data = np.maximum(0, d_pos - d_neg + self.margin)

        loss = Tensor(
            loss_data,
            requires_grad=anchor.requires_grad or positive.requires_grad or negative.requires_grad,
        )
        return self._reduce(loss)


class FocalLoss(Loss):
    """
    Focal Loss for imbalanced classification.

    Parameters
    ----------
    alpha : float, default=0.25
        Weighting factor.
    gamma : float, default=2.0
        Focusing parameter.
    reduction : str, default='mean'
        Reduction mode.
    """

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = 'mean',
    ):
        super().__init__(reduction)
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, input: Tensor, target: Tensor) -> Tensor:
        """
        Compute focal loss.

        Parameters
        ----------
        input : Tensor
            Logits of shape (N, C).
        target : Tensor
            Target indices of shape (N,).
        """
        # Softmax probabilities
        exp_x = np.exp(input.data - np.max(input.data, axis=-1, keepdims=True))
        probs = exp_x / np.sum(exp_x, axis=-1, keepdims=True)

        # Get probability of true class
        num_samples = input.shape[0]
        target_flat = target.data.flatten().astype(np.int64)
        p_t = probs[np.arange(num_samples), target_flat]

        # Focal loss: -alpha * (1 - p_t)^gamma * log(p_t)
        focal_weight = self.alpha * (1 - p_t) ** self.gamma
        loss_data = -focal_weight * np.log(p_t + 1e-8)

        loss = Tensor(
            loss_data,
            requires_grad=input.requires_grad,
            _children=(input,),
            _op="focal",
        )

        return self._reduce(loss)


class CTCLoss(Loss):
    """
    Connectionist Temporal Classification Loss.

    Parameters
    ----------
    blank : int, default=0
        Blank label index.
    reduction : str, default='mean'
        Reduction mode.
    zero_infinity : bool, default=False
        Replace inf/nan losses with zero.
    """

    def __init__(
        self,
        blank: int = 0,
        reduction: str = 'mean',
        zero_infinity: bool = False,
    ):
        super().__init__(reduction)
        self.blank = blank
        self.zero_infinity = zero_infinity

    def forward(
        self,
        log_probs: Tensor,
        targets: Tensor,
        input_lengths: Tensor,
        target_lengths: Tensor,
    ) -> Tensor:
        """
        Compute CTC loss.

        Parameters
        ----------
        log_probs : Tensor
            Log probabilities of shape (T, N, C).
        targets : Tensor
            Target sequences.
        input_lengths : Tensor
            Input sequence lengths.
        target_lengths : Tensor
            Target sequence lengths.
        """
        # Simplified CTC implementation
        # For full implementation, use forward-backward algorithm
        T, N, C = log_probs.shape

        losses = np.zeros(N)

        for i in range(N):
            t_len = int(input_lengths.data[i])
            s_len = int(target_lengths.data[i])

            if s_len == 0:
                continue

            # Simple approximation: sum of log probs for target sequence
            target_seq = targets.data[i, :s_len].astype(np.int64)
            loss = 0
            for t, label in enumerate(target_seq):
                if t < t_len:
                    loss -= log_probs.data[t, i, label]

            losses[i] = loss / s_len if s_len > 0 else 0

        if self.zero_infinity:
            losses = np.where(np.isfinite(losses), losses, 0)

        loss = Tensor(losses, requires_grad=log_probs.requires_grad)
        return self._reduce(loss)
