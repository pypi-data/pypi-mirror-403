"""
Transmission Port Listener for processing incoming data streams.

This module wraps the C++ TransmissionPortListener which handles all protocol layers
(PacketSerial/COBS, LumynTP, Transmission parsing, Event/Response parsing).
"""

import threading
import struct
from typing import Optional, Callable, List, Any
from queue import Queue
import warnings


class TransmissionPortListener:
    """
    Wraps the C++ TransmissionPortListener which handles all protocol layers.

    The C++ layer does all the heavy lifting:
    - COBS encoding/decoding
    - PacketSerial framing
    - LumynTP transmission protocol
    - Request/Response matching
    - Event parsing from transmissions

    This Python wrapper just provides the callbacks and queues events for polling.
    """

    def __init__(self):
        """Initialize the transmission listener."""
        self._running = False
        self._write_callback: Optional[Callable[[bytes], None]] = None
        self._event_queue: Queue = Queue()
        self._cpp_listener: Optional[Any] = None
        self._handler_wrapper: Optional[Any] = None

    def init(self) -> None:
        """Initialize the C++ protocol stack."""
        try:
            # Import C++ bindings
            import lumyn_sdk._bindings.transmission as trans_mod
            import lumyn_sdk._bindings.command as command_mod

            # Store CommandHeader size for command parsing
            self._command_header_size = struct.calcsize(
                'BB')  # type + union field

            # Create a handler wrapper that inherits from ILumynTransmissionHandler
            # The C++ TransmissionPortListener calls these methods when it receives data
            class HandlerWrapper(trans_mod.ILumynTransmissionHandler):
                def __init__(self, parent):
                    super().__init__()
                    self.parent = parent

                def HandleTransmission(self, transmission):
                    # C++ already parsed the transmission, we don't need to do anything
                    # (Events are handled via HandleEvent callback)
                    pass

                def HandleEvent(self, event):
                    # C++ already parsed the Event from the transmission payload
                    # Just queue it for the application to poll
                    self.parent._event_queue.put(event)

            # Create the wrapper and C++ TransmissionPortListener
            self._handler_wrapper = HandlerWrapper(self)
            self._cpp_listener = trans_mod.TransmissionPortListener(
                self._handler_wrapper)

            # Wire up write callback if already set
            if self._write_callback:
                self._cpp_listener.setWriteCallback(self._write_callback)

            # Initialize the C++ listener (creates COBSEncoder, PacketSerial, LumynTP internally)
            self._cpp_listener.Init()

            self._running = True

        except Exception as e:
            warnings.warn(f"Failed to initialize C++ protocol layers: {e}")
            import traceback
            traceback.print_exc()
            raise

    def set_write_callback(self, callback: Optional[Callable[[bytes], None]]) -> None:
        """
        Set the callback for writing bytes to serial port.

        Args:
            callback: Function that takes bytes to write
        """
        self._write_callback = callback

        # Also set on C++ listener if already initialized
        if self._cpp_listener:
            self._cpp_listener.setWriteCallback(callback)

    def ingress_bytes(self, data: bytes) -> None:
        """
        Process incoming bytes from serial port.

        This is called by the serial I/O read thread.

        Args:
            data: Raw bytes received from serial
        """
        if not self._running or not data:
            return

        # Feed bytes to C++ TransmissionPortListener
        # It handles: COBS decode -> PacketSerial -> LumynTP -> HandleTransmission callback
        if self._cpp_listener:
            try:
                self._cpp_listener.ingressBytes(data)
            except Exception as e:
                warnings.warn(f"Error processing received data: {e}")

    def send_command(self, command_bytes: bytes) -> None:
        """
        Send a command to the device.

        Args:
            command_bytes: Serialized command bytes from CommandBuilder (header + payload)
        """
        if not self._cpp_listener:
            warnings.warn(
                "TransmissionPortListener not initialized - cannot send command")
            return

        try:
            # CommandBuilder returns [CommandHeader][Payload] concatenated
            # C++ SendCommand expects them separated
            # CommandHeader is 2 bytes: type (1 byte) + union field (1 byte)
            if len(command_bytes) < self._command_header_size:
                warnings.warn(f"Command too small: {len(command_bytes)} bytes")
                return

            # Import CommandHeader to parse the header bytes
            import lumyn_sdk._bindings.command as command_mod

            # Parse header from first 2 bytes
            # We need to reconstruct a CommandHeader object
            header = command_mod.CommandHeader()
            header_bytes = command_bytes[:self._command_header_size]
            # CommandHeader: type (CommandType enum), then union of ledType/systemType/deviceType
            header.type = command_mod.CommandType(header_bytes[0])

            # Set the appropriate union field based on command type
            if header.type == command_mod.CommandType.LED:
                header.ledType = command_mod.LEDCommandType(header_bytes[1])
            elif header.type == command_mod.CommandType.System:
                header.systemType = command_mod.SystemCommandType(
                    header_bytes[1])
            elif header.type == command_mod.CommandType.Device:
                header.deviceType = command_mod.DeviceCommandType(
                    header_bytes[1])

            # Extract payload (everything after header)
            payload = command_bytes[self._command_header_size:]

            # Call C++ SendCommand with separated header and payload
            self._cpp_listener.SendCommand(header, payload)

        except Exception as e:
            warnings.warn(f"Failed to send command: {e}")
            import traceback
            traceback.print_exc()

    def send_request(self, request: Any, timeout_ms: int = 10000) -> Optional[Any]:
        """
        Send a request and wait for response.

        C++ TransmissionPortListener handles:
        - Assigning request ID
        - Serializing the request
        - Sending via LumynTP
        - Waiting for matching response
        - Parsing response from transmission

        Args:
            request: Request object (C++ Request)
            timeout_ms: Timeout in milliseconds

        Returns:
            Response object or None if timeout
        """
        if not self._cpp_listener:
            warnings.warn(
                "TransmissionPortListener not initialized - cannot send request")
            return None

        try:
            # C++ does all the work: serialize, send, wait, match, parse
            response = self._cpp_listener.SendRequest(request, timeout_ms)
            return response
        except Exception as e:
            warnings.warn(f"Failed to send request: {e}")
            return None

    def try_pop_event(self) -> Optional[Any]:
        """
        Try to pop an event from the queue (populated by C++ HandleEvent callback).

        Returns:
            Event object or None
        """
        if self._event_queue.empty():
            return None
        return self._event_queue.get_nowait()

    def get_all_events(self) -> List[Any]:
        """
        Get all pending events from the queue.

        Returns:
            List of Event objects
        """
        events = []
        while not self._event_queue.empty():
            try:
                events.append(self._event_queue.get_nowait())
            except:
                break
        return events

    def close(self) -> None:
        """Stop the listener and clean up."""
        self._running = False
        self._write_callback = None
