"""
Learners module for Nalyst.

This module contains all supervised learning algorithms including:

- linear: Linear models for regression and classification
- trees: Decision trees and related models
- ensemble: Ensemble methods (forests, boosting)
- neural: Neural network models
- neighbors: K-nearest neighbors
- svm: Support Vector Machines
- bayes: Naive Bayes classifiers
"""

from nalyst.learners.linear import (
    OrdinaryLinearRegressor,
    RidgeRegressor,
    LassoRegressor,
    ElasticNetRegressor,
    LogisticLearner,
    RidgeClassifier,
    SGDLearner,
    PerceptronLearner,
)

__all__ = [
    # Linear regression
    "OrdinaryLinearRegressor",
    "RidgeRegressor",
    "LassoRegressor",
    "ElasticNetRegressor",
    # Linear classification
    "LogisticLearner",
    "RidgeClassifier",
    "SGDLearner",
    "PerceptronLearner",
]
