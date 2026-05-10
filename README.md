# Autonomous Laser Defense System (ALDS-26-I)

Computer-vision prototype for tracking people and optional custom target classes with YOLO, relative monocular depth estimation, and Arduino pan/tilt laser control.

## What This Repo Does

- Runs a live OpenCV pipeline from a webcam or video file.
- Detects people with YOLO out of the box.
- Supports an additional custom target class such as `zombie` if your YOLO checkpoint was trained with it.
- Estimates relative depth with Depth Anything V2 when the model is available.
- Sends `PAN`, `TILT`, and `FIRE` commands to an Arduino controller when hardware is enabled.

## Important Defaults

- `configs/config.yaml` ships with `laser.enabled: false` for safe desktop testing.
- The included `models/yolov8m.pt` is a stock YOLO model. It can detect `person`, which the app maps to `human`.
- Automatic zombie targeting requires a custom YOLO checkpoint that contains a `zombie` class.
- Depth values in this repo are relative `0..1` scores, not calibrated meters.
- The first depth-model load may download files from Hugging Face unless they are already cached locally.

## Project Structure

```text
ALDS-26-I/
├── src/
│   ├── detection/            # YOLO detection and label mapping
│   ├── depth_estimation/     # Depth Anything V2 wrapper
│   ├── laser_control/        # Serial hardware control
│   └── utils/                # Config and video I/O helpers
├── hardware/
│   ├── arduino/              # Servo and fire-control firmware
│   ├── mechanical/           # Assembly and calibration notes
│   └── 3d_printing/          # Printed part notes and available STL files
├── configs/config.yaml       # Runtime configuration
├── image_demo.py             # Single-image demo
└── main.py                   # Main application
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

## Config Notes

Key settings in `configs/config.yaml`:

- `detection.model`: YOLO checkpoint path.
- `detection.classes`: Logical labels the app will look for.
- `depth.device`: `auto`, `cpu`, or `cuda`.
- `laser.enabled`: set to `true` only after wiring and testing the Arduino controller.
- `laser.target_class`: logical class to target, usually `zombie`.
- `laser.min_distance` and `laser.max_distance`: relative depth thresholds in the `0..1` range.

## Hardware

- [Hardware Integration](HARDWARE_INTEGRATION.md)
- [Arduino Setup](hardware/arduino/README.md)
- [Mechanical Guide](hardware/mechanical/README.md)
- [3D Printing](hardware/3d_printing/README.md)

## Verification

The repo includes lightweight smoke tests:

```bash
pytest -q
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
