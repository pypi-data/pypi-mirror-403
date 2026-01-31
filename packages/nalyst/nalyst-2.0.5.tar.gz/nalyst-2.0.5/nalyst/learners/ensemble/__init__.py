"""
Ensemble learning methods.

This module provides ensemble learners that combine multiple
base learners for improved performance:

- RandomForestClassifier: Random forest for classification
- RandomForestRegressor: Random forest for regression
- GradientBoostingClassifier: Gradient boosting for classification
- GradientBoostingRegressor: Gradient boosting for regression
- AdaBoostClassifier: Adaptive boosting for classification
- BaggingClassifier: Bootstrap aggregating for classification
- VotingClassifier: Voting ensemble for classification
- StackingClassifier: Stacking ensemble for classification
"""

from nalyst.learners.ensemble.forest import (
    RandomForestClassifier,
    RandomForestRegressor,
)

from nalyst.learners.ensemble.boosting import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    AdaBoostClassifier,
)

from nalyst.learners.ensemble.bagging import (
    BaggingClassifier,
    BaggingRegressor,
)

from nalyst.learners.ensemble.voting import (
    VotingClassifier,
    VotingRegressor,
)

from nalyst.learners.ensemble.isolation import IsolationForest

from nalyst.learners.ensemble.extra_trees import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
)

__all__ = [
    # Forest
    "RandomForestClassifier",
    "RandomForestRegressor",
    # Extra Trees
    "ExtraTreesClassifier",
    "ExtraTreesRegressor",
    # Boosting
    "GradientBoostingClassifier",
    "GradientBoostingRegressor",
    "AdaBoostClassifier",
    # Bagging
    "BaggingClassifier",
    "BaggingRegressor",
    # Voting
    "VotingClassifier",
    # Isolation
    "IsolationForest",
    "VotingRegressor",
]
