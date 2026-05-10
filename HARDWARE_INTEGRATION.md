# Hardware Integration Guide

This document describes the current integration behavior in the repo as implemented.

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

1. **Video Capture** (`video_handler.py`)
   - Reads frame from camera/video file

2. **Object Detection** (`detector.py`)
   - YOLOv8 detects humans and zombies
   - Returns bounding boxes with confidence

3. **Depth Estimation** (`depth_estimator.py`)
   - Depth Anything V2 analyzes the frame when the model is available
   - Returns a relative depth map normalized to `0..1`

4. **Target Selection** (`main.py`)
   - Finds the closest configured target class within the configured relative-depth range
   - Excludes humans from targeting unless explicitly configured otherwise
   - Calculates servo angles

5. **Laser Control** (`laser_controller.py`)
   - Sends commands to Arduino via serial
   - Pan/Tilt commands: `PAN:45,TILT:30`
   - Fire commands: `FIRE:ON` / `FIRE:OFF`

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
# From laser_controller.py
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

Conversion in `laser_controller.py`:
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
  port: /dev/ttyUSB0        # Adjust for your OS
  baud_rate: 9600
  target_class: zombie
  min_distance: 0.05
  max_distance: 0.95
```

Notes:
- `min_distance` and `max_distance` are relative depth thresholds, not calibrated meters.
- The default config keeps hardware disabled until the controller has been tested separately.

## Performance Notes

- **Servo Response Time**: ~0.1 seconds per command
- **Detection FPS**: Depends on model (YOLOv8m: ~30-50 FPS)
- **Latency**: depends on your CPU/GPU, model sizes, and camera resolution.
- **Targeting Accuracy**: depends on mechanical alignment, servo backlash, and your checkpoint quality.
