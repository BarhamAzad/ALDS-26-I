# Arduino Laser Controller Setup

## Components

### Servos
- **Pan Servo**: SG90 or MG90S (horizontal movement)
- **Tilt Servo**: SG90 or MG90S (vertical movement)
- Power: 5V, 500mA per servo

### Laser Module
- **Type**: 5V laser diode module (laser pointer or actual laser)
- **Power**: 5V, ~50mA
- **Control**: Direct pin control (HIGH = on, LOW = off)

### Relay Module
- **Type**: Single-channel 5V relay module
- **Purpose**: Fire trigger mechanism
- **Control**: GPIO pin switching

### Arduino
- **Board**: Arduino Uno or Nano
- **Serial**: USB to TTL 9600 baud
- **Supply**: 9V via barrel jack (or USB)

## Pin Configuration

| Component | Arduino Pin | Function |
|-----------|-------------|----------|
| Pan Servo | D9 (PWM) | Horizontal servo control |
| Tilt Servo | D10 (PWM) | Vertical servo control |
| Laser | D11 | Laser enable |
| Relay (Fire) | D12 | Fire trigger mechanism |

## Wiring Diagram

```
Arduino 5V ──┬─── Pan Servo (red wire)
             ├─── Tilt Servo (red wire)
             ├─── Laser Module (5V+)
             └─── Relay Module (VCC)

Arduino GND ─┬─── Pan Servo (black wire)
             ├─── Tilt Servo (black wire)
             ├─── Laser Module (GND)
             └─── Relay Module (GND)

D9 (PWM) ────── Pan Servo (yellow/signal wire)
D10 (PWM) ───── Tilt Servo (yellow/signal wire)
D11 ──────────── Laser Module (IN)
D12 ──────────── Relay Module (IN)
```

## Serial Commands

Send commands via Serial at 9600 baud:

```
PAN:45.5,TILT:30.2  # Move to Pan: 45.5°, Tilt: 30.2°
FIRE:ON              # Turn on laser and fire
FIRE:OFF             # Turn off laser and fire
STATUS               # Get current status
```

## Installation

1. Upload `laser_controller.ino` to Arduino board
2. Connect components according to wiring diagram
3. Power Arduino (9V or USB)
4. Connect USB to computer for serial communication
5. Set `laser.port` in `configs/config.yaml` for your OS, for example `/dev/ttyUSB0`, `/dev/tty.usbserial*`, or `COM3`
6. Keep `laser.enabled: false` until manual serial testing succeeds
7. Keep `laser.auto_fire: false` for aiming-only runs
8. If the camera is mounted on the pan/tilt head, tune `laser.pan_gain`, `laser.tilt_gain`, and the `laser.invert_*` settings in small steps

## Testing

```
# In Arduino IDE Serial Monitor (9600 baud):
PAN:90,TILT:90   # Center position
FIRE:ON
FIRE:OFF
STATUS
```

When the serial test works, run the Python app with `laser.enabled: true`. With `auto_fire: false`, the app sends pan/tilt aiming commands and explicit `FIRE:OFF` commands without firing.

For camera-on-head tracking, place an object off-center in the camera view. The servos should move until the object approaches the center of the image. If either axis moves the object farther from center, flip the matching `laser.invert_pan` or `laser.invert_tilt` value.

## Integration Log

For the project report and presentation, record:

- Arduino board model and serial port.
- Servo model and power source.
- Camera model and mounting position.
- Commands tested manually.
- Any missed commands, jitter, power issues, or calibration offsets.
