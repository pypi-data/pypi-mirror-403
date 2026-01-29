"""GPU cloud providers for gpuci.

Supported providers:
- ssh: Direct SSH to your own GPU machines
- runpod: RunPod cloud GPUs (https://runpod.io)
- lambdalabs: Lambda Labs cloud GPUs (https://lambdalabs.com)
- vastai: Vast.ai GPU marketplace (https://vast.ai)
- fluidstack: FluidStack enterprise GPUs (https://fluidstack.io)
- brev: NVIDIA Brev cloud GPUs (https://brev.dev)
"""

from gpuci.providers.base import BaseProvider, ExecutionResult
from gpuci.providers.ssh import SSHProvider
from gpuci.providers.brev import BrevProvider
from gpuci.providers.runpod import RunPodProvider
from gpuci.providers.lambdalabs import LambdaLabsProvider
from gpuci.providers.vastai import VastAIProvider
from gpuci.providers.fluidstack import FluidStackProvider

__all__ = [
    "BaseProvider",
    "ExecutionResult",
    "SSHProvider",
    "BrevProvider",
    "RunPodProvider",
    "LambdaLabsProvider",
    "VastAIProvider",
    "FluidStackProvider",
]
