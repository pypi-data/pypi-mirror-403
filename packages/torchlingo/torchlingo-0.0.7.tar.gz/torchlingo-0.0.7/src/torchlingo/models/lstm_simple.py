"""Simple LSTM-based sequence-to-sequence model for neural machine translation.

This module implements a basic encoder-decoder architecture using LSTM layers
for sequence-to-sequence learning tasks, such as machine translation. The model
encodes source sequences and decodes target sequences with shared hidden state.

Typical usage:
    >>> model = SimpleSeq2SeqLSTM(src_vocab_size=1000, tgt_vocab_size=1000)
    >>> src = torch.randint(0, 1000, (2, 10))
    >>> tgt = torch.randint(0, 1000, (2, 15))
    >>> output = model(src, tgt)
    >>> output.shape
    torch.Size([2, 15, 1000])
"""

import torch
import torch.nn as nn
from ..config import Config, get_default_config


class SimpleSeq2SeqLSTM(nn.Module):
    """Simple LSTM encoder-decoder model for sequence-to-sequence tasks.

    This model encodes source sequences into a context vector using an LSTM encoder,
    then decodes target sequences using an LSTM decoder initialized with the encoder's
    final hidden and cell states. Token embeddings use padding index from config.

    Args:
        src_vocab_size (int): Size of the source vocabulary.
        tgt_vocab_size (int): Size of the target vocabulary.
        emb_dim (int, optional): Embedding dimension. Falls back to config.lstm_emb_dim.
        hidden_dim (int, optional): Hidden dimension for LSTM layers. Falls back to config.lstm_hidden_dim.
        num_layers (int, optional): Number of LSTM layers in encoder and decoder. Falls back to config.lstm_num_layers.
        dropout (float, optional): Dropout rate applied between LSTM layers. Falls back to config.lstm_dropout.
        pad_idx (int, optional): Padding token index for embeddings. Falls back to config.pad_idx.
        config (Config, optional): Configuration object. Defaults to default config.

    Attributes:
        pad_idx (int): Resolved padding index.
        src_embed (nn.Embedding): Source token embedding layer.
        tgt_embed (nn.Embedding): Target token embedding layer.
        encoder (nn.LSTM): LSTM encoder for source sequences.
        decoder (nn.LSTM): LSTM decoder for target sequences.
        output (nn.Linear): Linear output layer projecting decoder hidden state to target vocabulary.
        hidden_dim (int): Hidden dimension size.
    """

    def __init__(
        self,
        src_vocab_size: int,
        tgt_vocab_size: int,
        emb_dim: int = None,
        hidden_dim: int = None,
        num_layers: int = None,
        dropout: float = None,
        pad_idx: int = None,
        config: Config = None,
    ):
        super().__init__()
        cfg = config if config is not None else get_default_config()
        self.pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx
        emb_dim = emb_dim if emb_dim is not None else cfg.lstm_emb_dim
        hidden_dim = hidden_dim if hidden_dim is not None else cfg.lstm_hidden_dim
        num_layers = num_layers if num_layers is not None else cfg.lstm_num_layers
        dropout = dropout if dropout is not None else cfg.lstm_dropout

        self.src_embed = nn.Embedding(src_vocab_size, emb_dim, padding_idx=self.pad_idx)
        self.tgt_embed = nn.Embedding(tgt_vocab_size, emb_dim, padding_idx=self.pad_idx)
        self.encoder = nn.LSTM(
            emb_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.decoder = nn.LSTM(
            emb_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.output = nn.Linear(hidden_dim, tgt_vocab_size)
        self.hidden_dim = hidden_dim

    def forward(
        self,
        src: torch.Tensor,
        tgt: torch.Tensor,
    ) -> torch.Tensor:
        """Encode source and decode target sequences.

        Encodes source tokens into context using the LSTM encoder, then passes
        the final hidden and cell states to the LSTM decoder to generate target
        token predictions. Attention masks are currently unused but accepted for
        API compatibility.

        Args:
            src (torch.Tensor): Source token indices with shape (batch_size, src_len).
                Values should be in range [0, src_vocab_size).
            tgt (torch.Tensor): Target token indices with shape (batch_size, tgt_len).
                Values should be in range [0, tgt_vocab_size).

        Returns:
            torch.Tensor: Logits of shape (batch_size, tgt_len, tgt_vocab_size) representing
                probability distributions over the target vocabulary for each position.
        """
        src_emb = self.src_embed(src)
        enc_out, (h, c) = self.encoder(src_emb)
        tgt_emb = self.tgt_embed(tgt)
        dec_out, _ = self.decoder(tgt_emb, (h, c))
        return self.output(dec_out)
