"""
Rigctl client for controlling SDR++ via Hamlib rigctl protocol.
"""

import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RigctlClient:
    """Client for communicating with rigctl server (Hamlib protocol)."""

    def __init__(self, host: str = "localhost", port: int = 4532):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Connect to rigctl server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            logger.info(f"Connected to rigctl at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to rigctl: {e}")
            self.socket = None
            return False

    def disconnect(self):
        """Disconnect from rigctl server."""
        if self.socket:
            try:
                self._send_command("q")
            except:
                pass
            self.socket.close()
            self.socket = None
            logger.info("Disconnected from rigctl")

    def _send_command(self, command: str, num_lines: int = 1) -> str:
        """Send a command and return the response."""
        if not self.socket:
            raise RuntimeError("Not connected to rigctl server")

        # Add newline if not present
        if not command.endswith('\n'):
            command += '\n'

        self.socket.sendall(command.encode('ascii'))

        # Read response
        response = b''
        while True:
            chunk = self.socket.recv(1024)
            if not chunk:
                break
            response += chunk
            # Check if we have enough lines
            if response.count(b'\n') >= num_lines:
                break

        result = response.decode('ascii').strip()
        logger.debug(f"Command: {command.strip()} -> Response: {result}")
        return result

    def set_frequency(self, frequency_hz: int) -> bool:
        """Set the frequency in Hz."""
        try:
            response = self._send_command(f"F {frequency_hz}")
            success = response.startswith("RPRT 0")
            if success:
                logger.info(f"Set frequency to {frequency_hz} Hz")
            else:
                logger.error(f"Failed to set frequency: {response}")
            return success
        except Exception as e:
            logger.error(f"Error setting frequency: {e}")
            return False

    def get_frequency(self) -> Optional[int]:
        """Get the current frequency in Hz."""
        try:
            response = self._send_command("f")
            frequency = int(response)
            logger.debug(f"Current frequency: {frequency} Hz")
            return frequency
        except Exception as e:
            logger.error(f"Error getting frequency: {e}")
            return None

    def set_mode(self, mode: str, bandwidth: int = 0) -> bool:
        """
        Set the demodulation mode.

        Args:
            mode: Mode string (FM, WFM, AM, USB, LSB, CW, DSB, RAW)
            bandwidth: Bandwidth in Hz (0 for default)
        """
        try:
            response = self._send_command(f"M {mode} {bandwidth}")
            success = response.startswith("RPRT 0")
            if success:
                logger.info(f"Set mode to {mode} with bandwidth {bandwidth} Hz")
            else:
                logger.error(f"Failed to set mode: {response}")
            return success
        except Exception as e:
            logger.error(f"Error setting mode: {e}")
            return False

    def get_mode(self) -> Optional[tuple[str, int]]:
        """Get the current mode and bandwidth."""
        try:
            response = self._send_command("m")
            parts = response.split()
            if len(parts) >= 1:
                mode = parts[0]
                bandwidth = int(parts[1]) if len(parts) >= 2 else 0
                logger.debug(f"Current mode: {mode}, bandwidth: {bandwidth} Hz")
                return (mode, bandwidth)
            return None
        except Exception as e:
            logger.error(f"Error getting mode: {e}")
            return None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def start_recording(self) -> bool:
        """Start recording in SDR++."""
        try:
            response = self._send_command("AOS")
            success = response.startswith("RPRT 0")
            if success:
                logger.info("Started recording")
            else:
                logger.error(f"Failed to start recording: {response}")
            return success
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False

    def stop_recording(self) -> bool:
        """Stop recording in SDR++."""
        try:
            response = self._send_command("LOS")
            success = response.startswith("RPRT 0")
            if success:
                logger.info("Stopped recording")
            else:
                logger.error(f"Failed to stop recording: {response}")
            return success
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
