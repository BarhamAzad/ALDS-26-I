"""Evaluate the base YOLO26 model against the fine-tuned ALDS checkpoint."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(".ultralytics").resolve()))
os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib").resolve()))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml
from ultralytics import YOLO


DEFAULT_BASE_MODEL = "models/yolo26s.pt"
DEFAULT_FINE_TUNED_MODEL = (
    "runs/detect/runs/detect/yolo26s_human_zombie_finetune_afterlife/weights/best.pt"
)
DEFAULT_DATA_CONFIG = "configs/zombie_dataset.yaml"
DEFAULT_OUTPUT_DIR = "results/model_evaluation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare YOLO26 base and fine-tuned checkpoints on the ALDS dataset."
    )
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL, help="Path to the base YOLO model.")
    parser.add_argument(
        "--fine-model",
        default=DEFAULT_FINE_TUNED_MODEL,
        help="Path to the fine-tuned YOLO model.",
    )
    parser.add_argument("--data", default=DEFAULT_DATA_CONFIG, help="YOLO dataset YAML file.")
    parser.add_argument(
        "--split",
        default="val",
        choices=("train", "val", "test"),
        help="Dataset split to evaluate.",
    )
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory for metrics and plots.")
    parser.add_argument("--imgsz", type=int, default=640, help="Validation image size.")
    parser.add_argument("--batch", type=int, default=4, help="Validation batch size.")
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device passed to Ultralytics, for example 'cpu', '0', or 'mps'. Use 'auto' for default.",
    )
    parser.add_argument("--conf", type=float, default=0.001, help="Confidence threshold for validation.")
    parser.add_argument("--iou", type=float, default=0.7, help="IoU threshold for validation.")
    parser.add_argument(
        "--no-native-plots",
        action="store_true",
        help="Disable Ultralytics per-model plots and save only comparison plots.",
    )
    return parser.parse_args()


def require_file(path: str | Path, description: str) -> Path:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"{description} not found: {resolved}")
    return resolved


def load_class_names(data_config: Path) -> list[str]:
    with data_config.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    names = data.get("names", [])
    if isinstance(names, dict):
        return [str(names[index]) for index in sorted(names)]
    return [str(name) for name in names]


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if hasattr(value, "item"):
        value = value.item()
    try:
        if isinstance(value, (list, tuple, np.ndarray)):
            array = np.asarray(value, dtype=float)
            return float(array.mean()) if array.size else default
        return float(value)
    except (TypeError, ValueError):
        return default


def find_result_value(results_dict: dict[str, Any], candidates: tuple[str, ...]) -> float:
    normalized = {
        key.lower().replace(" ", "").replace("_", "").replace("-", ""): value
        for key, value in results_dict.items()
    }
    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "").replace("-", "")
        if key in normalized:
            return as_float(normalized[key])
    return 0.0


def extract_metrics(results: Any, model_label: str, run_dir: Path, class_names: list[str]) -> dict[str, Any]:
    box = getattr(results, "box", None)
    results_dict = getattr(results, "results_dict", {}) or {}

    precision = as_float(getattr(box, "mp", None))
    recall = as_float(getattr(box, "mr", None))
    map50 = as_float(getattr(box, "map50", None))
    map50_95 = as_float(getattr(box, "map", None))

    if not precision:
        precision = find_result_value(results_dict, ("metrics/precision(B)", "precision"))
    if not recall:
        recall = find_result_value(results_dict, ("metrics/recall(B)", "recall"))
    if not map50:
        map50 = find_result_value(results_dict, ("metrics/mAP50(B)", "map50"))
    if not map50_95:
        map50_95 = find_result_value(results_dict, ("metrics/mAP50-95(B)", "map50-95", "map"))

    f1 = (2.0 * precision * recall / (precision + recall)) if precision + recall else 0.0

    maps = getattr(box, "maps", None)
    per_class_map = {}
    if maps is not None:
        maps_array = np.asarray(maps, dtype=float).ravel()
        for index, class_name in enumerate(class_names):
            if index < len(maps_array):
                per_class_map[class_name] = float(maps_array[index])

    speed = {}
    for key, value in (getattr(results, "speed", {}) or {}).items():
        speed[str(key)] = as_float(value)

    return {
        "model": model_label,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "map50": map50,
        "map50_95": map50_95,
        "fitness": as_float(results_dict.get("fitness")),
        "speed_ms_per_image": speed,
        "per_class_map50_95": per_class_map,
        "ultralytics_run_dir": str(run_dir),
    }


def evaluate_model(
    model_path: Path,
    model_key: str,
    model_label: str,
    data_config: Path,
    output_dir: Path,
    args: argparse.Namespace,
    class_names: list[str],
) -> dict[str, Any]:
    run_dir = output_dir / f"{model_key}_ultralytics"
    model = YOLO(str(model_path))
    device = None if args.device.lower() == "auto" else args.device

    results = model.val(
        data=str(data_config),
        split=args.split,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        conf=args.conf,
        iou=args.iou,
        plots=not args.no_native_plots,
        project=str(output_dir),
        name=f"{model_key}_ultralytics",
        exist_ok=True,
        verbose=False,
    )

    return extract_metrics(results, model_label, run_dir, class_names)


def save_summary(metrics: list[dict[str, Any]], output_dir: Path) -> None:
    json_path = output_dir / "metrics_summary.json"
    csv_path = output_dir / "metrics_summary.csv"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    columns = ("model", "precision", "recall", "f1", "map50", "map50_95", "fitness", "ultralytics_run_dir")
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in metrics:
            writer.writerow({column: row.get(column, "") for column in columns})


def add_value_labels(ax: plt.Axes, bars: Any) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.3f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def plot_metric_bars(metrics: list[dict[str, Any]], output_dir: Path) -> None:
    metric_keys = ["precision", "recall", "f1", "map50", "map50_95"]
    metric_labels = ["Precision", "Recall", "F1", "mAP50", "mAP50-95"]
    model_labels = [entry["model"] for entry in metrics]

    x = np.arange(len(metric_keys))
    width = 0.8 / max(1, len(metrics))

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for index, entry in enumerate(metrics):
        offset = (index - (len(metrics) - 1) / 2) * width
        values = [entry[key] for key in metric_keys]
        bars = ax.bar(x + offset, values, width, label=model_labels[index])
        add_value_labels(ax, bars)

    ax.set_title("Base YOLO26 vs Fine-tuned YOLO26 Detection Metrics")
    ax.set_ylabel("Score")
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels)
    ax.set_ylim(0.0, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "metrics_comparison.png", dpi=200)
    plt.close(fig)


def plot_metric_delta(metrics: list[dict[str, Any]], output_dir: Path) -> None:
    if len(metrics) < 2:
        return

    metric_keys = ["precision", "recall", "f1", "map50", "map50_95"]
    metric_labels = ["Precision", "Recall", "F1", "mAP50", "mAP50-95"]
    base = metrics[0]
    fine = metrics[1]
    deltas = [fine[key] - base[key] for key in metric_keys]
    colors = ["#237a57" if value >= 0 else "#b23b3b" for value in deltas]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    bars = ax.bar(metric_labels, deltas, color=colors)
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_title(f"{fine['model']} minus {base['model']}")
    ax.set_ylabel("Score difference")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    add_value_labels(ax, bars)
    fig.tight_layout()
    fig.savefig(output_dir / "fine_tuned_metric_delta.png", dpi=200)
    plt.close(fig)


def plot_per_class_map(metrics: list[dict[str, Any]], output_dir: Path, class_names: list[str]) -> None:
    if not class_names:
        return
    if not any(entry["per_class_map50_95"] for entry in metrics):
        return

    x = np.arange(len(class_names))
    width = 0.8 / max(1, len(metrics))

    fig, ax = plt.subplots(figsize=(9, 5))
    for index, entry in enumerate(metrics):
        offset = (index - (len(metrics) - 1) / 2) * width
        values = [entry["per_class_map50_95"].get(class_name, 0.0) for class_name in class_names]
        bars = ax.bar(x + offset, values, width, label=entry["model"])
        add_value_labels(ax, bars)

    ax.set_title("Per-class mAP50-95")
    ax.set_ylabel("mAP50-95")
    ax.set_xticks(x)
    ax.set_xticklabels(class_names)
    ax.set_ylim(0.0, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "per_class_map50_95.png", dpi=200)
    plt.close(fig)


def plot_speed(metrics: list[dict[str, Any]], output_dir: Path) -> None:
    speed_keys = sorted({key for entry in metrics for key in entry["speed_ms_per_image"]})
    if not speed_keys:
        return

    x = np.arange(len(speed_keys))
    width = 0.8 / max(1, len(metrics))

    fig, ax = plt.subplots(figsize=(9, 5))
    for index, entry in enumerate(metrics):
        offset = (index - (len(metrics) - 1) / 2) * width
        values = [entry["speed_ms_per_image"].get(key, 0.0) for key in speed_keys]
        bars = ax.bar(x + offset, values, width, label=entry["model"])
        add_value_labels(ax, bars)

    ax.set_title("Validation Speed")
    ax.set_ylabel("Milliseconds per image")
    ax.set_xticks(x)
    ax.set_xticklabels([key.title() for key in speed_keys])
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "speed_comparison.png", dpi=200)
    plt.close(fig)


def save_plots(metrics: list[dict[str, Any]], output_dir: Path, class_names: list[str]) -> None:
    plot_metric_bars(metrics, output_dir)
    plot_metric_delta(metrics, output_dir)
    plot_per_class_map(metrics, output_dir, class_names)
    plot_speed(metrics, output_dir)


def main() -> int:
    args = parse_args()
    base_model = require_file(args.base_model, "Base model")
    fine_model = require_file(args.fine_model, "Fine-tuned model")
    data_config = require_file(args.data, "Dataset config")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    class_names = load_class_names(data_config)

    models = [
        (base_model, "base_model", "Base YOLO26s"),
        (fine_model, "fine_tuned_model", "Fine-tuned YOLO26s"),
    ]

    metrics = []
    for model_path, model_key, model_label in models:
        print(f"Evaluating {model_label}: {model_path}")
        metrics.append(
            evaluate_model(
                model_path=model_path,
                model_key=model_key,
                model_label=model_label,
                data_config=data_config,
                output_dir=output_dir,
                args=args,
                class_names=class_names,
            )
        )

    save_summary(metrics, output_dir)
    save_plots(metrics, output_dir, class_names)

    print(f"\nSaved evaluation artifacts to {output_dir}")
    for entry in metrics:
        print(
            f"{entry['model']}: "
            f"P={entry['precision']:.3f}, "
            f"R={entry['recall']:.3f}, "
            f"F1={entry['f1']:.3f}, "
            f"mAP50={entry['map50']:.3f}, "
            f"mAP50-95={entry['map50_95']:.3f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
