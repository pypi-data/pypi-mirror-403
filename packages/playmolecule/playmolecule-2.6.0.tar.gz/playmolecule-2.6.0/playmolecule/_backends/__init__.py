# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Backend selection for PlayMolecule based on PM_APP_ROOT."""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playmolecule._backends._local import (
        _LocalManifestBackend,
        _LocalExecutionBackend,
    )
    from playmolecule._backends._http import _HTTPManifestBackend, _HTTPExecutionBackend
    from playmolecule._backends._docker import _DockerManifestBackend


def _get_manifest_backend(
    root: str,
) -> Optional["_LocalManifestBackend | _HTTPManifestBackend | _DockerManifestBackend"]:
    """Get a manifest backend instance based on PM_APP_ROOT.

    Parameters
    ----------
    root : str
        The app root path (PM_APP_ROOT)

    Returns
    -------
    ManifestBackend or None
        Backend instance, or None if root is None
    """
    if root is None:
        return None

    if root.startswith("http"):
        from playmolecule._backends._http import _HTTPManifestBackend

        return _HTTPManifestBackend(root)

    if root.startswith("docker"):
        from playmolecule._backends._docker import _DockerManifestBackend

        return _DockerManifestBackend(root)

    # Default: local filesystem
    from playmolecule._backends._local import _LocalManifestBackend

    return _LocalManifestBackend(root)


def _get_execution_backend(
    root: str,
) -> Optional["_LocalExecutionBackend | _HTTPExecutionBackend"]:
    """Get an execution backend instance based on PM_APP_ROOT.

    Parameters
    ----------
    root : str
        The app root path (PM_APP_ROOT)

    Returns
    -------
    ExecutionBackend or None
        Backend instance, or None if root is None
    """
    if root is None:
        return None

    if root.startswith("http"):
        from playmolecule._backends._http import _HTTPExecutionBackend

        return _HTTPExecutionBackend(root)

    # Docker and local both use local execution
    from playmolecule._backends._local import _LocalExecutionBackend

    return _LocalExecutionBackend(root)
