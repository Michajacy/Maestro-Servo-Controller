import logging

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

class MaestroInterface:
    """Interface for the controller"""
    def set_target(self, channel: int, target_us: int) -> None:
        raise NotImplementedError("set_target ust be implemented")

    def close(self) -> None:
        pass



class SerialMaestroController(MaestroInterface):
    """Communication with controller via serial port"""
    def __init__(self, port: str = "COM3", baudrate: int = 9600) -> None:
        if not SERIAL_AVAILABLE:
            raise ImportError("pyserial not installed")

        try:
            self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            logging.info(f"Connected with Maestro on port {port}")
        except:
            logging.error(f"Connection with Maestro on port {port} failed: {e}")
            self.serial_conn = None


    def set_target(self, channel: int, target_us: int) -> None:
        if not self.serial_conn or not self.serial_conn.is_open:
            return

        target_qs = int(target_us * 4) #magic number

        low_bits = target_qs & 0x7F #magic number
        high_bits = (target_qs >> 7) & 0x7F

        command = bytes ([0x84, channel, low_bits, high_bits])
        self.serial_conn.write(command)

    def close(self) -> None:
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()


class MockMaestroController(MaestroInterface): 
    """Prints in CLI sent bytes"""
    def __init__(self) -> None:
        logging.info("Virtual Controller (MOCK) Initialised")

    def set_target(self, channel: int, target_us: int) -> None:
        target_qs = int(target_us * 4)
        low_bits = target_qs & 0x7F
        high_bits = (target_qs >> 7) & 0x7F

        hex_cmd = f"0x84 0x{channel:02X} 0x{low_bits:02X} 0x{high_bits:02X}"

        logging.info(f"[Device] Channel {channel} -> {target_us} us | Bytes: {hex_cmd}")
    