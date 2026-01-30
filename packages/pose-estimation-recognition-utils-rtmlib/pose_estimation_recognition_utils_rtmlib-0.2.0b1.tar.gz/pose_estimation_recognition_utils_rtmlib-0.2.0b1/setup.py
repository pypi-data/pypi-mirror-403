import os
import re
from setuptools import setup
import subprocess
from typing import Dict, Optional


def read_requirements():
    here=os.path.dirname(os.path.abspath(__file__))
    req_path=os.path.join(here, 'requirements.txt')
    with open(req_path, 'r') as f:
        return f.read().splitlines()


def get_cuda_version():
    try:
        output=subprocess.check_output(['nvcc', '--version']).decode()
        match=re.search(r'release (\d+\.\d+)', output)
        if match:
            return float(match.group(1))
    except Exception:
        return None



def _run(cmd):
    return subprocess.check_output(
        cmd,
        stderr=subprocess.STDOUT,
        text=True
    ).strip()


def _parse_version(text):
    m = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', text)
    if not m:
        return None
    major, minor, patch = m.groups()
    return int(major), int(minor), int(patch or 0)


def get_rocm_version() -> Optional[Dict]:
    try:
        version_file = "/opt/rocm/.info/version"
        if os.path.exists(version_file):
            raw = open(version_file).read().strip()
            v = _parse_version(raw)
            if v:
                return {
                    "version": v,
                    "source": "runtime",
                    "raw": raw
                }
    except Exception:
        pass

    try:
        raw = _run(["hipcc", "--version"])
        v = _parse_version(raw)
        if v:
            return {
                "version": v,
                "source": "hipcc",
                "raw": raw
            }
    except Exception:
        pass

    try:
        raw = _run(["rocminfo"])
        v = _parse_version(raw)
        if v:
            return {
                "version": v,
                "source": "rocminfo",
                "raw": raw[:500]  # Output ist riesig
            }
    except Exception:
        pass

    try:
        raw = _run(["rocm-smi", "--version"])
        v = _parse_version(raw)
        if v:
            return {
                "version": v,
                "source": "rocm-smi",
                "raw": raw
            }
    except Exception:
        pass

    try:
        rocm_path = os.getenv("ROCM_PATH") or os.getenv("ROCM_HOME")
        if rocm_path:
            v = _parse_version(rocm_path)
            if v:
                return {
                    "version": v,
                    "source": "env",
                    "raw": rocm_path
                }
    except Exception:
        pass

    return None


def get_pytorch_version(cuda_version=None, rocm_version=None):
    if cuda_version is not None:
        if 12.6 <= cuda_version < 12.8:
            return 'torch>=2.4.0+cu126'
        elif 12.8 <= cuda_version < 13.0:
            return 'torch>=2.4.0+cu128'
        elif cuda_version >= 13.0:
            return 'torch>=2.4.0+cu130'
        else:
            return 'torch>=2.4.0'
    elif rocm_version is not None:
        if rocm_version >= 7.1:
            return 'torch>=2.4.0+rocm7.1'
        else:
            return 'torch>=2.4.0'
    else:
        return 'torch>=2.4.0'


requirements=read_requirements()

try:
    # noinspection PyPackageRequirements
    import torch
    torch_installed=True
except ImportError:
    torch_installed=False

if not torch_installed:
    detected_cuda=get_cuda_version()
    detected_rocm=get_rocm_version()

    print(f"recognized CUDA-Version: {detected_cuda}")
    print(f"recognized ROCm-Version: {detected_rocm}")

    requirements.append(get_pytorch_version(detected_cuda, detected_rocm))

setup(
    name='pose-estimation-recognition-utils-rtmlib',
    version='0.2.0b1',
    packages=['pose_estimation_recognition_utils_rtmlib'],
    install_requires=requirements,
    url='https://github.com/cobtras/pose-estimation-recognition-utils-rtmlib',
    license='Apache 2.0',
    author='Jonas David Stephan, Sabine Dawletow, Nathalie Dollmann, Benjamin Otto Ernst Bruch',
    author_email='j.stephan@system-systeme.de',
    description='Classes for AI recognition on pose estimation data with rtmlib',
    long_description='Includes all general classes needed for AI movement recognition based on pose estimation data with rtmlib'
)