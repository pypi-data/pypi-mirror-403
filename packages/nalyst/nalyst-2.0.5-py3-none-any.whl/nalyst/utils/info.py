"""
System information utilities.
"""

from __future__ import annotations

import sys
import platform
from typing import Optional


def show_info(show_all: bool = False) -> str:
    """
    Print useful debugging information.

    Parameters
    ----------
    show_all : bool, default=False
        If True, print all information including optional dependencies.

    Returns
    -------
    info : str
        Formatted system information string.

    Examples
    --------
    >>> from nalyst.utils import show_info
    >>> show_info()  # doctest: +SKIP
    """
    import nalyst

    lines = []
    lines.append("")
    lines.append("System:")
    lines.append("-" * 40)
    lines.append(f"    python: {sys.version}")
    lines.append(f"executable: {sys.executable}")
    lines.append(f"   machine: {platform.machine()}")
    lines.append(f"  platform: {platform.platform()}")
    lines.append("")
    lines.append("Python Dependencies:")
    lines.append("-" * 40)

    # Core dependencies
    try:
        import numpy
        lines.append(f"     numpy: {numpy.__version__}")
    except ImportError:
        lines.append("     numpy: Not installed")

    try:
        import scipy
        lines.append(f"     scipy: {scipy.__version__}")
    except ImportError:
        lines.append("     scipy: Not installed")

    try:
        import joblib
        lines.append(f"    joblib: {joblib.__version__}")
    except ImportError:
        lines.append("    joblib: Not installed")

    if show_all:
        lines.append("")
        lines.append("Optional Dependencies:")
        lines.append("-" * 40)

        try:
            import pandas
            lines.append(f"    pandas: {pandas.__version__}")
        except ImportError:
            lines.append("    pandas: Not installed")

        try:
            import matplotlib
            lines.append(f"matplotlib: {matplotlib.__version__}")
        except ImportError:
            lines.append("matplotlib: Not installed")

    lines.append("")
    lines.append("Nalyst:")
    lines.append("-" * 40)
    lines.append(f"    nalyst: {nalyst.__version__}")
    lines.append("")

    info = "\n".join(lines)
    print(info)
    return info
