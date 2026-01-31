import os
import pytest


@pytest.fixture
def test_fake_app_root():
    old_root = os.environ.get("PM_APP_ROOT")
    os.environ["PM_APP_ROOT"] = "/dev/null"
    yield
    if old_root:
        os.environ["PM_APP_ROOT"] = old_root
    else:
        os.environ.pop("PM_APP_ROOT", None)


def test_local_backend_without_installation(test_fake_app_root):
    from playmolecule._backends._local import _LocalManifestBackend

    backend = _LocalManifestBackend("/dev/null")
    assert backend.get_apps() == {}

    # Set the PM_APP_ROOT to the temporary directory
    from playmolecule import apps

    ignore_attrs = ["Path", "logging", "logger", "os", "stat", "KWARGS"]
    assert (
        len([x for x in dir(apps) if not x.startswith("_") and x not in ignore_attrs])
        == 0
    )
    assert not hasattr(apps, "datasets")

    from playmolecule import JobStatus, ExecutableDirectory
