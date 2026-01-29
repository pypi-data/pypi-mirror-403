import torch
from torch import nn
import triton
import triton.language as tl
import math

from wickyvllm.utils.context import get_context

# Conditional import
try:
    from flash_attn import flash_attn_varlen_func, flash_attn_with_kvcache
    FLASH_ATTN_AVAILABLE = True
except ImportError:
    FLASH_ATTN_AVAILABLE = False


@triton.jit
def store_kvcache_kernel(
    key_ptr,
    key_stride,
    value_ptr,
    value_stride,
    k_cache_ptr,
    v_cache_ptr,
    slot_mapping_ptr,
    D: tl.constexpr,
):
    idx = tl.program_id(0)
    slot = tl.load(slot_mapping_ptr + idx)
    if slot == -1: return
    key_offsets = idx * key_stride + tl.arange(0, D)
    value_offsets = idx * value_stride + tl.arange(0, D)
    key = tl.load(key_ptr + key_offsets)
    value = tl.load(value_ptr + value_offsets)
    cache_offsets = slot * D + tl.arange(0, D)
    tl.store(k_cache_ptr + cache_offsets, key)
    tl.store(v_cache_ptr + cache_offsets, value)


def store_kvcache(key: torch.Tensor, value: torch.Tensor, k_cache: torch.Tensor, v_cache: torch.Tensor, slot_mapping: torch.Tensor):
    N, num_heads, head_dim = key.shape
    D = num_heads * head_dim
    assert key.stride(-1) == 1 and value.stride(-1) == 1
    assert key.stride(1) == head_dim and value.stride(1) == head_dim
    assert k_cache.stride(1) == D and v_cache.stride(1) == D
    assert slot_mapping.numel() == N
    store_kvcache_kernel[(N,)](key, key.stride(0), value, value.stride(0), k_cache, v_cache, slot_mapping, D)


class Attention(nn.Module):

    def __init__(
        self,
        num_heads,
        head_dim,
        scale,
        num_kv_heads,
        use_flash_attn=True,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.scale = scale
        self.num_kv_heads = num_kv_heads
        self.use_flash_attn = use_flash_attn and FLASH_ATTN_AVAILABLE
        self.k_cache = self.v_cache = torch.tensor([])

    def forward(self, q: torch.Tensor, k: torch.Tensor, v: torch.Tensor):
        context = get_context()
        k_cache, v_cache = self.k_cache, self.v_cache
        if k_cache.numel() and v_cache.numel():
            store_kvcache(k, v, k_cache, v_cache, context.slot_mapping)
        
        if self.use_flash_attn:
            # Use FlashAttention
            if context.is_prefill:
                if context.block_tables is not None:    # prefix cache
                    k, v = k_cache, v_cache
                o = flash_attn_varlen_func(q, k, v,
                                           max_seqlen_q=context.max_seqlen_q, cu_seqlens_q=context.cu_seqlens_q,
                                           max_seqlen_k=context.max_seqlen_k, cu_seqlens_k=context.cu_seqlens_k,
                                           softmax_scale=self.scale, causal=True, block_table=context.block_tables)
            else:    # decode
                o = flash_attn_with_kvcache(q.unsqueeze(1), k_cache, v_cache,
                                            cache_seqlens=context.context_lens, block_table=context.block_tables, 
                                            softmax_scale=self.scale, causal=True)
        else:
            # Fallback to PyTorch native attention
            if context.is_prefill:
                if context.block_tables is not None:
                    k, v = k_cache, v_cache
                # Reshape for multi-head attention
                batch_size = len(context.cu_seqlens_q) - 1
                q_list, k_list, v_list = [], [], []
                for i in range(batch_size):
                    start_q, end_q = context.cu_seqlens_q[i], context.cu_seqlens_q[i + 1]
                    start_k, end_k = context.cu_seqlens_k[i], context.cu_seqlens_k[i + 1]
                    q_list.append(q[start_q:end_q])
                    k_list.append(k[start_k:end_k])
                    v_list.append(v[start_k:end_k])
                
                o_list = []
                for qi, ki, vi in zip(q_list, k_list, v_list):
                    # qi: [seq_len, num_heads, head_dim]
                    qi = qi.transpose(0, 1)  # [num_heads, seq_len, head_dim]
                    ki = ki.transpose(0, 1)
                    vi = vi.transpose(0, 1)
                    
                    scores = torch.matmul(qi, ki.transpose(-2, -1)) * self.scale
                    # Causal mask
                    seq_len = qi.size(1)
                    mask = torch.triu(torch.ones(seq_len, seq_len, device=qi.device), diagonal=1).bool()
                    scores = scores.masked_fill(mask, float('-inf'))
                    attn = torch.softmax(scores, dim=-1)
                    oi = torch.matmul(attn, vi)
                    oi = oi.transpose(0, 1)  # [seq_len, num_heads, head_dim]
                    o_list.append(oi)
                o = torch.cat(o_list, dim=0)
            else:  # decode
                # q: [batch_size, num_heads, head_dim]
                batch_size = q.size(0)
                o_list = []
                for i in range(batch_size):
                    context_len = context.context_lens[i]
                    block_table = context.block_tables[i]
                    # Gather k, v from cache
                    # This is simplified - you may need to adjust based on actual cache structure
                    qi = q[i:i+1]  # [1, num_heads, head_dim]
                    # Use the full cache up to context_len
                    # For simplicity, assuming k_cache/v_cache indexing
                    ki = k_cache[block_table[:context_len]]  # approximate
                    vi = v_cache[block_table[:context_len]]
                    
                    scores = torch.matmul(qi, ki.transpose(-2, -1)) * self.scale
                    attn = torch.softmax(scores, dim=-1)
                    oi = torch.matmul(attn, vi)
                    o_list.append(oi)
                o = torch.cat(o_list, dim=0)
        
        return o
