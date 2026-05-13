# 3D Printing Guide

## STL Files Location

All committed STL files for 3D printing are in `stl_files/`.
At the moment, this repo includes `frame_base.stl`. The README below keeps the larger intended bill of materials for future expansion, but only files present in the repo should be treated as available.

## Recommended Print Settings

### Material: PETG (Recommended)
- **Nozzle Temperature**: 210-230°C
- **Bed Temperature**: 60-80°C
- **Layer Height**: 0.2mm
- **Infill**: 15-20% (gyroid pattern)
- **Wall Thickness**: 2.4mm (3 perimeters @ 0.8mm nozzle)
- **Print Speed**: 40-50 mm/s
- **Support**: Tree supports where needed

### Alternative: PLA
- **Nozzle Temperature**: 190-210°C
- **Bed Temperature**: 50-60°C
- **Layer Height**: 0.1-0.2mm
- **Print Speed**: 50-60 mm/s
- **Note**: Less durable than PETG, good for prototypes

### Alternative: ASA
- **Nozzle Temperature**: 230-250°C
- **Bed Temperature**: 100-110°C
- **Layer Height**: 0.2mm
- **Print Speed**: 40-50 mm/s
- **Note**: Better UV resistance and durability

## Parts to Print

### Required Parts
| File | Quantity | Weight | Est. Time | Cost* |
|------|----------|--------|-----------|-------|
| `frame_base.stl` | 1 | ~40g | 2-3h | $1-2 |
| `pan_platform.stl` | planned | ~30g | 1.5-2h | $1 |
| `tilt_arm.stl` | planned | ~25g | 1.5h | $0.75 |
| `camera_bracket.stl` | planned | ~15g | 1h | $0.50 |
| `laser_mount.stl` | planned | ~10g | 0.5-1h | $0.50 |

**Total: ~120g, 6-8.5 hours, $4-5 per set*

*Costs vary by material and service (at $0.05/g PETG)

## Print Order & Dependencies

1. **First**: `frame_base.stl` (foundation)
2. **Second**: `pan_platform.stl` (mounts to frame_base)
3. **Third**: `tilt_arm.stl` (mounts to pan_platform)
4. **Fourth**: `camera_bracket.stl` & `laser_mount.stl` (mounts to tilt_arm)

## Printing Tips

### Orientation for Optimal Prints
- **frame_base**: Flat on bed (largest face down)
- **pan_platform**: Flat on bed to minimize supports
- **tilt_arm**: Long axis parallel to bed
- **camera_bracket**: Standard orientation
- **laser_mount**: Minimal supports needed

### Post-Processing
1. **Support Removal**: Use flush cutters for clean removal
2. **Smoothing**: Sand rough edges with 120→220 grit
3. **Cleaning**: Remove print bed residue with isopropyl alcohol
4. **Assembly**: Test fit parts before final assembly

## Software Tools

### Free Slicing Software
- **Cura** (Ultimaker) - User-friendly, good presets
- **PrusaSlicer** - Advanced options, quality output
- **SuperSlicer** - Enhanced PrusaSlicer fork

### CAD Software (if modifying designs)
- **FreeCAD** - Free, parametric design
- **Fusion 360** - Free for students, commercial option
- **OpenSCAD** - Parametric, scripting-based

## Slicing Profiles

No slicing profiles are committed yet. Add your own slicer profile locally for your printer and material.

## Quality Checklist

- [ ] All parts printed in PETG or better
- [ ] No critical failures (layer shifts, nozzle clogs)
- [ ] Infill >= 15% for structural integrity
- [ ] Support properly removed without damage
- [ ] Parts fit together without force
- [ ] Servo mounts aligned properly
- [ ] Camera bracket level and secure
- [ ] Laser mount aligned with camera

## Troubleshooting

### Warping/Curling
- Increase bed temperature
- Use adhesion aids (glue stick, PEI sheet)
- Check bed leveling

### Stringing
- Reduce retraction distance
- Lower nozzle temperature slightly
- Disable retraction for short moves

### Poor Layer Adhesion
- Clean nozzle thoroughly
- Re-level bed
- Increase bed temperature

### Parts Don't Fit
- Check scale in slicer (should be 100%)
- Sand mating surfaces
- Verify original dimensions correct

## Assembly After Printing

See `../mechanical/README.md` for assembly notes and calibration guidance.

## Project Documentation Notes

- Photograph the printed base and final mount if used in the demo.
- Record material, infill, layer height, and any print failures.
- Note whether the final demo used the printed part, a temporary mount, or a benchtop test fixture.

## Estimated Project Cost

| Item | Est. Cost |
|------|-----------|
| 3D Printing (120g PETG) | $4-5 |
| Arduino Uno | $10 |
| Servos (2x MG90S) | $10 |
| Laser Module | $5 |
| Relay Module | $3 |
| Camera (USB) | $10-20 |
| **Total** | **$42-53** |

*Prices vary by supplier and region*
