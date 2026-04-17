"""Laser Pointer Control Module"""

import serial
import numpy as np
from typing import Tuple, Optional


class LaserController:
    """Controls laser pointer to target zombies"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baud_rate: int = 9600):
        """
        Initialize laser controller
        
        Args:
            port: Serial port for laser control
            baud_rate: Serial communication baud rate
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """
        Connect to laser control hardware
        
        Returns:
            True if connection successful
        """
        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.is_connected = True
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to laser: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from laser control hardware"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
    
    def move_laser(self, pan: float, tilt: float):
        """
        Move laser to position
        
        Args:
            pan: Horizontal angle in degrees
            tilt: Vertical angle in degrees
        """
        if not self.is_connected:
            return
        
        # TODO: Implement actual serial commands for your laser hardware
        # This is a placeholder
        command = f"PAN:{pan:.2f},TILT:{tilt:.2f}\n"
        try:
            self.serial_conn.write(command.encode())
        except Exception as e:
            print(f"Error sending command: {e}")
    
    def target_bbox(self, bbox: np.ndarray, frame_shape: Tuple[int, int]):
        """
        Target laser at bounding box center
        
        Args:
            bbox: Bounding box [x1, y1, x2, y2]
            frame_shape: Frame dimensions (height, width)
        """
        # Calculate center of bounding box
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        
        # Normalize to frame center and map to servo range (0-180 degrees)
        h, w = frame_shape
        pan = 90 + ((cx - w/2) / (w/2)) * 90  # Convert to degrees (0 to 180)
        tilt = 90 + ((cy - h/2) / (h/2)) * 90  # Convert to degrees (0 to 180)
        
        # Clamp to valid servo range
        pan = np.clip(pan, 0, 180)
        tilt = np.clip(tilt, 0, 180)
        
        self.move_laser(pan, tilt)
    
    def on_target(self, laser_pos: Tuple[float, float], 
                 bbox: np.ndarray, tolerance: int = 10) -> bool:
        """
        Check if laser is on target
        
        Args:
            laser_pos: Current laser position (x, y)
            bbox: Target bounding box
            tolerance: Tolerance in pixels
            
        Returns:
            True if laser is within tolerance of bbox
        """
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        
        distance = np.sqrt((laser_pos[0] - cx)**2 + (laser_pos[1] - cy)**2)
        return distance <= tolerance
    
    def fire(self):
        """
        Fire laser (activate laser pointer)
        """
        if not self.is_connected:
            return
        
        try:
            self.serial_conn.write(b"FIRE\n")
        except Exception as e:
            print(f"Error firing laser: {e}")
        return distance <= tolerance
    
    def fire(self):
        """Activate laser (turn on)"""
        if not self.is_connected:
            return
        
        try:
            self.serial_conn.write(b"FIRE:ON\n")
        except Exception as e:
            print(f"Error firing laser: {e}")
    
    def cease_fire(self):
        """Deactivate laser (turn off)"""
        if not self.is_connected:
            return
        
        try:
            self.serial_conn.write(b"FIRE:OFF\n")
        except Exception as e:
            print(f"Error ceasing fire: {e}")
