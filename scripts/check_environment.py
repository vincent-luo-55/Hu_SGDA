"""Run with paper_a's Python on the host, not inside a GPU-hidden sandbox."""
import importlib
import json
import shutil
import subprocess
import sys

report = {"python": sys.version, "executable": sys.executable, "modules": {}}
for name in ["torch", "numpy", "cv2", "open3d", "scipy", "roma", "einops", "evo",
             "pytorch_msssim", "torchmetrics", "wandb", "rerun", "faiss", "pygicp",
             "simple_knn._C", "gaussian_rasterizer", "evaluate_3d_reconstruction"]:
    try:
        mod = importlib.import_module(name)
        report["modules"][name] = {"ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:
        report["modules"][name] = {"ok": False, "error": str(exc)}
try:
    import torch
    report["cuda"] = {"available": torch.cuda.is_available(), "torch_cuda": torch.version.cuda}
    if torch.cuda.is_available():
        x = torch.randn(64, 64, device="cuda")
        y = x @ x.T
        torch.cuda.synchronize()
        report["cuda"].update(device=torch.cuda.get_device_name(),
                              capability=torch.cuda.get_device_capability(),
                              matmul_ok=bool(torch.isfinite(y).all()))
except Exception as exc:
    report["cuda_error"] = str(exc)
report["nvcc"] = shutil.which("nvcc")
result = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
report["pip_check"] = {"code": result.returncode, "output": result.stdout.strip()}
print(json.dumps(report, indent=2, ensure_ascii=False))
