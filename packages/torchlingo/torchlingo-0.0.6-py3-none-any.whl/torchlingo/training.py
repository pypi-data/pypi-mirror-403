"""High-level training helper for TorchLingo models.

Provides a lightweight, single-GPU training loop that works for both
Transformer and LSTM seq2seq models. Decoding and translation utilities live
in `torchlingo.inference` to keep responsibilities separated.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.nn.utils import clip_grad_norm_
from torch.nn.utils.rnn import pad_sequence

try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover - optional dependency
    # Fallback: simple identity when tqdm is not available (keeps behavior testable)
    def tqdm(x, **kwargs):
        return x


try:
    from torch.utils.tensorboard import SummaryWriter
except Exception:  # pragma: no cover - optional dependency
    SummaryWriter = None


from .config import Config, get_default_config


@dataclass
class TrainResult:
    """Container for training metrics and artifacts.

    Attributes:
        train_losses: Mean training loss per epoch.
        val_losses: Mean validation loss per epoch (empty when no val_loader).
        best_checkpoint: Path to the best checkpoint file if saved, else None.
    """

    train_losses: List[float]
    val_losses: List[float]
    best_checkpoint: Optional[Path]


def _resolve_device(device: Optional[torch.device]) -> torch.device:
    return (
        device
        if device is not None
        else torch.device("cuda" if torch.cuda.is_available() else "cpu")
    )


def train_model(
    model: nn.Module,
    train_loader: torch.utils.data.DataLoader,
    val_loader: Optional[torch.utils.data.DataLoader] = None,
    num_epochs: int = 10,
    optimizer: Optional[optim.Optimizer] = None,
    criterion: Optional[nn.Module] = None,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    gradient_clip: Optional[float] = None,
    device: Optional[torch.device] = None,
    config: Optional[Config] = None,
    save_dir: Optional[Path] = None,
    use_amp: bool = False,
    log_every: int = 0,
) -> TrainResult:
    """Train a seq2seq model with optional validation and checkpointing.

    Args:
        model: Seq2seq model (Transformer or LSTM) supporting forward(src, tgt).
        train_loader: DataLoader yielding (src, tgt) tensors.
        val_loader: Optional DataLoader for validation loss.
        num_epochs: Number of training epochs to run.
        optimizer: Optimizer instance. Defaults to Adam with config.learning_rate.
        criterion: Loss function. Defaults to CrossEntropyLoss with padding ignore.
        scheduler: Optional LR scheduler stepped once per optimizer step.
        gradient_clip: If provided, max gradient norm applied each step.
        device: Torch device. Defaults to CUDA if available else CPU.
        config: TorchLingo Config providing pad_idx, label_smoothing, etc.
        save_dir: If provided, best model (lowest val loss) is saved here.
        use_amp: Enable automatic mixed precision for speed on GPUs.
        log_every: If >0, prints running train loss every log_every steps.

    Returns:
        TrainResult containing per-epoch losses and optional checkpoint path.
    """

    cfg = config if config is not None else get_default_config()
    device = _resolve_device(device)
    model = model.to(device)

    opt = (
        optimizer
        if optimizer is not None
        else optim.Adam(model.parameters(), lr=cfg.learning_rate)
    )
    loss_fn = (
        criterion
        if criterion is not None
        else nn.CrossEntropyLoss(
            ignore_index=cfg.pad_idx, label_smoothing=cfg.label_smoothing
        )
    )

    scaler = torch.amp.GradScaler(device=device, enabled=use_amp)
    best_val = float("inf")
    best_path: Optional[Path] = None
    train_losses: List[float] = []
    val_losses: List[float] = []
    global_step = 0
    stop_training = False
    no_improve_steps = 0

    # Initialize TensorBoard writer if enabled
    writer = None
    if cfg.use_tensorboard and SummaryWriter is not None:
        tb_dir = cfg.tensorboard_dir / cfg.experiment_name
        tb_dir.mkdir(parents=True, exist_ok=True)
        writer = SummaryWriter(log_dir=str(tb_dir))

    for epoch in range(num_epochs):
        model.train()
        total_train = 0.0
        steps_in_epoch = 0
        # Use tqdm to present a progress bar for steps in the epoch
        for step, (src, tgt) in enumerate(
            tqdm(train_loader, desc=f"Epoch {epoch + 1}", total=len(train_loader)),
            start=1,
        ):
            src = src.to(device)
            tgt = tgt.to(device)
            tgt_input = tgt[:, :-1]
            tgt_output = tgt[:, 1:]

            opt.zero_grad()
            with torch.amp.autocast(device_type=device.type, enabled=use_amp):
                logits = model(src, tgt_input)
                loss = loss_fn(
                    logits.reshape(-1, logits.size(-1)), tgt_output.reshape(-1)
                )

            scaler.scale(loss).backward()
            if gradient_clip is not None:
                scaler.unscale_(opt)
                clip_grad_norm_(model.parameters(), gradient_clip)
            scaler.step(opt)
            scaler.update()

            if scheduler is not None:
                scheduler.step()

            total_train += loss.item()
            global_step += 1
            steps_in_epoch += 1
            # stop when either explicit step_limit or config.num_steps reached
            if (
                getattr(cfg, "step_limit", None) is not None
                and global_step >= cfg.step_limit
            ):
                stop_training = True
            if (
                getattr(cfg, "num_steps", None) is not None
                and cfg.num_steps
                and global_step >= cfg.num_steps
            ):
                stop_training = True

            # Periodic validation (step-based)
            if val_loader is not None and getattr(cfg, "val_interval", None):
                if global_step % cfg.val_interval == 0:
                    model.eval()
                    total_val = 0.0
                    with torch.no_grad():
                        for v_src, v_tgt in val_loader:
                            v_src = v_src.to(device)
                            v_tgt = v_tgt.to(device)
                            v_logits = model(v_src, v_tgt[:, :-1])
                            v_loss = loss_fn(
                                v_logits.reshape(-1, v_logits.size(-1)),
                                v_tgt[:, 1:].reshape(-1),
                            )
                            total_val += v_loss.item()
                    avg_val = total_val / max(1, len(val_loader))
                    val_losses.append(avg_val)
                    # early stopping logic (patience)
                    if avg_val < best_val:
                        best_val = avg_val
                        no_improve_steps = 0
                        # save best checkpoint
                        if save_dir is not None:
                            save_dir.mkdir(parents=True, exist_ok=True)
                            best_path = Path(save_dir) / "model_best.pt"
                            torch.save(model.state_dict(), best_path)
                        else:
                            torch.save(model.state_dict(), cfg.checkpoint_path)
                    else:
                        no_improve_steps += 1
                        if no_improve_steps >= getattr(cfg, "patience", 0):
                            stop_training = True
                    if writer is not None:
                        writer.add_scalar("val/loss", avg_val, global_step)
                    model.train()

            # Periodic save of last checkpoint
            if (
                getattr(cfg, "save_interval", None)
                and cfg.save_interval
                and global_step % cfg.save_interval == 0
            ):
                if save_dir is not None:
                    save_dir.mkdir(parents=True, exist_ok=True)
                    last_path = Path(save_dir) / "model_last.pt"
                    torch.save(model.state_dict(), last_path)
                    best_path = last_path if best_path is None else best_path
                else:
                    torch.save(model.state_dict(), cfg.last_checkpoint_path)

            if stop_training:
                break

            # logging: prefer explicit function arg, fall back to config
            effective_log = log_every if log_every else getattr(cfg, "log_interval", 0)
            if effective_log and step % effective_log == 0:
                running = total_train / max(1, steps_in_epoch)
                print(
                    f"Epoch {epoch + 1} Step {step}/{len(train_loader)} | Train Loss: {running:.4f}"
                )
                if writer is not None:
                    writer.add_scalar("train/loss", running, global_step)
                    # Log learning rate from optimizer
                    for param_group in opt.param_groups:
                        writer.add_scalar(
                            "train/learning_rate", param_group["lr"], global_step
                        )

        # Average over steps actually run in this epoch
        avg_train = total_train / max(1, steps_in_epoch)
        train_losses.append(avg_train)
        if writer is not None:
            writer.add_scalar("train/epoch_loss", avg_train, epoch)

        if val_loader is None:
            print(f"Epoch {epoch + 1}/{num_epochs} | Train: {avg_train:.4f}")
            if stop_training:
                break
            continue

        # Epoch-end validation (also used to update early-stopping state)
        model.eval()
        total_val = 0.0
        with torch.no_grad():
            for src, tgt in val_loader:
                src = src.to(device)
                tgt = tgt.to(device)
                logits = model(src, tgt[:, :-1])
                loss = loss_fn(
                    logits.reshape(-1, logits.size(-1)), tgt[:, 1:].reshape(-1)
                )
                total_val += loss.item()
        avg_val = total_val / max(1, len(val_loader))
        val_losses.append(avg_val)

        print(
            f"Epoch {epoch + 1}/{num_epochs} | Train: {avg_train:.4f} | Val: {avg_val:.4f}"
        )
        if writer is not None:
            writer.add_scalar("val/epoch_loss", avg_val, epoch)

        if avg_val < best_val:
            best_val = avg_val
            no_improve_steps = 0
            # save best checkpoint
            if save_dir is not None:
                save_dir.mkdir(parents=True, exist_ok=True)
                best_path = Path(save_dir) / "model_best.pt"
                torch.save(model.state_dict(), best_path)
                print("  -> Saved best checkpoint")
            else:
                torch.save(model.state_dict(), cfg.checkpoint_path)
        else:
            no_improve_steps += 1
            if no_improve_steps >= getattr(cfg, "patience", 0):
                stop_training = True

        if stop_training:
            print(
                "Reached stopping condition (step limit or patience). Stopping training."
            )
            break

    if writer is not None:
        writer.close()

    return TrainResult(
        train_losses=train_losses, val_losses=val_losses, best_checkpoint=best_path
    )


def greedy_decode(
    model: nn.Module,
    src: torch.Tensor,
    max_len: int = 100,
    device: Optional[torch.device] = None,
    config: Optional[Config] = None,
) -> List[List[int]]:
    """Greedy autoregressive decoding for Transformer or LSTM models.

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

    src = src.to(device)
    pad_mask = src.eq(cfg.pad_idx)

    with torch.no_grad():
        if hasattr(model, "encode") and hasattr(model, "decode"):
            memory = model.encode(src, src_key_padding_mask=pad_mask)
            ys = torch.full(
                (src.size(0), 1), cfg.sos_idx, device=device, dtype=torch.long
            )
            finished = torch.zeros(src.size(0), dtype=torch.bool, device=device)
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
            return ys.tolist()

        # Fallback: LSTM incremental decoding
        if not all(
            hasattr(model, attr)
            for attr in ("src_embed", "encoder", "decoder", "output")
        ):
            raise ValueError(
                "Model must expose encode/decode or LSTM modules for greedy decoding."
            )

        src_emb = model.src_embed(src)
        _, (h, c) = model.encoder(src_emb)
        outputs = torch.full(
            (src.size(0), 1), cfg.sos_idx, device=device, dtype=torch.long
        )
        finished = torch.zeros(src.size(0), dtype=torch.bool, device=device)

        for _ in range(max_len):
            step_input = model.tgt_embed(outputs[:, -1:])
            dec_out, (h, c) = model.decoder(step_input, (h, c))
            logits = model.output(dec_out)
            next_token = logits[:, -1, :].argmax(-1)
            outputs = torch.cat([outputs, next_token.unsqueeze(1)], dim=1)
            finished |= next_token.eq(cfg.eos_idx)
            if finished.all():
                break
        return outputs.tolist()


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
    src_vocab,
    tgt_vocab,
    decode_strategy: str = "greedy",
    beam_size: int = 5,
    max_len: int = 100,
    device: Optional[torch.device] = None,
    config: Optional[Config] = None,
) -> List[str]:
    """Translate a batch of raw sentences using provided vocabularies.

    Args:
        model: Seq2seq model (Transformer or LSTM).
        sentences: Iterable of raw source sentences.
        src_vocab: Vocabulary with encode(add_special_tokens=True).
        tgt_vocab: Vocabulary with decode(skip_special_tokens=True).
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
    padded = pad_sequence(encoded, batch_first=True, padding_value=cfg.pad_idx).to(
        device
    )

    outputs: List[List[int]]
    if decode_strategy == "beam":
        outputs = []
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
        outputs = greedy_decode(
            model, padded, max_len=max_len, device=device, config=cfg
        )

    decoded: List[str] = []
    for token_ids in outputs:
        decoded.append(tgt_vocab.decode(token_ids, skip_special_tokens=True))
    return decoded


__all__ = ["TrainResult", "train_model"]
