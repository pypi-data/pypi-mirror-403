from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

from .metrics import art_weights_from_f1, per_class_f1

ArrayLike = Union[np.ndarray, Sequence[Sequence[float]]]
LabelLike = Union[np.ndarray, Sequence[int]]
LoaderKwargs = Mapping[str, Any]


class ARTDataset(Dataset[Dict[str, torch.Tensor]]):
    """
    A PyTorch Dataset that optionally applies ART resampling on tabular features.

    When `enable_art=False`, this behaves like a normal dataset:
    it returns the original (X, y) without any resampling.

    When `enable_art=True`, each (re)build creates a training set using:
    1) A "balanced" portion: `round(c * N)` samples drawn uniformly from all samples (no replacement).
    2) A remaining portion: `round(w_i * (N - balanced))` samples per class i,
       drawn from that class with replacement.

    This matches the core behavior in your PyTorch notebook.
    """

    def __init__(
        self,
        X: ArrayLike,
        y: LabelLike,
        c: float = 0.3,
        cls_weights: Optional[Sequence[float]] = None,
        seed: int = 8719183,
        enable_art: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        X
            Feature matrix with shape (n_samples, n_features).
        y
            Class labels with shape (n_samples,).
        c
            Fraction of samples used for the uniform "balanced" portion when ART is enabled.
            Typical range is [0.0, 1.0].
        cls_weights
            Per-class weights (must sum to 1.0). Required only when `enable_art=True`.
            These weights control how many samples are drawn for each class in the
            remaining portion of the ART dataset.
        seed
            Random seed used for sampling when ART is enabled.
        enable_art
            If False, disable ART and return the original dataset without resampling.
        """
        self.X_base: np.ndarray = np.asarray(X)
        self.y_base: np.ndarray = np.asarray(y).astype(int)
        self.enable_art: bool = bool(enable_art)

        self.X: np.ndarray
        self.y: np.ndarray
        self.c: float = float(c)
        self.cls_weights: Optional[np.ndarray] = None
        self.rng: Optional[np.random.Generator] = None

        if not self.enable_art:
            self.X = self.X_base
            self.y = self.y_base
            return

        if cls_weights is None:
            raise ValueError("Require class weights for ART")
        cls_weights_array = np.asarray(cls_weights, dtype=np.float64)
        if not np.isclose(np.sum(cls_weights_array), 1.0):
            raise ValueError(f"class_weights must sum to 1.0, but got {np.sum(cls_weights_array):.4f}")

        num_classes = len(np.unique(self.y_base))
        if len(cls_weights_array) != num_classes:
            raise ValueError("Length of class weights do not match the number of unique target variables")

        self.cls_weights = cls_weights_array
        self.rng = np.random.default_rng(seed)

        self._build()

    def _build(self) -> None:
        if self.cls_weights is None or self.rng is None:
            raise ValueError("ART is enabled but cls_weights or rng is not initialized")

        num_samples = int(self.X_base.shape[0])
        num_balanced_samples = int(round(self.c * num_samples))

        all_indices = np.arange(num_samples)
        if num_balanced_samples > 0:
            chosen_indices = self.rng.choice(all_indices, size=num_balanced_samples, replace=False)
            resampled_X = self.X_base[chosen_indices]
            resampled_y = self.y_base[chosen_indices]
        else:
            resampled_X = self.X_base[:0]
            resampled_y = self.y_base[:0]

        remaining_samples = num_samples - num_balanced_samples

        for class_index in range(len(self.cls_weights)):
            num_class_samples = int(round(float(self.cls_weights[class_index]) * remaining_samples))
            if num_class_samples <= 0:
                continue

            class_indices = np.where(self.y_base == class_index)[0]
            chosen_class_indices = self.rng.choice(class_indices, size=num_class_samples, replace=True)

            class_X = self.X_base[chosen_class_indices]
            class_y = self.y_base[chosen_class_indices]

            resampled_X = np.concatenate((resampled_X, class_X), axis=0)
            resampled_y = np.concatenate((resampled_y, class_y), axis=0)

        self.X = resampled_X
        self.y = resampled_y

    def refresh(self, cls_weights: Sequence[float]) -> None:
        """
        Refresh the ART dataset with new class weights.

        This rebuilds the resampled training set. If ART is disabled, this is a no-op.

        Parameters
        ----------
        cls_weights
            New per-class weights (must sum to 1.0). Length must match the number of classes.
        """
        if not self.enable_art:
            return

        if self.rng is None:
            raise ValueError("ART is enabled but rng is not initialized")

        cls_weights_array = np.asarray(cls_weights, dtype=np.float64)
        if not np.isclose(np.sum(cls_weights_array), 1.0):
            raise ValueError(f"class_weights must sum to 1.0, but got {np.sum(cls_weights_array):.4f}")

        num_classes = len(np.unique(self.y_base))
        if len(cls_weights_array) != num_classes:
            raise ValueError("Length of class weights do not match the number of unique target variables")

        self.cls_weights = cls_weights_array
        self._build()

    @staticmethod
    def should_refresh(epoch_number: int, bf: Optional[int]) -> bool:
        """
        Decide whether to refresh ART weights at a given epoch.

        Parameters
        ----------
        epoch_number
            Current epoch number (typically 1-based).
        bf
            Refresh frequency. If bf is None or 0, never refresh.
            If bf is k, refresh when epoch_number % k == 0.

        Returns
        -------
        bool
            True if you should refresh at this epoch, else False.
        """
        return bool(bf) and (epoch_number % int(bf) == 0)

    def __len__(self) -> int:
        return int(self.X.shape[0])

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        x_tensor = torch.tensor(self.X[idx], dtype=torch.float32)
        y_tensor = torch.tensor(self.y[idx], dtype=torch.long)
        return {"x": x_tensor, "y": y_tensor}


def art_refresh_dataset_from_f1_scores(
    art_dataset: ARTDataset,
    f1: Sequence[float],
    train_loader_kwargs: LoaderKwargs,
) -> Tuple[DataLoader, np.ndarray, np.ndarray]:
    """
    Refresh an ART training dataset using precomputed per-class F1 scores.

    This is useful when you already have per-class F1 values and want to:
    - convert them into ART weights using: weight_i ∝ (1 - f1_i)
    - rebuild the ART dataset
    - rebuild the DataLoader

    Parameters
    ----------
    art_dataset
        The training dataset created with `enable_art=True`.
    f1
        Per-class F1 scores, shape (n_classes,).
    train_loader_kwargs
        Keyword arguments for `torch.utils.data.DataLoader`, such as
        {"batch_size": 256, "shuffle": True, "drop_last": True}.

    Returns
    -------
    (train_loader, class_weights, f1)
        train_loader
            A new DataLoader created from the refreshed dataset.
        class_weights
            Normalized ART weights computed from F1.
        f1
            The same F1 values as a NumPy array (for convenience).
    """
    f1_array = np.asarray(f1, dtype=np.float64)
    class_weights = art_weights_from_f1(f1_array)
    art_dataset.refresh(class_weights)
    train_loader = DataLoader(art_dataset, **dict(train_loader_kwargs))
    return train_loader, class_weights, f1_array


def art_refresh_dataset_from_predictions(
    art_dataset: ARTDataset,
    y_true: Sequence[int],
    y_pred: Sequence[int],
    n_classes: int,
    train_loader_kwargs: LoaderKwargs,
) -> Tuple[DataLoader, np.ndarray, np.ndarray]:
    """
    Refresh an ART training dataset using validation predictions.

    This computes per-class F1 using sklearn, then computes ART weights as:
    - scores_i = 1 - f1_i
    - weights = scores / sum(scores)

    Then it rebuilds the ART dataset and returns a new DataLoader.

    Parameters
    ----------
    art_dataset
        The training dataset created with `enable_art=True`.
    y_true
        True labels from the validation set.
    y_pred
        Predicted labels from the validation set.
    n_classes
        Number of classes.
    train_loader_kwargs
        Keyword arguments for `torch.utils.data.DataLoader`, such as
        {"batch_size": 256, "shuffle": True, "drop_last": True}.

    Returns
    -------
    (train_loader, class_weights, f1)
        train_loader
            A new DataLoader created from the refreshed dataset.
        class_weights
            Normalized ART weights computed from F1.
        f1
            Per-class F1 scores as a NumPy array.
    """
    f1_array = per_class_f1(y_true, y_pred, n_classes)
    class_weights = art_weights_from_f1(f1_array)
    art_dataset.refresh(class_weights)
    train_loader = DataLoader(art_dataset, **dict(train_loader_kwargs))
    return train_loader, class_weights, f1_array
