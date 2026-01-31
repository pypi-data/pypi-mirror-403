"""
Partial dependence plots.
"""

from __future__ import annotations

from typing import Optional, List, Union

import numpy as np


def partial_dependence(
    estimator,
    X: np.ndarray,
    features: Union[int, List[int]],
    *,
    percentiles: tuple = (0.05, 0.95),
    grid_resolution: int = 100,
    method: str = "auto",
    kind: str = "average",
) -> dict:
    """
    Compute partial dependence.

    Parameters
    ----------
    estimator : object
        Fitted estimator with predict method.
    X : ndarray of shape (n_samples, n_features)
        Data to compute partial dependence on.
    features : int or list of int
        Feature index or pair of indices.
    percentiles : tuple, default=(0.05, 0.95)
        Percentiles to limit grid range.
    grid_resolution : int, default=100
        Number of grid points.
    method : str, default="auto"
        Method to compute: "auto", "brute".
    kind : str, default="average"
        "average" or "individual".

    Returns
    -------
    result : dict
        Dictionary with keys:
        - average: Partial dependence values.
        - grid_values: Grid values for each feature.

    Examples
    --------
    >>> from nalyst.inspection import partial_dependence
    >>> result = partial_dependence(model, X, features=[0])
    >>> result["average"], result["grid_values"]
    """
    X = np.asarray(X)

    if isinstance(features, int):
        features = [features]

    n_samples = X.shape[0]

    # Create grid
    grid_values = []
    for feature in features:
        values = X[:, feature]
        lower = np.percentile(values, percentiles[0] * 100)
        upper = np.percentile(values, percentiles[1] * 100)
        grid = np.linspace(lower, upper, grid_resolution)
        grid_values.append(grid)

    if len(features) == 1:
        # 1D partial dependence
        grid = grid_values[0]
        pdp = np.zeros((grid_resolution,))

        for i, val in enumerate(grid):
            X_temp = X.copy()
            X_temp[:, features[0]] = val

            if hasattr(estimator, "infer_proba"):
                predictions = estimator.infer_proba(X_temp)[:, 1]
            else:
                predictions = estimator.infer(X_temp)

            pdp[i] = np.mean(predictions)

        return {
            "average": pdp.reshape(1, -1),
            "grid_values": grid_values,
        }
    else:
        # 2D partial dependence
        grid_1, grid_2 = grid_values
        pdp = np.zeros((len(grid_1), len(grid_2)))

        for i, val1 in enumerate(grid_1):
            for j, val2 in enumerate(grid_2):
                X_temp = X.copy()
                X_temp[:, features[0]] = val1
                X_temp[:, features[1]] = val2

                if hasattr(estimator, "infer_proba"):
                    predictions = estimator.infer_proba(X_temp)[:, 1]
                else:
                    predictions = estimator.infer(X_temp)

                pdp[i, j] = np.mean(predictions)

        return {
            "average": pdp.reshape(1, len(grid_1), len(grid_2)),
            "grid_values": grid_values,
        }


class PartialDependenceDisplay:
    """
    Partial Dependence Plot visualization.

    Parameters
    ----------
    pd_results : list of dicts
        Results from partial_dependence.
    features : list
        Feature indices.
    feature_names : list, optional
        Feature names.
    target_idx : int, default=0
        Target index for multi-output.

    Examples
    --------
    >>> from nalyst.inspection import partial_dependence, PartialDependenceDisplay
    >>> result = partial_dependence(model, X, features=[0])
    >>> disp = PartialDependenceDisplay([result], features=[0])
    >>> disp.plot()
    """

    def __init__(
        self,
        pd_results: list,
        features: list,
        feature_names: Optional[list] = None,
        target_idx: int = 0,
    ):
        self.pd_results = pd_results
        self.features = features
        self.feature_names = feature_names
        self.target_idx = target_idx

    @classmethod
    def from_estimator(
        cls,
        estimator,
        X: np.ndarray,
        features: list,
        *,
        feature_names: Optional[list] = None,
        target_idx: int = 0,
        grid_resolution: int = 100,
        **kwargs,
    ) -> "PartialDependenceDisplay":
        """
        Create display from an estimator.

        Parameters
        ----------
        estimator : object
            Fitted estimator.
        X : ndarray
            Data for computing partial dependence.
        features : list
            Features to plot.
        feature_names : list, optional
            Feature names.
        target_idx : int, default=0
            Target index.
        grid_resolution : int, default=100
            Grid resolution.

        Returns
        -------
        display : PartialDependenceDisplay
            Object with computed values.
        """
        pd_results = []

        for feature in features:
            if isinstance(feature, (list, tuple)):
                result = partial_dependence(
                    estimator, X, feature,
                    grid_resolution=grid_resolution
                )
            else:
                result = partial_dependence(
                    estimator, X, [feature],
                    grid_resolution=grid_resolution
                )
            pd_results.append(result)

        return cls(pd_results, features, feature_names, target_idx)

    def plot(self, ax=None, **kwargs):
        """
        Plot partial dependence.

        Parameters
        ----------
        ax : matplotlib axes, optional
            Axes to plot on.
        **kwargs
            Additional arguments for matplotlib.

        Returns
        -------
        display : PartialDependenceDisplay
            Self.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for plotting")

        n_features = len(self.features)

        if ax is None:
            fig, axes = plt.subplots(1, n_features, figsize=(4 * n_features, 3))
            if n_features == 1:
                axes = [axes]
        else:
            axes = [ax]

        for idx, (result, feature, ax) in enumerate(zip(self.pd_results, self.features, axes)):
            grid = result["grid_values"][0]
            pdp = result["average"][0]

            ax.plot(grid, pdp, **kwargs)

            if self.feature_names is not None:
                if isinstance(feature, (list, tuple)):
                    name = f"{self.feature_names[feature[0]]}, {self.feature_names[feature[1]]}"
                else:
                    name = self.feature_names[feature]
            else:
                name = f"Feature {feature}"

            ax.set_xlabel(name)
            ax.set_ylabel("Partial dependence")

        plt.tight_layout()

        self.axes_ = axes
        self.figure_ = axes[0].figure

        return self
