"""
Model Explainability for Nalyst.

Provides interpretability tools for machine learning models.
"""

from nalyst.explainability.shap_explain import (
    TreeExplainer,
    LinearExplainer,
    KernelExplainer,
    shap_summary,
    shap_dependence,
    shap_force,
)
from nalyst.explainability.lime_explain import (
    LimeTabularExplainer,
    LimeTextExplainer,
)
from nalyst.explainability.feature_importance import (
    permutation_importance,
    drop_column_importance,
    mutual_info_importance,
)

__all__ = [
    # SHAP-style explanations
    "TreeExplainer",
    "LinearExplainer",
    "KernelExplainer",
    "shap_summary",
    "shap_dependence",
    "shap_force",
    # LIME-style explanations
    "LimeTabularExplainer",
    "LimeTextExplainer",
    # Feature importance
    "permutation_importance",
    "drop_column_importance",
    "mutual_info_importance",
]
