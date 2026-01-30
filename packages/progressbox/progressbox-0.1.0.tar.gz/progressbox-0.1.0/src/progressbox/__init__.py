"""
ProgressBox - Stage-aware progress monitoring for parallel Python jobs.

A progress tracking library designed for data science and machine learning
workflows with support for parallel processing, stage timing, and rich
terminal displays.

Quick Start:
    >>> from progressbox import Progress, Config
    >>>
    >>> config = Config(total=100, n_workers=4)
    >>> with Progress(config) as progress:
    ...     for i in range(100):
    ...         progress.task_start(f"task_{i}")
    ...         # ... do work ...
    ...         progress.task_finish(f"task_{i}")

With Stages:
    >>> with Progress(config) as progress:
    ...     for i in range(100):
    ...         progress.task_start(f"task_{i}")
    ...         progress.task_update(f"task_{i}", stage="loading")
    ...         # ... load data ...
    ...         progress.task_update(f"task_{i}", stage="processing")
    ...         # ... process data ...
    ...         progress.task_finish(f"task_{i}")

With Callbacks:
    >>> def on_complete(snapshot):
    ...     print(f"Completed {snapshot['completed']} tasks")
    >>>
    >>> config = Config(total=100, on_complete=on_complete)
    >>> with Progress(config) as progress:
    ...     # ... process tasks ...
    ...     pass

For Joblib Integration:
    >>> from progressbox.adapters import joblib_progress
    >>> from joblib import Parallel, delayed
    >>>
    >>> with joblib_progress(total=100) as progress:
    ...     results = Parallel(n_jobs=4)(
    ...         delayed(process)(i) for i in range(100)
    ...     )
"""

from progressbox.core import Progress
from progressbox.config import Config, BarChars, create_default_config
from progressbox.state import ProgressState, TaskInfo

__version__ = "0.1.0"
__all__ = [
    # Core classes
    "Progress",
    "Config",
    "ProgressState",
    "TaskInfo",
    # Config helpers
    "BarChars",
    "create_default_config",
    # IPC components (lazy loaded)
    "Reporter",
    "consume",
    "Manager",
]


def __getattr__(name):
    """Lazy import for IPC components to avoid side-effects.

    The IPC components (Reporter, consume, Manager) are only loaded
    when explicitly accessed, keeping the base import lightweight.
    """
    if name in {"Reporter", "consume", "Manager"}:
        from importlib import import_module

        if name == "Reporter":
            return import_module("progressbox.ipc.reporter").Reporter
        if name == "consume":
            return import_module("progressbox.ipc.queue").consume
        if name == "Manager":
            return import_module("progressbox.ipc.manager").Manager

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
