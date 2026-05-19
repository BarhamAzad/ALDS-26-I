"""Main entry point for ALDS object detection, depth, and servo targeting."""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".ultralytics").resolve()))

import cv2
import numpy as np
import yaml
from ultralytics import YOLO

from depth_estimator import DepthEstimator


class ObjectDetector:
    """Small YOLO wrapper that returns normalized detection dictionaries."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        classes: list[str] | None = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.allowed_classes = {label.lower() for label in classes or []}
        self.model: YOLO | None = None
        self.names: dict[int, str] = {}
        self.is_ready = False
        self.error: str | None = None
        self.load()

    def load(self) -> bool:
        if not self.model_path.exists():
            self.error = f"YOLO model not found: {self.model_path}"
            return False

        try:
            self.model = YOLO(str(self.model_path))
            names = self.model.names or {}
            self.names = {int(key): str(value) for key, value in names.items()}
            self.is_ready = True
            self.error = None
        except Exception as exc:  # noqa: BLE001 - keep startup errors clear.
            self.is_ready = False
            self.error = str(exc)

        return self.is_ready

    @staticmethod
    def _logical_label(label: str) -> str:
        label = label.strip().lower()
        return "human" if label == "person" else label

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        if not self.is_ready or self.model is None:
            return []

        result = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False,
        )[0]

        detections: list[dict[str, Any]] = []
        for box in result.boxes:
            class_id = int(box.cls[0])
            raw_label = self.names.get(class_id, str(class_id))
            label = self._logical_label(raw_label)

            if self.allowed_classes and label not in self.allowed_classes:
                continue

            detections.append(
                {
                    "bbox": box.xyxy[0].detach().cpu().numpy().astype(np.float32),
                    "confidence": float(box.conf[0]),
                    "label": label,
                    "raw_label": raw_label,
                    "class_id": class_id,
                }
            )

        return detections

    @staticmethod
    def draw(frame: np.ndarray, detections: list[dict[str, Any]]) -> np.ndarray:
        colors = {
            "human": (0, 220, 0),
            "zombie": (0, 0, 255),
        }

        for detection in detections:
            bbox = detection["bbox"].astype(int)
            label = detection["label"]
            confidence = detection["confidence"]
            color = colors.get(label, (255, 180, 0))

            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(
                frame,
                f"{label} {confidence:.2f}",
                (bbox[0], max(20, bbox[1] - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

        return frame


class PanTiltController:
    """Serial controller for the Arduino Mega + HW-170 pan/tilt sketch.

    Uses the model-space command range expected by pan_tilt_controller.ino:
    pan 90..270 with 180 centered, tilt 80..150 with 90 centered.
    """

    def __init__(
        self,
        port: str,
        baud_rate: int = 9600,
        pan_start: float = 180.0,
        tilt_start: float = 90.0,
        pan_min: float = 90.0,
        pan_max: float = 270.0,
        tilt_min: float = 80.0,
        tilt_max: float = 150.0,
        pan_gain: float = 6.0,
        tilt_gain: float = 6.0,
        deadband_px: int = 20,
        command_interval: float = 0.05,
        invert_pan: bool = True,
        invert_tilt: bool = False,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn: Any = None
        self.is_connected = False
        self.current_pan = float(np.clip(pan_start, pan_min, pan_max))
        self.current_tilt = float(np.clip(tilt_start, tilt_min, tilt_max))
        self.pan_min = pan_min
        self.pan_max = pan_max
        self.tilt_min = tilt_min
        self.tilt_max = tilt_max
        self.pan_gain = pan_gain
        self.tilt_gain = tilt_gain
        self.deadband_px = max(0, deadband_px)
        self.command_interval = max(0.0, command_interval)
        self.invert_pan = invert_pan
        self.invert_tilt = invert_tilt
        self._last_command_time = 0.0

    def connect(self) -> bool:
        try:
            import serial

            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2.0)
            self.is_connected = True
            self.move_to(self.current_pan, self.current_tilt, force=True)
        except Exception as exc:  # noqa: BLE001 - serial availability varies.
            self.is_connected = False
            print(f"Warning: could not connect to pan/tilt controller: {exc}")

        return self.is_connected

    def send(self, command: str) -> None:
        if not self.is_connected or self.serial_conn is None:
            return
        self.serial_conn.write(f"{command}\n".encode("utf-8"))

    def move_to(self, pan: float, tilt: float, force: bool = False) -> tuple[float, float]:
        now = time.monotonic()
        if not force and now - self._last_command_time < self.command_interval:
            return self.current_pan, self.current_tilt

        self.current_pan = float(np.clip(pan, self.pan_min, self.pan_max))
        self.current_tilt = float(np.clip(tilt, self.tilt_min, self.tilt_max))
        self.send(f"PAN:{self.current_pan:.1f},TILT:{self.current_tilt:.1f}")
        self._last_command_time = now
        return self.current_pan, self.current_tilt

    def target_bbox(self, bbox: np.ndarray, frame_shape: tuple[int, ...]) -> tuple[float, float]:
        height, width = frame_shape[:2]
        x1, y1, x2, y2 = bbox.astype(float)
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        error_x = cx - width / 2.0
        error_y = cy - height / 2.0
        pan_delta = 0.0
        tilt_delta = 0.0

        if abs(error_x) > self.deadband_px:
            pan_delta = (error_x / (width / 2.0)) * self.pan_gain
        if abs(error_y) > self.deadband_px:
            tilt_delta = (error_y / (height / 2.0)) * self.tilt_gain

        if self.invert_pan:
            pan_delta *= -1.0
        if self.invert_tilt:
            tilt_delta *= -1.0

        if pan_delta == 0.0 and tilt_delta == 0.0:
            return self.current_pan, self.current_tilt

        return self.move_to(self.current_pan + pan_delta, self.current_tilt + tilt_delta)

    def disconnect(self) -> None:
        if self.serial_conn is not None:
            self.serial_conn.close()
        self.is_connected = False


class VideoWriter:
    """OpenCV video writer with lazy output directory creation."""

    def __init__(self, output_path: str, fps: int, width: int, height: int) -> None:
        self.output_path = Path(output_path)
        self.fps = fps
        self.width = width
        self.height = height
        self.writer: cv2.VideoWriter | None = None

    def open(self) -> bool:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(
            str(self.output_path),
            fourcc,
            self.fps,
            (self.width, self.height),
        )
        return bool(self.writer.isOpened())

    def write(self, frame: np.ndarray) -> None:
        if self.writer is not None:
            self.writer.write(frame)

    def release(self) -> None:
        if self.writer is not None:
            self.writer.release()


class ALDS:
    """Object detection + depth ranking + optional Arduino servo aiming."""

    def __init__(self, config_path: str) -> None:
        self.config = self._load_config(config_path)
        detection_config = self.config["detection"]
        depth_config = self.config["depth"]
        pan_tilt_config = self.config.get("pan_tilt", {})
        self.depth_enabled = bool(depth_config.get("enabled", True))
        self.depth_update_interval = max(1, int(depth_config.get("update_interval", 1)))

        self.detector = ObjectDetector(
            model_path=detection_config["model"],
            confidence_threshold=float(detection_config.get("confidence_threshold", 0.5)),
            iou_threshold=float(detection_config.get("iou_threshold", 0.45)),
            classes=detection_config.get("classes"),
        )
        self.depth_estimator = DepthEstimator(
            model_type=str(depth_config.get("encoder", "vits")),
            device=str(depth_config.get("device", "auto")),
            input_size=int(depth_config.get("input_size", 518)),
            initialize=self.depth_enabled,
        )
        self.pan_tilt_config = pan_tilt_config
        self.pan_tilt_controller = PanTiltController(
            port=str(pan_tilt_config.get("port", "/dev/ttyUSB0")),
            baud_rate=int(pan_tilt_config.get("baud_rate", 9600)),
            pan_start=float(pan_tilt_config.get("pan_start", 180.0)),
            tilt_start=float(pan_tilt_config.get("tilt_start", 90.0)),
            pan_min=float(pan_tilt_config.get("pan_min", 90.0)),
            pan_max=float(pan_tilt_config.get("pan_max", 270.0)),
            tilt_min=float(pan_tilt_config.get("tilt_min", 80.0)),
            tilt_max=float(pan_tilt_config.get("tilt_max", 150.0)),
            pan_gain=float(pan_tilt_config.get("pan_gain", 6.0)),
            tilt_gain=float(pan_tilt_config.get("tilt_gain", 6.0)),
            deadband_px=int(pan_tilt_config.get("deadband_px", 20)),
            command_interval=float(pan_tilt_config.get("command_interval", 0.05)),
            invert_pan=bool(pan_tilt_config.get("invert_pan", True)),
            invert_tilt=bool(pan_tilt_config.get("invert_tilt", False)),
        )
        self.target_class = str(pan_tilt_config.get("target_class", "any")).lower()
        self.fallback_to_any_detection = bool(pan_tilt_config.get("fallback_to_any_detection", False))
        self.pan_tilt_enabled = bool(pan_tilt_config.get("enabled", False))
        self.video_writer: VideoWriter | None = None

    @staticmethod
    def _load_config(config_path: str) -> dict[str, Any]:
        with open(config_path, "r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)

    def _open_video(self) -> cv2.VideoCapture:
        video_config = self.config["video"]
        source = video_config.get("source", 0)
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(video_config.get("width", 800)))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(video_config.get("height", 600)))
        cap.set(cv2.CAP_PROP_FPS, int(video_config.get("fps", 60)))
        return cap

    def _open_writer(self) -> None:
        output_config = self.config["output"]
        if not output_config.get("save_video", False):
            return

        video_config = self.config["video"]
        output_path = Path(output_config.get("results_dir", "results")) / "output.mp4"
        self.video_writer = VideoWriter(
            str(output_path),
            fps=int(video_config.get("fps", 60)),
            width=int(video_config.get("width", 800)),
            height=int(video_config.get("height", 600)),
        )
        if not self.video_writer.open():
            print("Warning: could not open output video writer")
            self.video_writer = None

    def find_nearest_target(
        self,
        detections: list[dict[str, Any]],
        depth: np.ndarray,
        frame_shape: tuple[int, ...],
    ) -> dict[str, Any] | None:
        """Select the nearest configured target.

        With Depth Anything available, the highest median normalized depth value
        in the box is treated as closest. Without depth, larger boxes are used
        as a practical fallback because nearby objects usually occupy more area.
        """
        if self.target_class in {"any", "all", "*"}:
            candidates = detections
        else:
            candidates = [
                detection
                for detection in detections
                if detection["label"].lower() == self.target_class
            ]
            if not candidates and self.fallback_to_any_detection:
                candidates = detections
        if not candidates:
            return None

        best_target = None
        best_score = -1.0
        frame_area = float(frame_shape[0] * frame_shape[1])
        min_depth = float(self.pan_tilt_config.get("min_distance", 0.0))
        max_depth = float(self.pan_tilt_config.get("max_distance", 1.0))

        for detection in candidates:
            bbox = detection["bbox"]
            if self.depth_estimator.is_ready:
                score = self.depth_estimator.get_bbox_depth(depth, bbox)
                if not min_depth <= score <= max_depth:
                    continue
            else:
                x1, y1, x2, y2 = bbox
                score = max(0.0, ((x2 - x1) * (y2 - y1)) / frame_area)

            if score > best_score:
                best_score = score
                best_target = {**detection, "depth_score": score}

        return best_target

    @staticmethod
    def draw_target(frame: np.ndarray, target: dict[str, Any], pan_tilt: tuple[float, float] | None) -> None:
        bbox = target["bbox"].astype(int)
        cx = int((bbox[0] + bbox[2]) / 2)
        cy = int((bbox[1] + bbox[3]) / 2)
        cv2.circle(frame, (cx, cy), 30, (0, 0, 255), 2)
        cv2.line(frame, (cx - 45, cy), (cx + 45, cy), (0, 0, 255), 1)
        cv2.line(frame, (cx, cy - 45), (cx, cy + 45), (0, 0, 255), 1)

        aim_text = ""
        if pan_tilt is not None:
            aim_text = f" PAN:{pan_tilt[0]:.0f} TILT:{pan_tilt[1]:.0f}"
        cv2.putText(
            frame,
            f"TARGET {target['label'].upper()} D:{target['depth_score']:.2f}{aim_text}",
            (bbox[0], max(20, bbox[1] - 28)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (0, 0, 255),
            2,
        )

    def draw_status(self, frame: np.ndarray, detections: list[dict[str, Any]]) -> None:
        human_count = sum(1 for item in detections if item["label"] == "human")
        if self.target_class in {"any", "all", "*"}:
            target_count = len(detections)
            target_label = "Targets"
        else:
            target_count = sum(1 for item in detections if item["label"] == self.target_class)
            target_label = f"{self.target_class.title()}s"
        lines = [
            f"Humans: {human_count}",
            f"{target_label}: {target_count}",
        ]

        if not self.detector.is_ready:
            lines.append(f"Detector unavailable: {self.detector.error}")
        if not self.depth_enabled:
            lines.append("Depth disabled: using bbox-size fallback")
        elif not self.depth_estimator.is_ready:
            lines.append("Depth unavailable: using bbox-size fallback")
        if self.pan_tilt_enabled and not self.pan_tilt_controller.is_connected:
            lines.append("Pan/tilt controller offline")
        if self.pan_tilt_enabled and self.pan_tilt_controller.is_connected:
            lines.append("Pan/tilt tracking enabled")

        for index, line in enumerate(lines):
            cv2.putText(
                frame,
                line[:90],
                (10, 30 + index * 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.62,
                (0, 215, 255),
                2,
            )

    def run(self) -> None:
        cap = self._open_video()
        if not cap.isOpened():
            print("Failed to open video source")
            return

        if self.pan_tilt_enabled:
            self.pan_tilt_controller.connect()
        self._open_writer()

        frame_index = 0
        last_depth: np.ndarray | None = None

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                if self.config["video"].get("flip_horizontal", False):
                    frame = cv2.flip(frame, 1)

                detections = self.detector.detect(frame)
                if self.depth_enabled:
                    should_update_depth = frame_index % self.depth_update_interval == 0 or last_depth is None
                    if should_update_depth:
                        last_depth = self.depth_estimator.estimate_depth(frame)
                    depth = last_depth
                else:
                    depth = np.zeros(frame.shape[:2], dtype=np.float32)
                output_frame = frame.copy()

                if self.config["output"].get("draw_depth", True) and self.depth_estimator.is_ready:
                    depth_vis = self.depth_estimator.visualize_depth(depth)
                    output_frame = cv2.addWeighted(output_frame, 0.72, depth_vis, 0.28, 0)

                if self.config["output"].get("draw_bbox", True):
                    output_frame = self.detector.draw(output_frame, detections)

                target = self.find_nearest_target(detections, depth, frame.shape)
                pan_tilt = None
                if target is not None:
                    if self.pan_tilt_enabled and self.pan_tilt_controller.is_connected:
                        pan_tilt = self.pan_tilt_controller.target_bbox(target["bbox"], frame.shape)
                    self.draw_target(output_frame, target, pan_tilt)

                self.draw_status(output_frame, detections)
                cv2.imshow("ALDS", output_frame)

                if self.video_writer is not None:
                    self.video_writer.write(output_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                frame_index += 1
        finally:
            cap.release()
            if self.video_writer is not None:
                self.video_writer.release()
            self.pan_tilt_controller.disconnect()
            cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="ALDS")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/config.yaml",
        help="Path to configuration file",
    )
    args = parser.parse_args()
    ALDS(args.config).run()


if __name__ == "__main__":
    main()
