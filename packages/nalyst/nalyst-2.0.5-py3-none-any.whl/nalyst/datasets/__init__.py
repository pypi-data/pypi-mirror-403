"""
Datasets module.

Provides functions to load sample datasets
and generate synthetic data for machine learning.
"""

from nalyst.datasets.loaders import (
    load_iris,
    load_wine,
    load_breast_cancer,
    load_digits,
    load_diabetes,
    load_boston,
    load_linnerud,
)
from nalyst.datasets.generators import (
    make_classification,
    make_regression,
    make_blobs,
    make_circles,
    make_moons,
    make_gaussian_quantiles,
    make_sparse_coded_signal,
)
from nalyst.datasets.base import (
    Dataset,
    get_data_home,
    clear_data_home,
)

__all__ = [
    # Loaders
    "load_iris",
    "load_wine",
    "load_breast_cancer",
    "load_digits",
    "load_diabetes",
    "load_boston",
    "load_linnerud",
    # Generators
    "make_classification",
    "make_regression",
    "make_blobs",
    "make_circles",
    "make_moons",
    "make_gaussian_quantiles",
    "make_sparse_coded_signal",
    # Base
    "Dataset",
    "get_data_home",
    "clear_data_home",
]
