"""Tests for core.cloud.models module."""

from datetime import datetime

from core.cloud.models import (
    ArtifactType,
    CloudDevice,
    DeviceFilter,
    DeviceFormFactor,
    TestArtifact,
    TestRun,
    TestRunStatus,
)


class TestTestRunStatus:
    """Tests for TestRunStatus enum."""

    def test_enum_values(self):
        assert TestRunStatus.PENDING.value == "pending"
        assert TestRunStatus.RUNNING.value == "running"
        assert TestRunStatus.COMPLETED.value == "completed"
        assert TestRunStatus.FAILED.value == "failed"
        assert TestRunStatus.CANCELLED.value == "cancelled"
        assert TestRunStatus.TIMEOUT.value == "timeout"
        assert TestRunStatus.ERROR.value == "error"


class TestDeviceFormFactor:
    """Tests for DeviceFormFactor enum."""

    def test_enum_values(self):
        assert DeviceFormFactor.PHONE.value == "phone"
        assert DeviceFormFactor.TABLET.value == "tablet"
        assert DeviceFormFactor.WEARABLE.value == "wearable"
        assert DeviceFormFactor.TV.value == "tv"
        assert DeviceFormFactor.AUTO.value == "auto"


class TestCloudDevice:
    """Tests for CloudDevice dataclass."""

    def test_create_minimal(self):
        device = CloudDevice(device_id="device-1", model="Pixel 6")
        assert device.device_id == "device-1"
        assert device.model == "Pixel 6"
        assert device.form_factor == DeviceFormFactor.PHONE
        assert device.available is True

    def test_create_full(self):
        device = CloudDevice(
            device_id="device-1",
            model="Pixel 6",
            manufacturer="Google",
            os_version="13",
            sdk_version="33",
            form_factor=DeviceFormFactor.PHONE,
            screen_density=420,
            screen_width=1080,
            screen_height=2400,
            supported_abis=["arm64-v8a", "armeabi-v7a"],
            locale="en_US",
            orientation="portrait",
            provider="firebase",
            available=True,
            properties={"custom": "value"},
        )
        assert device.manufacturer == "Google"
        assert device.os_version == "13"
        assert "arm64-v8a" in device.supported_abis

    def test_to_dict(self):
        device = CloudDevice(
            device_id="device-1",
            model="Pixel 6",
            form_factor=DeviceFormFactor.TABLET,
        )
        d = device.to_dict()

        assert d["device_id"] == "device-1"
        assert d["model"] == "Pixel 6"
        assert d["form_factor"] == "tablet"

    def test_from_dict(self):
        data = {
            "device_id": "device-2",
            "model": "Galaxy S23",
            "manufacturer": "Samsung",
            "os_version": "14",
            "form_factor": "phone",
        }
        device = CloudDevice.from_dict(data)

        assert device.device_id == "device-2"
        assert device.model == "Galaxy S23"
        assert device.manufacturer == "Samsung"
        assert device.form_factor == DeviceFormFactor.PHONE

    def test_from_dict_minimal(self):
        data = {"device_id": "d1", "model": "Test"}
        device = CloudDevice.from_dict(data)
        assert device.device_id == "d1"
        assert device.locale == "en_US"  # Default


class TestTestRun:
    """Tests for TestRun dataclass."""

    def test_create_minimal(self):
        run = TestRun(run_id="run-1", provider="firebase")
        assert run.run_id == "run-1"
        assert run.provider == "firebase"
        assert run.status == TestRunStatus.PENDING

    def test_is_complete_pending(self):
        run = TestRun(run_id="run-1", provider="firebase", status=TestRunStatus.PENDING)
        assert run.is_complete is False

    def test_is_complete_running(self):
        run = TestRun(run_id="run-1", provider="firebase", status=TestRunStatus.RUNNING)
        assert run.is_complete is False

    def test_is_complete_completed(self):
        run = TestRun(run_id="run-1", provider="firebase", status=TestRunStatus.COMPLETED)
        assert run.is_complete is True

    def test_is_complete_failed(self):
        run = TestRun(run_id="run-1", provider="firebase", status=TestRunStatus.FAILED)
        assert run.is_complete is True

    def test_is_complete_cancelled(self):
        run = TestRun(run_id="run-1", provider="firebase", status=TestRunStatus.CANCELLED)
        assert run.is_complete is True

    def test_is_successful_completed(self):
        run = TestRun(run_id="run-1", provider="firebase", status=TestRunStatus.COMPLETED)
        assert run.is_successful is True

    def test_is_successful_failed(self):
        run = TestRun(run_id="run-1", provider="firebase", status=TestRunStatus.FAILED)
        assert run.is_successful is False

    def test_to_dict(self):
        now = datetime.now()
        device = CloudDevice(device_id="d1", model="Test")
        artifact = TestArtifact(artifact_id="a1", name="screenshot.png")

        run = TestRun(
            run_id="run-1",
            provider="aws",
            status=TestRunStatus.COMPLETED,
            devices=[device],
            workflow_path="/path/to/workflow.json",
            created_at=now,
            duration_seconds=120.5,
            artifacts=[artifact],
        )
        d = run.to_dict()

        assert d["run_id"] == "run-1"
        assert d["provider"] == "aws"
        assert d["status"] == "completed"
        assert len(d["devices"]) == 1
        assert d["duration_seconds"] == 120.5


class TestTestArtifact:
    """Tests for TestArtifact dataclass."""

    def test_create_minimal(self):
        artifact = TestArtifact(artifact_id="a1", name="test.png")
        assert artifact.artifact_id == "a1"
        assert artifact.name == "test.png"
        assert artifact.artifact_type == ArtifactType.OTHER

    def test_create_full(self):
        now = datetime.now()
        artifact = TestArtifact(
            artifact_id="a1",
            name="screenshot.png",
            artifact_type=ArtifactType.SCREENSHOT,
            url="https://example.com/screenshot.png",
            local_path="/tmp/screenshot.png",
            size_bytes=12345,
            device_id="device-1",
            timestamp=now,
            properties={"step": 5},
        )
        assert artifact.artifact_type == ArtifactType.SCREENSHOT
        assert artifact.size_bytes == 12345

    def test_to_dict(self):
        artifact = TestArtifact(
            artifact_id="a1",
            name="video.mp4",
            artifact_type=ArtifactType.VIDEO,
        )
        d = artifact.to_dict()

        assert d["artifact_id"] == "a1"
        assert d["name"] == "video.mp4"
        assert d["artifact_type"] == "video"


class TestArtifactType:
    """Tests for ArtifactType enum."""

    def test_enum_values(self):
        assert ArtifactType.SCREENSHOT.value == "screenshot"
        assert ArtifactType.VIDEO.value == "video"
        assert ArtifactType.LOG.value == "log"
        assert ArtifactType.INSTRUMENTATION.value == "instrumentation"
        assert ArtifactType.PERFORMANCE.value == "performance"
        assert ArtifactType.OTHER.value == "other"


class TestDeviceFilter:
    """Tests for DeviceFilter dataclass."""

    def test_create_empty(self):
        filter_ = DeviceFilter()
        assert filter_.models is None
        assert filter_.min_sdk is None

    def test_matches_no_filter(self):
        filter_ = DeviceFilter()
        device = CloudDevice(device_id="d1", model="Pixel 6")
        assert filter_.matches(device) is True

    def test_matches_model_filter(self):
        filter_ = DeviceFilter(models=["Pixel 6", "Pixel 7"])
        device1 = CloudDevice(device_id="d1", model="Pixel 6")
        device2 = CloudDevice(device_id="d2", model="Galaxy S23")

        assert filter_.matches(device1) is True
        assert filter_.matches(device2) is False

    def test_matches_manufacturer_filter(self):
        filter_ = DeviceFilter(manufacturers=["Google"])
        device1 = CloudDevice(device_id="d1", model="Pixel 6", manufacturer="Google")
        device2 = CloudDevice(device_id="d2", model="Galaxy", manufacturer="Samsung")

        assert filter_.matches(device1) is True
        assert filter_.matches(device2) is False

    def test_matches_os_version_filter(self):
        filter_ = DeviceFilter(os_versions=["13", "14"])
        device1 = CloudDevice(device_id="d1", model="Test", os_version="13")
        device2 = CloudDevice(device_id="d2", model="Test", os_version="12")

        assert filter_.matches(device1) is True
        assert filter_.matches(device2) is False

    def test_matches_min_sdk_filter(self):
        filter_ = DeviceFilter(min_sdk=30)
        device1 = CloudDevice(device_id="d1", model="Test", sdk_version="33")
        device2 = CloudDevice(device_id="d2", model="Test", sdk_version="28")

        assert filter_.matches(device1) is True
        assert filter_.matches(device2) is False

    def test_matches_max_sdk_filter(self):
        filter_ = DeviceFilter(max_sdk=32)
        device1 = CloudDevice(device_id="d1", model="Test", sdk_version="30")
        device2 = CloudDevice(device_id="d2", model="Test", sdk_version="34")

        assert filter_.matches(device1) is True
        assert filter_.matches(device2) is False

    def test_matches_form_factor_filter(self):
        filter_ = DeviceFilter(form_factors=[DeviceFormFactor.PHONE])
        device1 = CloudDevice(device_id="d1", model="Phone", form_factor=DeviceFormFactor.PHONE)
        device2 = CloudDevice(device_id="d2", model="Tab", form_factor=DeviceFormFactor.TABLET)

        assert filter_.matches(device1) is True
        assert filter_.matches(device2) is False

    def test_matches_abi_filter(self):
        filter_ = DeviceFilter(abis=["arm64-v8a"])
        device1 = CloudDevice(device_id="d1", model="Test", supported_abis=["arm64-v8a"])
        device2 = CloudDevice(device_id="d2", model="Test", supported_abis=["x86"])

        assert filter_.matches(device1) is True
        assert filter_.matches(device2) is False

    def test_to_dict(self):
        filter_ = DeviceFilter(
            models=["Pixel 6"],
            min_sdk=30,
            form_factors=[DeviceFormFactor.PHONE],
        )
        d = filter_.to_dict()

        assert d["models"] == ["Pixel 6"]
        assert d["min_sdk"] == 30
        assert d["form_factors"] == ["phone"]

    def test_matches_combined_filters(self):
        filter_ = DeviceFilter(
            manufacturers=["Google"],
            min_sdk=30,
            form_factors=[DeviceFormFactor.PHONE],
        )
        device = CloudDevice(
            device_id="d1",
            model="Pixel 6",
            manufacturer="Google",
            sdk_version="33",
            form_factor=DeviceFormFactor.PHONE,
        )
        assert filter_.matches(device) is True

        # Fail on manufacturer
        device2 = CloudDevice(
            device_id="d2",
            model="Galaxy",
            manufacturer="Samsung",
            sdk_version="33",
            form_factor=DeviceFormFactor.PHONE,
        )
        assert filter_.matches(device2) is False
