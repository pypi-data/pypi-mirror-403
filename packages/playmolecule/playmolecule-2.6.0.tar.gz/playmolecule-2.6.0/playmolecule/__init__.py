# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
import os
import sys
import logging.config
from playmolecule.apps import _set_root
from playmolecule._backends._slurm import slurm_mps
from playmolecule._backends._local import setup_local_installation
from playmolecule._update import update_apps
from importlib.metadata import version as __version
from importlib.metadata import PackageNotFoundError
from playmolecule._protocols import __find_protocols
from playmolecule._config import _get_config
from playmolecule._public_api import JobStatus, ExecutableDirectory

# from importlib.resources import files

try:
    __version__ = __version("playmolecule")
except PackageNotFoundError:
    pass

dirname = os.path.dirname(__file__)

try:
    logging.config.fileConfig(
        os.path.join(dirname, "logging.ini"), disable_existing_loggers=False
    )
except Exception:
    print("playmolecule: Logging setup failed")


logger = logging.getLogger(__name__)

# Load configuration from environment
_config = _get_config()
PM_APP_ROOT = _config.app_root
PM_SKIP_SETUP = _config.skip_setup

if not PM_SKIP_SETUP:
    if PM_APP_ROOT is None:
        logger.warning(
            "Could not find environment variable PM_APP_ROOT. Please set the variable to set the path to the app root."
        )
    else:
        _set_root(PM_APP_ROOT)


# Requires PM_APP_ROOT to be set, otherwise we get circular import errors
from playmolecule._backends._http import login, logout, _check_login_status

if PM_APP_ROOT and PM_APP_ROOT.startswith("http"):
    _check_login_status()


def describe_apps(as_dict=False):
    from playmolecule.apps import _function_dict

    app_dict = {}
    sorted_keys = sorted(_function_dict.keys())
    for func_path in sorted_keys:
        func = _function_dict[func_path]
        if "name" in func.__manifest__:
            name = func.__manifest__["name"]
        else:
            name = func_path.split(".")[-1]
        app_dict[func_path] = {"description": func.__doc__.strip().split("\n")[0]}
        if not as_dict:
            print(name, func_path)
            desc = func.__doc__.strip().split("\n")[0]
            print(f"    {desc}")

    if as_dict:
        return app_dict


module = sys.modules[__name__]
setattr(module, "protocols", None)

# Add the acellera-protocols folder as a submodule
if not PM_SKIP_SETUP and PM_APP_ROOT is not None:
    setattr(module, "protocols", __find_protocols(PM_APP_ROOT, parent_module=__name__))
