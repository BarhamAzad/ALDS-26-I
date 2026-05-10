"""Main entry point for ALDS"""

import argparse
import cv2
import numpy as np
from pathlib import Path

from src.utils.config_loader import load_config
from src.utils.video_handler import VideoHandler, VideoWriter
from src.detection.detector import ObjectDetector
from src.depth_estimation.depth_estimator import DepthEstimator
from src.laser_control.laser_controller import LaserController


class ALDS:
    """Main system for zombie detection and laser targeting"""
    
    def __init__(self, config_path: str):
        """
        Initialize the system
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        
        # Initialize modules
        self.detector = ObjectDetector(
            self.config["detection"]["model"],
            self.config["detection"]["confidence_threshold"],
            self.config["detection"].get("classes"),
        )
        
        self.depth_estimator = DepthEstimator(
            model_type=self.config["depth"]["encoder"],
            device=self.config["depth"]["device"]
        )
        
        self.laser_controller = LaserController(
            port=self.config["laser"]["port"],
            baud_rate=self.config["laser"]["baud_rate"]
        )
        self.target_class = str(self.config["laser"].get("target_class", "zombie")).lower()
        
        self.video_handler = VideoHandler(
            source=self.config["video"]["source"],
            fps=self.config["video"]["fps"],
            width=self.config["video"]["width"],
            height=self.config["video"]["height"]
        )
        
        self.video_writer = None
        if self.config["output"]["save_video"]:
            output_path = Path(self.config["output"]["results_dir"]) / "output.mp4"
            self.video_writer = VideoWriter(
                str(output_path),
                fps=self.config["video"]["fps"],
                width=self.config["video"]["width"],
                height=self.config["video"]["height"]
            )
    
    @staticmethod
    def _label_key(label: str) -> str:
        if label == "human":
            return "humans"
        if label.endswith("y"):
            return f"{label[:-1]}ies"
        return f"{label}s"

    def find_closest_target(self, detections: dict, depths: np.ndarray) -> dict | None:
        """
        Find the closest configured target that should be tracked.
        
        Args:
            detections: Detection results
            depths: Depth map
            
        Returns:
            Closest target info or None
        """
        if not self.depth_estimator.is_ready:
            return None

        target_key = self._label_key(self.target_class)
        targets = detections.get(target_key, [])
        if not targets:
            return None

        min_distance = float("inf")
        closest_target = None

        for target in targets:
            bbox = target["bbox"].astype(int)
            cx = (bbox[0] + bbox[2]) // 2
            cy = (bbox[1] + bbox[3]) // 2

            depth = self.depth_estimator.get_depth_at_point(depths, cx, cy)
            if self.config["laser"]["min_distance"] <= depth <= self.config["laser"]["max_distance"]:
                if depth < min_distance:
                    min_distance = depth
                    closest_target = {
                        "bbox": bbox,
                        "depth": depth,
                        "confidence": target["confidence"],
                        "label": target["label"],
                    }

        return closest_target
    
    def run(self):
        """Run the main detection loop"""
        if not self.video_handler.open():
            print("Failed to open video source")
            return
        
        if self.config["laser"]["enabled"]:
            if not self.laser_controller.connect():
                print("Warning: Could not connect to laser controller")
        
        if self.config["output"]["save_video"] and self.video_writer:
            if not self.video_writer.open():
                print("Warning: Could not open video writer")
                self.video_writer = None
        
        try:
            while True:
                ret, frame = self.video_handler.read_frame()
                if not ret:
                    break
                
                # Flip frame if configured
                if self.config["video"]["flip_horizontal"]:
                    frame = cv2.flip(frame, 1)
                
                # Detect objects
                detections = self.detector.detect(frame)
                
                # Estimate depth
                depth = self.depth_estimator.estimate_depth(frame)
                
                # Display frame
                output_frame = frame.copy()
                
                if self.config["output"]["draw_bbox"]:
                    output_frame = self.detector.draw_detections(output_frame, detections)
                
                if self.config["output"]["draw_depth"]:
                    depth_vis = self.depth_estimator.visualize_depth(depth)
                    # Blend depth visualization
                    output_frame = cv2.addWeighted(output_frame, 0.7, depth_vis, 0.3, 0)
                
                # Find and target closest zombie
                closest_target = self.find_closest_target(detections, depth)

                if closest_target and self.config["laser"]["enabled"]:
                    bbox = closest_target["bbox"]
                    self.laser_controller.target_bbox(bbox, frame.shape)
                    self.laser_controller.fire()

                    # Draw targeting reticle
                    cx = (bbox[0] + bbox[2]) // 2
                    cy = (bbox[1] + bbox[3]) // 2
                    cv2.circle(output_frame, (cx, cy), 30, (0, 0, 255), 2)
                    cv2.putText(
                        output_frame,
                        f"TARGET {closest_target['label'].upper()}: {closest_target['depth']:.2f}",
                        (bbox[0], bbox[1] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )
                else:
                    if self.config["laser"]["enabled"]:
                        self.laser_controller.cease_fire()

                # Add UI information
                human_count = len(detections.get("humans", []))
                target_count = len(detections.get(self._label_key(self.target_class), []))
                cv2.putText(output_frame, f"Humans: {human_count}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(output_frame, f"{self.target_class.title()}s: {target_count}",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if not self.detector.is_ready:
                    cv2.putText(output_frame, "Detector unavailable", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)
                if not self.depth_estimator.is_ready:
                    cv2.putText(output_frame, "Depth unavailable", (10, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)
                if self.config["laser"]["enabled"] and not self.laser_controller.is_connected:
                    cv2.putText(output_frame, "Laser controller offline", (10, 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)

                # Display
                cv2.imshow("ALDS", output_frame)
                
                # Save video
                if self.video_writer:
                    self.video_writer.write_frame(output_frame)
                
                # Exit on 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.video_handler.release()
        if self.video_writer:
            self.video_writer.release()
        if self.config["laser"]["enabled"]:
            self.laser_controller.cease_fire()
            self.laser_controller.disconnect()
        cv2.destroyAllWindows()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="ALDS")
    parser.add_argument("--config", type=str, default="configs/config.yaml",
                       help="Path to configuration file")
    args = parser.parse_args()
    
    system = ALDS(args.config)
    system.run()


if __name__ == "__main__":
    main()
