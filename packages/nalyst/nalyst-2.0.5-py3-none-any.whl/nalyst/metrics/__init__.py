"""
Metrics for model evaluation.

Provides scoring functions for classification,
regression, and clustering tasks.
"""

from nalyst.metrics.classification import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_auc_score,
    log_loss,
)
from nalyst.metrics.regression import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
    root_mean_squared_error,
    explained_variance_score,
    max_error,
    median_absolute_error,
    mean_squared_log_error,
)
from nalyst.metrics.clustering import (
    silhouette_score,
    silhouette_samples,
    calinski_harabasz_score,
    davies_bouldin_score,
    adjusted_rand_score,
    normalized_mutual_info_score,
    homogeneity_score,
    completeness_score,
    v_measure_score,
)

__all__ = [
    # Classification
    "accuracy_score",
    "precision_score",
    "recall_score",
    "f1_score",
    "confusion_matrix",
    "classification_report",
    "roc_auc_score",
    "log_loss",
    # Regression
    "mean_squared_error",
    "mean_absolute_error",
    "r2_score",
    "mean_absolute_percentage_error",
    "root_mean_squared_error",
    "explained_variance_score",
    "max_error",
    "median_absolute_error",
    "mean_squared_log_error",
    # Clustering
    "silhouette_score",
    "silhouette_samples",
    "calinski_harabasz_score",
    "davies_bouldin_score",
    "adjusted_rand_score",
    "normalized_mutual_info_score",
    "homogeneity_score",
    "completeness_score",
    "v_measure_score",
]
