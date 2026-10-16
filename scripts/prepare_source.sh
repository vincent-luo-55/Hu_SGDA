#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir=${1:-"$repo_root/SGAD-SLAM"}
upstream=https://github.com/MachinePerceptionLab/SGAD-SLAM.git
revision=2dca26dcef242edf07c3c361be390d3ca254aa43

if [[ ! -d "$source_dir/.git" ]]; then
  if [[ -e "$source_dir" ]]; then
    echo "目标路径已存在且不是 Git 仓库：$source_dir" >&2
    exit 1
  fi
  git clone "$upstream" "$source_dir"
fi

if [[ -n "$(git -C "$source_dir" status --porcelain)" ]]; then
  echo "作者源码目录有未提交改动，请先检查：$source_dir" >&2
  exit 1
fi
git -C "$source_dir" checkout "$revision"
git -C "$source_dir" apply --check "$repo_root/patches/runtime_compat.patch"
git -C "$source_dir" apply "$repo_root/patches/runtime_compat.patch"
cp "$repo_root/configs/tum_fr1_desk_kfreq8.yaml" \
  "$source_dir/configs_map/TUM_RGBD/rgbd_dataset_freiburg1_desk_kfreq8.yaml"
echo "源码已准备：$source_dir"
echo "接下来按作者 README 安装依赖和 CUDA 扩展，并准备 TUM 数据。"
