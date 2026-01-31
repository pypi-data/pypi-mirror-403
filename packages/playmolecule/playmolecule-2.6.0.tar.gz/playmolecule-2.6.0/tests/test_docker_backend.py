# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Tests for Docker backend app function setup with mocking."""

import base64
import gzip
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

curr_dir = os.path.dirname(os.path.abspath(__file__))
test_manifests_dir = os.path.join(curr_dir, "test_playmolecule/apps")
real_pdb = os.path.join(curr_dir, "3ptb.pdb")


def load_test_manifest(app_name, version):
    """Load a single manifest from test_playmolecule/apps directory."""
    version_path = os.path.join(test_manifests_dir, app_name, version)
    if not os.path.isdir(version_path):
        return None

    for filename in os.listdir(version_path):
        if filename.endswith(".json"):
            manifest_path = os.path.join(version_path, filename)
            with open(manifest_path, "r") as f:
                return json.load(f)
    return None


def create_docker_manifest(manifest):
    """Convert a test manifest to Docker-style manifest with container_config."""
    # Docker manifests need container_config with name and version
    if "container_config" not in manifest:
        manifest["container_config"] = {}

    if "name" not in manifest["container_config"]:
        manifest["container_config"]["name"] = manifest.get("name", "TestApp")

    if "version" not in manifest["container_config"]:
        manifest["container_config"]["version"] = manifest.get("version", "1")

    return manifest


def compress_manifest(manifest):
    """Compress manifest as Docker does (gzip + base64)."""
    json_bytes = json.dumps(manifest).encode("utf-8")
    compressed = gzip.compress(json_bytes)
    return base64.b64encode(compressed).decode("utf-8")


@pytest.fixture
def mock_docker_env():
    """Mock Docker and GCloud dependencies."""
    # Mock google.auth
    mock_credentials = MagicMock()
    mock_credentials.token = "mock_token"
    mock_credentials.expiry = None

    with patch("google.auth.default") as mock_auth_default, patch(
        "google.auth.transport.requests.Request"
    ) as mock_request:

        mock_auth_default.return_value = (mock_credentials, "project-id")

        yield mock_credentials


@pytest.fixture
def docker_backend_setup(mock_docker_env, tmp_path):
    """Set up a mock Docker backend."""
    # Save old environment
    old_root = os.environ.get("PM_APP_ROOT")
    old_skip = os.environ.get("PM_SKIP_SETUP")

    # Load test manifest
    test_manifest = load_test_manifest("proteinprepare", "v1")
    docker_manifest = create_docker_manifest(test_manifest)
    compressed = compress_manifest(docker_manifest)

    # Mock the Docker and GCloud components
    mock_docker_client = MagicMock()
    mock_ar_client = MagicMock()

    # Create mock repository
    mock_repo = MagicMock()
    mock_repo.name = "projects/test-project/locations/europe/repositories/apps"
    mock_repo.format_ = 1  # DOCKER format

    # Create mock package
    mock_package = MagicMock()
    mock_package.name = f"{mock_repo.name}/packages/proteinprepare"

    # Set up mock responses
    mock_ar_client.list_repositories.return_value = [mock_repo]
    mock_ar_client.list_packages.return_value = [mock_package]

    # Mock docker.from_env
    mock_image = MagicMock()
    mock_docker_client.images.get.side_effect = Exception("Image not found")

    # Mock the HTTP requests for remote label fetching
    mock_session = MagicMock()
    mock_manifest_response = MagicMock()
    mock_manifest_response.status_code = 200
    mock_manifest_response.json.return_value = {"config": {"digest": "sha256:abc123"}}

    mock_blob_response = MagicMock()
    mock_blob_response.status_code = 200
    mock_blob_response.json.return_value = {
        "config": {"Labels": {"function.manifest.compressed": compressed}}
    }

    mock_session.get.side_effect = [mock_manifest_response, mock_blob_response]

    try:
        os.environ["PM_APP_ROOT"] = "docker://"

        # Clear playmolecule modules
        modules_to_clear = [
            k for k in sys.modules.keys() if k.startswith("playmolecule")
        ]
        for mod in modules_to_clear:
            del sys.modules[mod]

        with patch("docker.from_env", return_value=mock_docker_client), patch(
            "google.cloud.artifactregistry_v1.ArtifactRegistryClient",
            return_value=mock_ar_client,
        ), patch("requests.Session", return_value=mock_session):

            # Reset config
            from playmolecule._config import _reset_config

            _reset_config()

            # Import playmolecule to trigger setup
            import playmolecule

            yield docker_manifest, tmp_path, playmolecule

    finally:
        # Restore environment
        if old_root:
            os.environ["PM_APP_ROOT"] = old_root
        else:
            os.environ.pop("PM_APP_ROOT", None)

        # Clear and reimport playmolecule
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
# Test DockerManifestBackend
# ============================================================================


def test_docker_manifest_backend_get_app_files():
    """Test _DockerManifestBackend.get_app_files() parses files from manifest."""
    from playmolecule._backends._docker import _DockerManifestBackend
    from playmolecule._appfiles import _File

    backend = _DockerManifestBackend("docker://")

    manifest = {
        "files": {
            "test.pdb": "/app/files/test.pdb",
            "data/file.txt": "/app/files/data/file.txt",
        }
    }

    files = backend.get_app_files(manifest)

    # Check files are parsed correctly
    assert "test.pdb" in files
    assert isinstance(files["test.pdb"], _File)
    assert files["test.pdb"].path == "/app/files/test.pdb"

    assert "data/file.txt" in files


def test_docker_manifest_backend_get_app_files_with_parent_dirs():
    """Test that get_app_files creates parent directory entries."""
    from playmolecule._backends._docker import _DockerManifestBackend

    backend = _DockerManifestBackend("docker://")

    manifest = {
        "files": {
            "nested/path/file.txt": "/app/files/nested/path/file.txt",
        }
    }

    files = backend.get_app_files(manifest)

    # Should have parent directories
    assert "nested" in files
    assert "nested/path" in files
    assert "nested/path/file.txt" in files


def test_docker_manifest_backend_get_app_files_empty():
    """Test get_app_files() returns empty dict for None manifest."""
    from playmolecule._backends._docker import _DockerManifestBackend

    backend = _DockerManifestBackend("docker://")
    files = backend.get_app_files(None)
    assert files == {}


def test_docker_manifest_backend_get_app_files_no_files():
    """Test get_app_files() returns empty dict for manifest without files."""
    from playmolecule._backends._docker import _DockerManifestBackend

    backend = _DockerManifestBackend("docker://")
    files = backend.get_app_files(
        {"container_config": {"name": "Test", "version": "1"}}
    )
    assert files == {}


def test_docker_manifest_backend_generate_run_script():
    """Test that run script is generated with correct image tag."""
    from playmolecule._backends._docker import _DockerManifestBackend

    backend = _DockerManifestBackend("docker://")
    image_tag = "europe-docker.pkg.dev/project/repo/image:latest"

    run_sh = backend._generate_run_script(image_tag)

    assert image_tag in run_sh
    assert "docker" in run_sh.lower() or "apptainer" in run_sh.lower()


# ============================================================================
# Test Backend Selection
# ============================================================================


def test_get_manifest_backend_selects_docker():
    """Test that _get_manifest_backend selects Docker backend for docker:// URLs."""
    from playmolecule._backends import _get_manifest_backend
    from playmolecule._backends._docker import _DockerManifestBackend

    backend = _get_manifest_backend("docker://")
    assert isinstance(backend, _DockerManifestBackend)


def test_get_execution_backend_uses_local_for_docker():
    """Test that Docker uses local execution backend."""
    from playmolecule._backends import _get_execution_backend
    from playmolecule._backends._local import _LocalExecutionBackend

    backend = _get_execution_backend("docker://")
    assert isinstance(backend, _LocalExecutionBackend)


# ============================================================================
# Test Manifest Compression
# ============================================================================


def test_manifest_decompression():
    """Test that compressed manifest can be decompressed correctly."""
    original = {
        "name": "TestApp",
        "version": "1",
        "container_config": {"name": "TestApp", "version": "1"},
        "params": [],
    }

    compressed = compress_manifest(original)

    # Decompress
    decompressed = json.loads(gzip.decompress(base64.b64decode(compressed)))

    assert decompressed == original


# ============================================================================
# Test Docker Image List Parsing
# ============================================================================


def test_docker_manifest_backend_init():
    """Test _DockerManifestBackend initialization with custom params."""
    from playmolecule._backends._docker import _DockerManifestBackend

    backend = _DockerManifestBackend(
        "docker://", project_id="custom-project", location="us-central1"
    )

    assert backend.project_id == "custom-project"
    assert backend.location == "us-central1"


# ============================================================================
# Test Local Execution with Docker Backend
# ============================================================================


def test_local_execution_backend_for_docker():
    """Test that local execution backend works with docker:// root."""
    from playmolecule._backends._local import _LocalExecutionBackend

    backend = _LocalExecutionBackend("docker://")
    assert backend.root == "docker://"


def test_local_execution_backend_normalize_values():
    """Test value normalization for execution backend."""
    from playmolecule._backends._local import _LocalExecutionBackend

    backend = _LocalExecutionBackend("docker://")

    assert backend._normalize_values([]) is None
    assert backend._normalize_values(["single"]) == "single"
    assert backend._normalize_values(["a", "b"]) == ["a", "b"]


def test_local_execution_backend_prepare_inputs(tmp_path):
    """Test input preparation for local execution."""
    from playmolecule._backends._local import _LocalExecutionBackend

    backend = _LocalExecutionBackend("docker://")

    # Create a test file
    test_file = tmp_path / "test.pdb"
    test_file.write_text("ATOM 1 CA ALA A 1")

    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()

    manifest = {
        "params": [
            {"name": "outdir", "type": "Path"},
            {"name": "pdbfile", "type": "Path"},
        ]
    }

    arguments = {
        "outdir": str(tmp_path / "output"),
        "pdbfile": str(test_file),
    }

    backend.prepare_inputs(
        write_dir=str(tmp_path),
        inputs_dir=str(inputs_dir),
        arguments=arguments,
        manifest=manifest,
        app_files={},
        function="test_function",
        slpm_path="testapp.v1.main",
    )

    # Should have created inputs.json
    assert (inputs_dir / "inputs.json").exists()

    # File should be copied
    assert (inputs_dir / "test.pdb").exists()


# ============================================================================
# Test Run Script Template
# ============================================================================


def test_docker_run_script_template_exists():
    """Test that docker_run.sh template exists."""
    import playmolecule

    share_dir = os.path.join(os.path.dirname(playmolecule.__file__), "share")
    template_path = os.path.join(share_dir, "docker_run.sh")

    assert os.path.exists(template_path)


# ============================================================================
# Test Running App with pdbfile argument (Docker backend uses local execution)
# ============================================================================


def test_prepare_inputs_with_pdbfile(tmp_path):
    """Test that input preparation works with pdbfile argument (3ptb.pdb)."""
    from playmolecule._backends._local import _LocalExecutionBackend
    import shutil

    backend = _LocalExecutionBackend("docker://")

    # Copy to tmp_path to avoid modifying test fixtures
    pdb_file = tmp_path / "3ptb.pdb"
    shutil.copy(real_pdb, pdb_file)

    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    manifest = {
        "params": [
            {"name": "outdir", "type": "Path", "description": "Output directory"},
            {"name": "pdbfile", "type": "Path", "description": "PDB file"},
            {"name": "pH", "type": "float", "description": "pH value"},
        ],
        "outputs": {"output.pdb": "Protonated structure"},
    }

    arguments = {
        "outdir": str(output_dir),
        "pdbfile": str(pdb_file),
        "pH": 7.4,
    }

    backend.prepare_inputs(
        write_dir=str(output_dir),
        inputs_dir=str(inputs_dir),
        arguments=arguments,
        manifest=manifest,
        app_files={},
        function="main",
        slpm_path="proteinprepare.v1.proteinprepare",
    )

    # Verify inputs.json was created
    inputs_json_path = inputs_dir / "inputs.json"
    assert inputs_json_path.exists()

    with open(inputs_json_path) as f:
        inputs_data = json.load(f)

    assert inputs_data["function"] == "main"
    assert inputs_data["slpm_path"] == "proteinprepare.v1.proteinprepare"
    assert inputs_data["arguments"]["pH"] == 7.4
    assert "pdbfile" in inputs_data["arguments"]

    # Verify PDB file was copied
    assert (inputs_dir / "3ptb.pdb").exists()

    # Verify file content (real 3ptb.pdb should have TRP residue)
    copied_content = (inputs_dir / "3ptb.pdb").read_text()
    assert "ATOM" in copied_content


def test_prepare_inputs_with_pdbfile_creates_original_paths(tmp_path):
    """Test that original_paths.json is created tracking input files."""
    from playmolecule._backends._local import _LocalExecutionBackend
    import shutil

    backend = _LocalExecutionBackend("docker://")

    pdb_file = tmp_path / "3ptb.pdb"
    shutil.copy(real_pdb, pdb_file)

    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    manifest = {
        "params": [
            {"name": "outdir", "type": "Path"},
            {"name": "pdbfile", "type": "Path"},
        ]
    }

    arguments = {
        "outdir": str(output_dir),
        "pdbfile": str(pdb_file),
    }

    backend.prepare_inputs(
        write_dir=str(output_dir),
        inputs_dir=str(inputs_dir),
        arguments=arguments,
        manifest=manifest,
        app_files={},
        function="main",
        slpm_path="proteinprepare.v1.proteinprepare",
    )

    # Verify original_paths.json was created
    original_paths_path = inputs_dir / "original_paths.json"
    assert original_paths_path.exists()

    with open(original_paths_path) as f:
        original_paths = json.load(f)

    # Should map copied file back to original
    assert len(original_paths) > 0
    copied_path = str(inputs_dir / "3ptb.pdb")
    assert copied_path in original_paths
    assert original_paths[copied_path] == str(pdb_file.resolve())
