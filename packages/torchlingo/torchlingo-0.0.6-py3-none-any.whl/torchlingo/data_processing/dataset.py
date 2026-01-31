"""PyTorch Dataset implementation for parallel neural machine translation data.

This module provides the NMTDataset class for loading and encoding parallel
text corpora. It supports both simple token-based vocabularies and SentencePiece
models, with automatic vocabulary construction if pre-built vocabularies are not
provided. The dataset handles data cleaning, tokenization, and encoding to tensor
representations suitable for training neural translation models.
"""

from typing import Tuple, Optional
from pathlib import Path
import torch
from torch.utils.data import Dataset

from ..config import Config, get_default_config
from ..preprocessing.base import load_data
from .vocab import BaseVocab, SimpleVocab


class NMTDataset(Dataset):
    """PyTorch Dataset for parallel neural machine translation data.

    Loads a parallel corpus from disk and provides encoded source/target tensor
    pairs suitable for training and evaluation. Automatically cleans data by
    removing empty rows, normalizing whitespace, and handling missing values.
    If vocabulary objects are not provided, the dataset will build simple `SimpleVocab`
    instances from the training data.

    The dataset supports optional pre-tokenized columns and enforces a maximum
    sequence length by truncating longer sequences while preserving the EOS token.

    Parameters are resolved with fallback priority:
    1. Explicitly passed parameter values
    2. Values from passed config object
    3. Values from default config (get_default_config())

    Args:
        data_file (Path or str): Path to a structured file (TSV/CSV/JSON/Parquet)
            containing configurable src/tgt columns. Parallel .txt corpora must
            be converted to a single file upstream (see
            `preprocessing.base.parallel_txt_to_dataframe`).
        src_col (str, optional): Column name for source text. Falls back to
            config.src_col if not provided.
        tgt_col (str, optional): Column name for target text. Falls back to
            config.tgt_col if not provided.
        src_tok_col (str, optional): Column name for pre-tokenized source text.
            Falls back to config.src_tok_col if not provided.
        tgt_tok_col (str, optional): Column name for pre-tokenized target text.
            Falls back to config.tgt_tok_col if not provided.
        src_vocab (BaseVocab, optional): Pre-built source vocabulary. If None,
            a SimpleVocab will be created from src_col. Defaults to None.
        tgt_vocab (BaseVocab, optional): Pre-built target vocabulary. If None,
            a SimpleVocab will be created from tgt_col. Defaults to None.
        max_length (int, optional): Maximum sequence length in tokens. Sequences
            longer than this are truncated to (max_length - 1) + eos_idx. Falls
            back to config.max_seq_length if not provided.
        eos_idx (int, optional): Index of the EOS (end-of-sequence) token used
            for truncation. Falls back to config.eos_idx if not provided.
        config (Config, optional): Configuration object to use for default values.
            If None, uses get_default_config().

    Raises:
        ValueError: If data_file does not contain both src_col and tgt_col.

    Attributes:
        df (pd.DataFrame): Loaded and cleaned dataframe.
        src_sentences (list[str]): Raw source sentences.
        tgt_sentences (list[str]): Raw target sentences.
        src_vocab (BaseVocab): Source vocabulary.
        tgt_vocab (BaseVocab): Target vocabulary.
        has_tokenized (bool): Whether pre-tokenized columns exist in data.
        eos_idx (int): Index of the EOS token used for truncation.
    """

    def __init__(
        self,
        data_file: Path,
        src_col: str = None,
        tgt_col: str = None,
        src_tok_col: str = None,
        tgt_tok_col: str = None,
        src_vocab: Optional[BaseVocab] = None,
        tgt_vocab: Optional[BaseVocab] = None,
        max_length: Optional[int] = None,
        eos_idx: int = None,
        config: Config = None,
    ):
        cfg = config if config is not None else get_default_config()
        self.data_file = Path(data_file)
        self.src_col = src_col if src_col is not None else cfg.src_col
        self.tgt_col = tgt_col if tgt_col is not None else cfg.tgt_col
        self.src_tok_col = src_tok_col if src_tok_col is not None else cfg.src_tok_col
        self.tgt_tok_col = tgt_tok_col if tgt_tok_col is not None else cfg.tgt_tok_col
        self.max_length = max_length if max_length is not None else cfg.max_seq_length
        self.eos_idx = eos_idx if eos_idx is not None else cfg.eos_idx

        # Load data using pandas
        self.df = load_data(self.data_file)

        # Ensure columns exist before manipulating them
        if self.src_col not in self.df.columns or self.tgt_col not in self.df.columns:
            raise ValueError(
                f"Data file {data_file} must contain columns '{self.src_col}' and '{self.tgt_col}'"
            )

        # Normalize columns: replace NaN with empty string, strip whitespace,
        # and drop rows where either source or target is blank. Blank lines are
        # not useful for translation and should be skipped.
        self.df[self.src_col] = self.df[self.src_col].fillna("").astype(str).str.strip()
        self.df[self.tgt_col] = self.df[self.tgt_col].fillna("").astype(str).str.strip()
        self.df = self.df[(self.df[self.src_col] != "") & (self.df[self.tgt_col] != "")]

        # Detect pre-tokenized columns and materialize
        self.has_tokenized = (
            self.src_tok_col in self.df.columns and self.tgt_tok_col in self.df.columns
        )
        if self.has_tokenized:
            self.src_tokenized = (
                self.df[self.src_tok_col].fillna("").astype(str).str.strip().tolist()
            )
            self.tgt_tokenized = (
                self.df[self.tgt_tok_col].fillna("").astype(str).str.strip().tolist()
            )

        self.src_sentences = self.df[self.src_col].astype(str).tolist()
        self.tgt_sentences = self.df[self.tgt_col].astype(str).tolist()

        self.src_vocab = src_vocab
        self.tgt_vocab = tgt_vocab

        if self.src_vocab is None or self.tgt_vocab is None:
            if self.src_vocab is None:
                self.src_vocab = SimpleVocab()
                if self.has_tokenized:
                    self.src_vocab.build_vocab(
                        [" ".join(t.split()) for t in self.src_tokenized]
                    )
                else:
                    self.src_vocab.build_vocab(self.src_sentences)
            if self.tgt_vocab is None:
                self.tgt_vocab = SimpleVocab()
                if self.has_tokenized:
                    self.tgt_vocab.build_vocab(
                        [" ".join(t.split()) for t in self.tgt_tokenized]
                    )
                else:
                    self.tgt_vocab.build_vocab(self.tgt_sentences)

    def __len__(self) -> int:
        """Return the number of samples in the dataset.

        Returns:
            int: Total number of (source, target) pairs after cleaning.
        """
        return len(self.src_sentences)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Retrieve and encode a (source, target) pair at the given index.

        Encodes raw sentences to token indices using the respective vocabularies,
        adds special tokens (SOS/EOS), and truncates sequences exceeding
        max_length while preserving the EOS token.

        Args:
            idx (int): Index of the sample to retrieve. Must be in range
                [0, len(self)).

        Returns:
            tuple[torch.Tensor, torch.Tensor]: A tuple containing:
                - src_tensor (torch.Tensor): Encoded source indices with shape
                  (seq_len,) and dtype torch.long. Contains special tokens SOS
                  (at position 0) and EOS (at position -1).
                - tgt_tensor (torch.Tensor): Encoded target indices with shape
                  (seq_len,) and dtype torch.long. Contains special tokens SOS
                  (at position 0) and EOS (at position -1).

        Raises:
            AssertionError: If vocabularies have not been initialized.
            IndexError: If idx is out of range.
        """
        src_sentence = self.src_sentences[idx]
        tgt_sentence = self.tgt_sentences[idx]

        assert self.src_vocab is not None and self.tgt_vocab is not None

        src_indices = self.src_vocab.encode(src_sentence, add_special_tokens=True)
        tgt_indices = self.tgt_vocab.encode(tgt_sentence, add_special_tokens=True)

        if len(src_indices) > self.max_length:
            src_indices = src_indices[: self.max_length - 1] + [self.eos_idx]
        if len(tgt_indices) > self.max_length:
            tgt_indices = tgt_indices[: self.max_length - 1] + [self.eos_idx]

        return torch.tensor(src_indices, dtype=torch.long), torch.tensor(
            tgt_indices, dtype=torch.long
        )
