"""
Linear models for classification and regression.

This module provides linear learners including:

Regression:
- OrdinaryLinearRegressor: Standard least squares regression
- RidgeRegressor: L2-regularized regression
- LassoRegressor: L1-regularized regression
- ElasticNetRegressor: Combined L1/L2 regularization
- BayesianRidgeRegressor: Bayesian regression with automatic relevance determination

Classification:
- LogisticLearner: Logistic regression classifier
- RidgeClassifier: Classification using ridge regression
- SGDLearner: Stochastic gradient descent learner
- PerceptronLearner: Simple perceptron classifier
"""

from nalyst.learners.linear.base import (
    LinearModel,
)

from nalyst.learners.linear.regression import (
    OrdinaryLinearRegressor,
    RidgeRegressor,
    LassoRegressor,
    ElasticNetRegressor,
)

from nalyst.learners.linear.classification import (
    LogisticLearner,
    RidgeClassifier,
    SGDLearner,
    PerceptronLearner,
)

__all__ = [
    # Base
    "LinearModel",
    # Regression
    "OrdinaryLinearRegressor",
    "RidgeRegressor",
    "LassoRegressor",
    "ElasticNetRegressor",
    # Classification
    "LogisticLearner",
    "RidgeClassifier",
    "SGDLearner",
    "PerceptronLearner",
]
