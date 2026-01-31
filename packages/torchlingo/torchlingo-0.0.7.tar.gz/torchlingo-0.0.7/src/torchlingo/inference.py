"""Inference utilities for TorchLingo models.

Provides decoding helpers and a batch translation convenience wrapper that
work across Transformer-style and LSTM seq2seq models. These functions are
kept separate from training logic to keep responsibilities focused.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import torch
import torch.nn.functional as F
from torch import nn
from torch.nn.utils.rnn import pad_sequence

from .config import Config, get_default_config
from .data_processing.vocab import BaseVocab


def greedy_decode(
    model: nn.Module,
    src: torch.Tensor,
    max_len: int = 100,
    device: Optional[torch.device] = None,
    config: Optional[Config] = None,
) -> List[List[int]]:
    """Greedy autoregressive decoding for Transformer or LSTM models.

    Decodes in mini-batches sized by ``config.batch_size`` to limit device
    memory usage when handling large input batches.

    Args:
        model: Seq2seq model. Transformer models must expose encode/decode; LSTM
            path uses src_embed/encoder/decoder/output modules present in
            SimpleSeq2SeqLSTM.
        src: Source tensor (batch, src_len).
        max_len: Maximum decoded length (including SOS/EOS).
        device: Torch device. Defaults to model's device or CUDA/CPU.
        config: TorchLingo Config providing special token indices.

    Returns:
        List of decoded token ID sequences (one list per batch element).
    """

    cfg = config if config is not None else get_default_config()
    device = device if device is not None else next(model.parameters()).device

    model.eval()

    batch_limit = max(1, cfg.batch_size)

    is_transformer = hasattr(model, "encode") and hasattr(model, "decode")
    is_lstm = all(
        hasattr(model, attr) for attr in ("src_embed", "encoder", "decoder", "output")
    )

    if not (is_transformer or is_lstm):
        raise ValueError(
            "Model must expose encode/decode or LSTM modules for greedy decoding."
        )

    def _decode_transformer(src_chunk: torch.Tensor) -> List[List[int]]:
        src_chunk = src_chunk.to(device)
        pad_mask = src_chunk.eq(cfg.pad_idx)
        with torch.no_grad():
            memory = model.encode(src_chunk, src_key_padding_mask=pad_mask)
            ys = torch.full(
                (src_chunk.size(0), 1), cfg.sos_idx, device=device, dtype=torch.long
            )
            finished = torch.zeros(src_chunk.size(0), dtype=torch.bool, device=device)
            for _ in range(max_len):
                tgt_mask = nn.Transformer.generate_square_subsequent_mask(
                    ys.size(1)
                ).to(device)
                out = model.decode(
                    ys,
                    memory,
                    src_key_padding_mask=pad_mask,
                    tgt_key_padding_mask=ys.eq(cfg.pad_idx),
                    tgt_mask=tgt_mask,
                )
                next_token = out[:, -1, :].argmax(-1)
                ys = torch.cat([ys, next_token.unsqueeze(1)], dim=1)
                finished |= next_token.eq(cfg.eos_idx)
                if finished.all():
                    break
        return ys.cpu().tolist()

    def _decode_lstm(src_chunk: torch.Tensor) -> List[List[int]]:
        src_chunk = src_chunk.to(device)
        with torch.no_grad():
            src_emb = model.src_embed(src_chunk)
            _, (h, c) = model.encoder(src_emb)

            batch_size = src_chunk.size(0)
            ys = torch.full(
                (batch_size, 1), cfg.sos_idx, device=device, dtype=torch.long
            )
            finished = torch.zeros(batch_size, dtype=torch.bool, device=device)

            hidden = (h, c)
            tgt_embed = getattr(model, "tgt_embed", None) or getattr(
                model, "src_embed", None
            )

            for _ in range(max_len):
                last_token = ys[:, -1].unsqueeze(1)
                emb = tgt_embed(last_token)
                dec_out, hidden = model.decoder(emb, hidden)
                logits = model.output(dec_out)
                next_token = logits[:, -1, :].argmax(-1)
                ys = torch.cat([ys, next_token.unsqueeze(1)], dim=1)
                finished |= next_token.eq(cfg.eos_idx)
                if finished.all():
                    break
        return ys.cpu().tolist()

    decoded: List[List[int]] = []
    for src_chunk in src.split(batch_limit):
        if is_transformer:
            decoded.extend(_decode_transformer(src_chunk))
        else:
            decoded.extend(_decode_lstm(src_chunk))

    return decoded


def beam_search_decode(
    model: nn.Module,
    src: torch.Tensor,
    beam_size: int = 5,
    max_len: int = 100,
    alpha: float = 0.6,
    device: Optional[torch.device] = None,
    config: Optional[Config] = None,
) -> List[int]:
    """Beam search decoding for Transformer-style models.

    Args:
        model: Transformer model exposing encode() and decode().
        src: Source tensor with shape (1, src_len). Batch size 1 is assumed.
        beam_size: Number of beams to maintain.
        max_len: Maximum generated length.
        alpha: Length normalization factor (Wu et al., 2016).
        device: Torch device. Defaults to model device.
        config: TorchLingo Config for special token indices.

    Returns:
        Best decoded token ID sequence (including SOS/EOS).
    """

    cfg = config if config is not None else get_default_config()
    device = device if device is not None else next(model.parameters()).device

    model.eval()

    if src.size(0) != 1:
        raise ValueError("beam_search_decode currently expects batch size = 1")
    if not (hasattr(model, "encode") and hasattr(model, "decode")):
        raise ValueError(
            "beam_search_decode requires a Transformer-style model with encode/decode"
        )

    src = src.to(device)
    pad_mask = src.eq(cfg.pad_idx)
    with torch.no_grad():
        memory = model.encode(src, src_key_padding_mask=pad_mask)

    beams: List[Tuple[List[int], float]] = [([cfg.sos_idx], 0.0)]
    completed: List[Tuple[List[int], float]] = []

    def length_norm(log_prob: float, length: int) -> float:
        return log_prob / (((5 + length) / 6) ** alpha)

    for _ in range(max_len):
        candidates: List[Tuple[List[int], float]] = []
        for tokens, score in beams:
            if tokens[-1] == cfg.eos_idx:
                completed.append((tokens, score))
                continue
            tgt = torch.tensor([tokens], dtype=torch.long, device=device)
            tgt_mask = nn.Transformer.generate_square_subsequent_mask(len(tokens)).to(
                device
            )
            with torch.no_grad():
                out = model.decode(
                    tgt,
                    memory,
                    src_key_padding_mask=pad_mask,
                    tgt_key_padding_mask=tgt.eq(cfg.pad_idx),
                    tgt_mask=tgt_mask,
                )
            log_probs = F.log_softmax(out[0, -1, :], dim=-1)
            top_log_probs, top_idx = torch.topk(log_probs, beam_size)
            for lp, idx in zip(top_log_probs.tolist(), top_idx.tolist()):
                candidates.append((tokens + [idx], score + lp))

        if not candidates:
            break
        candidates.sort(key=lambda x: length_norm(x[1], len(x[0])), reverse=True)
        beams = candidates[:beam_size]

        if all(tokens[-1] == cfg.eos_idx for tokens, _ in beams):
            completed.extend(beams)
            break

    completed.extend(beams)
    best_tokens, _ = max(completed, key=lambda x: length_norm(x[1], len(x[0])))
    return best_tokens


def translate_batch(
    model: nn.Module,
    sentences: Sequence[str],
    src_vocab: BaseVocab,
    tgt_vocab: BaseVocab,
    decode_strategy: str = "greedy",
    beam_size: int = 5,
    max_len: int = 100,
    device: Optional[torch.device] = None,
    config: Optional[Config] = None,
) -> List[str]:
    """Translate a batch of raw sentences using provided vocabularies.

    Processes inputs in chunks of ``config.batch_size`` to avoid moving very
    large padded batches to the device at once.

    Args:
        model: Seq2seq model (Transformer or LSTM).
        sentences: Iterable of raw source sentences.
        src_vocab: Vocabulary implementing BaseVocab.encode(add_special_tokens=True).
        tgt_vocab: Vocabulary implementing BaseVocab.decode(skip_special_tokens=True).
        decode_strategy: "greedy" or "beam".
        beam_size: Beam width when decode_strategy == "beam".
        max_len: Maximum generation length.
        device: Torch device. Defaults to model device.
        config: TorchLingo Config.

    Returns:
        List of decoded text strings aligned with input sentences.
    """

    cfg = config if config is not None else get_default_config()
    device = device if device is not None else next(model.parameters()).device

    encoded = [
        torch.tensor(src_vocab.encode(s, add_special_tokens=True), dtype=torch.long)
        for s in sentences
    ]

    batch_limit = max(1, cfg.batch_size)

    # Prefer special-token indices carried by the vocabulary (SentencePiece models
    # often encode these directly) to avoid mismatches with an unrelated config.
    pad_idx = getattr(tgt_vocab, "pad_idx", cfg.pad_idx)
    sos_idx = getattr(tgt_vocab, "sos_idx", cfg.sos_idx)
    eos_idx = getattr(tgt_vocab, "eos_idx", cfg.eos_idx)

    outputs: List[List[int]] = []

    for start in range(0, len(encoded), batch_limit):
        batch_tokens = encoded[start : start + batch_limit]
        padded = pad_sequence(batch_tokens, batch_first=True, padding_value=cfg.pad_idx)

        if decode_strategy == "beam":
            for row in padded:
                tokens = beam_search_decode(
                    model,
                    row.unsqueeze(0),
                    beam_size=beam_size,
                    max_len=max_len,
                    device=device,
                    config=cfg,
                )
                outputs.append(tokens)
        else:
            outputs.extend(
                greedy_decode(model, padded, max_len=max_len, device=device, config=cfg)
            )

    decoded: List[str] = []

    def _strip_after_special(tokens: Sequence[int]) -> List[int]:
        # Drop SOS and everything after the first EOS/PAD using vocab-aware IDs.
        cleaned: List[int] = []
        for t in tokens:
            if t in (eos_idx, pad_idx):
                break
            if t == sos_idx:
                continue
            cleaned.append(int(t))
        return cleaned

    for token_ids in outputs:
        cleaned = _strip_after_special(token_ids)
        # Let the vocab handle decoding (SentencePiece will rejoin subwords correctly).
        decoded_text = tgt_vocab.decode(cleaned, skip_special_tokens=True)
        decoded.append(
            decoded_text.strip() if hasattr(decoded_text, "strip") else decoded_text
        )
    return decoded


__all__ = [
    "greedy_decode",
    "beam_search_decode",
    "translate_batch",
]
