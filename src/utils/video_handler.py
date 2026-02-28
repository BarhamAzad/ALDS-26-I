"""Video input/output handler"""

import cv2
from pathlib import Path


class VideoHandler:
    """Handles video input from camera or file"""
    
    def __init__(self, source: int | str = 0, fps: int = 30, 
                 width: int = 640, height: int = 480):
        """
        Initialize video handler
        
        Args:
            source: Camera index (0) or video file path
            fps: Frames per second
            width: Video width
            height: Video height
        """
        self.source = source
        self.fps = fps
        self.width = width
        self.height = height
        self.cap = None
        self.is_open = False
    
    def open(self) -> bool:
        """
        Open video source
        
        Returns:
            True if successfully opened
        """
        try:
            self.cap = cv2.VideoCapture(self.source)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            self.is_open = self.cap.isOpened()
            return self.is_open
        except Exception as e:
            print(f"Failed to open video source: {e}")
            return False
    
    def read_frame(self):
        """
        Read next frame
        
        Returns:
            (success, frame) tuple
        """
        if not self.is_open:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame
    
    def release(self):
        """Release video source"""
        if self.cap:
            self.cap.release()
            self.is_open = False
    
    def get_fps(self) -> float:
        """Get video FPS"""
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0.0
    
    def get_frame_count(self) -> int:
        """Get total frame count"""
        if self.cap:
            return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return 0


class VideoWriter:
    """Writes video output"""
    
    def __init__(self, output_path: str, fps: int = 30, 
                 width: int = 640, height: int = 480):
        """
        Initialize video writer
        
        Args:
            output_path: Path to save video
            fps: Frames per second
            width: Video width
            height: Video height
        """
        self.output_path = Path(output_path)
        self.fps = fps
        self.width = width
        self.height = height
        self.writer = None
        
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def open(self) -> bool:
        """
        Open video writer
        
        Returns:
            True if successfully opened
        """
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(str(self.output_path), fourcc, 
                                         self.fps, (self.width, self.height))
            return self.writer.isOpened()
        except Exception as e:
            print(f"Failed to open video writer: {e}")
            return False
    
    def write_frame(self, frame):
        """
        Write frame to video
        
        Args:
            frame: Frame to write
        """
        if self.writer:
            self.writer.write(frame)
    
    def release(self):
        """Release video writer"""
        if self.writer:
            self.writer.release()
