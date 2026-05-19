# ALDS-26-I Presentation Demo

Autonomous Pan/Tilt Detection System  
Computer Vision, Relative Depth, and Arduino Pan/Tilt Tracking

---

## 1. Project Goal

Build a working prototype that can:

- Read a live camera feed or video file.
- Detect relevant objects with YOLO.
- Estimate which detected object is closest.
- Select the nearest configured target.
- Optionally move a 2-axis Arduino pan/tilt platform toward that target.

The core idea is:

```text
Camera -> YOLO detection -> relative depth ranking -> target selection -> pan/tilt control
```

---

## 2. Problem Statement

The system needs to recognize objects in a moving visual scene and decide which target should receive attention first.

Main challenges:

- Detecting humans and custom targets reliably.
- Ranking targets by apparent distance.
- Keeping the hardware safe during testing.
- Moving a camera-mounted pan/tilt head smoothly toward the target.
- Powering and calibrating the servo hardware safely.

---

## 3. Repository Structure

Important files:

- `main.py`: live detection, depth, targeting, display, and serial control.
- `depth_estimator.py`: Depth Anything V2 wrapper.
- `image_demo.py`: single-image detection and depth demo.
- `evaluate_models.py`: base YOLO vs fine-tuned YOLO evaluation.
- `configs/config.yaml`: runtime configuration.
- `hardware/arduino/pan_tilt_controller/pan_tilt_controller.ino`: Arduino Mega + HW-170 servo firmware.
- `HARDWARE_INTEGRATION.md`: hardware and software integration guide.

---

## 4. System Architecture

```text
Computer / Python
  |
  | OpenCV camera frame
  v
YOLO object detector
  |
  | bounding boxes + class labels
  v
Depth estimator / fallback size ranking
  |
  | nearest target
  v
Serial command over USB
  |
  v
Arduino Mega 2560
  |
  | I2C: SDA D20, SCL D21
  v
HW-170 / PCA9685 servo driver
  |
  +-- Channel 0: Pan MG996R
  +-- Channel 1: Tilt MG996R
```

---

## 5. Detection Pipeline

The detector uses Ultralytics YOLO through `ObjectDetector` in `main.py`.

Configuration:

```yaml
detection:
  model: runs/detect/runs/detect/yolo26s_human_zombie_finetune_afterlife/weights/best.pt
  confidence_threshold: 0.5
  iou_threshold: 0.45
  classes:
    - human
    - zombie
```

Notes:

- YOLO `person` labels are mapped to the logical label `human`.
- A fine-tuned checkpoint can add the custom `zombie` class.
- The included base model is stored under `models/yolo26s.pt`.

---

## 6. Depth and Nearest Target Selection

The repo uses relative monocular depth estimation with Depth Anything V2.

Depth behavior:

- Returns a normalized `0..1` proximity map.
- Higher values are treated as closer.
- Median depth inside each bounding box is used as the target score.
- If depth is disabled or unavailable, the system falls back to bounding-box area.

This is controlled by:

```yaml
depth:
  enabled: true
  encoder: vits
  device: auto
  input_size: 256
  update_interval: 8
```

---

## 7. Targeting Logic

Target selection happens in `ALDS.find_nearest_target`.

Current behavior:

- Prefer the nearest configured detection when `pan_tilt.target_class: any`.
- Use depth score when the depth model is ready.
- Use larger bounding boxes as a practical fallback.
- Ignore non-target detections unless fallback is explicitly enabled.

Configuration:

```yaml
pan_tilt:
  target_class: any
  fallback_to_any_detection: false
  min_distance: 0.05
  max_distance: 0.95
```

For a general nearest-object demo, set:

```yaml
pan_tilt:
  target_class: any
```

---

## 8. Hardware Controller

The Arduino sketch is a low-level serial controller.

Pins:

| Component | Connection |
|---|---|
| Pan MG996R | HW-170 channel 0 |
| Tilt MG996R | HW-170 channel 1 |
| HW-170 SDA | Mega D20 / SDA |
| HW-170 SCL | Mega D21 / SCL |

Serial commands:

```text
PAN:180,TILT:90
STATUS
```

The sketch clamps commands to `PAN 90..270` and `TILT 80..150`; `PAN:180,TILT:90` is the centered position.

The Arduino does not process images. Python processes the camera feed and sends movement commands. The Mega receives those commands over USB serial, then sends servo positions to the HW-170 over I2C.

---

## 9. Camera-Mounted Pan/Tilt Tracking

The camera is mounted on top of the 2-axis motor platform.

That means the software uses closed-loop aiming:

1. Detect target.
2. Measure target center relative to image center.
3. Nudge current pan/tilt angles.
4. Repeat until the object is centered.

This avoids treating image position as an absolute servo angle, which is better for fixed-camera systems but unstable for a moving camera head.

---

## 10. Pan/Tilt Configuration

The tracking controller can be tuned without changing code:

```yaml
pan_tilt:
  pan_start: 180
  tilt_start: 90
  pan_min: 90
  pan_max: 270
  tilt_min: 80
  tilt_max: 150
  pan_gain: 6.0
  tilt_gain: 6.0
  deadband_px: 20
  command_interval: 0.05
  invert_pan: true
  invert_tilt: false
```

Calibration rule:

- If the head moves away from the target, flip `invert_pan` or `invert_tilt`.
- If movement is too jumpy, lower the gain.
- If movement is too slow, raise the gain.

---

## 11. Safety Defaults

The repo ships with safe defaults:

```yaml
pan_tilt:
  enabled: false
```

This means:

- Detection can run without moving hardware.
- Serial connection is only attempted when `pan_tilt.enabled: true`.
- The servos stay idle during software-only tests.

---

## 12. Demo Flow

Recommended live demo sequence:

1. Run software-only detection:

   ```bash
   python main.py --config configs/config.yaml
   ```

2. Show bounding boxes and target overlay.
3. Enable hardware after camera and detection work:

   ```yaml
   pan_tilt:
     enabled: true
   ```

4. Confirm serial port:

   ```yaml
   pan_tilt:
     port: /dev/tty.usbmodem...
   ```

5. Place a target off-center and show the pan/tilt head centering it.

---

## 13. Single Image Demo

For a safer or repeatable demo without a live camera:

```bash
python image_demo.py data/raw/twd1.png --no-display
```

Outputs:

- `results/detection.jpg`
- `results/depth.jpg`

This demonstrates:

- Model loading.
- Object detection.
- Depth visualization.
- Human and target counts.

---

## 14. Model Training Workflow

Dataset workflow:

1. Put videos/images in `data/raw/`.
2. Extract frames:

   ```bash
   python scripts/extract_frames.py --sample-fps 1
   ```

3. Annotate frames in YOLO format.
4. Store the dataset under `data/processed/yolo_dataset/`.
5. Train YOLO:

   ```bash
   yolo detect train model=models/yolo26s.pt data=configs/zombie_dataset.yaml epochs=50 imgsz=640
   ```

6. Update `detection.model` to the selected `weights/best.pt`.

---

## 15. Evaluation Plan

The repo includes `evaluate_models.py` to compare:

- Base YOLO26 model.
- Fine-tuned ALDS checkpoint.

Metrics saved:

- Precision.
- Recall.
- F1.
- mAP50.
- mAP50-95.
- Per-class mAP when available.

Example:

```bash
python evaluate_models.py --device cpu
```

Evaluation outputs are written under:

```text
results/model_evaluation/
```

---

## 16. Current Readiness

Ready in the repo:

- YOLO detection pipeline.
- Relative depth estimation wrapper.
- Nearest-target selection.
- Arduino serial command protocol.
- Camera-mounted pan/tilt correction logic.
- Safe default config with hardware disabled.
- Hardware and calibration documentation.

Still required for the physical demo:

- macOS camera permission must be enabled for the terminal or IDE.
- Arduino serial port must be updated in `configs/config.yaml`.
- Arduino sketch must be uploaded from Arduino IDE or `arduino-cli`.
- Pan/tilt direction must be calibrated with `invert_pan` and `invert_tilt`.

---

## 17. Known Demo Notes

During the latest run attempt, the Python app started and loaded the model, but macOS denied camera access.

Observed issue:

```text
OpenCV: camera access has been denied.
Failed to open video source
```

Fix:

- Open macOS System Settings.
- Go to Privacy & Security -> Camera.
- Enable camera access for Terminal, iTerm, or the IDE being used.
- Re-run `python main.py --config configs/config.yaml`.

---

## 18. Risks and Limitations

Technical limitations:

- Monocular depth is relative, not measured in meters.
- Target ranking depends on detector quality and depth consistency.
- Servo accuracy depends on mechanical alignment and backlash.
- Fast motion can cause detection lag or overshoot.
- The custom target class requires a good fine-tuned checkpoint.

Safety limitations:

- MG996R servos should be powered from the external regulator, not the Arduino 5V pin.
- Servo calibration should start with small gains and low-speed movement.
- Humans should remain a protected class, not an automatic target.

---

## 19. What We Would Show in the Final Demo

Visual evidence:

- Live camera feed with detection boxes.
- Depth overlay or fallback targeting status.
- Target crosshair over the selected nearest object.
- Serial monitor output showing `PAN` and `TILT`.
- Pan/tilt platform physically centering the target.

Configuration evidence:

- `pan_tilt.enabled: true`
- Correct Arduino serial port.
- Calibrated axis inversion settings.

---

## 20. Closing

ALDS-26-I demonstrates an end-to-end robotics perception loop:

```text
See -> Detect -> Estimate proximity -> Choose target -> Move hardware
```

The project combines:

- Computer vision.
- Model training and evaluation.
- Relative depth estimation.
- Serial hardware control.
- Mechanical calibration and safety constraints.

The current implementation is ready for software demonstration and prepared for hardware integration after camera permission, Arduino upload, and servo calibration are completed.
