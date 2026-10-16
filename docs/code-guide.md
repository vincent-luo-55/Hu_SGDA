# 从一帧数据理解论文与代码

阅读顺序：作者仓库的 `scripts/tum.sh` → `slam.py` → `mp_Tracker.py`、`mp_Tracker_scene.py` → `mp_Mapper.py`、`src/entities/mapper.py` → `src/evaluation/evaluator.py`。

| 论文概念 | 通俗解释 | 作者代码位置 |
| --- | --- | --- |
| RGB-D 输入与相机内参 | 彩色图、每像素深度，以及像素到三维空间的换算参数 | `configs/TUM/*.txt`、`configs_map/TUM_RGBD/*.yaml`、`utils/traj_utils.py` |
| Tracking（第 3.3 节） | 用当前深度点与累计场景几何进行 GICP 对齐，得到相机位姿 | `mp_Tracker.py`；`mp_Tracker_scene.py` 更新目标几何 |
| Mapping（第 3.2 节） | 根据图像、深度和位姿创建高斯，渲染并优化 | `mp_Mapper.py` 调度；`src/entities/mapper.py` 初始化与优化 |
| Adjusted Depth（第 3.2 节） | 让高斯沿对应像素的视线前后移动 | `src/entities/mapper.py` 的 `factor_opt` 和 `_xyz` 更新 |
| Evaluation（第 4.2 节） | 用真值轨迹评价位姿，用原图评价渲染 | `src/evaluation/evaluate_trajectory.py`、`src/evaluation/evaluator.py` |

论文把沿射线移动写成深度偏移。实现中先固定高斯的初始点 `X` 和相机中心 `C`，学习一个初始为 1 的因子 `f`，更新位置为 `C + f(X-C)`。当 `f` 增大，点离相机更远；减小则更近。随后渲染当前帧的 RGB 和深度，并用颜色 L1、SSIM、深度 L1 的损失优化参数。

“跟踪高斯”和“渲染高斯”承担不同任务：前者帮助求相机位姿，后者帮助生成图像。改 `--keyframe_freq_tracking` 改的是前者更新频率，不会直接改变高斯深度偏移的损失公式。

需要区分论文描述与当前代码启用的分支。论文第 3.2 节描述邻近视角约束；这次运行的 `src/entities/mapper.py` 设置 `mapping_one_frame_gs = True`，调用 `optimize_submap([(frame_id, keyframe)], ...)`，即当前帧优化。TUM 配置还设置每帧新建一个子地图。理解这些实际分支，才能正确解释为何轨迹误差变化很大而输入视角的 PSNR 几乎不变。
