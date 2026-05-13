# Mechanical Guide

This guide covers the current physical assumptions used by the software and firmware in this repo.

## Intended Assembly

- Mount the pan servo to the base.
- Mount the tilt stage on the pan servo horn.
- Mount the camera and laser so they move together on the tilt stage.
- Keep the camera and laser as close together as practical to reduce parallax.

## Centering Procedure

1. Upload `hardware/arduino/laser_controller.ino` to the Arduino.
2. Open a serial monitor at `9600` baud.
3. Send `PAN:90,TILT:90`.
4. Physically align the platform so this command points near the visual center of the camera frame.
5. Tighten the servo horns and brackets.

## Calibration Notes

- The Python side assumes the left edge of the image maps toward lower pan angles.
- The Python side assumes the top edge of the image maps toward lower tilt angles.
- If your mechanism is reversed on either axis, swap the linkage mechanically or invert the mapping in `LaserController.target_bbox` in `main.py`.
- Fine aiming should be done with hardware disabled first.
- Record the camera resolution, servo center position, and any mechanical offsets used during the final demo.

## Demo Procedure

1. Run software-only detection with `laser.enabled: false`.
2. Center the servos with `PAN:90,TILT:90`.
3. Enable hardware with `laser.enabled: true` and `laser.auto_fire: false`.
4. Verify pan/tilt tracking with a safe indicator instead of an active laser.
5. Capture calibration notes and any alignment error for the final report.

## Safety

- Keep `laser.enabled: false` until servo motion and serial communication are confirmed.
- Keep `laser.auto_fire: false` while validating pan/tilt alignment.
- Test with the laser disconnected or replaced by a harmless indicator LED first.
- Do not energize the relay output until the mechanism has been dry-run successfully.
