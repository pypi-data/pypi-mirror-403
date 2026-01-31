from pathlib import Path
import os


class SleepException(Exception):
    pass


def report_alive(sentinel_dir):
    from datetime import datetime
    import time

    sentinel_dir = os.path.abspath(sentinel_dir)
    os.makedirs(sentinel_dir, exist_ok=True)

    while True:
        try:
            with open(os.path.join(sentinel_dir, ".pm.alive"), "w") as f:
                f.write(datetime.now().isoformat())
        except Exception:
            pass
        time.sleep(5)


def dump_manifest(func, outfile, files_path=None):
    import json
    import importlib

    pieces = func.split(".")
    module_name = ".".join(pieces[:-1])
    module = importlib.import_module(module_name)
    manifest = module.__manifest__

    if files_path is not None:
        manifest["files"] = get_file_list(files_path)

    with open(outfile, "w") as f:
        json.dump(manifest, f)


def get_file_list(files_path):
    from glob import glob
    import os

    files = {
        os.path.relpath(x, files_path): x
        for x in glob(os.path.join(files_path, "**", "*"), recursive=True)
        if os.path.isfile(x)
    }

    return files


def app_wrapper(func=None, cli_arg_str=None, input_json=None):
    from func2argparse import func_to_manifest, manifest_to_argparser
    from unittest import mock
    from shlex import split
    import importlib
    import threading
    import shutil
    import json

    sentinel_dir = None
    try:
        json_dir = None
        if input_json is not None:
            json_dir = os.path.dirname(os.path.abspath(input_json))
            # If the input_json is provided, use the directory of the input_json as the sentinel_dir
            sentinel_dir = json_dir

            with open(input_json, "r") as f:
                params = json.load(f)
            if "function" in params:
                func = params["function"]
                params = params["arguments"]

        # Import the module/function of the app to call
        pieces = func.split(".")
        module_name = ".".join(pieces[:-1])
        module = importlib.import_module(module_name)
        func = getattr(module, pieces[-1])

        if input_json is None:
            manifest = func_to_manifest(func)
            parser = manifest_to_argparser(manifest)
            cli_arg = split(cli_arg_str)
            print("Parsing arguments", cli_arg)
            # The parser really likes to kill the app when failing to parse... This mock.patch prevents it
            with mock.patch("sys.exit") as m:
                appargs, unknownargs = parser.parse_known_args(cli_arg)
                if len(unknownargs):
                    # Otherwise throw an error for unknown arguments
                    parser.print_help()
                    raise RuntimeError(
                        f"Unrecognized arguments \"{' '.join(unknownargs)}\""
                    )
                if m.call_count > 0:
                    raise RuntimeError("Failed parsing app arguments")
            params = vars(appargs)

        # Convert empty strings to Nones and Paths to strings
        for arg, value in params.items():
            if value == "":
                params[arg] = None
            if isinstance(value, Path):
                params[arg] = str(value)
            if isinstance(value, list) or isinstance(value, tuple):
                params[arg] = [str(x) if isinstance(x, Path) else x for x in value]

        if sentinel_dir is None:  # If input_json is provided this is already set
            if "outdir" in params:
                sentinel_dir = params["outdir"]
            elif "execdir" in params:
                sentinel_dir = params["execdir"]
            else:
                raise RuntimeError("No outdir or execdir specified in the arguments")

        os.makedirs(sentinel_dir, exist_ok=True)

        scratchdir = params.get("scratchdir", None)
        if scratchdir is not None:
            if input_json is not None:
                # Create a scratchdir with a unique identifier based on the input_json path
                identifier = os.path.basename(json_dir)
                scratchdir = os.path.join(params["scratchdir"], identifier)

            params["scratchdir"] = scratchdir
            os.makedirs(scratchdir, exist_ok=True)
    except Exception as e:
        # Catch errors in job preparation and write an error sentinel
        if sentinel_dir is None:
            sentinel_dir = "."
        os.makedirs(sentinel_dir, exist_ok=True)
        with open(os.path.join(sentinel_dir, ".pm.err"), "w") as f:
            f.write("")
        raise e

    thread = threading.Thread(target=report_alive, args=(sentinel_dir,), daemon=True)
    thread.start()

    # Execute the job
    try:
        func(**params)
    except SleepException:
        with open(os.path.join(sentinel_dir, ".pm.sleep"), "w") as f:
            f.write("")
    except Exception as e:
        with open(os.path.join(sentinel_dir, ".pm.err"), "w") as f:
            f.write("")
        raise e
    else:
        with open(os.path.join(sentinel_dir, ".pm.done"), "w") as f:
            f.write("")
        # Check that scratchdir is not the whole home or tmp directory or /
        if scratchdir is not None:
            scratchdir = Path(scratchdir).resolve()
            if scratchdir not in (Path.home().resolve(), Path("/tmp"), Path("/")):
                shutil.rmtree(scratchdir)
    return


def ensurelist(tocheck, tomod=None):
    """Convert np.ndarray and scalars to lists.

    Lists and tuples are left as is. If a second argument is given,
    the type check is performed on the first argument, and the second argument is converted.
    """
    if tomod is None:
        tomod = tocheck
    if type(tocheck).__name__ == "ndarray":
        return list(tomod)
    if isinstance(tocheck, range):
        return list(tocheck)
    if not isinstance(tocheck, list) and not isinstance(tocheck, tuple):
        return [
            tomod,
        ]
    return tomod


def wait_jobs(dirs, name, wait, logger, error=True, sleep_time=30):
    """
    Wait for jobs to complete or return directly if any job has not completed
    """
    from playmolecule._public_api import ExecutableDirectory, JobStatus
    import time

    dirs = ensurelist(dirs)
    if len(dirs) == 0:
        raise RuntimeError(
            f"No {name} directories to wait for. Check if the application ran correctly."
        )

    while True:
        non_completed = [
            ExecutableDirectory(dd).status not in (JobStatus.COMPLETED, JobStatus.ERROR)
            for dd in dirs
        ]

        if error and any(
            ExecutableDirectory(dd).status == JobStatus.ERROR for dd in dirs
        ):
            raise RuntimeError(f"Error in {name} job")

        if any(non_completed) and wait:
            logger.info(
                f"Waiting for {sum(non_completed)} {name} job to complete. Sleeping for {sleep_time}s"
            )
            time.sleep(sleep_time)
        else:
            break
    return any(non_completed)
