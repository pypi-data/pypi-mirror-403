from .kernels import HAS_TRITON, run_fused_mlp

__version__ = "0.1.0"
__author__ = "Ashley (Hacker's Kernels)"

def hello() -> str:
    """
    打个招呼，并报告当前硬件环境
    """
    status = "Triton-Ready" if HAS_TRITON else "CPU-Only (Mac/Non-GPU)"
    return f"🚀 Hello from Hacker's Kernels! [Version: {__version__} | Mode: {status}]"

# 这里的导出非常重要，方便用户直接调用
# 这样用户可以: from hackers_kernels import run_mla
__all__ = ["hello", "HAS_TRITON", "run_fused_mlp"]

