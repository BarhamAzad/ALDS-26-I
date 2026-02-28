# Zombie Laser Targeting System

Computer Vision project that detects humans and zombies using YOLOv8, estimates depth with Depth Anything V2, and controls a laser pointer to target only zombies (excluding humans).

## Features

- **Object Detection**: YOLOv8 for human and zombie classification
- **Depth Estimation**: Depth Anything V2 for distance measurement
- **Laser Targeting**: Automatic laser pointer control to target closest zombie
- **Arduino Integration**: Pan-tilt servo and fire control via serial
- **Mechanical Platform**: Modular aluminum/3D-printed design
- **Real-time Processing**: Live video stream processing with OpenCV

## Structure

```
.
├── src/                          # Python source code
│   ├── detection/
│   │   └── detector.py          # YOLOv8 object detection
│   ├── depth_estimation/
│   │   └── depth_estimator.py   # Depth Anything V2
│   ├── laser_control/
│   │   └── laser_controller.py  # Arduino laser control
│   └── utils/
│       ├── config_loader.py     # Configuration handling
│       └── video_handler.py     # Video I/O
├── hardware/                     # Hardware control & design
│   ├── arduino/
│   │   ├── laser_controller.ino # Arduino firmware
│   │   └── README.md            # Arduino setup guide
│   ├── mechanical/
│   │   ├── README.md            # Mechanical design specs
│   │   └── models/              # CAD files (STEP/STL)
│   └── 3d_printing/
│       ├── README.md            # 3D printing guide & settings
│       ├── stl_files/           # STL files for printing
│       └── slicing_profiles/    # Slicer configurations
├── models/                       # Pretrained ML models
├── data/
│   ├── raw/                     # Raw video/image data
│   └── processed/               # Processed annotations
├── configs/
│   └── config.yaml              # System configuration
├── results/                      # Detection outputs
├── main.py                       # Entry point
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Installation

1. Clone/Navigate to the project directory:
```bash
cd ALDS-26-I
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the zombie detection system:
```bash
python main.py --config configs/config.yaml
```

## Hardware Setup

### Arduino Controller
See [hardware/arduino/README.md](hardware/arduino/README.md) for detailed setup:
- Pan/tilt servo control
- Laser firing mechanism
- Serial communication (9600 baud)

### Mechanical Assembly
See [hardware/mechanical/README.md](hardware/mechanical/README.md) for:
- Pan-tilt platform specifications
- Component mounting guide
- CAD file locations
- Calibration procedure

### 3D Printing
See [hardware/3d_printing/README.md](hardware/3d_printing/README.md) for:
- Print settings (PETG, PLA, ASA)
- Part list and estimated print times
- Slicing profiles for common printers
- Post-processing and assembly guide

## Configuration

Edit `configs/config.yaml` to adjust:
- Model paths and confidence thresholds
- Laser control serial port
- Video source (webcam index or file path)
- Output settings (save video, draw detection boxes)

## Dependencies

- **Ultralytics YOLOv8**: Real-time object detection
- **Depth Anything V2**: Monocular depth estimation
- **OpenCV**: Image processing and video handling
- **PyTorch**: Deep learning framework

## Authors

Ahmed Fatah Majeed 
Barham Azad Tawfeeq
Las Azad Taha 

## License

MIT
