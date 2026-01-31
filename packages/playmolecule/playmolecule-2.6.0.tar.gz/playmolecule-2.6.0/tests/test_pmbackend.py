# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
import json
import os
import pytest
from unittest.mock import Mock, patch
import responses
import io
import zipfile
import urllib.parse

curr_dir = os.path.dirname(os.path.abspath(__file__))
test_manifests_dir = os.path.join(curr_dir, "test_playmolecule/apps")

# We'll set PM_APP_ROOT in the fixture, not at module level
# to avoid connection attempts before mocking is active


def load_test_manifests():
    """Load all manifests from test_playmolecule/apps directory"""
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


# ============================================================================
# Helper functions for tests
# ============================================================================


def get_submitted_input(submitted_jobs):
    """Extract and parse input args from first submitted job"""
    job_data = list(submitted_jobs.values())[0]
    if isinstance(job_data["input"], dict) and "input" in job_data["input"]:
        return json.loads(job_data["input"]["input"])
    elif isinstance(job_data["input"], str):
        return json.loads(job_data["input"])
    return job_data["input"]


def get_job_dir_from_url(url):
    """Extract job_dir parameter from submission URL"""
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    return query.get("job_dir", [""])[0]


def get_submission_calls(rsps):
    """Get all job submission calls from responses mock"""
    return [
        call
        for call in rsps.calls
        if "/run" in call.request.url and call.request.method == "POST"
    ]


@pytest.fixture
def mock_backend():
    """Create a mock HTTP backend that serves manifests from test_playmolecule"""
    backend_url = "https://test.backend.com"

    # Save old environment
    old_root = os.environ.get("PM_APP_ROOT")

    # Load test manifests
    test_manifests = load_test_manifests()

    # Start responses mock BEFORE setting PM_APP_ROOT to avoid connection attempts
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()

    try:
        # Set environment variable after mock is active
        os.environ["PM_APP_ROOT"] = backend_url
        # Mock the manifests endpoint
        rsps.add(
            responses.GET,
            f"{backend_url}/apps/manifests",
            json=test_manifests,
            status=200,
        )

        # Mock CSRF endpoint for login
        rsps.add(
            responses.GET,
            f"{backend_url}/auth/csrf",
            json={"csrf_token": "test_csrf_token"},
            status=200,
        )

        # Mock login endpoint
        rsps.add(
            responses.POST,
            f"{backend_url}/auth/login",
            json={"status": "success"},
            status=200,
        )

        # Store submitted jobs for status checking
        submitted_jobs = {}

        def job_submission_callback(request):
            """Handle job submission and store job info"""
            # Extract job_dir from query params
            import urllib.parse

            parsed = urllib.parse.urlparse(request.url)
            query = urllib.parse.parse_qs(parsed.query)
            job_id = query.get("job_dir", ["test_job"])[0]

            # Parse the input data - handle both JSON and multipart
            input_data = {}
            if request.body:
                body_str = (
                    request.body.decode("utf-8")
                    if isinstance(request.body, bytes)
                    else request.body
                )
                # Try to extract input field from form data
                if "input=" in body_str:
                    # Multipart form data
                    for part in body_str.split("&"):
                        if part.startswith("input="):
                            input_data = {"input": urllib.parse.unquote_plus(part[6:])}
                            break
                else:
                    # Plain JSON
                    try:
                        input_data = json.loads(body_str)
                    except:
                        input_data = {"input": body_str}

            # Store job info for status checks
            submitted_jobs[job_id] = {
                "status": 1,  # RUNNING
                "input": input_data,
                "files": [],
            }

            return (200, {}, json.dumps({"job_id": job_id}))

        # Mock job submission endpoint (use regex to match any app path)
        import re

        rsps.add_callback(
            responses.POST,
            re.compile(f"{backend_url}/apps/.*/(run|proteinprepare|bar)"),
            callback=job_submission_callback,
            content_type="application/json",
        )

        def status_callback(request):
            """Handle status checks"""
            import urllib.parse

            parsed = urllib.parse.urlparse(request.url)
            query = urllib.parse.parse_qs(parsed.query)
            job_prefix = query.get("prefix", [""])[0]

            # Find matching job
            for job_id, job_info in submitted_jobs.items():
                if job_id.startswith(job_prefix):
                    return (200, {}, json.dumps([{"status": job_info["status"]}]))

            # No job found
            return (200, {}, json.dumps([]))

        # Mock status check endpoint
        rsps.add_callback(
            responses.GET,
            f"{backend_url}/jobs",
            callback=status_callback,
            content_type="application/json",
        )

        # Mock file download endpoint
        def file_download_callback(request):
            """Handle file downloads"""
            # Create a simple zip file with mock results
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                zf.writestr("output.pdb", "ATOM      1  CA  ALA A   1")
                zf.writestr("details.csv", "residue,protonation\nALA,neutral")
            zip_buffer.seek(0)
            return (200, {}, zip_buffer.read())

        # Use regex for matching file download URLs
        import re

        rsps.add_callback(
            responses.GET,
            re.compile(f"{backend_url}/file/.*"),
            callback=file_download_callback,
        )

        # Make submitted_jobs accessible
        rsps._submitted_jobs = submitted_jobs

        # Clear and reimport playmolecule modules to pick up the new backend URL
        # We remove modules from sys.modules to force a fresh import
        import sys
        import importlib

        # Remove playmolecule modules to force fresh import with new PM_APP_ROOT
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("playmolecule")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        # Reset config to pick up new environment
        from playmolecule._config import _reset_config

        _reset_config()

        # Fresh import with new environment
        import playmolecule

        # Set auth cookies after reload
        from playmolecule._backends._http import _get_http_session

        session = _get_http_session()
        session.cookies.set("access_token", "test_token")
        session.cookies.set("csrf_token", "test_csrf")

        yield rsps, backend_url, submitted_jobs

    finally:
        # Stop the mock
        rsps.stop()
        rsps.reset()

        # Restore environment
        if old_root:
            os.environ["PM_APP_ROOT"] = old_root
        else:
            os.environ.pop("PM_APP_ROOT", None)

        # Clear and reimport playmolecule module again to restore original state
        import sys

        # Set PM_SKIP_SETUP during import to avoid environment check
        os.environ["PM_SKIP_SETUP"] = "1"
        try:
            # Clear playmolecule modules
            modules_to_clear = [
                k for k in sys.modules.keys() if k.startswith("playmolecule")
            ]
            for mod in modules_to_clear:
                del sys.modules[mod]

            # Reset config cache
            from playmolecule._config import _reset_config

            _reset_config()

            # Fresh import with restored environment
            import playmolecule  # noqa: F401
        finally:
            os.environ.pop("PM_SKIP_SETUP", None)


@pytest.fixture
def work_in_tmp(tmp_path):
    """Change to tmp_path directory for the test and restore afterwards"""
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        yield tmp_path
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def job_dir_prefix():
    """Set PM_JOB_DIR_PREFIX environment variable for testing"""
    old_prefix = os.environ.get("PM_JOB_DIR_PREFIX")
    os.environ["PM_JOB_DIR_PREFIX"] = "user-project/"

    try:
        yield "user-project/"
    finally:
        if old_prefix is not None:
            os.environ["PM_JOB_DIR_PREFIX"] = old_prefix
        else:
            os.environ.pop("PM_JOB_DIR_PREFIX", None)


# ============================================================================
# Test manifests loading from backend
# ============================================================================


def test_backend_serves_manifests(mock_backend):
    """Test that the mock backend serves manifests correctly"""
    rsps, backend_url, _ = mock_backend

    import requests

    response = requests.get(f"{backend_url}/apps/manifests")

    assert response.status_code == 200
    manifests = response.json()

    # Check that we have the test manifests
    assert "proteinprepare.v1" in manifests
    assert "name" in manifests["proteinprepare.v1"]
    assert manifests["proteinprepare.v1"]["name"] == "ProteinPrepare"


# ============================================================================
# Test login/logout
# ============================================================================


def test_login(mock_backend):
    """Test login function sends correct credentials"""
    rsps, backend_url, _ = mock_backend
    from playmolecule._backends._http import login

    # Login should use the mocked endpoints
    login("testuser", "testpass")

    # Verify the requests were made
    # CSRF request
    csrf_calls = [call for call in rsps.calls if "csrf" in call.request.url]
    assert len(csrf_calls) == 1

    # Login request
    login_calls = [call for call in rsps.calls if "login" in call.request.url]
    assert len(login_calls) == 1
    assert login_calls[0].request.method == "POST"


def test_logout(mock_backend):
    """Test logout clears session cookies"""
    from playmolecule._backends._http import logout, _get_http_session

    session = _get_http_session()
    # Set some cookies
    session.cookies.set("access_token", "test")

    logout()

    # Cookies should be cleared
    assert "access_token" not in session.cookies


# ============================================================================
# Test job submission with real app
# ============================================================================


def test_job_submission_with_pdbid(mock_backend, work_in_tmp, job_dir_prefix):
    """Test job submission with PDB ID argument sends correct data"""
    rsps, _, submitted_jobs = mock_backend
    from playmolecule import apps

    outdir = os.path.join(work_in_tmp, "my_job")

    # Create job using the real app interface
    job = apps.proteinprepare.v1.proteinprepare(outdir, pdbid="3ptb", pH=7.4)

    # Run the job (will submit to mocked backend)
    job.run()

    # Find the job submission request
    submission_calls = get_submission_calls(rsps)
    assert len(submission_calls) == 1

    # Verify URL structure
    url = submission_calls[0].request.url
    assert "proteinprepare" in url.lower()

    # Verify job_dir includes prefix
    job_dir = get_job_dir_from_url(url)
    assert job_dir == f"{job_dir_prefix}my_job"

    # Verify job was stored
    assert len(submitted_jobs) == 1

    # Get the submitted job data and verify arguments
    input_args = get_submitted_input(submitted_jobs)
    assert input_args["pdbid"] == "3ptb"
    assert input_args["pH"] == 7.4


def test_job_submission_with_nested_folder(mock_backend, work_in_tmp, job_dir_prefix):
    """Test job submission with PDB ID argument sends correct data"""
    rsps, _, submitted_jobs = mock_backend
    from playmolecule import apps

    outdir = os.path.join(work_in_tmp, "nested/folder/my_job")

    # Create job using the real app interface
    job = apps.proteinprepare.v1.proteinprepare(outdir, pdbid="3ptb", pH=7.4)

    # Run the job (will submit to mocked backend)
    job.run()

    # Find the job submission request
    submission_calls = get_submission_calls(rsps)
    assert len(submission_calls) == 1

    # Verify job_dir includes prefix
    url = submission_calls[0].request.url
    assert "proteinprepare" in url.lower()
    job_dir = get_job_dir_from_url(url)
    assert job_dir == f"{job_dir_prefix}nested/folder/my_job"


def test_job_submission_with_file(mock_backend, work_in_tmp, job_dir_prefix):
    """Test job submission with file upload"""
    rsps, _, submitted_jobs = mock_backend
    from playmolecule import apps

    # Create a test PDB file
    test_pdb = os.path.join(work_in_tmp, "test.pdb")
    with open(test_pdb, "w") as f:
        f.write("ATOM      1  CA  ALA A   1\n")

    outdir = os.path.join(work_in_tmp, "my_job")
    # Create job with file input
    job = apps.proteinprepare.v1.proteinprepare(outdir, pdbfile=test_pdb)
    job.run()

    # Verify submission occurred
    submission_calls = get_submission_calls(rsps)
    assert len(submission_calls) == 1

    # Verify job_dir includes prefix
    url = submission_calls[0].request.url
    job_dir = get_job_dir_from_url(url)
    assert job_dir == f"{job_dir_prefix}my_job"

    # The request body should be multipart (contains file)
    # We can't easily check the exact multipart structure with responses,
    # but we can verify the submission happened
    assert len(submitted_jobs) == 1


# ============================================================================
# Test status checking
# ============================================================================


def test_status_checking_running(mock_backend, work_in_tmp):
    """Test status checking for running job"""
    rsps, _, submitted_jobs = mock_backend
    from playmolecule import apps, JobStatus

    outdir = os.path.join(work_in_tmp, "my_job")

    job = apps.proteinprepare.v1.proteinprepare(outdir, pdbid="3ptb")
    job.run()

    # Set job status to RUNNING
    for job_info in submitted_jobs.values():
        job_info["status"] = 1  # RUNNING

    # Check status
    status = job.status

    # Verify status check was made
    status_calls = [
        call
        for call in rsps.calls
        if "/jobs" in call.request.url and call.request.method == "GET"
    ]
    assert len(status_calls) >= 1

    # Status should be RUNNING
    assert status == JobStatus.RUNNING


def test_status_checking_completed(mock_backend, work_in_tmp):
    """Test status checking for completed job triggers download"""
    rsps, _, submitted_jobs = mock_backend
    from playmolecule import apps, JobStatus

    outdir = os.path.join(work_in_tmp, "my_job")

    job = apps.proteinprepare.v1.proteinprepare(outdir, pdbid="3ptb")
    job.run()

    # Set job status to COMPLETED
    for job_info in submitted_jobs.values():
        job_info["status"] = 2  # COMPLETED

    # Check status - should download files
    status = job.status

    # Verify file download was requested
    download_calls = [call for call in rsps.calls if "/file/" in call.request.url]
    assert len(download_calls) >= 1

    assert status == JobStatus.COMPLETED


def test_status_checking_error(mock_backend, work_in_tmp):
    """Test status checking for errored job"""
    rsps, backend_url, submitted_jobs = mock_backend
    from playmolecule import apps, JobStatus
    import re

    # Add error file endpoints
    rsps.add(
        responses.GET,
        re.compile(f"{backend_url}/files.*"),
        json={
            "err": {"name": "slurm.123.err", "uri": "/slurm.123.err"},
            "out": {"name": "slurm.123.out", "uri": "/slurm.123.out"},
        },
        status=200,
    )

    outdir = os.path.join(work_in_tmp, "my_job")

    job = apps.proteinprepare.v1.proteinprepare(outdir, pdbid="3ptb")
    job.run()

    # Set job status to ERROR
    for job_info in submitted_jobs.values():
        job_info["status"] = 3  # ERROR

    # Check status
    status = job.status
    assert status == JobStatus.ERROR


# ============================================================================
# Test error handling
# ============================================================================


def test_submission_without_auth_fails(mock_backend, work_in_tmp):
    """Test that job submission fails without authentication"""
    from playmolecule import apps
    from playmolecule._backends._http import _get_http_session

    session = _get_http_session()
    outdir = os.path.join(work_in_tmp, "my_job")

    # Temporarily remove authentication
    old_cookies = dict(session.cookies)
    session.cookies.clear()

    try:
        job = apps.proteinprepare.v1.proteinprepare(outdir, pdbid="3ptb")

        with pytest.raises(RuntimeError, match="Access token not found"):
            job.run()
    finally:
        # Restore cookies
        for key, value in old_cookies.items():
            session.cookies.set(key, value)


# ============================================================================
# Test with app datasets
# ============================================================================


def test_submission_with_app_dataset(mock_backend, work_in_tmp):
    """Test that app:// URIs are passed as string references"""
    _, _, submitted_jobs = mock_backend
    from playmolecule import apps

    outdir = os.path.join(work_in_tmp, "my_job")

    # Use an app:// URI directly to test that it's not uploaded
    app_file_uri = "app://files/datasets/3ptb.pdb"

    job = apps.proteinprepare.v1.proteinprepare(outdir, pdbfile=app_file_uri)
    job.run()

    # Verify submission
    assert len(submitted_jobs) == 1

    # Get the submitted job data and verify app:// URI is preserved
    input_args = get_submitted_input(submitted_jobs)
    # The pdbfile should still be an app:// URI (not uploaded)
    assert input_args["pdbfile"].startswith("app://files/")


# ============================================================================
# Test apps with different functions
# ============================================================================


def test_proteinpreparenew_bar_function(mock_backend, work_in_tmp):
    """Test that proteinpreparenew's bar function works"""
    rsps, _, _ = mock_backend
    from playmolecule import apps

    outdir = os.path.join(work_in_tmp, "my_job")

    # Use the bar function from proteinpreparenew
    job = apps.proteinpreparenew.v1.bar(outdir, pdbid="3ptb")
    job.run()

    # Verify submission
    submission_calls = get_submission_calls(rsps)
    assert len(submission_calls) >= 1

    # Should call proteinpreparenew endpoint
    assert "proteinpreparenew" in submission_calls[0].request.url.lower()
