# Hardware Integration Guide

This document describes the current integration behavior in the repo as implemented.

For the ENGR 422 project scope, the hardware contribution is the camera-based inference loop plus optional Arduino pan/tilt feedback. The robotic/mechatronic portion should be demonstrated only after software-only detection, serial communication, and safe calibration have been verified.

## System Architecture

```
┌─────────────────────────────────────────────────┐
│          Python Computer Vision System           │
│  (YOLO Detection + Depth Estimation)            │
└──────────────────┬──────────────────────────────┘
                   │
             Serial (USB)
            9600 baud
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│     Arduino Uno/Nano (laser_controller.ino)     │
│   - Pan/Tilt Servo Control (PWM)                │
│   - Laser On/Off (GPIO)                         │
│   - Fire Mechanism (Relay)                      │
└──────────────────┬──────────────────────────────┘
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Pan Servo  Tilt Servo  Laser & Fire
```

## Data Flow

### Detection & Targeting Loop

1. **Video Capture** (`ALDS._open_video` in `main.py`)
   - Reads frame from camera/video file

2. **Object Detection** (`ObjectDetector` in `main.py`)
   - YOLO detects configured classes
   - Maps `person` detections to logical `human`
   - Returns bounding boxes, labels, class ids, and confidence scores

3. **Depth Estimation** (`depth_estimator.py`)
   - Depth Anything V2 analyzes the frame when the model is available
   - Returns a relative depth map normalized to `0..1`
   - Can be disabled with `depth.enabled: false`
   - Can be throttled with `depth.update_interval`

4. **Target Selection** (`main.py`)
   - Finds the closest configured target class within the configured relative-depth range
   - Falls back to all detections if no configured target class is present
   - Uses bounding-box size as a fallback when depth is disabled or unavailable
   - Calculates servo angles

5. **Laser Control** (`LaserController` in `main.py`)
   - Sends commands to Arduino via serial
   - Pan/Tilt commands: `PAN:45,TILT:30`
   - Fire commands: `FIRE:ON` / `FIRE:OFF`
   - Keeps firing off unless `laser.auto_fire: true`

6. **Arduino Execution** (`laser_controller.ino`)
   - Receives serial commands
   - Controls servos (PWM pins 9, 10)
   - Controls laser & relay (GPIO pins 11, 12)

## Serial Protocol

### Command Format
```
PAN:angle,TILT:angle
FIRE:ON
FIRE:OFF
STATUS
```

### Python to Arduino Example
```python
# From LaserController in main.py
self.serial_conn.write(b"PAN:45.5,TILT:30.2\n")
self.serial_conn.write(b"FIRE:ON\n")
```

### Arduino Response
```
PAN:45 TILT:30
FIRING
CEASE_FIRE
```

## Angle Conversion

Frame coordinates to servo angles:

```
Frame:  (0,0) ─────────── (W,0)
         │                 │
         │   (cx,cy)       │
         │        *        │
         │                 │
        (0,H) ─────────── (W,H)

Servo command space:
  pan  = 0° .. 180°
  tilt = 0° .. 180°

Conversion in `LaserController.target_bbox`:
  pan = 90 + ((cx - w/2) / (w/2)) * 90
  tilt = 90 + ((cy - h/2) / (h/2)) * 90
```

## Connection Checklist

- [ ] Arduino uploaded with `laser_controller.ino`
- [ ] USB cable connected to Arduino
- [ ] Pan servo on pin D9
- [ ] Tilt servo on pin D10
- [ ] Laser module on pin D11
- [ ] Relay module on pin D12
- [ ] All servos powered from 5V supply
- [ ] Serial terminal test successful (see Arduino README)
- [ ] `laser.enabled` intentionally set for hardware testing
- [ ] `laser.auto_fire` kept `false` unless firing is intentional and safe
- [ ] Laser disconnected or replaced with an LED for first integration tests

## Troubleshooting

### No Serial Connection
- Check USB cable and Arduino driver installation
- Verify port in `config.yaml` (macOS: `/dev/tty.usbserial*`, Linux: `/dev/ttyUSB0`, Windows: `COM3`)
- Test in Arduino IDE Serial Monitor

### Servos Not Moving
- Check PWM pins (D9, D10) connections
- Verify servo power supply (5V, 500mA+)
- Test servo directly: `PAN:45,TILT:45`

### Laser Not Firing
- Check laser module power (D11)
- Test with command: `FIRE:ON`
- Verify relay connections and power

### Misaligned Laser
- See Calibration Procedure in `hardware/mechanical/README.md`
- Run servo to center: `PAN:90,TILT:90`
- Adjust laser mount mechanically

## Python Configuration

In `configs/config.yaml`:
```yaml
laser:
  enabled: false
  auto_fire: false
  port: /dev/ttyUSB0        # Adjust for your OS
  baud_rate: 9600
  target_class: zombie
  min_distance: 0.05
  max_distance: 0.95
```

Notes:
- `min_distance` and `max_distance` are relative depth thresholds, not calibrated meters.
- The default config keeps hardware disabled until the controller has been tested separately.
- Keep `auto_fire: false` during servo aiming and calibration; set it to `true` only when intentional.
- If `depth.enabled: false` or the depth model cannot load, targeting uses larger bounding boxes as a practical nearest-object fallback.

## Performance Notes

- **Servo Response Time**: ~0.1 seconds per command
- **Detection FPS**: Depends on model, resolution, CPU/GPU, and camera source.
- **Depth FPS**: Depth Anything V2 is usually the slowest stage; use `depth.input_size` and `depth.update_interval` to tune preview speed.
- **Latency**: depends on your CPU/GPU, model sizes, and camera resolution.
- **Targeting Accuracy**: depends on mechanical alignment, servo backlash, and your checkpoint quality.

## Demo Evidence To Capture

- Screenshot or short clip of detection overlays with human and target counts.
- Screenshot or short clip of the depth overlay or fallback status message.
- Serial monitor output showing `PAN`, `TILT`, and `FIRE:OFF` behavior.
- Notes on calibration, lighting, distance, and any failure cases observed.
