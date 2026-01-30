"""
Data models for cloud provider integration.

This module defines the common data structures used across all cloud providers.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TestRunStatus(Enum):
    """Status of a cloud test run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    ERROR = "error"


class DeviceFormFactor(Enum):
    """Device form factor."""

    PHONE = "phone"
    TABLET = "tablet"
    WEARABLE = "wearable"
    TV = "tv"
    AUTO = "auto"


@dataclass
class CloudDevice:
    """
    Represents a device available in a cloud testing platform.

    Attributes:
        device_id: Unique identifier for the device in the cloud platform.
        model: Device model name (e.g., "Pixel 6").
        manufacturer: Device manufacturer (e.g., "Google").
        os_version: Android version (e.g., "13").
        sdk_version: Android SDK level (e.g., "33").
        form_factor: Device form factor (phone, tablet, etc.).
        screen_density: Screen density in DPI.
        screen_width: Screen width in pixels.
        screen_height: Screen height in pixels.
        supported_abis: List of supported CPU architectures.
        locale: Default locale.
        orientation: Default orientation.
        provider: Cloud provider name.
        available: Whether the device is currently available.
        properties: Additional provider-specific properties.
    """

    device_id: str
    model: str
    manufacturer: Optional[str] = None
    os_version: Optional[str] = None
    sdk_version: Optional[str] = None
    form_factor: DeviceFormFactor = DeviceFormFactor.PHONE
    screen_density: Optional[int] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    supported_abis: List[str] = field(default_factory=list)
    locale: str = "en_US"
    orientation: str = "portrait"
    provider: Optional[str] = None
    available: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "model": self.model,
            "manufacturer": self.manufacturer,
            "os_version": self.os_version,
            "sdk_version": self.sdk_version,
            "form_factor": self.form_factor.value,
            "screen_density": self.screen_density,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "supported_abis": self.supported_abis,
            "locale": self.locale,
            "orientation": self.orientation,
            "provider": self.provider,
            "available": self.available,
            "properties": self.properties,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CloudDevice":
        """Create from dictionary."""
        form_factor = data.get("form_factor", "phone")
        if isinstance(form_factor, str):
            form_factor = DeviceFormFactor(form_factor)

        return cls(
            device_id=data["device_id"],
            model=data["model"],
            manufacturer=data.get("manufacturer"),
            os_version=data.get("os_version"),
            sdk_version=data.get("sdk_version"),
            form_factor=form_factor,
            screen_density=data.get("screen_density"),
            screen_width=data.get("screen_width"),
            screen_height=data.get("screen_height"),
            supported_abis=data.get("supported_abis", []),
            locale=data.get("locale", "en_US"),
            orientation=data.get("orientation", "portrait"),
            provider=data.get("provider"),
            available=data.get("available", True),
            properties=data.get("properties", {}),
        )


@dataclass
class TestRun:
    """
    Represents a test run on a cloud platform.

    Attributes:
        run_id: Unique identifier for the test run.
        provider: Cloud provider name.
        status: Current status of the test run.
        devices: List of devices the test is running on.
        workflow_path: Path to the workflow file being executed.
        created_at: When the test run was created.
        started_at: When the test actually started.
        completed_at: When the test completed.
        duration_seconds: Total duration in seconds.
        results: Test results summary.
        artifacts: List of artifacts generated.
        error_message: Error message if the run failed.
        properties: Additional provider-specific properties.
    """

    run_id: str
    provider: str
    status: TestRunStatus = TestRunStatus.PENDING
    devices: List[CloudDevice] = field(default_factory=list)
    workflow_path: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    results: Dict[str, Any] = field(default_factory=dict)
    artifacts: List["TestArtifact"] = field(default_factory=list)
    error_message: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if the test run is complete."""
        return self.status in (
            TestRunStatus.COMPLETED,
            TestRunStatus.FAILED,
            TestRunStatus.CANCELLED,
            TestRunStatus.TIMEOUT,
            TestRunStatus.ERROR,
        )

    @property
    def is_successful(self) -> bool:
        """Check if the test run completed successfully."""
        return self.status == TestRunStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "provider": self.provider,
            "status": self.status.value,
            "devices": [d.to_dict() for d in self.devices],
            "workflow_path": self.workflow_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "results": self.results,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "error_message": self.error_message,
            "properties": self.properties,
        }


class ArtifactType(Enum):
    """Type of test artifact."""

    SCREENSHOT = "screenshot"
    VIDEO = "video"
    LOG = "log"
    INSTRUMENTATION = "instrumentation"
    PERFORMANCE = "performance"
    OTHER = "other"


@dataclass
class TestArtifact:
    """
    Represents an artifact from a cloud test run.

    Attributes:
        artifact_id: Unique identifier for the artifact.
        name: Display name of the artifact.
        artifact_type: Type of artifact.
        url: URL to download the artifact.
        local_path: Local path if already downloaded.
        size_bytes: Size of the artifact in bytes.
        device_id: Device that generated this artifact.
        timestamp: When the artifact was created.
        properties: Additional properties.
    """

    artifact_id: str
    name: str
    artifact_type: ArtifactType = ArtifactType.OTHER
    url: Optional[str] = None
    local_path: Optional[str] = None
    size_bytes: Optional[int] = None
    device_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "artifact_type": self.artifact_type.value,
            "url": self.url,
            "local_path": self.local_path,
            "size_bytes": self.size_bytes,
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "properties": self.properties,
        }


@dataclass
class DeviceFilter:
    """
    Filter criteria for selecting cloud devices.

    Attributes:
        models: List of model names to include.
        manufacturers: List of manufacturers to include.
        os_versions: List of OS versions to include.
        min_sdk: Minimum SDK version.
        max_sdk: Maximum SDK version.
        form_factors: List of form factors to include.
        abis: List of CPU architectures to include.
    """

    models: Optional[List[str]] = None
    manufacturers: Optional[List[str]] = None
    os_versions: Optional[List[str]] = None
    min_sdk: Optional[int] = None
    max_sdk: Optional[int] = None
    form_factors: Optional[List[DeviceFormFactor]] = None
    abis: Optional[List[str]] = None

    def matches(self, device: CloudDevice) -> bool:
        """Check if a device matches this filter."""
        if self.models and device.model not in self.models:
            return False
        if self.manufacturers and device.manufacturer not in self.manufacturers:
            return False
        if self.os_versions and device.os_version not in self.os_versions:
            return False
        if self.min_sdk and device.sdk_version:
            try:
                if int(device.sdk_version) < self.min_sdk:
                    return False
            except ValueError:
                pass
        if self.max_sdk and device.sdk_version:
            try:
                if int(device.sdk_version) > self.max_sdk:
                    return False
            except ValueError:
                pass
        if self.form_factors and device.form_factor not in self.form_factors:
            return False
        if self.abis:
            if not any(abi in device.supported_abis for abi in self.abis):
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "models": self.models,
            "manufacturers": self.manufacturers,
            "os_versions": self.os_versions,
            "min_sdk": self.min_sdk,
            "max_sdk": self.max_sdk,
            "form_factors": [f.value for f in self.form_factors] if self.form_factors else None,
            "abis": self.abis,
        }
