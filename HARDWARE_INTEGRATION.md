# Hardware Integration Guide

This document describes the current integration behavior in the repo as implemented.

The hardware build is a camera-mounted 2-axis pan/tilt system. Python reads camera frames, selects the nearest configured object, and sends pan/tilt commands to an Arduino Mega 2560. The Mega controls two MG996R servos through an HW-170/PCA9685 servo driver over I2C.

## System Architecture

```text
Python Computer Vision System
  YOLO detection + relative depth ranking
        |
        | USB serial, 9600 baud
        v
Arduino Mega 2560
  Receives PAN/TILT serial commands
        |
        | I2C: SDA D20, SCL D21
        v
HW-170 / PCA9685 Servo Driver
  Channel 0: Pan MG996R
  Channel 1: Tilt MG996R
```

## Data Flow

1. **Video Capture** (`ALDS._open_video` in `main.py`)
   - Reads frame from camera/video file.

2. **Object Detection** (`ObjectDetector` in `main.py`)
   - YOLO detects configured classes.
   - Maps `person` detections to logical `human`.
   - Returns bounding boxes, labels, class ids, and confidence scores.

3. **Depth Estimation** (`depth_estimator.py`)
   - Depth Anything V2 analyzes the frame when the model is available.
   - Returns a relative depth/proximity map normalized to `0..1`.
   - Can be disabled with `depth.enabled: false`.
   - Can be throttled with `depth.update_interval`.

4. **Target Selection** (`main.py`)
   - Finds the closest configured target class within the configured relative-depth range.
   - Targets the nearest configured detection when `pan_tilt.target_class: any`.
   - Can fall back to all detections with `pan_tilt.fallback_to_any_detection: true`.
   - Uses bounding-box size as a fallback when depth is disabled or unavailable.

5. **Pan/Tilt Control** (`PanTiltController` in `main.py`)
   - Sends commands to Arduino Mega via serial.
   - Command format: `PAN:180,TILT:90`.
   - Uses closed-loop corrections to move the camera toward the target center.

6. **Arduino Execution** (`pan_tilt_controller.ino`)
   - Receives serial commands.
   - Sends servo positions to the HW-170/PCA9685 over I2C.
   - HW-170 generates PWM for the MG996R servos.

## Serial Protocol

### Command Format

```text
PAN:angle,TILT:angle
STATUS
```

### Python to Arduino Example

```python
self.serial_conn.write(b"PAN:180.0,TILT:90.0\n")
```

### Arduino Response

```text
PAN:180 TILT:90
```

The sketch clamps commands to its model-space range:

- `PAN`: `90..270`, with `180` centered.
- `TILT`: `80..150`, with `90` centered.

## Camera-On-Pan/Tilt Tracking

The camera is mounted on top of the 2-axis pan/tilt head. That means targeting is a closed-loop correction:

1. Detect the nearest configured target.
2. Measure how far the target center is from the image center.
3. Nudge the current servo angles by a small amount.
4. Repeat until the target is centered.

This is different from a fixed-camera setup. If the software mapped image coordinates directly to absolute servo angles, the head would tend to jump back toward center after the target becomes centered in the camera view.

```text
error_x = cx - w / 2
error_y = cy - h / 2
pan  = current_pan  + normalized(error_x) * pan_gain
tilt = current_tilt + normalized(error_y) * tilt_gain
```

Use `pan_tilt.invert_pan` or `pan_tilt.invert_tilt` if an axis moves away from the target during calibration.

## Connection Checklist

- [ ] Arduino Mega uploaded with `hardware/arduino/pan_tilt_controller/pan_tilt_controller.ino`.
- [ ] USB cable connected from computer to Arduino Mega.
- [ ] Arduino Mega SDA D20 connected to HW-170 SDA.
- [ ] Arduino Mega SCL D21 connected to HW-170 SCL.
- [ ] Arduino Mega GND connected to HW-170/regulator GND.
- [ ] HW-170 logic VCC connected to Arduino Mega 5V.
- [ ] Pan MG996R connected to HW-170 channel 0.
- [ ] Tilt MG996R connected to HW-170 channel 1.
- [ ] Servo rail powered by external 5V-6V regulator, not Arduino 5V.
- [ ] Serial terminal test successful with `PAN:180,TILT:90`.
- [ ] `pan_tilt.enabled` intentionally set for hardware testing.

## Troubleshooting

### No Serial Connection

- Check USB cable and Arduino driver installation.
- Verify port in `config.yaml` (macOS: `/dev/tty.usbmodem*` or `/dev/tty.usbserial*`, Linux: `/dev/ttyUSB0`, Windows: `COM3`).
- Test in Arduino IDE Serial Monitor.

### Servos Not Moving

- Check HW-170 SDA/SCL wiring to Mega D20/D21.
- Check that the pan servo is on HW-170 channel 0 and tilt is on channel 1.
- Verify servo rail power from the regulator.
- Verify Arduino Mega GND, HW-170 GND, and regulator GND are tied together.
- Test servo directly with `PAN:180,TILT:90`, then small moves such as `PAN:170,TILT:90` and `PAN:180,TILT:100`.

### Servo Moves Away From Target

- Flip `pan_tilt.invert_pan` if horizontal tracking moves the wrong way.
- Flip `pan_tilt.invert_tilt` if vertical tracking moves the wrong way.
- Lower `pan_tilt.pan_gain` or `pan_tilt.tilt_gain` if movement is too jumpy.

## Python Configuration

In `configs/config.yaml`:

```yaml
pan_tilt:
  enabled: false
  port: /dev/ttyUSB0
  baud_rate: 9600
  target_class: any
  fallback_to_any_detection: false
  min_distance: 0.05
  max_distance: 0.95
  pan_gain: 6.0
  tilt_gain: 6.0
  pan_start: 180
  tilt_start: 90
  pan_min: 90
  pan_max: 270
  tilt_min: 80
  tilt_max: 150
  deadband_px: 20
  invert_pan: true
  invert_tilt: false
```

Notes:

- `min_distance` and `max_distance` are relative depth thresholds, not calibrated meters.
- The default config keeps hardware disabled until the controller has been tested separately.
- If `depth.enabled: false` or the depth model cannot load, targeting uses larger bounding boxes as a practical nearest-object fallback.
- If the camera moves away from the target, flip the matching `invert_*` setting and test again.

## Performance Notes

- **Servo response time**: depends on load, power supply, and pan/tilt mass.
- **Detection FPS**: depends on model, resolution, CPU/GPU, and camera source.
- **Depth FPS**: Depth Anything V2 is usually the slowest stage; use `depth.input_size` and `depth.update_interval` to tune preview speed.
- **Targeting accuracy**: depends on mechanical alignment, servo backlash, and model quality.

## Demo Evidence To Capture

- Screenshot or short clip of detection overlays with target count.
- Screenshot or short clip of the target crosshair and pan/tilt angle overlay.
- Serial monitor output showing `PAN` and `TILT` behavior.
- Short video of the pan/tilt head centering an object.
- Notes on calibration, lighting, distance, and any failure cases observed.
