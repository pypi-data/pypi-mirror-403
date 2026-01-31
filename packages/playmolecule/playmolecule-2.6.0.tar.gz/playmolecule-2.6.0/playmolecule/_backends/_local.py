# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Local filesystem manifest and execution backend."""

import datetime
import json
import logging
import os
import shutil
import stat
from glob import glob
from typing import Any, Dict, List, Optional
from types import ModuleType
from jinja2 import Environment, PackageLoader, select_autoescape
from playmolecule._appfiles import _File, _get_app_files
from playmolecule._config import _get_config
from playmolecule._validation import _VALIDATORS, _validate_argument_type
from playmolecule._public_api import JobStatus

logger = logging.getLogger(__name__)

JOB_TIMEOUT = 60  # Timeout in seconds for heartbeat

env = Environment(
    loader=PackageLoader("playmolecule", "share"),
    autoescape=select_autoescape(["*"]),
)


class _LocalManifestBackend:
    """Backend for loading app manifests from local filesystem."""

    def __init__(self, root: str):
        """Initialize the local manifest backend.

        Parameters
        ----------
        root : str
            Root directory containing apps
        """
        self.root = root

    def get_apps(self) -> Dict[str, Dict[str, dict]]:
        """Get all available apps from local filesystem.

        Returns
        -------
        dict
            Nested dict: {appname: {version: {"manifest": ..., "appdir": ..., "run.sh": ...}}}
        """
        from natsort import natsorted

        apps = {}

        for app_d in natsorted(glob(os.path.join(self.root, "apps", "*", ""))):
            appname = os.path.basename(os.path.abspath(app_d))
            if not self._check_folder_validity(app_d):
                continue

            versions = glob(os.path.join(app_d, "*"))
            versions.sort(key=lambda s: natsorted(os.path.basename(s)))

            app_versions = {}
            for vv in versions:
                vname = os.path.basename(vv)
                if not self._check_folder_validity(vv):
                    continue

                jf = glob(os.path.join(vv, "*.json"))
                if len(jf) > 1:
                    logger.error(f"Multiple json files found in {vv}")
                    continue
                if len(jf) == 1 and os.stat(jf[0]).st_size != 0:
                    try:
                        with open(jf[0]) as f:
                            app_versions[vname] = {
                                "manifest": json.load(f),
                                "appdir": vv,
                                "run.sh": os.path.join(vv, "run.sh"),
                            }
                    except Exception as e:
                        logger.error(
                            f"Failed at parsing manifest JSON file {jf[0]} with error: {e}"
                        )

            if app_versions:
                apps[appname] = app_versions

        return apps

    def get_app_files(self, manifest: dict, appdir: Optional[str] = None) -> dict:
        """Get files associated with an app.

        Parameters
        ----------
        manifest : dict
            The app manifest
        appdir : str, optional
            The app directory

        Returns
        -------
        dict
            Dictionary of filename -> _File objects
        """
        source_dir = None
        if appdir is not None:
            source_dir = os.path.join(appdir, "files")
        return _get_app_files(source_dir, manifest)

    def _check_folder_validity(self, app_d: str) -> bool:
        """Check if folder path has valid characters."""
        import re

        folder_path = os.path.relpath(app_d, self.root)

        # Check if the folder consists only of lowercase letters, numbers, underscores or path separators
        if not re.match(r"^[a-z0-9_/\\]+$", folder_path):
            logger.warning(
                f'Path {app_d} has invalid characters in the part: "{folder_path}". '
                "Only lowercase letters, numbers and underscores are allowed. "
                "Please fix the path. Skipping..."
            )
            return False
        return True

    def set_global_datasets(self, playmolecule: ModuleType):
        """Set the global datasets for the local backend."""
        from playmolecule._appfiles import _Artifacts

        dsdir = os.path.join(self.root, "datasets")
        dsjson = os.path.join(dsdir, "datasets.json")
        if os.path.exists(dsdir) and os.path.exists(dsjson):
            with open(dsjson) as f:
                manifest = json.load(f)
            files = _get_app_files(dsdir)
            playmolecule.datasets = _Artifacts(manifest["datasets"], files)


class _LocalExecutionBackend:
    """Backend for executing apps locally."""

    def __init__(self, root: str):
        """Initialize the local execution backend.

        Parameters
        ----------
        root : str
            Root directory containing apps
        """
        self.root = root

    def prepare_inputs(
        self,
        write_dir: str,
        inputs_dir: str,
        arguments: dict,
        manifest: dict,
        app_files: dict,
        function: str,
        slpm_path: str,
    ) -> None:
        """Prepare inputs for local execution.

        This copies/symlinks input files to the inputs directory and
        writes the inputs.json file.

        Parameters
        ----------
        write_dir : str
            Output directory
        inputs_dir : str
            Directory to write inputs to
        arguments : dict
            Function arguments
        manifest : dict
            Function manifest
        app_files : dict
            App files dictionary
        function : str
            Function name
        slpm_path : str
            The slpm path
        """
        config = _get_config()
        os.makedirs(inputs_dir, exist_ok=True)

        if "outputs" in manifest:
            with open(os.path.join(inputs_dir, "expected_outputs.json"), "w") as f:
                json.dump(manifest["outputs"], f)

        # Track original paths for deduplication
        original_paths = {}

        # Validate and process arguments
        for arg in manifest["params"]:
            name = arg["name"]
            argtype = arg["type"]
            nargs = arg.get("nargs")

            vals = arguments.get(name)
            if vals is None:
                continue

            # Validate type
            vals = _validate_argument_type(name, vals, argtype, nargs)

            # Copy Path-type arguments to folder
            if argtype == "Path" and name not in ("outdir", "scratchdir", "execdir"):
                newvals = self._process_path_arguments(
                    vals,
                    app_files,
                    inputs_dir,
                    write_dir,
                    original_paths,
                    config.symlink,
                )
                arguments[name] = self._normalize_values(newvals)

            # Handle KWARGS type (for HTMD app)
            if argtype == "KWARGS" and vals[0] is not None:
                self._process_kwargs_arguments(
                    vals[0], inputs_dir, write_dir, original_paths, config.symlink
                )
                arguments[name] = vals[0]

        # Write inputs.json
        with open(os.path.join(inputs_dir, "inputs.json"), "w") as f:
            json.dump(
                {"function": function, "slpm_path": slpm_path, "arguments": arguments},
                f,
                indent=4,
            )

        # Write original_paths.json
        with open(os.path.join(inputs_dir, "original_paths.json"), "w") as f:
            json.dump(original_paths, f, indent=4)

    def _process_path_arguments(
        self,
        vals: list,
        app_files: dict,
        inputs_dir: str,
        write_dir: str,
        original_paths: dict,
        use_symlink: bool,
    ) -> list:
        """Process Path-type arguments, copying files to inputs directory."""
        newvals = []

        for val in vals:
            if val is None or (isinstance(val, str) and val == ""):
                continue

            # Handle app://files URIs
            if isinstance(val, str) and val.startswith("app://files"):
                val = app_files[val.replace("app://files/", "")]

            if isinstance(val, _File):
                newvals.append(val.path)
                continue  # Don't copy artifacts

            val = os.path.abspath(val)

            # Deduplicate file names
            outname = os.path.join(inputs_dir, os.path.basename(val))
            if os.path.exists(outname) and val != original_paths.get(outname):
                i = 0
                while os.path.exists(outname):
                    parts = os.path.splitext(os.path.basename(val))
                    outname = os.path.join(inputs_dir, f"{parts[0]}_{i}{parts[1]}")
                    i += 1

            original_paths[outname] = val

            # Copy or symlink
            if use_symlink:
                os.symlink(val, outname)
            else:
                if os.path.isdir(val):
                    shutil.copytree(val, outname)
                else:
                    shutil.copy(val, outname)

            newvals.append(os.path.relpath(outname, write_dir))

        return newvals

    def _process_kwargs_arguments(
        self,
        kwargs_dict: dict,
        inputs_dir: str,
        write_dir: str,
        original_paths: dict,
        use_symlink: bool,
    ) -> None:
        """Process KWARGS type arguments (for HTMD app)."""
        for key, item_vals in kwargs_dict.items():
            if not isinstance(item_vals, (list, tuple)):
                item_vals = [item_vals]

            newvals = []
            for val in item_vals:
                if val is None:
                    continue

                if isinstance(val, _File):
                    newvals.append(val.path)
                    continue

                if not isinstance(val, str) or not os.path.exists(val):
                    newvals.append(val)
                    continue

                val = os.path.abspath(val)

                outname = os.path.join(inputs_dir, os.path.basename(val))
                if os.path.exists(outname) and val != original_paths.get(outname):
                    i = 0
                    while os.path.exists(outname):
                        parts = os.path.splitext(os.path.basename(val))
                        outname = os.path.join(inputs_dir, f"{parts[0]}_{i}{parts[1]}")
                        i += 1

                original_paths[outname] = val

                if use_symlink:
                    os.symlink(val, outname)
                else:
                    if os.path.isdir(val):
                        shutil.copytree(val, outname)
                    else:
                        shutil.copy(val, outname)
                newvals.append(os.path.relpath(outname, write_dir))

            kwargs_dict[key] = self._normalize_values(newvals)

    def _normalize_values(self, vals: list) -> Any:
        """Normalize a list of values to single value or list."""
        if len(vals) == 0:
            return None
        elif len(vals) == 1:
            return vals[0]
        return vals

    def run(
        self,
        dirname: str,
        runsh: str,
        verbose: bool = True,
        **kwargs,
    ) -> None:
        """Run the app locally.

        Parameters
        ----------
        dirname : str
            Directory containing the run script
        runsh : str
            Run script filename
        verbose : bool
            Whether to print output
        **kwargs
            Ignored for local execution
        """
        import subprocess

        logfile_path = os.path.join(dirname, runsh.replace(".sh", ".log"))

        with open(logfile_path, "w") as logfile:
            process = subprocess.Popen(
                ["bash", runsh],
                cwd=dirname,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in process.stdout:
                if verbose:
                    print(line, end="")
                logfile.write(line)
            process.wait()
            if process.returncode != 0:
                raise RuntimeError(f"Job failed with exit code {process.returncode}")

    def get_status(
        self,
        dirname: str,
        inputs_dir: str,
        slurmq: Any = None,
    ) -> JobStatus:
        """Get job status for local execution.

        Parameters
        ----------
        dirname : str
            Output directory
        inputs_dir : str
            Directory containing inputs
        slurmq : SlurmQueue, optional
            SLURM queue object if submitted to SLURM

        Returns
        -------
        JobStatus
            Current job status
        """
        # Check for completion/error sentinel files
        if os.path.exists(os.path.join(inputs_dir, ".pm.done")) or os.path.exists(
            os.path.join(dirname, ".pm.done")
        ):
            return JobStatus.COMPLETED
        elif os.path.exists(os.path.join(inputs_dir, ".pm.err")) or os.path.exists(
            os.path.join(dirname, ".pm.err")
        ):
            return JobStatus.ERROR

        # Check heartbeat
        heartbeat = os.path.join(inputs_dir, ".pm.alive")
        if not os.path.exists(heartbeat):
            heartbeat = os.path.join(dirname, ".pm.alive")

        if os.path.exists(heartbeat):
            with open(heartbeat, "r") as f:
                timestamp_str = f.read().strip()
                timestamp = None

                if len(timestamp_str):
                    try:
                        timestamp = datetime.datetime.fromisoformat(timestamp_str)
                    except Exception:
                        logger.error(f"Malformed timestamp in {heartbeat}")

                if timestamp is not None:
                    diff = datetime.datetime.now() - timestamp
                    if diff > datetime.timedelta(seconds=JOB_TIMEOUT):
                        return JobStatus.ERROR
                    else:
                        return JobStatus.RUNNING

        # Check SLURM status
        if slurmq is not None:
            from playmolecule._backends._slurm import _get_slurm_status

            return _get_slurm_status(slurmq)

        # Check expected outputs
        outputs_file = os.path.join(inputs_dir, "expected_outputs.json")
        if os.path.exists(outputs_file):
            with open(outputs_file, "r") as f:
                outputs = json.load(f)

            for outf in outputs:
                if len(glob(os.path.join(dirname, outf))) == 0:
                    return JobStatus.RUNNING
            else:
                return JobStatus.COMPLETED

        logger.warning(
            f"Could not yet determine job status for directory {dirname}. "
            "The job might have not started running yet."
        )
        return JobStatus.WAITING_INFO


def setup_local_installation(root_dir: str):
    """Setup the local installation in the given root directory."""
    os.makedirs(root_dir, exist_ok=True)
    os.makedirs(os.path.join(root_dir, "apps"), exist_ok=True)
    os.makedirs(os.path.join(root_dir, "datasets"), exist_ok=True)

    apptainer_runner = os.path.join(root_dir, "apptainer_run.sh")
    if not os.path.exists(apptainer_runner):
        try:
            import questionary

            license_type = questionary.select(
                "Do you use a floating license server (IP/Port) or a license file?:",
                choices=["Floating License Server", "License File"],
                default="Floating License Server",
                use_shortcuts=True,
            ).unsafe_ask()
            if license_type == "Floating License Server":
                license_ip = questionary.text(
                    message="Type the IP/URL of the license server:"
                ).unsafe_ask()
                license_port = questionary.text(
                    message="Type the port of the license server:", default="27000"
                ).unsafe_ask()
                license_file = f"{license_port}@{license_ip}"
            else:
                license_file = questionary.path(
                    message="Path to license file:",
                ).unsafe_ask()
                new_lic_file = os.path.join(root_dir, "license.dat")
                if os.path.abspath(new_lic_file) != os.path.abspath(license_file):
                    shutil.copy(license_file, new_lic_file)
                license_file = new_lic_file
        except KeyboardInterrupt:
            raise RuntimeError("PlayMolecule setup cancelled...")

        template = env.get_template("apptainer_run.sh")
        fstring = template.render(
            license_file_or_server=license_file,
            root_dir=root_dir,
        )
        with open(apptainer_runner, "w") as f:
            f.write(fstring)

        st = os.stat(apptainer_runner)
        os.chmod(
            apptainer_runner, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )

        with open(os.path.join(root_dir, "license_path.txt"), "w") as f:
            f.write(license_file)

    if len(glob(os.path.join(root_dir, "apps", "*", ""))) == 0:
        from playmolecule._update import update_apps

        update_apps()
