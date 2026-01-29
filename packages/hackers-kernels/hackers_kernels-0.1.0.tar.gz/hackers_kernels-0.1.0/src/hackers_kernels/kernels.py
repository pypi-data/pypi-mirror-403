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
