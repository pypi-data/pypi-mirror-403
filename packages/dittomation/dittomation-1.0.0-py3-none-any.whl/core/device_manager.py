"""
Unified device management for DittoMation.

This module provides a unified interface to manage devices across:
- Physical Android devices connected via USB/WiFi
- Local Android emulators
- Cloud-based devices (Firebase Test Lab, AWS Device Farm)
"""

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .emulator import EmulatorConfig, EmulatorManager
from .exceptions import (
    DeviceConnectionError,
    DeviceNotFoundError,
    EmulatorError,
)


class DeviceType(Enum):
    """Type of device."""

    PHYSICAL = "physical"
    EMULATOR = "emulator"
    CLOUD = "cloud"


class DeviceStatus(Enum):
    """Device connection status."""

    CONNECTED = "connected"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    STARTING = "starting"
    AVAILABLE = "available"


@dataclass
class UnifiedDevice:
    """Represents a device from any source (physical, emulator, or cloud)."""

    device_id: str
    device_type: DeviceType
    status: DeviceStatus
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    os_version: Optional[str] = None
    sdk_version: Optional[str] = None
    serial: Optional[str] = None  # ADB serial for connected devices
    avd_name: Optional[str] = None  # AVD name for emulators
    cloud_provider: Optional[str] = None  # Cloud provider name
    cloud_device_id: Optional[str] = None  # Cloud device ID
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "status": self.status.value,
            "model": self.model,
            "manufacturer": self.manufacturer,
            "os_version": self.os_version,
            "sdk_version": self.sdk_version,
            "serial": self.serial,
            "avd_name": self.avd_name,
            "cloud_provider": self.cloud_provider,
            "cloud_device_id": self.cloud_device_id,
            "properties": self.properties,
        }


class DeviceManager:
    """
    Unified device management across local/emulator/cloud.

    Provides a single interface to discover, select, and connect to
    Android devices regardless of their source.
    """

    def __init__(
        self,
        adb_path: Optional[str] = None,
        emulator_manager: Optional[EmulatorManager] = None,
    ):
        """
        Initialize DeviceManager.

        Args:
            adb_path: Path to adb executable (auto-detected if not provided).
            emulator_manager: EmulatorManager instance (created if not provided).
        """
        self._adb_path = adb_path
        self._emulator_manager = emulator_manager
        self._cloud_providers: Dict[str, Any] = {}

    @property
    def adb_path(self) -> str:
        """Get the path to the adb executable."""
        if self._adb_path:
            return self._adb_path

        # Try to auto-detect
        import shutil

        path = shutil.which("adb")
        if path:
            self._adb_path = path
            return path

        # Try from emulator manager
        if self._emulator_manager:
            try:
                self._adb_path = self._emulator_manager.adb_path
                return self._adb_path
            except Exception:
                pass

        raise DeviceNotFoundError("ADB not found. Install Android SDK Platform Tools.")

    @property
    def emulator_manager(self) -> EmulatorManager:
        """Get or create the EmulatorManager."""
        if self._emulator_manager is None:
            self._emulator_manager = EmulatorManager()
        return self._emulator_manager

    def register_cloud_provider(self, name: str, provider: Any) -> None:
        """
        Register a cloud provider.

        Args:
            name: Provider name (e.g., "firebase", "aws").
            provider: CloudProvider instance.
        """
        self._cloud_providers[name.lower()] = provider

    def list_all_devices(
        self,
        include_physical: bool = True,
        include_emulators: bool = True,
        include_avds: bool = True,
        include_cloud: bool = False,
        cloud_providers: Optional[List[str]] = None,
    ) -> List[UnifiedDevice]:
        """
        List all available devices from all sources.

        Args:
            include_physical: Include physical devices connected via ADB.
            include_emulators: Include running emulators.
            include_avds: Include available (not running) AVDs.
            include_cloud: Include cloud devices.
            cloud_providers: List of cloud providers to query (all if None).

        Returns:
            List of UnifiedDevice objects.
        """
        devices = []

        if include_physical or include_emulators:
            devices.extend(self._list_adb_devices())

        if include_avds:
            devices.extend(self._list_available_avds())

        if include_cloud:
            providers = cloud_providers or list(self._cloud_providers.keys())
            for provider_name in providers:
                if provider_name in self._cloud_providers:
                    devices.extend(self._list_cloud_devices(provider_name))

        return devices

    def _list_adb_devices(self) -> List[UnifiedDevice]:
        """List devices connected via ADB."""
        devices = []

        try:
            result = subprocess.run(
                [self.adb_path, "devices", "-l"], capture_output=True, text=True, timeout=10
            )

            for line in result.stdout.strip().split("\n")[1:]:  # Skip header
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status_str = parts[1]

                    # Parse status
                    if status_str == "device":
                        status = DeviceStatus.CONNECTED
                    elif status_str == "offline":
                        status = DeviceStatus.OFFLINE
                    elif status_str == "unauthorized":
                        status = DeviceStatus.UNAUTHORIZED
                    else:
                        continue

                    # Determine device type
                    if serial.startswith("emulator-"):
                        device_type = DeviceType.EMULATOR
                        avd_name = self._get_emulator_avd_name(serial)
                    else:
                        device_type = DeviceType.PHYSICAL
                        avd_name = None

                    # Parse additional properties from line
                    props = {}
                    for part in parts[2:]:
                        if ":" in part:
                            key, value = part.split(":", 1)
                            props[key] = value

                    device = UnifiedDevice(
                        device_id=serial,
                        device_type=device_type,
                        status=status,
                        serial=serial,
                        avd_name=avd_name,
                        model=props.get("model"),
                        properties=props,
                    )

                    # Get more details for connected devices
                    if status == DeviceStatus.CONNECTED:
                        device = self._enrich_device_info(device)

                    devices.append(device)

        except Exception:
            pass

        return devices

    def _list_available_avds(self) -> List[UnifiedDevice]:
        """List available AVDs that are not currently running."""
        devices = []

        try:
            # Get running emulators
            running_avds = set()
            for emu in self.emulator_manager.get_running_emulators():
                if emu.avd_name:
                    running_avds.add(emu.avd_name)

            # Get all AVDs
            for avd in self.emulator_manager.list_avds():
                if avd.name not in running_avds:
                    device = UnifiedDevice(
                        device_id=f"avd:{avd.name}",
                        device_type=DeviceType.EMULATOR,
                        status=DeviceStatus.AVAILABLE,
                        avd_name=avd.name,
                        model=avd.device,
                        properties={
                            "path": avd.path,
                            "target": avd.target,
                            "abi": avd.abi,
                            "skin": avd.skin,
                        },
                    )
                    devices.append(device)

        except Exception:
            pass

        return devices

    def _list_cloud_devices(self, provider_name: str) -> List[UnifiedDevice]:
        """List devices from a cloud provider."""
        devices = []

        provider = self._cloud_providers.get(provider_name)
        if not provider:
            return devices

        try:
            cloud_devices = provider.list_devices()
            for cd in cloud_devices:
                device = UnifiedDevice(
                    device_id=f"cloud:{provider_name}:{cd.model}",
                    device_type=DeviceType.CLOUD,
                    status=DeviceStatus.AVAILABLE,
                    model=cd.model,
                    manufacturer=cd.manufacturer,
                    os_version=cd.os_version,
                    cloud_provider=provider_name,
                    cloud_device_id=cd.device_id,
                    properties=cd.to_dict() if hasattr(cd, "to_dict") else {},
                )
                devices.append(device)
        except Exception:
            pass

        return devices

    def _get_emulator_avd_name(self, serial: str) -> Optional[str]:
        """Get AVD name for a running emulator."""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "emu", "avd", "name"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines:
                    return lines[0].strip()
        except Exception:
            pass
        return None

    def _enrich_device_info(self, device: UnifiedDevice) -> UnifiedDevice:
        """Enrich device with additional information from ADB."""
        if not device.serial or device.status != DeviceStatus.CONNECTED:
            return device

        props_to_get = {
            "ro.product.model": "model",
            "ro.product.manufacturer": "manufacturer",
            "ro.build.version.release": "os_version",
            "ro.build.version.sdk": "sdk_version",
        }

        for prop, attr in props_to_get.items():
            if getattr(device, attr):
                continue
            try:
                result = subprocess.run(
                    [self.adb_path, "-s", device.serial, "shell", "getprop", prop],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    value = result.stdout.strip()
                    if value:
                        setattr(device, attr, value)
            except Exception:
                pass

        return device

    def select_device(
        self,
        device_type: Optional[DeviceType] = None,
        model: Optional[str] = None,
        serial: Optional[str] = None,
        avd_name: Optional[str] = None,
        prefer_emulator: bool = False,
    ) -> Optional[UnifiedDevice]:
        """
        Select a device based on criteria.

        Args:
            device_type: Preferred device type.
            model: Device model to match.
            serial: Specific serial number.
            avd_name: Specific AVD name.
            prefer_emulator: Prefer emulators over physical devices.

        Returns:
            Selected UnifiedDevice or None if no match found.
        """
        devices = self.list_all_devices(include_cloud=False)

        # Filter by criteria
        candidates = []
        for device in devices:
            if serial and device.serial == serial:
                return device
            if avd_name and device.avd_name == avd_name:
                return device
            if device_type and device.device_type != device_type:
                continue
            if model and device.model and model.lower() not in device.model.lower():
                continue
            if device.status not in (DeviceStatus.CONNECTED, DeviceStatus.AVAILABLE):
                continue
            candidates.append(device)

        if not candidates:
            return None

        # Sort by preference
        def sort_key(d: UnifiedDevice) -> tuple:
            # Connected devices first
            status_priority = 0 if d.status == DeviceStatus.CONNECTED else 1
            # Emulator preference
            type_priority = 0 if prefer_emulator and d.device_type == DeviceType.EMULATOR else 1
            if not prefer_emulator and d.device_type == DeviceType.PHYSICAL:
                type_priority = 0
            return (status_priority, type_priority)

        candidates.sort(key=sort_key)
        return candidates[0]

    def connect(
        self,
        device: Union[UnifiedDevice, str],
        start_if_avd: bool = True,
        emulator_config: Optional[EmulatorConfig] = None,
        boot_timeout: int = 300,
    ) -> str:
        """
        Connect to a device and return its ADB serial.

        For physical devices or running emulators, returns the serial directly.
        For AVDs, starts the emulator first if start_if_avd is True.
        For cloud devices, raises an error (use cloud provider directly).

        Args:
            device: UnifiedDevice or device identifier string.
            start_if_avd: Start AVD if device is an available AVD.
            emulator_config: Configuration for starting emulator.
            boot_timeout: Timeout for emulator boot.

        Returns:
            ADB serial number for the connected device.

        Raises:
            DeviceNotFoundError: If device cannot be found.
            DeviceConnectionError: If connection fails.
            EmulatorError: If emulator fails to start.
        """
        # Resolve device if string
        if isinstance(device, str):
            device = self._resolve_device(device)
            if not device:
                raise DeviceNotFoundError(f"Device not found: {device}")

        # Handle based on device type and status
        if device.device_type == DeviceType.CLOUD:
            raise DeviceConnectionError(
                f"Cannot connect directly to cloud device. "
                f"Use cloud provider '{device.cloud_provider}' to acquire the device."
            )

        if device.status == DeviceStatus.CONNECTED:
            return device.serial

        if device.status == DeviceStatus.AVAILABLE and device.device_type == DeviceType.EMULATOR:
            if not start_if_avd:
                raise DeviceConnectionError(
                    f"AVD '{device.avd_name}' is not running. "
                    "Set start_if_avd=True to start it automatically."
                )

            # Start the emulator
            try:
                instance = self.emulator_manager.start(
                    device.avd_name,
                    config=emulator_config,
                    wait_boot=True,
                    timeout=boot_timeout,
                )
                return instance.serial
            except EmulatorError:
                raise
            except Exception as e:
                raise DeviceConnectionError(f"Failed to start emulator: {e}")

        if device.status == DeviceStatus.OFFLINE:
            raise DeviceConnectionError(
                f"Device '{device.device_id}' is offline. " "Check the connection and try again."
            )

        if device.status == DeviceStatus.UNAUTHORIZED:
            raise DeviceConnectionError(
                f"Device '{device.device_id}' is unauthorized. "
                "Check the device screen and authorize USB debugging."
            )

        raise DeviceNotFoundError(f"Cannot connect to device: {device.device_id}")

    def _resolve_device(self, identifier: str) -> Optional[UnifiedDevice]:
        """Resolve a device identifier to a UnifiedDevice."""
        devices = self.list_all_devices(include_cloud=True)

        for device in devices:
            if device.device_id == identifier:
                return device
            if device.serial == identifier:
                return device
            if device.avd_name == identifier:
                return device
            if identifier.startswith("avd:") and device.avd_name == identifier[4:]:
                return device

        return None

    def auto_connect(
        self,
        prefer_emulator: bool = False,
        start_avd: Optional[str] = None,
        emulator_config: Optional[EmulatorConfig] = None,
        boot_timeout: int = 300,
    ) -> str:
        """
        Automatically connect to an available device.

        Tries to find and connect to a device in this order:
        1. Specific AVD if start_avd is provided
        2. Already connected device (physical or emulator)
        3. Start first available AVD

        Args:
            prefer_emulator: Prefer emulators over physical devices.
            start_avd: Specific AVD to start if no device is connected.
            emulator_config: Configuration for starting emulator.
            boot_timeout: Timeout for emulator boot.

        Returns:
            ADB serial number for the connected device.

        Raises:
            DeviceNotFoundError: If no device can be connected.
        """
        # If specific AVD requested, try to start it
        if start_avd:
            device = self.select_device(avd_name=start_avd)
            if device:
                return self.connect(
                    device,
                    start_if_avd=True,
                    emulator_config=emulator_config,
                    boot_timeout=boot_timeout,
                )
            raise DeviceNotFoundError(f"AVD not found: {start_avd}")

        # Try to find an already connected device
        devices = self.list_all_devices(include_cloud=False)
        connected = [d for d in devices if d.status == DeviceStatus.CONNECTED]

        if connected:
            # Sort by preference
            if prefer_emulator:
                connected.sort(key=lambda d: 0 if d.device_type == DeviceType.EMULATOR else 1)
            else:
                connected.sort(key=lambda d: 0 if d.device_type == DeviceType.PHYSICAL else 1)
            return connected[0].serial

        # Try to start an available AVD
        available_avds = [
            d
            for d in devices
            if d.device_type == DeviceType.EMULATOR and d.status == DeviceStatus.AVAILABLE
        ]

        if available_avds:
            return self.connect(
                available_avds[0],
                start_if_avd=True,
                emulator_config=emulator_config,
                boot_timeout=boot_timeout,
            )

        raise DeviceNotFoundError(
            "No device available. Connect a physical device or create an AVD."
        )

    def disconnect(self, serial: str) -> bool:
        """
        Disconnect from a device.

        For emulators, this stops the emulator.
        For physical devices, this does nothing (can't disconnect USB programmatically).

        Args:
            serial: ADB serial number.

        Returns:
            True if disconnected successfully.
        """
        if serial.startswith("emulator-"):
            try:
                return self.emulator_manager.stop(serial)
            except Exception:
                return False
        return True
