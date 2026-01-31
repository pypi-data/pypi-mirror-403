# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Tests for HTTP backend app function setup with mocking."""

import json
import os
import sys

import pytest
import responses

curr_dir = os.path.dirname(os.path.abspath(__file__))
test_manifests_dir = os.path.join(curr_dir, "test_playmolecule/apps")
real_pdb = os.path.join(curr_dir, "3ptb.pdb")


def load_test_manifests():
    """Load all manifests from test_playmolecule/apps directory as HTTP backend format."""
    manifests = {}

    for app_name in os.listdir(test_manifests_dir):
        app_dir = os.path.join(test_manifests_dir, app_name)
        if not os.path.isdir(app_dir):
            continue

        for version_dir in os.listdir(app_dir):
            version_path = os.path.join(app_dir, version_dir)
            if not os.path.isdir(version_path):
                continue

            # Look for JSON manifest file
            for filename in os.listdir(version_path):
                if filename.endswith(".json"):
                    manifest_path = os.path.join(version_path, filename)
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)

                    # Create module path like "proteinprepare.v1"
                    module_path = f"{app_name}.{version_dir}"
                    manifests[module_path] = manifest

    return manifests


@pytest.fixture
def http_backend_setup():
    """Set up a mock HTTP backend and return the module after setup."""
    backend_url = "https://test.http.backend.com"

    # Save old environment
    old_root = os.environ.get("PM_APP_ROOT")
    old_skip = os.environ.get("PM_SKIP_SETUP")

    # Load test manifests
    test_manifests = load_test_manifests()

    # Start responses mock BEFORE setting PM_APP_ROOT
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()

    try:
        # Set environment before import
        os.environ["PM_APP_ROOT"] = backend_url

        # Mock the manifests endpoint
        rsps.add(
            responses.GET,
            f"{backend_url}/apps/manifests",
            json=test_manifests,
            status=200,
        )

        # Clear playmolecule modules to force fresh import
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("playmolecule")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Reset config to pick up new environment
        from playmolecule._config import _reset_config

        _reset_config()

        # Fresh import with HTTP backend URL
        import playmolecule

        yield rsps, backend_url, test_manifests, playmolecule

    finally:
        rsps.stop()
        rsps.reset()

        # Restore environment
        if old_root:
            os.environ["PM_APP_ROOT"] = old_root
        else:
            os.environ.pop("PM_APP_ROOT", None)

        # Clear and reimport playmolecule module again to restore original state
        os.environ["PM_SKIP_SETUP"] = "1"
        try:
            modules_to_clear = [
                k for k in sys.modules.keys() if k.startswith("playmolecule")
            ]
            for mod in modules_to_clear:
                del sys.modules[mod]

            from playmolecule._config import _reset_config

            _reset_config()

            import playmolecule  # noqa: F401
        finally:
            if old_skip:
                os.environ["PM_SKIP_SETUP"] = old_skip
            else:
                os.environ.pop("PM_SKIP_SETUP", None)


# ============================================================================
# Test HTTPManifestBackend
# ============================================================================


def test_http_manifest_backend_get_apps():
    """Test _HTTPManifestBackend.get_apps() parses API response correctly."""
    from playmolecule._backends._http import _HTTPManifestBackend, _HTTPSession

    backend_url = "https://test.backend.com"
    test_manifests = {
        "testapp.v1": {
            "name": "TestApp",
            "description": "A test application",
            "version": "1",
            "params": [{"name": "outdir", "type": "Path", "description": "Output dir"}],
        },
        "testapp.v2": {
            "name": "TestApp",
            "description": "A test application v2",
            "version": "2",
            "params": [{"name": "outdir", "type": "Path", "description": "Output dir"}],
        },
    }

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            f"{backend_url}/apps/manifests",
            json=test_manifests,
            status=200,
        )

        session = _HTTPSession()
        backend = _HTTPManifestBackend(backend_url, session=session)
        apps = backend.get_apps()

        # Should group by app name
        assert "testapp" in apps
        assert "v1" in apps["testapp"]
        assert "v2" in apps["testapp"]
        assert apps["testapp"]["v1"]["manifest"]["name"] == "TestApp"
        assert apps["testapp"]["v2"]["manifest"]["version"] == "2"


def test_http_manifest_backend_get_apps_with_container_config_version():
    """Test that version is extracted from container_config if not at top level."""
    from playmolecule._backends._http import _HTTPManifestBackend, _HTTPSession

    backend_url = "https://test.backend.com"
    test_manifests = {
        "oldapp.v1": {
            "name": "OldApp",
            "description": "An old-style manifest",
            "container_config": {"version": "3"},
            "params": [],
        }
    }

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            f"{backend_url}/apps/manifests",
            json=test_manifests,
            status=200,
        )

        session = _HTTPSession()
        backend = _HTTPManifestBackend(backend_url, session=session)
        apps = backend.get_apps()

        assert "oldapp" in apps
        assert "v3" in apps["oldapp"]


def test_http_manifest_backend_get_apps_error_handling():
    """Test that get_apps() raises error on HTTP failure."""
    from playmolecule._backends._http import _HTTPManifestBackend
    import requests

    backend_url = "https://test.backend.com"

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            f"{backend_url}/apps/manifests",
            json={"error": "Not found"},
            status=404,
        )

        # Use a plain requests session without retries to avoid MaxRetryError
        class SimpleSession:
            def __init__(self):
                self._session = requests.Session()

            @property
            def session(self):
                return self._session

        simple_session = SimpleSession()
        backend = _HTTPManifestBackend(backend_url, session=simple_session)

        with pytest.raises(RuntimeError, match="Failed to get apps"):
            backend.get_apps()


def test_http_manifest_backend_get_app_files():
    """Test _HTTPManifestBackend.get_app_files() parses files from manifest."""
    from playmolecule._backends._http import _HTTPManifestBackend
    from playmolecule._appfiles import _File

    backend = _HTTPManifestBackend("https://test.backend.com")

    manifest = {
        "files": {
            "test.pdb": "A test PDB file",
            "data/": "A data directory",
            "nested/path/file.txt": "A nested file",
        }
    }

    files = backend.get_app_files(manifest)

    # Check files are parsed correctly
    assert "test.pdb" in files
    assert isinstance(files["test.pdb"], _File)
    assert files["test.pdb"].path == "app://files/test.pdb"
    assert files["test.pdb"].description == "A test PDB file"

    # Trailing slash should be removed
    assert "data" in files
    assert files["data"].path == "app://files/data"

    assert "nested/path/file.txt" in files


def test_http_manifest_backend_get_app_files_empty():
    """Test get_app_files() returns empty dict for None manifest."""
    from playmolecule._backends._http import _HTTPManifestBackend

    backend = _HTTPManifestBackend("https://test.backend.com")
    files = backend.get_app_files(None)
    assert files == {}


def test_http_manifest_backend_get_app_files_no_files():
    """Test get_app_files() returns empty dict for manifest without files."""
    from playmolecule._backends._http import _HTTPManifestBackend

    backend = _HTTPManifestBackend("https://test.backend.com")
    files = backend.get_app_files({"name": "TestApp", "params": []})
    assert files == {}


# ============================================================================
# Test App Function Setup via _set_root
# ============================================================================


def test_set_root_creates_app_functions(http_backend_setup):
    """Test that _set_root with HTTP URL creates callable app functions."""
    rsps, backend_url, test_manifests, playmolecule = http_backend_setup

    # Verify manifest endpoint was called
    manifest_calls = [c for c in rsps.calls if "/apps/manifests" in c.request.url]
    assert len(manifest_calls) == 1

    # Verify proteinprepare app was created
    from playmolecule import apps

    assert hasattr(apps, "proteinprepare")
    assert hasattr(apps.proteinprepare, "v1")


def test_app_function_is_callable(http_backend_setup):
    """Test that created app function is callable."""
    _, _, _, playmolecule = http_backend_setup
    from playmolecule import apps

    # The function should be callable
    assert callable(apps.proteinprepare.v1.proteinprepare)


def test_app_function_has_manifest(http_backend_setup):
    """Test that created app function has __manifest__ attribute."""
    _, _, test_manifests, playmolecule = http_backend_setup
    from playmolecule import apps

    func = apps.proteinprepare.v1.proteinprepare
    assert hasattr(func, "__manifest__")
    assert func.__manifest__["description"] is not None


def test_app_function_has_docstring(http_backend_setup):
    """Test that created app function has proper docstring."""
    _, _, _, playmolecule = http_backend_setup
    from playmolecule import apps

    func = apps.proteinprepare.v1.proteinprepare
    assert func.__doc__ is not None
    assert "ProteinPrepare" in func.__doc__


def test_app_module_has_files(http_backend_setup):
    """Test that app module has files attribute."""
    _, _, test_manifests, playmolecule = http_backend_setup
    from playmolecule import apps

    # The module should have files attribute
    assert hasattr(apps.proteinprepare.v1, "files")
    files = apps.proteinprepare.v1.files

    # Should contain files from manifest
    assert isinstance(files, dict)
    # The test manifest has "tests/3ptb.pdb" as a file
    assert "tests/3ptb.pdb" in files


def test_app_module_has_tests(http_backend_setup):
    """Test that app function has tests attribute."""
    _, _, _, playmolecule = http_backend_setup
    from playmolecule import apps

    func = apps.proteinprepare.v1.proteinprepare
    assert hasattr(func, "tests")


def test_latest_version_linked(http_backend_setup):
    """Test that latest version is linked to parent module."""
    _, _, _, playmolecule = http_backend_setup
    from playmolecule import apps

    # Should be able to access function directly from app module
    assert hasattr(apps.proteinprepare, "proteinprepare")
    assert callable(apps.proteinprepare.proteinprepare)


def test_multiple_app_functions(http_backend_setup):
    """Test that apps with multiple functions are set up correctly."""
    _, _, test_manifests, playmolecule = http_backend_setup
    from playmolecule import apps

    # proteinpreparenew has multiple functions in manifest
    if hasattr(apps, "proteinpreparenew"):
        assert hasattr(apps.proteinpreparenew, "v1")
        # Check if multiple functions exist (depends on manifest)
        module = apps.proteinpreparenew.v1
        assert hasattr(module, "__manifest__")


def test_app_in_function_dict(http_backend_setup):
    """Test that app functions are registered in _function_dict."""
    _, _, _, playmolecule = http_backend_setup
    from playmolecule.apps import _function_dict

    # Should have entries for the app functions
    matching_keys = [k for k in _function_dict.keys() if "proteinprepare" in k]
    assert len(matching_keys) > 0


# ============================================================================
# Test Backend Selection
# ============================================================================


def test_get_manifest_backend_selects_http():
    """Test that _get_manifest_backend selects HTTP backend for http:// URLs."""
    from playmolecule._backends import _get_manifest_backend
    from playmolecule._backends._http import _HTTPManifestBackend

    backend = _get_manifest_backend("https://example.com")
    assert isinstance(backend, _HTTPManifestBackend)

    backend = _get_manifest_backend("http://example.com")
    assert isinstance(backend, _HTTPManifestBackend)


def test_get_execution_backend_selects_http():
    """Test that _get_execution_backend selects HTTP backend for http:// URLs."""
    from playmolecule._backends import _get_execution_backend
    from playmolecule._backends._http import _HTTPExecutionBackend

    backend = _get_execution_backend("https://example.com")
    assert isinstance(backend, _HTTPExecutionBackend)


# ============================================================================
# Test HTTPSession
# ============================================================================


def test_http_session_has_retry_strategy():
    """Test that _HTTPSession configures retries."""
    from playmolecule._backends._http import _HTTPSession

    session = _HTTPSession()
    assert session.session is not None
    # Session should have adapters mounted
    assert "https://" in session.session.adapters
    assert "http://" in session.session.adapters


def test_get_http_session_returns_singleton():
    """Test that _get_http_session returns same instance."""
    from playmolecule._backends._http import _get_http_session, _HTTPSession

    # Reset global session
    import playmolecule._backends._http as http_module

    http_module._http_session = None

    session1 = _get_http_session()
    session2 = _get_http_session()

    assert session1 is session2
    assert isinstance(session1, _HTTPSession)


# ============================================================================
# Test Running App with pdbfile argument
# ============================================================================


@pytest.fixture
def http_backend_with_job_submission():
    """Set up a mock HTTP backend with job submission endpoints."""
    import re
    import io
    import zipfile
    import urllib.parse

    backend_url = "https://test.http.backend.com"

    # Save old environment
    old_root = os.environ.get("PM_APP_ROOT")
    old_skip = os.environ.get("PM_SKIP_SETUP")

    # Load test manifests
    test_manifests = load_test_manifests()

    # Track submitted jobs
    submitted_jobs = {}

    # Start responses mock
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()

    try:
        os.environ["PM_APP_ROOT"] = backend_url

        # Mock the manifests endpoint
        rsps.add(
            responses.GET,
            f"{backend_url}/apps/manifests",
            json=test_manifests,
            status=200,
        )

        # Job submission callback
        def job_submission_callback(request):
            parsed = urllib.parse.urlparse(request.url)
            query = urllib.parse.parse_qs(parsed.query)
            job_id = query.get("job_dir", ["test_job"])[0]

            input_data = {}
            if request.body:
                # Try to decode safely, fallback to ignoring errors if binary
                try:
                    body_str = (
                        request.body.decode("utf-8")
                        if isinstance(request.body, bytes)
                        else request.body
                    )
                except UnicodeDecodeError:
                    # Binary content (like zip), treat as string with replacement or latin1
                    body_str = request.body.decode("latin1", errors="replace")

                if "input=" in body_str:
                    for part in body_str.split("&"):
                        if part.startswith("input="):
                            input_data = {"input": urllib.parse.unquote_plus(part[6:])}
                            break

            submitted_jobs[job_id] = {
                "status": 2,  # COMPLETED
                "input": input_data,
            }

            return (200, {}, json.dumps({"job_id": job_id}))

        # Mock job submission endpoint
        rsps.add_callback(
            responses.POST,
            re.compile(f"{backend_url}/apps/.*"),
            callback=job_submission_callback,
            content_type="application/json",
        )

        # Status callback
        def status_callback(request):
            parsed = urllib.parse.urlparse(request.url)
            query = urllib.parse.parse_qs(parsed.query)
            job_prefix = query.get("prefix", [""])[0]

            for job_id, job_info in submitted_jobs.items():
                if job_id.startswith(job_prefix):
                    return (200, {}, json.dumps([{"status": job_info["status"]}]))
            return (200, {}, json.dumps([]))

        rsps.add_callback(
            responses.GET,
            f"{backend_url}/jobs",
            callback=status_callback,
            content_type="application/json",
        )

        # File download callback
        def file_download_callback(request):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr("output.pdb", "ATOM      1  CA  ALA A   1")
            zip_buffer.seek(0)
            return (200, {}, zip_buffer.read())

        rsps.add_callback(
            responses.GET,
            re.compile(f"{backend_url}/file/.*"),
            callback=file_download_callback,
        )

        # Clear and reimport playmolecule
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("playmolecule")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        from playmolecule._config import _reset_config

        _reset_config()

        import playmolecule

        # Set auth cookies
        from playmolecule._backends._http import _get_http_session

        session = _get_http_session()
        session.cookies.set("access_token", "test_token")
        session.cookies.set("csrf_token", "test_csrf")

        yield rsps, backend_url, submitted_jobs, playmolecule

    finally:
        rsps.stop()
        rsps.reset()

        if old_root:
            os.environ["PM_APP_ROOT"] = old_root
        else:
            os.environ.pop("PM_APP_ROOT", None)

        os.environ["PM_SKIP_SETUP"] = "1"
        try:
            modules_to_clear = [
                k for k in sys.modules.keys() if k.startswith("playmolecule")
            ]
            for mod in modules_to_clear:
                del sys.modules[mod]

            from playmolecule._config import _reset_config

            _reset_config()

            import playmolecule  # noqa: F401
        finally:
            if old_skip:
                os.environ["PM_SKIP_SETUP"] = old_skip
            else:
                os.environ.pop("PM_SKIP_SETUP", None)


def test_run_proteinprepare_with_pdbfile(http_backend_with_job_submission, tmp_path):
    """Test running proteinprepare app with pdbfile argument (3ptb.pdb)."""
    rsps, backend_url, submitted_jobs, playmolecule = http_backend_with_job_submission
    from playmolecule import apps

    # Change to tmp_path for job directory resolution
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        outdir = tmp_path / "output"

        # Run the app
        job = apps.proteinprepare.v1.proteinprepare(
            outdir=str(outdir), pdbfile=real_pdb
        )

        # The job should be created
        assert job is not None

        # Run the job
        job.run()

        # Verify job was submitted
        assert len(submitted_jobs) == 1

        # Verify submission was made
        submission_calls = [
            c
            for c in rsps.calls
            if "/apps/" in c.request.url and c.request.method == "POST"
        ]
        assert len(submission_calls) == 1

        # Verify proteinprepare endpoint was called
        assert "proteinprepare" in submission_calls[0].request.url.lower()

    finally:
        os.chdir(old_cwd)


def test_run_proteinprepare_with_pdbfile_checks_status(
    http_backend_with_job_submission, tmp_path
):
    """Test that status checking works after submitting job with pdbfile."""
    rsps, backend_url, submitted_jobs, playmolecule = http_backend_with_job_submission
    from playmolecule import apps, JobStatus

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        outdir = tmp_path / "output"

        job = apps.proteinprepare.v1.proteinprepare(
            outdir=str(outdir), pdbfile=real_pdb
        )
        job.run()

        # Check status (should be COMPLETED based on our mock)
        status = job.status
        assert status == JobStatus.COMPLETED

    finally:
        os.chdir(old_cwd)


def test_run_proteinprepare_with_directory(http_backend_with_job_submission, tmp_path):
    """Test running proteinprepare app with a directory argument, checking if it gets zipped."""
    rsps, backend_url, submitted_jobs, playmolecule = http_backend_with_job_submission
    from playmolecule import apps
    import zipfile
    import io

    # Create a test directory with files
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "file2.txt").write_text("content2")

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        outdir = tmp_path / "output"

        # Capture requests to inspect the body
        request_body = None
        original_callback = None

        # Find the existing callback for POST /apps/.*
        for callback_match in rsps.calls:
            # This is tricky because responses doesn't expose callbacks easily this way
            # Instead we will wrap the mock behavior by inspecting the last call
            pass

        # Run the app
        job = apps.proteinprepare.v1.proteinprepare(
            outdir=str(outdir),
            pdbfile=str(
                test_dir
            ),  # Pass directory as pdbfile (just for testing the mechanism)
        )
        job.run()

        # Inspect the last POST request
        post_calls = [c for c in rsps.calls if c.request.method == "POST"]
        assert len(post_calls) > 0
        last_call = post_calls[-1]

        # Verify content type and filename in the multipart body
        # Since 'requests' builds the body, we need to inspect the raw body or headers
        # However, checking the raw body for multipart boundaries is complex.
        # But we know _http.py adds it to 'files'.

        # We can inspect the body to find the filename and content type
        body_content = last_call.request.body
        if isinstance(body_content, bytes):
            body_content = body_content.decode("latin1")  # Decode to search text

        assert 'filename="test_data.zip"' in body_content
        assert "Content-Type: application/x-directory-zip" in body_content

        # We can also attempt to verify the zip content if we can extract it,
        # but verifying the metadata (MIME + filename) is the primary goal here.

    finally:
        os.chdir(old_cwd)
