"""Serial laser controller module."""

from __future__ import annotations

import numpy as np
import serial


class LaserController:
    """Controls the laser pointer hardware over a serial link."""

    def __init__(self, port: str = "/dev/ttyUSB0", baud_rate: int = 9600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.is_connected = False

    def connect(self) -> bool:
        """Connect to the laser controller hardware."""
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.is_connected = True
            return True
        except Exception as exc:
            print(f"Failed to connect to laser controller: {exc}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from the laser controller hardware."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False

    def _write_command(self, command: str):
        """Send a newline-terminated command to the controller."""
        if not self.is_connected:
            return

        try:
            self.serial_conn.write(f"{command}\n".encode("utf-8"))
        except Exception as exc:
            print(f"Error sending serial command '{command}': {exc}")

    def move_laser(self, pan: float, tilt: float):
        """Move the laser to a pan/tilt position in degrees."""
        pan = float(np.clip(pan, 0, 180))
        tilt = float(np.clip(tilt, 0, 180))
        self._write_command(f"PAN:{pan:.2f},TILT:{tilt:.2f}")

    def target_bbox(self, bbox: np.ndarray, frame_shape: Tuple[int, ...]):
        """
        Target the laser at the center of a bounding box.

        Args:
            bbox: Bounding box in ``[x1, y1, x2, y2]`` format.
            frame_shape: Frame dimensions from OpenCV, e.g. ``(h, w, c)``.
        """
        h, w = frame_shape[:2]
        cx = float((bbox[0] + bbox[2]) / 2)
        cy = float((bbox[1] + bbox[3]) / 2)

        pan = 90 + ((cx - (w / 2)) / (w / 2)) * 90
        tilt = 90 + ((cy - (h / 2)) / (h / 2)) * 90
        self.move_laser(pan, tilt)

    def fire(self):
        """Turn the laser/fire output on."""
        self._write_command("FIRE:ON")

    def cease_fire(self):
        """Turn the laser/fire output off."""
        self._write_command("FIRE:OFF")
