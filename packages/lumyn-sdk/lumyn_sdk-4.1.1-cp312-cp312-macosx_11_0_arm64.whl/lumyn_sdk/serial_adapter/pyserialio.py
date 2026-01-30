import serial
from ..lumyn_sdk.serial import ISerialIO

class PySerialIO(ISerialIO):
    """Python implementation of ISerialIO using PySerial"""
    
    def __init__(self, port, baudrate=115200, timeout=1):
        super().__init__()
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        self._read_callback = None
        self._running = False
        self._read_thread = None
    
    def writeBytes(self, data_bytes):
        """Write bytes to the serial port"""
        print(f"[Serial OUT] {data_bytes.hex()}")
        self.ser.write(data_bytes)
    
    def setReadCallback(self, callback):
        self._read_callback = callback
        
    def start_reading(self):
        print("[Serial IN] Starting read thread...")
        import threading
        if not self._running:
            self._running = True
            self._read_thread = threading.Thread(target=self._read_loop)
            self._read_thread.start()
    
    def _read_loop(self):
        import time
        while self._running:
            # print("[Serial IN] Checking for data...")
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting)
                if data:
                    print(f"[Serial IN] {data.hex()}")
                    if self._read_callback:
                        self._read_callback(data, len(data))
            time.sleep(0.001)
    
    def stop_reading(self):
        self._running = False
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2.0)  # Increased timeout
            if self._read_thread.is_alive():
                print("Warning: Serial read thread did not stop cleanly")
    
    def close(self):
        self.stop_reading()
        if self.ser.is_open:
            self.ser.close()
