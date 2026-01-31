"""Vocabulary management for neural machine translation.

Provides vocabulary interfaces and implementations for encoding and decoding text:

1. **BaseVocab**: Abstract base class defining the contract for all vocabularies.

2. **SimpleVocab**: Simple, frequency-based token vocabulary
   built from raw text. Splits sentences by whitespace and creates a mapping
   between tokens and integer indices. Useful for small vocabularies or when
   you control the preprocessing pipeline.

3. **SentencePieceVocab**: Wrapper around pre-trained SentencePiece models
   for subword tokenization. Handles language-specific preprocessing and
   handles rare characters gracefully.

4. **MeCabVocab**: Vocabulary for Japanese text using MeCab morphological
   analysis via the fugashi library. Supports languages without whitespace
   word boundaries.

5. **JiebaVocab**: Vocabulary for Chinese text using the jieba segmentation
   library. Handles Chinese word segmentation for languages without spaces.

All vocabularies reserve special token indices for padding (PAD), unknown
tokens (UNK), and sequence boundaries (SOS/EOS) as defined in config.

Note:
    This module is adapted from the top-level `data_processing/vocab.py` with
    `config` imports updated to reference the package namespace.

    MeCabVocab requires: ``pip install fugashi[unidic-lite]``
    JiebaVocab requires: ``pip install jieba``
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Union

import sentencepiece as spm
import torch

from ..config import Config, get_default_config

IndexInput = Union[Sequence[int], Sequence[Sequence[int]], torch.Tensor]
DecodedOutput = Union[str, List[str]]


class BaseVocab(ABC):
    """Abstract base class describing the vocabulary contract.

    Subclasses must implement the abstract methods below. The base class
    centralizes handling of special tokens (PAD/UNK/SOS/EOS) and their
    default indices so that concrete implementations behave consistently.

    Implementations are expected to be lightweight and to focus on token
    splitting/merging (`encode`/`decode`) and token<->index conversions. The
    `SimpleVocab` stores an in-memory mapping and supports building from raw
    sentences; `SentencePieceVocab` wraps a pre-trained SentencePiece model and
    therefore does not implement `build_vocab`.

    Examples:
        >>> from torchlingo.data_processing import BaseVocab, SimpleVocab
        >>> v: BaseVocab = SimpleVocab()
        >>> v.build_vocab(["a b", "a c"])  # only available for SimpleVocab
        >>> v.encode("a b")
    """

    def __init__(
        self,
        *,
        pad_token: Optional[str] = None,
        unk_token: Optional[str] = None,
        sos_token: Optional[str] = None,
        eos_token: Optional[str] = None,
        pad_idx: Optional[int] = None,
        unk_idx: Optional[int] = None,
        sos_idx: Optional[int] = None,
        eos_idx: Optional[int] = None,
        config: Optional[Config] = None,
    ) -> None:
        cfg = config if config is not None else get_default_config()

        self.pad_token = pad_token if pad_token is not None else cfg.pad_token
        self.unk_token = unk_token if unk_token is not None else cfg.unk_token
        self.sos_token = sos_token if sos_token is not None else cfg.sos_token
        self.eos_token = eos_token if eos_token is not None else cfg.eos_token

        self.pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx
        self.unk_idx = unk_idx if unk_idx is not None else cfg.unk_idx
        self.sos_idx = sos_idx if sos_idx is not None else cfg.sos_idx
        self.eos_idx = eos_idx if eos_idx is not None else cfg.eos_idx

    # ------------------------------------------------------------------
    # Abstract API
    # ------------------------------------------------------------------
    @abstractmethod
    def __len__(self) -> int:
        """Return the vocabulary size (number of token ids available).

        The returned value must include any reserved special tokens (PAD/UNK/
        SOS/EOS) so that consumers can size embedding layers and related
        structures using `len(vocab)`.

        Returns:
            int: Total number of tokens in the vocabulary.
        """

    @abstractmethod
    def build_vocab(self, sentences: Sequence[str]) -> None:
        """Populate internal structures from raw sentences.

        Not all implementations are required to support building a vocabulary
        from raw text (for example, `SentencePieceVocab` loads a pre-trained
        model and will raise). Implementations that *do* support building
        should accept an iterable of raw (untokenized or tokenized) sentence
        strings.

        Args:
            sentences (Sequence[str]): Iterable of raw sentence strings.
        """

    @abstractmethod
    def token_to_idx(self, token: str) -> int:
        """Return the integer id for `token`.

        If `token` is not present in the vocabulary, implementations should
        return the configured unknown index (`unk_idx`).

        Args:
            token (str): Token string to look up.

        Returns:
            int: Integer index for the token.
        """

    @abstractmethod
    def idx_to_token(self, idx: int) -> str:
        """Return the token string for `idx`.

        Unknown indices should map to the configured unknown token string
        (`unk_token`).

        Args:
            idx (int): Integer index to look up.

        Returns:
            str: Token string corresponding to the index.
        """

    @abstractmethod
    def encode(self, sentence: str, add_special_tokens: bool = True) -> List[int]:
        """Convert a raw sentence to a list of token ids.

        Args:
            sentence (str): Raw input string. For simple vocabularies this is
                expected to be an untokenized string; for SentencePiece it may
                be preprocessed as appropriate for the model.
            add_special_tokens (bool, optional): If True, the encoder should
                prepend `sos_idx` and append `eos_idx` to the returned id
                sequence. Defaults to True.

        Returns:
            List[int]: A list of integer token ids.
        """

    @abstractmethod
    def decode(
        self, indices: IndexInput, skip_special_tokens: bool = True
    ) -> DecodedOutput:
        """Decode integer ids back to human-readable text.

        The method must accept either a flat 1D sequence of ids, a 2D batched
        sequence (list of lists) or a 1/2-D `torch.Tensor`. When a batch is
        provided the method should return a list of decoded strings; for a 1-D
        input it should return a single string.

        Args:
            indices (IndexInput): 1-D or 2-D sequence of token ids or a tensor.
            skip_special_tokens (bool, optional): When True, remove any special
                PAD/SOS/EOS/UNK tokens from the decoded output (useful for
                displaying model output). Defaults to True.

        Returns:
            DecodedOutput: Decoded text (str) or list of strings.
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def tokens_to_indices(self, tokens: Sequence[str]) -> List[int]:
        """Helper: map a sequence of tokens to their indices.

        Implemented in terms of `token_to_idx` to guarantee consistent UNK
        handling across vocab implementations.

        Args:
            tokens (Sequence[str]): List of token strings.

        Returns:
            List[int]: List of corresponding token indices.
        """

        return [self.token_to_idx(token) for token in tokens]

    def indices_to_tokens(self, indices: Sequence[int]) -> List[str]:
        """Helper: map a sequence of indices to their token strings.

        Implemented in terms of `idx_to_token` and preserves the order of the
        input indices.

        Args:
            indices (Sequence[int]): List of token indices.

        Returns:
            List[str]: List of corresponding token strings.
        """

        return [self.idx_to_token(idx) for idx in indices]

    @staticmethod
    def _coerce_indices(indices: IndexInput) -> Union[List[int], List[List[int]]]:
        """Internal helper: coerce tensors into native Python lists.

        Accepts 1-D or 2-D `torch.Tensor` inputs and returns a list or nested
        list suitable for decoding. Raises `ValueError` for tensors of
        unexpected dimensionality.

        Args:
            indices (IndexInput): Input indices (list or tensor).

        Returns:
            Union[List[int], List[List[int]]]: Python list representation.

        Raises:
            ValueError: If tensor dimensionality is not 1 or 2.
        """

        if isinstance(indices, torch.Tensor):
            if indices.dim() == 1:
                return indices.tolist()
            if indices.dim() == 2:
                return [row.tolist() for row in indices]
            raise ValueError("decode expects a 1D or 2D tensor of indices")
        return indices  # type: ignore[return-value]

    @staticmethod
    def _is_batch(indices: Sequence[Union[int, Sequence[int]]]) -> bool:
        """Return True when `indices` is a batch (a sequence of sequences).

        This is used to distinguish between flat and batched decoding
        invocation styles.

        Args:
            indices (Sequence): Input sequence to check.

        Returns:
            bool: True if input appears to be a batch of sequences.
        """

        return (
            len(indices) > 0
            and isinstance(indices[0], Sequence)
            and not isinstance(indices[0], (str, bytes))
        )


class SimpleVocab(BaseVocab):
    """Simple whitespace-tokenized vocabulary with frequency-based filtering.

    Builds a vocabulary by splitting raw text on whitespace and counting token
    frequencies. Only tokens appearing at least min_freq times are included.
    Special tokens (PAD, UNK, SOS, EOS) are always reserved and included.

    This vocabulary is suitable for small datasets or when you have limited
    preprocessing control. For production use or languages with complex word
    boundaries, consider SentencePieceVocab.

    Args:
        min_freq (int, optional): Minimum frequency threshold for including a
            token in the vocabulary. Tokens appearing fewer than min_freq times
            are mapped to the UNK token index. If None, uses value from config.
            Defaults to None.
        pad_token (str, optional): Padding token string. If None, uses value from
            config. Defaults to None.
        unk_token (str, optional): Unknown token string. If None, uses value from
            config. Defaults to None.
        sos_token (str, optional): Start-of-sequence token string. If None, uses
            value from config. Defaults to None.
        eos_token (str, optional): End-of-sequence token string. If None, uses
            value from config. Defaults to None.
        pad_idx (int, optional): Padding token index. If None, uses value from
            config. Defaults to None.
        unk_idx (int, optional): Unknown token index. If None, uses value from
            config. Defaults to None.
        sos_idx (int, optional): Start-of-sequence token index. If None, uses
            value from config. Defaults to None.
        eos_idx (int, optional): End-of-sequence token index. If None, uses
            value from config. Defaults to None.
        config (Config, optional): Configuration object to use for default values.
            If None, uses get_default_config(). Defaults to None.

    Attributes:
        token2idx (dict): Mapping from token strings to integer indices.
        idx2token (dict): Mapping from integer indices to token strings.
        token_freqs (dict): Frequency count for each observed token.
        min_freq (int): Minimum frequency threshold.
        pad_token (str): Padding token string.
        unk_token (str): Unknown token string.
        sos_token (str): Start-of-sequence token string.
        eos_token (str): End-of-sequence token string.
        pad_idx (int): Padding token index.
        unk_idx (int): Unknown token index.
        sos_idx (int): Start-of-sequence token index.
        eos_idx (int): End-of-sequence token index.
    """

    def __init__(
        self,
        min_freq: Optional[int] = None,
        *,
        pad_token: Optional[str] = None,
        unk_token: Optional[str] = None,
        sos_token: Optional[str] = None,
        eos_token: Optional[str] = None,
        pad_idx: Optional[int] = None,
        unk_idx: Optional[int] = None,
        sos_idx: Optional[int] = None,
        eos_idx: Optional[int] = None,
        config: Optional[Config] = None,
    ) -> None:
        cfg = config if config is not None else get_default_config()
        super().__init__(
            pad_token=pad_token,
            unk_token=unk_token,
            sos_token=sos_token,
            eos_token=eos_token,
            pad_idx=pad_idx,
            unk_idx=unk_idx,
            sos_idx=sos_idx,
            eos_idx=eos_idx,
            config=cfg,
        )

        self.min_freq = min_freq if min_freq is not None else cfg.min_freq
        self.token2idx = {
            self.pad_token: self.pad_idx,
            self.unk_token: self.unk_idx,
            self.sos_token: self.sos_idx,
            self.eos_token: self.eos_idx,
        }
        self.idx2token = {idx: tok for tok, idx in self.token2idx.items()}
        self.token_freqs: dict[str, int] = {}

    def __len__(self) -> int:
        """Return the total vocabulary size.

        Returns:
            int: Number of unique tokens in the vocabulary, including special tokens.
        """

        return len(self.token2idx)

    def build_vocab(self, sentences: Sequence[str]) -> None:
        """Build the vocabulary from a list of raw sentences.

        Counts token frequencies by splitting each sentence on whitespace.
        Adds tokens with frequency >= min_freq to the vocabulary, skipping
        special tokens that are pre-initialized.

        Args:
            sentences (list[str]): List of raw sentences to build vocabulary from.
                Each sentence is assumed to be whitespace-separated tokens.

        Notes:
            - Modifies self.token_freqs and self.token2idx in place.
            - Special tokens (PAD, UNK, SOS, EOS) are not overwritten.
            - Tokens are assigned indices in order of appearance in the iteration.
        """

        for sentence in sentences:
            for token in sentence.split():
                self.token_freqs[token] = self.token_freqs.get(token, 0) + 1

        for token, freq in self.token_freqs.items():
            if freq >= self.min_freq and token not in self.token2idx:
                idx = len(self.token2idx)
                self.token2idx[token] = idx
                self.idx2token[idx] = token

    def token_to_idx(self, token: str) -> int:
        """Convert a single token string to its vocabulary index.

        Args:
            token (str): The token to convert.

        Returns:
            int: The vocabulary index of the token. Returns unk_idx if the token
                is not in the vocabulary.
        """

        return self.token2idx.get(token, self.unk_idx)

    def idx_to_token(self, idx: int) -> str:
        """Convert a vocabulary index to its token string.

        Args:
            idx (int): The vocabulary index.

        Returns:
            str: The token string corresponding to the index. Returns unk_token
                if the index is not in the vocabulary.
        """

        return self.idx2token.get(idx, self.unk_token)

    def encode(self, sentence: str, add_special_tokens: bool = True) -> List[int]:
        """Encode a sentence to a list of vocabulary indices.

        Splits the sentence on whitespace and converts each token to its
        vocabulary index. Optionally prepends SOS (start-of-sequence) and
        appends EOS (end-of-sequence) indices.

        Args:
            sentence (str): Raw sentence string, whitespace-separated tokens.
            add_special_tokens (bool, optional): If True, prepend SOS_IDX and
                append EOS_IDX to the sequence. Defaults to True.

        Returns:
            list[int]: Encoded sequence of vocabulary indices. Shape is
                (len(tokens) + 2,) if add_special_tokens is True, else
                (len(tokens),).

        Examples:
            >>> vocab = SimpleVocab(min_freq=1)
            >>> vocab.build_vocab(["hello world", "world peace"])
            >>> indices = vocab.encode("hello world", add_special_tokens=False)
            >>> len(indices)  # 2 tokens
            2
            >>> indices_with_special = vocab.encode("hello world")
            >>> len(indices_with_special)  # 2 tokens + SOS + EOS
            4
        """

        tokens = sentence.split()
        indices = self.tokens_to_indices(tokens)
        if add_special_tokens:
            indices = [self.sos_idx] + indices + [self.eos_idx]
        return indices

    def decode(
        self, indices: IndexInput, skip_special_tokens: bool = True
    ) -> DecodedOutput:
        """Decode indices back to text (supports batched inputs).

        Accepts a flat 1D sequence of indices or a batched 2D structure
        (list[list[int]] or tensor of shape [batch, seq]). Batched inputs
        return a list of decoded strings; flat inputs return a single string.

        Args:
            indices (Union[Sequence[int], Sequence[Sequence[int]]): 1D indices, 2D nested indices, or tensor.
            skip_special_tokens (bool, optional): If True, drop PAD/SOS/EOS/UNK tokens.

        Returns:
            str | list[str]: Decoded text for each sequence.

        Examples:
            >>> vocab = SimpleVocab(min_freq=1)
            >>> vocab.build_vocab(["hello world"])
            >>> indices = vocab.encode("hello world")
            >>> decoded = vocab.decode(indices)
            >>> decoded
            'hello world'
        """

        normalized = self._coerce_indices(indices)

        if isinstance(normalized, Sequence) and self._is_batch(normalized):
            return [
                self.decode(list(seq), skip_special_tokens=skip_special_tokens)  # type: ignore[list-item]
                for seq in normalized
            ]

        flat: List[int] = list(normalized)  # type: ignore[list-item]
        tokens = self.indices_to_tokens(flat)

        if skip_special_tokens:
            specials = {self.pad_token, self.unk_token, self.sos_token, self.eos_token}
            tokens = [tok for tok in tokens if tok not in specials]

        return " ".join(tokens)


class SentencePieceVocab(BaseVocab):
    """Vocabulary wrapper for pre-trained SentencePiece subword tokenization models.

    Loads and uses a SentencePiece model for encoding and decoding text.
    SentencePiece handles language-specific preprocessing, rare characters,
    and provides statistically-driven subword segmentation.

    Args:
        model_path (str): Path to a SentencePiece model file (.model).
        pad_idx (int, optional): Padding token index. If None, uses value from
            config. Defaults to None.
        unk_idx (int, optional): Unknown token index. If None, uses value from
            config. Defaults to None.
        sos_idx (int, optional): Start-of-sequence token index. If None, uses
            value from config. Defaults to None.
        eos_idx (int, optional): End-of-sequence token index. If None, uses
            value from config. Defaults to None.
        config (Config, optional): Configuration object to use for default values.
            If None, uses get_default_config(). Defaults to None.

    Raises:
        FileNotFoundError: If the model file does not exist.
        RuntimeError: If the model cannot be loaded by SentencePiece.

    Attributes:
        sp (spm.SentencePieceProcessor): The loaded SentencePiece model instance.
        pad_idx (int): Padding token index.
        unk_idx (int): Unknown token index.
        sos_idx (int): Start-of-sequence token index.
        eos_idx (int): End-of-sequence token index.
    """

    def __init__(
        self,
        model_path: str,
        pad_idx: Optional[int] = None,
        unk_idx: Optional[int] = None,
        sos_idx: Optional[int] = None,
        eos_idx: Optional[int] = None,
        config: Optional[Config] = None,
    ) -> None:
        cfg = config if config is not None else get_default_config()
        super().__init__(
            pad_idx=pad_idx,
            unk_idx=unk_idx,
            sos_idx=sos_idx,
            eos_idx=eos_idx,
            pad_token=cfg.pad_token,
            unk_token=cfg.unk_token,
            sos_token=cfg.sos_token,
            eos_token=cfg.eos_token,
            config=cfg,
        )

        # Load sentencepiece processor; the load() call returns False when the
        # model could not be found/loaded which we surface as FileNotFoundError
        # to make failures explicit and easy to debug in upstream code.
        self.sp: spm.SentencePieceProcessor = spm.SentencePieceProcessor()
        loaded = self.sp.load(model_path)
        if not loaded:
            raise FileNotFoundError(f"SentencePiece model not found: {model_path}")

    def __len__(self) -> int:
        """Return the vocabulary size (number of pieces).

        Returns:
            int: Total number of subword pieces in the SentencePiece model.
        """

        return self.sp.get_piece_size()

    def build_vocab(
        self, sentences: Sequence[str]
    ) -> None:  # pragma: no cover - explicit guard
        """Not supported for SentencePiece-backed vocabularies.

        SentencePiece models contain their own vocabulary learned during
        training; they cannot (and should not) be built from raw sentences
        via this wrapper. Callers who need a SentencePiece model should
        create it using the SentencePiece training utilities and pass the
        resulting `.model` file to this class.

        Args:
            sentences (Sequence[str]): Ignored.

        Raises:
            NotImplementedError: Always.
        """

        raise NotImplementedError(
            "SentencePieceVocab does not support build_vocab; train models separately."
        )

    def token_to_idx(self, token: str) -> int:
        """Convert a subword piece string to its index in the model.

        Args:
            token (str): A subword piece string.

        Returns:
            int: The index of the piece in the SentencePiece vocabulary.
        """

        return self.sp.piece_to_id(token)

    def idx_to_token(self, idx: int) -> str:
        """Convert a piece index to its subword piece string.

        Args:
            idx (int): Index in the SentencePiece vocabulary.

        Returns:
            str: The subword piece string at the given index.
        """

        return self.sp.id_to_piece(idx)

    def encode(self, sentence: str, add_special_tokens: bool = True) -> List[int]:
        """Encode a sentence using the SentencePiece model.

        Args:
            sentence (str): Raw sentence to encode.
            add_special_tokens (bool, optional): If True, prepend sos_idx and
                append eos_idx. Defaults to True.

        Returns:
            list[int]: List of subword piece indices. Shape is (num_pieces + 2,)
                if add_special_tokens is True, else (num_pieces,).
        """

        pieces = self.sp.encode(sentence, out_type=int)
        if add_special_tokens:
            return [self.sos_idx] + pieces + [self.eos_idx]
        return list(pieces)

    def decode(
        self, indices: IndexInput, skip_special_tokens: bool = True
    ) -> DecodedOutput:
        """Decode piece indices back to a sentence (supports batched inputs).

        Accepts a flat 1D sequence or a batched 2D structure (list[list[int]]
        or tensor). Batched inputs return a list of decoded strings; flat inputs
        return a single string.

        Args:
            indices (list[int], list[list[int]], tensor): 1D/2D indices or tensor.
            skip_special_tokens (bool, optional): If True, drop PAD/SOS/EOS/UNK
                tokens before decoding. Defaults to True.

        Returns:
            text (str, list[str]): Decoded string for flat inputs or list of strings for batched inputs.
        """

        normalized = self._coerce_indices(indices)

        if isinstance(normalized, Sequence) and self._is_batch(normalized):
            return [
                self.decode(list(seq), skip_special_tokens=skip_special_tokens)  # type: ignore[list-item]
                for seq in normalized
            ]

        flat: List[int] = list(normalized)  # type: ignore[list-item]
        if skip_special_tokens:
            flat = [
                idx
                for idx in flat
                if idx not in (self.pad_idx, self.unk_idx, self.sos_idx, self.eos_idx)
            ]

        if not flat:
            return ""

        return self.sp.decode(flat)


class MeCabVocab(BaseVocab):
    """Vocabulary for Japanese text using MeCab morphological analysis.

    Uses the fugashi library (a Python wrapper for MeCab) to tokenize Japanese
    text into morphemes. This is essential for Japanese NMT because Japanese
    does not use spaces between words.

    Args:
        min_freq (int, optional): Minimum frequency threshold for including a
            token in the vocabulary. Tokens appearing fewer than min_freq times
            are mapped to the UNK token index. If None, uses value from config.
            Defaults to None.
        pad_token (str, optional): Padding token string. If None, uses value from
            config. Defaults to None.
        unk_token (str, optional): Unknown token string. If None, uses value from
            config. Defaults to None.
        sos_token (str, optional): Start-of-sequence token string. If None, uses
            value from config. Defaults to None.
        eos_token (str, optional): End-of-sequence token string. If None, uses
            value from config. Defaults to None.
        pad_idx (int, optional): Padding token index. If None, uses value from
            config. Defaults to None.
        unk_idx (int, optional): Unknown token index. If None, uses value from
            config. Defaults to None.
        sos_idx (int, optional): Start-of-sequence token index. If None, uses
            value from config. Defaults to None.
        eos_idx (int, optional): End-of-sequence token index. If None, uses
            value from config. Defaults to None.
        config (Config, optional): Configuration object to use for default values.
            If None, uses get_default_config(). Defaults to None.

    Raises:
        ImportError: If fugashi is not installed.

    Attributes:
        tagger: The MeCab tagger instance from fugashi.
        token2idx (dict): Mapping from token strings to integer indices.
        idx2token (dict): Mapping from integer indices to token strings.
        token_freqs (dict): Frequency count for each observed token.
        min_freq (int): Minimum frequency threshold.

    Examples:
        >>> from torchlingo.data_processing import MeCabVocab
        >>> vocab = MeCabVocab(min_freq=1)
        >>> vocab.build_vocab(["私は学生です", "彼は先生です"])
        >>> indices = vocab.encode("私は学生です")
        >>> decoded = vocab.decode(indices)

    Note:
        Requires installation: ``pip install fugashi[unidic-lite]``
    """

    def __init__(
        self,
        min_freq: Optional[int] = None,
        *,
        pad_token: Optional[str] = None,
        unk_token: Optional[str] = None,
        sos_token: Optional[str] = None,
        eos_token: Optional[str] = None,
        pad_idx: Optional[int] = None,
        unk_idx: Optional[int] = None,
        sos_idx: Optional[int] = None,
        eos_idx: Optional[int] = None,
        config: Optional[Config] = None,
    ) -> None:
        try:
            import fugashi
        except ImportError as e:
            raise ImportError(
                "MeCabVocab requires fugashi. Install with: "
                "pip install fugashi[unidic-lite]"
            ) from e

        cfg = config if config is not None else get_default_config()
        super().__init__(
            pad_token=pad_token,
            unk_token=unk_token,
            sos_token=sos_token,
            eos_token=eos_token,
            pad_idx=pad_idx,
            unk_idx=unk_idx,
            sos_idx=sos_idx,
            eos_idx=eos_idx,
            config=cfg,
        )

        self.min_freq = min_freq if min_freq is not None else cfg.min_freq
        self.tagger = fugashi.Tagger()
        self.token2idx: dict[str, int] = {
            self.pad_token: self.pad_idx,
            self.unk_token: self.unk_idx,
            self.sos_token: self.sos_idx,
            self.eos_token: self.eos_idx,
        }
        self.idx2token: dict[int, str] = {
            idx: tok for tok, idx in self.token2idx.items()
        }
        self.token_freqs: dict[str, int] = {}

    def _tokenize(self, sentence: str) -> List[str]:
        """Tokenize a Japanese sentence using MeCab.

        Args:
            sentence (str): Raw Japanese sentence.

        Returns:
            List[str]: List of morpheme tokens.
        """
        return [word.surface for word in self.tagger(sentence)]

    def __len__(self) -> int:
        """Return the total vocabulary size.

        Returns:
            int: Number of unique tokens in the vocabulary, including special tokens.
        """
        return len(self.token2idx)

    def build_vocab(self, sentences: Sequence[str]) -> None:
        """Build the vocabulary from a list of Japanese sentences.

        Tokenizes each sentence using MeCab and counts token frequencies.
        Adds tokens with frequency >= min_freq to the vocabulary, skipping
        special tokens that are pre-initialized.

        Args:
            sentences (Sequence[str]): List of raw Japanese sentences to build
                vocabulary from.

        Notes:
            - Modifies self.token_freqs and self.token2idx in place.
            - Special tokens (PAD, UNK, SOS, EOS) are not overwritten.
            - Tokens are assigned indices in order of appearance in the iteration.
        """
        for sentence in sentences:
            for token in self._tokenize(sentence):
                self.token_freqs[token] = self.token_freqs.get(token, 0) + 1

        for token, freq in self.token_freqs.items():
            if freq >= self.min_freq and token not in self.token2idx:
                idx = len(self.token2idx)
                self.token2idx[token] = idx
                self.idx2token[idx] = token

    def token_to_idx(self, token: str) -> int:
        """Convert a single token string to its vocabulary index.

        Args:
            token (str): The token to convert.

        Returns:
            int: The vocabulary index of the token. Returns unk_idx if the token
                is not in the vocabulary.
        """
        return self.token2idx.get(token, self.unk_idx)

    def idx_to_token(self, idx: int) -> str:
        """Convert a vocabulary index to its token string.

        Args:
            idx (int): The vocabulary index.

        Returns:
            str: The token string corresponding to the index. Returns unk_token
                if the index is not in the vocabulary.
        """
        return self.idx2token.get(idx, self.unk_token)

    def encode(self, sentence: str, add_special_tokens: bool = True) -> List[int]:
        """Encode a Japanese sentence to a list of vocabulary indices.

        Tokenizes the sentence using MeCab and converts each token to its
        vocabulary index. Optionally prepends SOS and appends EOS indices.

        Args:
            sentence (str): Raw Japanese sentence string.
            add_special_tokens (bool, optional): If True, prepend SOS_IDX and
                append EOS_IDX to the sequence. Defaults to True.

        Returns:
            List[int]: Encoded sequence of vocabulary indices.

        Examples:
            >>> vocab = MeCabVocab(min_freq=1)
            >>> vocab.build_vocab(["私は学生です", "彼は先生です"])
            >>> indices = vocab.encode("私は学生です", add_special_tokens=False)
        """
        tokens = self._tokenize(sentence)
        indices = self.tokens_to_indices(tokens)
        if add_special_tokens:
            indices = [self.sos_idx] + indices + [self.eos_idx]
        return indices

    def decode(
        self, indices: IndexInput, skip_special_tokens: bool = True
    ) -> DecodedOutput:
        """Decode indices back to Japanese text (supports batched inputs).

        Accepts a flat 1D sequence of indices or a batched 2D structure
        (list[list[int]] or tensor of shape [batch, seq]). Batched inputs
        return a list of decoded strings; flat inputs return a single string.

        Note:
            Japanese text is reconstructed by joining tokens without spaces,
            which is the convention for Japanese.

        Args:
            indices (IndexInput): 1D indices, 2D nested indices, or tensor.
            skip_special_tokens (bool, optional): If True, drop PAD/SOS/EOS/UNK
                tokens. Defaults to True.

        Returns:
            DecodedOutput: Decoded text for each sequence.

        Examples:
            >>> vocab = MeCabVocab(min_freq=1)
            >>> vocab.build_vocab(["私は学生です"])
            >>> indices = vocab.encode("私は学生です")
            >>> decoded = vocab.decode(indices)
            >>> decoded
            '私は学生です'
        """
        normalized = self._coerce_indices(indices)

        if isinstance(normalized, Sequence) and self._is_batch(normalized):
            return [
                self.decode(list(seq), skip_special_tokens=skip_special_tokens)
                for seq in normalized
            ]

        flat: List[int] = list(normalized)  # type: ignore[list-item]
        tokens = self.indices_to_tokens(flat)

        if skip_special_tokens:
            specials = {self.pad_token, self.unk_token, self.sos_token, self.eos_token}
            tokens = [tok for tok in tokens if tok not in specials]

        # Japanese text: join without spaces
        return "".join(tokens)


class JiebaVocab(BaseVocab):
    """Vocabulary for Chinese text using jieba word segmentation.

    Uses the jieba library to segment Chinese text into words. This is essential
    for Chinese NMT because Chinese does not use spaces between words.

    Args:
        min_freq (int, optional): Minimum frequency threshold for including a
            token in the vocabulary. Tokens appearing fewer than min_freq times
            are mapped to the UNK token index. If None, uses value from config.
            Defaults to None.
        cut_all (bool, optional): Whether to use jieba's full mode (True) or
            accurate mode (False). Accurate mode is recommended for NMT.
            Defaults to False.
        use_paddle (bool, optional): Whether to use PaddlePaddle-based word
            segmentation for improved accuracy. Requires paddlepaddle.
            Defaults to False.
        pad_token (str, optional): Padding token string. If None, uses value from
            config. Defaults to None.
        unk_token (str, optional): Unknown token string. If None, uses value from
            config. Defaults to None.
        sos_token (str, optional): Start-of-sequence token string. If None, uses
            value from config. Defaults to None.
        eos_token (str, optional): End-of-sequence token string. If None, uses
            value from config. Defaults to None.
        pad_idx (int, optional): Padding token index. If None, uses value from
            config. Defaults to None.
        unk_idx (int, optional): Unknown token index. If None, uses value from
            config. Defaults to None.
        sos_idx (int, optional): Start-of-sequence token index. If None, uses
            value from config. Defaults to None.
        eos_idx (int, optional): End-of-sequence token index. If None, uses
            value from config. Defaults to None.
        config (Config, optional): Configuration object to use for default values.
            If None, uses get_default_config(). Defaults to None.

    Raises:
        ImportError: If jieba is not installed.

    Attributes:
        cut_all (bool): Whether jieba uses full mode.
        use_paddle (bool): Whether jieba uses PaddlePaddle.
        token2idx (dict): Mapping from token strings to integer indices.
        idx2token (dict): Mapping from integer indices to token strings.
        token_freqs (dict): Frequency count for each observed token.
        min_freq (int): Minimum frequency threshold.

    Examples:
        >>> from torchlingo.data_processing import JiebaVocab
        >>> vocab = JiebaVocab(min_freq=1)
        >>> vocab.build_vocab(["我是学生", "他是老师"])
        >>> indices = vocab.encode("我是学生")
        >>> decoded = vocab.decode(indices)

    Note:
        Requires installation: ``pip install jieba``
    """

    def __init__(
        self,
        min_freq: Optional[int] = None,
        cut_all: bool = False,
        use_paddle: bool = False,
        *,
        pad_token: Optional[str] = None,
        unk_token: Optional[str] = None,
        sos_token: Optional[str] = None,
        eos_token: Optional[str] = None,
        pad_idx: Optional[int] = None,
        unk_idx: Optional[int] = None,
        sos_idx: Optional[int] = None,
        eos_idx: Optional[int] = None,
        config: Optional[Config] = None,
    ) -> None:
        try:
            import jieba as _jieba

            self._jieba = _jieba
        except ImportError as e:
            raise ImportError(
                "JiebaVocab requires jieba. Install with: pip install jieba"
            ) from e

        cfg = config if config is not None else get_default_config()
        super().__init__(
            pad_token=pad_token,
            unk_token=unk_token,
            sos_token=sos_token,
            eos_token=eos_token,
            pad_idx=pad_idx,
            unk_idx=unk_idx,
            sos_idx=sos_idx,
            eos_idx=eos_idx,
            config=cfg,
        )

        self.min_freq = min_freq if min_freq is not None else cfg.min_freq
        self.cut_all = cut_all
        self.use_paddle = use_paddle

        if use_paddle:
            self._jieba.enable_paddle()

        self.token2idx: dict[str, int] = {
            self.pad_token: self.pad_idx,
            self.unk_token: self.unk_idx,
            self.sos_token: self.sos_idx,
            self.eos_token: self.eos_idx,
        }
        self.idx2token: dict[int, str] = {
            idx: tok for tok, idx in self.token2idx.items()
        }
        self.token_freqs: dict[str, int] = {}

    def _tokenize(self, sentence: str) -> List[str]:
        """Tokenize a Chinese sentence using jieba.

        Args:
            sentence (str): Raw Chinese sentence.

        Returns:
            List[str]: List of word tokens.
        """
        if self.use_paddle:
            return list(self._jieba.cut(sentence, use_paddle=True))
        return list(self._jieba.cut(sentence, cut_all=self.cut_all))

    def __len__(self) -> int:
        """Return the total vocabulary size.

        Returns:
            int: Number of unique tokens in the vocabulary, including special tokens.
        """
        return len(self.token2idx)

    def build_vocab(self, sentences: Sequence[str]) -> None:
        """Build the vocabulary from a list of Chinese sentences.

        Tokenizes each sentence using jieba and counts token frequencies.
        Adds tokens with frequency >= min_freq to the vocabulary, skipping
        special tokens that are pre-initialized.

        Args:
            sentences (Sequence[str]): List of raw Chinese sentences to build
                vocabulary from.

        Notes:
            - Modifies self.token_freqs and self.token2idx in place.
            - Special tokens (PAD, UNK, SOS, EOS) are not overwritten.
            - Tokens are assigned indices in order of appearance in the iteration.
        """
        for sentence in sentences:
            for token in self._tokenize(sentence):
                self.token_freqs[token] = self.token_freqs.get(token, 0) + 1

        for token, freq in self.token_freqs.items():
            if freq >= self.min_freq and token not in self.token2idx:
                idx = len(self.token2idx)
                self.token2idx[token] = idx
                self.idx2token[idx] = token

    def token_to_idx(self, token: str) -> int:
        """Convert a single token string to its vocabulary index.

        Args:
            token (str): The token to convert.

        Returns:
            int: The vocabulary index of the token. Returns unk_idx if the token
                is not in the vocabulary.
        """
        return self.token2idx.get(token, self.unk_idx)

    def idx_to_token(self, idx: int) -> str:
        """Convert a vocabulary index to its token string.

        Args:
            idx (int): The vocabulary index.

        Returns:
            str: The token string corresponding to the index. Returns unk_token
                if the index is not in the vocabulary.
        """
        return self.idx2token.get(idx, self.unk_token)

    def encode(self, sentence: str, add_special_tokens: bool = True) -> List[int]:
        """Encode a Chinese sentence to a list of vocabulary indices.

        Tokenizes the sentence using jieba and converts each token to its
        vocabulary index. Optionally prepends SOS and appends EOS indices.

        Args:
            sentence (str): Raw Chinese sentence string.
            add_special_tokens (bool, optional): If True, prepend SOS_IDX and
                append EOS_IDX to the sequence. Defaults to True.

        Returns:
            List[int]: Encoded sequence of vocabulary indices.

        Examples:
            >>> vocab = JiebaVocab(min_freq=1)
            >>> vocab.build_vocab(["我是学生", "他是老师"])
            >>> indices = vocab.encode("我是学生", add_special_tokens=False)
        """
        tokens = self._tokenize(sentence)
        indices = self.tokens_to_indices(tokens)
        if add_special_tokens:
            indices = [self.sos_idx] + indices + [self.eos_idx]
        return indices

    def decode(
        self, indices: IndexInput, skip_special_tokens: bool = True
    ) -> DecodedOutput:
        """Decode indices back to Chinese text (supports batched inputs).

        Accepts a flat 1D sequence of indices or a batched 2D structure
        (list[list[int]] or tensor of shape [batch, seq]). Batched inputs
        return a list of decoded strings; flat inputs return a single string.

        Note:
            Chinese text is reconstructed by joining tokens without spaces,
            which is the convention for Chinese.

        Args:
            indices (IndexInput): 1D indices, 2D nested indices, or tensor.
            skip_special_tokens (bool, optional): If True, drop PAD/SOS/EOS/UNK
                tokens. Defaults to True.

        Returns:
            DecodedOutput: Decoded text for each sequence.

        Examples:
            >>> vocab = JiebaVocab(min_freq=1)
            >>> vocab.build_vocab(["我是学生"])
            >>> indices = vocab.encode("我是学生")
            >>> decoded = vocab.decode(indices)
            >>> decoded
            '我是学生'
        """
        normalized = self._coerce_indices(indices)

        if isinstance(normalized, Sequence) and self._is_batch(normalized):
            return [
                self.decode(list(seq), skip_special_tokens=skip_special_tokens)
                for seq in normalized
            ]

        flat: List[int] = list(normalized)  # type: ignore[list-item]
        tokens = self.indices_to_tokens(flat)

        if skip_special_tokens:
            specials = {self.pad_token, self.unk_token, self.sos_token, self.eos_token}
            tokens = [tok for tok in tokens if tok not in specials]

        # Chinese text: join without spaces
        return "".join(tokens)
