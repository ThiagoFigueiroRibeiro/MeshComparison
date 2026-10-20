import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Optional

DEVICE_CHOICES = ("auto", "cuda", "cpu")

TORCH_INSTALL_URL = "https://pytorch.org/get-started/locally/"
CUDA_INSTALL_COMMAND = (
    "pip uninstall -y torch torchvision\n"
    "pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128"
)
CUDA_INSTALL_HINT = (
    "A NVIDIA GPU was detected, but the installed PyTorch is a CPU-only build, so CUDA cannot be used.\n"
    "Reinstall PyTorch with CUDA support (pick the command matching your driver at "
    f"{TORCH_INSTALL_URL}), for example:\n"
    + "\n".join("    " + line for line in CUDA_INSTALL_COMMAND.splitlines())
)


@dataclass
class DeviceInfo:
    device: str = "cpu"
    gpu_name: Optional[str] = None
    torch_version: Optional[str] = None
    torch_cuda_version: Optional[str] = None
    nvidia_gpu_detected: bool = False
    warning: Optional[str] = None

    @property
    def uses_cuda(self):
        return self.device == "cuda"

    def describe(self):
        if self.uses_cuda:
            return f"CUDA ({self.gpu_name})"
        return "CPU"


def detect_nvidia_gpu():
    """Return the name of the first NVIDIA GPU reported by ``nvidia-smi``, or None if there is none."""
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return None
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    names = [line.strip() for line in out.splitlines() if line.strip()]
    return names[0] if names else None


def get_device_info(preferred="auto"):
    """
    Pick the device used by the neural-network (LPIPS) step.

    ``auto`` (default) prefers CUDA whenever PyTorch can use it and falls back to the CPU otherwise.
    ``cuda`` raises if CUDA is unavailable; ``cpu`` forces the CPU.
    """
    if preferred not in DEVICE_CHOICES:
        raise ValueError(f"Unknown device {preferred!r}; expected one of {DEVICE_CHOICES}")

    nvidia_name = detect_nvidia_gpu()
    info = DeviceInfo(nvidia_gpu_detected=nvidia_name is not None)

    try:
        import torch
    except ImportError:
        info.warning = "PyTorch is not installed; install it with: pip install torch torchvision lpips"
        if preferred == "cuda":
            raise RuntimeError(info.warning)
        return info

    info.torch_version = torch.__version__
    info.torch_cuda_version = torch.version.cuda
    cuda_ok = torch.cuda.is_available()

    if cuda_ok and preferred != "cpu":
        info.device = "cuda"
        info.gpu_name = torch.cuda.get_device_name(0)
        return info

    if preferred == "cuda":
        raise RuntimeError(
            "CUDA was requested but is not available.\n" + (CUDA_INSTALL_HINT if torch.version.cuda is None
                                                             else "Check the NVIDIA driver installation.")
        )

    if nvidia_name is not None and preferred == "auto":
        info.gpu_name = nvidia_name
        info.warning = CUDA_INSTALL_HINT if torch.version.cuda is None else (
            "A NVIDIA GPU was detected, but torch.cuda.is_available() is False. Check the NVIDIA driver installation."
        )
    return info


def main():
    print(json.dumps(asdict(get_device_info("auto"))))


if __name__ == "__main__":
    sys.exit(main())
