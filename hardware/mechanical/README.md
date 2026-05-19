# Mechanical Guide

This guide covers the current physical assumptions used by the software and firmware in this repo.

## Intended Assembly

- Mount the pan servo to the base.
- Mount the tilt stage on the pan servo horn.
- Mount the camera so it moves with the tilt stage.
- Keep wiring loose enough that it cannot pull the head off target at the motion limits.

## Centering Procedure

1. Upload `hardware/arduino/pan_tilt_controller/pan_tilt_controller.ino` to the Arduino Mega.
2. Open a serial monitor at `9600` baud.
3. Send `PAN:180,TILT:90`.
4. Physically align the platform so this command points near the visual center of the camera frame.
5. Tighten the servo horns and brackets.

## Calibration Notes

- The Arduino sketch accepts pan values from `90..270`, with `180` centered.
- The Arduino sketch accepts tilt values from `80..150`, with `90` centered.
- If your mechanism moves away from the target on either axis, flip `pan_tilt.invert_pan` or `pan_tilt.invert_tilt` in the config.
- Fine aiming should be done with hardware disabled first.
- Record the camera resolution, servo center position, and any mechanical offsets used during the final demo.

## Demo Procedure

1. Run software-only detection with `pan_tilt.enabled: false`.
2. Center the servos with `PAN:180,TILT:90`.
3. Enable hardware with `pan_tilt.enabled: true`.
4. Verify pan/tilt tracking with a target placed off-center in the camera view.
5. Capture calibration notes and any alignment error for the final report.

## Safety

- Keep `pan_tilt.enabled: false` until servo motion and serial communication are confirmed.
- Start with low gains and small test movements.
- Power the servos from the external regulator, not from the Arduino Mega 5V pin.
- Keep hands clear of the pan/tilt linkage during hardware tests.
