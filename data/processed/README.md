# Dataset Prep

Suggested workflow for training a custom YOLO model from videos in `data/raw`:

1. Extract sparse frames for annotation:

```bash
python scripts/extract_frames.py --sample-fps 1
```

2. Annotate the extracted JPGs in a tool such as CVAT or Roboflow.

3. Export labels in YOLO detection format and place them under:

```text
data/processed/yolo_dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

4. Use `configs/zombie_dataset.yaml` as the dataset config for YOLO training.

Notes:
- Split by video, not by random frame, to avoid leakage.
- Keep class ids stable: `0=human`, `1=zombie`.
- Start by labeling the extracted frames before sampling more densely.
