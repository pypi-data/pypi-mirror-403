"""
AWS Device Farm provider for DittoMation.

This module provides integration with AWS Device Farm for running
automated tests on real Android devices in the AWS cloud.

Requires:
    - boto3 library installed
    - AWS credentials configured
    - Device Farm project ARN
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..exceptions import (
    CloudAuthenticationError,
    CloudDeviceNotAvailableError,
    CloudProviderError,
    CloudQuotaExceededError,
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

# Lazy import boto3
_boto3 = None


def _get_boto3():
    """Lazy import boto3."""
    global _boto3
    if _boto3 is None:
        try:
            import boto3

            _boto3 = boto3
        except ImportError:
            raise CloudProviderError(
                "aws", "boto3 library not installed. Install with: pip install boto3"
            )
    return _boto3


class AWSDeviceFarmProvider(CloudProvider):
    """
    AWS Device Farm cloud provider.

    Uses boto3 to interact with AWS Device Farm API.
    Supports running DittoMation workflows on real Android devices.
    """

    def __init__(
        self,
        project_arn: Optional[str] = None,
        region: str = "us-west-2",
        device_pool_arn: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """
        Initialize AWS Device Farm provider.

        Args:
            project_arn: ARN of the Device Farm project.
            region: AWS region (default: us-west-2).
            device_pool_arn: ARN of a device pool to use.
            aws_access_key_id: AWS access key (uses env/config if not provided).
            aws_secret_access_key: AWS secret key (uses env/config if not provided).
        """
        self._project_arn = project_arn or os.environ.get("AWS_DEVICE_FARM_PROJECT_ARN")
        self._region = region
        self._device_pool_arn = device_pool_arn
        self._client = None
        self._authenticated = False
        self._devices_cache: Optional[List[CloudDevice]] = None
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes

        # Optional explicit credentials
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key

    @property
    def name(self) -> str:
        return "aws"

    @property
    def client(self):
        """Get or create boto3 Device Farm client."""
        if self._client is None:
            boto3 = _get_boto3()

            kwargs = {"region_name": self._region}
            if self._aws_access_key_id and self._aws_secret_access_key:
                kwargs["aws_access_key_id"] = self._aws_access_key_id
                kwargs["aws_secret_access_key"] = self._aws_secret_access_key

            self._client = boto3.client("devicefarm", **kwargs)

        return self._client

    def authenticate(self) -> bool:
        """Authenticate with AWS."""
        try:
            # Try to list projects to verify credentials
            self.client.list_projects(maxResults=1)
            self._authenticated = True
            return True

        except Exception as e:
            error_msg = str(e)
            if "credentials" in error_msg.lower():
                raise CloudAuthenticationError("aws", "Invalid or missing AWS credentials")
            raise CloudAuthenticationError("aws", error_msg)

    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        if self._authenticated:
            return True

        try:
            self.client.list_projects(maxResults=1)
            self._authenticated = True
            return True
        except Exception:
            return False

    def list_devices(self, filters: Optional[DeviceFilter] = None) -> List[CloudDevice]:
        """List available devices in AWS Device Farm."""
        # Check cache
        if self._devices_cache and self._cache_time:
            if time.time() - self._cache_time < self._cache_ttl:
                devices = self._devices_cache
                if filters:
                    devices = [d for d in devices if filters.matches(d)]
                return devices

        try:
            devices = []
            paginator = self.client.get_paginator("list_devices")

            for page in paginator.paginate():
                for device in page.get("devices", []):
                    # Only include Android devices
                    if device.get("platform") != "ANDROID":
                        continue

                    # Determine form factor
                    form_factor = DeviceFormFactor.PHONE
                    ff = device.get("formFactor", "PHONE").upper()
                    if ff == "TABLET":
                        form_factor = DeviceFormFactor.TABLET

                    # Parse resolution
                    resolution = device.get("resolution", {})

                    cloud_device = CloudDevice(
                        device_id=device["arn"],
                        model=device.get("name", device["arn"]),
                        manufacturer=device.get("manufacturer"),
                        os_version=device.get("os"),
                        form_factor=form_factor,
                        screen_width=resolution.get("width"),
                        screen_height=resolution.get("height"),
                        provider="aws",
                        available=device.get("availability") == "AVAILABLE",
                        properties={
                            "arn": device["arn"],
                            "carrier": device.get("carrier"),
                            "fleet_type": device.get("fleetType"),
                            "fleet_name": device.get("fleetName"),
                            "memory": device.get("memory"),
                            "cpu": device.get("cpu"),
                            "heap_size": device.get("heapSize"),
                        },
                    )
                    devices.append(cloud_device)

            self._devices_cache = devices
            self._cache_time = time.time()

            if filters:
                devices = [d for d in devices if filters.matches(d)]

            return devices

        except Exception as e:
            raise CloudProviderError("aws", f"Failed to list devices: {e}")

    def acquire_device(
        self, model: str, os_version: Optional[str] = None, timeout: int = 300
    ) -> CloudDevice:
        """Acquire a device for testing."""
        devices = self.list_devices()

        for device in devices:
            if model.lower() in device.model.lower():
                if os_version is None or device.os_version == os_version:
                    if device.available:
                        return device

        raise CloudDeviceNotAvailableError("aws", model, os_version)

    def release_device(self, device: CloudDevice) -> bool:
        """Release a device (handled automatically by Device Farm)."""
        return True

    def _get_or_create_device_pool(self, devices: List[CloudDevice]) -> str:
        """Get or create a device pool for the specified devices."""
        if self._device_pool_arn:
            return self._device_pool_arn

        if not self._project_arn:
            raise CloudProviderError(
                "aws", "Project ARN not configured. Set project_arn or AWS_DEVICE_FARM_PROJECT_ARN."
            )

        # Create a temporary device pool
        device_arns = [d.properties.get("arn", d.device_id) for d in devices]

        rules = []
        for arn in device_arns:
            rules.append({"attribute": "ARN", "operator": "EQUALS", "value": arn})

        try:
            response = self.client.create_device_pool(
                projectArn=self._project_arn,
                name=f"dittomation-pool-{int(time.time())}",
                rules=rules,
                maxDevices=len(devices),
            )
            return response["devicePool"]["arn"]

        except Exception as e:
            raise CloudProviderError("aws", f"Failed to create device pool: {e}")

    def _upload_app(self, app_path: Path) -> str:
        """Upload an APK to Device Farm."""
        if not self._project_arn:
            raise CloudProviderError("aws", "Project ARN not configured.")

        try:
            # Create upload
            response = self.client.create_upload(
                projectArn=self._project_arn, name=app_path.name, type="ANDROID_APP"
            )

            upload = response["upload"]
            upload_url = upload["url"]
            upload_arn = upload["arn"]

            # Upload the file
            with open(app_path, "rb") as f:
                import requests

                requests.put(upload_url, data=f, timeout=300)

            # Wait for upload to complete
            for _ in range(60):
                response = self.client.get_upload(arn=upload_arn)
                status = response["upload"]["status"]

                if status == "SUCCEEDED":
                    return upload_arn
                elif status == "FAILED":
                    raise CloudProviderError(
                        "aws",
                        f"Upload failed: {response['upload'].get('message', 'Unknown error')}",
                    )

                time.sleep(2)

            raise CloudTimeoutError("aws", "upload", 120)

        except CloudProviderError:
            raise
        except Exception as e:
            raise CloudProviderError("aws", f"Failed to upload app: {e}")

    def run_test(
        self,
        devices: List[CloudDevice],
        workflow_path: Union[str, Path],
        timeout: int = 3600,
        **options,
    ) -> TestRun:
        """Run a test on AWS Device Farm."""
        workflow_path = Path(workflow_path)
        if not workflow_path.exists():
            raise CloudTestRunError("aws", "N/A", f"Workflow file not found: {workflow_path}")

        if not self._project_arn:
            raise CloudProviderError("aws", "Project ARN not configured.")

        try:
            # Get or create device pool
            device_pool_arn = self._get_or_create_device_pool(devices)

            # Upload app if provided
            app_arn = None
            if "app_apk" in options:
                app_arn = self._upload_app(Path(options["app_apk"]))

            # Upload test package if provided
            test_arn = None
            test_type = options.get("test_type", "BUILTIN_FUZZ")

            if "test_package" in options:
                test_arn = self._upload_test_package(Path(options["test_package"]))
                test_type = options.get("test_type", "INSTRUMENTATION")

            # Schedule run
            run_config = {
                "projectArn": self._project_arn,
                "name": f"dittomation-{int(time.time())}",
                "devicePoolArn": device_pool_arn,
                "test": {
                    "type": test_type,
                },
            }

            if app_arn:
                run_config["appArn"] = app_arn

            if test_arn:
                run_config["test"]["testPackageArn"] = test_arn

            # Add execution configuration
            run_config["executionConfiguration"] = {
                "jobTimeoutMinutes": timeout // 60,
                "accountsCleanup": options.get("accounts_cleanup", True),
                "appPackagesCleanup": options.get("app_packages_cleanup", True),
            }

            response = self.client.schedule_run(**run_config)
            run = response["run"]

            test_run = TestRun(
                run_id=run["arn"],
                provider="aws",
                status=self._parse_run_status(run.get("status", "PENDING")),
                devices=devices,
                workflow_path=str(workflow_path),
                created_at=datetime.now(),
                properties={
                    "arn": run["arn"],
                    "device_pool_arn": device_pool_arn,
                    "app_arn": app_arn,
                },
            )

            return test_run

        except CloudProviderError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "LimitExceededException" in error_msg:
                raise CloudQuotaExceededError("aws", "concurrent runs")
            raise CloudTestRunError("aws", "N/A", error_msg)

    def _upload_test_package(self, package_path: Path) -> str:
        """Upload a test package to Device Farm."""
        try:
            response = self.client.create_upload(
                projectArn=self._project_arn,
                name=package_path.name,
                type="INSTRUMENTATION_TEST_PACKAGE",
            )

            upload = response["upload"]
            upload_url = upload["url"]
            upload_arn = upload["arn"]

            with open(package_path, "rb") as f:
                import requests

                requests.put(upload_url, data=f, timeout=300)

            for _ in range(60):
                response = self.client.get_upload(arn=upload_arn)
                status = response["upload"]["status"]

                if status == "SUCCEEDED":
                    return upload_arn
                elif status == "FAILED":
                    raise CloudProviderError("aws", "Test package upload failed")

                time.sleep(2)

            raise CloudTimeoutError("aws", "test package upload", 120)

        except CloudProviderError:
            raise
        except Exception as e:
            raise CloudProviderError("aws", f"Failed to upload test package: {e}")

    def _parse_run_status(self, status: str) -> TestRunStatus:
        """Parse AWS Device Farm run status."""
        status_map = {
            "PENDING": TestRunStatus.PENDING,
            "PENDING_CONCURRENCY": TestRunStatus.PENDING,
            "PENDING_DEVICE": TestRunStatus.PENDING,
            "PROCESSING": TestRunStatus.RUNNING,
            "SCHEDULING": TestRunStatus.RUNNING,
            "PREPARING": TestRunStatus.RUNNING,
            "RUNNING": TestRunStatus.RUNNING,
            "COMPLETED": TestRunStatus.COMPLETED,
            "STOPPING": TestRunStatus.RUNNING,
            "ERRORED": TestRunStatus.ERROR,
        }
        return status_map.get(status.upper(), TestRunStatus.PENDING)

    def get_run_status(self, run_id: str) -> TestRun:
        """Get the status of a test run."""
        try:
            response = self.client.get_run(arn=run_id)
            run = response["run"]

            status = self._parse_run_status(run.get("status", "PENDING"))

            # Parse result
            result = run.get("result", "")
            if result == "PASSED":
                status = TestRunStatus.COMPLETED
            elif result in ("FAILED", "ERRORED"):
                status = TestRunStatus.FAILED

            # Parse timing
            started = run.get("started")
            stopped = run.get("stopped")

            test_run = TestRun(
                run_id=run_id,
                provider="aws",
                status=status,
                started_at=started,
                completed_at=stopped,
                results={
                    "result": run.get("result"),
                    "counters": run.get("counters", {}),
                },
                properties=run,
            )

            if started and stopped:
                test_run.duration_seconds = (stopped - started).total_seconds()

            return test_run

        except Exception as e:
            raise CloudTestRunError("aws", run_id, str(e))

    def wait_for_completion(
        self, run: TestRun, timeout: Optional[int] = None, poll_interval: int = 30
    ) -> TestRun:
        """Wait for a test run to complete."""
        start_time = time.time()

        while True:
            updated_run = self.get_run_status(run.run_id)

            if updated_run.is_complete:
                return updated_run

            if timeout and (time.time() - start_time) > timeout:
                raise CloudTimeoutError("aws", "wait_for_completion", timeout)

            time.sleep(poll_interval)

    def cancel_run(self, run: TestRun) -> bool:
        """Cancel a running test."""
        try:
            self.client.stop_run(arn=run.run_id)
            return True
        except Exception:
            return False

    def list_artifacts(self, run: TestRun) -> List[TestArtifact]:
        """List artifacts from a test run."""
        artifacts = []

        try:
            # List jobs in the run
            jobs_response = self.client.list_jobs(arn=run.run_id)

            for job in jobs_response.get("jobs", []):
                # List suites in each job
                suites_response = self.client.list_suites(arn=job["arn"])

                for suite in suites_response.get("suites", []):
                    # List tests in each suite
                    tests_response = self.client.list_tests(arn=suite["arn"])

                    for test in tests_response.get("tests", []):
                        # List artifacts for each test
                        for artifact_type in ["FILE", "LOG", "SCREENSHOT"]:
                            art_response = self.client.list_artifacts(
                                arn=test["arn"], type=artifact_type
                            )

                            for art in art_response.get("artifacts", []):
                                artifact = TestArtifact(
                                    artifact_id=art["arn"],
                                    name=art.get("name", "unnamed"),
                                    artifact_type=self._map_artifact_type(art.get("type", "")),
                                    url=art.get("url"),
                                    properties={
                                        "extension": art.get("extension"),
                                        "job_arn": job["arn"],
                                        "suite_arn": suite["arn"],
                                        "test_arn": test["arn"],
                                    },
                                )
                                artifacts.append(artifact)

        except Exception:
            pass

        return artifacts

    def _map_artifact_type(self, aws_type: str) -> ArtifactType:
        """Map AWS artifact type to ArtifactType."""
        type_map = {
            "SCREENSHOT": ArtifactType.SCREENSHOT,
            "VIDEO": ArtifactType.VIDEO,
            "LOG": ArtifactType.LOG,
            "DEVICE_LOG": ArtifactType.LOG,
            "LOGCAT": ArtifactType.LOG,
            "INSTRUMENTATION_OUTPUT": ArtifactType.INSTRUMENTATION,
            "PERFORMANCE_DATA": ArtifactType.PERFORMANCE,
        }
        return type_map.get(aws_type.upper(), ArtifactType.OTHER)

    def download_artifact(self, artifact: TestArtifact, output_path: Union[str, Path]) -> Path:
        """Download an artifact."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not artifact.url:
            raise CloudProviderError("aws", "Artifact has no download URL")

        try:
            import requests

            response = requests.get(artifact.url, stream=True, timeout=300)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            artifact.local_path = str(output_path)
            return output_path

        except Exception as e:
            raise CloudProviderError("aws", f"Failed to download artifact: {e}")

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "project_arn": self._project_arn,
            "region": self._region,
            "device_pool_arn": self._device_pool_arn,
        }

    def set_configuration(self, config: Dict[str, Any]) -> None:
        """Set configuration."""
        if "project_arn" in config:
            self._project_arn = config["project_arn"]
        if "region" in config:
            self._region = config["region"]
            self._client = None  # Reset client for new region
        if "device_pool_arn" in config:
            self._device_pool_arn = config["device_pool_arn"]
        # Clear cache when config changes
        self._devices_cache = None
