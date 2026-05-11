"""Depth estimation helper for the ALDS pipeline.

The estimator prefers Depth Anything V2 through Hugging Face Transformers. If
the model cannot be loaded, callers can still run detection and fall back to a
non-depth targeting heuristic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class DepthConfig:
    """Configuration for the depth model."""

    encoder: str = "vits"
    device: str = "auto"
    input_size: int = 518


class DepthEstimator:
    """Estimate a normalized relative depth/proximity map for an OpenCV frame."""

    MODEL_IDS = {
        "vits": "depth-anything/Depth-Anything-V2-Small-hf",
        "vitb": "depth-anything/Depth-Anything-V2-Base-hf",
        "vitl": "depth-anything/Depth-Anything-V2-Large-hf",
    }

    def __init__(
        self,
        model_type: str = "vits",
        device: str = "auto",
        input_size: int = 518,
        initialize: bool = True,
    ) -> None:
        self.config = DepthConfig(model_type, device, input_size)
        self.model_id = self.MODEL_IDS.get(model_type, model_type)
        self.is_ready = False
        self.error: str | None = None
        self._torch: Any = None
        self._processor: Any = None
        self._model: Any = None
        self._device = "cpu"

        if initialize:
            self.load()

    def load(self) -> bool:
        """Load the configured depth model."""
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForDepthEstimation

            self._torch = torch
            if self.config.device == "auto":
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self._device = self.config.device

            self._processor = AutoImageProcessor.from_pretrained(
                self.model_id,
                size={"height": self.config.input_size, "width": self.config.input_size},
            )
            self._model = AutoModelForDepthEstimation.from_pretrained(self.model_id)
            self._model.to(self._device)
            self._model.eval()
            self.is_ready = True
            self.error = None
        except Exception as exc:  # noqa: BLE001 - keep video pipeline usable.
            self.is_ready = False
            self.error = str(exc)

        return self.is_ready

    def estimate_depth(self, frame: np.ndarray) -> np.ndarray:
        """Return a normalized `0..1` proximity map matching the frame size.

        Higher values are treated as closer/more targetable by the main
        pipeline. If the model is unavailable, this returns a zero map.
        """
        height, width = frame.shape[:2]
        if not self.is_ready or self._model is None or self._processor is None:
            return np.zeros((height, width), dtype=np.float32)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inputs = self._processor(images=rgb_frame, return_tensors="pt")
        inputs = {key: value.to(self._device) for key, value in inputs.items()}

        with self._torch.no_grad():
            outputs = self._model(**inputs)
            predicted_depth = outputs.predicted_depth
            depth = self._torch.nn.functional.interpolate(
                predicted_depth.unsqueeze(1),
                size=(height, width),
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        depth_np = depth.detach().cpu().numpy().astype(np.float32)
        return self._normalize(depth_np)

    @staticmethod
    def _normalize(depth: np.ndarray) -> np.ndarray:
        depth = np.nan_to_num(depth, nan=0.0, posinf=0.0, neginf=0.0)
        min_value = float(depth.min())
        max_value = float(depth.max())
        if max_value - min_value < 1e-6:
            return np.zeros_like(depth, dtype=np.float32)
        return ((depth - min_value) / (max_value - min_value)).astype(np.float32)

    @staticmethod
    def get_depth_at_point(depth: np.ndarray, x: int, y: int) -> float:
        """Read a normalized depth/proximity value at an image coordinate."""
        if depth.size == 0:
            return 0.0
        height, width = depth.shape[:2]
        px = int(np.clip(x, 0, width - 1))
        py = int(np.clip(y, 0, height - 1))
        return float(depth[py, px])

    @staticmethod
    def get_bbox_depth(depth: np.ndarray, bbox: np.ndarray) -> float:
        """Use the median depth inside the detection box as a stable score."""
        if depth.size == 0:
            return 0.0

        height, width = depth.shape[:2]
        x1, y1, x2, y2 = bbox.astype(int)
        x1 = int(np.clip(x1, 0, width - 1))
        x2 = int(np.clip(x2, x1 + 1, width))
        y1 = int(np.clip(y1, 0, height - 1))
        y2 = int(np.clip(y2, y1 + 1, height))
        crop = depth[y1:y2, x1:x2]
        if crop.size == 0:
            return 0.0
        return float(np.median(crop))

    @staticmethod
    def visualize_depth(depth: np.ndarray) -> np.ndarray:
        """Create a color visualization for overlay/debugging."""
        depth_u8 = np.clip(depth * 255.0, 0, 255).astype(np.uint8)
        return cv2.applyColorMap(depth_u8, cv2.COLORMAP_INFERNO)
