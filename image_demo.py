"""Run ALDS detection and depth estimation on a single image."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from src.depth_estimation.depth_estimator import DepthEstimator
from src.detection.detector import ObjectDetector
from src.utils.config_loader import load_config


def run_image_demo(image_path: str, config_path: str = "configs/config.yaml", display: bool = True):
    """Run detection and depth estimation on a single image."""
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"Error: image not found at {image_file}")
        return 1

    config = load_config(config_path)
    frame = cv2.imread(str(image_file))
    if frame is None:
        print(f"Error: could not load image at {image_file}")
        return 1

    detector = ObjectDetector(
        config["detection"]["model"],
        config["detection"]["confidence_threshold"],
        config["detection"].get("classes"),
    )
    depth_estimator = DepthEstimator(
        model_type=config["depth"]["encoder"],
        device=config["depth"]["device"],
    )

    detections = detector.detect(frame)
    depth = depth_estimator.estimate_depth(frame)

    output_frame = detector.draw_detections(frame, detections)
    depth_vis = depth_estimator.visualize_depth(depth)

    cv2.putText(output_frame, f"Humans: {len(detections.get('humans', []))}",
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(output_frame, f"Zombies: {len(detections.get('zombies', []))}",
               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    cv2.imwrite(str(output_dir / "detection.jpg"), output_frame)
    cv2.imwrite(str(output_dir / "depth.jpg"), depth_vis)

    print(f"Humans detected: {len(detections.get('humans', []))}")
    print(f"Zombies detected: {len(detections.get('zombies', []))}")
    print(f"Depth available: {depth_estimator.is_ready}")
    print(f"Detection available: {detector.is_ready}")
    print(f"Results saved to {output_dir}/")

    if display:
        cv2.imshow("Detection", output_frame)
        cv2.imshow("Depth Map", depth_vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return 0


def main():
    parser = argparse.ArgumentParser(description="Run ALDS on a single image")
    parser.add_argument("image", type=str, help="Path to the input image")
    parser.add_argument("--config", type=str, default="configs/config.yaml", help="Path to configuration file")
    parser.add_argument("--no-display", action="store_true", help="Skip OpenCV windows and just save outputs")
    args = parser.parse_args()

    raise SystemExit(run_image_demo(args.image, args.config, display=not args.no_display))


if __name__ == "__main__":
    main()
