# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Shared argument validation logic."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from playmolecule._appfiles import _File

logger = logging.getLogger(__name__)


# Type validators mapping type names to accepted Python types
_VALIDATORS = {
    "str": str,
    "Path": (str, Path, _File),
    "bool": bool,
    "int": (int, float),
    "float": (int, float),
    "dict": dict,
}


def _validate_argument_type(
    name: str, value: Any, argtype: str, nargs: Optional[int]
) -> List[Any]:
    """Validate a single argument's type and convert to list format.

    Parameters
    ----------
    name : str
        Argument name
    value : Any
        Argument value
    argtype : str
        Expected type string
    nargs : int or None
        Number of expected arguments (None for single value)

    Returns
    -------
    list
        Value(s) as a list

    Raises
    ------
    RuntimeError
        If validation fails
    """
    # Check if multiple values were passed when single expected
    if nargs is None and isinstance(value, (list, tuple)):
        raise RuntimeError(
            f"Argument '{name}' was passed value '{value}' which is of type "
            f"'{type(value).__name__}'. Was expecting a single value of type '{argtype}'."
        )

    # Convert to list for uniform processing
    vals = value if isinstance(value, (list, tuple)) else [value]

    # Validate type
    if argtype in _VALIDATORS:
        validator = _VALIDATORS[argtype]
        for val in vals:
            if val is not None and not isinstance(val, validator):
                raise RuntimeError(
                    f"Argument '{name}' was passed value '{val}' which is of type "
                    f"'{type(val).__name__}'. Was expecting value of type '{argtype}'."
                )
    else:
        logger.warning(
            f"Could not find validator for type: {argtype}. "
            "Please notify the PM developers."
        )

    return vals


def _validate_arguments(
    arguments: Dict[str, Any], manifest: dict
) -> List[Tuple[str, List[Any], str, Optional[int]]]:
    """Validate all arguments against manifest specification.

    Parameters
    ----------
    arguments : dict
        Dictionary of argument name -> value
    manifest : dict
        Manifest containing 'params' list with argument specifications

    Returns
    -------
    list of tuples
        Each tuple contains (name, values_list, argtype, nargs)

    Raises
    ------
    RuntimeError
        If validation fails
    """
    validated = []

    for arg in manifest["params"]:
        name = arg["name"]
        argtype = arg["type"]
        nargs = arg.get("nargs")

        if name not in arguments:
            continue

        vals = _validate_argument_type(name, arguments[name], argtype, nargs)
        validated.append((name, vals, argtype, nargs))

    return validated


def _resolve_app_file_uri(value: str, app_files: dict) -> Any:
    """Resolve an app://files URI to the actual file object.

    Parameters
    ----------
    value : str
        The URI string (e.g., "app://files/tests/input.pdb")
    app_files : dict
        Dictionary of available app files

    Returns
    -------
    _File or str
        The resolved file object or original string if not a URI
    """
    if isinstance(value, str) and value.startswith("app://files"):
        key = value.replace("app://files/", "")
        if key in app_files:
            return app_files[key]
    return value


def _get_unique_output_path(base_path: str, original_paths: Dict[str, str]) -> str:
    """Get a unique output path, avoiding collisions.

    Parameters
    ----------
    base_path : str
        The desired output path
    original_paths : dict
        Mapping of output paths to original source paths

    Returns
    -------
    str
        A unique output path
    """
    if not os.path.exists(base_path):
        return base_path

    # Check if it's the same source file
    if base_path in original_paths:
        return base_path

    # Generate unique name
    i = 0
    while os.path.exists(base_path):
        parts = os.path.splitext(os.path.basename(base_path))
        dirname = os.path.dirname(base_path)
        base_path = os.path.join(dirname, f"{parts[0]}_{i}{parts[1]}")
        i += 1

    return base_path
