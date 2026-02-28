"""YOLOv8 Object Detection Module"""

import cv2
import numpy as np
from ultralytics import YOLO


class ObjectDetector:
    """YOLOv8 based object detector for humans and zombies"""
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        """
        Initialize the object detector
        
        Args:
            model_path: Path to YOLOv8 model
            confidence_threshold: Minimum confidence for detection
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.class_names = {0: "human", 1: "zombie"}
    
    def detect(self, frame: np.ndarray) -> dict:
        """
        Detect objects in frame
        
        Args:
            frame: Input image frame
            
        Returns:
            Dictionary containing detections
        """
        results = self.model(frame, conf=self.confidence_threshold)
        
        detections = {
            "humans": [],
            "zombies": [],
            "frame": frame
        }
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                coords = box.xyxy[0].cpu().numpy()
                
                detection = {
                    "bbox": coords,
                    "confidence": conf,
                    "class": cls
                }
                
                if cls == 0:
                    detections["humans"].append(detection)
                elif cls == 1:
                    detections["zombies"].append(detection)
        
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: dict) -> np.ndarray:
        """
        Draw bounding boxes on frame
        
        Args:
            frame: Input frame
            detections: Detection results
            
        Returns:
            Annotated frame
        """
        frame = frame.copy()
        
        # Draw humans in green
        for human in detections["humans"]:
            bbox = human["bbox"].astype(int)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            cv2.putText(frame, f"Human: {human['confidence']:.2f}", 
                       (bbox[0], bbox[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Draw zombies in red
        for zombie in detections["zombies"]:
            bbox = zombie["bbox"].astype(int)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2)
            cv2.putText(frame, f"Zombie: {zombie['confidence']:.2f}", 
                       (bbox[0], bbox[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame
