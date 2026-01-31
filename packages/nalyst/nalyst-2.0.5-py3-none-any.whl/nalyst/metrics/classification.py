"""
Classification metrics.

Provides scoring functions for evaluating
classification models.
"""

from __future__ import annotations

from typing import Optional, Literal, List, Dict

import numpy as np


def accuracy_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    normalize: bool = True,
    sample_weight: Optional[np.ndarray] = None,
) -> float:
    """
    Compute accuracy classification score.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth labels.
    y_pred : array-like of shape (n_samples,)
        Predicted labels.
    normalize : bool, default=True
        If True, return fraction. If False, return count.
    sample_weight : array-like, optional
        Sample weights.

    Returns
    -------
    score : float
        Accuracy score.

    Examples
    --------
    >>> from nalyst.metrics import accuracy_score
    >>> y_true = [0, 1, 2, 3]
    >>> y_pred = [0, 2, 1, 3]
    >>> accuracy_score(y_true, y_pred)
    0.5
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    correct = y_true == y_pred

    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)
        score = np.sum(correct * sample_weight)
        if normalize:
            score /= np.sum(sample_weight)
    else:
        score = np.sum(correct)
        if normalize:
            score /= len(y_true)

    return float(score)


def confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    labels: Optional[np.ndarray] = None,
    sample_weight: Optional[np.ndarray] = None,
    normalize: Optional[Literal["true", "pred", "all"]] = None,
) -> np.ndarray:
    """
    Compute confusion matrix.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth labels.
    y_pred : array-like of shape (n_samples,)
        Predicted labels.
    labels : array-like, optional
        List of labels to index the matrix.
    sample_weight : array-like, optional
        Sample weights.
    normalize : {"true", "pred", "all"}, optional
        Normalize over rows, columns, or all.

    Returns
    -------
    cm : ndarray of shape (n_classes, n_classes)
        Confusion matrix.

    Examples
    --------
    >>> from nalyst.metrics import confusion_matrix
    >>> y_true = [0, 0, 1, 1]
    >>> y_pred = [0, 1, 0, 1]
    >>> confusion_matrix(y_true, y_pred)
    array([[1, 1],
           [1, 1]])
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))
    else:
        labels = np.asarray(labels)

    n_labels = len(labels)
    label_to_idx = {label: i for i, label in enumerate(labels)}

    cm = np.zeros((n_labels, n_labels), dtype=float)

    for i, (true, pred) in enumerate(zip(y_true, y_pred)):
        if true in label_to_idx and pred in label_to_idx:
            weight = 1.0 if sample_weight is None else sample_weight[i]
            cm[label_to_idx[true], label_to_idx[pred]] += weight

    if normalize == "true":
        row_sums = cm.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        cm = cm / row_sums
    elif normalize == "pred":
        col_sums = cm.sum(axis=0, keepdims=True)
        col_sums[col_sums == 0] = 1
        cm = cm / col_sums
    elif normalize == "all":
        total = cm.sum()
        if total > 0:
            cm = cm / total

    return cm.astype(int) if normalize is None else cm


def precision_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    labels: Optional[np.ndarray] = None,
    pos_label: int = 1,
    average: Optional[Literal["binary", "micro", "macro", "weighted"]] = "binary",
    sample_weight: Optional[np.ndarray] = None,
    zero_division: float = 0.0,
) -> float:
    """
    Compute precision score.

    Precision = TP / (TP + FP)

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth labels.
    y_pred : array-like of shape (n_samples,)
        Predicted labels.
    labels : array-like, optional
        Labels to include.
    pos_label : int, default=1
        Positive class for binary classification.
    average : {"binary", "micro", "macro", "weighted"}, default="binary"
        Averaging method.
    sample_weight : array-like, optional
        Sample weights.
    zero_division : float, default=0.0
        Value when there are no predictions.

    Returns
    -------
    precision : float
        Precision score.

    Examples
    --------
    >>> from nalyst.metrics import precision_score
    >>> y_true = [0, 1, 1, 0, 1, 1]
    >>> y_pred = [0, 0, 1, 0, 1, 1]
    >>> precision_score(y_true, y_pred)
    1.0
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))
    else:
        labels = np.asarray(labels)

    if average == "binary":
        tp = np.sum((y_true == pos_label) & (y_pred == pos_label))
        fp = np.sum((y_true != pos_label) & (y_pred == pos_label))

        if tp + fp == 0:
            return zero_division
        return tp / (tp + fp)

    elif average == "micro":
        tp_sum = 0
        fp_sum = 0
        for label in labels:
            tp_sum += np.sum((y_true == label) & (y_pred == label))
            fp_sum += np.sum((y_true != label) & (y_pred == label))

        if tp_sum + fp_sum == 0:
            return zero_division
        return tp_sum / (tp_sum + fp_sum)

    elif average in ("macro", "weighted"):
        precisions = []
        supports = []

        for label in labels:
            tp = np.sum((y_true == label) & (y_pred == label))
            fp = np.sum((y_true != label) & (y_pred == label))

            if tp + fp == 0:
                precisions.append(zero_division)
            else:
                precisions.append(tp / (tp + fp))

            supports.append(np.sum(y_true == label))

        if average == "macro":
            return np.mean(precisions)
        else:
            total_support = np.sum(supports)
            if total_support == 0:
                return zero_division
            return np.sum(np.array(precisions) * np.array(supports)) / total_support

    return 0.0


def recall_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    labels: Optional[np.ndarray] = None,
    pos_label: int = 1,
    average: Optional[Literal["binary", "micro", "macro", "weighted"]] = "binary",
    sample_weight: Optional[np.ndarray] = None,
    zero_division: float = 0.0,
) -> float:
    """
    Compute recall score.

    Recall = TP / (TP + FN)

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth labels.
    y_pred : array-like of shape (n_samples,)
        Predicted labels.
    labels : array-like, optional
        Labels to include.
    pos_label : int, default=1
        Positive class for binary classification.
    average : {"binary", "micro", "macro", "weighted"}, default="binary"
        Averaging method.
    sample_weight : array-like, optional
        Sample weights.
    zero_division : float, default=0.0
        Value when there are no positives.

    Returns
    -------
    recall : float
        Recall score.

    Examples
    --------
    >>> from nalyst.metrics import recall_score
    >>> y_true = [0, 1, 1, 0, 1, 1]
    >>> y_pred = [0, 0, 1, 0, 1, 1]
    >>> recall_score(y_true, y_pred)
    0.75
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))
    else:
        labels = np.asarray(labels)

    if average == "binary":
        tp = np.sum((y_true == pos_label) & (y_pred == pos_label))
        fn = np.sum((y_true == pos_label) & (y_pred != pos_label))

        if tp + fn == 0:
            return zero_division
        return tp / (tp + fn)

    elif average == "micro":
        tp_sum = 0
        fn_sum = 0
        for label in labels:
            tp_sum += np.sum((y_true == label) & (y_pred == label))
            fn_sum += np.sum((y_true == label) & (y_pred != label))

        if tp_sum + fn_sum == 0:
            return zero_division
        return tp_sum / (tp_sum + fn_sum)

    elif average in ("macro", "weighted"):
        recalls = []
        supports = []

        for label in labels:
            tp = np.sum((y_true == label) & (y_pred == label))
            fn = np.sum((y_true == label) & (y_pred != label))

            if tp + fn == 0:
                recalls.append(zero_division)
            else:
                recalls.append(tp / (tp + fn))

            supports.append(np.sum(y_true == label))

        if average == "macro":
            return np.mean(recalls)
        else:
            total_support = np.sum(supports)
            if total_support == 0:
                return zero_division
            return np.sum(np.array(recalls) * np.array(supports)) / total_support

    return 0.0


def f1_score(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    labels: Optional[np.ndarray] = None,
    pos_label: int = 1,
    average: Optional[Literal["binary", "micro", "macro", "weighted"]] = "binary",
    sample_weight: Optional[np.ndarray] = None,
    zero_division: float = 0.0,
) -> float:
    """
    Compute F1 score (harmonic mean of precision and recall).

    F1 = 2 * (precision * recall) / (precision + recall)

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth labels.
    y_pred : array-like of shape (n_samples,)
        Predicted labels.
    labels : array-like, optional
        Labels to include.
    pos_label : int, default=1
        Positive class for binary classification.
    average : {"binary", "micro", "macro", "weighted"}, default="binary"
        Averaging method.
    sample_weight : array-like, optional
        Sample weights.
    zero_division : float, default=0.0
        Value when there are no predictions.

    Returns
    -------
    f1 : float
        F1 score.

    Examples
    --------
    >>> from nalyst.metrics import f1_score
    >>> y_true = [0, 1, 1, 0, 1, 1]
    >>> y_pred = [0, 0, 1, 0, 1, 1]
    >>> f1_score(y_true, y_pred)
    0.857...
    """
    prec = precision_score(
        y_true, y_pred, labels=labels, pos_label=pos_label,
        average=average, sample_weight=sample_weight, zero_division=zero_division
    )
    rec = recall_score(
        y_true, y_pred, labels=labels, pos_label=pos_label,
        average=average, sample_weight=sample_weight, zero_division=zero_division
    )

    if prec + rec == 0:
        return zero_division

    return 2 * prec * rec / (prec + rec)


def classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    labels: Optional[np.ndarray] = None,
    target_names: Optional[List[str]] = None,
    sample_weight: Optional[np.ndarray] = None,
    digits: int = 2,
    output_dict: bool = False,
    zero_division: float = 0.0,
) -> str:
    """
    Build a text report of classification metrics.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth labels.
    y_pred : array-like of shape (n_samples,)
        Predicted labels.
    labels : array-like, optional
        Labels to include.
    target_names : list of str, optional
        Display names for labels.
    sample_weight : array-like, optional
        Sample weights.
    digits : int, default=2
        Decimal places.
    output_dict : bool, default=False
        Return dict instead of string.
    zero_division : float, default=0.0
        Value when there are no predictions.

    Returns
    -------
    report : str or dict
        Classification report.

    Examples
    --------
    >>> from nalyst.metrics import classification_report
    >>> y_true = [0, 0, 1, 1]
    >>> y_pred = [0, 1, 1, 1]
    >>> print(classification_report(y_true, y_pred))
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if labels is None:
        labels = np.unique(np.concatenate([y_true, y_pred]))
    else:
        labels = np.asarray(labels)

    if target_names is None:
        target_names = [str(l) for l in labels]

    # Compute per-class metrics
    report_dict = {}

    for label, name in zip(labels, target_names):
        prec = precision_score(
            y_true, y_pred, pos_label=label, average="binary",
            zero_division=zero_division
        )
        rec = recall_score(
            y_true, y_pred, pos_label=label, average="binary",
            zero_division=zero_division
        )
        f1 = f1_score(
            y_true, y_pred, pos_label=label, average="binary",
            zero_division=zero_division
        )
        support = np.sum(y_true == label)

        report_dict[name] = {
            "precision": prec,
            "recall": rec,
            "f1-score": f1,
            "support": int(support),
        }

    # Add aggregates
    report_dict["accuracy"] = {
        "precision": 0,
        "recall": 0,
        "f1-score": accuracy_score(y_true, y_pred),
        "support": len(y_true),
    }

    report_dict["macro avg"] = {
        "precision": precision_score(
            y_true, y_pred, labels=labels, average="macro",
            zero_division=zero_division
        ),
        "recall": recall_score(
            y_true, y_pred, labels=labels, average="macro",
            zero_division=zero_division
        ),
        "f1-score": f1_score(
            y_true, y_pred, labels=labels, average="macro",
            zero_division=zero_division
        ),
        "support": len(y_true),
    }

    report_dict["weighted avg"] = {
        "precision": precision_score(
            y_true, y_pred, labels=labels, average="weighted",
            zero_division=zero_division
        ),
        "recall": recall_score(
            y_true, y_pred, labels=labels, average="weighted",
            zero_division=zero_division
        ),
        "f1-score": f1_score(
            y_true, y_pred, labels=labels, average="weighted",
            zero_division=zero_division
        ),
        "support": len(y_true),
    }

    if output_dict:
        return report_dict

    # Format as string
    headers = ["", "precision", "recall", "f1-score", "support"]
    width = max(len(name) for name in target_names) + 2

    lines = []
    lines.append(f"{headers[0]:<{width}} {headers[1]:>10} {headers[2]:>10} {headers[3]:>10} {headers[4]:>10}")
    lines.append("")

    for name in target_names:
        row = report_dict[name]
        lines.append(
            f"{name:<{width}} "
            f"{row['precision']:>10.{digits}f} "
            f"{row['recall']:>10.{digits}f} "
            f"{row['f1-score']:>10.{digits}f} "
            f"{row['support']:>10}"
        )

    lines.append("")

    for avg in ["accuracy", "macro avg", "weighted avg"]:
        row = report_dict[avg]
        if avg == "accuracy":
            lines.append(
                f"{avg:<{width}} "
                f"{'':>10} "
                f"{'':>10} "
                f"{row['f1-score']:>10.{digits}f} "
                f"{row['support']:>10}"
            )
        else:
            lines.append(
                f"{avg:<{width}} "
                f"{row['precision']:>10.{digits}f} "
                f"{row['recall']:>10.{digits}f} "
                f"{row['f1-score']:>10.{digits}f} "
                f"{row['support']:>10}"
            )

    return "\n".join(lines)


def roc_auc_score(
    y_true: np.ndarray,
    y_score: np.ndarray,
    *,
    average: Literal["micro", "macro", "weighted"] = "macro",
    sample_weight: Optional[np.ndarray] = None,
    multi_class: Literal["raise", "ovr", "ovo"] = "raise",
) -> float:
    """
    Compute Area Under the ROC Curve (AUC).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        True binary labels.
    y_score : array-like of shape (n_samples,) or (n_samples, n_classes)
        Probability estimates or decision scores.
    average : {"micro", "macro", "weighted"}, default="macro"
        Averaging method for multiclass.
    sample_weight : array-like, optional
        Sample weights.
    multi_class : {"raise", "ovr", "ovo"}, default="raise"
        Multiclass strategy.

    Returns
    -------
    auc : float
        Area Under the Curve.

    Examples
    --------
    >>> from nalyst.metrics import roc_auc_score
    >>> y_true = [0, 0, 1, 1]
    >>> y_score = [0.1, 0.4, 0.35, 0.8]
    >>> roc_auc_score(y_true, y_score)
    0.75
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)

    if y_score.ndim == 1:
        # Binary classification
        # Compute AUC using trapezoidal rule
        desc_idx = np.argsort(y_score)[::-1]
        y_true_sorted = y_true[desc_idx]

        # Compute TPR and FPR
        n_pos = np.sum(y_true == 1)
        n_neg = np.sum(y_true == 0)

        if n_pos == 0 or n_neg == 0:
            return 0.5

        tpr = np.cumsum(y_true_sorted == 1) / n_pos
        fpr = np.cumsum(y_true_sorted == 0) / n_neg

        # Add origin
        tpr = np.concatenate([[0], tpr])
        fpr = np.concatenate([[0], fpr])

        # Compute AUC with trapezoidal rule
        auc = np.trapz(tpr, fpr)

        return float(auc)

    else:
        # Multiclass
        classes = np.unique(y_true)

        if multi_class == "raise":
            if len(classes) > 2:
                raise ValueError("multi_class must be set for multiclass")

        aucs = []
        supports = []

        for i, cls in enumerate(classes):
            binary_true = (y_true == cls).astype(int)
            cls_score = y_score[:, i]

            auc = roc_auc_score(binary_true, cls_score)
            aucs.append(auc)
            supports.append(np.sum(y_true == cls))

        if average == "macro":
            return np.mean(aucs)
        elif average == "weighted":
            return np.sum(np.array(aucs) * np.array(supports)) / np.sum(supports)
        else:  # micro
            # Not strictly correct, but simplified
            return np.mean(aucs)


def log_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    eps: float = 1e-15,
    normalize: bool = True,
    sample_weight: Optional[np.ndarray] = None,
    labels: Optional[np.ndarray] = None,
) -> float:
    """
    Compute log loss (cross-entropy loss).

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        True labels.
    y_pred : array-like of shape (n_samples,) or (n_samples, n_classes)
        Predicted probabilities.
    eps : float, default=1e-15
        Small value to avoid log(0).
    normalize : bool, default=True
        Return mean log loss.
    sample_weight : array-like, optional
        Sample weights.
    labels : array-like, optional
        Labels.

    Returns
    -------
    loss : float
        Log loss.

    Examples
    --------
    >>> from nalyst.metrics import log_loss
    >>> y_true = [0, 0, 1, 1]
    >>> y_pred = [[0.9, 0.1], [0.8, 0.2], [0.3, 0.7], [0.01, 0.99]]
    >>> log_loss(y_true, y_pred)
    0.173...
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    # Clip predictions
    y_pred = np.clip(y_pred, eps, 1 - eps)

    if y_pred.ndim == 1:
        # Binary classification
        loss = -(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
    else:
        # Multiclass
        n_samples = len(y_true)
        if labels is None:
            labels = np.unique(y_true)

        # One-hot encode y_true
        y_true_onehot = np.zeros((n_samples, len(labels)))
        for i, label in enumerate(labels):
            y_true_onehot[y_true == label, i] = 1

        loss = -np.sum(y_true_onehot * np.log(y_pred), axis=1)

    if sample_weight is not None:
        loss = loss * sample_weight

    if normalize:
        if sample_weight is not None:
            return np.sum(loss) / np.sum(sample_weight)
        return np.mean(loss)

    return np.sum(loss)
