# Autonomous Laser Defense System (ALDS-26-I)

Real-time human/zombie classification, monocular depth estimation, and automated laser targeting system integrating computer vision with embedded hardware.


## Solution Components

1. **Detection**: YOLOv8 for human/zombie classification
2. **Depth Estimation**: Depth Anything V2 for distance measurement
3. **Hardware**: Arduino servo control paired with mechanical platform
4. **Integration**: Real-time targeting pipeline 

## Project Structure

```
ALDS-26-I/
├── src/                      # Core Python modules
│   ├── detection/            # YOLOv8 detector
│   ├── depth_estimation/     # Depth Anything V2
│   ├── laser_control/        # Hardware control
│   └── utils/                # Config & video I/O
├── hardware/
│   ├── arduino/              # Servo & fire control firmware
│   └── 3d_printing/          # 3D models & print guides
├── data/                     # Training & test data
├── models/                   # Pretrained checkpoints
├── configs/config.yaml       # System settings
└── main.py                   # Entry point
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
Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the system
python main.py --config configs/config.yaml
```

## Documentation
- **[Hardware Integration](HARDWARE_INTEGRATION.md)** - Arduino + mechanical assembly
- **[Arduino Setup](hardware/arduino/README.md)** - Firmware and wiring
- **[Mechanical Design](hardware/mechanical/README.md)** - Platform specifications
- **[3D Printing](hardware/3d_printing/README.md)** - Print settings and files

## Media Engagment
### Social Media Channels:
- [Instagram](https://www.instagram.com/alds_26_i/)


## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
Key Technologies
