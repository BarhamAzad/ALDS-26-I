"""Extract annotation-ready frames from raw videos."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2


VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}


def iter_videos(input_dir: Path) -> list[Path]:
    return sorted(path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS)


def extract_video_frames(video_path: Path, output_dir: Path, sample_fps: float) -> int:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if video_fps <= 0:
        video_fps = 24.0

    output_dir.mkdir(parents=True, exist_ok=True)

    step = max(int(round(video_fps / sample_fps)), 1)
    written = 0
    frame_idx = 0
    digits = max(6, len(str(frame_count)))

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_idx % step == 0:
            out_name = f"{video_path.stem}_frame_{frame_idx:0{digits}d}.jpg"
            cv2.imwrite(str(output_dir / out_name), frame)
            written += 1

        frame_idx += 1

    cap.release()
    return written


def main():
    parser = argparse.ArgumentParser(description="Extract frames from videos for YOLO annotation")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"), help="Directory containing raw videos")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/frames"),
        help="Directory where extracted frames will be saved",
    )
    parser.add_argument("--sample-fps", type=float, default=1.0, help="How many frames per second to keep")
    args = parser.parse_args()

    videos = iter_videos(args.input_dir)
    if not videos:
        raise SystemExit(f"No videos found in {args.input_dir}")

    total_written = 0
    for video in videos:
        video_output_dir = args.output_dir / video.stem
        written = extract_video_frames(video, video_output_dir, args.sample_fps)
        total_written += written
        print(f"{video.name}: wrote {written} frames to {video_output_dir}")

    print(f"Done. Wrote {total_written} frames from {len(videos)} videos.")


if __name__ == "__main__":
    main()
