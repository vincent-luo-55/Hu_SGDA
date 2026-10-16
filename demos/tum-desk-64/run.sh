#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "用法：$0 /path/to/SGAD-SLAM /path/to/output" >&2
  exit 2
fi
source_dir=$(realpath "$1")
output_dir=$(realpath -m "$2")
dataset_dir="$source_dir/dataset/TUM/rgbd_dataset_freiburg1_desk_first80"
if [[ ! -f "$dataset_dir/rgb.txt" ]]; then
  echo "请先运行 scripts/make_tum_subset.py 创建前 80 条记录的小数据集。" >&2
  exit 1
fi
if [[ -e "$output_dir" ]]; then
  echo "输出路径已存在，请指定一个新路径：$output_dir" >&2
  exit 1
fi
mkdir -p "$output_dir"
cat > "$output_dir/map_config.yaml" <<EOF
inherit_from: configs_map/TUM_RGBD/rgbd_dataset_freiburg1_desk.yaml
data:
  input_path: $dataset_dir
  output_path: $output_dir
  scene_name: rgbd_dataset_freiburg1_desk_first80
EOF
cd "$source_dir"
CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0} PYTHONUNBUFFERED=1 python -W ignore slam.py \
  --dataset_path "$dataset_dir" \
  --config configs/TUM/rgbd_dataset_freiburg1_desk.txt \
  --output_path "$output_dir" \
  --keyframe_th 0.81 --knn_maxd 99999.0 --overlapped_th 1e-3 \
  --max_correspondence_distance 0.03 --trackable_opacity_th 0.09 \
  --overlapped_th2 1e-3 --downsample_rate 5 --save_results \
  --k_choice 10 --knn_cov 23 --keyframe_freq_tracking 8 \
  --depth_trunc 3.0 --init_rate 1.0 \
  --config_map_path "$output_dir/map_config.yaml" \
  2>&1 | tee "$output_dir/run.log"
