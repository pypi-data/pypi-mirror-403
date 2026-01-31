"""Rotary positional embeddings (RoPE) for transformer models.

This module implements Rotary Position Embedding (RoPE), a method that encodes
position information by rotating query and key vectors in the embedding space.
RoPE offers improved extrapolation to longer sequences compared to absolute
position embeddings and is efficiently implemented using precomputed rotation
matrices cached in buffers.

Reference:
    Su et al. (2024): "RoFormer: Enhanced Transformer with Rotary Position Embedding"
    https://arxiv.org/abs/2104.09864

Typical usage:
    >>> rope = RotaryPositionalEmbedding(dim=64, max_seq_len=512)
    >>> q = torch.randn(2, 8, 10, 64)  # (batch, heads, seq_len, dim)
    >>> k = torch.randn(2, 8, 10, 64)
    >>> q_rot, k_rot = rope(q, k)
"""

from typing import Tuple
import torch
import torch.nn as nn

from ..config import Config, get_default_config


class RotaryPositionalEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE) for queries and keys in attention.

    Applies rotation matrices to query and key embeddings based on their positions
    in the sequence. Rotation angles are derived from sinusoidal basis frequencies,
    enabling the model to encode relative position information. Cosine and sine
    matrices are precomputed and cached to improve efficiency.

    Args:
        dim (int): Embedding dimension. Must be even.
        max_seq_len (int, optional): Maximum sequence length to precompute rotations for.
            Defaults to 2048. Cache is dynamically extended if longer sequences are encountered.
        base (float, optional): Base for the geometric progression of rotation frequencies.
            Defaults to 10000.0.

    Attributes:
        dim (int): Embedding dimension.
        max_seq_len (int): Maximum precomputed sequence length.
        base (float): Frequency base.
        inv_freq (torch.Tensor): Inverse frequencies for rotation angles, shape (dim // 2,).
        cos_cache (torch.Tensor): Precomputed cosine values for rotations.
        sin_cache (torch.Tensor): Precomputed sine values for rotations.
        cached_seq_len (int): Length of the currently cached rotation matrices.

    Raises:
        RuntimeError: If embedding dimension is odd (RoPE requires even dimensions).
    """

    def __init__(
        self,
        dim: int = None,
        max_seq_len: int = None,
        base: float = 10000.0,
        config: Config = None,
    ) -> None:
        super().__init__()
        cfg = config if config is not None else get_default_config()
        dim = dim if dim is not None else cfg.d_model
        max_seq_len = max_seq_len if max_seq_len is not None else cfg.max_seq_length
        self.dim = dim
        self.max_seq_len = max_seq_len
        self.base = base
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self._build_cache(max_seq_len)

    def _build_cache(self, seq_len: int) -> None:
        """Precompute cosine and sine rotation matrices for a given sequence length.

        Generates rotation frequency pairs and computes their cosine and sine values,
        storing them as buffers for efficient reuse during forward passes. Called
        automatically during initialization and extended if a longer sequence is
        encountered during inference.

        Args:
            seq_len (int): Sequence length to precompute rotations for.
        """
        positions = torch.arange(seq_len).float()
        inv_freq_tensor = getattr(self, "inv_freq")
        freqs = torch.outer(positions, inv_freq_tensor)
        emb = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer("cos_cache", emb.cos(), persistent=False)
        self.register_buffer("sin_cache", emb.sin(), persistent=False)
        self.cached_seq_len = seq_len

    def _rotate_half(self, x: torch.Tensor) -> torch.Tensor:
        """Rotate embedding by 90 degrees in the complex plane.

        Splits the embedding into two halves and swaps with negation to achieve
        a 90-degree rotation: [x1, x2] -> [-x2, x1]. This rotation is applied
        as part of the RoPE mechanism.

        Args:
            x (torch.Tensor): Input tensor of shape (..., dim).

        Returns:
            torch.Tensor: Rotated tensor of the same shape as input.
        """
        x1, x2 = x.chunk(2, dim=-1)
        return torch.cat([-x2, x1], dim=-1)

    def apply_rotary_pos_emb(
        self, q: torch.Tensor, k: torch.Tensor, seq_len: int
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Apply rotary embeddings to query and key tensors.

        Multiplies precomputed rotation matrices with query and key embeddings
        to encode position information. Dynamically extends the cache if the
        input sequence length exceeds the currently cached length.

        Args:
            q (torch.Tensor): Query tensor of shape (batch_size, seq_len, dim)
                or (batch_size, num_heads, seq_len, dim).
            k (torch.Tensor): Key tensor of shape (batch_size, seq_len, dim)
                or (batch_size, num_heads, seq_len, dim).
            seq_len (int): Sequence length to use for rotation matrices.

        Returns:
            Tuple[torch.Tensor, torch.Tensor]: Rotated query and key tensors,
                same shape as inputs.
        """
        if seq_len > self.cached_seq_len:
            self._build_cache(seq_len)
        cos_cache = getattr(self, "cos_cache")
        sin_cache = getattr(self, "sin_cache")
        cos = cos_cache[:seq_len]
        sin = sin_cache[:seq_len]
        if q.dim() == 4:
            cos = cos.unsqueeze(0).unsqueeze(0)
            sin = sin.unsqueeze(0).unsqueeze(0)
        else:
            cos = cos.unsqueeze(0)
            sin = sin.unsqueeze(0)
        q_rot = q * cos + self._rotate_half(q) * sin
        k_rot = k * cos + self._rotate_half(k) * sin
        return q_rot, k_rot

    def forward(
        self, q: torch.Tensor, k: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Apply rotary positional embeddings to query and key tensors.

        Infers sequence length from input tensors and applies rotary embeddings.
        Supports both 3D (batch_size, seq_len, dim) and 4D (batch_size, num_heads,
        seq_len, dim) tensor formats.

        Args:
            q (torch.Tensor): Query embeddings.
            k (torch.Tensor): Key embeddings.

        Returns:
            Tuple[torch.Tensor, torch.Tensor]: Rotated query and key tensors.
        """
        seq_len = q.shape[-2] if q.dim() == 4 else q.shape[1]
        return self.apply_rotary_pos_emb(q, k, seq_len)


class RoPEEmbedding(nn.Module):
    """Wrapper for Rotary Position Embeddings applied to partial dimensions.

    Applies RoPE to the first even portion of embeddings while preserving
    remaining dimensions. Useful for integration with existing models that
    use embeddings with odd dimensions or custom split strategies.

    Args:
        d_model (int): Total embedding dimension.
        max_seq_len (int, optional): Maximum sequence length. Defaults to 2048.

    Attributes:
        rope (RotaryPositionalEmbedding): Internal RoPE instance applied to even dimensions.
    """

    def __init__(
        self,
        d_model: int = None,
        max_seq_len: int = None,
        config: Config = None,
    ):
        super().__init__()
        cfg = config if config is not None else get_default_config()
        d_model = d_model if d_model is not None else cfg.d_model
        max_seq_len = max_seq_len if max_seq_len is not None else cfg.max_seq_length
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.rope = RotaryPositionalEmbedding(d_model, max_seq_len, config=cfg)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply RoPE to first even dimensions of embedding, preserving the rest.

        Splits the input embedding into an even portion (to which RoPE is applied)
        and a remainder portion (left unchanged). Concatenates the results.

        Args:
            x (torch.Tensor): Input embedding of shape (..., d_model).

        Returns:
            torch.Tensor: Embedding with RoPE applied to first even dimensions,
                same shape as input.
        """
        mid = x.shape[-1] // 2
        x_first = x[..., : mid * 2]
        x_rot, _ = self.rope(x_first, x_first)
        if x.shape[-1] > mid * 2:
            x_rot = torch.cat([x_rot, x[..., mid * 2 :]], dim=-1)
        return x_rot
