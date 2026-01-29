import torch

try:
    import triton
    import triton.language as tl
    HAS_TRITON = True
except ImportError:
    HAS_TRITON = False

if HAS_TRITON:
    # SwiGLU 融合算子 (MLP)
    @triton.jit
    def swiglu_fused_kernel(x_ptr, w1_ptr, w3_ptr, out_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
        pid = tl.program_id(0)
        block_start = pid * BLOCK_SIZE
        offsets = block_start + tl.arange(0, BLOCK_SIZE)
        mask = offsets < n_elements

        # 读取数据
        x = tl.load(x_ptr + offsets, mask=mask)
        w1 = tl.load(w1_ptr + offsets, mask=mask)
        w3 = tl.load(w3_ptr + offsets, mask=mask)

        # SwiGLU 逻辑: SiLU(x*w1) * (x*w3)
        # SiLU(z) = z * sigmoid(z)
        v1 = x * w1
        v1_silu = v1 * tl.sigmoid(v1)
        res = v1_silu * (x * w3)

        tl.store(out_ptr + offsets, res, mask=mask)

# --- 关键：增加这个函数供外部调用 ---
def run_fused_mlp(x, w1, w3):
    """
    Hacker's Kernels 的 MLP 融合入口
    """
    if HAS_TRITON and x.is_cuda:
        n_elements = x.numel()
        # 准备输出张量
        out = torch.empty_like(x)
        # 定义计算网格 (Grid)
        grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
        # 启动 Kernel
        swiglu_fused_kernel[grid](x, w1, w3, out, n_elements, BLOCK_SIZE=1024)
        return out
    else:
        # Fallback 逻辑 (针对 Mac M5/CPU)
        return torch.nn.functional.silu(x * w1) * (x * w3)
