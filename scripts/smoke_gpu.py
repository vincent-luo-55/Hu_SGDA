"""Small kernel checks; this is not a dataset reproduction."""
import torch
import numpy as np
from simple_knn._C import distCUDA2
from gaussian_rasterizer import GaussianRasterizer, GaussianRasterizationSettings

torch.manual_seed(0)
points = torch.rand(128, 3, device='cuda')
dist = distCUDA2(points)
torch.cuda.synchronize()
assert torch.isfinite(dist).all() and (dist >= 0).all()
print('simple_knn CUDA: PASS')

settings = GaussianRasterizationSettings(
    image_height=32, image_width=32, tanfovx=1., tanfovy=1.,
    bg=torch.zeros(3, device='cuda'), scale_modifier=1.,
    viewmatrix=torch.eye(4, device='cuda'), projmatrix=torch.eye(4, device='cuda'),
    sh_degree=0, campos=torch.zeros(3, device='cuda'), prefiltered=False, debug=False)
xyz = torch.tensor([[0., 0., 2.]], device='cuda', requires_grad=True)
out = GaussianRasterizer(settings)(
    means3D=xyz, means2D=torch.zeros_like(xyz, requires_grad=True),
    opacities=torch.tensor([[.8]], device='cuda', requires_grad=True),
    colors_precomp=torch.tensor([[.8,.2,.1]], device='cuda', requires_grad=True),
    scales=torch.full((1,3), .1, device='cuda', requires_grad=True),
    rotations=torch.tensor([[1.,0.,0.,0.]], device='cuda'))
image = out[0]
assert torch.isfinite(image).all() and image.max() > 0
image.sum().backward()
torch.cuda.synchronize()
assert xyz.grad is not None and torch.isfinite(xyz.grad).all()
print('Gaussian rasterizer CUDA forward/backward: PASS')

import faiss
resources = faiss.StandardGpuResources()
index = faiss.index_cpu_to_gpu(resources, 0, faiss.IndexFlatL2(3))
data = np.random.default_rng(0).random((32,3)).astype('float32')
index.add(data)
d, i = index.search(data[:3], 1)
assert np.array_equal(i[:,0], np.arange(3))
print('FAISS GPU: PASS')

import pygicp
cloud = np.random.default_rng(0).random((100,3))
mask = np.arange(1,101,dtype=np.int32)
registration = pygicp.FastGICP()
registration.set_num_threads(1)
registration.set_input_target(cloud)
registration.set_target_filter(100,mask)
registration.calculate_target_covariance_with_filter()
registration.set_input_source(cloud)
registration.set_source_filter(100,mask)
transform = registration.align(np.eye(4))
assert np.allclose(transform, np.eye(4), atol=1e-4)
print('Project-specific filtered GICP: PASS')
