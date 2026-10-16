"""Build a visual audit of real SGAD-SLAM output (no generated frames)."""
from pathlib import Path
import argparse
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("result_dir", type=Path)
parser.add_argument("--frames", nargs="+", type=int, default=[40, 300, 500])
args = parser.parse_args()
root = args.result_dir

fig, axes = plt.subplots(len(args.frames), 3, figsize=(12, 3.4 * len(args.frames)))
if len(args.frames) == 1:
    axes = axes[None, :]
for row, frame_id in enumerate(args.frames):
    name = f"{frame_id:04d}.png"
    pair = [root / "gt_rgb" / f"gt_{name}", root / "rendered_rgb" / f"gs_{name}"]
    if not all(p.exists() for p in pair):
        raise FileNotFoundError(pair)
    gt, rendered = (cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB) for p in pair)
    diff = cv2.absdiff(gt, rendered)
    for col, (img, label) in enumerate(zip((gt, rendered, diff), ("Ground truth", "SGAD-SLAM render", "Absolute RGB difference"))):
        axes[row, col].imshow(img)
        axes[row, col].set_title(f"Frame {frame_id}: {label}")
        axes[row, col].axis("off")
fig.tight_layout()
output = root / "comparison_preview.png"
fig.savefig(output, dpi=150)
print(output)

frames = sorted((root / "rendered_rgb").glob("gs_*.png"))
if frames:
    first = cv2.imread(str(frames[0]))
    h, w = first.shape[:2]
    video_path = root / "rendered_sample.mp4"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (w, h))
    if not writer.isOpened():
        raise RuntimeError("Could not open MP4 writer")
    for frame in frames:
        writer.write(cv2.imread(str(frame)))
    writer.release()
    print(video_path, "sampled frames:", len(frames))
