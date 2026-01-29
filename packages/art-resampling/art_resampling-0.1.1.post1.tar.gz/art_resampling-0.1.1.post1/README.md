# art-resampling

`art-resampling` is a PyTorch utility for Adaptive Resampling-Based Training for Imbalanced Datasets (ART).

This repository contains the reference implementation used in the paper: [Adaptive Resampling for Imbalanced Datasets (ART)](https://arxiv.org/abs/2509.00955)

## Install

```bash
pip install art-resampling
````

## Quick start

Run the example script:

```bash
python examples/tabular_multiclass.py
```

## Library API

### `ARTDataset`

A PyTorch `Dataset` that can act as:

* a normal dataset (`enable_art=False`), or
* an ART-resampled dataset (`enable_art=True`).

```python
from art_resampling import ARTDataset

train_dataset = ARTDataset(
    X_train,
    y_train,
    enable_art=True,
    c=0.3,
    cls_weights=initial_class_weights,
    seed=5529,
)

val_dataset = ARTDataset(X_val, y_val, enable_art=False)
```

### Refresh helpers

#### Refresh using validation predictions

```python
from art_resampling import art_refresh_dataset_from_predictions

train_loader, class_weights, per_class_f1 = art_refresh_dataset_from_predictions(
    art_dataset=train_dataset,
    y_true=val_true,
    y_pred=val_pred,
    n_classes=num_classes,
    train_loader_kwargs={"batch_size": 256, "shuffle": True, "drop_last": True},
)
```

#### Refresh using precomputed per-class F1

```python
from art_resampling import art_refresh_dataset_from_f1_scores

train_loader, class_weights, per_class_f1 = art_refresh_dataset_from_f1_scores(
    art_dataset=train_dataset,
    f1=per_class_f1,
    train_loader_kwargs={"batch_size": 256, "shuffle": True, "drop_last": True},
)
```

### Weight and metric utilities

```python
import numpy as np
from art_resampling import per_class_f1, art_weights_from_f1

val_true = np.array([0, 0, 0, 1, 1, 2, 2, 2])
val_pred = np.array([0, 0, 1, 1, 2, 0, 2, 2])

f1 = per_class_f1(val_true, val_pred, n_classes=3)
weights = art_weights_from_f1(f1)

print("per_class_f1:", np.round(f1, 4))
print("class_weights:", np.round(weights, 4))
print("sum:", float(weights.sum()))
```

## Smoke test

```bash
pytest -q
```

## Notes

* This library focuses on the ART resampling logic only.
* The example uses a synthetic tabular dataset for a complete end-to-end demonstration.

### Minimal PyTorch training loop with ART

You choose two key ART parameters:

* `c`: fraction of each refreshed training set drawn uniformly from all samples (the "balanced" portion).
* `bf`: refresh frequency in epochs (refresh every `bf` epochs).

A typical training loop looks like:

```python
from torch.utils.data import DataLoader
from art_resampling import ARTDataset, art_refresh_dataset_from_predictions

c = 0.3
bf = 4

initial_class_weights = [1 / num_classes] * num_classes

train_dataset = ARTDataset(X_train, y_train, enable_art=True, c=c, cls_weights=initial_class_weights, seed=seed)
val_dataset = ARTDataset(X_val, y_val, enable_art=False)

train_loader_kwargs = {"batch_size": 256, "shuffle": True, "drop_last": True}
val_loader_kwargs = {"batch_size": 512, "shuffle": False, "drop_last": False}

train_loader = DataLoader(train_dataset, **train_loader_kwargs)
val_loader = DataLoader(val_dataset, **val_loader_kwargs)

for epoch in range(1, epochs + 1):
    train_one_epoch(model, train_loader, optimizer, loss_fn)

    if epoch % bf == 0:
        val_true, val_pred = predict_labels(model, val_loader)
        train_loader, class_weights, per_class_f1 = art_refresh_dataset_from_predictions(
            art_dataset=train_dataset,
            y_true=val_true,
            y_pred=val_pred,
            n_classes=num_classes,
            train_loader_kwargs=train_loader_kwargs,
        )
```

## Support

If you find a bug, please open a GitHub Issue with:

* a minimal code snippet to reproduce
* your Python / PyTorch / numpy versions
* the exact error message or unexpected behavior

For questions about how to integrate ART into a specific training loop, include a small sketch of your dataloader and evaluation step.
