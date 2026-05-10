from __future__ import annotations

import numpy as np

from src.depth_estimation.depth_estimator import DepthEstimator
from src.laser_control.laser_controller import LaserController


def test_depth_estimator_returns_zero_map_when_model_is_unavailable():
    estimator = DepthEstimator(model_type="base", device="cpu", initialize=False)

    frame = np.zeros((32, 48, 3), dtype=np.uint8)
    depth = estimator.estimate_depth(frame)

    assert depth.shape == (32, 48)
    assert np.all(depth == 0)


def test_laser_target_bbox_accepts_full_opencv_frame_shape():
    controller = LaserController()
    recorded = {}

    def fake_move_laser(pan, tilt):
        recorded["pan"] = pan
        recorded["tilt"] = tilt

    controller.move_laser = fake_move_laser
    controller.target_bbox(np.array([220, 140, 420, 340]), (480, 640, 3))

    assert 0 <= recorded["pan"] <= 180
    assert 0 <= recorded["tilt"] <= 180
