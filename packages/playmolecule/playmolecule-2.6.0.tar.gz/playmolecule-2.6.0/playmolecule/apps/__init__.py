# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
import os
from jinja2 import Environment as _JinjaEnvironment
from jinja2 import PackageLoader as _JinjaPackageLoader
from jinja2 import select_autoescape as _jinja_select_autoescape
from playmolecule._appfiles import _File, _Artifacts, _get_app_files
from playmolecule._tests import _Tests

# Do not remove unused imports. They are used in the jinja file probably
from pathlib import Path
import stat
import logging

logger = logging.getLogger(__name__)


_function_dict = {}


_env = _JinjaEnvironment(
    loader=_JinjaPackageLoader("playmolecule", "share"),
    autoescape=_jinja_select_autoescape(["*"]),
)


_JOB_TIMEOUT = 60  # Timeout after which if there is no newer date in .pm.alive we consider the job dead


class KWARGS(dict):
    pass


def _inner_function(
    args: dict,
    function_name: str,
    function_resources: dict,
    func_manifest: dict,
    slpm_path: str,
    files: dict,
    run_sh: str,
):
    from playmolecule._public_api import ExecutableDirectory, JobStatus
    from playmolecule._config import _get_config
    from playmolecule._backends import _get_execution_backend
    from playmolecule._backends._http import _HTTPExecutionBackend
    from datetime import datetime
    import uuid
    import os

    config = _get_config()

    assert (
        "outdir" in args or "execdir" in args
    ), "Functions must accept either 'outdir' or 'execdir'"

    if "outdir" in args:
        outdir = args["outdir"]
        args["outdir"] = "."
    elif "execdir" in args:
        if isinstance(args["execdir"], _File):
            args["execdir"] = args["execdir"].path
        outdir = args["execdir"]
        args["execdir"] = "."

    # Get execution backend
    backend = _get_execution_backend(config.app_root)

    # HTTP backend path
    if isinstance(backend, _HTTPExecutionBackend):
        input_dict = backend.prepare_inputs(args, func_manifest, files, slpm_path)
        ed = ExecutableDirectory(
            dirname=outdir,
            inputs_dir=outdir,
            _execution_resources=function_resources,
            _input_json=input_dict,
            _execution_backend=backend,
        )
        if not config.blocking:
            return ed
        else:
            import time

            ed.run()
            time.sleep(2)
            while ed.status not in (JobStatus.COMPLETED, JobStatus.ERROR):
                time.sleep(3)
            return None

    # Local execution path
    if "scratchdir" in args:
        if args["scratchdir"] is None:
            args["scratchdir"] = os.path.join(outdir, "scratch")
        os.makedirs(args["scratchdir"], exist_ok=True)

    now = datetime.now()
    identifier = f"_{now.strftime(r'%d_%m_%Y_%H_%M')}_{uuid.uuid4().hex[:8]}"
    inputs_dir = os.path.join(outdir, f"run{identifier}")

    # Use backend's prepare_inputs
    backend.prepare_inputs(
        outdir, inputs_dir, args, func_manifest, files, function_name, slpm_path
    )

    target_run_sh = None
    if run_sh is not None and len(run_sh):
        target_run_sh = os.path.join(outdir, f"run{identifier}.sh")
        with open(target_run_sh, "w") as f:
            f.write(run_sh)
        st = os.stat(target_run_sh)
        os.chmod(target_run_sh, st.st_mode | stat.S_IEXEC)

    return ExecutableDirectory(
        dirname=outdir,
        inputs_dir=inputs_dir,
        _execution_resources=function_resources,
        _execution_backend=backend,
    )


def _docs_from_manifest(manifest, appname, appdir):
    from copy import deepcopy
    from glob import glob

    manifest = deepcopy(manifest)

    if "description" not in manifest:
        raise RuntimeError(
            "Missing the 'description' field in your app manifest with a description of the app."
        )

    docs = [manifest["description"], "", "Parameters", "----------"]
    for i, param in enumerate(manifest["params"]):
        pp = f"{param['name']} : {param['type']}"
        if "choices" in param and param["choices"] is not None:
            choices = '", "'.join(param["choices"])
            pp += f', choices=("{choices}")'
        docs.append(pp)
        docs.append(f"    {param['description']}")

    missing = []

    if "outputs" in manifest:
        docs.append("")
        docs.append("Outputs")
        docs.append("-------")
        for key, val in manifest["outputs"].items():
            docs.append(key)
            docs.append(f"    {val}")
    else:
        missing.append("outputs")

    if "resources" in manifest and manifest["resources"] is not None:
        docs.append("")
        docs.append("Note")
        docs.append("----")
        docs.append("Minimum job requirements::")
        docs.append("")
        for key, val in manifest["resources"].items():
            docs.append(f"    {key}: {val}")

    if "examples" in manifest:
        docs.append("")
        docs.append("Examples")
        docs.append("--------")
        for exp in manifest["examples"]:
            docs.append(f">>> {exp}")
    else:
        missing.append("examples")

    if "tests" in manifest:
        for test_name in manifest["tests"]:
            desc = manifest["tests"][test_name]["description"]
            args = manifest["tests"][test_name]["arguments"]
            args_str = ""
            for key, vals in args.items():
                if not isinstance(vals, (list, tuple)):
                    vals = [vals]
                for i in range(len(vals)):
                    val = vals[i]
                    if isinstance(val, str):
                        if val.startswith("tests/"):
                            val = f"{appname}.files['{val}']"
                        elif val.startswith("datasets/"):
                            val = val.replace("datasets/", "")
                            val = f"{appname}.datasets.{val}"
                        elif val.startswith("artifacts/"):
                            val = val.replace("artifacts/", "")
                            val = f"{appname}.artifacts.{val}"
                        else:
                            val = f"'{val}'"
                    vals[i] = val
                if len(vals) > 1:
                    args_str += f"{key}=[{', '.join(map(str, vals))}], "
                else:
                    args_str += f"{key}={vals[0]}, "

            docs.append("")
            docs.append(desc)
            docs.append(f">>> {appname}(outdir='./out', {args_str[:-2]}).run()")

        if "examples" in missing:  # if there are tests don't complain about examples
            missing.remove("examples")

    if appdir is not None:
        tutorials = glob(os.path.join(appdir, "tutorials", "*"))
        if len(tutorials):
            docs.append("")
            docs.append("Notes")
            docs.append("-----")
            docs.append("Tutorials are available for this app:")
            docs.append("")
            for fname in tutorials:
                docs.append(f"    - {fname}")

    if len(missing):
        logger.warning(f"{appname} manifest is missing fields: {', '.join(missing)}")
    return docs


def _args_from_manifest(func_args):
    # Fix for old apps
    fix_old_types = {"string": "str", "file": "Path"}

    # Arguments which don't have a "value" field should be mandatory
    for arg in func_args:
        if "mandatory" not in arg:
            arg["mandatory"] = "value" not in arg

    args = []
    # Ensure mandaroty args come first if someone messes up the manifest
    mand_params = [x for x in func_args if x["mandatory"]]
    opt_params = [x for x in func_args if not x["mandatory"]]

    params = mand_params + opt_params
    for i, param in enumerate(params):
        atype = param["type"]
        if atype in fix_old_types:
            atype = fix_old_types[atype]
        if atype == "str_to_bool":
            atype = "bool"

        atype_final = atype
        if "nargs" in param and param["nargs"] is not None:
            atype_final = f"list[{atype}]"

        argstr = f"{param['name']} : {atype_final}"

        if not param["mandatory"]:
            default = param["value"]

            if atype in ("str", "Path") and param["value"] is not None:
                if isinstance(default, (list, tuple)):
                    for k in range(len(default)):
                        if default[k].startswith("app://files"):
                            # Handle app://files URIs
                            default[k] = (
                                f"files['{default.replace('app://files/', '')}']"
                            )
                elif default.startswith("app://files"):
                    # Handle app://files URIs
                    default = f"files['{default.replace('app://files/', '')}']"
                else:
                    default = f"\"{param['value']}\""

            # Fix for old apps
            if atype not in ("str", "Path") and param["value"] == "":
                default = None

            argstr += f" = {default}"

        if i != len(params) - 1:
            argstr += ","
        args.append(argstr)
    return args


def __ensure_module_path(module_path):
    """
    Ensures that all parts of the dotted module path exist in sys.modules
    and returns the final module object.
    """
    import sys
    import types

    parts = module_path.split(".")
    full_path = ""
    parent = None

    for part in parts:
        full_path = f"{full_path}.{part}" if full_path else part
        if full_path not in sys.modules:
            mod = types.ModuleType(full_path)
            sys.modules[full_path] = mod
            if parent:
                setattr(parent, part, mod)
        parent = sys.modules[full_path]

    return sys.modules[full_path]


def _manifest_to_func(appname, app_versions):
    from copy import deepcopy

    template = _env.get_template("func.py.jinja")

    for version in app_versions:
        manifest = app_versions[version]["manifest"]
        new_mode = True
        if (
            "functions" not in manifest
        ):  # TODO: Deprecate eventually. Just for backwards compatibility
            new_mode = False
            manifest = deepcopy(manifest)
            try:
                manifest["functions"] = [
                    {
                        "function": (
                            manifest["container_config"]["appfunction"]
                            if "container_config" in manifest
                            else "main"
                        ),
                        "env": "base",
                        "resources": manifest.get("resources", None),
                        "examples": manifest.get("examples", []),
                        "params": manifest["params"],
                        "tests": manifest.get("tests", {}),
                        "outputs": manifest.get("outputs", {}),
                        "description": manifest["description"],
                    }
                ]
            except Exception:
                import traceback

                logger.error(
                    f"Failed to parse manifest for app {appname} version {version} due to error:\n{traceback.format_exc()}"
                )
                continue

        module_path = f"playmolecule.apps.{appname}.{version}"
        module = __ensure_module_path(module_path)

        setattr(module, "__manifest__", deepcopy(manifest))

        if app_versions[version].get("run.sh") is not None:
            with open(app_versions[version].get("run.sh"), "r") as f:
                run_sh = f.read()
            setattr(module, "__runsh", run_sh)
        else:
            setattr(module, "__runsh", None)

        app_artifacts = None
        source_dir = app_versions[version].get("appdir")
        if source_dir is not None:
            source_dir = os.path.join(source_dir, "files")
        app_files = _get_app_files(source_dir, manifest)
        setattr(module, "files", app_files)

        artifact_dict = manifest.get("artifacts", manifest.get("datasets", {}))
        if len(artifact_dict):
            app_artifacts = _Artifacts(artifact_dict, app_files)
            setattr(module, "artifacts", app_artifacts)
            setattr(module, "datasets", app_artifacts)

        func_names = []
        for idx, func_mani in enumerate(manifest["functions"]):
            try:
                func_name = func_mani["function"].split(".")[-1]
                if func_name == "main":
                    func_name = appname

                code = template.render(
                    function=func_mani["function"],
                    function_idx=idx,
                    function_name=func_name,
                    function_args=_args_from_manifest(func_mani["params"]),
                    function_docs=_docs_from_manifest(
                        func_mani, appname, app_versions[version]["appdir"]
                    ),
                    function_resources=func_mani.get("resources", None),
                    module_path=module_path,
                    slpm_path=f"{appname}.{version}.{func_name}",
                )
                local_ns = {"files": app_files}
                exec(code, globals().copy(), local_ns)
                _func = local_ns[func_name]

                tests = _Tests(func_mani["tests"], _func, app_files, app_artifacts)
                # Add some metadata to the function object
                _func.tests = tests
                _func._name = func_name
                _func.__manifest__ = deepcopy(func_mani)
                func_names.append(func_name)
                setattr(module, func_name, _func)
                _function_dict[f"{module_path}.{func_name}"] = _func
            except Exception:
                import traceback

                logger.error(
                    f"Failed to parse manifest for app {appname} version {version} with error: {traceback.format_exc()}"
                )
    return func_names


def _link_latest_version(appname, latest, func_names):
    import sys

    # Link the latest version of the app to the top level module
    parent_module = sys.modules[f"playmolecule.apps.{appname}"]
    latest_module = sys.modules[f"playmolecule.apps.{appname}.{latest}"]
    for symbol in func_names + [
        "artifacts",
        "datasets",
        "files",
        "tests",
        "__manifest__",
    ]:
        if symbol not in parent_module.__dict__ and symbol in latest_module.__dict__:
            setattr(
                sys.modules[f"playmolecule.apps.{appname}"],
                symbol,
                getattr(
                    sys.modules.get(f"playmolecule.apps.{appname}.{latest}"), symbol
                ),
            )


def _set_root(root_dir):
    """Set the root directory for apps using the backend registry."""
    from natsort import natsorted
    import playmolecule
    from playmolecule._backends import _get_manifest_backend
    from playmolecule._backends._local import _LocalManifestBackend

    logger.info(f"Setting PlayMolecule source to {root_dir}")

    # Get the appropriate manifest backend
    backend = _get_manifest_backend(root_dir)

    if backend is None:
        raise RuntimeError(f"No backend found for root: {root_dir}")

    app_manifests = backend.get_apps()
    for appname in app_manifests:
        func_names = _manifest_to_func(appname, app_manifests[appname])
        versions = list(app_manifests[appname].keys())
        versions.sort(key=lambda s: natsorted(s))
        _link_latest_version(appname, versions[-1], func_names)

    # HTTP and Docker backends handle everything internally
    if isinstance(backend, _LocalManifestBackend):
        backend.set_global_datasets(playmolecule)
