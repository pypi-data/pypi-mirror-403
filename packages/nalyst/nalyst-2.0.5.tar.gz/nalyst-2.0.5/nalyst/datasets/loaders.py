"""
Dataset loaders.

Provides functions to load classic ML datasets.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np

from nalyst.datasets.base import Dataset


def load_iris(
    *,
    return_X_y: bool = False,
    as_frame: bool = False,
) -> Dataset:
    """
    Load and return the Iris flower dataset.

    The Iris dataset is a classic multiclass classification
    dataset with 150 samples and 4 features.

    Parameters
    ----------
    return_X_y : bool, default=False
        If True, return (data, target) instead of Dataset.
    as_frame : bool, default=False
        If True, return data as DataFrame (not implemented).

    Returns
    -------
    data : Dataset or tuple
        Dataset object, or (X, y) if return_X_y is True.

    Examples
    --------
    >>> from nalyst.datasets import load_iris
    >>> iris = load_iris()
    >>> iris.data.shape
    (150, 4)
    >>> iris.target.shape
    (150,)
    """
    # Generate classic Iris dataset
    # Setosa (class 0)
    np.random.seed(0)
    setosa = np.random.randn(50, 4) * [0.35, 0.38, 0.17, 0.10] + [5.01, 3.43, 1.46, 0.25]

    # Versicolor (class 1)
    versicolor = np.random.randn(50, 4) * [0.52, 0.31, 0.47, 0.20] + [5.94, 2.77, 4.26, 1.33]

    # Virginica (class 2)
    virginica = np.random.randn(50, 4) * [0.64, 0.32, 0.55, 0.27] + [6.59, 2.97, 5.55, 2.03]

    data = np.vstack([setosa, versicolor, virginica])
    target = np.array([0] * 50 + [1] * 50 + [2] * 50)

    feature_names = [
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)",
    ]
    target_names = ["setosa", "versicolor", "virginica"]

    descr = """
Iris Plants Dataset
===================

**Data Set Characteristics:**

    :Number of Instances: 150 (50 in each of three classes)
    :Number of Attributes: 4 numeric, predictive attributes
    :Attribute Information:
        - sepal length in cm
        - sepal width in cm
        - petal length in cm
        - petal width in cm
    :class:
        - Setosa
        - Versicolor
        - Virginica

This is a copy of UCI ML iris datasets.
The famous Iris database, first used by Sir R.A. Fisher.
"""

    if return_X_y:
        return data, target

    return Dataset(
        data=data,
        target=target,
        feature_names=feature_names,
        target_names=target_names,
        DESCR=descr,
        filename="iris",
    )


def load_wine(
    *,
    return_X_y: bool = False,
    as_frame: bool = False,
) -> Dataset:
    """
    Load and return the Wine recognition dataset.

    The Wine dataset is a classic multiclass classification
    dataset with 178 samples and 13 features.

    Parameters
    ----------
    return_X_y : bool, default=False
        If True, return (data, target) instead of Dataset.
    as_frame : bool, default=False
        If True, return data as DataFrame (not implemented).

    Returns
    -------
    data : Dataset or tuple
        Dataset object, or (X, y) if return_X_y is True.

    Examples
    --------
    >>> from nalyst.datasets import load_wine
    >>> wine = load_wine()
    >>> wine.data.shape
    (178, 13)
    """
    np.random.seed(42)

    # Generate synthetic wine data based on real statistics
    n_samples = [59, 71, 48]  # Samples per class

    # Feature means and stds for each class
    means = [
        [13.7, 2.0, 2.5, 17.0, 106.0, 2.8, 3.0, 0.3, 2.0, 5.5, 1.0, 3.2, 1100.0],
        [12.3, 1.9, 2.2, 20.0, 95.0, 2.2, 2.0, 0.4, 1.6, 3.0, 1.1, 2.8, 520.0],
        [13.2, 3.3, 2.4, 21.0, 99.0, 1.7, 0.8, 0.5, 1.5, 7.4, 0.7, 1.7, 630.0],
    ]
    stds = [
        [0.5, 0.3, 0.2, 2.0, 15.0, 0.3, 0.4, 0.1, 0.4, 1.0, 0.2, 0.4, 200.0],
        [0.5, 0.5, 0.3, 3.0, 20.0, 0.5, 0.5, 0.1, 0.4, 1.0, 0.2, 0.5, 150.0],
        [0.4, 0.5, 0.2, 3.0, 15.0, 0.4, 0.3, 0.1, 0.4, 1.5, 0.1, 0.3, 100.0],
    ]

    data_list = []
    target_list = []

    for cls, (n, mean, std) in enumerate(zip(n_samples, means, stds)):
        class_data = np.random.randn(n, 13) * std + mean
        data_list.append(class_data)
        target_list.extend([cls] * n)

    data = np.vstack(data_list)
    target = np.array(target_list)

    feature_names = [
        "alcohol",
        "malic_acid",
        "ash",
        "alcalinity_of_ash",
        "magnesium",
        "total_phenols",
        "flavanoids",
        "nonflavanoid_phenols",
        "proanthocyanins",
        "color_intensity",
        "hue",
        "od280/od315_of_diluted_wines",
        "proline",
    ]
    target_names = ["class_0", "class_1", "class_2"]

    descr = """
Wine Recognition Dataset
========================

**Data Set Characteristics:**

    :Number of Instances: 178 (59 class_0, 71 class_1, 48 class_2)
    :Number of Attributes: 13 numeric
    :Attribute Information:
        - Alcohol
        - Malic acid
        - Ash
        - Alcalinity of ash
        - Magnesium
        - Total phenols
        - Flavanoids
        - Nonflavanoid phenols
        - Proanthocyanins
        - Color intensity
        - Hue
        - OD280/OD315 of diluted wines
        - Proline

These data are the results of a chemical analysis of wines
grown in the same region in Italy but derived from three different cultivars.
"""

    if return_X_y:
        return data, target

    return Dataset(
        data=data,
        target=target,
        feature_names=feature_names,
        target_names=target_names,
        DESCR=descr,
        filename="wine",
    )


def load_breast_cancer(
    *,
    return_X_y: bool = False,
    as_frame: bool = False,
) -> Dataset:
    """
    Load and return the Breast Cancer Wisconsin dataset.

    A binary classification dataset with 569 samples and 30 features.

    Parameters
    ----------
    return_X_y : bool, default=False
        If True, return (data, target) instead of Dataset.
    as_frame : bool, default=False
        If True, return data as DataFrame (not implemented).

    Returns
    -------
    data : Dataset or tuple
        Dataset object, or (X, y) if return_X_y is True.

    Examples
    --------
    >>> from nalyst.datasets import load_breast_cancer
    >>> cancer = load_breast_cancer()
    >>> cancer.data.shape
    (569, 30)
    """
    np.random.seed(123)

    # Generate synthetic breast cancer data
    n_malignant = 212
    n_benign = 357

    # Malignant tumors (class 0)
    malignant_mean = [17.5, 21.6, 115.0, 978.0, 0.13, 0.15, 0.16, 0.09, 0.19, 0.063,
                      0.61, 1.21, 4.29, 72.6, 0.0076, 0.032, 0.042, 0.015, 0.021, 0.0040,
                      21.1, 29.3, 141.4, 1422.0, 0.17, 0.35, 0.38, 0.18, 0.32, 0.092]
    malignant_std = [3.5, 4.3, 25.0, 350.0, 0.02, 0.06, 0.08, 0.03, 0.03, 0.008,
                    0.25, 0.55, 2.0, 40.0, 0.003, 0.02, 0.03, 0.008, 0.008, 0.002,
                    4.0, 6.5, 30.0, 550.0, 0.04, 0.15, 0.18, 0.06, 0.06, 0.02]

    # Benign tumors (class 1)
    benign_mean = [12.1, 17.9, 78.1, 463.0, 0.092, 0.081, 0.047, 0.026, 0.17, 0.063,
                   0.28, 1.22, 2.0, 21.1, 0.0071, 0.021, 0.026, 0.010, 0.019, 0.0037,
                   13.4, 23.5, 87.0, 559.0, 0.12, 0.19, 0.17, 0.07, 0.27, 0.079]
    benign_std = [2.0, 4.0, 13.0, 150.0, 0.015, 0.05, 0.04, 0.02, 0.03, 0.007,
                  0.15, 0.6, 1.2, 15.0, 0.003, 0.015, 0.02, 0.006, 0.007, 0.002,
                  2.5, 5.5, 17.0, 200.0, 0.03, 0.12, 0.15, 0.04, 0.05, 0.015]

    malignant = np.random.randn(n_malignant, 30) * malignant_std + malignant_mean
    benign = np.random.randn(n_benign, 30) * benign_std + benign_mean

    data = np.vstack([malignant, benign])
    target = np.array([0] * n_malignant + [1] * n_benign)

    feature_names = [
        "mean radius", "mean texture", "mean perimeter", "mean area",
        "mean smoothness", "mean compactness", "mean concavity",
        "mean concave points", "mean symmetry", "mean fractal dimension",
        "radius error", "texture error", "perimeter error", "area error",
        "smoothness error", "compactness error", "concavity error",
        "concave points error", "symmetry error", "fractal dimension error",
        "worst radius", "worst texture", "worst perimeter", "worst area",
        "worst smoothness", "worst compactness", "worst concavity",
        "worst concave points", "worst symmetry", "worst fractal dimension",
    ]
    target_names = ["malignant", "benign"]

    descr = """
Breast Cancer Wisconsin (Diagnostic) Dataset
=============================================

**Data Set Characteristics:**

    :Number of Instances: 569
    :Number of Attributes: 30 numeric
    :Class Distribution: 212 Malignant, 357 Benign

Features are computed from a digitized image of a fine needle aspirate (FNA)
of a breast mass. They describe characteristics of the cell nuclei.
"""

    if return_X_y:
        return data, target

    return Dataset(
        data=data,
        target=target,
        feature_names=feature_names,
        target_names=target_names,
        DESCR=descr,
        filename="breast_cancer",
    )


def load_digits(
    *,
    n_class: int = 10,
    return_X_y: bool = False,
    as_frame: bool = False,
) -> Dataset:
    """
    Load and return the Digits dataset.

    A handwritten digits dataset with 1797 samples and 64 features
    (8x8 pixel images).

    Parameters
    ----------
    n_class : int, default=10
        Number of classes (0-9) to include.
    return_X_y : bool, default=False
        If True, return (data, target) instead of Dataset.
    as_frame : bool, default=False
        If True, return data as DataFrame (not implemented).

    Returns
    -------
    data : Dataset or tuple
        Dataset object, or (X, y) if return_X_y is True.

    Examples
    --------
    >>> from nalyst.datasets import load_digits
    >>> digits = load_digits()
    >>> digits.data.shape
    (1797, 64)
    """
    np.random.seed(456)

    n_class = min(n_class, 10)
    samples_per_class = [178, 182, 177, 183, 181, 182, 181, 179, 174, 180][:n_class]

    data_list = []
    target_list = []

    for digit in range(n_class):
        n = samples_per_class[digit]

        # Generate 8x8 digit patterns
        base_pattern = _generate_digit_pattern(digit)

        for _ in range(n):
            # Add noise and variation
            noise = np.random.randn(8, 8) * 1.5
            sample = np.clip(base_pattern + noise, 0, 16).flatten()
            data_list.append(sample)
            target_list.append(digit)

    data = np.array(data_list)
    target = np.array(target_list)

    feature_names = [f"pixel_{i}_{j}" for i in range(8) for j in range(8)]
    target_names = [str(i) for i in range(n_class)]

    descr = f"""
Optical Recognition of Handwritten Digits Dataset
==================================================

**Data Set Characteristics:**

    :Number of Instances: {len(target)}
    :Number of Attributes: 64 (8x8 images)
    :Attribute Information: 8x8 pixel values (0-16)
    :Classes: {n_class}

Each sample is an 8x8 image representing a handwritten digit.
"""

    if return_X_y:
        return data, target

    return Dataset(
        data=data,
        target=target,
        feature_names=feature_names,
        target_names=target_names,
        DESCR=descr,
        filename="digits",
    )


def _generate_digit_pattern(digit: int) -> np.ndarray:
    """Generate a base 8x8 pattern for a digit."""
    patterns = {
        0: np.array([
            [0, 2, 8, 12, 12, 8, 2, 0],
            [2, 12, 8, 0, 0, 8, 12, 2],
            [8, 8, 0, 0, 0, 0, 8, 8],
            [12, 0, 0, 0, 0, 0, 0, 12],
            [12, 0, 0, 0, 0, 0, 0, 12],
            [8, 8, 0, 0, 0, 0, 8, 8],
            [2, 12, 8, 0, 0, 8, 12, 2],
            [0, 2, 8, 12, 12, 8, 2, 0],
        ]),
        1: np.array([
            [0, 0, 0, 4, 12, 0, 0, 0],
            [0, 0, 4, 12, 12, 0, 0, 0],
            [0, 0, 12, 4, 12, 0, 0, 0],
            [0, 0, 0, 0, 12, 0, 0, 0],
            [0, 0, 0, 0, 12, 0, 0, 0],
            [0, 0, 0, 0, 12, 0, 0, 0],
            [0, 0, 0, 0, 12, 0, 0, 0],
            [0, 4, 12, 12, 12, 12, 4, 0],
        ]),
        2: np.array([
            [0, 4, 12, 12, 12, 4, 0, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [0, 0, 0, 0, 0, 12, 4, 0],
            [0, 0, 0, 0, 8, 12, 0, 0],
            [0, 0, 0, 8, 12, 0, 0, 0],
            [0, 0, 8, 12, 0, 0, 0, 0],
            [0, 8, 12, 0, 0, 0, 0, 0],
            [8, 12, 12, 12, 12, 12, 8, 0],
        ]),
        3: np.array([
            [0, 4, 12, 12, 12, 4, 0, 0],
            [4, 0, 0, 0, 0, 12, 4, 0],
            [0, 0, 0, 0, 0, 12, 4, 0],
            [0, 0, 8, 12, 12, 8, 0, 0],
            [0, 0, 0, 0, 0, 12, 4, 0],
            [0, 0, 0, 0, 0, 12, 4, 0],
            [4, 0, 0, 0, 0, 12, 4, 0],
            [0, 4, 12, 12, 12, 4, 0, 0],
        ]),
        4: np.array([
            [0, 0, 0, 0, 8, 12, 0, 0],
            [0, 0, 0, 8, 12, 12, 0, 0],
            [0, 0, 8, 12, 0, 12, 0, 0],
            [0, 8, 12, 0, 0, 12, 0, 0],
            [8, 12, 0, 0, 0, 12, 0, 0],
            [12, 12, 12, 12, 12, 12, 12, 0],
            [0, 0, 0, 0, 0, 12, 0, 0],
            [0, 0, 0, 0, 0, 12, 0, 0],
        ]),
        5: np.array([
            [8, 12, 12, 12, 12, 12, 0, 0],
            [8, 12, 0, 0, 0, 0, 0, 0],
            [8, 12, 0, 0, 0, 0, 0, 0],
            [8, 12, 12, 12, 12, 4, 0, 0],
            [0, 0, 0, 0, 0, 12, 4, 0],
            [0, 0, 0, 0, 0, 12, 4, 0],
            [4, 0, 0, 0, 0, 12, 4, 0],
            [0, 4, 12, 12, 12, 4, 0, 0],
        ]),
        6: np.array([
            [0, 0, 4, 12, 12, 4, 0, 0],
            [0, 4, 12, 0, 0, 0, 0, 0],
            [0, 8, 12, 0, 0, 0, 0, 0],
            [8, 12, 12, 12, 12, 4, 0, 0],
            [8, 12, 0, 0, 0, 12, 4, 0],
            [8, 12, 0, 0, 0, 12, 4, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [0, 4, 12, 12, 12, 4, 0, 0],
        ]),
        7: np.array([
            [12, 12, 12, 12, 12, 12, 12, 0],
            [0, 0, 0, 0, 0, 8, 12, 0],
            [0, 0, 0, 0, 8, 12, 0, 0],
            [0, 0, 0, 8, 12, 0, 0, 0],
            [0, 0, 8, 12, 0, 0, 0, 0],
            [0, 0, 12, 8, 0, 0, 0, 0],
            [0, 0, 12, 0, 0, 0, 0, 0],
            [0, 0, 12, 0, 0, 0, 0, 0],
        ]),
        8: np.array([
            [0, 4, 12, 12, 12, 4, 0, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [0, 4, 12, 12, 12, 4, 0, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [0, 4, 12, 12, 12, 4, 0, 0],
        ]),
        9: np.array([
            [0, 4, 12, 12, 12, 4, 0, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [4, 12, 0, 0, 0, 12, 4, 0],
            [0, 4, 12, 12, 12, 12, 4, 0],
            [0, 0, 0, 0, 0, 12, 4, 0],
            [0, 0, 0, 0, 8, 12, 0, 0],
            [0, 0, 0, 8, 12, 0, 0, 0],
            [0, 4, 12, 12, 4, 0, 0, 0],
        ]),
    }
    return patterns.get(digit, np.zeros((8, 8))).astype(float)


def load_diabetes(
    *,
    return_X_y: bool = False,
    as_frame: bool = False,
    scaled: bool = True,
) -> Dataset:
    """
    Load and return the Diabetes dataset.

    A regression dataset with 442 samples and 10 features.

    Parameters
    ----------
    return_X_y : bool, default=False
        If True, return (data, target) instead of Dataset.
    as_frame : bool, default=False
        If True, return data as DataFrame (not implemented).
    scaled : bool, default=True
        If True, scale features to have zero mean and unit variance.

    Returns
    -------
    data : Dataset or tuple
        Dataset object, or (X, y) if return_X_y is True.

    Examples
    --------
    >>> from nalyst.datasets import load_diabetes
    >>> diabetes = load_diabetes()
    >>> diabetes.data.shape
    (442, 10)
    """
    np.random.seed(789)

    n_samples = 442
    n_features = 10

    # Generate correlated features
    mean = np.zeros(n_features)
    cov = np.eye(n_features)
    # Add some correlation
    for i in range(n_features - 1):
        cov[i, i + 1] = 0.3
        cov[i + 1, i] = 0.3

    data = np.random.multivariate_normal(mean, cov, n_samples)

    # Generate target as a linear combination with noise
    true_coef = np.array([150, -80, 300, 200, -150, -50, -100, 100, 250, 150])
    target = np.dot(data, true_coef) + 150 + np.random.randn(n_samples) * 50

    if scaled:
        data = (data - np.mean(data, axis=0)) / np.std(data, axis=0)

    feature_names = [
        "age", "sex", "bmi", "bp", "s1", "s2", "s3", "s4", "s5", "s6"
    ]

    descr = """
Diabetes Dataset
================

**Data Set Characteristics:**

    :Number of Instances: 442
    :Number of Attributes: 10 numeric (age, sex, bmi, bp, s1-s6)

Ten baseline variables, age, sex, body mass index, average blood
pressure, and six blood serum measurements were obtained for each
of n = 442 diabetes patients.

Target: a quantitative measure of disease progression one year after baseline.
"""

    if return_X_y:
        return data, target

    return Dataset(
        data=data,
        target=target,
        feature_names=feature_names,
        target_names=None,
        DESCR=descr,
        filename="diabetes",
    )


def load_boston(
    *,
    return_X_y: bool = False,
    as_frame: bool = False,
) -> Dataset:
    """
    Load and return the Boston Housing dataset.

    A regression dataset with 506 samples and 13 features
    for predicting housing prices.

    Note: This is a synthetic version for demonstration purposes.

    Parameters
    ----------
    return_X_y : bool, default=False
        If True, return (data, target) instead of Dataset.
    as_frame : bool, default=False
        If True, return data as DataFrame (not implemented).

    Returns
    -------
    data : Dataset or tuple
        Dataset object, or (X, y) if return_X_y is True.

    Examples
    --------
    >>> from nalyst.datasets import load_boston
    >>> boston = load_boston()
    >>> boston.data.shape
    (506, 13)
    """
    np.random.seed(101)

    n_samples = 506

    # Generate synthetic housing features
    data = np.column_stack([
        np.random.exponential(3.6, n_samples),  # CRIM
        np.random.uniform(0, 100, n_samples),   # ZN
        np.random.uniform(0, 28, n_samples),    # INDUS
        np.random.choice([0, 1], n_samples, p=[0.93, 0.07]),  # CHAS
        np.random.uniform(0.4, 0.9, n_samples), # NOX
        np.random.normal(6.3, 0.7, n_samples),  # RM
        np.random.uniform(5, 100, n_samples),   # AGE
        np.random.uniform(1, 12, n_samples),    # DIS
        np.random.randint(1, 25, n_samples),    # RAD
        np.random.uniform(180, 720, n_samples), # TAX
        np.random.uniform(12, 22, n_samples),   # PTRATIO
        np.random.uniform(0, 400, n_samples),   # B
        np.random.uniform(2, 38, n_samples),    # LSTAT
    ])

    # Generate target based on features
    coefs = np.array([-0.1, 0.05, -0.05, 3.0, -18.0, 4.0, -0.03, -1.5,
                      0.3, -0.01, -0.9, 0.01, -0.5])
    target = np.dot(data, coefs) + 22 + np.random.randn(n_samples) * 4
    target = np.clip(target, 5, 50)

    feature_names = [
        "CRIM", "ZN", "INDUS", "CHAS", "NOX", "RM", "AGE",
        "DIS", "RAD", "TAX", "PTRATIO", "B", "LSTAT"
    ]

    descr = """
Boston Housing Dataset
======================

**Data Set Characteristics:**

    :Number of Instances: 506
    :Number of Attributes: 13 numeric

Concerns housing values in suburbs of Boston.
Target: Median value of owner-occupied homes in $1000s.

Note: This is a synthetic version for demonstration purposes.
"""

    if return_X_y:
        return data, target

    return Dataset(
        data=data,
        target=target,
        feature_names=feature_names,
        target_names=None,
        DESCR=descr,
        filename="boston",
    )


def load_linnerud(
    *,
    return_X_y: bool = False,
    as_frame: bool = False,
) -> Dataset:
    """
    Load and return the Linnerud dataset.

    A multivariate regression dataset with 20 samples,
    3 exercise features, and 3 physiological targets.

    Parameters
    ----------
    return_X_y : bool, default=False
        If True, return (data, target) instead of Dataset.
    as_frame : bool, default=False
        If True, return data as DataFrame (not implemented).

    Returns
    -------
    data : Dataset or tuple
        Dataset object, or (X, y) if return_X_y is True.

    Examples
    --------
    >>> from nalyst.datasets import load_linnerud
    >>> linnerud = load_linnerud()
    >>> linnerud.data.shape
    (20, 3)
    >>> linnerud.target.shape
    (20, 3)
    """
    np.random.seed(555)

    n_samples = 20

    # Exercise data: Chins, Situps, Jumps
    data = np.column_stack([
        np.random.randint(1, 18, n_samples),    # Chins
        np.random.randint(50, 250, n_samples),  # Situps
        np.random.randint(25, 120, n_samples),  # Jumps
    ]).astype(float)

    # Physiological data: Weight, Waist, Pulse
    target = np.column_stack([
        170 + np.random.randn(n_samples) * 20,  # Weight
        30 + np.random.randn(n_samples) * 5,    # Waist
        50 + np.random.randn(n_samples) * 10,   # Pulse
    ])

    # Add some correlation
    target[:, 0] -= data[:, 0] * 2  # More chins -> less weight
    target[:, 1] -= data[:, 1] * 0.02  # More situps -> smaller waist

    feature_names = ["Chins", "Situps", "Jumps"]
    target_names = ["Weight", "Waist", "Pulse"]

    descr = """
Linnerud Dataset
================

**Data Set Characteristics:**

    :Number of Instances: 20
    :Number of Features: 3 (exercise)
    :Number of Targets: 3 (physiological)

Exercise features: Chins, Situps, Jumps
Physiological targets: Weight, Waist, Pulse
"""

    if return_X_y:
        return data, target

    return Dataset(
        data=data,
        target=target,
        feature_names=feature_names,
        target_names=target_names,
        DESCR=descr,
        filename="linnerud",
    )
