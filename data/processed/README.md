# Dataset Prep

Suggested workflow for training a custom YOLO model from videos in `data/raw`:

## Data Sources

Document each raw source before training:

| Source | Type | License/permission | Intended split | Notes |
|--------|------|--------------------|----------------|-------|
| `data/raw/*.mp4` | Video | Local project data | Train/val/test by source video | Confirm permission before sharing |
| `data/raw/*.{jpg,png}` | Image | Local project data | Train/val/test by source image group | Keep labels consistent |

1. Extract sparse frames for annotation:

```bash
python scripts/extract_frames.py --sample-fps 1
```

By default, frames are written under `data/processed/frames/<video-name>/`.

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

Example training command:

```bash
yolo detect train model=models/yolo26s.pt data=configs/zombie_dataset.yaml epochs=50 imgsz=640 project=runs/detect name=yolo26s_human_zombie
```

Notes:
- Split by video, not by random frame, to avoid leakage.
- Keep class ids stable: `0=human`, `1=zombie`.
- Start by labeling the extracted frames before sampling more densely.
- Training outputs are generated under `runs/`, which is ignored by Git.
- Point `detection.model` in `configs/config.yaml` at the desired `weights/best.pt` checkpoint after training.

## Evaluation Checklist

- Run YOLO validation on the held-out test split.
- Save precision, recall, F1, mAP50, and confusion matrix artifacts from the selected run.
- Inspect false positives and false negatives manually.
- Record whether failures are caused by labels, lighting, blur, occlusion, class ambiguity, or model limits.
- Keep enough notes that another team member can reproduce the chosen result.
