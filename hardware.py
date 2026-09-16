"""
Hardware integration module for Maestro Servo Controller.
Provides interfaces and implementations for serial communication.
"""
import logging
from typing import Any

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    serial: Any = None
    SERIAL_AVAILABLE = False


class MaestroInterface:
    """Base interface for the Maestro controller. Enforces consistent API."""

    def set_target(self, channel: int, target_us: int) -> None:
        """
        Sets the target position for a specific channel.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("set_target must be implemented")

    def close(self) -> None:
        """Closes the connection to the hardware device."""


class SerialMaestroController(MaestroInterface):
    """Real implementation communicating with hardware via a serial port."""

    def __init__(self, port: str = "COM3", baudrate: int = 9600) -> None:
        if not SERIAL_AVAILABLE:
            raise ImportError("pyserial is not installed")

        try:
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            logging.info("Connected with Maestro on port %s", port)
        except serial.SerialException as err:
            logging.error("Connection with Maestro on port %s failed: %s", port, err)
            self.serial_conn = None

    def set_target(self, channel: int, target_us: int) -> None:
        """Formats and sends the Compact Protocol command over serial."""
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        target_qs = int(target_us * 4)

        low_bits = target_qs & 0x7F
        high_bits = (target_qs >> 7) & 0x7F

        command = bytes([0x84, channel, low_bits, high_bits])
        self.serial_conn.write(command)

    def close(self) -> None:
        """Safely closes the active serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()


class MockMaestroController(MaestroInterface):
    """Mock implementation for testing. Prints bytes to the CLI."""

    def __init__(self) -> None:
        logging.info("Virtual Controller (MOCK) Initialised")

    def set_target(self, channel: int, target_us: int) -> None:
        """Simulates command formatting and logs the result."""
        target_qs = int(target_us * 4)
        low_bits = target_qs & 0x7F
        high_bits = (target_qs >> 7) & 0x7F

        hex_cmd = f"0x84 0x{channel:02X} 0x{low_bits:02X} 0x{high_bits:02X}"

        # Pylint allows f-strings if we don't care about lazy evaluation,
        # but to satisfy it fully, we use %-formatting here.
        logging.info("[Device] Channel %d -> %d us | Bytes: %s", channel, target_us, hex_cmd)
