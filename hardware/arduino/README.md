# Arduino / HW-170 Pan-Tilt Controller Setup

## Components

### Servos
- **Pan Servo**: MG996R / 996R high-torque servo
- **Tilt Servo**: MG996R / 996R high-torque servo
- Power: external 5V-6V regulator, sized for both servos

### HW-170 / PCA9685 Servo Driver
- **Purpose**: Generates servo PWM signals from Arduino Mega I2C commands
- **Logic**: 3V-5V from Arduino Mega
- **Servo Power**: Separate 5V-6V input from regulator
- **I2C Address**: `0x40` by default

### Arduino
- **Board**: Arduino Mega 2560
- **Serial**: USB to computer at 9600 baud
- **I2C**: SDA on D20, SCL on D21

## Pin Configuration

| Connection | Arduino Mega / HW-170 Pin | Function |
|-----------|-------------|----------|
| Mega SDA | D20 / SDA | I2C data to HW-170 |
| Mega SCL | D21 / SCL | I2C clock to HW-170 |
| Mega 5V | HW-170 VCC | HW-170 logic power |
| Mega GND | HW-170 GND | Shared logic ground |
| Pan Servo | HW-170 channel 0 | Horizontal servo |
| Tilt Servo | HW-170 channel 1 | Vertical servo |

## Wiring Diagram

```text
Arduino Mega 5V --------- HW-170 VCC / logic VCC
Arduino Mega GND -------- HW-170 GND
Arduino Mega D20/SDA ---- HW-170 SDA
Arduino Mega D21/SCL ---- HW-170 SCL

Regulator 5V-6V + ------- HW-170 servo V+
Regulator GND ----------- HW-170 servo GND
Regulator GND ----------- Arduino Mega GND

Pan MG996R 3-pin plug --- HW-170 channel 0
Tilt MG996R 3-pin plug -- HW-170 channel 1
```

Match each servo plug to the HW-170 silkscreen:

- Servo red wire: `V+`
- Servo brown/black wire: `GND`
- Servo orange/yellow/white wire: PWM signal

Do not power MG996R servos from the Arduino Mega 5V pin. Use the regulator for servo power and connect all grounds together.

## Serial Commands

Python sends pan/tilt commands to the Arduino Mega over USB serial:

```text
PAN:180.0,TILT:90.0
STATUS
```

The Arduino replies with:

```text
PAN:180 TILT:90
```

The sketch uses model-space limits that match `main.py` and `configs/config.yaml`:

- `PAN`: `90..270`, with `180` centered.
- `TILT`: `80..150`, with `90` centered.

## Installation

1. Open and upload `hardware/arduino/pan_tilt_controller/pan_tilt_controller.ino` to the Arduino Mega.
2. Connect the Mega to the HW-170 with SDA, SCL, 5V logic, and GND.
3. Connect pan servo to HW-170 channel 0.
4. Connect tilt servo to HW-170 channel 1.
5. Power the HW-170 servo rail from the regulator.
6. Power the Arduino Mega from USB or a separate regulated source.
7. Set `pan_tilt.port` in `configs/config.yaml` for your OS, for example `/dev/ttyUSB0`, `/dev/tty.usbmodem*`, `/dev/tty.usbserial*`, or `COM3`.
8. Keep `pan_tilt.enabled: false` until manual serial testing succeeds.

## Testing

In Arduino IDE Serial Monitor at 9600 baud:

```text
PAN:180,TILT:90
PAN:170,TILT:90
PAN:190,TILT:90
PAN:180,TILT:80
PAN:180,TILT:100
STATUS
```

When the serial test works, run the Python app with `pan_tilt.enabled: true`. The Python app detects the target, estimates which detection is nearest, and sends updated `PAN`/`TILT` commands to center the target in the camera frame.

For camera-on-head tracking, place an object off-center in the camera view. The servos should move until the object approaches the center of the image. If either axis moves the object farther from center, flip the matching `pan_tilt.invert_pan` or `pan_tilt.invert_tilt` value.

## Integration Log

For the project report and presentation, record:

- Arduino Mega serial port.
- HW-170 channel assignments.
- Servo model and power source.
- Camera model and mounting position.
- Commands tested manually.
- Any missed commands, jitter, power issues, or calibration offsets.
