"""YOLO object detection module."""

from __future__ import annotations

import inspect
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import torch.nn as nn
import torch


_CACHE_ROOT = Path(tempfile.gettempdir()) / "alds-cache"
(_CACHE_ROOT / "ultralytics").mkdir(parents=True, exist_ok=True)
(_CACHE_ROOT / "matplotlib").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(_CACHE_ROOT / "ultralytics"))
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))

from ultralytics import YOLO


class ObjectDetector:
    """YOLO-based detector for humans and optional custom target classes."""

    DEFAULT_LABELS = ("human", "zombie")
    DISPLAY_COLORS = {
        "human": (0, 255, 0),
        "zombie": (0, 0, 255),
    }
    LABEL_ALIASES = {
        "human": ("human", "person"),
        "zombie": ("zombie",),
    }

    def __init__(self, model_path: str, confidence_threshold: float = 0.5, class_names: list[str] | None = None):
        """
        Initialize the object detector.

        Args:
            model_path: Path to a YOLO model checkpoint.
            confidence_threshold: Minimum confidence for detections.
            class_names: Logical class labels expected by the app.
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.class_names = [str(name).lower() for name in (class_names or self.DEFAULT_LABELS)]
        self.model = None
        self.model_names: dict[int, str] = {}
        self.is_ready = False
        self.last_error = None

        self._load_model()

    @staticmethod
    def _safe_label_key(label: str) -> str:
        if label == "human":
            return "humans"
        if label.endswith("y"):
            return f"{label[:-1]}ies"
        return f"{label}s"

    def _empty_detections(self) -> dict:
        detections = {"all": []}
        for label in self.class_names:
            detections[self._safe_label_key(label)] = []
        return detections

    def _register_safe_globals(self):
        """Allow trusted Ultralytics checkpoints to load under PyTorch 2.6+ defaults."""
        if not hasattr(torch.serialization, "add_safe_globals"):
            return

        safe_globals = [nn.Sequential, nn.ModuleList]
        try:
            import ultralytics.nn.modules as ultralytics_modules
            import ultralytics.nn.tasks as ultralytics_tasks

            for namespace in (ultralytics_modules, ultralytics_tasks):
                for value in vars(namespace).values():
                    if inspect.isclass(value) or inspect.isfunction(value):
                        safe_globals.append(value)
        except Exception as exc:
            print(f"Warning: could not register Ultralytics safe globals: {exc}")
            return

        if safe_globals:
            torch.serialization.add_safe_globals(safe_globals)

    @staticmethod
    def _load_with_unrestricted_torch(model_path: str):
        """
        Load a trusted local checkpoint with ``weights_only=False`` when required.

        PyTorch 2.6+ changed the default checkpoint loading behavior. The bundled
        local YOLO checkpoint in this repo is trusted project data, so a narrow
        fallback is safe here.
        """
        original_torch_load = torch.load

        def trusted_torch_load(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return original_torch_load(*args, **kwargs)

        torch.load = trusted_torch_load
        try:
            return YOLO(model_path)
        finally:
            torch.load = original_torch_load

    def _load_model(self):
        """Load the YOLO model, degrading gracefully if unavailable."""
        model_file = Path(self.model_path)
        if not model_file.exists():
            self.last_error = f"Detection model not found: {model_file}"
            print(self.last_error)
            return

        try:
            self._register_safe_globals()
            self.model = YOLO(str(model_file))
        except Exception as exc:
            if "Weights only load failed" not in str(exc):
                self.model = None
                self.is_ready = False
                self.last_error = (
                    "Detection model unavailable. The app will continue without detections. "
                    f"Reason: {exc}"
                )
                print(self.last_error)
                return

            try:
                self.model = self._load_with_unrestricted_torch(str(model_file))
            except Exception as retry_exc:
                self.model = None
                self.is_ready = False
                self.last_error = (
                    "Detection model unavailable. The app will continue without detections. "
                    f"Reason: {retry_exc}"
                )
                print(self.last_error)
                return

        try:
            names = self.model.names
            if isinstance(names, dict):
                self.model_names = {int(idx): str(name) for idx, name in names.items()}
            else:
                self.model_names = {idx: str(name) for idx, name in enumerate(names)}

            self.is_ready = True
            self.last_error = None
        except Exception as exc:
            self.model = None
            self.is_ready = False
            self.last_error = (
                "Detection model unavailable. The app will continue without detections. "
                f"Reason: {exc}"
            )
            print(self.last_error)

    def _logical_label_for_model_label(self, model_label: str) -> str | None:
        normalized = model_label.lower()
        for label in self.class_names:
            aliases = self.LABEL_ALIASES.get(label, (label,))
            if normalized in aliases:
                return label
        return None

    def detect(self, frame: np.ndarray) -> dict:
        """
        Detect objects in a frame.

        Args:
            frame: Input image frame.

        Returns:
            Dictionary containing detections keyed by logical label.
        """
        detections = self._empty_detections()
        if self.model is None:
            return detections

        try:
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        except Exception as exc:
            self.last_error = f"Detection failed: {exc}"
            print(self.last_error)
            return detections

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                coords = box.xyxy[0].cpu().numpy()
                model_label = self.model_names.get(cls_id, str(cls_id))
                logical_label = self._logical_label_for_model_label(model_label)

                detection = {
                    "bbox": coords,
                    "confidence": conf,
                    "class_id": cls_id,
                    "model_label": model_label,
                    "label": logical_label,
                }
                detections["all"].append(detection)

                if logical_label is not None:
                    detections[self._safe_label_key(logical_label)].append(detection)

        return detections

    def draw_detections(self, frame: np.ndarray, detections: dict) -> np.ndarray:
        """
        Draw bounding boxes on a frame.

        Args:
            frame: Input frame.
            detections: Detection results.

        Returns:
            Annotated frame.
        """
        annotated = frame.copy()

        for detection in detections.get("all", []):
            label = detection.get("label") or detection.get("model_label", "object")
            color = self.DISPLAY_COLORS.get(label, (255, 191, 0))
            bbox = detection["bbox"].astype(int)
            cv2.rectangle(annotated, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(
                annotated,
                f"{label.title()}: {detection['confidence']:.2f}",
                (bbox[0], bbox[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

        return annotated
