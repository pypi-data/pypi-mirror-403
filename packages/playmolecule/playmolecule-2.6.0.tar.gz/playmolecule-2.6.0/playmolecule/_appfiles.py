# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
from typing import Dict, List, Optional


class _Artifacts:
    """Container for app artifacts/datasets."""

    def __init__(self, artifacts: List[dict], files_dict: Dict[str, "_File"]) -> None:
        import os

        searchpaths = [
            ["datasets"],
            ["artifacts"],
            ["files", "datasets"],
            ["files", "artifacts"],
            [],
        ]

        for ds in artifacts:
            path = None
            for sp in searchpaths:
                path = os.path.join(*sp, ds["path"])
                if path in files_dict:
                    break

            if path is None:
                raise RuntimeError(
                    f"Could not find dataset {ds['name']} at path {path}"
                )

            try:
                if "." in ds["name"]:
                    raise RuntimeError(
                        f"Dataset/artifact names cannot include dots in the name. {ds['name']} contains a dot."
                    )
                if not ds["name"][0].isalpha():
                    raise RuntimeError(
                        f"Dataset/artifact names must start with a letter. {ds['name']} does not."
                    )
                setattr(
                    self,
                    ds["name"],
                    _File(ds["name"], files_dict[path].path, ds["description"]),
                )
            except Exception:
                pass

    def __str__(self) -> str:
        descr = ""
        for key in self.__dict__:
            descr += f"{self.__dict__[key]}\n"
        return descr

    def __repr__(self) -> str:
        return self.__str__()


class _File:
    """Represents a file in an app's files directory."""

    def __init__(self, name: str, path: str, description: Optional[str] = None) -> None:
        self.name = name
        self.path = path
        self.description = description

    def __str__(self) -> str:
        string = f"[{self.name}] {self.path}"
        if self.description is not None:
            string += f" '{self.description}'"
        return string

    def __repr__(self) -> str:
        return self.__str__()


def _get_app_files(
    source_dir: Optional[str], manifest: Optional[dict] = None
) -> Dict[str, _File]:
    """Get app files for the current backend.

    This function delegates to the appropriate backend based on PM_APP_ROOT.

    Parameters
    ----------
    source_dir : str or None
        Source directory for local files
    manifest : dict, optional
        App manifest (required for HTTP/Docker backends)

    Returns
    -------
    dict
        Dictionary mapping filename to _File objects
    """
    from glob import glob
    import os

    # Try to get PM_APP_ROOT, but handle cases where it's not set
    try:
        from playmolecule import PM_APP_ROOT
    except (ImportError, RuntimeError):
        PM_APP_ROOT = None

    # HTTP and Docker backends use manifest-based file lookup
    if PM_APP_ROOT and PM_APP_ROOT.startswith(("http", "docker")):
        from playmolecule._backends import _get_manifest_backend

        backend = _get_manifest_backend(PM_APP_ROOT)
        if backend is not None:
            return backend.get_app_files(manifest)

    # Local backend - scan the filesystem
    files: Dict[str, _File] = {}

    if source_dir is None:
        return files

    for ff in glob(os.path.join(source_dir, "**", "*"), recursive=True):
        fname = os.path.relpath(ff, source_dir)
        abspath = os.path.abspath(ff)
        files[fname] = _File(fname, abspath)

    return files
