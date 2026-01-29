from __future__ import annotations

from typing import Sequence, Union

import numpy as np
from sklearn.metrics import f1_score

ArrayLike1D = Union[np.ndarray, Sequence[float]]
IntArrayLike1D = Union[np.ndarray, Sequence[int]]


def art_weights_from_f1(per_class_f1: ArrayLike1D) -> np.ndarray:
    """
    Convert per-class F1 scores into ART sampling weights.

    ART increases sampling for classes with lower F1.
    It does this by computing:
    - score_i = 1 - f1_i
    - weight_i = score_i / sum(score)

    If all F1 values are 1.0 (perfect), it returns uniform weights.

    Parameters
    ----------
    per_class_f1
        Per-class F1 scores, shape (n_classes,).

    Returns
    -------
    np.ndarray
        Normalized ART weights, shape (n_classes,), dtype float64.
        Always sums to 1.0.
    """
    f1_array = np.asarray(per_class_f1, dtype=np.float64)
    scores = 1.0 - f1_array
    score_sum = float(np.sum(scores))

    if score_sum <= 0.0:
        return np.ones_like(scores, dtype=np.float64) / float(scores.size)

    return scores / score_sum


def per_class_f1(
    y_true: IntArrayLike1D,
    y_pred: IntArrayLike1D,
    n_classes: int,
) -> np.ndarray:
    """
    Compute per-class F1 scores using sklearn.

    This returns one F1 score per class label in [0, n_classes - 1].
    Classes that do not appear in y_true are assigned F1=0 via `zero_division=0`.

    Parameters
    ----------
    y_true
        True labels, shape (n_samples,).
    y_pred
        Predicted labels, shape (n_samples,).
    n_classes
        Number of classes. This controls which labels are included.

    Returns
    -------
    np.ndarray
        Per-class F1 scores, shape (n_classes,), dtype float64.
    """
    true_labels = np.asarray(y_true, dtype=int).reshape(-1)
    pred_labels = np.asarray(y_pred, dtype=int).reshape(-1)

    class_labels = np.arange(int(n_classes), dtype=int)
    f1_values = f1_score(
        true_labels,
        pred_labels,
        labels=class_labels,
        average=None,
        zero_division=0,
    )
    return np.asarray(f1_values, dtype=np.float64)
