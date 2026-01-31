"""
Global configuration settings for Nalyst.

This module provides functions to configure global settings that
affect all Nalyst operations without passing explicit parameters.
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Iterator, Literal, Optional, Union


@dataclass
class NalystSettings:
    """
    Configuration settings for Nalyst operations.

    Attributes
    ----------
    assume_finite : bool
        If True, skip input validation for finite values (NaN/Inf).
        Improves performance but may cause crashes on invalid input.

    working_memory : int
        Target working memory in MB for chunked operations.
        Default is 1024 (1 GB).

    print_changed_only : bool
        If True, only print parameters differing from defaults in repr.

    repr_decimals : int
        Number of decimal places for floating point in repr.

    array_output : {"default", "pandas", "polars"}
        Default output format for array results.

    transform_output : {"default", "pandas", "polars"}
        Default output format for transform methods.

    parallel_backend : str
        Default backend for parallel processing.

    n_jobs : int or None
        Default number of parallel jobs. -1 means all CPUs.

    random_state : int, RandomState, or None
        Default random state for reproducibility.

    enable_cython_pairwise_dist : bool
        Whether to use optimized Cython implementations for pairwise distances.

    skip_param_validation : bool
        If True, skip parameter validation for performance.

    display : {"text", "diagram"}
        How to display learners in notebooks.

    pairwise_dist_chunk_size : int
        Chunk size for parallel pairwise distance computation.
    """

    assume_finite: bool = False
    working_memory: int = 1024
    print_changed_only: bool = True
    repr_decimals: int = 3
    array_output: Literal["default", "pandas", "polars"] = "default"
    transform_output: Optional[Literal["default", "pandas", "polars"]] = None
    parallel_backend: str = "loky"
    n_jobs: Optional[int] = None
    random_state: Optional[int] = None
    enable_cython_pairwise_dist: bool = True
    skip_param_validation: bool = False
    display: Literal["text", "diagram"] = "diagram"
    pairwise_dist_chunk_size: int = 256

    def __post_init__(self):
        """Validate settings after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all settings."""
        if self.working_memory <= 0:
            raise ValueError("working_memory must be positive")
        if self.repr_decimals < 0:
            raise ValueError("repr_decimals must be non-negative")
        if self.array_output not in ("default", "pandas", "polars"):
            raise ValueError(
                f"array_output must be 'default', 'pandas', or 'polars', "
                f"got {self.array_output!r}"
            )
        if self.transform_output is not None and self.transform_output not in (
            "default", "pandas", "polars"
        ):
            raise ValueError(
                f"transform_output must be 'default', 'pandas', 'polars', or None"
            )
        if self.display not in ("text", "diagram"):
            raise ValueError(f"display must be 'text' or 'diagram'")


class _ThreadLocalSettings(threading.local):
    """Thread-local storage for settings."""

    def __init__(self):
        super().__init__()
        self.stack: list[NalystSettings] = []


# Global settings instance
_global_settings = NalystSettings()
_thread_local_settings = _ThreadLocalSettings()


def _get_effective_settings() -> NalystSettings:
    """Get current effective settings (thread-local if set, else global)."""
    if _thread_local_settings.stack:
        return _thread_local_settings.stack[-1]
    return _global_settings


def get_settings() -> Dict[str, Any]:
    """
    Get current configuration settings.

    Returns
    -------
    settings : dict
        Dictionary of current setting values.

    Examples
    --------
    >>> from nalyst.core import get_settings
    >>> settings = get_settings()
    >>> settings['assume_finite']
    False
    """
    current = _get_effective_settings()
    return {f.name: getattr(current, f.name) for f in fields(NalystSettings)}


def set_settings(
    assume_finite: Optional[bool] = None,
    working_memory: Optional[int] = None,
    print_changed_only: Optional[bool] = None,
    repr_decimals: Optional[int] = None,
    array_output: Optional[Literal["default", "pandas", "polars"]] = None,
    transform_output: Optional[Literal["default", "pandas", "polars"]] = None,
    parallel_backend: Optional[str] = None,
    n_jobs: Optional[int] = None,
    random_state: Optional[int] = None,
    enable_cython_pairwise_dist: Optional[bool] = None,
    skip_param_validation: Optional[bool] = None,
    display: Optional[Literal["text", "diagram"]] = None,
    pairwise_dist_chunk_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Set global configuration settings.

    Parameters
    ----------
    assume_finite : bool, optional
        Skip validation for finite values.
    working_memory : int, optional
        Target working memory in MB.
    print_changed_only : bool, optional
        Only show changed params in repr.
    repr_decimals : int, optional
        Decimal places in repr.
    array_output : {"default", "pandas", "polars"}, optional
        Output format for arrays.
    transform_output : {"default", "pandas", "polars"}, optional
        Output format for transforms.
    parallel_backend : str, optional
        Default parallel backend.
    n_jobs : int, optional
        Default number of jobs.
    random_state : int, optional
        Default random state.
    enable_cython_pairwise_dist : bool, optional
        Use optimized Cython code.
    skip_param_validation : bool, optional
        Skip param validation.
    display : {"text", "diagram"}, optional
        Display mode in notebooks.
    pairwise_dist_chunk_size : int, optional
        Chunk size for pairwise distances.

    Returns
    -------
    old_settings : dict
        Previous setting values before the update.

    Examples
    --------
    >>> from nalyst.core import set_settings, get_settings
    >>> old = set_settings(assume_finite=True)
    >>> get_settings()['assume_finite']
    True
    >>> set_settings(**old)  # Restore
    """
    global _global_settings

    old_settings = get_settings()
    current = _get_effective_settings()

    # Create new settings with updates
    new_values = {}
    for f in fields(NalystSettings):
        new_val = locals().get(f.name)
        if new_val is not None:
            new_values[f.name] = new_val
        else:
            new_values[f.name] = getattr(current, f.name)

    new_settings = NalystSettings(**new_values)

    if _thread_local_settings.stack:
        _thread_local_settings.stack[-1] = new_settings
    else:
        _global_settings = new_settings

    return old_settings


@contextmanager
def settings_context(
    assume_finite: Optional[bool] = None,
    working_memory: Optional[int] = None,
    print_changed_only: Optional[bool] = None,
    repr_decimals: Optional[int] = None,
    array_output: Optional[Literal["default", "pandas", "polars"]] = None,
    transform_output: Optional[Literal["default", "pandas", "polars"]] = None,
    parallel_backend: Optional[str] = None,
    n_jobs: Optional[int] = None,
    random_state: Optional[int] = None,
    enable_cython_pairwise_dist: Optional[bool] = None,
    skip_param_validation: Optional[bool] = None,
    display: Optional[Literal["text", "diagram"]] = None,
    pairwise_dist_chunk_size: Optional[int] = None,
) -> Iterator[None]:
    """
    Context manager for temporary settings changes.

    Changes are automatically reverted when exiting the context.
    This is thread-safe; settings in one thread don't affect others.

    Parameters
    ----------
    assume_finite : bool, optional
        Skip validation for finite values.
    working_memory : int, optional
        Target working memory in MB.
    print_changed_only : bool, optional
        Only show changed params in repr.
    repr_decimals : int, optional
        Decimal places in repr.
    array_output : {"default", "pandas", "polars"}, optional
        Output format for arrays.
    transform_output : {"default", "pandas", "polars"}, optional
        Output format for transforms.
    parallel_backend : str, optional
        Default parallel backend.
    n_jobs : int, optional
        Default number of jobs.
    random_state : int, optional
        Default random state.
    enable_cython_pairwise_dist : bool, optional
        Use optimized Cython code.
    skip_param_validation : bool, optional
        Skip param validation.
    display : {"text", "diagram"}, optional
        Display mode in notebooks.
    pairwise_dist_chunk_size : int, optional
        Chunk size for pairwise distances.

    Yields
    ------
    None

    Examples
    --------
    >>> from nalyst.core import settings_context, get_settings
    >>> with settings_context(assume_finite=True):
    ...     print(get_settings()['assume_finite'])
    True
    >>> print(get_settings()['assume_finite'])
    False
    """
    current = _get_effective_settings()

    # Build new settings with overrides
    new_values = {}
    for f in fields(NalystSettings):
        local_val = locals().get(f.name)
        if local_val is not None:
            new_values[f.name] = local_val
        else:
            new_values[f.name] = getattr(current, f.name)

    new_settings = NalystSettings(**new_values)
    _thread_local_settings.stack.append(new_settings)

    try:
        yield
    finally:
        _thread_local_settings.stack.pop()


def reset_settings() -> None:
    """
    Reset all settings to their default values.

    This only affects global settings, not thread-local contexts.
    """
    global _global_settings
    _global_settings = NalystSettings()


# Environment variable configuration
def _init_from_environment() -> None:
    """Initialize settings from environment variables."""
    env_mapping = {
        "NALYST_ASSUME_FINITE": ("assume_finite", lambda x: x.lower() == "true"),
        "NALYST_WORKING_MEMORY": ("working_memory", int),
        "NALYST_N_JOBS": ("n_jobs", lambda x: int(x) if x.lower() != "none" else None),
        "NALYST_RANDOM_STATE": ("random_state", lambda x: int(x) if x.lower() != "none" else None),
    }

    updates = {}
    for env_var, (setting_name, converter) in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None:
            try:
                updates[setting_name] = converter(value)
            except (ValueError, TypeError):
                pass  # Ignore invalid environment values

    if updates:
        set_settings(**updates)


# Initialize from environment on import
_init_from_environment()
