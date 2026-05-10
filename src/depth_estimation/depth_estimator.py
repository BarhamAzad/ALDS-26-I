"""Depth Anything V2 depth estimation module."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import cv2
import numpy as np


_CACHE_ROOT = Path(tempfile.gettempdir()) / "alds-cache"
_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(_CACHE_ROOT / "huggingface"))


class DepthEstimator:
    """Depth estimation using Depth Anything V2."""

    MODEL_NAME_MAP = {
        "vits": "small",
        "vitb": "base",
        "vitl": "large",
        "small": "small",
        "base": "base",
        "large": "large",
    }

    def __init__(self, model_type: str = "base", device: str = "auto", initialize: bool = True):
        """
        Initialize the depth estimator.

        Args:
            model_type: Encoder/model size. Supports ``vits``, ``vitb``, ``vitl``,
                ``small``, ``base``, or ``large``.
            device: ``auto``, ``cuda``, or ``cpu``.
            initialize: Whether to attempt model initialization immediately.
        """
        self.requested_device = device.lower()
        self.model_type = model_type.lower()
        self.depth_pipeline = None
        self.is_ready = False
        self.last_error = None

        if initialize:
            self._initialize_model()

    def _resolve_model_name(self) -> str:
        variant = self.MODEL_NAME_MAP.get(self.model_type, self.model_type)
        return f"depth-anything/Depth-Anything-V2-{variant}-hf"

    def _initialize_model(self):
        """Initialize the Depth Anything V2 model lazily and safely."""
        try:
            import torch
            from transformers import pipeline
        except Exception as exc:
            self.last_error = f"Depth dependencies unavailable: {exc}"
            print(self.last_error)
            return

        try:
            use_cuda = False
            if self.requested_device == "auto":
                use_cuda = torch.cuda.is_available()
            elif self.requested_device == "cuda":
                use_cuda = torch.cuda.is_available()
                if not use_cuda:
                    print("CUDA requested for depth estimation but no GPU is available. Falling back to CPU.")
            elif self.requested_device != "cpu":
                print(f"Unknown depth device '{self.requested_device}'. Falling back to auto selection.")
                use_cuda = torch.cuda.is_available()

            model_name = self._resolve_model_name()
            device_idx = 0 if use_cuda else -1
            self.depth_pipeline = pipeline(
                task="depth-estimation",
                model=model_name,
                device=device_idx,
            )
            self.is_ready = True
            self.last_error = None
            print(f"Depth model loaded: {model_name}")
        except Exception as exc:
            self.depth_pipeline = None
            self.is_ready = False
            self.last_error = (
                "Depth model unavailable. The app will continue without depth-based targeting. "
                f"Reason: {exc}"
            )
            print(self.last_error)

    def estimate_depth(self, frame: np.ndarray) -> np.ndarray:
        """
        Estimate a relative depth map from a frame.

        Args:
            frame: Input image frame in BGR format.

        Returns:
            Depth map normalized to the ``0..1`` range.
        """
        if self.depth_pipeline is None:
            return np.zeros(frame.shape[:2], dtype=np.float32)

        try:
            from PIL import Image

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            result = self.depth_pipeline(pil_image)
            depth_map = np.array(result["depth"], dtype=np.float32)

            min_value = float(depth_map.min())
            max_value = float(depth_map.max())
            depth_normalized = (depth_map - min_value) / (max_value - min_value + 1e-6)
            return depth_normalized.astype(np.float32)
        except Exception as exc:
            self.last_error = f"Error in depth estimation: {exc}"
            print(self.last_error)
            return np.zeros(frame.shape[:2], dtype=np.float32)

    def get_depth_at_point(self, depth_map: np.ndarray, x: int, y: int, window_size: int = 5) -> float:
        """
        Get the average depth value around a point.

        Args:
            depth_map: Depth estimation map.
            x: X coordinate.
            y: Y coordinate.
            window_size: Window size for averaging.

        Returns:
            Relative depth value in the ``0..1`` range.
        """
        h, w = depth_map.shape[:2]
        half_window = max(1, window_size // 2)
        x1 = max(0, x - half_window)
        x2 = min(w, x + half_window + 1)
        y1 = max(0, y - half_window)
        y2 = min(h, y + half_window + 1)

        region = depth_map[y1:y2, x1:x2]
        return float(np.mean(region)) if region.size > 0 else 0.0

    def visualize_depth(self, depth_map: np.ndarray) -> np.ndarray:
        """
        Create a color visualization of the depth map.

        Args:
            depth_map: Depth estimation map.

        Returns:
            Colored depth visualization.
        """
        depth_normalized = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return cv2.applyColorMap(depth_normalized, cv2.COLORMAP_TURBO)
