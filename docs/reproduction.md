# TUM fr1/desk 复现步骤

## 范围、机器与来源

- 作者源码：[MachinePerceptionLab/SGAD-SLAM](https://github.com/MachinePerceptionLab/SGAD-SLAM)，实验基于 commit `2dca26dcef242edf07c3c361be390d3ca254aa43`。
- 论文：[SGAD-SLAM，CVPR 2026](https://arxiv.org/html/2603.21055v1)。
- 数据：官方 TUM RGB-D `rgbd_dataset_freiburg1_desk.tgz`，SHA256 `e983d6830916e66dc4a46a71368046b149b283de87769690e7aa4e0b9483530c`；RGB、深度和真值位姿关联后为 592 帧。请按作者 README 准备到 `dataset/TUM/rgbd_dataset_freiburg1_desk`。
- 本机：RTX 5060 Laptop GPU（8 GB 显存）、约 14 GiB 系统内存、Conda 环境 `paper_a`、Python 3.10、PyTorch 2.11 / CUDA 12.8。作者 README 的测试环境与之不同，因此这里的构建调整是本机兼容性工作。

## 使用本仓库材料

下列命令均从**作者源码仓库根目录**运行。本仓库不是作者源码的替代品。

```bash
git checkout 2dca26dcef242edf07c3c361be390d3ca254aa43
git apply /path/to/Hu_SGDA/patches/runtime_compat.patch
cp /path/to/Hu_SGDA/configs/tum_fr1_desk_kfreq8.yaml configs_map/TUM_RGBD/rgbd_dataset_freiburg1_desk_kfreq8.yaml
```

补丁做三类事：将 `SharedTargetPoints` 的十亿点固定预分配改成按帧数上界分配；让部分 C++/CUDA 扩展在本机依赖版本下编译；渲染评测先在 CPU 读取保存的子地图，再把参数移动到 GPU。补丁不更改 SGAD-SLAM 的跟踪或沿射线调整深度的目标函数。扩展的安装方法仍按作者仓库 README；`scripts/check_environment.py` 与 `scripts/smoke_gpu.py` 可作为额外验证。

本仓库的 `scripts/tracking_recheck.py` 是跟踪诊断辅助脚本。若要单独重跑跟踪，先把它复制到作者仓库根目录，再设置 `SGAD_KEYFRAME_FREQ=16` 或 `8` 运行；该脚本不做建图。`scripts/make_results_preview.py` 则接受完整结果目录作为参数，从已保存的真实渲染帧生成对比图和抽帧 MP4。

原始参数来自作者的 `scripts/tum.sh`，具体数值如下。该脚本中的 `CUDA_VISIBLE_DEVICES=1` 适合多 GPU 环境；本机只有一块 GPU，运行时设为 `0`。

```bash
CUDA_VISIBLE_DEVICES=0 python -W ignore slam.py \
  --dataset_path dataset/TUM/rgbd_dataset_freiburg1_desk \
  --config configs/TUM/rgbd_dataset_freiburg1_desk.txt \
  --output_path experiments/results/rgbd_dataset_freiburg1_desk \
  --keyframe_th 0.81 --knn_maxd 99999.0 --overlapped_th 1e-3 \
  --max_correspondence_distance 0.03 --trackable_opacity_th 0.09 \
  --overlapped_th2 1e-3 --downsample_rate 5 --save_results \
  --k_choice 10 --knn_cov 23 --keyframe_freq_tracking 16 \
  --depth_trunc 3.0 --init_rate 1.0 \
  --config_map_path configs_map/TUM_RGBD/rgbd_dataset_freiburg1_desk.yaml
```

诊断运行只改以下三处，其他参数相同：

```text
--keyframe_freq_tracking 8
--output_path experiments/results/rgbd_dataset_freiburg1_desk_kfreq8
--config_map_path configs_map/TUM_RGBD/rgbd_dataset_freiburg1_desk_kfreq8.yaml
```

两处输出路径分别供跟踪端和建图端使用，实验中保持其目标目录一致。仓库的 YAML 继承原始 TUM 场景配置，仅覆盖建图端的 `data.output_path`。先导测试使用原始序列前 80 条 RGB/深度记录构造的小子集，关联后为 64 帧；它仅用于确认管线可运行，不作为论文数值比较。

## 实际运行与结果

1. 验证 Python、GPU、GICP、FAISS 和自定义 CUDA 扩展。
2. 完成 64 帧先导测试。
3. 按作者 TUM 参数跑完 592 帧。其 PSNR 为 39.2111，但轨迹在约第 192 帧之后明显偏离，程序显示的 ATE 为 50.13 cm。
4. 单独重复跟踪，确认间隔 16 的漂移可复现；改为间隔 8 后程序显示的 ATE 降为约 2.88 cm。
5. 用间隔 8 再跑完跟踪和逐帧建图。主流程生成全部 592 个子地图。自动渲染评测偶发 `torch.load` EOF；逐个 CPU 读取表明文件均可读。采用补丁中的 CPU 读取方式补跑评测，592 帧全部完成。
6. 保存指标 JSON、轨迹图、三帧原图/渲染/误差对比图及 119 帧渲染抽样视频。

原始指标：[默认参数 JSON](../results/tum_fr1_desk/rendering_metrics_default.json)；诊断指标：[间隔 8 JSON](../results/tum_fr1_desk/rendering_metrics_kfreq8.json)。ATE 来自保存轨迹与 TUM 真值经过刚体对齐的误差。作者 `src/evaluation/evaluate_trajectory.py` 把误差平均值打印为 `ATE-RMSE`；本仓库 README 另列真正的均方根，避免混淆。

渲染评测在已输入的 592 个视角进行；本次配置 `map_every: 1`、`new_submap_every: 1`，检查点每个子地图对应一帧。因此渲染分数相近并不代表两组运行的全局轨迹同样准确。作者默认评测入口没有启用重建评测，本次不报告论文的 F1/网格重建指标，也不声称完成论文全部数据集或五次重复平均。

本机还保留约 16 GB/场景的完整检查点、逐帧图片与日志；这些文件体积大，不适合直接放入普通 Git 仓库。
