import sys
import types

import pytest

from meshcomparison.common import device as device_module
from meshcomparison.common.device import get_device_info


def _fake_torch(cuda_available, cuda_version):
    torch = types.SimpleNamespace(__version__="0.0")
    torch.version = types.SimpleNamespace(cuda=cuda_version)
    torch.cuda = types.SimpleNamespace(
        is_available=lambda: cuda_available, get_device_name=lambda index: "Fake GPU")
    return torch


@pytest.fixture
def no_nvidia(monkeypatch):
    monkeypatch.setattr(device_module, "detect_nvidia_gpu", lambda: None)


def test_auto_prefers_cuda_when_available(monkeypatch, no_nvidia):
    monkeypatch.setitem(sys.modules, "torch", _fake_torch(True, "12.8"))
    info = get_device_info("auto")
    assert info.device == "cuda" and info.gpu_name == "Fake GPU" and info.warning is None


def test_auto_falls_back_to_cpu_without_cuda(monkeypatch, no_nvidia):
    monkeypatch.setitem(sys.modules, "torch", _fake_torch(False, None))
    info = get_device_info("auto")
    assert info.device == "cpu" and info.warning is None


def test_cpu_only_torch_with_nvidia_gpu_warns(monkeypatch):
    monkeypatch.setattr(device_module, "detect_nvidia_gpu", lambda: "RTX Fake")
    monkeypatch.setitem(sys.modules, "torch", _fake_torch(False, None))
    info = get_device_info("auto")
    assert info.device == "cpu" and info.nvidia_gpu_detected
    assert "CPU-only" in info.warning


def test_explicit_cuda_without_cuda_raises(monkeypatch, no_nvidia):
    monkeypatch.setitem(sys.modules, "torch", _fake_torch(False, None))
    with pytest.raises(RuntimeError):
        get_device_info("cuda")


def test_explicit_cpu_ignores_cuda(monkeypatch, no_nvidia):
    monkeypatch.setitem(sys.modules, "torch", _fake_torch(True, "12.8"))
    assert get_device_info("cpu").device == "cpu"


def test_unknown_device_rejected():
    with pytest.raises(ValueError):
        get_device_info("tpu")
