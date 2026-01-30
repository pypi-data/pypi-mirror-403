"""
Serial I/O abstraction for ConnectorX communication.

This module provides the ISerialIO interface and platform-specific implementations
that mirror the wpilib vendordep architecture.
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable
import serial
import serial.tools.list_ports


class ISerialIO(ABC):
    """Abstract interface for serial communication."""

    @abstractmethod
    def write_bytes(self, data: bytes) -> None:
        """Write bytes to the serial port."""
        pass

    @abstractmethod
    def set_read_callback(self, callback: Optional[Callable[[bytes], None]]) -> None:
        """Set callback to be called when data is received."""
        pass

    @abstractmethod
    def is_open(self) -> bool:
        """Check if the serial port is open."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the serial port and stop read thread."""
        pass


class PySerialIO(ISerialIO):
    """PySerial implementation of ISerialIO with dedicated read thread."""

    def __init__(self, port: str, baudrate: int = 115200):
        """
        Initialize serial I/O.

        Args:
            port: Serial port identifier (e.g., "COM3", "/dev/ttyUSB0")
            baudrate: Baud rate (default 115200)
        """
        self._port = port
        self._baudrate = baudrate
        self._serial: Optional[serial.Serial] = None
        self._read_callback: Optional[Callable[[bytes], None]] = None
        self._read_thread: Optional[threading.Thread] = None
        self._running = False

    def open(self) -> bool:
        """
        Open the serial port and start the read thread.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=0.01,  # 10ms timeout for reads
                write_timeout=1.0
            )

            # Start dedicated read thread
            self._running = True
            self._read_thread = threading.Thread(
                target=self._read_loop, daemon=True)
            self._read_thread.start()

            return True

        except (serial.SerialException, OSError) as e:
            print(f"Failed to open {self._port}: {e}")
            return False

    def close(self) -> None:
        """Close the serial port and stop the read thread."""
        # Stop read thread first
        self._running = False
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=1.0)

        # Close serial port
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass

        self._serial = None
        self._read_thread = None

    def is_open(self) -> bool:
        """Check if the serial port is open."""
        return self._serial is not None and self._serial.is_open

    def write_bytes(self, data: bytes) -> None:
        """Write bytes to the serial port."""
        if not self.is_open():
            return

        try:
            self._serial.write(data)
            self._serial.flush()
        except serial.SerialException as e:
            print(f"Serial write error: {e}")

    def set_read_callback(self, callback: Optional[Callable[[bytes], None]]) -> None:
        """Set the callback to be invoked when data is received."""
        self._read_callback = callback

    def _read_loop(self) -> None:
        """Background thread that continuously reads from serial port."""
        buffer_size = 256

        while self._running:
            if not self.is_open():
                break

            try:
                # Non-blocking read with timeout
                data = self._serial.read(buffer_size)

                if data and self._read_callback:
                    self._read_callback(data)

                # Small sleep to prevent CPU spinning
                time.sleep(0.002)  # 2ms, matching C++ implementation

            except serial.SerialException as e:
                print(f"Serial read error: {e}")
                break
            except Exception as e:
                print(f"Unexpected error in read loop: {e}")
                break


def list_available_ports():
    """
    List all available serial ports.

    Returns:
        List of port names
    """
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]
