"""Repeat the unmodified GICP tracking path without mapping for diagnosis."""
from types import SimpleNamespace
import os
import torch.multiprocessing as mp
import slam
from src.utils.utils import setup_seed

if __name__ == '__main__':
    slam.with_mapper = False
    setup_seed(0)
    args = SimpleNamespace(
        dataset_path='dataset/TUM/rgbd_dataset_freiburg1_desk',
        config='configs/TUM/rgbd_dataset_freiburg1_desk.txt',
        output_path=os.environ.get('SGAD_OUTPUT_PATH', 'experiments/results/tracking_recheck'),
        keyframe_th=0.81, knn_maxd=99999.0, overlapped_th=1e-3,
        max_correspondence_distance=0.03, trackable_opacity_th=0.09,
        overlapped_th2=1e-3, downsample_rate=5, k_choice=10, knn_cov=23,
        keyframe_freq_tracking=int(os.environ.get('SGAD_KEYFRAME_FREQ', '16')), depth_trunc=3.0, init_rate=1.0,
        verbose=False, demo=False, test=None, save_results=True,
        config_map_path='configs_map/TUM_RGBD/rgbd_dataset_freiburg1_desk.yaml')
    system = slam.SGAD_SLAM(args)
    processes = [mp.Process(target=system.tracking, args=(0,)),
                 mp.Process(target=system.tracking_scene, args=(1,))]
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    codes = [process.exitcode for process in processes]
    print('tracking process exit codes:', codes, flush=True)
    if any(code != 0 for code in codes):
        raise SystemExit(1)
