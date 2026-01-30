"""
Emulator management for DittoMation.

This module provides functionality to manage Android emulators:
- List available AVDs (Android Virtual Devices)
- Start emulators in headless mode for CI/CD
- Stop emulators gracefully or forcefully
- Wait for emulator boot completion
- Monitor running emulator instances
"""

import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .exceptions import (
    AVDNotFoundError,
    EmulatorBootTimeoutError,
    EmulatorError,
    EmulatorNotRunningError,
    EmulatorStartError,
)


class EmulatorState(Enum):
    """Emulator state enum."""

    STARTING = "starting"
    BOOTING = "booting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AVDInfo:
    """Information about an Android Virtual Device."""

    name: str
    device: Optional[str] = None
    path: Optional[str] = None
    target: Optional[str] = None
    abi: Optional[str] = None
    skin: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "device": self.device,
            "path": self.path,
            "target": self.target,
            "abi": self.abi,
            "skin": self.skin,
        }


@dataclass
class EmulatorConfig:
    """Configuration for starting an emulator."""

    headless: bool = True
    gpu: str = "swiftshader_indirect"
    memory_mb: int = 2048
    cores: int = 2
    no_audio: bool = True
    no_boot_anim: bool = True
    no_window: bool = True
    wipe_data: bool = False
    read_only: bool = False
    port: Optional[int] = None
    extra_args: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmulatorConfig":
        """Create config from dictionary."""
        return cls(
            headless=data.get("headless", True),
            gpu=data.get("gpu", "swiftshader_indirect"),
            memory_mb=data.get("memory_mb", 2048),
            cores=data.get("cores", 2),
            no_audio=data.get("no_audio", True),
            no_boot_anim=data.get("no_boot_anim", True),
            no_window=data.get("no_window", True),
            wipe_data=data.get("wipe_data", False),
            read_only=data.get("read_only", False),
            port=data.get("port"),
            extra_args=data.get("extra_args", []),
        )


@dataclass
class EmulatorInstance:
    """Represents a running emulator instance."""

    serial: str
    avd_name: Optional[str] = None
    pid: Optional[int] = None
    port: Optional[int] = None
    state: EmulatorState = EmulatorState.STARTING
    boot_completed: bool = False
    process: Optional[subprocess.Popen] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "serial": self.serial,
            "avd_name": self.avd_name,
            "pid": self.pid,
            "port": self.port,
            "state": self.state.value,
            "boot_completed": self.boot_completed,
        }


class EmulatorManager:
    """
    Manages Android emulator lifecycle.

    Provides methods to list, start, stop, and monitor Android emulators.
    Supports headless mode for CI/CD environments.
    """

    # Default paths for emulator and SDK tools
    DEFAULT_EMULATOR_NAMES = ["emulator", "emulator.exe"]
    DEFAULT_ADB_NAMES = ["adb", "adb.exe"]

    def __init__(
        self,
        android_home: Optional[str] = None,
        emulator_path: Optional[str] = None,
        adb_path: Optional[str] = None,
    ):
        """
        Initialize EmulatorManager.

        Args:
            android_home: Path to Android SDK (defaults to ANDROID_HOME env var)
            emulator_path: Path to emulator executable (auto-detected if not provided)
            adb_path: Path to adb executable (auto-detected if not provided)
        """
        self.android_home = (
            android_home or os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        )
        self._emulator_path = emulator_path
        self._adb_path = adb_path
        self._running_instances: Dict[str, EmulatorInstance] = {}

    @property
    def emulator_path(self) -> str:
        """Get the path to the emulator executable."""
        if self._emulator_path:
            return self._emulator_path

        # Try to find emulator in common locations
        search_paths = []

        if self.android_home:
            search_paths.extend(
                [
                    os.path.join(self.android_home, "emulator"),
                    os.path.join(self.android_home, "tools"),
                ]
            )

        # Also search PATH
        for name in self.DEFAULT_EMULATOR_NAMES:
            path = shutil.which(name)
            if path:
                self._emulator_path = path
                return path

        for base_path in search_paths:
            for name in self.DEFAULT_EMULATOR_NAMES:
                full_path = os.path.join(base_path, name)
                if os.path.isfile(full_path):
                    self._emulator_path = full_path
                    return full_path

        raise EmulatorError(
            "Emulator not found",
            hint="Set ANDROID_HOME environment variable or specify emulator_path.",
        )

    @property
    def adb_path(self) -> str:
        """Get the path to the adb executable."""
        if self._adb_path:
            return self._adb_path

        search_paths = []

        if self.android_home:
            search_paths.append(os.path.join(self.android_home, "platform-tools"))

        # Also search PATH
        for name in self.DEFAULT_ADB_NAMES:
            path = shutil.which(name)
            if path:
                self._adb_path = path
                return path

        for base_path in search_paths:
            for name in self.DEFAULT_ADB_NAMES:
                full_path = os.path.join(base_path, name)
                if os.path.isfile(full_path):
                    self._adb_path = full_path
                    return full_path

        raise EmulatorError(
            "ADB not found", hint="Set ANDROID_HOME environment variable or specify adb_path."
        )

    def list_avds(self) -> List[AVDInfo]:
        """
        List available AVDs (Android Virtual Devices).

        Returns:
            List of AVDInfo objects for available AVDs.

        Raises:
            EmulatorError: If AVD list cannot be retrieved.
        """
        try:
            result = subprocess.run(
                [self.emulator_path, "-list-avds"], capture_output=True, text=True, timeout=30
            )

            avds = []
            for line in result.stdout.strip().split("\n"):
                name = line.strip()
                if name:
                    avd_info = self._get_avd_info(name)
                    avds.append(avd_info)

            return avds

        except subprocess.TimeoutExpired:
            raise EmulatorError("Timeout listing AVDs")
        except Exception as e:
            raise EmulatorError(f"Failed to list AVDs: {e}")

    def _get_avd_info(self, avd_name: str) -> AVDInfo:
        """
        Get detailed information about an AVD.

        Args:
            avd_name: Name of the AVD.

        Returns:
            AVDInfo object with AVD details.
        """
        avd_info = AVDInfo(name=avd_name)

        # Try to find AVD directory and config
        avd_dir = self._find_avd_directory(avd_name)
        if avd_dir:
            avd_info.path = avd_dir
            config_path = os.path.join(avd_dir, "config.ini")
            if os.path.exists(config_path):
                config = self._parse_avd_config(config_path)
                avd_info.device = config.get("hw.device.name")
                avd_info.target = config.get("tag.id")
                avd_info.abi = config.get("abi.type")
                avd_info.skin = config.get("skin.name")

        return avd_info

    def _find_avd_directory(self, avd_name: str) -> Optional[str]:
        """Find the directory for an AVD."""
        avd_home = os.environ.get("ANDROID_AVD_HOME")
        if not avd_home:
            home = os.path.expanduser("~")
            avd_home = os.path.join(home, ".android", "avd")

        avd_dir = os.path.join(avd_home, f"{avd_name}.avd")
        if os.path.isdir(avd_dir):
            return avd_dir
        return None

    def _parse_avd_config(self, config_path: str) -> Dict[str, str]:
        """Parse AVD config.ini file."""
        config = {}
        try:
            with open(config_path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except Exception:
            pass
        return config

    def start(
        self,
        avd_name: str,
        config: Optional[EmulatorConfig] = None,
        wait_boot: bool = True,
        timeout: int = 300,
    ) -> EmulatorInstance:
        """
        Start an emulator.

        Args:
            avd_name: Name of the AVD to start.
            config: Emulator configuration (uses defaults if not provided).
            wait_boot: Whether to wait for boot completion.
            timeout: Boot timeout in seconds.

        Returns:
            EmulatorInstance representing the running emulator.

        Raises:
            AVDNotFoundError: If the AVD doesn't exist.
            EmulatorStartError: If the emulator fails to start.
            EmulatorBootTimeoutError: If boot doesn't complete within timeout.
        """
        # Verify AVD exists
        available = [avd.name for avd in self.list_avds()]
        if avd_name not in available:
            raise AVDNotFoundError(avd_name, available)

        config = config or EmulatorConfig()

        # Build emulator command
        cmd = [self.emulator_path, "-avd", avd_name]

        if config.headless or config.no_window:
            cmd.append("-no-window")
        if config.gpu:
            cmd.extend(["-gpu", config.gpu])
        if config.memory_mb:
            cmd.extend(["-memory", str(config.memory_mb)])
        if config.cores:
            cmd.extend(["-cores", str(config.cores)])
        if config.no_audio:
            cmd.append("-no-audio")
        if config.no_boot_anim:
            cmd.append("-no-boot-anim")
        if config.wipe_data:
            cmd.append("-wipe-data")
        if config.read_only:
            cmd.append("-read-only")
        if config.port:
            cmd.extend(["-port", str(config.port)])

        cmd.extend(config.extra_args)

        # Start emulator process
        try:
            # Determine the port that will be used
            port = config.port or self._find_available_port()
            serial = f"emulator-{port}"

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
            )

            instance = EmulatorInstance(
                serial=serial,
                avd_name=avd_name,
                pid=process.pid,
                port=port,
                state=EmulatorState.STARTING,
                process=process,
            )

            self._running_instances[serial] = instance

            # Wait for emulator to appear in adb devices
            start_time = time.time()
            while time.time() - start_time < 60:  # 60 second startup timeout
                if process.poll() is not None:
                    # Process exited
                    _, stderr = process.communicate()
                    raise EmulatorStartError(
                        avd_name,
                        f"Process exited: {stderr.decode()[:200] if stderr else 'unknown error'}",
                    )

                running = self.get_running_emulators()
                for emu in running:
                    if emu.avd_name == avd_name or emu.serial == serial:
                        instance.serial = emu.serial
                        instance.state = EmulatorState.BOOTING
                        break

                if instance.state == EmulatorState.BOOTING:
                    break

                time.sleep(2)

            if instance.state != EmulatorState.BOOTING:
                raise EmulatorStartError(avd_name, "Emulator did not appear in device list")

            # Wait for boot if requested
            if wait_boot:
                if not self.wait_for_boot(instance.serial, timeout):
                    raise EmulatorBootTimeoutError(avd_name, timeout, instance.serial)
                instance.boot_completed = True
                instance.state = EmulatorState.RUNNING

            return instance

        except (AVDNotFoundError, EmulatorStartError, EmulatorBootTimeoutError):
            raise
        except Exception as e:
            raise EmulatorStartError(avd_name, str(e))

    def _find_available_port(self) -> int:
        """Find an available port for the emulator."""
        used_ports = set()
        for emu in self.get_running_emulators():
            if emu.port:
                used_ports.add(emu.port)

        # Emulator ports start at 5554 and use consecutive even numbers
        port = 5554
        while port in used_ports:
            port += 2
        return port

    def stop(self, instance_or_serial: str, force: bool = False) -> bool:
        """
        Stop an emulator.

        Args:
            instance_or_serial: EmulatorInstance or serial number (e.g., "emulator-5554").
            force: Force kill the emulator process.

        Returns:
            True if emulator was stopped successfully.

        Raises:
            EmulatorNotRunningError: If the emulator is not running.
        """
        if isinstance(instance_or_serial, EmulatorInstance):
            serial = instance_or_serial.serial
        else:
            serial = instance_or_serial

        # Check if emulator is running
        running = self.get_running_emulators()
        target = None
        for emu in running:
            if emu.serial == serial:
                target = emu
                break

        if not target:
            raise EmulatorNotRunningError(serial)

        try:
            if force:
                # Force kill using adb
                subprocess.run(
                    [self.adb_path, "-s", serial, "emu", "kill"], capture_output=True, timeout=10
                )
            else:
                # Graceful shutdown
                subprocess.run(
                    [self.adb_path, "-s", serial, "shell", "reboot", "-p"],
                    capture_output=True,
                    timeout=30,
                )

            # Wait for emulator to disappear
            start_time = time.time()
            while time.time() - start_time < 30:
                running = self.get_running_emulators()
                if not any(e.serial == serial for e in running):
                    if serial in self._running_instances:
                        del self._running_instances[serial]
                    return True
                time.sleep(1)

            # If still running after timeout, force kill
            if not force:
                return self.stop(serial, force=True)

            return False

        except Exception as e:
            raise EmulatorError(f"Failed to stop emulator {serial}: {e}")

    def stop_all(self) -> int:
        """
        Stop all running emulators.

        Returns:
            Number of emulators that were stopped.
        """
        running = self.get_running_emulators()
        stopped = 0

        for emu in running:
            try:
                if self.stop(emu.serial, force=True):
                    stopped += 1
            except Exception:
                pass

        return stopped

    def wait_for_boot(self, serial: str, timeout: int = 300) -> bool:
        """
        Wait for an emulator to complete booting.

        Args:
            serial: Emulator serial number.
            timeout: Maximum time to wait in seconds.

        Returns:
            True if boot completed, False if timeout occurred.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check boot_completed property
                result = subprocess.run(
                    [self.adb_path, "-s", serial, "shell", "getprop", "sys.boot_completed"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.stdout.strip() == "1":
                    # Also check that the package manager is ready
                    pm_result = subprocess.run(
                        [self.adb_path, "-s", serial, "shell", "pm", "path", "android"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if pm_result.returncode == 0:
                        return True

            except Exception:
                pass

            time.sleep(2)

        return False

    def get_running_emulators(self) -> List[EmulatorInstance]:
        """
        Get list of currently running emulators.

        Returns:
            List of EmulatorInstance objects for running emulators.
        """
        emulators = []

        try:
            result = subprocess.run(
                [self.adb_path, "devices"], capture_output=True, text=True, timeout=10
            )

            for line in result.stdout.strip().split("\n")[1:]:  # Skip header
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1]

                    # Only include emulators (serial starts with "emulator-")
                    if serial.startswith("emulator-") and status == "device":
                        port = int(serial.split("-")[1]) if "-" in serial else None
                        avd_name = self._get_emulator_avd_name(serial)

                        instance = EmulatorInstance(
                            serial=serial,
                            avd_name=avd_name,
                            port=port,
                            state=EmulatorState.RUNNING,
                            boot_completed=True,
                        )

                        # Update from our tracked instances if available
                        if serial in self._running_instances:
                            tracked = self._running_instances[serial]
                            instance.pid = tracked.pid
                            instance.process = tracked.process

                        emulators.append(instance)

        except Exception:
            pass

        return emulators

    def _get_emulator_avd_name(self, serial: str) -> Optional[str]:
        """Get the AVD name for a running emulator."""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "emu", "avd", "name"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Output is like "AVD_NAME\r\nOK"
                lines = result.stdout.strip().split("\n")
                if lines:
                    return lines[0].strip()
        except Exception:
            pass
        return None

    def is_running(self, avd_name: Optional[str] = None, serial: Optional[str] = None) -> bool:
        """
        Check if an emulator is running.

        Args:
            avd_name: AVD name to check.
            serial: Serial number to check.

        Returns:
            True if the emulator is running.
        """
        running = self.get_running_emulators()

        for emu in running:
            if avd_name and emu.avd_name == avd_name:
                return True
            if serial and emu.serial == serial:
                return True

        return False

    def get_status(self, serial: str) -> Dict[str, Any]:
        """
        Get detailed status of an emulator.

        Args:
            serial: Emulator serial number.

        Returns:
            Dictionary with emulator status information.
        """
        running = self.get_running_emulators()
        for emu in running:
            if emu.serial == serial:
                status = emu.to_dict()

                # Get additional properties
                try:
                    props = ["ro.product.model", "ro.build.version.release", "ro.build.version.sdk"]
                    for prop in props:
                        result = subprocess.run(
                            [self.adb_path, "-s", serial, "shell", "getprop", prop],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if result.returncode == 0:
                            status[prop.split(".")[-1]] = result.stdout.strip()
                except Exception:
                    pass

                return status

        raise EmulatorNotRunningError(serial)
