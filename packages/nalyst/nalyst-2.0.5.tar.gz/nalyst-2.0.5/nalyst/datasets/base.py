"""
Dataset base classes and utilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, Dict, List
import os
import shutil

import numpy as np


@dataclass
class Dataset:
    """
    Container for dataset information.

    A simple namespace class to hold dataset data
    and metadata.

    Parameters
    ----------
    data : ndarray
        Feature matrix of shape (n_samples, n_features).
    target : ndarray
        Target values of shape (n_samples,) or (n_samples, n_targets).
    feature_names : list of str, optional
        Names of each feature.
    target_names : list of str, optional
        Names of each target class.
    DESCR : str, optional
        Full description of the dataset.
    filename : str, optional
        Name of the source file.
    frame : Any, optional
        DataFrame representation (if available).

    Examples
    --------
    >>> from nalyst.datasets import Dataset
    >>> import numpy as np
    >>> data = Dataset(
    ...     data=np.array([[1, 2], [3, 4]]),
    ...     target=np.array([0, 1]),
    ...     feature_names=["f1", "f2"],
    ...     target_names=["class_0", "class_1"]
    ... )
    >>> data.data.shape
    (2, 2)
    """

    data: np.ndarray
    target: np.ndarray
    feature_names: Optional[List[str]] = None
    target_names: Optional[List[str]] = None
    DESCR: Optional[str] = None
    filename: Optional[str] = None
    frame: Any = None
    data_module: Optional[str] = None

    # Additional metadata
    _metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate data after initialization."""
        self.data = np.asarray(self.data)
        self.target = np.asarray(self.target)

    @property
    def n_samples(self) -> int:
        """Number of samples in the dataset."""
        return self.data.shape[0]

    @property
    def n_features(self) -> int:
        """Number of features in the dataset."""
        if self.data.ndim == 1:
            return 1
        return self.data.shape[1]

    def keys(self) -> List[str]:
        """Return available keys (for dict-like access)."""
        return ["data", "target", "feature_names", "target_names", "DESCR"]

    def __getitem__(self, key: str) -> Any:
        """Enable dict-like access."""
        return getattr(self, key)

    def __repr__(self) -> str:
        return (
            f"Dataset(n_samples={self.n_samples}, "
            f"n_features={self.n_features})"
        )


def get_data_home(data_home: Optional[str] = None) -> Path:
    """
    Get the path to nalyst's data directory.

    By default, the data directory is set to a folder named
    'nalyst_data' in the user's home folder.

    Parameters
    ----------
    data_home : str, optional
        The path to the data directory. If None, the default
        directory is used.

    Returns
    -------
    data_home : Path
        The path to the data directory.

    Examples
    --------
    >>> from nalyst.datasets import get_data_home
    >>> data_home = get_data_home()
    >>> str(data_home).endswith('nalyst_data')
    True
    """
    if data_home is None:
        data_home = os.environ.get(
            "NALYST_DATA",
            os.path.join("~", "nalyst_data")
        )

    data_home = os.path.expanduser(data_home)
    path = Path(data_home)

    path.mkdir(parents=True, exist_ok=True)

    return path


def clear_data_home(data_home: Optional[str] = None) -> None:
    """
    Delete all contents of the data directory.

    Parameters
    ----------
    data_home : str, optional
        The path to the data directory. If None, the default
        directory is used.

    Examples
    --------
    >>> from nalyst.datasets import clear_data_home
    >>> clear_data_home()  # Clears default directory
    """
    data_home = get_data_home(data_home)
    shutil.rmtree(data_home, ignore_errors=True)
