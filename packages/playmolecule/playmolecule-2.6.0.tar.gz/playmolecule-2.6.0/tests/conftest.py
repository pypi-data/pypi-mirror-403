# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Pytest configuration and fixtures for test isolation."""

import pytest
import os
import sys


@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset module state before and after each test to ensure isolation."""
    # Save original environment
    old_env = dict(os.environ)

    # Save modules that might need to be reloaded
    saved_modules = {}
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("playmolecule"):
            saved_modules[mod_name] = sys.modules[mod_name]

    # Ensure PM_APP_ROOT is not set by default for tests
    os.environ.pop("PM_APP_ROOT", None)

    # Reset config to ensure it picks up the clean environment
    try:
        from playmolecule._config import _reset_config

        _reset_config()
    except Exception:
        pass

    yield

    # Reset config cache after test
    try:
        from playmolecule._config import _reset_config

        _reset_config()
    except Exception:
        pass

    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)

    # Remove modules that were not present before
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("playmolecule") and mod_name not in saved_modules:
            del sys.modules[mod_name]


@pytest.fixture
def clean_env():
    """Fixture that provides a clean environment for a test."""
    old_env = dict(os.environ)

    try:
        from playmolecule._config import _reset_config

        _reset_config()
    except Exception:
        pass

    yield os.environ

    os.environ.clear()
    os.environ.update(old_env)

    try:
        from playmolecule._config import _reset_config

        _reset_config()
    except Exception:
        pass
