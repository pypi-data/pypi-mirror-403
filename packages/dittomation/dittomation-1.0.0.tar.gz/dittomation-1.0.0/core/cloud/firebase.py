"""
Firebase Test Lab provider for DittoMation.

This module provides integration with Google's Firebase Test Lab for
running automated tests on real and virtual Android devices in the cloud.

Requires:
    - gcloud CLI installed and configured
    - Firebase Test Lab API enabled
    - Appropriate IAM permissions
"""

import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..exceptions import (
    CloudAuthenticationError,
    CloudDeviceNotAvailableError,
    CloudProviderError,
    CloudTestRunError,
    CloudTimeoutError,
)
from .base import CloudProvider
from .models import (
    ArtifactType,
    CloudDevice,
    DeviceFilter,
    DeviceFormFactor,
    TestArtifact,
    TestRun,
    TestRunStatus,
)


class FirebaseTestLabProvider(CloudProvider):
    """
    Firebase Test Lab cloud provider.

    Uses the gcloud CLI to interact with Firebase Test Lab.
    Supports running DittoMation workflows on real and virtual devices.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_file: Optional[str] = None,
        gcloud_path: Optional[str] = None,
        results_bucket: Optional[str] = None,
    ):
        """
        Initialize Firebase Test Lab provider.

        Args:
            project_id: Google Cloud project ID.
            credentials_file: Path to service account JSON file.
            gcloud_path: Path to gcloud CLI (auto-detected if not provided).
            results_bucket: GCS bucket for test results.
        """
        self._project_id = project_id or os.environ.get("GCLOUD_PROJECT")
        self._credentials_file = credentials_file
        self._gcloud_path = gcloud_path
        self._results_bucket = results_bucket
        self._authenticated = False
        self._devices_cache: Optional[List[CloudDevice]] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes

    @property
    def name(self) -> str:
        return "firebase"

    @property
    def gcloud_path(self) -> str:
        """Get path to gcloud CLI."""
        if self._gcloud_path:
            return self._gcloud_path

        path = shutil.which("gcloud")
        if path:
            self._gcloud_path = path
            return path

        raise CloudProviderError(
            "firebase",
            "gcloud CLI not found. Install Google Cloud SDK.",
            hint="Download from https://cloud.google.com/sdk/install",
        )

    def _run_gcloud(
        self, args: List[str], timeout: int = 60, check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a gcloud command."""
        cmd = [self.gcloud_path] + args

        if self._project_id:
            cmd.extend(["--project", self._project_id])

        cmd.append("--format=json")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            if check and result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise CloudProviderError("firebase", f"gcloud command failed: {error_msg}")

            return result

        except subprocess.TimeoutExpired:
            raise CloudTimeoutError("firebase", "gcloud command", timeout)

    def authenticate(self) -> bool:
        """Authenticate with Google Cloud."""
        try:
            if self._credentials_file:
                # Activate service account
                result = self._run_gcloud(
                    ["auth", "activate-service-account", f"--key-file={self._credentials_file}"],
                    check=False,
                )

                if result.returncode != 0:
                    raise CloudAuthenticationError(
                        "firebase", f"Failed to activate service account: {result.stderr}"
                    )

            # Verify authentication
            result = self._run_gcloud(["auth", "list"], check=False)

            if result.returncode == 0:
                auth_info = json.loads(result.stdout) if result.stdout else []
                if auth_info:
                    self._authenticated = True
                    return True

            raise CloudAuthenticationError("firebase", "No active account found")

        except CloudAuthenticationError:
            raise
        except Exception as e:
            raise CloudAuthenticationError("firebase", str(e))

    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        if self._authenticated:
            return True

        try:
            result = self._run_gcloud(["auth", "list"], check=False, timeout=10)
            if result.returncode == 0:
                auth_info = json.loads(result.stdout) if result.stdout else []
                self._authenticated = bool(auth_info)
                return self._authenticated
        except Exception:
            pass

        return False

    def list_devices(self, filters: Optional[DeviceFilter] = None) -> List[CloudDevice]:
        """List available devices in Firebase Test Lab."""
        # Check cache
        if self._devices_cache and self._cache_time:
            if time.time() - self._cache_time < self._cache_ttl:
                devices = self._devices_cache
                if filters:
                    devices = [d for d in devices if filters.matches(d)]
                return devices

        try:
            result = self._run_gcloud(["firebase", "test", "android", "models", "list"], timeout=30)

            devices = []
            models = json.loads(result.stdout) if result.stdout else []

            for model in models:
                # Skip deprecated models
                if model.get("deprecated"):
                    continue

                # Determine form factor
                form = model.get("formFactor", "PHONE").upper()
                if form == "PHONE":
                    form_factor = DeviceFormFactor.PHONE
                elif form == "TABLET":
                    form_factor = DeviceFormFactor.TABLET
                elif form == "WEARABLE":
                    form_factor = DeviceFormFactor.WEARABLE
                else:
                    form_factor = DeviceFormFactor.PHONE

                # Get supported versions
                supported_versions = model.get("supportedVersionIds", [])

                for version in supported_versions:
                    device = CloudDevice(
                        device_id=f"{model['id']}_{version}",
                        model=model.get("name", model["id"]),
                        manufacturer=model.get("manufacturer"),
                        os_version=version,
                        sdk_version=self._version_to_sdk(version),
                        form_factor=form_factor,
                        screen_density=model.get("screenDensity"),
                        screen_width=model.get("screenX"),
                        screen_height=model.get("screenY"),
                        supported_abis=model.get("supportedAbis", []),
                        provider="firebase",
                        properties={
                            "model_id": model["id"],
                            "brand": model.get("brand"),
                            "tags": model.get("tags", []),
                        },
                    )
                    devices.append(device)

            self._devices_cache = devices
            self._cache_time = time.time()

            if filters:
                devices = [d for d in devices if filters.matches(d)]

            return devices

        except CloudProviderError:
            raise
        except Exception as e:
            raise CloudProviderError("firebase", f"Failed to list devices: {e}")

    def _version_to_sdk(self, version: str) -> Optional[str]:
        """Convert Android version to SDK level."""
        version_map = {
            "14": "34",
            "13": "33",
            "12": "32",
            "12L": "32",
            "11": "30",
            "10": "29",
            "9": "28",
            "8.1": "27",
            "8.0": "26",
            "7.1": "25",
            "7.0": "24",
        }
        return version_map.get(version)

    def acquire_device(
        self, model: str, os_version: Optional[str] = None, timeout: int = 300
    ) -> CloudDevice:
        """
        Acquire a device for testing.

        Note: Firebase Test Lab doesn't have a separate acquire step.
        This method verifies the device exists and returns it.
        """
        devices = self.list_devices()

        for device in devices:
            if model.lower() in device.model.lower():
                if os_version is None or device.os_version == os_version:
                    return device

        raise CloudDeviceNotAvailableError("firebase", model, os_version)

    def release_device(self, device: CloudDevice) -> bool:
        """Release a device (no-op for Firebase Test Lab)."""
        return True

    def run_test(
        self,
        devices: List[CloudDevice],
        workflow_path: Union[str, Path],
        timeout: int = 3600,
        **options,
    ) -> TestRun:
        """Run a test on Firebase Test Lab."""
        workflow_path = Path(workflow_path)
        if not workflow_path.exists():
            raise CloudTestRunError("firebase", "N/A", f"Workflow file not found: {workflow_path}")

        # For Firebase Test Lab, we need to package the workflow with DittoMation
        # This would typically involve creating an APK or using Robo test
        # For now, we'll use the instrumentation test approach

        # Build device specifications
        device_specs = []
        for device in devices:
            model_id = device.properties.get("model_id", device.device_id.split("_")[0])
            spec = f"model={model_id},version={device.os_version}"
            if device.locale:
                spec += f",locale={device.locale}"
            if device.orientation:
                spec += f",orientation={device.orientation}"
            device_specs.append(spec)

        # Build gcloud command
        cmd = [
            "firebase",
            "test",
            "android",
            "run",
            "--type",
            options.get("test_type", "robo"),
            "--timeout",
            f"{timeout}s",
        ]

        for spec in device_specs:
            cmd.extend(["--device", spec])

        # Add app APK if provided
        if "app_apk" in options:
            cmd.extend(["--app", options["app_apk"]])

        # Add results bucket
        if self._results_bucket:
            cmd.extend(["--results-bucket", self._results_bucket])

        # Add results directory
        results_dir = options.get("results_dir", f"dittomation-{int(time.time())}")
        cmd.extend(["--results-dir", results_dir])

        try:
            result = self._run_gcloud(cmd, timeout=timeout + 60, check=False)

            # Parse the output to get run ID
            run_id = results_dir

            # Check if test started successfully
            if result.returncode != 0 and "error" in result.stderr.lower():
                raise CloudTestRunError("firebase", run_id, result.stderr or "Failed to start test")

            test_run = TestRun(
                run_id=run_id,
                provider="firebase",
                status=TestRunStatus.RUNNING,
                devices=devices,
                workflow_path=str(workflow_path),
                created_at=datetime.now(),
                properties={
                    "results_bucket": self._results_bucket,
                    "results_dir": results_dir,
                },
            )

            return test_run

        except CloudTestRunError:
            raise
        except Exception as e:
            raise CloudTestRunError("firebase", "N/A", str(e))

    def get_run_status(self, run_id: str) -> TestRun:
        """Get the status of a test run."""
        try:
            # Query test matrices
            result = self._run_gcloud(["firebase", "test", "android", "list"], timeout=30)

            matrices = json.loads(result.stdout) if result.stdout else []

            for matrix in matrices:
                if run_id in str(matrix.get("resultStorage", {}).get("resultsDir", "")):
                    status = self._parse_matrix_status(matrix.get("state", ""))
                    return TestRun(
                        run_id=run_id, provider="firebase", status=status, properties=matrix
                    )

            raise CloudTestRunError("firebase", run_id, "Test run not found")

        except CloudTestRunError:
            raise
        except Exception as e:
            raise CloudTestRunError("firebase", run_id, str(e))

    def _parse_matrix_status(self, state: str) -> TestRunStatus:
        """Parse Firebase Test Lab matrix state to TestRunStatus."""
        state_map = {
            "PENDING": TestRunStatus.PENDING,
            "RUNNING": TestRunStatus.RUNNING,
            "FINISHED": TestRunStatus.COMPLETED,
            "ERROR": TestRunStatus.ERROR,
            "CANCELLED": TestRunStatus.CANCELLED,
            "INVALID": TestRunStatus.ERROR,
        }
        return state_map.get(state.upper(), TestRunStatus.PENDING)

    def wait_for_completion(
        self, run: TestRun, timeout: Optional[int] = None, poll_interval: int = 30
    ) -> TestRun:
        """Wait for a test run to complete."""
        start_time = time.time()

        while True:
            updated_run = self.get_run_status(run.run_id)

            if updated_run.is_complete:
                updated_run.completed_at = datetime.now()
                updated_run.duration_seconds = time.time() - start_time
                return updated_run

            if timeout and (time.time() - start_time) > timeout:
                raise CloudTimeoutError("firebase", "wait_for_completion", timeout)

            time.sleep(poll_interval)

    def cancel_run(self, run: TestRun) -> bool:
        """Cancel a running test (limited support in Firebase Test Lab)."""
        # Firebase Test Lab doesn't have a direct cancel API via gcloud
        # Tests will continue running until completion or timeout
        return False

    def list_artifacts(self, run: TestRun) -> List[TestArtifact]:
        """List artifacts from a test run."""
        artifacts = []

        results_bucket = run.properties.get("results_bucket", self._results_bucket)
        results_dir = run.properties.get("results_dir", run.run_id)

        if not results_bucket:
            return artifacts

        try:
            result = self._run_gcloud(
                ["storage", "ls", "-r", f"gs://{results_bucket}/{results_dir}/"],
                timeout=60,
                check=False,
            )

            if result.returncode != 0:
                return artifacts

            for line in result.stdout.strip().split("\n"):
                if not line or line.endswith("/"):
                    continue

                # Parse GCS URL
                name = line.split("/")[-1]
                artifact_type = self._infer_artifact_type(name)

                artifact = TestArtifact(
                    artifact_id=line,
                    name=name,
                    artifact_type=artifact_type,
                    url=line,
                )
                artifacts.append(artifact)

        except Exception:
            pass

        return artifacts

    def _infer_artifact_type(self, filename: str) -> ArtifactType:
        """Infer artifact type from filename."""
        lower = filename.lower()
        if lower.endswith((".png", ".jpg", ".jpeg")):
            return ArtifactType.SCREENSHOT
        elif lower.endswith((".mp4", ".webm")):
            return ArtifactType.VIDEO
        elif lower.endswith((".log", ".txt")):
            return ArtifactType.LOG
        elif "instrumentation" in lower:
            return ArtifactType.INSTRUMENTATION
        elif "perf" in lower or "performance" in lower:
            return ArtifactType.PERFORMANCE
        return ArtifactType.OTHER

    def download_artifact(self, artifact: TestArtifact, output_path: Union[str, Path]) -> Path:
        """Download an artifact from GCS."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._run_gcloud(
                ["storage", "cp", artifact.url, str(output_path)], timeout=300, check=True
            )

            artifact.local_path = str(output_path)
            return output_path

        except Exception as e:
            raise CloudProviderError("firebase", f"Failed to download artifact: {e}")

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "project_id": self._project_id,
            "results_bucket": self._results_bucket,
            "credentials_file": self._credentials_file,
        }

    def set_configuration(self, config: Dict[str, Any]) -> None:
        """Set configuration."""
        if "project_id" in config:
            self._project_id = config["project_id"]
        if "results_bucket" in config:
            self._results_bucket = config["results_bucket"]
        if "credentials_file" in config:
            self._credentials_file = config["credentials_file"]
        # Clear cache when config changes
        self._devices_cache = None
