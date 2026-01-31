# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Tests for backend abstraction layer."""

import json
import os
import shutil
import tempfile

import pytest

curr_dir = os.path.dirname(os.path.abspath(__file__))
real_pdb = os.path.join(curr_dir, "3ptb.pdb")


# ============================================================================
# Test Config Module
# ============================================================================


def test_config_defaults():
    """Test Config dataclass default values."""
    from playmolecule._config import _Config

    config = _Config()
    assert config.app_root is None
    assert config.queue_config is None
    assert config.symlink is False
    assert config.blocking is False
    assert config.backend_headers == {}
    assert config.job_dir_prefix == ""
    assert config.skip_setup is False


def test_load_config_from_env():
    """Test loading config from environment variables."""
    import os
    from playmolecule._config import _load_config, _reset_config

    old_env = dict(os.environ)
    try:
        os.environ["PM_APP_ROOT"] = "/test/path"
        os.environ["PM_SYMLINK"] = "1"
        os.environ["PM_BLOCKING"] = "1"
        os.environ["PM_JOB_DIR_PREFIX"] = "prefix/"
        os.environ["PM_QUEUE_CONFIG"] = '{"queue": "slurm"}'
        os.environ["PM_BACKEND_HEADERS"] = '{"X-Test": "value"}'

        _reset_config()
        config = _load_config()

        assert config.app_root == "/test/path"
        assert config.symlink is True
        assert config.blocking is True
        assert config.job_dir_prefix == "prefix/"
        assert config.queue_config == {"queue": "slurm"}
        assert config.backend_headers == {"X-Test": "value"}
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        _reset_config()


def test_config_normalizes_trailing_slashes():
    """Test that app_root trailing slashes are removed."""
    import os
    from playmolecule._config import _load_config, _reset_config

    old_env = dict(os.environ)
    try:
        os.environ["PM_APP_ROOT"] = "/test/path///"
        os.environ["PM_SKIP_SETUP"] = "1"

        _reset_config()
        config = _load_config()

        assert config.app_root == "/test/path"
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        _reset_config()


# ============================================================================
# Test Validation Module
# ============================================================================


def test_validators_exist():
    """Test that all expected validators exist."""
    from playmolecule._validation import _VALIDATORS

    assert "str" in _VALIDATORS
    assert "Path" in _VALIDATORS
    assert "bool" in _VALIDATORS
    assert "int" in _VALIDATORS
    assert "float" in _VALIDATORS
    assert "dict" in _VALIDATORS


def test_validate_argument_type_str():
    """Test string argument validation."""
    from playmolecule._validation import _validate_argument_type

    result = _validate_argument_type("test", "value", "str", None)
    assert result == ["value"]


def test_validate_argument_type_list():
    """Test list argument validation."""
    from playmolecule._validation import _validate_argument_type

    result = _validate_argument_type("test", ["a", "b"], "str", 2)
    assert result == ["a", "b"]


def test_validate_argument_type_wrong_type():
    """Test that wrong type raises error."""
    from playmolecule._validation import _validate_argument_type

    with pytest.raises(RuntimeError, match="type"):
        _validate_argument_type("test", 123, "str", None)


def test_validate_argument_type_list_when_single_expected():
    """Test that list when single expected raises error."""
    from playmolecule._validation import _validate_argument_type

    with pytest.raises(RuntimeError, match="single value"):
        _validate_argument_type("test", ["a", "b"], "str", None)


# ============================================================================
# Test Backend Selection
# ============================================================================


def test_get_manifest_backend_local():
    """Test manifest backend selection for local path."""
    from playmolecule._backends import _get_manifest_backend
    from playmolecule._backends._local import _LocalManifestBackend

    backend = _get_manifest_backend("/some/local/path")
    assert isinstance(backend, _LocalManifestBackend)


def test_get_manifest_backend_http():
    """Test manifest backend selection for HTTP URL."""
    from playmolecule._backends import _get_manifest_backend
    from playmolecule._backends._http import _HTTPManifestBackend

    backend = _get_manifest_backend("https://example.com")
    assert isinstance(backend, _HTTPManifestBackend)

    backend = _get_manifest_backend("http://example.com")
    assert isinstance(backend, _HTTPManifestBackend)


def test_get_manifest_backend_docker():
    """Test manifest backend selection for Docker."""
    from playmolecule._backends import _get_manifest_backend
    from playmolecule._backends._docker import _DockerManifestBackend

    backend = _get_manifest_backend("docker://")
    assert isinstance(backend, _DockerManifestBackend)


def test_get_manifest_backend_none():
    """Test manifest backend selection returns None for None input."""
    from playmolecule._backends import _get_manifest_backend

    backend = _get_manifest_backend(None)
    assert backend is None


def test_get_execution_backend_local():
    """Test execution backend selection for local path."""
    from playmolecule._backends import _get_execution_backend
    from playmolecule._backends._local import _LocalExecutionBackend

    backend = _get_execution_backend("/some/local/path")
    assert isinstance(backend, _LocalExecutionBackend)


def test_get_execution_backend_http():
    """Test execution backend selection for HTTP URL."""
    from playmolecule._backends import _get_execution_backend
    from playmolecule._backends._http import _HTTPExecutionBackend

    backend = _get_execution_backend("https://example.com")
    assert isinstance(backend, _HTTPExecutionBackend)


def test_get_execution_backend_docker_uses_local():
    """Test that Docker uses local execution backend."""
    from playmolecule._backends import _get_execution_backend
    from playmolecule._backends._local import _LocalExecutionBackend

    backend = _get_execution_backend("docker://")
    assert isinstance(backend, _LocalExecutionBackend)


def test_get_execution_backend_none():
    """Test execution backend selection returns None for None input."""
    from playmolecule._backends import _get_execution_backend

    backend = _get_execution_backend(None)
    assert backend is None


# ============================================================================
# Test LocalManifestBackend
# ============================================================================


def test_local_manifest_backend_check_folder_validity():
    """Test folder validity checking."""
    from playmolecule._backends._local import _LocalManifestBackend

    backend = _LocalManifestBackend("/home/test")

    # Valid folder names
    assert backend._check_folder_validity("/home/test/app_name")
    assert backend._check_folder_validity("/home/test/app123")
    assert backend._check_folder_validity("/home/test/my_app")

    # Invalid folder names
    assert not backend._check_folder_validity("/home/test/App-Name")
    assert not backend._check_folder_validity("/home/test/app.name")
    assert not backend._check_folder_validity("/home/test/app name")


def test_local_manifest_backend_get_apps():
    """Test getting apps from local filesystem."""
    from playmolecule._backends._local import _LocalManifestBackend

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test app structure
        app_dir = os.path.join(tmpdir, "apps", "testapp", "v1")
        os.makedirs(app_dir)

        manifest = {
            "name": "TestApp",
            "description": "Test application",
            "params": [],
        }
        with open(os.path.join(app_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        backend = _LocalManifestBackend(tmpdir)
        apps = backend.get_apps()

        assert "testapp" in apps
        assert "v1" in apps["testapp"]
        assert apps["testapp"]["v1"]["manifest"]["name"] == "TestApp"


# ============================================================================
# Test LocalExecutionBackend
# ============================================================================


def test_local_execution_backend_normalize_values():
    """Test value normalization."""
    from playmolecule._backends._local import _LocalExecutionBackend

    backend = _LocalExecutionBackend("/test")

    assert backend._normalize_values([]) is None
    assert backend._normalize_values(["a"]) == "a"
    assert backend._normalize_values(["a", "b"]) == ["a", "b"]


def test_local_execution_backend_get_status_completed():
    """Test status checking for completed job."""
    from playmolecule._backends._local import _LocalExecutionBackend
    from playmolecule._public_api import JobStatus

    with tempfile.TemporaryDirectory() as tmpdir:
        inputs_dir = os.path.join(tmpdir, "run_test")
        os.makedirs(inputs_dir)

        # Create done sentinel
        with open(os.path.join(inputs_dir, ".pm.done"), "w") as f:
            f.write("")

        backend = _LocalExecutionBackend("/test")
        status = backend.get_status(tmpdir, inputs_dir)

        assert status == JobStatus.COMPLETED


def test_local_execution_backend_get_status_error():
    """Test status checking for errored job."""
    from playmolecule._backends._local import _LocalExecutionBackend
    from playmolecule._public_api import JobStatus

    with tempfile.TemporaryDirectory() as tmpdir:
        inputs_dir = os.path.join(tmpdir, "run_test")
        os.makedirs(inputs_dir)

        # Create error sentinel
        with open(os.path.join(inputs_dir, ".pm.err"), "w") as f:
            f.write("")

        backend = _LocalExecutionBackend("/test")
        status = backend.get_status(tmpdir, inputs_dir)

        assert status == JobStatus.ERROR


# ============================================================================
# Test HTTPManifestBackend
# ============================================================================


def test_http_manifest_backend_get_app_files():
    """Test getting app files from manifest."""
    from playmolecule._backends._http import _HTTPManifestBackend

    backend = _HTTPManifestBackend("https://example.com")

    manifest = {
        "files": {
            "test.pdb": "A test PDB file",
            "data/": "A data directory",
        }
    }

    files = backend.get_app_files(manifest)

    assert "test.pdb" in files
    assert files["test.pdb"].path == "app://files/test.pdb"
    assert files["test.pdb"].description == "A test PDB file"
    assert "data" in files  # Trailing slash removed


def test_http_manifest_backend_accepts_custom_session():
    """Test that HTTPManifestBackend accepts custom session."""
    from playmolecule._backends._http import _HTTPManifestBackend, _HTTPSession

    session = _HTTPSession()
    backend = _HTTPManifestBackend("https://example.com", session=session)

    assert backend._session is session


# ============================================================================
# Test HTTPExecutionBackend
# ============================================================================


def test_http_execution_backend_normalize_values():
    """Test value normalization."""
    from playmolecule._backends._http import _HTTPExecutionBackend

    backend = _HTTPExecutionBackend("https://example.com")

    assert backend._normalize_values([]) is None
    assert backend._normalize_values(["a"]) == "a"
    assert backend._normalize_values(["a", "b"]) == ["a", "b"]


def test_http_execution_backend_accepts_custom_session():
    """Test that HTTPExecutionBackend accepts custom session."""
    from playmolecule._backends._http import _HTTPExecutionBackend, _HTTPSession

    session = _HTTPSession()
    backend = _HTTPExecutionBackend("https://example.com", session=session)

    assert backend._session is session


# ============================================================================
# Test DockerManifestBackend
# ============================================================================


def test_docker_manifest_backend_get_app_files():
    """Test getting app files from Docker manifest."""
    from playmolecule._backends._docker import _DockerManifestBackend
    from playmolecule._appfiles import _File

    backend = _DockerManifestBackend("docker://")

    manifest = {
        "files": {
            "test.pdb": "/container/path/test.pdb",
            "data/file.txt": "/container/path/data/file.txt",
        }
    }

    files = backend.get_app_files(manifest)

    assert "test.pdb" in files
    assert isinstance(files["test.pdb"], _File)
    assert "data/file.txt" in files


# ============================================================================
# Test SLURM Backend
# ============================================================================


def test_slurm_functions_exist():
    """Test that SLURM functions are exported."""
    from playmolecule._backends._slurm import (
        _submit_slurm,
        _get_slurm_status,
        slurm_mps,
    )

    assert callable(_submit_slurm)
    assert callable(_get_slurm_status)
    assert callable(slurm_mps)


# ============================================================================
# Test Backwards Compatibility Shims
# ============================================================================


def test_http_backend_exports_auth():
    """Test that HTTP backend exports login/logout functions."""
    from playmolecule._backends._http import login, logout

    assert callable(login)
    assert callable(logout)


def test_docker_backend_exports():
    """Test that Docker backend exports expected functions."""
    from playmolecule._backends._docker import (
        _DockerManifestBackend,
        _update_docker_apps_from_gcloud,
    )

    assert _DockerManifestBackend is not None
    assert callable(_update_docker_apps_from_gcloud)


# ============================================================================
# Test Local Backend with pdbfile argument
# ============================================================================


def test_local_backend_prepare_inputs_with_pdbfile():
    """Test local backend input preparation with pdbfile argument (3ptb.pdb)."""
    from playmolecule._backends._local import _LocalExecutionBackend

    with tempfile.TemporaryDirectory() as tmpdir:
        backend = _LocalExecutionBackend("/test/root")

        pdb_file = os.path.join(tmpdir, "3ptb.pdb")
        shutil.copy(real_pdb, pdb_file)

        inputs_dir = os.path.join(tmpdir, "inputs")
        os.makedirs(inputs_dir)
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)

        manifest = {
            "params": [
                {"name": "outdir", "type": "Path", "description": "Output directory"},
                {"name": "pdbfile", "type": "Path", "description": "Input PDB file"},
                {"name": "pH", "type": "float", "description": "pH value"},
            ],
            "outputs": {"output.pdb": "Protonated structure"},
        }

        arguments = {
            "outdir": output_dir,
            "pdbfile": pdb_file,
            "pH": 7.4,
        }

        backend.prepare_inputs(
            write_dir=output_dir,
            inputs_dir=inputs_dir,
            arguments=arguments,
            manifest=manifest,
            app_files={},
            function="main",
            slpm_path="proteinprepare.v1.proteinprepare",
        )

        # Verify inputs.json was created
        inputs_json = os.path.join(inputs_dir, "inputs.json")
        assert os.path.exists(inputs_json)

        with open(inputs_json) as f:
            data = json.load(f)

        assert data["function"] == "main"
        assert data["slpm_path"] == "proteinprepare.v1.proteinprepare"
        assert data["arguments"]["pH"] == 7.4

        # Verify PDB file was copied
        copied_pdb = os.path.join(inputs_dir, "3ptb.pdb")
        assert os.path.exists(copied_pdb)

        # Verify content (real 3ptb.pdb should have ATOM records)
        with open(copied_pdb) as f:
            content = f.read()
        assert "ATOM" in content


def test_local_backend_prepare_inputs_with_symlink():
    """Test local backend input preparation using symlinks."""
    from playmolecule._backends._local import _LocalExecutionBackend
    from playmolecule._config import _reset_config

    with tempfile.TemporaryDirectory() as tmpdir:
        # Set PM_SYMLINK=1
        old_symlink = os.environ.get("PM_SYMLINK")
        os.environ["PM_SYMLINK"] = "1"
        _reset_config()

        try:
            backend = _LocalExecutionBackend("/test/root")

            pdb_file = os.path.join(tmpdir, "3ptb.pdb")
            shutil.copy(real_pdb, pdb_file)

            inputs_dir = os.path.join(tmpdir, "inputs")
            os.makedirs(inputs_dir)
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir)

            manifest = {
                "params": [
                    {"name": "outdir", "type": "Path"},
                    {"name": "pdbfile", "type": "Path"},
                ]
            }

            arguments = {
                "outdir": output_dir,
                "pdbfile": pdb_file,
            }

            backend.prepare_inputs(
                write_dir=output_dir,
                inputs_dir=inputs_dir,
                arguments=arguments,
                manifest=manifest,
                app_files={},
                function="main",
                slpm_path="test.v1.main",
            )

            # Verify symlink was created instead of copy
            linked_file = os.path.join(inputs_dir, "3ptb.pdb")
            assert os.path.islink(linked_file)
            assert os.path.realpath(linked_file) == os.path.abspath(pdb_file)

        finally:
            if old_symlink:
                os.environ["PM_SYMLINK"] = old_symlink
            else:
                os.environ.pop("PM_SYMLINK", None)
            _reset_config()


def test_local_backend_prepare_inputs_multiple_pdbfiles():
    """Test local backend with multiple PDB files (nargs scenario)."""
    from playmolecule._backends._local import _LocalExecutionBackend

    with tempfile.TemporaryDirectory() as tmpdir:
        backend = _LocalExecutionBackend("/test/root")

        # Create multiple test PDB files by copying real 3ptb.pdb
        pdb_files = []
        for name in ["3ptb.pdb", "1abc.pdb", "2xyz.pdb"]:
            pdb_file = os.path.join(tmpdir, name)
            shutil.copy(real_pdb, pdb_file)
            pdb_files.append(pdb_file)

        inputs_dir = os.path.join(tmpdir, "inputs")
        os.makedirs(inputs_dir)
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)

        manifest = {
            "params": [
                {"name": "outdir", "type": "Path"},
                {"name": "pdbfiles", "type": "Path", "nargs": 3},
            ]
        }

        arguments = {
            "outdir": output_dir,
            "pdbfiles": pdb_files,
        }

        backend.prepare_inputs(
            write_dir=output_dir,
            inputs_dir=inputs_dir,
            arguments=arguments,
            manifest=manifest,
            app_files={},
            function="main",
            slpm_path="test.v1.main",
        )

        # Verify all files were copied
        for name in ["3ptb.pdb", "1abc.pdb", "2xyz.pdb"]:
            assert os.path.exists(os.path.join(inputs_dir, name))
