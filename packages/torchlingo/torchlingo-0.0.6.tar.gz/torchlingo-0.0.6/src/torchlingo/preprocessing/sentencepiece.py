"""SentencePiece tokenization preprocessing for neural machine translation.

This module provides utilities for training and applying SentencePiece subword
tokenization models. SentencePiece enables language-agnostic, vocabulary-size
efficient tokenization suitable for multilingual and low-resource scenarios.
"""

from pathlib import Path
from typing import List, Optional
import sentencepiece as spm
from ..config import Config, get_default_config
from .base import load_data, save_data, preprocess_base


def train_sentencepiece(
    input_files: List[Path],
    model_prefix: str,
    vocab_size: int = None,
    columns: Optional[List[str]] = None,
    src_col: str = None,
    tgt_col: str = None,
    model_type: str = None,
    character_coverage: float = None,
    normalization_rule_name: str = None,
    pad_idx: int = None,
    unk_idx: int = None,
    sos_idx: int = None,
    eos_idx: int = None,
    pad_token: str = None,
    unk_token: str = None,
    sos_token: str = None,
    eos_token: str = None,
    config: Config = None,
):
    """Train a SentencePiece tokenization model on raw text data.

    Reads all input files, extracts selected columns (src/tgt by default),
    concatenates them into a temporary file, and trains a SentencePiece model. Model files
    are saved with the specified prefix (e.g., 'model.model' and 'model.vocab').

    Model training respects configuration for normalization, special tokens,
    and character coverage.

    Args:
        input_files (List[Path]): Data files to use for training.
        model_prefix (str): Output prefix for .model and .vocab files.
        vocab_size (int, optional): Target vocabulary size. Falls back to config.vocab_size.
        columns (List[str], optional): Columns to use for training data. Defaults
            to [src_col, tgt_col].
        src_col (str, optional): Source column name. Falls back to config.src_col.
        tgt_col (str, optional): Target column name. Falls back to config.tgt_col.
        model_type (str, optional): SentencePiece model type. Falls back to config.sp_model_type.
        character_coverage (float, optional): Character coverage. Falls back to config.sp_character_coverage.
        normalization_rule_name (str, optional): Normalization rule. Falls back to config.sp_normalization_rule_name.
        pad_idx (int, optional): Padding token index. Falls back to config.pad_idx.
        unk_idx (int, optional): Unknown token index. Falls back to config.unk_idx.
        sos_idx (int, optional): Start-of-sequence token index. Falls back to config.sos_idx.
        eos_idx (int, optional): End-of-sequence token index. Falls back to config.eos_idx.
        pad_token (str, optional): Padding token string. Falls back to config.pad_token.
        unk_token (str, optional): Unknown token string. Falls back to config.unk_token.
        sos_token (str, optional): Start-of-sequence token string. Falls back to config.sos_token.
        eos_token (str, optional): End-of-sequence token string. Falls back to config.eos_token.
        config (Config, optional): Configuration object. Falls back to get_default_config().

    Side Effects:
        - Creates temporary file during training (automatically cleaned up).
        - Writes {model_prefix}.model and {model_prefix}.vocab to disk.
        - Prints confirmation message with output path.

    Examples:
        >>> train_sentencepiece([Path('train.tsv')], 'models/sp', vocab_size=16000)
        SentencePiece model saved to models/sp.model
    """
    import tempfile

    cfg = config if config is not None else get_default_config()
    vocab_size = vocab_size if vocab_size is not None else cfg.vocab_size
    src_col = src_col if src_col is not None else cfg.src_col
    tgt_col = tgt_col if tgt_col is not None else cfg.tgt_col
    model_type = model_type if model_type is not None else cfg.sp_model_type
    character_coverage = (
        character_coverage
        if character_coverage is not None
        else cfg.sp_character_coverage
    )
    normalization_rule_name = (
        normalization_rule_name
        if normalization_rule_name is not None
        else cfg.sp_normalization_rule_name
    )
    pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx
    unk_idx = unk_idx if unk_idx is not None else cfg.unk_idx
    sos_idx = sos_idx if sos_idx is not None else cfg.sos_idx
    eos_idx = eos_idx if eos_idx is not None else cfg.eos_idx
    pad_token = pad_token if pad_token is not None else cfg.pad_token
    unk_token = unk_token if unk_token is not None else cfg.unk_token
    sos_token = sos_token if sos_token is not None else cfg.sos_token
    eos_token = eos_token if eos_token is not None else cfg.eos_token

    cols = columns or [src_col, tgt_col]

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        for f in input_files:
            df = load_data(f)
            for col in cols:
                if col in df.columns:
                    for line in df[col].astype(str):
                        tmp.write(line + "\n")
        tmp_path = tmp.name

    try:
        spm.SentencePieceTrainer.train(
            input=tmp_path,
            model_prefix=model_prefix,
            vocab_size=vocab_size,
            model_type=model_type,
            character_coverage=character_coverage,
            normalization_rule_name=normalization_rule_name,
            pad_id=pad_idx,
            unk_id=unk_idx,
            bos_id=sos_idx,
            eos_id=eos_idx,
            pad_piece=pad_token,
            unk_piece=unk_token,
            bos_piece=sos_token,
            eos_piece=eos_token,
        )
        print(f"SentencePiece model saved to {model_prefix}.model")
    finally:
        Path(tmp_path).unlink()


def apply_sentencepiece(
    input_file: Path,
    output_file: Path,
    sp_src_model: spm.SentencePieceProcessor,
    sp_tgt_model: Optional[spm.SentencePieceProcessor] = None,
    src_col: str = None,
    tgt_col: str = None,
    config: Config = None,
):
    """Apply trained SentencePiece tokenization to all src/tgt columns.

    Accepts input_file/output_file as either a str or pathlib.Path. Accepts
    sp_src_model and sp_tgt_model as either a filesystem path (str/Path) pointing
    to a .model file or an already-loaded sentencepiece.SentencePieceProcessor.

    Args:
        input_file (Path or str): Input data file with src/tgt columns.
        output_file (Path or str): Output path for tokenized data.
        sp_src_model (str, Path, or spm.SentencePieceProcessor): Path to or loaded SentencePiece model for src.
        sp_tgt_model (str, Path, or spm.SentencePieceProcessor, optional): Path to or loaded model for target. If None, reuse source model.
        src_col (str, optional): Source column name. Falls back to config.src_col.
        tgt_col (str, optional): Target column name. Falls back to config.tgt_col.
        config (Config, optional): Configuration object. Falls back to get_default_config().

    Side Effects:
        - Modifies src_col and tgt_col columns in-place during DataFrame manipulation.
        - Creates output file with same format as input.
    """
    # Normalize path-like arguments to Path
    if not isinstance(input_file, Path):
        input_file = Path(input_file)
    if not isinstance(output_file, Path):
        output_file = Path(output_file)

    # Helper to ensure we have a SentencePieceProcessor instance.
    def _ensure_processor(m):
        # Accept either a real SentencePieceProcessor, a filesystem path to a
        # model, or any object that implements the sentencepiece processor
        # API (duck-typed). This lets tests pass a MagicMock with an
        # `encode`/`load`/`decode` attribute without requiring an actual
        # SentencePieceProcessor instance.
        if m is None:
            return None
        if isinstance(m, (str, Path)):
            proc = spm.SentencePieceProcessor()
            proc.load(str(m))
            return proc
        # Prefer exact type check when available
        try:
            if isinstance(m, spm.SentencePieceProcessor):
                return m
        except Exception:
            # If spm.SentencePieceProcessor isn't importable or isinstance
            # raises for some reason, fall back to duck typing below.
            pass

        # Duck-typing: accept any object exposing the encode method
        if hasattr(m, "encode"):
            return m

        raise TypeError(
            "sp_src_model/sp_tgt_model must be a path (str/Path) or SentencePieceProcessor-like object"
        )

    sp_src_model = _ensure_processor(sp_src_model)
    sp_tgt_model = (
        _ensure_processor(sp_tgt_model) if sp_tgt_model is not None else sp_src_model
    )
    cfg = config if config is not None else get_default_config()
    src_col = src_col if src_col is not None else cfg.src_col
    tgt_col = tgt_col if tgt_col is not None else cfg.tgt_col

    df = load_data(input_file)
    sp_tgt_model = sp_tgt_model or sp_src_model
    for col in [src_col, tgt_col]:
        if col in df.columns:
            model = sp_src_model if col == src_col else sp_tgt_model
            df[col] = (
                df[col]
                .astype(str)
                .apply(lambda x: " ".join(model.encode(x, out_type=str)))
            )
    save_data(df, output_file)


def preprocess_sentencepiece(
    train_file: Path = None,
    val_file: Path = None,
    test_file: Path = None,
    sp_src_model_prefix: str = None,
    sp_tgt_model_prefix: str = None,
    sp_src_model: str = None,
    sp_tgt_model: str = None,
    vocab_size: int = None,
    src_col: str = None,
    tgt_col: str = None,
    data_dir: Path = None,
    data_format: str = None,
    config: Config = None,
):
    """Execute SentencePiece tokenization preprocessing pipeline.

    Calls preprocess_base() if needed, trains a SentencePiece model on training
    data, then applies tokenization to train/val/test splits. Supports either
    a shared model for src/tgt or distinct models for each side. All tokenized
    outputs are saved to a 'tokenized' subdirectory under data_dir.

    Args:
        train_file (Path, optional): Path to training data. Falls back to config.train_file.
        val_file (Path, optional): Path to validation data. Falls back to config.val_file.
        test_file (Path, optional): Path to test data. Falls back to config.test_file.
        sp_src_model_prefix (str, optional): Prefix for source SentencePiece model. Falls back to config.sentencepiece_src_model_prefix.
        sp_tgt_model_prefix (str, optional): Prefix for target SentencePiece model. Falls back to config.sentencepiece_tgt_model_prefix.
        sp_src_model (str, optional): Path to source SentencePiece model. Falls back to config.sentencepiece_src_model.
        sp_tgt_model (str, optional): Path to target SentencePiece model. Falls back to config.sentencepiece_tgt_model.
        vocab_size (int, optional): Target vocabulary size. Falls back to config.vocab_size.
        src_col (str, optional): Source column name. Falls back to config.src_col.
        tgt_col (str, optional): Target column name. Falls back to config.tgt_col.
        data_dir (Path, optional): Data directory. Falls back to config.data_dir.
        data_format (str, optional): Data file format. Falls back to config.data_format.
        config (Config, optional): Configuration object. Falls back to get_default_config().

    Creates:
        - {data_dir}/tokenized/train.{data_format}
        - {data_dir}/tokenized/val.{data_format}
        - {data_dir}/tokenized/test.{data_format}

    Also generates SentencePiece model files at the configured prefixes.

    Side Effects:
        - Prints tokenization progress for each file.
        - Creates {data_dir}/tokenized/ directory.

    Examples:
        >>> preprocess_sentencepiece()
        Tokenized ./data/train.tsv -> ./data/tokenized/train.tsv
        Tokenized ./data/val.tsv -> ./data/tokenized/val.tsv
        Tokenized ./data/test.tsv -> ./data/tokenized/test.tsv
    """
    cfg = config if config is not None else get_default_config()
    train_file = train_file if train_file is not None else cfg.train_file
    val_file = val_file if val_file is not None else cfg.val_file
    test_file = test_file if test_file is not None else cfg.test_file
    sp_src_model_prefix = (
        sp_src_model_prefix
        if sp_src_model_prefix is not None
        else cfg.sentencepiece_src_model_prefix
    )
    sp_tgt_model_prefix = (
        sp_tgt_model_prefix
        if sp_tgt_model_prefix is not None
        else cfg.sentencepiece_tgt_model_prefix
    )
    sp_src_model = (
        sp_src_model if sp_src_model is not None else cfg.sentencepiece_src_model
    )
    sp_tgt_model = (
        sp_tgt_model if sp_tgt_model is not None else cfg.sentencepiece_tgt_model
    )
    vocab_size = vocab_size if vocab_size is not None else cfg.vocab_size
    src_col = src_col if src_col is not None else cfg.src_col
    tgt_col = tgt_col if tgt_col is not None else cfg.tgt_col
    data_dir = data_dir if data_dir is not None else cfg.data_dir
    data_format = data_format if data_format is not None else cfg.data_format

    if not train_file.exists():
        preprocess_base(config=cfg)

    share_model = sp_src_model == sp_tgt_model

    if share_model:
        train_sentencepiece(
            [train_file],
            sp_src_model_prefix,
            vocab_size=vocab_size,
            columns=[src_col, tgt_col],
            src_col=src_col,
            tgt_col=tgt_col,
            config=cfg,
        )
    else:
        train_sentencepiece(
            [train_file],
            sp_src_model_prefix,
            vocab_size=vocab_size,
            columns=[src_col],
            src_col=src_col,
            tgt_col=tgt_col,
            config=cfg,
        )
        train_sentencepiece(
            [train_file],
            sp_tgt_model_prefix,
            vocab_size=vocab_size,
            columns=[tgt_col],
            src_col=src_col,
            tgt_col=tgt_col,
            config=cfg,
        )

    sp_src = spm.SentencePieceProcessor()
    sp_src.load(sp_src_model)
    sp_tgt = sp_src
    if not share_model:
        sp_tgt = spm.SentencePieceProcessor()
        sp_tgt.load(sp_tgt_model)
    tokenized_dir = data_dir / "tokenized"
    tokenized_dir.mkdir(exist_ok=True)
    files = [
        (train_file, tokenized_dir / f"train.{data_format}"),
        (val_file, tokenized_dir / f"val.{data_format}"),
        (test_file, tokenized_dir / f"test.{data_format}"),
    ]
    for inp, out in files:
        if inp.exists():
            apply_sentencepiece(
                inp,
                out,
                sp_src,
                sp_tgt_model=sp_tgt,
                src_col=src_col,
                tgt_col=tgt_col,
                config=cfg,
            )
            print(f"Tokenized {inp} -> {out}")
