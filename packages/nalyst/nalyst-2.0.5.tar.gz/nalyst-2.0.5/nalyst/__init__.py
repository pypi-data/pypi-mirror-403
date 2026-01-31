"""
Nalyst - Advanced Machine Learning, Statistical Analysis & Deep Learning Library
=================================================================================

Nalyst is a comprehensive machine learning, statistical analysis, and deep learning
library providing:

Core Machine Learning
---------------------
- Supervised Learning (classification, regression)
- Unsupervised Learning (clustering, dimensionality reduction)
- Model Evaluation and Selection
- Data Transformation and Preprocessing
- Workflow and Pipeline Construction

Deep Learning (nn module)
-------------------------
- Tensor operations with automatic differentiation
- Neural network layers (Linear, Conv, RNN, Transformer)
- Optimizers (SGD, Adam, RMSprop, AdamW)
- Loss functions
- Data loading utilities

Advanced Statistics
-------------------
- Time Series Analysis (ARIMA, exponential smoothing, VAR)
- Statistical Tests (t-tests, ANOVA, normality, correlation)
- Generalized Linear Models (GLM with various families)
- Regression Diagnostics (heteroscedasticity, multicollinearity)

Specialized Modeling
--------------------
- AutoML (automated model selection and tuning)
- Class Imbalance Handling (SMOTE, ADASYN, undersampling)
- Model Explainability (SHAP, LIME, permutation importance)
- Robust Regression (Huber, TheilSen, RANSAC)
- Survival Analysis (Kaplan-Meier, Cox PH)
- Nonparametric Methods (KDE, kernel regression, LOWESS)
- Quantile Regression
- Generalized Additive Models (GAM)

Quick Start - ML
----------------
>>> from nalyst.learners.linear import LogisticLearner
>>> from nalyst.evaluation import split_data
>>>
>>> model = LogisticLearner()
>>> model.train(X_train, y_train)
>>> predictions = model.infer(X_test)

Quick Start - Deep Learning
---------------------------
>>> from nalyst import nn
>>>
>>> class MyModel(nn.Module):
...     def __init__(self):
...         super().__init__()
...         self.fc1 = nn.Linear(784, 128)
...         self.fc2 = nn.Linear(128, 10)
...
...     def forward(self, x):
...         x = nn.functional.relu(self.fc1(x))
...         return self.fc2(x)
>>>
>>> model = MyModel()
>>> optimizer = nn.optim.Adam(model.parameters(), lr=0.001)
>>> criterion = nn.CrossEntropyLoss()

For more information, visit: https://nalyst.readthedocs.io
"""

__version__ = "2.0.5"
__author__ = "Hemant Thapa"

import os
import logging
import random

# Configure logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Package-level imports for convenience
from nalyst.core.foundation import (
    BaseLearner,
    duplicate,
)
from nalyst.core.settings import (
    get_settings,
    set_settings,
    settings_context,
)
from nalyst.utils.info import show_info

# Lazy loading for submodules
_submodules = [
    # Core modules
    "core",
    "learners",
    "clustering",
    "reduction",
    "transform",
    "evaluation",
    "workflow",
    "datasets",
    "metrics",
    "inspection",
    "calibration",
    "covariance",
    "discriminant",
    "gaussian_process",
    "manifold",
    "multiclass",
    "selection",
    "semi_supervised",
    "utils",
    # Advanced statistics
    "timeseries",
    "stats",
    "glm",
    "diagnostics",
    # Specialized modeling
    "automl",
    "imbalance",
    "explainability",
    "robust",
    "survival",
    "nonparametric",
    "quantile",
    "gam",
    # Deep Learning
    "nn",
]

__all__ = [
    # Core exports
    "BaseLearner",
    "duplicate",
    # Settings
    "get_settings",
    "set_settings",
    "settings_context",
    # Info
    "show_info",
    # Submodules
    *_submodules,
]


def __dir__():
    return __all__


def __getattr__(name: str):
    """Lazy import of submodules."""
    if name in _submodules:
        import importlib
        return importlib.import_module(f"nalyst.{name}")
    raise AttributeError(f"module 'nalyst' has no attribute '{name}'")


def setup_module(module):
    """Fixture for tests to ensure reproducible RNG seeding."""
    import numpy as np

    seed = os.environ.get("NALYST_SEED", None)
    if seed is None:
        seed = int(np.random.uniform() * np.iinfo(np.int32).max)
    else:
        seed = int(seed)

    print(f"Nalyst: Seeding RNGs with {seed}")
    np.random.seed(seed)
    random.seed(seed)
