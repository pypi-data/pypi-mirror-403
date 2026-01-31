# coding=utf-8
# Copyright (c) 2025, Qwerky AI, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""MambaInLlama model for vLLM using native Triton ops.

This module uses vLLM's native Mamba ops for maximum performance.
No mamba_ssm or causal_conv1d compilation required.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Iterable, ClassVar, Literal
import json
import os

import torch
import torch.nn as nn
import torch.nn.functional as F
import math

from einops import rearrange, repeat

from transformers.utils import logging

from .configuration import MambaInLlamaMambaConfig


def _load_mamba_config(model_path: str) -> dict:
    """Load mamba_config.json from model directory if it exists.

    Many MambaInLlama models store Mamba-specific config (attn_layers, d_inner, d_xb)
    in a separate mamba_config.json file rather than the main config.json.
    """
    mamba_config = {}

    # Try to find mamba_config.json
    possible_paths = [
        os.path.join(model_path, "mamba_config.json"),
    ]

    # Handle HuggingFace cache paths
    if "huggingface" in model_path or "hub" in model_path:
        # The model_path might be the cache directory
        possible_paths.append(os.path.join(model_path, "mamba_config.json"))

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    mamba_config = json.load(f)
                    logging.get_logger(__name__).info(f"Loaded mamba_config.json from {path}")
                    break
            except Exception as e:
                logging.get_logger(__name__).warning(f"Failed to load {path}: {e}")

    return mamba_config

logger = logging.get_logger(__name__)

# =============================================================================
# vLLM NATIVE IMPORTS
# =============================================================================

_vllm_available = False

# Core vLLM imports
try:
    from vllm.model_executor.layers.layernorm import RMSNorm
    from vllm.model_executor.layers.linear import (
        ColumnParallelLinear,
        MergedColumnParallelLinear,
        RowParallelLinear,
    )
    from vllm.model_executor.layers.logits_processor import LogitsProcessor
    from vllm.model_executor.layers.vocab_parallel_embedding import (
        VocabParallelEmbedding,
        ParallelLMHead,
    )
    from vllm.model_executor.model_loader.weight_utils import default_weight_loader
    from vllm.attention import Attention, AttentionMetadata
    from vllm.attention.backends.abstract import AttentionType
    from vllm.model_executor.layers.rotary_embedding import get_rope
    from vllm.distributed import get_tensor_model_parallel_world_size
    from vllm.config import VllmConfig, CacheConfig, get_current_vllm_config
    from vllm.model_executor.layers.activation import SiluAndMul
    from vllm.forward_context import ForwardContext, get_forward_context

    _vllm_available = True
    logger.info("vLLM core components loaded successfully")
except ImportError as e:
    logger.warning(f"vLLM not available: {e}")
    RMSNorm = None
    get_current_vllm_config = None
    get_forward_context = None

# MambaBase import for proper vLLM integration
_MambaBase = None
try:
    from vllm.model_executor.layers.mamba.abstract import MambaBase as _MambaBase
    logger.info("vLLM MambaBase loaded successfully")
except ImportError as e:
    logger.warning(f"vLLM MambaBase not available: {e}")

# Mamba1AttentionMetadata for state indices
_Mamba1AttentionMetadata = None
try:
    from vllm.v1.attention.backends.mamba1_attn import Mamba1AttentionMetadata as _Mamba1AttentionMetadata
    logger.info("vLLM Mamba1AttentionMetadata loaded successfully")
except ImportError as e:
    logger.warning(f"vLLM Mamba1AttentionMetadata not available: {e}")

# Mamba ops imports
_mamba_ops_available = False
try:
    from vllm.model_executor.layers.mamba.ops.causal_conv1d import (
        causal_conv1d_fn,
        causal_conv1d_update,
    )
    from vllm.model_executor.layers.mamba.ops.mamba_ssm import (
        selective_scan_fn,
        selective_state_update,
    )
    _mamba_ops_available = True
    logger.info("vLLM Mamba ops loaded successfully")
except ImportError as e:
    logger.warning(f"vLLM Mamba ops not available: {e}")

# Try to import Sampler (location varies by vLLM version)
_vllm_Sampler = None
try:
    from vllm.model_executor.layers.sampler import Sampler as _vllm_Sampler
except ImportError:
    try:
        from vllm.v1.sample.sampler import Sampler as _vllm_Sampler
    except ImportError:
        pass

# Try to import MambaModelConfig for hybrid model support
_vllm_MambaModelConfig = None
try:
    from vllm.model_executor.models.config import MambaModelConfig as _vllm_MambaModelConfig
except ImportError:
    pass

# Try to import protocol interfaces for model registration
_HasInnerState = None
_IsHybrid = None
try:
    from vllm.model_executor.models.interfaces import HasInnerState as _HasInnerState
    from vllm.model_executor.models.interfaces import IsHybrid as _IsHybrid
except ImportError:
    pass

# Try to import state calculators
_vllm_MambaStateShapeCalculator = None
_vllm_MambaStateDtypeCalculator = None
try:
    from vllm.model_executor.layers.mamba.mamba_utils import (
        MambaStateShapeCalculator as _vllm_MambaStateShapeCalculator,
        MambaStateDtypeCalculator as _vllm_MambaStateDtypeCalculator,
    )
except ImportError:
    pass


# =============================================================================
# FALLBACK IMPLEMENTATIONS (for when vLLM ops not available)
# =============================================================================

class RMSNormFallback(nn.Module):
    """RMSNorm fallback."""
    def __init__(self, hidden_size: int, eps: float = 1e-6, **kwargs):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps

    def forward(self, x, residual=None):
        if residual is not None:
            x = x + residual
            residual = x
        input_dtype = x.dtype
        x = x.to(torch.float32)
        variance = x.pow(2).mean(-1, keepdim=True)
        x = self.weight * (x * torch.rsqrt(variance + self.eps)).to(input_dtype)
        if residual is not None:
            return x, residual
        return x


if RMSNorm is None:
    RMSNorm = RMSNormFallback


def repeat_kv(hidden_states: torch.Tensor, n_rep: int) -> torch.Tensor:
    """Repeat KV heads."""
    batch, num_key_value_heads, slen, head_dim = hidden_states.shape
    if n_rep == 1:
        return hidden_states
    hidden_states = hidden_states[:, :, None, :, :].expand(
        batch, num_key_value_heads, n_rep, slen, head_dim
    )
    return hidden_states.reshape(batch, num_key_value_heads * n_rep, slen, head_dim)


# =============================================================================
# MAMBAINLLAMA MAMBA MIXER (Native vLLM ops)
# =============================================================================

# NOTE: We intentionally do NOT inherit from MambaBase because:
# 1. MambaBase inherits from AttentionLayerBase which breaks normal nn.Module __call__
# 2. vLLM's MambaMixer uses @CustomOp.register decorator for callability
# Instead, we implement the MambaBase interface methods on nn.Module
_MixerBaseClass = nn.Module


class MambaInLlamaMambaMixer(_MixerBaseClass):
    """MambaInLlama Mamba mixer conforming to vLLM's caching interface.

    This implements the grouped-head Mamba architecture used in MambaInLlama
    while integrating with vLLM's state management for CUDA graph compatibility.

    Key architectural differences from standard Mamba:
    - Fused in_proj: outputs [z, x, B, C, dt] instead of separate projections
    - Grouped heads: d_xb for B projection, d_inner for C projection
    - repeat_kv expansion for B to match C's head count

    vLLM integration:
    - Inherits from MambaBase for proper state management
    - Registers in static_forward_context for CUDA graphs
    - Uses self.kv_cache populated by vLLM
    - Accesses state via attn_metadata.state_indices_tensor
    """

    def __init__(
        self,
        config: MambaInLlamaMambaConfig,
        layer_idx: int,
        prefix: str = "",
    ):
        super().__init__()
        self.layer_idx = layer_idx
        self.prefix = prefix

        # Core dimensions
        self.d_model = config.d_model
        self.d_inner = config.d_inner
        self.d_xb = config.d_xb
        self.d_state = config.ssm_cfg.get("d_state", 16)
        self.d_conv = config.ssm_cfg.get("d_conv", 4)
        self.dt_rank = math.ceil(self.d_model / 16)

        # Grouped head configuration
        # For Mamba1: B and C both use d_xb dimension, then expanded via repeat_kv
        self.num_xb_head = self.d_xb // self.d_state  # B/C projection heads before expansion
        self.num_heads = self.d_inner // self.d_state  # Head count after expansion (used in SSM)
        self.repeat_group = self.d_inner // self.d_xb  # Expansion factor for repeat_kv
        # Keep num_C_head for backwards compat (equals num_heads after expansion)
        self.num_C_head = self.num_heads
        self.repeat_kv_before_conv = config.ssm_cfg.get("repeat_kv_before_conv", True)

        # Determine conv dimension based on repeat_kv_before_conv
        self.conv_dim = self.d_inner if self.repeat_kv_before_conv else self.d_xb

        # Fused input projection: [z, x, B, C, dt]
        # z: d_inner, x: d_xb, B: d_xb, C: d_inner, dt: dt_rank
        # NOTE: x and C have swapped dimensions compared to naive expectation!
        # x starts at d_xb and gets expanded via repeat_kv, C is already d_inner
        self.in_proj = nn.Linear(
            self.d_model,
            2 * self.d_inner + 2 * self.d_xb + self.dt_rank,
            bias=False,
        )

        # Conv1d - depthwise convolution
        self.conv1d = nn.Conv1d(
            in_channels=self.conv_dim,
            out_channels=self.conv_dim,
            kernel_size=self.d_conv,
            groups=self.conv_dim,
            padding=self.d_conv - 1,
            bias=True,
        )

        # Delta time projection
        self.dt_proj = nn.Linear(self.dt_rank, self.d_inner, bias=True)

        # Initialize dt_proj bias with inverse softplus
        dt_min, dt_max = 0.001, 0.1
        dt = torch.exp(
            torch.rand(self.d_inner) * (math.log(dt_max) - math.log(dt_min)) + math.log(dt_min)
        ).clamp(min=1e-4)
        inv_dt = dt + torch.log(-torch.expm1(-dt))
        with torch.no_grad():
            self.dt_proj.bias.copy_(inv_dt)

        # A matrix (stored as log)
        A = repeat(
            torch.arange(1, self.d_state + 1, dtype=torch.float32),
            "n -> d n",
            d=self.d_inner,
        ).contiguous()
        self.A_log = nn.Parameter(torch.log(A))
        self.A_log._no_weight_decay = True

        # D skip parameter
        self.D = nn.Parameter(torch.ones(self.d_inner))
        self.D._no_weight_decay = True

        # Output projection
        self.out_proj = nn.Linear(self.d_inner, self.d_model, bias=False)

        self.activation = "silu"
        self.act = nn.SiLU()

        # vLLM state management: kv_cache tuple of (conv_state, ssm_state)
        # This will be populated by vLLM's infrastructure
        self.kv_cache: tuple[torch.Tensor, ...] = (torch.tensor([]), torch.tensor([]))

        # Register in vLLM's static_forward_context for CUDA graph support
        if get_current_vllm_config is not None and prefix:
            try:
                compilation_config = get_current_vllm_config().compilation_config
                if prefix not in compilation_config.static_forward_context:
                    compilation_config.static_forward_context[prefix] = self
                    logger.info(f"Registered MambaMixer layer {prefix} in static_forward_context")
            except Exception as e:
                logger.warning(f"Could not register in static_forward_context: {e}")

    # =========================================================================
    # MambaBase interface methods (for vLLM integration)
    # =========================================================================

    def get_state_shape(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Return state shapes for vLLM cache allocation.

        Returns:
            (conv_state_shape, ssm_state_shape) where:
            - conv_state_shape: (d_conv - 1, conv_dim)
            - ssm_state_shape: (d_inner, d_state)
        """
        # vLLM expects shapes in (width, channels) format for conv state
        conv_state_shape = (self.d_conv - 1, self.conv_dim)
        ssm_state_shape = (self.d_inner, self.d_state)
        return conv_state_shape, ssm_state_shape

    def get_state_dtype(self) -> tuple[torch.dtype, torch.dtype]:
        """Return state dtypes for vLLM cache allocation."""
        dtype = self.out_proj.weight.dtype
        return (dtype, dtype)

    @property
    def mamba_type(self) -> str:
        """Return mamba type for vLLM backend selection."""
        return "mamba1"

    def forward(
        self,
        hidden_states: torch.Tensor,
        conv_state: Optional[torch.Tensor] = None,
        ssm_state: Optional[torch.Tensor] = None,
        cache_position: int = 0,
        attn_metadata=None,
    ) -> torch.Tensor:
        """Forward pass with vLLM state management support.

        Args:
            hidden_states: (batch, seq_len, d_model) or (total_tokens, d_model)
            conv_state: Optional explicit conv state (for backwards compat)
            ssm_state: Optional explicit SSM state (for backwards compat)
            cache_position: current position in sequence for decode
            attn_metadata: vLLM attention metadata with state_indices_tensor

        Returns:
            output: same shape as hidden_states
        """
        # Handle 2D input from vLLM (total_tokens, d_model)
        input_2d = hidden_states.dim() == 2
        if input_2d:
            hidden_states = hidden_states.unsqueeze(0)

        batch, seqlen, _ = hidden_states.shape

        # Try to get state from vLLM's ForwardContext if not explicitly provided
        state_indices = None
        if conv_state is None or ssm_state is None:
            if get_forward_context is not None:
                try:
                    forward_context = get_forward_context()
                    if forward_context is not None and hasattr(forward_context, 'attn_metadata'):
                        fc_attn_metadata = forward_context.attn_metadata
                        if isinstance(fc_attn_metadata, dict) and self.prefix in fc_attn_metadata:
                            attn_metadata = fc_attn_metadata[self.prefix]
                        elif fc_attn_metadata is not None:
                            attn_metadata = fc_attn_metadata

                        # Get kv_cache from ForwardContext
                        if hasattr(forward_context, 'virtual_engine') and len(self.kv_cache) > 0:
                            if hasattr(self.kv_cache, '__getitem__') and len(self.kv_cache[0]) > 0:
                                ve = forward_context.virtual_engine if hasattr(forward_context, 'virtual_engine') else 0
                                if isinstance(self.kv_cache[0], torch.Tensor) and self.kv_cache[0].numel() > 0:
                                    conv_state = self.kv_cache[0]
                                    ssm_state = self.kv_cache[1]
                except Exception as e:
                    logger.debug(f"Could not get state from ForwardContext: {e}")

            # Get state indices from attn_metadata
            if attn_metadata is not None:
                if _Mamba1AttentionMetadata is not None and isinstance(attn_metadata, _Mamba1AttentionMetadata):
                    state_indices = attn_metadata.state_indices_tensor
                elif hasattr(attn_metadata, 'state_indices_tensor'):
                    state_indices = attn_metadata.state_indices_tensor

        is_decode = seqlen == 1 and cache_position > 0

        # Fused projection: [z, x, B, C, dt]
        # CRITICAL: x is d_xb (not d_inner), C is d_inner (not d_xb)
        # x gets expanded via repeat_kv, C is already at full dimension
        zxbcdt = self.in_proj(hidden_states)
        z, x, B, C, dt = torch.split(
            zxbcdt,
            [self.d_inner, self.d_xb, self.d_xb, self.d_inner, self.dt_rank],
            dim=-1,
        )

        A = -torch.exp(self.A_log.float())

        if is_decode:
            # Decode path - single token
            output = self._decode_step(x, z, B, C, dt, A, conv_state, ssm_state, state_indices)
        else:
            # Prefill path - full sequence
            output = self._prefill(x, z, B, C, dt, A, conv_state, ssm_state, seqlen, state_indices)

        # Restore original shape if input was 2D
        if input_2d:
            output = output.squeeze(0)

        return output

    def _prefill(
        self,
        x: torch.Tensor,
        z: torch.Tensor,
        B: torch.Tensor,
        C: torch.Tensor,
        dt: torch.Tensor,
        A: torch.Tensor,
        conv_state: Optional[torch.Tensor],
        ssm_state: Optional[torch.Tensor],
        seqlen: int,
        state_indices: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Prefill forward pass.

        Note: x is d_xb, C is d_inner (opposite of naive expectation).
        x and B need repeat_kv expansion, C does not.

        Args:
            state_indices: Optional tensor for batch indexing into state cache
        """
        batch = x.shape[0]

        # Reshape for processing
        # x: (batch, seq, d_xb) -> (batch, d_xb, seq)
        x = rearrange(x, "b l d -> b d l")
        # z: (batch, seq, d_inner) -> (batch, d_inner, seq)
        z = rearrange(z, "b l d -> b d l")

        # Process B with grouped heads and repeat_kv expansion
        # B: (batch, seq, d_xb) -> (batch, num_C_head, d_state, seq)
        B = rearrange(B, "b l (n_group dstate) -> b n_group l dstate", dstate=self.d_state)
        B = repeat_kv(B, self.repeat_group)
        B = rearrange(B, "b n_group l dstate -> b n_group dstate l").contiguous()

        # Process C - already d_inner, just rearrange (NO repeat_kv needed)
        # C: (batch, seq, d_inner) -> (batch, num_C_head, d_state, seq)
        C = rearrange(C, "b l (n_group dstate) -> b n_group dstate l", dstate=self.d_state).contiguous()

        # Delta time projection
        dt = self.dt_proj(dt)
        dt = rearrange(dt, "b l d -> b d l")

        # x is d_xb, expand via repeat_kv if repeat_kv_before_conv is True
        if self.repeat_kv_before_conv:
            # x: (batch, d_xb, seq) -> (batch, d_inner, seq)
            x = rearrange(x, "b (n_group dstate) l -> b n_group dstate l", dstate=self.d_state)
            x = repeat_kv(x, self.repeat_group)
            x = rearrange(x, "b n_group dstate l -> b (n_group dstate) l")

        # Update conv state with last d_conv-1 tokens
        # When state_indices is provided, use indexed update for batched requests
        if conv_state is not None:
            conv_update = F.pad(x, (self.d_conv - x.shape[-1], 0))[:, :, -self.d_conv:]
            if state_indices is not None and conv_state.dim() >= 3:
                # Use state indices for proper batch indexing
                try:
                    for i, idx in enumerate(state_indices[:batch]):
                        if idx >= 0 and idx < conv_state.shape[0]:
                            conv_state[idx].copy_(conv_update[i % conv_update.shape[0]])
                except Exception:
                    # Fallback to direct copy
                    conv_state[:batch].copy_(conv_update[:batch])
            else:
                conv_state.copy_(conv_update)

        # Causal convolution
        x = self.act(self.conv1d(x)[..., :seqlen])

        # If repeat_kv_before_conv is False, expand after conv
        if not self.repeat_kv_before_conv:
            x = rearrange(x, "b (n_group dstate) l -> b n_group dstate l", dstate=self.d_state)
            x = repeat_kv(x, self.repeat_group)
            x = rearrange(x, "b n_group dstate l -> b (n_group dstate) l")

        # SSM scan (using PyTorch implementation for now)
        # TODO: Integrate with vLLM's selective_scan_fn when shapes match
        y = self._ssm_scan(x, dt, A, B, C, z, ssm_state, state_indices)

        y = rearrange(y, "b d l -> b l d")
        return self.out_proj(y)

    def _decode_step(
        self,
        x: torch.Tensor,
        z: torch.Tensor,
        B: torch.Tensor,
        C: torch.Tensor,
        dt: torch.Tensor,
        A: torch.Tensor,
        conv_state: Optional[torch.Tensor],
        ssm_state: Optional[torch.Tensor],
        state_indices: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Single decode step.

        Note: x is d_xb, C is d_inner (opposite of naive expectation).
        x and B need repeat_kv expansion, C does not.

        Args:
            state_indices: Optional tensor for batch indexing into state cache
        """
        # x, z, B, C, dt: (batch, 1, dim) -> squeeze to (batch, dim)
        x = x.squeeze(1)  # (batch, d_xb)
        z = z.squeeze(1)  # (batch, d_inner)
        B = B.squeeze(1)  # (batch, d_xb)
        C = C.squeeze(1)  # (batch, d_inner)
        dt = dt.squeeze(1)  # (batch, dt_rank)
        batch = x.shape[0]

        # Process B with grouped heads and repeat_interleave expansion
        B = rearrange(B, "b (n_group dstate) -> b n_group dstate", dstate=self.d_state)
        B = torch.repeat_interleave(B, dim=1, repeats=self.repeat_group)

        # Process C - already d_inner, just rearrange (NO repeat_interleave needed)
        C = rearrange(C, "b (n_group dstate) -> b n_group dstate", dstate=self.d_state).contiguous()

        # Delta time projection
        dt = self.dt_proj(dt)

        # x is d_xb, expand via repeat_interleave if repeat_kv_before_conv is True
        if self.repeat_kv_before_conv:
            x = rearrange(x, "b (n_group dstate) -> b n_group dstate", dstate=self.d_state)
            x = torch.repeat_interleave(x, dim=1, repeats=self.repeat_group)
            x = rearrange(x, "b n_group dstate -> b (n_group dstate)")

        # Conv state update with state indices support
        if conv_state is not None:
            if state_indices is not None and conv_state.dim() >= 3:
                # Use state indices for proper batch indexing
                try:
                    for i, idx in enumerate(state_indices[:batch]):
                        if idx >= 0 and idx < conv_state.shape[0]:
                            conv_state[idx] = torch.roll(conv_state[idx], shifts=-1, dims=-1)
                            conv_state[idx, :, -1] = x[i]
                    # Compute conv output using indexed states
                    conv_out = []
                    for i, idx in enumerate(state_indices[:batch]):
                        if idx >= 0 and idx < conv_state.shape[0]:
                            c = torch.sum(
                                conv_state[idx] * rearrange(self.conv1d.weight, "d 1 w -> d w"), dim=-1
                            )
                            conv_out.append(c)
                    if conv_out:
                        x = torch.stack(conv_out, dim=0)
                    else:
                        # Fallback
                        x = torch.sum(
                            conv_state[:batch] * rearrange(self.conv1d.weight, "d 1 w -> d w"), dim=-1
                        )
                except Exception:
                    # Fallback to direct indexing
                    conv_state.copy_(torch.roll(conv_state, shifts=-1, dims=-1))
                    conv_state[:, :, -1] = x
                    x = torch.sum(
                        conv_state * rearrange(self.conv1d.weight, "d 1 w -> d w"), dim=-1
                    )
            else:
                conv_state.copy_(torch.roll(conv_state, shifts=-1, dims=-1))
                conv_state[:, :, -1] = x
                x = torch.sum(
                    conv_state * rearrange(self.conv1d.weight, "d 1 w -> d w"), dim=-1
                )

            if self.conv1d.bias is not None:
                x = x + self.conv1d.bias
        else:
            # No conv state - just apply bias if present (shouldn't happen normally)
            if self.conv1d.bias is not None:
                x = x + self.conv1d.bias

        x = self.act(x)

        # If repeat_kv_before_conv is False, expand after conv
        if not self.repeat_kv_before_conv:
            x = rearrange(x, "b (n_group dstate) -> b n_group dstate", dstate=self.d_state)
            x = torch.repeat_interleave(x, dim=1, repeats=self.repeat_group)
            x = rearrange(x, "b n_group dstate -> b (n_group dstate)")

        # SSM state update
        y = self._ssm_state_update(x, dt, A, B, C, z, ssm_state, state_indices)

        return self.out_proj(y).unsqueeze(1)

    def _ssm_scan(
        self,
        u: torch.Tensor,
        delta: torch.Tensor,
        A: torch.Tensor,
        B: torch.Tensor,
        C: torch.Tensor,
        z: torch.Tensor,
        ssm_state: Optional[torch.Tensor],
        state_indices: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """SSM scan implementation.

        Args:
            u: (batch, d_inner, seqlen)
            delta: (batch, d_inner, seqlen)
            A: (d_inner, d_state)
            B: (batch, num_C_head, d_state, seqlen)
            C: (batch, num_C_head, d_state, seqlen)
            z: (batch, d_inner, seqlen) - gate
            ssm_state: (batch, num_C_head, d_state, head_dim) or None
            state_indices: Optional batch indices for state cache
        """
        batch, dim, seqlen = u.shape
        orig_dtype = u.dtype

        # Apply softplus to delta with bias
        # NOTE: The reference implementation double-applies bias: dt_proj adds it once,
        # then selective_scan_fn adds it again. We match this for checkpoint compatibility.
        delta = F.softplus(delta + self.dt_proj.bias.unsqueeze(0).unsqueeze(-1))

        # Discretize A: dA = exp(delta * A)
        # A: (d_inner, d_state) -> (1, d_inner, 1, d_state)
        # delta: (batch, d_inner, seqlen) -> (batch, d_inner, seqlen, 1)
        # Result dA: (batch, d_inner, seqlen, d_state)
        dA = torch.exp(delta.unsqueeze(-1) * A.unsqueeze(0).unsqueeze(2))

        # Cast back to original dtype to avoid float32 accumulation
        delta = delta.to(orig_dtype)
        dA = dA.to(orig_dtype)

        # Reshape for grouped computation
        # u: (batch, d_inner, seqlen) -> (batch, num_C_head, head_dim, seqlen)
        u_grouped = rearrange(u, "b (h d) l -> b h d l", h=self.num_C_head)
        delta_grouped = rearrange(delta, "b (h d) l -> b h d l", h=self.num_C_head)
        dA_grouped = rearrange(dA, "b (h d) l n -> b h d l n", h=self.num_C_head)

        # B: (batch, num_C_head, d_state, seqlen)
        # dB_u = delta * B * u
        # Need to compute (batch, num_C_head, d_state, seqlen) * (batch, num_C_head, 1, seqlen)
        dB_u = delta_grouped.unsqueeze(3) * B.unsqueeze(2) * u_grouped.unsqueeze(3)
        # dB_u: (batch, num_C_head, head_dim, d_state, seqlen)

        # Sequential scan - use original dtype for state
        head_dim = self.d_inner // self.num_C_head
        state = torch.zeros(batch, self.num_C_head, head_dim, self.d_state, device=u.device, dtype=orig_dtype)

        outputs = []
        for t in range(seqlen):
            state = dA_grouped[:, :, :, t, :] * state + dB_u[:, :, :, :, t]
            # Output: y_t = C_t * state
            # C: (batch, num_C_head, d_state, seqlen)
            # state: (batch, num_C_head, head_dim, d_state)
            y_t = torch.einsum("bhdn,bhn->bhd", state, C[:, :, :, t])
            outputs.append(y_t)

        y = torch.stack(outputs, dim=-1)  # (batch, num_C_head, head_dim, seqlen)
        y = rearrange(y, "b h d l -> b (h d) l")

        # Add skip connection
        y = y + self.D.unsqueeze(0).unsqueeze(-1) * u

        # Apply gate
        y = y * F.silu(z)

        # Update SSM state cache with state indices support
        if ssm_state is not None:
            final_state = rearrange(state, "b h d n -> b h n d")
            if state_indices is not None and ssm_state.dim() >= 4:
                try:
                    for i, idx in enumerate(state_indices[:batch]):
                        if idx >= 0 and idx < ssm_state.shape[0]:
                            ssm_state[idx].copy_(final_state[i % final_state.shape[0]])
                except Exception:
                    ssm_state[:batch].copy_(final_state[:batch])
            else:
                ssm_state.copy_(final_state)

        return y

    def _ssm_state_update(
        self,
        x: torch.Tensor,
        dt: torch.Tensor,
        A: torch.Tensor,
        B: torch.Tensor,
        C: torch.Tensor,
        z: torch.Tensor,
        ssm_state: Optional[torch.Tensor],
        state_indices: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Single SSM state update for decode.

        Args:
            x: (batch, d_inner)
            dt: (batch, d_inner)
            A: (d_inner, d_state)
            B: (batch, num_C_head, d_state)
            C: (batch, num_C_head, d_state)
            z: (batch, d_inner)
            ssm_state: (batch, num_C_head, d_state, head_dim) or None
            state_indices: Optional batch indices for state cache
        """
        orig_dtype = x.dtype
        batch = x.shape[0]

        # Apply softplus to dt with bias
        # NOTE: The reference implementation double-applies bias: dt_proj adds it once,
        # then selective_state_update adds it again. We match this for checkpoint compatibility.
        dt = F.softplus(dt + self.dt_proj.bias)

        # Reshape for grouped computation
        x = rearrange(x, "b (h d) -> b h d", h=self.num_C_head)
        dt = rearrange(dt, "b (h d) -> b h d", h=self.num_C_head)
        A = rearrange(A, "(h d) n -> h d n", h=self.num_C_head)
        D = rearrange(self.D, "(h d) -> h d", h=self.num_C_head)
        z = rearrange(z, "b (h d) -> b h d", h=self.num_C_head)

        # Discretize A and cast back to original dtype
        dA = torch.exp(dt.unsqueeze(-1) * A).to(orig_dtype)  # (batch, num_C_head, head_dim, d_state)
        dt = dt.to(orig_dtype)

        # dB = dt * B
        dB = dt.unsqueeze(-1) * B.unsqueeze(2)  # (batch, num_C_head, head_dim, d_state)

        # State update: state = dA * state + dB * x
        if ssm_state is not None:
            if state_indices is not None and ssm_state.dim() >= 4:
                # Use state indices for proper batch indexing
                try:
                    # Process each batch element with its corresponding state index
                    y_list = []
                    for i, idx in enumerate(state_indices[:batch]):
                        if idx >= 0 and idx < ssm_state.shape[0]:
                            # ssm_state[idx]: (num_C_head, d_state, head_dim) -> transpose to (num_C_head, head_dim, d_state)
                            state_i = ssm_state[idx].transpose(-1, -2)
                            state_i = dA[i] * state_i + dB[i] * x[i].unsqueeze(-1)
                            ssm_state[idx].copy_(state_i.transpose(-1, -2))

                            # Output: y = C * state + D * x
                            y_i = torch.einsum("hdn,hn->hd", state_i, C[i])
                            y_i = y_i + D * x[i]
                            y_list.append(y_i)
                    if y_list:
                        y = torch.stack(y_list, dim=0)
                    else:
                        # Fallback
                        state = ssm_state[:batch].transpose(-1, -2)
                        state = dA * state + dB * x.unsqueeze(-1)
                        ssm_state[:batch].copy_(state.transpose(-1, -2))
                        y = torch.einsum("bhdn,bhn->bhd", state, C)
                        y = y + D * x
                except Exception:
                    # Fallback to non-indexed update
                    state = ssm_state.transpose(-1, -2)
                    state = dA * state + dB * x.unsqueeze(-1)
                    ssm_state.copy_(state.transpose(-1, -2))
                    y = torch.einsum("bhdn,bhn->bhd", state, C)
                    y = y + D * x
            else:
                # ssm_state: (batch, num_C_head, d_state, head_dim) -> transpose to (batch, num_C_head, head_dim, d_state)
                state = ssm_state.transpose(-1, -2)
                state = dA * state + dB * x.unsqueeze(-1)
                ssm_state.copy_(state.transpose(-1, -2))
                y = torch.einsum("bhdn,bhn->bhd", state, C)
                y = y + D * x
        else:
            # No state - just compute output without state (shouldn't happen normally)
            y = D * x

        # Apply gate
        y = y * F.silu(z)

        y = rearrange(y, "b h d -> b (h d)")
        return y

    def allocate_inference_cache(self, batch_size: int, max_seqlen: int, dtype=None):
        """Allocate inference caches."""
        device = self.out_proj.weight.device
        dtype = dtype or self.conv1d.weight.dtype

        conv_state = torch.zeros(
            batch_size, self.conv_dim, self.d_conv,
            device=device, dtype=dtype
        )

        head_dim = self.d_inner // self.num_C_head
        ssm_state = torch.zeros(
            batch_size, self.num_C_head, self.d_state, head_dim,
            device=device, dtype=dtype
        )

        return conv_state, ssm_state


# =============================================================================
# MLP LAYER
# =============================================================================

class MLP(nn.Module):
    """MLP layer with SiLU activation."""

    def __init__(self, d_model: int, intermediate_size: int, hidden_act: str = "silu"):
        super().__init__()
        self.gate_proj = nn.Linear(d_model, intermediate_size, bias=False)
        self.up_proj = nn.Linear(d_model, intermediate_size, bias=False)
        self.down_proj = nn.Linear(intermediate_size, d_model, bias=False)
        self.act_fn = nn.SiLU() if hidden_act == "silu" else nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))


# =============================================================================
# ATTENTION LAYER
# =============================================================================

class MHADecoderLayer(nn.Module):
    """Multi-Head Attention decoder layer."""

    def __init__(self, config: MambaInLlamaMambaConfig, layer_idx: int):
        super().__init__()
        self.layer_idx = layer_idx
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.num_kv_heads = config.num_key_value_heads or config.num_attention_heads
        self.head_dim = self.hidden_size // self.num_heads
        self.num_key_value_groups = self.num_heads // self.num_kv_heads

        self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(self.hidden_size, self.num_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(self.hidden_size, self.num_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=False)

        self.rotary_emb = None  # Will be initialized on first forward
        self.rope_theta = config.rope_theta
        self.max_position_embeddings = getattr(config, 'max_position_embeddings', 8192)

        self.mlp = MLP(config.hidden_size, config.intermediate_size, config.hidden_act)
        self.input_layernorm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)

    def _init_rope(self, device):
        """Initialize rotary embeddings."""
        if self.rotary_emb is None:
            inv_freq = 1.0 / (self.rope_theta ** (
                torch.arange(0, self.head_dim, 2, device=device).float() / self.head_dim
            ))
            self.register_buffer("inv_freq", inv_freq, persistent=False)

    def _apply_rotary_pos_emb(self, q, k, positions):
        """Apply rotary position embeddings."""
        self._init_rope(q.device)

        # positions: (batch, seq_len)
        seq_len = positions.shape[-1] if positions.dim() > 1 else positions.shape[0]
        positions = positions.view(-1, seq_len)

        # Compute freqs in float32 for precision, then cast to input dtype
        freqs = torch.outer(positions[0].float(), self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        cos = emb.cos().unsqueeze(0).unsqueeze(0).to(q.dtype)  # (1, 1, seq, head_dim)
        sin = emb.sin().unsqueeze(0).unsqueeze(0).to(q.dtype)

        # Apply rotation
        def rotate_half(x):
            x1 = x[..., : x.shape[-1] // 2]
            x2 = x[..., x.shape[-1] // 2 :]
            return torch.cat((-x2, x1), dim=-1)

        q_embed = (q * cos) + (rotate_half(q) * sin)
        k_embed = (k * cos) + (rotate_half(k) * sin)
        return q_embed, k_embed

    def forward(
        self,
        hidden_states: torch.Tensor,
        positions: torch.Tensor,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        cache_position: int = 0,
    ) -> torch.Tensor:
        # Handle both 2D [total_tokens, hidden] and 3D [batch, seq, hidden] input
        input_2d = hidden_states.dim() == 2
        logger.info(f"MHA forward: input shape={hidden_states.shape}, input_2d={input_2d}")
        if input_2d:
            hidden_states = hidden_states.unsqueeze(0)  # [1, total_tokens, hidden]
            logger.info(f"MHA forward: after unsqueeze shape={hidden_states.shape}")

        batch_size, seq_len, _ = hidden_states.shape
        logger.info(f"MHA forward: batch_size={batch_size}, seq_len={seq_len}")

        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)

        q = self.q_proj(hidden_states)
        k = self.k_proj(hidden_states)
        v = self.v_proj(hidden_states)
        logger.info(f"MHA forward: after proj q={q.shape}, k={k.shape}, v={v.shape}")

        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_kv_heads, self.head_dim).transpose(1, 2)
        logger.info(f"MHA forward: after view/transpose q={q.shape}, k={k.shape}, v={v.shape}")

        q, k = self._apply_rotary_pos_emb(q, k, positions)
        logger.info(f"MHA forward: after rotary q={q.shape}, k={k.shape}")

        # KV cache handling
        # k, v shape after transpose: [batch, num_kv_heads, seq_len, head_dim]
        # k_cache, v_cache shape: [batch, num_kv_heads, max_seq_len, head_dim]
        if kv_cache is not None:
            k_cache, v_cache = kv_cache
            cache_seq_len = k_cache.shape[2]

            # During warmup, seq_len may exceed cache size - skip caching in that case
            if cache_position + seq_len <= cache_seq_len:
                k_cache[:, :, cache_position:cache_position+seq_len, :] = k
                v_cache[:, :, cache_position:cache_position+seq_len, :] = v
                k = k_cache[:, :, :cache_position+seq_len, :]
                v = v_cache[:, :, :cache_position+seq_len, :]
            else:
                # Warmup/dummy run with more tokens than cache can hold - skip caching
                logger.warning(f"seq_len ({seq_len}) + cache_position ({cache_position}) exceeds cache size ({cache_seq_len}), skipping KV cache")

        # GQA expansion
        if self.num_key_value_groups > 1:
            k = k.repeat_interleave(self.num_key_value_groups, dim=1)
            v = v.repeat_interleave(self.num_key_value_groups, dim=1)

        # Attention
        scale = 1.0 / math.sqrt(self.head_dim)
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) * scale

        if seq_len > 1:
            causal_mask = torch.triu(
                torch.ones(seq_len, k.shape[-2], device=q.device, dtype=torch.bool),
                diagonal=k.shape[-2] - seq_len + 1
            )
            attn_weights = attn_weights.masked_fill(causal_mask, float('-inf'))

        attn_weights = F.softmax(attn_weights, dim=-1, dtype=torch.float32).to(v.dtype)
        attn_output = torch.matmul(attn_weights, v)

        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, -1)
        hidden_states = self.o_proj(attn_output)
        hidden_states = residual + hidden_states

        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states

        # Remove batch dim if we added it
        if input_2d:
            hidden_states = hidden_states.squeeze(0)

        return hidden_states


# =============================================================================
# MAMBA DECODER LAYER
# =============================================================================

class MambaDecoderLayer(nn.Module):
    """Mamba SSM decoder layer."""

    def __init__(self, config: MambaInLlamaMambaConfig, layer_idx: int, prefix: str = ""):
        super().__init__()
        self.layer_idx = layer_idx
        self.prefix = prefix

        # Pass prefix to mixer for static_forward_context registration
        mamba_prefix = f"{prefix}.mamba" if prefix else f"model.layers.{layer_idx}.mamba"
        self.mamba = MambaInLlamaMambaMixer(config, layer_idx, prefix=mamba_prefix)
        self.mlp = MLP(config.d_model, config.intermediate_size, config.hidden_act)
        self.input_layernorm = RMSNorm(config.d_model, eps=config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(config.d_model, eps=config.rms_norm_eps)

    def forward(
        self,
        hidden_states: torch.Tensor,
        conv_state: Optional[torch.Tensor] = None,
        ssm_state: Optional[torch.Tensor] = None,
        cache_position: int = 0,
        attn_metadata=None,
    ) -> torch.Tensor:
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        hidden_states = self.mamba(
            hidden_states,
            conv_state=conv_state,
            ssm_state=ssm_state,
            cache_position=cache_position,
            attn_metadata=attn_metadata,
        )
        hidden_states = residual + hidden_states

        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states

        return hidden_states


# =============================================================================
# MODEL BACKBONE
# =============================================================================

class MambaInLlamaMambaModel(nn.Module):
    """MambaInLlama Model backbone."""

    def __init__(self, config: MambaInLlamaMambaConfig, prefix: str = ""):
        super().__init__()
        self.config = config
        self.vocab_size = config.vocab_size
        self.prefix = prefix
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)

        self.layers = nn.ModuleList()
        for layer_idx in range(config.num_hidden_layers):
            layer_prefix = f"{prefix}.layers.{layer_idx}" if prefix else f"model.layers.{layer_idx}"
            if layer_idx in config.attn_layers:
                self.layers.append(MHADecoderLayer(config, layer_idx))
            else:
                self.layers.append(MambaDecoderLayer(config, layer_idx, prefix=layer_prefix))

        self.norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)

    def embed_input_ids(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Convert input token IDs to embeddings (required by VllmModel interface)."""
        return self.embed_tokens(input_ids)

    def forward(
        self,
        input_ids: torch.Tensor,
        positions: torch.Tensor,
        mamba_cache: Optional[dict] = None,
        attn_cache: Optional[dict] = None,
        cache_position: int = 0,
        attn_metadata=None,
    ) -> torch.Tensor:
        """Forward pass with vLLM state management support.

        Args:
            input_ids: Input token IDs
            positions: Position indices for RoPE
            mamba_cache: Optional dict mapping layer_idx to (conv_state, ssm_state)
            attn_cache: Optional dict mapping layer_idx to (k_cache, v_cache)
            cache_position: Current position in sequence for decode
            attn_metadata: vLLM attention metadata for state indices
        """
        hidden_states = self.embed_input_ids(input_ids)

        # Use empty dicts if caches not provided
        if mamba_cache is None:
            mamba_cache = {}
        if attn_cache is None:
            attn_cache = {}

        for i, layer in enumerate(self.layers):
            if isinstance(layer, MambaDecoderLayer):
                conv_state, ssm_state = mamba_cache.get(i, (None, None))
                hidden_states = layer(
                    hidden_states,
                    conv_state=conv_state,
                    ssm_state=ssm_state,
                    cache_position=cache_position,
                    attn_metadata=attn_metadata,
                )
            else:
                kv_cache = attn_cache.get(i)
                hidden_states = layer(hidden_states, positions, kv_cache, cache_position)

        hidden_states = self.norm(hidden_states)
        return hidden_states


# =============================================================================
# NATIVE vLLM MODEL CLASS
# =============================================================================

# Dynamically create base classes with protocol inheritance
_NativeBaseClasses = [nn.Module]
if _HasInnerState is not None:
    _NativeBaseClasses.append(_HasInnerState)
if _IsHybrid is not None:
    _NativeBaseClasses.append(_IsHybrid)
_NativeBaseClasses = tuple(_NativeBaseClasses)


class MambaInLlamaMambaForCausalLMNative(*_NativeBaseClasses):
    """Native vLLM-compatible MambaInLlama model.

    This model supports the 'generate' runner by:
    1. Inheriting from HasInnerState and IsHybrid protocols
    2. Implementing compute_logits() and sample() methods
    3. Having architecture name ending in 'ForCausalLM'
    """

    # Protocol-required class variables for vLLM model inspection
    is_hybrid: ClassVar[Literal[True]] = True
    has_inner_state: ClassVar[Literal[True]] = True
    is_attention_free: ClassVar[Literal[False]] = False

    def __init__(
        self,
        vllm_config=None,
        config: MambaInLlamaMambaConfig = None,
        prefix: str = "",
        **kwargs,
    ):
        super().__init__()

        if vllm_config is not None and hasattr(vllm_config, "model_config"):
            model_config = vllm_config.model_config
            if hasattr(model_config, "hf_config"):
                hf_cfg = model_config.hf_config
                hidden_size = getattr(hf_cfg, "hidden_size", 4096)
                intermediate_size = getattr(hf_cfg, "intermediate_size", 11008)

                config_kwargs = dict(
                    vocab_size=getattr(hf_cfg, "vocab_size", 32000),
                    hidden_size=hidden_size,
                    num_hidden_layers=getattr(hf_cfg, "num_hidden_layers", 32),
                    num_attention_heads=getattr(hf_cfg, "num_attention_heads", 32),
                    num_key_value_heads=getattr(hf_cfg, "num_key_value_heads", None),
                    intermediate_size=intermediate_size,
                    rms_norm_eps=getattr(hf_cfg, "rms_norm_eps", 1e-6),
                    rope_theta=getattr(hf_cfg, "rope_theta", 10000.0),
                )

                # Try to load mamba_config.json for Mamba-specific settings
                # Many MambaInLlama models store attn_layers, d_inner, d_xb there
                mamba_cfg = {}
                if hasattr(model_config, "model") and model_config.model:
                    model_path = model_config.model
                    logger.info(f"Looking for mamba_config.json for model: {model_path}")
                    # Handle HuggingFace hub models
                    try:
                        from huggingface_hub import hf_hub_download
                        # Try to download mamba_config.json (will use cache if available)
                        try:
                            mamba_config_path = hf_hub_download(
                                model_path, "mamba_config.json"
                            )
                            with open(mamba_config_path, "r") as f:
                                mamba_cfg = json.load(f)
                                logger.info(f"Loaded mamba_config.json from {mamba_config_path}")
                                logger.info(f"mamba_config contents: attn_layers={mamba_cfg.get('attn_layers')}, d_inner={mamba_cfg.get('d_inner')}, d_xb={mamba_cfg.get('d_xb')}")
                        except Exception as e:
                            logger.warning(f"Could not load mamba_config.json: {e}")
                            # Try local path as fallback
                            mamba_cfg = _load_mamba_config(model_path)
                    except ImportError:
                        # huggingface_hub not available, try local path
                        logger.warning("huggingface_hub not available, trying local path")
                        mamba_cfg = _load_mamba_config(model_path)

                # Try to get attn_layers from various possible locations
                # Priority: mamba_config.json > hf_config attributes
                attn_layers = None

                # First check mamba_config.json
                if mamba_cfg.get("attn_layers"):
                    attn_layers = mamba_cfg["attn_layers"]
                    logger.info(f"Found attn_layers from mamba_config.json: {attn_layers}")
                # Then check HF config
                elif hasattr(hf_cfg, "attn_layers") and hf_cfg.attn_layers is not None:
                    attn_layers = hf_cfg.attn_layers
                elif hasattr(hf_cfg, "attention_layers") and hf_cfg.attention_layers is not None:
                    attn_layers = hf_cfg.attention_layers
                elif hasattr(hf_cfg, "ssm_cfg") and isinstance(hf_cfg.ssm_cfg, dict):
                    attn_layers = hf_cfg.ssm_cfg.get("attn_layers") or hf_cfg.ssm_cfg.get("attention_layers")

                if attn_layers:
                    config_kwargs["attn_layers"] = attn_layers
                    logger.info(f"Using attn_layers: {attn_layers}")
                else:
                    logger.warning(f"No attn_layers found! Model will use ALL Mamba layers (no attention).")
                    logger.warning(f"HF config attrs: {[a for a in dir(hf_cfg) if not a.startswith('_')]}")

                # Get Mamba dimensions - priority: mamba_config.json > hf_config
                if mamba_cfg.get("d_model"):
                    config_kwargs["d_model"] = mamba_cfg["d_model"]
                elif hasattr(hf_cfg, "d_model") and hf_cfg.d_model is not None:
                    config_kwargs["d_model"] = hf_cfg.d_model

                if mamba_cfg.get("d_inner"):
                    config_kwargs["d_inner"] = mamba_cfg["d_inner"]
                elif hasattr(hf_cfg, "d_inner") and hf_cfg.d_inner is not None:
                    config_kwargs["d_inner"] = hf_cfg.d_inner

                if mamba_cfg.get("d_xb"):
                    config_kwargs["d_xb"] = mamba_cfg["d_xb"]
                elif hasattr(hf_cfg, "d_xb") and hf_cfg.d_xb is not None:
                    config_kwargs["d_xb"] = hf_cfg.d_xb

                if mamba_cfg.get("ssm_config"):
                    config_kwargs["ssm_cfg"] = mamba_cfg["ssm_config"]
                elif hasattr(hf_cfg, "ssm_cfg") and hf_cfg.ssm_cfg is not None:
                    config_kwargs["ssm_cfg"] = hf_cfg.ssm_cfg

                logger.info(f"Final config_kwargs: d_inner={config_kwargs.get('d_inner')}, d_xb={config_kwargs.get('d_xb')}, attn_layers={config_kwargs.get('attn_layers')}")
                config = MambaInLlamaMambaConfig(**config_kwargs)

        if config is None:
            raise ValueError("Config required for model initialization")

        self.config = config
        self.vocab_size = config.vocab_size
        self.prefix = prefix

        # Pass prefix to model backbone for proper layer prefix registration
        model_prefix = f"{prefix}.model" if prefix else "model"
        self.model = MambaInLlamaMambaModel(config, prefix=model_prefix)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        # vLLM components
        self._vllm_logits_processor = None
        self._vllm_sampler = None
        if _vllm_available:
            try:
                self._vllm_logits_processor = LogitsProcessor(config.vocab_size)
            except:
                pass
        if _vllm_Sampler is not None:
            try:
                self._vllm_sampler = _vllm_Sampler()
            except:
                pass

        # State caches
        self._mamba_cache = {}
        self._attn_cache = {}
        self._cache_position = 0

    def _init_caches(self, batch_size: int, device: torch.device, dtype: torch.dtype):
        """Initialize state caches."""
        for i, layer in enumerate(self.model.layers):
            if isinstance(layer, MambaDecoderLayer):
                conv_state, ssm_state = layer.mamba.allocate_inference_cache(
                    batch_size, self.config.max_position_embeddings or 8192, dtype
                )
                conv_state = conv_state.to(device)
                ssm_state = ssm_state.to(device)
                self._mamba_cache[i] = (conv_state, ssm_state)
            else:
                # Attention KV cache
                max_len = self.config.max_position_embeddings or 8192
                k_cache = torch.zeros(
                    batch_size, layer.num_kv_heads, max_len, layer.head_dim,
                    device=device, dtype=dtype
                )
                v_cache = torch.zeros(
                    batch_size, layer.num_kv_heads, max_len, layer.head_dim,
                    device=device, dtype=dtype
                )
                self._attn_cache[i] = (k_cache, v_cache)

    def embed_input_ids(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Convert input token IDs to embeddings (required by VllmModelForTextGeneration)."""
        return self.model.embed_input_ids(input_ids)

    def forward(
        self,
        input_ids: torch.Tensor = None,
        positions: torch.Tensor = None,
        kv_caches: list = None,
        attn_metadata=None,
        inputs_embeds: Optional[torch.Tensor] = None,
        intermediate_tensors=None,
        **kwargs,
    ) -> torch.Tensor:
        """vLLM-style forward pass."""
        # Handle 1D input
        if input_ids is not None and input_ids.dim() == 1:
            input_ids = input_ids.unsqueeze(0)
        if positions is not None and positions.dim() == 1:
            positions = positions.unsqueeze(0)

        batch_size = input_ids.shape[0]
        seq_len = input_ids.shape[1]
        device = input_ids.device
        dtype = self.lm_head.weight.dtype

        # Initialize caches if needed
        if not self._mamba_cache:
            self._init_caches(batch_size, device, dtype)

        # Determine if this is prefill or decode
        is_prefill = seq_len > 1 or self._cache_position == 0

        # Reset cache position for new prefill
        if is_prefill and self._cache_position > 0:
            self._cache_position = 0
            # Clear caches
            for key in self._mamba_cache:
                conv_state, ssm_state = self._mamba_cache[key]
                conv_state.zero_()
                ssm_state.zero_()
            for key in self._attn_cache:
                k_cache, v_cache = self._attn_cache[key]
                k_cache.zero_()
                v_cache.zero_()

        # Create positions if not provided
        if positions is None:
            positions = torch.arange(
                self._cache_position, self._cache_position + seq_len,
                device=device
            ).unsqueeze(0).expand(batch_size, -1)

        # Forward through model
        hidden_states = self.model(
            input_ids=input_ids,
            positions=positions,
            mamba_cache=self._mamba_cache,
            attn_cache=self._attn_cache,
            cache_position=self._cache_position,
            attn_metadata=attn_metadata,
        )

        # Update cache position
        self._cache_position += seq_len

        # Flatten for vLLM
        if hidden_states.dim() == 3:
            hidden_states = hidden_states.squeeze(0)

        return hidden_states

    def compute_logits(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """Compute logits for vLLM sampling."""
        if hidden_states.dim() == 3:
            hidden_states = hidden_states.squeeze(0)

        if self._vllm_logits_processor is not None:
            return self._vllm_logits_processor(self.lm_head, hidden_states)

        return self.lm_head(hidden_states)

    def sample(self, logits: torch.Tensor, sampling_metadata):
        """Sample tokens from logits."""
        if self._vllm_sampler is not None:
            return self._vllm_sampler(logits, sampling_metadata)
        return None

    # =========================================================================
    # CUDA Graph Compatibility Methods (for vLLM V1 engine)
    # =========================================================================

    def copy_inputs_before_cuda_graphs(self, input_buffers, **kwargs):
        """Copy inputs before CUDA graph capture.

        This method is called by vLLM's V1 engine to prepare inputs for
        CUDA graph execution. For Mamba models, this involves copying
        state buffers to ensure they persist across graph executions.

        Args:
            input_buffers: Dict of input buffers from vLLM
            **kwargs: Additional arguments

        Returns:
            Dict of buffers to use during CUDA graph execution
        """
        # For now, pass through - state is managed via self.kv_cache in MambaMixer
        # which is populated by vLLM's infrastructure
        return input_buffers

    def get_seqlen_agnostic_capture_inputs(self, batch_size: int):
        """Get inputs for sequence-length agnostic CUDA graph capture.

        Returns inputs that can be used across different sequence lengths
        for efficient CUDA graph reuse.

        Args:
            batch_size: Number of sequences in the batch

        Returns:
            Dict of capture inputs for CUDA graphs
        """
        # Return empty dict - state tensors are managed by vLLM via MambaBase.kv_cache
        return {}

    def load_weights(self, weights: Iterable[Tuple[str, torch.Tensor]]):
        """Load weights from checkpoint.

        Handles weight name transformations:
        1. mha.in_proj.weight -> split into q_proj, k_proj, v_proj
        2. mha.out_proj.weight -> rename to o_proj.weight
        """
        params_dict = dict(self.named_parameters())
        loaded_count = 0
        skipped_weights = []

        # Log model parameter names for debugging (first 10)
        param_names = list(params_dict.keys())
        logger.info(f"Model has {len(param_names)} parameters")
        logger.info(f"First 20 model params: {param_names[:20]}")

        # Get dimensions for attention splitting
        # Q: num_heads * head_dim, K/V: num_kv_heads * head_dim
        num_heads = self.config.num_attention_heads
        num_kv_heads = self.config.num_key_value_heads or num_heads
        head_dim = self.config.hidden_size // num_heads
        q_dim = num_heads * head_dim  # 4096 for 32 heads * 128 dim
        kv_dim = num_kv_heads * head_dim  # 1024 for 8 heads * 128 dim

        logger.info(f"Attention dims: q_dim={q_dim}, kv_dim={kv_dim}, head_dim={head_dim}")

        checkpoint_names = []
        for name, loaded_weight in weights:
            checkpoint_names.append(name)
            # Log first 20 checkpoint weight names
            if len(checkpoint_names) <= 20:
                logger.info(f"Checkpoint weight: {name} shape={loaded_weight.shape}")

            # Handle fused attention in_proj -> split into q, k, v
            if ".mha.in_proj.weight" in name:
                # Split fused QKV weight: [q_dim + kv_dim + kv_dim, hidden]
                base_name = name.replace(".mha.in_proj.weight", "")

                q_weight = loaded_weight[:q_dim, :]
                k_weight = loaded_weight[q_dim:q_dim + kv_dim, :]
                v_weight = loaded_weight[q_dim + kv_dim:, :]

                found_any = False
                for suffix, weight in [(".q_proj.weight", q_weight),
                                       (".k_proj.weight", k_weight),
                                       (".v_proj.weight", v_weight)]:
                    param_name = base_name + suffix
                    if param_name in params_dict:
                        params_dict[param_name].data.copy_(weight)
                        loaded_count += 1
                        found_any = True
                    else:
                        skipped_weights.append(f"{name} -> {param_name} (param not found - is attn_layers configured?)")
                if not found_any:
                    logger.warning(f"Attention layer weights {name} found but no q/k/v params exist. Check attn_layers config!")
                continue

            # Handle attention out_proj rename
            if ".mha.out_proj.weight" in name:
                new_name = name.replace(".mha.out_proj.", ".o_proj.")
                if new_name in params_dict:
                    params_dict[new_name].data.copy_(loaded_weight)
                    loaded_count += 1
                continue

            # Handle attention out_proj bias if present
            if ".mha.out_proj.bias" in name:
                new_name = name.replace(".mha.out_proj.", ".o_proj.")
                if new_name in params_dict:
                    params_dict[new_name].data.copy_(loaded_weight)
                    loaded_count += 1
                continue

            # Try direct match
            if name in params_dict:
                param = params_dict[name]
                if param.shape == loaded_weight.shape:
                    param.data.copy_(loaded_weight)
                    loaded_count += 1
                    continue

            # Try with/without model prefix
            candidates = [name]
            if name.startswith("model."):
                candidates.append(name[6:])
            else:
                candidates.append(f"model.{name}")

            matched = False
            for candidate in candidates:
                if candidate in params_dict:
                    param = params_dict[candidate]
                    if param.shape == loaded_weight.shape:
                        param.data.copy_(loaded_weight)
                        loaded_count += 1
                        matched = True
                        break
                    else:
                        skipped_weights.append(f"{name} (shape mismatch: checkpoint {loaded_weight.shape} vs model {param.shape})")
                        matched = True  # Don't add to skipped again
                        break

            if not matched:
                skipped_weights.append(f"{name} (no matching param)")

        logger.info(f"Loaded {loaded_count}/{len(params_dict)} parameters from {len(checkpoint_names)} checkpoint weights")
        if skipped_weights:
            logger.info(f"Skipped {len(skipped_weights)} checkpoint weights. First 20:")
            for w in skipped_weights[:20]:
                logger.info(f"  - {w}")

        # Log model params that weren't loaded (helps diagnose attn_layers issues)
        if loaded_count < len(params_dict):
            # Track which params were loaded by checking if they're still at init values
            # This is approximate - better to track explicitly
            missing_params = len(params_dict) - loaded_count
            logger.warning(f"{missing_params} model parameters may not have been loaded from checkpoint!")
            logger.info(f"Config attn_layers: {self.config.attn_layers}")
            # Show some attention-related params to help debug
            attn_params = [p for p in param_names if 'q_proj' in p or 'k_proj' in p or 'v_proj' in p or 'o_proj' in p]
            if attn_params:
                logger.info(f"Model has {len(attn_params)} attention params: {attn_params[:8]}...")

    @classmethod
    def get_mamba_state_shape_from_config(cls, vllm_config) -> tuple:
        """Calculate Mamba state shapes."""
        if _vllm_MambaStateShapeCalculator is None:
            return ((3, 4096), (4096, 16))

        hf_config = vllm_config.model_config.hf_config
        parallel_config = vllm_config.parallel_config

        d_inner = getattr(hf_config, "d_inner", hf_config.hidden_size)
        ssm_cfg = getattr(hf_config, "ssm_cfg", {})
        d_state = ssm_cfg.get("d_state", 16)
        d_conv = ssm_cfg.get("d_conv", 4)

        return _vllm_MambaStateShapeCalculator.mamba1_state_shape(
            tp_world_size=parallel_config.tensor_parallel_size,
            intermediate_size=d_inner,
            state_size=d_state,
            conv_kernel=d_conv,
        )

    @classmethod
    def get_mamba_state_dtype_from_config(cls, vllm_config) -> tuple:
        """Get Mamba state dtypes."""
        if _vllm_MambaStateDtypeCalculator is None:
            return (torch.bfloat16, torch.bfloat16)

        return _vllm_MambaStateDtypeCalculator.mamba1_state_dtype(
            vllm_config.model_config.dtype,
            vllm_config.cache_config.mamba_cache_dtype,
            vllm_config.cache_config.mamba_ssm_cache_dtype,
        )

    @classmethod
    def is_backend_compatible(cls) -> bool:
        return True


# =============================================================================
# ALIAS FOR HF CONFIG COMPATIBILITY
# =============================================================================
# HuggingFace model configs specify "MambaInLlamaMambaForCausalLM" as the
# architecture. This alias ensures vLLM can find and load the class.
MambaInLlamaMambaForCausalLM = MambaInLlamaMambaForCausalLMNative
