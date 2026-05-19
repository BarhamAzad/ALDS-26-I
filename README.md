# Autonomous Pan/Tilt Detection System (ALDS-26-I)

Computer-vision prototype for tracking objects with YOLO, relative monocular depth estimation, and Arduino Mega + HW-170 pan/tilt servo control.

## What This Repo Does

- Runs a live OpenCV pipeline from a webcam or video file.
- Detects people with YOLO out of the box.
- Supports an additional custom target class such as `zombie` if your YOLO checkpoint was trained with it.
- Estimates relative depth with Depth Anything V2 when the model is available.
- Sends `PAN` and `TILT` commands to an Arduino Mega controller when hardware is enabled.

## Course Project Framing

This repository is structured as an ENGR 422 computer vision project prototype: an end-to-end vision pipeline with data acquisition, annotation, model training, evaluation, live inference, and optional mechatronic interaction.

Problem definition:
- Goal: detect and rank relevant targets in a camera feed while preserving human detections as a protected class.
- Engineering context: real-time perception, relative depth ranking, and closed-loop pan/tilt control.
- Success criteria: reliable human/target detection, reproducible training and inference, clear evaluation metrics, documented failure cases, and safe hardware behavior.

Core pipeline:

```text
Camera or video -> YOLO detection -> relative depth/proximity scoring -> target selection -> OpenCV display -> optional Arduino pan/tilt commands
```

## Important Defaults

- `configs/config.yaml` ships with `pan_tilt.enabled: false` for safe desktop testing.
- The default config points at a local fine-tuned checkpoint under `runs/`. That directory is ignored by Git, so new clones must either train/download that checkpoint or set `detection.model` to another local `.pt` file.
- The repo also includes `models/yolo26s.pt` as a base YOLO26 model.
- YOLO labels named `person` are mapped to the logical label `human`.
- Zombie targeting requires a checkpoint that contains a `zombie` class.
- Depth values in this repo are relative `0..1` scores, not calibrated meters.
- The first depth-model load may download files from Hugging Face unless they are already cached locally.
- Depth can be disabled with `depth.enabled: false`; targeting then falls back to bounding-box size.

## Project Structure

```text
ALDS-26-I/
├── main.py                   # Live detection, targeting, serial control, and video I/O
├── depth_estimator.py        # Depth Anything V2 wrapper with graceful fallback
├── image_demo.py             # Single-image detection/depth demo
├── configs/
│   ├── config.yaml           # Runtime configuration
│   └── zombie_dataset.yaml   # YOLO dataset config for custom training
├── data/
│   ├── raw/                  # Source videos/images for dataset prep
│   └── processed/            # Extracted frames and YOLO dataset output
├── scripts/
│   └── extract_frames.py     # Sparse frame extraction for annotation
├── hardware/
│   ├── arduino/              # Arduino Mega + HW-170 pan/tilt firmware
│   ├── mechanical/           # Assembly and calibration notes
│   └── 3d_printing/          # Printed part notes and available STL files
├── models/                   # Local base/model weights
├── results/                  # Generated demo/video outputs
└── runs/                     # Generated YOLO training/evaluation runs
```

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run the live app:

```bash
python main.py --config configs/config.yaml
```

Run the single-image demo:

```bash
python image_demo.py /path/to/image.jpg --no-display
```

The demo writes `results/detection.jpg` and `results/depth.jpg`.

## Config Notes

Key settings in `configs/config.yaml`:

- `detection.model`: YOLO checkpoint path.
- `detection.confidence_threshold` and `detection.iou_threshold`: prediction filtering.
- `detection.classes`: Logical labels the app will look for.
- `depth.enabled`: set `false` to skip model loading and use the bbox-size fallback.
- `depth.device`: `auto`, `cpu`, or `cuda`.
- `depth.input_size`: square model input size for Depth Anything V2.
- `depth.update_interval`: estimate depth every N frames to improve live preview speed.
- `pan_tilt.enabled`: set to `true` only after wiring and testing the Arduino controller.
- `pan_tilt.target_class`: use `any` to track the nearest configured detection, currently `human` or `zombie`.
- `pan_tilt.fallback_to_any_detection`: set `true` only if the head should track the nearest detected object when the target class is absent.
- `pan_tilt.min_distance` and `pan_tilt.max_distance`: relative depth thresholds in the `0..1` range.
- `pan_tilt.pan_gain`, `pan_tilt.tilt_gain`, and `pan_tilt.deadband_px`: closed-loop camera-on-pan/tilt aiming sensitivity.
- `pan_tilt.pan_min/max` and `pan_tilt.tilt_min/max`: Arduino model-space limits; the current sketch uses `PAN 90..270` and `TILT 80..150`.
- `pan_tilt.invert_pan` and `pan_tilt.invert_tilt`: flip an axis if calibration shows it moves away from the target.

## Dataset And Training

Dataset workflow:

1. Place source videos/images under `data/raw/`.
2. Extract annotation frames with `scripts/extract_frames.py`.
3. Annotate frames in YOLO detection format.
4. Save the final dataset under `data/processed/yolo_dataset/`.
5. Train with `configs/zombie_dataset.yaml`.
6. Update `detection.model` to the selected `weights/best.pt`.

See [data/processed/README.md](data/processed/README.md) for the dataset layout and an example training command.

## Evaluation Plan

Recommended project evidence:

- Detection metrics: precision, recall, F1, mAP50, and confusion matrix from YOLO validation.
- Runtime metrics: FPS, depth update interval, latency, CPU/GPU device, and camera resolution.
- Robustness tests: lighting changes, motion blur, camera movement, occlusion, and distance changes.
- Ablations: detection only, detection plus depth, depth throttling values, and hardware disabled/enabled.
- Error analysis: false positives, missed detections, class confusion, bad depth ranking, and servo misalignment.

Keep generated experiment artifacts in `runs/` and summarize the chosen runs in the final report or presentation.

## Reproducibility

- Use `requirements.txt` for the Python environment.
- Keep runtime settings in `configs/config.yaml`.
- Keep dataset split definitions stable in `configs/zombie_dataset.yaml`.
- Document local-only weights or datasets that are too large to commit.
- Commit code, configuration, hardware notes, and experiment summaries.

## Safety And Ethics

- Keep `pan_tilt.enabled: false` for software-only testing.
- Enable pan/tilt hardware only after the Arduino Mega and HW-170 pass manual serial tests.
- Power MG996R servos from the external regulator, not from the Arduino Mega 5V pin.
- Treat the `human` class as protected; do not configure automatic targeting for people.
- Document limitations and failure cases clearly in reports and presentations.

## Hardware

- [Hardware Integration](HARDWARE_INTEGRATION.md)
- [Arduino Setup](hardware/arduino/README.md)
- [Mechanical Guide](hardware/mechanical/README.md)
- [3D Printing](hardware/3d_printing/README.md)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
