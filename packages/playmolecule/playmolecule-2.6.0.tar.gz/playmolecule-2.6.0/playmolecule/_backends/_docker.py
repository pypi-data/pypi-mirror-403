# (c) 2015-2023 Acellera Ltd http://www.acellera.com
# All Rights Reserved
# Distributed under HTMD Software License Agreement
# No redistribution in whole or part
#
"""Docker/GCloud manifest backend."""

import base64
import gzip
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("playmolecule.backends.docker")

# Cache directory for run scripts
_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "playmolecule")

# Cached credentials and session
_cached_credentials = None
_cached_session = None


def _get_or_create_session():
    """Get or create a cached requests session with authentication."""
    import google.auth
    from google.auth.transport.requests import Request
    import requests

    global _cached_credentials, _cached_session

    # Check if we need to refresh credentials
    need_refresh = True
    if _cached_credentials is not None:
        expiry = getattr(_cached_credentials, "expiry", None)
        if expiry is not None:
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry > datetime.now(timezone.utc):
                need_refresh = False

    if need_refresh:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(Request())
        _cached_credentials = credentials

    if _cached_session is None:
        _cached_session = requests.Session()

    return _cached_session, _cached_credentials.token


class _DockerManifestBackend:
    """Backend for loading app manifests from Docker/GCloud registry."""

    def __init__(
        self,
        root: str,
        project_id: str = "repositories-368911",
        location: str = "europe-southwest1",
    ):
        """Initialize the Docker manifest backend.

        Parameters
        ----------
        root : str
            Root path (should start with "docker")
        project_id : str
            GCloud project ID
        location : str
            GCloud location
        """
        self.root = root
        self.project_id = project_id
        self.location = location

    def get_apps(self) -> Dict[str, Dict[str, dict]]:
        """Get all available apps from Docker registry.

        Returns
        -------
        dict
            Nested dict: {appname: {version: {"manifest": ..., "appdir": None, "run.sh": ...}}}
        """
        os.makedirs(_CACHE_DIR, exist_ok=True)

        prefix = f"{self.location}-docker.pkg.dev/{self.project_id}"
        manifests = self._get_app_manifests(prefix)

        apps = {}
        for image_tag, manifest in manifests.items():
            container_config = manifest["container_config"]
            app_name = container_config["name"].lower()
            version = container_config["version"]

            # Generate run script
            run_sh = self._generate_run_script(image_tag)
            cache_run_sh = os.path.join(_CACHE_DIR, f"run_{app_name}_{version}.sh")
            with open(cache_run_sh, "w") as f:
                f.write(run_sh)

            if app_name not in apps:
                apps[app_name] = {}
            apps[app_name][f"v{version}"] = {
                "manifest": manifest,
                "appdir": None,
                "run.sh": cache_run_sh,
                "container_image": image_tag,
            }

        return apps

    def get_app_files(self, manifest: Optional[dict]) -> dict:
        """Get files associated with an app.

        Parameters
        ----------
        manifest : dict or None
            The app manifest

        Returns
        -------
        dict
            Dictionary of filename -> _File objects
        """
        from playmolecule._appfiles import _File

        if manifest is None:
            return {}

        files = {}
        for name, fullpath in manifest.get("files", {}).items():
            # Add parent directories
            for dir_name, dir_path in self._get_parent_dirs(name, fullpath):
                if dir_name not in files:
                    files[dir_name] = _File(dir_name, dir_path)
            files[name] = _File(name, fullpath)

        return files

    def _get_parent_dirs(self, name: str, fullpath: str):
        """Yield parent directories for a file path."""
        fullpath_p = Path(fullpath)
        name_p = Path(name)

        for i in range(1, len(name_p.parts)):
            yield str(Path(*name_p.parts[:i])), str(
                Path(*fullpath_p.parts[: -len(name_p.parts) + i])
            )

    def _generate_run_script(self, image_tag: str) -> str:
        """Generate the docker run script for an image."""
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        share_dir = os.path.join(os.path.dirname(curr_dir), "share")

        with open(os.path.join(share_dir, "docker_run.sh"), "r") as f:
            run_sh = f.read()

        return run_sh.replace("{docker_container_name}", f'"{image_tag}"')

    def _get_app_list(self) -> list:
        """Get list of all Docker images from GCloud Artifact Registry."""
        from google.cloud import artifactregistry_v1

        ar_client = artifactregistry_v1.ArtifactRegistryClient()
        parent = f"projects/{self.project_id.strip()}/locations/{self.location}"
        registry_host = f"{self.location}-docker.pkg.dev"

        repos_request = artifactregistry_v1.ListRepositoriesRequest(parent=parent)
        repos = list(ar_client.list_repositories(request=repos_request))

        def process_repo(repo):
            if repo.format_ != artifactregistry_v1.Repository.Format.DOCKER:
                return []

            repo_id = repo.name.split("/")[-1]
            if repo_id == "acellera-docker-apps":
                return []

            pkg_request = artifactregistry_v1.ListPackagesRequest(parent=repo.name)
            packages = ar_client.list_packages(request=pkg_request)

            repo_images = []
            for pkg in packages:
                image_name = pkg.name.split("/")[-1]
                full_tag = (
                    f"{registry_host}/{self.project_id}/{repo_id}/{image_name}:latest"
                )

                repo_images.append(
                    {
                        "project_id": self.project_id,
                        "location": self.location,
                        "repo": repo_id,
                        "image": image_name,
                        "tag": "latest",
                        "full_tag": full_tag,
                    }
                )
            return repo_images

        all_images = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(process_repo, repos)
            for result in results:
                all_images.extend(result)

        return all_images

    def _get_remote_label(
        self,
        project_id: str,
        location: str,
        repo: str,
        image: str,
        tag: str = "latest",
    ) -> Optional[dict]:
        """Fetch Docker Config Blob from Artifact Registry API to extract labels."""
        t_start = time.time()
        session, token = _get_or_create_session()
        logger.debug(f"  Time to get session/token: {time.time() - t_start:.3f}s")

        base_url = f"https://{location}-docker.pkg.dev"
        image_path = f"v2/{project_id}/{repo}/{image}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        }

        # Get manifest
        manifest_url = f"{base_url}/{image_path}/manifests/{tag}"
        t = time.time()
        r = session.get(manifest_url, headers=headers)
        if r.status_code != 200:
            raise ValueError(f"Failed to get manifest: {r.status_code} {r.text}")
        logger.debug(f"  Time to get manifest: {time.time() - t:.3f}s")

        manifest = r.json()

        # Extract config digest
        config_digest = manifest.get("config", {}).get("digest")
        if not config_digest:
            config_digest = manifest.get("manifests", [{}])[0].get("digest")
        if not config_digest:
            raise ValueError("Could not find config digest in manifest")

        # Get config blob
        blob_url = f"{base_url}/{image_path}/blobs/{config_digest}"
        t = time.time()
        r = session.get(blob_url, headers=headers)
        if r.status_code != 200:
            raise ValueError(f"Failed to get config blob: {r.status_code}")
        logger.debug(f"  Time to get config blob: {time.time() - t:.3f}s")

        config_data = r.json()

        # Extract and decode label
        t = time.time()
        labels = config_data.get("config", {}).get("Labels", {})
        b64_string = labels.get("function.manifest.compressed")

        if not b64_string:
            return None

        result = json.loads(gzip.decompress(base64.b64decode(b64_string)))
        logger.debug(f"  Time to decompress: {time.time() - t:.3f}s")

        return result

    def _get_app_manifests(self, prefix: str) -> Dict[str, dict]:
        """Get manifests for all images matching prefix."""
        import docker
        import subprocess

        client = docker.from_env()
        images = self._get_app_list()

        # Filter by prefix
        target_images = [img for img in images if img["full_tag"].startswith(prefix)]

        manifests = {}

        # Separate local and remote images
        local_images = []
        remote_images = []

        for image_info in target_images:
            image_tag = image_info["full_tag"]
            try:
                client.images.get(image_tag)
                local_images.append(image_info)
            except docker.errors.ImageNotFound:
                remote_images.append(image_info)

        # Process local images
        for image_info in local_images:
            image_tag = image_info["full_tag"]
            try:
                result = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        "-f",
                        '{{ index .Config.Labels "function.manifest.compressed" }}',
                        image_tag,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                compressed_manifest = result.stdout.strip()

                if not compressed_manifest or compressed_manifest == "<no value>":
                    logger.warning(
                        f"  Warning: No manifest label found for {image_tag}"
                    )
                    continue

                manifest_bytes = base64.b64decode(compressed_manifest)
                manifest_json = gzip.decompress(manifest_bytes).decode("utf-8")
                manifests[image_tag] = json.loads(manifest_json)
                logger.info(f"  {image_tag} (local)")

            except subprocess.CalledProcessError as e:
                logger.error(f"  Failed to get manifest for {image_tag}: {e.stderr}")
            except Exception as e:
                logger.error(f"  Error processing {image_tag}: {e}")

        # Process remote images in parallel
        if remote_images:
            t_start = time.time()

            def fetch_remote_manifest(image_info):
                try:
                    manifest = self._get_remote_label(
                        image_info["project_id"],
                        image_info["location"],
                        image_info["repo"],
                        image_info["image"],
                        image_info["tag"],
                    )
                    return image_info["full_tag"], manifest, None
                except Exception as e:
                    return image_info["full_tag"], None, str(e)

            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_image = {
                    executor.submit(fetch_remote_manifest, img): img
                    for img in remote_images
                }

                for future in as_completed(future_to_image):
                    image_tag, manifest, error = future.result()

                    if error:
                        logger.error(f"  Error fetching {image_tag}: {error}")
                    elif manifest:
                        manifests[image_tag] = manifest
                        logger.info(f"  {image_tag}")
                    else:
                        logger.warning(
                            f"  Warning: No manifest label found for {image_tag}"
                        )

            elapsed = time.time() - t_start
            logger.info(
                f"Loaded {len(remote_images)} app manifests in {elapsed:.2f}s "
                f"({elapsed/len(remote_images):.2f}s per app)"
            )

        return manifests


def _update_docker_apps_from_gcloud(
    project_id: str = "repositories-368911",
    location: str = "europe-southwest1",
) -> None:
    """Pull all Docker images from GCloud Artifact Registry.

    Parameters
    ----------
    project_id : str
        GCloud project ID
    location : str
        GCloud location
    """
    from docker import from_env

    docker_client = from_env()
    backend = _DockerManifestBackend("docker://", project_id, location)
    images = backend._get_app_list()

    for image_info in images:
        tag = image_info["full_tag"]
        try:
            logger.info(f"Pulling: {tag} ...")
            docker_client.images.pull(tag)
        except Exception as e:
            logger.error(f"Failed to pull {tag}: {e}")
