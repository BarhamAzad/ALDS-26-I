# Mechanical Design - Zombie Laser Targeting System

## Assembly Overview

This is a pan-tilt laser targeting platform capable of tracking and aiming at objects.

## Components

### Frame
- **Material**: Aluminum extrusion or 3D-printed PLA/PETG
- **Dimensions**: ~200x200x150 mm (adjustable based on your design)
- **Purpose**: Sturdy base to mount servos and camera

### Pan Assembly (Horizontal)
- **Servo**: MG90S or better (higher torque)
- **Mount**: Servo bracket on base, rotating platform on top
- **Rotation**: 180° (0-180°)
- **Load**: Camera + depth sensor + laser module (~200g)

### Tilt Assembly (Vertical)
- **Servo**: MG90S (mounted on pan platform)
- **Mount**: Servo bracket, rotating arm pointing upward
- **Rotation**: 180° (0-180°)
- **Load**: Laser module + sighting mechanism (~50g)

### Camera Mount
- **Position**: Top of pan assembly
- **Purpose**: Track targets for detection
- **Sensors**: USB camera + depth sensor (Intel RealSense or similar)

### Laser Mount
- **Position**: Aligned with camera optical axis
- **Type**: 5V laser diode module or laser pointer
- **Alignment**: Must be calibrated to camera FOV

### Mechanical Specifications

| Feature | Spec |
|---------|------|
| Pan Range | 0-180° |
| Tilt Range | 0-180° |
| Pan Speed | ~60°/sec |
| Tilt Speed | ~60°/sec |
| Max Load | ~300g |
| Positioning Accuracy | ±2-3° |

## CAD Files

Place your CAD files here:
- `frame_base.step` or `.stl`
- `pan_platform.step` or `.stl`
- `tilt_arm.step` or `.stl`
- `camera_bracket.step` or `.stl`
- `laser_mount.step` or `.stl`

## Assembly Steps

1. **Prepare Base Frame**: Assemble aluminum extrusion or 3D print frame parts
2. **Mount Pan Servo**: Attach to base with rotating platform
3. **Mount Tilt Servo**: Attach to pan platform
4. **Attach Tilt Arm**: Connect to tilt servo
5. **Mount Camera**: Secure camera with bracket on tilt arm
6. **Mount Laser**: Align and secure laser module
7. **Cable Management**: Route servo cables to Arduino connections
8. **Calibration**: Ensure laser is aligned with camera view

## Calibration Procedure

1. Position platform to center (Pan: 90°, Tilt: 90°)
2. Mark camera's center of view
3. Adjust laser mount so beam hits the mark
4. Verify alignment at multiple angles
5. Fine-tune servo trim values in Arduino code if needed

## Material Recommendations

### For 3D Printing
- **Material**: PETG or ASA (better durability than PLA)
- **Infill**: 15-20%
- **Wall Thickness**: 2.4mm minimum
- **Support**: Where needed for arms

### For Aluminum Frame
- **Profile**: 2020 or 2040 aluminum extrusion
- **Fasteners**: M4 or M5 hex bolts
- **Brackets**: Standard aluminum servo brackets

## Power Considerations

- **Total Power**: ~2A @ 5V worst case
- **Supply**: 2A 5V USB power adapter or regulated DC supply
- **Capacitor**: 100µF@5V near servo power for stability

## Future Improvements

- Add limit switches for safety
- Increase servo torque for heavier loads
- Add air filter/cooling for continuous operation
- Implement feedback position sensing
- Add protective housing/casing
