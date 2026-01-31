# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""HTTP backend for PM web service."""

import io
import json
import logging
import os
import tempfile
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from playmolecule._appfiles import _File
from playmolecule._config import _get_config
from playmolecule._validation import _validate_argument_type
from playmolecule._public_api import JobStatus

logger = logging.getLogger(__name__)

# Default timeout: (connect, read)
_DEFAULT_TIMEOUT = (5, 30)


def _get_cookie_file_path() -> str:
    """Get path to the cookie file."""
    home = os.path.expanduser("~")
    return os.path.join(home, ".playmolecule", "cookies.json")


def _save_cookies(session: requests.Session, username: Optional[str] = None) -> None:
    """Save cookies to a persistent file."""
    try:
        path = _get_cookie_file_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = {"cookies": session.cookies.get_dict(), "username": username}

        with open(path, "w") as f:
            json.dump(data, f)
        os.chmod(path, 0o600)
    except Exception as e:
        logger.warning(f"Failed to save cookies: {e}")


def _load_cookies(session: requests.Session) -> Optional[str]:
    """Load cookies from persistent file. Returns username if present."""
    path = _get_cookie_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)

            if isinstance(data, dict):
                session.cookies.update(data.get("cookies", {}))
                return data.get("username")

        except Exception as e:
            logger.warning(f"Failed to load cookies: {e}")
    return None


def _check_login_status() -> None:
    """Check if user is logged in via persisted cookies and log it."""
    path = _get_cookie_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)

            username = None
            if isinstance(data, dict) and "username" in data:
                username = data["username"]

            if username:
                logger.info(f"Logged in as {username}")
        except Exception:
            pass


def _refresh_token(session: requests.Session, base_url: str) -> None:
    """Refresh the access token using the refresh token."""
    logger.info("Refreshing access token...")
    try:
        headers = _get_headers()

        # Add CSRF token from cookies if available
        csrf_token = session.cookies.get("csrf_token")
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        # Call refresh endpoint
        response = session.post(
            f"{base_url}/auth/refresh-token",
            headers=headers,
            timeout=_DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        # Save updated cookies
        _save_cookies(session)
        logger.info("Token refreshed successfully")

    except Exception as e:
        logger.warning(f"Failed to refresh token: {e}")
        raise


class _HTTPSession:
    """Manages HTTP session with connection pooling and retries."""

    def __init__(self):
        self._session = requests.Session()
        _load_cookies(self._session)

        # Configure connection pooling + retries
        retry_strategy = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
            pool_block=False,
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        # Add response hook for auto-refresh
        self._session.hooks["response"].append(self._auth_retry_hook)

    def _auth_retry_hook(self, response, *args, **kwargs):
        """Hook to refresh token on 401/403 errors and retry."""
        if response.status_code not in (401, 403):
            return response

        # Check error messages
        try:
            # Try to get error message from JSON, fallback to text
            try:
                error_msg = response.json().get("error", "")
            except Exception:
                error_msg = response.text

            should_refresh = False
            if (
                response.status_code == 401
                and "Could not validate credentials" in error_msg
            ):
                should_refresh = True
            elif response.status_code == 403 and "Invalid CSRF token" in error_msg:
                should_refresh = True

            if not should_refresh:
                return response

            # Avoid infinite loops - check if we are already refreshing
            if "/auth/refresh-token" in response.request.url:
                return response

            config = _get_config()
            base_url = config.app_root
            if not base_url:
                return response

            # Refresh token
            _refresh_token(self._session, base_url)

            # Retry original request
            request = response.request

            # Update X-CSRF-Token header if present in cookies or if we fetched a new one
            csrf_token = self._session.cookies.get("csrf_token")
            if csrf_token:
                request.headers["X-CSRF-Token"] = csrf_token

            # Re-send request
            return self._session.send(
                request, verify=False
            )  # verify handled by adapter/session?

        except Exception as e:
            logger.debug(f"Auto-refresh failed: {e}")
            return response

    @property
    def session(self) -> requests.Session:
        return self._session

    @property
    def cookies(self):
        return self._session.cookies


# Global session instance
_http_session: Optional[_HTTPSession] = None


def _get_http_session() -> _HTTPSession:
    """Get or create the global HTTP session."""
    global _http_session
    if _http_session is None:
        _http_session = _HTTPSession()
    return _http_session


def _get_headers() -> dict:
    """Get headers for HTTP requests."""
    config = _get_config()
    return dict(config.backend_headers)


class _HTTPManifestBackend:
    """Backend for loading app manifests from HTTP API."""

    def __init__(self, root: str, session: Optional[_HTTPSession] = None):
        """Initialize the HTTP manifest backend.

        Parameters
        ----------
        root : str
            Base URL of the PM web service
        session : _HTTPSession, optional
            HTTP session to use. If None, uses the global session.
        """
        self.base_url = root
        self._session = session or _get_http_session()

    def get_apps(self) -> Dict[str, Dict[str, dict]]:
        """Get all available apps from HTTP API.

        Returns
        -------
        dict
            Nested dict: {appname: {version: {"manifest": ..., "appdir": None, "run.sh": None}}}
        """
        rsp = self._session.session.get(
            f"{self.base_url}/apps/manifests",
            headers=_get_headers(),
            timeout=_DEFAULT_TIMEOUT,
        )
        if rsp.status_code != 200:
            raise RuntimeError(f"Failed to get apps from {self.base_url}: {rsp.text}")

        apps = {}
        for app_module, manifest in rsp.json().items():
            app_name = app_module.split(".")[0]
            if app_name not in apps:
                apps[app_name] = {}

            version = manifest.get("version")
            if version is None:
                try:
                    version = manifest["container_config"]["version"]
                except Exception:
                    version = "1"

            apps[app_name][f"v{int(float(version))}"] = {
                "manifest": manifest,
                "appdir": None,
                "run.sh": None,
            }

        return apps

    def get_app_files(self, manifest: Optional[dict]) -> dict:
        """Get files associated with an app from manifest.

        Parameters
        ----------
        manifest : dict or None
            The app manifest

        Returns
        -------
        dict
            Dictionary of filename -> _File objects
        """
        if manifest is None:
            return {}
        files = manifest.get("files", {})
        result = {}
        for name, description in files.items():
            while name.endswith("/"):
                name = name[:-1]
            path = f"app://files/{name}"
            result[name] = _File(name, path, description)
        return result


class _HTTPExecutionBackend:
    """Backend for executing apps via HTTP API."""

    def __init__(self, root: str, session: Optional[_HTTPSession] = None):
        """Initialize the HTTP execution backend.

        Parameters
        ----------
        root : str
            Base URL of the PM web service
        session : _HTTPSession, optional
            HTTP session to use. If None, uses the global session.
        """
        self.base_url = root
        self._session = session or _get_http_session()

    def prepare_inputs(
        self,
        arguments: dict,
        manifest: dict,
        app_files: dict,
        slpm_path: str,
    ) -> dict:
        """Prepare inputs for HTTP execution.

        Parameters
        ----------
        arguments : dict
            Function arguments
        manifest : dict
            Function manifest
        app_files : dict
            App files dictionary
        slpm_path : str
            The slpm path

        Returns
        -------
        dict
            Dictionary with arguments, files, and file_handles
        """
        files: List[Tuple[str, Tuple[str, Any, str]]] = []
        file_handles: List[Any] = []

        # Remove directory arguments
        for key in ("outdir", "scratchdir", "execdir"):
            if key in arguments:
                del arguments[key]

        # Process arguments
        for arg in manifest["params"]:
            name = arg["name"]
            argtype = arg["type"]
            nargs = arg.get("nargs")

            if name in ("outdir", "scratchdir", "execdir"):
                continue

            if name not in arguments:
                continue

            vals = arguments[name]
            vals = _validate_argument_type(name, vals, argtype, nargs)

            # Open files for Path-type arguments
            if argtype == "Path":
                newvals = []
                for val in vals:
                    if val is None or (isinstance(val, str) and val == ""):
                        continue

                    # Keep app:// URIs as-is
                    if isinstance(val, str) and val.startswith("app://files"):
                        newvals.append(val)
                        continue

                    if isinstance(val, _File):
                        newvals.append(val.path)
                        continue

                    val = os.path.abspath(val)
                    filename = os.path.basename(val)

                    if os.path.isdir(val):
                        # Create a temp file for the zip
                        fh = tempfile.TemporaryFile()
                        with zipfile.ZipFile(fh, "w", zipfile.ZIP_DEFLATED) as zf:
                            for root, _dirs, _files in os.walk(val):
                                for _file in _files:
                                    _path = os.path.join(root, _file)
                                    _arcname = os.path.relpath(_path, val)
                                    zf.write(_path, _arcname)
                        fh.seek(0)
                        file_handles.append(fh)

                        # Add with custom MIME type as hint
                        files.append(
                            (
                                name,
                                (filename + ".zip", fh, "application/x-directory-zip"),
                            )
                        )
                        # We assume the backend will unzip to original filename
                        newvals.append(filename)
                        continue

                    fh = open(val, "rb")
                    file_handles.append(fh)
                    files.append((name, (filename, fh, "application/octet-stream")))
                    newvals.append(filename)

                arguments[name] = self._normalize_values(newvals)

        return {
            "arguments": arguments,
            "slpm_path": slpm_path,
            "files": files,
            "file_handles": file_handles,
        }

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
        input_data: dict,
        job_id: Optional[str] = None,
        prefix: Optional[str] = None,
        _logger: bool = True,
    ) -> str:
        """Run the app via HTTP API.

        Parameters
        ----------
        dirname : str
            Output directory
        input_data : dict
            Data from prepare_inputs
        job_id : str
            Job ID (if empty, derived from dirname)
        prefix : str, optional
            Job directory prefix
        _logger : bool
            Whether to log

        Returns
        -------
        str
            Job ID
        """
        config = _get_config()
        session = self._session.session

        if (
            "access_token" not in session.cookies
            and "chat_request_id" not in _get_headers()
        ):
            raise RuntimeError(
                "Access token not found. Please login to the PM backend."
            )

        if prefix is None:
            prefix = config.job_dir_prefix

        file_handles = input_data.get("file_handles", [])

        # Derive job_id from dirname if not provided
        if job_id is None:
            working_dir = config.working_dir or os.getcwd()
            job_id = os.path.relpath(os.path.abspath(dirname), working_dir)
            if job_id.startswith(".."):
                raise RuntimeError(
                    f"Job directory {job_id} is outside the current working directory."
                )

        try:
            headers = _get_headers()
            headers["X-CSRF-Token"] = session.cookies.get("csrf_token")

            res = session.post(
                f"{self.base_url}/apps/{input_data['slpm_path']}/run?job_dir={prefix}{job_id}",
                data={"input": json.dumps(input_data["arguments"])},
                files=input_data["files"],
                headers=headers,
                timeout=(10, 120),
            )

            if res.status_code != 200:
                raise RuntimeError(f"Failed to run job on {self.base_url}: {res.text}")
            return res.json()["job_id"]
        finally:
            # Always close file handles
            for fh in file_handles:
                try:
                    fh.close()
                except Exception as e:
                    logger.warning(f"Failed to close file handle: {e}")

    def get_status(self, dirname: str, job_id: str) -> JobStatus:
        """Get job status from HTTP API.

        Parameters
        ----------
        dirname : str
            Output directory (for downloading results)
        job_id : str
            Job ID

        Returns
        -------
        JobStatus
            Current job status
        """
        import safezipfile

        session = self._session.session

        try:
            headers = _get_headers()
            headers["Connection"] = "close"
            res = session.get(
                f"{self.base_url}/jobs?prefix={job_id}",
                timeout=_DEFAULT_TIMEOUT,
                headers=headers,
            )
        except requests.exceptions.RequestException as e:
            logger.warning(f"PM backend status poll failed for job '{job_id}': {e}")
            return JobStatus.WAITING_INFO

        res.raise_for_status()
        jobs = res.json()

        if not isinstance(jobs, list) or len(jobs) != 1:
            return JobStatus.WAITING_INFO

        metadata = jobs[0]
        status_map = {0: "WAITING_INFO", 1: "RUNNING", 2: "COMPLETED", 3: "ERROR"}
        status = status_map[int(metadata["status"])]

        if status == "ERROR":
            # Fetch error details (but don't use them currently)
            self._fetch_error_details(job_id)
            return JobStatus.ERROR

        if status in ("WAITING_INFO", "RUNNING"):
            return JobStatus.RUNNING

        # Completed - download files
        res = session.get(
            f"{self.base_url}/file/{job_id}/",
            timeout=(5, 360),  # Longer read timeout for file downloads
            headers=_get_headers(),
        )

        with safezipfile.ZipFile(io.BytesIO(res.content)) as zf:
            zf.extractall(
                dirname, max_files=1e9, max_file_size=1e11, max_total_size=1e12
            )

        return JobStatus.COMPLETED

    def _fetch_error_details(self, job_id: str) -> Optional[str]:
        """Fetch error details for a failed job."""
        session = self._session.session

        res = session.get(
            f"{self.base_url}/files?prefix={job_id}/",
            timeout=_DEFAULT_TIMEOUT,
            headers=_get_headers(),
        )
        files = res.json()

        errf = None
        outf = None
        for f in files.values():
            if f["name"].startswith("slurm."):
                if f["name"].endswith(".err"):
                    errf = f["uri"]
                elif f["name"].endswith(".out"):
                    outf = f["uri"]

        if errf and outf:
            errres = session.get(
                f"{self.base_url}/file/{job_id}{errf}",
                timeout=_DEFAULT_TIMEOUT,
                headers=_get_headers(),
            )
            outres = session.get(
                f"{self.base_url}/file/{job_id}{outf}",
                timeout=_DEFAULT_TIMEOUT,
                headers=_get_headers(),
            )
            return f"{outres.content}{errres.content}"
        return None


# Authentication functions (kept for backwards compatibility)
def login(username: str, password: str) -> None:
    """Authenticate and store cookies in the global session.

    Parameters
    ----------
    username : str
        Username
    password : str
        Password
    """
    config = _get_config()
    base_url = config.app_root

    if not base_url or not base_url.startswith("http"):
        raise RuntimeError(f"Invalid backend URL: {base_url}")

    session = _get_http_session().session

    # Get CSRF token
    response = session.get(
        f"{base_url}/auth/csrf",
        headers=_get_headers(),
        timeout=_DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    csrf_token = response.json()["csrf_token"]

    headers = _get_headers()
    headers["X-CSRF-Token"] = csrf_token

    # Login
    response = session.post(
        f"{base_url}/auth/login",
        data={"username": username, "password": password},
        headers=headers,
        timeout=_DEFAULT_TIMEOUT,
    )
    response.raise_for_status()

    _save_cookies(session, username)

    logger.info(f"Logged in as {username}")


def logout() -> None:
    """Clear cookies from the global session."""
    _get_http_session().session.cookies.clear()

    path = _get_cookie_file_path()
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

    logger.info("Logged out.")
