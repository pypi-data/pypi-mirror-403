"""
Formatting utilities for learner representations.

This module provides functions to create readable string and HTML
representations of learners and their parameters.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Type

import numpy as np


def format_learner(
    learner: Any,
    *,
    max_chars: int = 500,
    indent: int = 0,
) -> str:
    """
    Create a readable string representation of a learner.

    Parameters
    ----------
    learner : BaseLearner
        The learner to format.
    max_chars : int
        Maximum characters in output.
    indent : int
        Current indentation level.

    Returns
    -------
    str
        Formatted string representation.
    """
    from nalyst.core.settings import get_settings

    settings = get_settings()
    learner_name = type(learner).__name__

    try:
        params = learner.get_params(deep=False)
    except Exception:
        return f"{learner_name}()"

    if not params:
        return f"{learner_name}()"

    # Get default values if possible
    defaults = _get_default_params(type(learner))

    # Filter to changed params if setting enabled
    if settings.get("print_changed_only", True):
        params = {
            k: v for k, v in params.items()
            if k not in defaults or not _params_equal(v, defaults[k])
        }

    if not params:
        return f"{learner_name}()"

    # Format parameters
    param_strs = []
    for name, value in sorted(params.items()):
        value_str = _format_value(value, max_chars=max_chars // 2)
        param_strs.append(f"{name}={value_str}")

    # Try single line first
    single_line = f"{learner_name}({', '.join(param_strs)})"
    if len(single_line) <= max_chars:
        return single_line

    # Multi-line format
    indent_str = "  " * (indent + 1)
    params_formatted = f",\n{indent_str}".join(param_strs)
    return f"{learner_name}(\n{indent_str}{params_formatted})"


def _get_default_params(klass: Type) -> Dict[str, Any]:
    """Get default parameter values from class constructor."""
    import inspect

    try:
        sig = inspect.signature(klass.__init__)
        return {
            p.name: p.default
            for p in sig.parameters.values()
            if p.default is not inspect.Parameter.empty and p.name != "self"
        }
    except (ValueError, TypeError):
        return {}


def _params_equal(a: Any, b: Any) -> bool:
    """Check if two parameter values are equal."""
    # Handle numpy arrays
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        try:
            return np.array_equal(a, b)
        except (TypeError, ValueError):
            return False

    # Handle callables
    if callable(a) or callable(b):
        return a is b

    # Standard equality
    try:
        return a == b
    except (TypeError, ValueError):
        return a is b


def _format_value(value: Any, max_chars: int = 100) -> str:
    """Format a single parameter value."""
    from nalyst.core.settings import get_settings

    settings = get_settings()
    decimals = settings.get("repr_decimals", 3)

    if value is None:
        return "None"

    if isinstance(value, bool):
        return str(value)

    if isinstance(value, float):
        if np.isnan(value):
            return "nan"
        if np.isinf(value):
            return "inf" if value > 0 else "-inf"
        # Use scientific notation for very small/large numbers
        if abs(value) < 1e-4 or abs(value) > 1e6:
            return f"{value:.{decimals}e}"
        return f"{value:.{decimals}f}".rstrip("0").rstrip(".")

    if isinstance(value, (int, np.integer)):
        return str(value)

    if isinstance(value, str):
        return repr(value)

    if isinstance(value, np.ndarray):
        if value.size <= 10:
            return repr(value)
        return f"array(shape={value.shape}, dtype={value.dtype})"

    if hasattr(value, "get_params"):
        # Nested learner
        return format_learner(value, max_chars=max_chars // 2)

    if isinstance(value, (list, tuple)):
        if len(value) <= 5:
            items = [_format_value(v, max_chars // 5) for v in value]
            if isinstance(value, tuple):
                return f"({', '.join(items)})"
            return f"[{', '.join(items)}]"
        return f"[...{len(value)} items...]"

    if isinstance(value, dict):
        if len(value) <= 3:
            items = [f"{k!r}: {_format_value(v, max_chars // 5)}"
                     for k, v in value.items()]
            return "{" + ", ".join(items) + "}"
        return f"{{...{len(value)} items...}}"

    # Fallback
    result = repr(value)
    if len(result) > max_chars:
        return result[:max_chars - 3] + "..."
    return result


def learner_html_repr(learner: Any) -> str:
    """
    Create HTML representation for Jupyter notebooks.

    Parameters
    ----------
    learner : BaseLearner
        The learner to represent.

    Returns
    -------
    str
        HTML string for notebook display.
    """
    from nalyst.core.settings import get_settings

    settings = get_settings()
    display_mode = settings.get("display", "diagram")

    if display_mode == "text":
        text_repr = format_learner(learner)
        return f"<pre>{_escape_html(text_repr)}</pre>"

    # Diagram mode
    return _create_learner_diagram(learner)


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _create_learner_diagram(learner: Any) -> str:
    """Create a visual diagram for a learner."""
    from nalyst.core.tags import get_tags

    learner_name = type(learner).__name__
    tags = get_tags(learner)

    # Determine learner type badge
    type_badge = ""
    if tags.learner_type == "classifier":
        type_badge = '<span class="nl-badge nl-classifier">Classifier</span>'
    elif tags.learner_type == "regressor":
        type_badge = '<span class="nl-badge nl-regressor">Regressor</span>'
    elif tags.learner_type == "clusterer":
        type_badge = '<span class="nl-badge nl-clusterer">Clusterer</span>'
    elif tags.transformer_tags is not None:
        type_badge = '<span class="nl-badge nl-transformer">Transformer</span>'

    # Get parameters
    try:
        params = learner.get_params(deep=False)
    except Exception:
        params = {}

    # Check if trained
    is_trained = any(
        attr.endswith("_") and not attr.startswith("__")
        for attr in dir(learner)
    )
    trained_badge = (
        '<span class="nl-badge nl-trained">Trained</span>'
        if is_trained else
        '<span class="nl-badge nl-untrained">Not Trained</span>'
    )

    # Build parameters table
    params_html = ""
    if params:
        params_rows = []
        defaults = _get_default_params(type(learner))

        for name, value in sorted(params.items()):
            is_default = name in defaults and _params_equal(value, defaults[name])
            value_str = _format_value(value, max_chars=50)
            style = "color: #888;" if is_default else ""
            params_rows.append(
                f'<tr><td style="{style}">{name}</td>'
                f'<td style="{style}">{_escape_html(value_str)}</td></tr>'
            )

        params_html = f"""
        <details open>
            <summary style="cursor: pointer; font-weight: bold;">
                Parameters ({len(params)})
            </summary>
            <table class="nl-params-table">
                {''.join(params_rows)}
            </table>
        </details>
        """

    # CSS styles
    styles = """
    <style>
        .nl-container {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            background: #fafafa;
            max-width: 500px;
        }
        .nl-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }
        .nl-name {
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
        }
        .nl-badge {
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 500;
        }
        .nl-classifier { background: #e3f2fd; color: #1565c0; }
        .nl-regressor { background: #f3e5f5; color: #7b1fa2; }
        .nl-clusterer { background: #e8f5e9; color: #2e7d32; }
        .nl-transformer { background: #fff3e0; color: #e65100; }
        .nl-trained { background: #c8e6c9; color: #2e7d32; }
        .nl-untrained { background: #ffecb3; color: #ff8f00; }
        .nl-params-table {
            font-size: 0.9em;
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
        }
        .nl-params-table td {
            padding: 4px 8px;
            border-bottom: 1px solid #eee;
        }
        .nl-params-table td:first-child {
            font-weight: 500;
            width: 40%;
        }
    </style>
    """

    return f"""
    {styles}
    <div class="nl-container">
        <div class="nl-header">
            <span class="nl-name">{learner_name}</span>
            {type_badge}
            {trained_badge}
        </div>
        {params_html}
    </div>
    """


def format_time(seconds: float) -> str:
    """
    Format a duration in human-readable form.

    Parameters
    ----------
    seconds : float
        Duration in seconds.

    Returns
    -------
    str
        Formatted duration string.
    """
    if seconds < 0.001:
        return f"{seconds * 1e6:.1f}s"
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    if seconds < 60:
        return f"{seconds:.2f}s"
    if seconds < 3600:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}h {mins}m"


def format_memory(bytes_: int) -> str:
    """
    Format memory size in human-readable form.

    Parameters
    ----------
    bytes_ : int
        Size in bytes.

    Returns
    -------
    str
        Formatted size string.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(bytes_) < 1024:
            return f"{bytes_:.1f}{unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f}PB"
