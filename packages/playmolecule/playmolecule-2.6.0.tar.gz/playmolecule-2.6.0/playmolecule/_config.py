# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Centralized configuration from environment variables."""

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class _Config:
    """Configuration loaded from environment variables.

    Attributes
    ----------
    app_root : str or None
        Root path for apps (PM_APP_ROOT). Can be a local path, HTTP URL, or docker://
    queue_config : dict or None
        Queue configuration (PM_QUEUE_CONFIG) parsed from JSON
    symlink : bool
        Whether to use symlinks for input files (PM_SYMLINK)
    blocking : bool
        Whether to run jobs in blocking mode (PM_BLOCKING)
    backend_headers : dict
        HTTP headers for backend requests (PM_BACKEND_HEADERS)
    job_dir_prefix : str
        Prefix for job directories (PM_JOB_DIR_PREFIX)
    working_dir : str
        Working directory for relative paths (PM_WORKING_DIR)
    skip_setup : bool
        Whether to skip setup (PM_SKIP_SETUP)
    """

    app_root: Optional[str] = None
    queue_config: Optional[dict] = field(default=None)
    symlink: bool = False
    blocking: bool = False
    backend_headers: dict = field(default_factory=dict)
    job_dir_prefix: str = ""
    working_dir: Optional[str] = None
    skip_setup: bool = False


def _load_config() -> _Config:
    """Load configuration from environment variables.

    Returns
    -------
    _Config
        Configuration object with values from environment
    """
    app_root = os.environ.get("PM_APP_ROOT", None)

    # Normalize app_root - remove trailing slashes
    if app_root is not None:
        while app_root.endswith("/"):
            app_root = app_root[:-1]

    queue_config = None
    pm_queue_config = os.environ.get("PM_QUEUE_CONFIG", None)
    if pm_queue_config is not None:
        queue_config = json.loads(pm_queue_config)

    backend_headers = {}
    pm_backend_headers = os.environ.get("PM_BACKEND_HEADERS", None)
    if pm_backend_headers is not None:
        backend_headers = json.loads(pm_backend_headers)

    working_dir = None
    if "PM_WORKING_DIR" in os.environ:
        working_dir = os.path.abspath(os.environ["PM_WORKING_DIR"])

    return _Config(
        app_root=app_root,
        queue_config=queue_config,
        symlink="PM_SYMLINK" in os.environ,
        blocking=os.environ.get("PM_BLOCKING", "0") == "1",
        backend_headers=backend_headers,
        job_dir_prefix=os.environ.get("PM_JOB_DIR_PREFIX", ""),
        working_dir=working_dir,
        skip_setup=bool(os.environ.get("PM_SKIP_SETUP", False)),
    )


# Global config instance - lazily initialized
_config: Optional[_Config] = None


def _get_config() -> _Config:
    """Get the global configuration instance.

    Returns
    -------
    _Config
        The global configuration object
    """
    global _config
    if _config is None:
        _config = _load_config()
    return _config


def _reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
