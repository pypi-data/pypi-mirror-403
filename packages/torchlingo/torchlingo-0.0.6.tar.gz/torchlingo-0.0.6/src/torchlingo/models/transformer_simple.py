"""Simple transformer-based sequence-to-sequence model with RoPE embeddings.

This module implements a basic transformer encoder-decoder architecture for
sequence-to-sequence tasks such as neural machine translation. It uses rotary
position embeddings (RoPE) for efficient position encoding and PyTorch's built-in
Transformer layers with batch-first computation.

The model automatically generates causal masks for the decoder and padding masks
for both encoder and decoder based on vocabulary padding indices.

Typical usage:
    >>> model = SimpleTransformer(src_vocab_size=1000, tgt_vocab_size=1000)
    >>> src = torch.randint(0, 1000, (2, 10))
    >>> tgt = torch.randint(0, 1000, (2, 15))
    >>> output = model(src, tgt)
    >>> output.shape
    torch.Size([2, 15, 1000])

References:
    - Vaswani et al. (2017): "Attention is All You Need"
    - Su et al. (2024): "RoFormer: Enhanced Transformer with Rotary Position Embedding"
"""

from typing import Optional, Tuple
import math
import torch
import torch.nn as nn
from ..config import Config, get_default_config
from .positional import RoPEEmbedding


class SimpleTransformer(nn.Module):
    """Transformer encoder-decoder model with rotary positional embeddings.

    A standard transformer architecture combining an encoder and decoder, each
    composed of stacked multi-head self-attention and feed-forward layers. Uses
    RoPE for position encoding, which improves extrapolation to longer sequences.
    Embeddings are scaled by sqrt(d_model) to prevent vanishing gradients.

    Args:
        src_vocab_size (int): Size of the source vocabulary.
        tgt_vocab_size (int): Size of the target vocabulary.
        d_model (int, optional): Model hidden dimension. Defaults to 512.
        n_heads (int, optional): Number of attention heads. Defaults to 8.
        num_encoder_layers (int, optional): Number of encoder transformer blocks. Defaults to 6.
        num_decoder_layers (int, optional): Number of decoder transformer blocks. Defaults to 6.
        d_ff (int, optional): Feed-forward inner dimension. Defaults to 2048.
        max_seq_length (int, optional): Maximum sequence length for RoPE cache. Defaults to 512.
        dropout (float, optional): Dropout rate throughout the model. Defaults to 0.1.
        pad_idx (int, optional): Padding token index. Falls back to config.pad_idx.
        config (Config, optional): Configuration object. Defaults to default config.

    Attributes:
        d_model (int): Model dimension.
        max_seq_length (int): Maximum sequence length.
        pad_idx (int): Resolved padding index.
        src_tok_emb (nn.Embedding): Source token embedding layer.
        tgt_tok_emb (nn.Embedding): Target token embedding layer.
        rope (RoPEEmbedding): Rotary position embedding module.
        transformer (nn.Transformer): PyTorch transformer with encoder and decoder.
        generator (nn.Linear): Output projection to target vocabulary logits.
    """

    def __init__(
        self,
        src_vocab_size: int,
        tgt_vocab_size: int,
        d_model: Optional[int] = None,
        n_heads: Optional[int] = None,
        num_encoder_layers: Optional[int] = None,
        num_decoder_layers: Optional[int] = None,
        d_ff: Optional[int] = None,
        max_seq_length: Optional[int] = None,
        dropout: Optional[float] = None,
        pad_idx: Optional[int] = None,
        config: Optional[Config] = None,
    ) -> None:
        super().__init__()
        cfg = config if config is not None else get_default_config()
        self.pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx
        d_model = d_model if d_model is not None else cfg.d_model
        n_heads = n_heads if n_heads is not None else cfg.n_heads
        num_encoder_layers = (
            num_encoder_layers
            if num_encoder_layers is not None
            else cfg.num_encoder_layers
        )
        num_decoder_layers = (
            num_decoder_layers
            if num_decoder_layers is not None
            else cfg.num_decoder_layers
        )
        d_ff = d_ff if d_ff is not None else cfg.d_ff
        max_seq_length = (
            max_seq_length if max_seq_length is not None else cfg.max_seq_length
        )
        dropout = dropout if dropout is not None else cfg.dropout

        self.d_model = d_model
        self.max_seq_length = max_seq_length
        self.dropout = dropout

        self.src_tok_emb = nn.Embedding(
            src_vocab_size, d_model, padding_idx=self.pad_idx
        )
        self.tgt_tok_emb = nn.Embedding(
            tgt_vocab_size, d_model, padding_idx=self.pad_idx
        )
        self.rope = RoPEEmbedding(d_model, max_seq_length)
        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=n_heads,
            num_encoder_layers=num_encoder_layers,
            num_decoder_layers=num_decoder_layers,
            dim_feedforward=d_ff,
            dropout=dropout,
            batch_first=True,
        )
        self.generator = nn.Linear(d_model, tgt_vocab_size)
        self._init_parameters()

    def _init_parameters(self) -> None:
        """Initialize linear layer weights using Xavier uniform and zero biases.

        Applies Xavier uniform initialization to all linear layer weights and
        zero initialization to biases. This helps stabilize training by preventing
        saturated activations early in training.
        """
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def encode(
        self, src: torch.Tensor, src_key_padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Encode source sequence using the transformer encoder.

        Embeds and applies rotary position embeddings to source tokens, then passes
        through the transformer encoder stack. Position information is encoded in
        the embedding rotations, not as additional position embeddings.

        Args:
            src (torch.Tensor): Source token indices of shape (batch_size, src_len).
            src_key_padding_mask (torch.Tensor, optional): Boolean mask where True indicates
                padding positions to ignore. Shape (batch_size, src_len). Defaults to None.

        Returns:
            torch.Tensor: Encoded source representation of shape (batch_size, src_len, d_model).
        """
        src_emb = self._embed(src, is_src=True)
        return self.transformer.encoder(
            src_emb, src_key_padding_mask=src_key_padding_mask
        )

    def decode(
        self,
        tgt: torch.Tensor,
        memory: torch.Tensor,
        src_key_padding_mask: Optional[torch.Tensor] = None,
        tgt_key_padding_mask: Optional[torch.Tensor] = None,
        tgt_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Decode target sequence using the transformer decoder and encoder output.

        Embeds and applies rotary position embeddings to target tokens, then passes
        them through the transformer decoder with cross-attention to the encoder output.
        The decoder is typically run with a causal mask to prevent attending to future tokens.

        Args:
            tgt (torch.Tensor): Target token indices of shape (batch_size, tgt_len).
            memory (torch.Tensor): Encoded source from encoder output, shape (batch_size, src_len, d_model).
            src_key_padding_mask (torch.Tensor, optional): Mask for encoder output padding.
                Shape (batch_size, src_len). Defaults to None.
            tgt_key_padding_mask (torch.Tensor, optional): Mask for target padding.
                Shape (batch_size, tgt_len). Defaults to None.
            tgt_mask (torch.Tensor, optional): Causal mask for target self-attention.
                Shape (tgt_len, tgt_len). Defaults to None.

        Returns:
            torch.Tensor: Decoder output logits of shape (batch_size, tgt_len, tgt_vocab_size).
        """
        tgt_emb = self._embed(tgt, is_src=False)
        dec = self.transformer.decoder(
            tgt_emb,
            memory,
            tgt_mask=tgt_mask,
            memory_key_padding_mask=src_key_padding_mask,
            tgt_key_padding_mask=tgt_key_padding_mask,
        )
        return self.generator(dec)

    def forward(
        self,
        src: torch.Tensor,
        tgt: torch.Tensor,
        src_key_padding_mask: Optional[torch.Tensor] = None,
        tgt_key_padding_mask: Optional[torch.Tensor] = None,
        tgt_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Encode source and decode target in a single forward pass.

        Automatically generates padding and causal masks if not provided.
        Calls encode() to process source sequences, then decode() to generate
        target sequence predictions.

        Args:
            src (torch.Tensor): Source token indices of shape (batch_size, src_len).
            tgt (torch.Tensor): Target token indices of shape (batch_size, tgt_len).
            src_key_padding_mask (torch.Tensor, optional): Boolean mask for source padding.
                If None, generated automatically from padding index. Defaults to None.
            tgt_key_padding_mask (torch.Tensor, optional): Boolean mask for target padding.
                If None, generated automatically from padding index. Defaults to None.
            tgt_mask (torch.Tensor, optional): Causal mask for target self-attention.
                If None, generated automatically. Defaults to None.

        Returns:
            torch.Tensor: Logits of shape (batch_size, tgt_len, tgt_vocab_size).
        """
        if src_key_padding_mask is None:
            src_key_padding_mask = create_key_padding_mask(src, pad_idx=self.pad_idx)
        if tgt_key_padding_mask is None:
            tgt_key_padding_mask = create_key_padding_mask(tgt, pad_idx=self.pad_idx)
        if tgt_mask is None:
            tgt_mask = create_causal_mask(tgt.size(1), tgt.device)
        memory = self.encode(src, src_key_padding_mask)
        return self.decode(
            tgt,
            memory,
            src_key_padding_mask=src_key_padding_mask,
            tgt_key_padding_mask=tgt_key_padding_mask,
            tgt_mask=tgt_mask,
        )

    def _embed(self, tokens: torch.Tensor, is_src: bool) -> torch.Tensor:
        """Embed and scale tokens, then apply rotary positional embeddings.

        Looks up token embeddings, scales them by sqrt(d_model), and applies RoPE.
        This prevents embedding magnitude from dominating the scaled dot-product
        attention mechanism.

        Args:
            tokens (torch.Tensor): Token indices of shape (batch_size, seq_len).
            is_src (bool): If True, use source embeddings; otherwise use target embeddings.

        Returns:
            torch.Tensor: Embedded and rotated tokens of shape (batch_size, seq_len, d_model).
        """
        tok_emb = self.src_tok_emb(tokens) if is_src else self.tgt_tok_emb(tokens)
        tok_emb = tok_emb * math.sqrt(self.d_model)
        return self.rope(tok_emb)


def create_key_padding_mask(
    seq: torch.Tensor,
    pad_idx: Optional[int] = None,
    config: Optional[Config] = None,
) -> torch.Tensor:
    """Create a key padding mask from a sequence.

    Identifies padding token positions in a sequence for use in attention masks.
    Padding masks are boolean tensors where True indicates positions to mask (ignore).

    Args:
        seq (torch.Tensor): Token indices of shape (batch_size, seq_len).
        pad_idx (int, optional): Padding token index. Falls back to config.pad_idx.
        config (Config, optional): Configuration object. Defaults to default config.

    Returns:
        torch.Tensor: Boolean mask of shape (batch_size, seq_len) where True indicates padding positions.
    """
    cfg = config if config is not None else get_default_config()
    pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx
    return seq == pad_idx


def create_causal_mask(seq_len: int, device: torch.device) -> torch.Tensor:
    """Create a causal (autoregressive) mask for transformer decoder.

    Generates an upper triangular boolean mask where True indicates attention
    positions that should be masked. Prevents decoder from attending to future
    tokens, enforcing causal/autoregressive generation.

    Args:
        seq_len (int): Sequence length.
        device (torch.device): Device to create the mask on (cpu, cuda, etc.).

    Returns:
        torch.Tensor: Boolean mask of shape (seq_len, seq_len) with True in upper triangle
            (excluding diagonal), indicating masked positions.
    """
    return torch.triu(
        torch.ones(seq_len, seq_len, dtype=torch.bool, device=device), diagonal=1
    )


def create_masks(
    src: torch.Tensor,
    tgt: torch.Tensor,
    pad_idx: Optional[int] = None,
    config: Optional[Config] = None,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Create all necessary masks for transformer encoder-decoder.

    Convenience function to generate source padding mask, target padding mask,
    and target causal mask in a single call.

    Args:
        src (torch.Tensor): Source token sequence of shape (batch_size, src_len).
        tgt (torch.Tensor): Target token sequence of shape (batch_size, tgt_len).
        pad_idx (int, optional): Padding token index. Falls back to config.pad_idx.
        config (Config, optional): Configuration object. Defaults to default config.

    Returns:
        Tuple[torch.Tensor, torch.Tensor, torch.Tensor]: A tuple containing:
            - src_key_padding_mask: Boolean mask for source padding of shape (batch_size, src_len).
            - tgt_key_padding_mask: Boolean mask for target padding of shape (batch_size, tgt_len).
            - tgt_mask: Causal mask for target of shape (tgt_len, tgt_len).
    """
    cfg = config if config is not None else get_default_config()
    pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx
    return (
        create_key_padding_mask(src, pad_idx=pad_idx),
        create_key_padding_mask(tgt, pad_idx=pad_idx),
        create_causal_mask(tgt.size(1), tgt.device),
    )
