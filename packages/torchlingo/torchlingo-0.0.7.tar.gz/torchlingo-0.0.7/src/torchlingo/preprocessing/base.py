"""Data loading, saving, and splitting utilities for neural machine translation.

This module provides functions for loading parallel corpora from various file
formats (TSV, CSV, Parquet, JSON), saving preprocessed data, and splitting
datasets into train/val/test splits. It serves as the foundational layer for
all downstream preprocessing operations.
"""

from pathlib import Path
from typing import Union, Tuple
import pandas as pd
from ..config import Config, get_default_config


def parallel_txt_to_dataframe(
    src_path: Path,
    tgt_path: Path,
    src_col: str = None,
    tgt_col: str = None,
    config: Config = None,
) -> pd.DataFrame:
    """Convert parallel .txt files into a single DataFrame with src/tgt columns.

    Reads two aligned text files (source and target) and combines them into a
    single DataFrame with 'src' and 'tgt' columns. Files must have an equal
    number of lines. Each line is stripped of whitespace.

    Args:
        src_path (Path): Path to source language file (one sentence per line).
        tgt_path (Path): Path to target language file (one sentence per line).
        src_col (str, optional): Column name for source text. Falls back to
            config.src_col if not provided. Defaults to None.
        tgt_col (str, optional): Column name for target text. Falls back to
            config.tgt_col if not provided. Defaults to None.
        config (Config, optional): Configuration object. If None, uses default
            config. Explicit parameters take priority over config values.

    Returns:
        pd.DataFrame: DataFrame with columns defined by src_col and tgt_col,
            containing one parallel pair per row.

    Raises:
        ValueError: If src_path and tgt_path have different number of lines.
        FileNotFoundError: If either file does not exist.

    Examples:
        >>> df = parallel_txt_to_dataframe('en.txt', 'es.txt')
        >>> print(df.columns)
        Index(['src', 'tgt'], dtype='object')
        >>> len(df)
        1000
    """
    cfg = config if config is not None else get_default_config()
    src_col = src_col if src_col is not None else cfg.src_col
    tgt_col = tgt_col if tgt_col is not None else cfg.tgt_col

    src_path = Path(src_path)
    tgt_path = Path(tgt_path)
    with open(src_path, "r", encoding="utf-8") as f_src:
        src_lines = [ln.rstrip("\n") for ln in f_src]
    with open(tgt_path, "r", encoding="utf-8") as f_tgt:
        tgt_lines = [ln.rstrip("\n") for ln in f_tgt]
    if len(src_lines) != len(tgt_lines):
        raise ValueError(
            f"Parallel files have different number of lines: {src_path} ({len(src_lines)}), {tgt_path} ({len(tgt_lines)})"
        )
    pairs = []
    for s, t in zip(src_lines, tgt_lines):
        pairs.append({src_col: s.strip(), tgt_col: t.strip()})
    return pd.DataFrame(pairs)


def load_data(filepath: Union[Path, str], format: str = None) -> pd.DataFrame:
    """Load a single structured data file containing src/tgt columns.

    Supports multiple file formats and automatically detects format from file
    extension if not explicitly specified. Single-file inputs only; for
    parallel .txt corpora, use parallel_txt_to_dataframe first.

    Args:
        filepath (Path | str): Path to the data file.
        format (str, optional): File format ('tsv', 'csv', 'parquet', 'json').
            If None, inferred from file extension. Defaults to None.

    Returns:
        pd.DataFrame: Loaded data with src/tgt columns.

    Raises:
        ValueError: If format is 'txt' (must use parallel_txt_to_dataframe),
            or if format is unsupported.
        FileNotFoundError: If filepath does not exist.

    Examples:
        >>> df = load_data('data.tsv')
        >>> df = load_data('data.csv', format='csv')
        >>> df = load_data('data.parquet')
    """
    filepath = Path(filepath)
    if format is None:
        format = filepath.suffix.lstrip(".")
    if format == "tsv":
        return pd.read_csv(filepath, sep="\t")
    elif format == "csv":
        return pd.read_csv(filepath)
    elif format == "parquet":
        return pd.read_parquet(filepath)
    elif format == "json":
        return pd.read_json(filepath, lines=True)
    elif format == "txt":
        raise ValueError(
            "Single-file 'txt' format is not supported. Convert parallel txt files to a DataFrame first using parallel_txt_to_dataframe."
        )
    else:
        raise ValueError(f"Unsupported format: {format}")


def save_data(df: pd.DataFrame, filepath: Path, format: str = None):
    """Save a DataFrame to disk in the specified format.

    Creates parent directories as needed. Automatically detects format from
    file extension if not explicitly specified. Prints a confirmation message
    with record count and output path.

    Args:
        df (pd.DataFrame): DataFrame to save with src/tgt columns.
        filepath (Path): Destination file path.
        format (str, optional): Output format ('tsv', 'csv', 'parquet', 'json').
            If None, inferred from file extension. Defaults to None.

    Raises:
        ValueError: If format is unsupported.

    Examples:
        >>> save_data(df, Path('output.tsv'))
        Saved 1000 records to output.tsv
        >>> save_data(df, Path('output.json'), format='json')
    """
    if format is None:
        format = filepath.suffix.lstrip(".")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if format == "tsv":
        df.to_csv(filepath, sep="\t", index=False)
    elif format == "csv":
        df.to_csv(filepath, index=False)
    elif format == "parquet":
        df.to_parquet(filepath, index=False)
    elif format == "json":
        df.to_json(filepath, orient="records", lines=True)
    else:
        raise ValueError(f"Unsupported format: {format}")
    print(f"Saved {len(df)} records to {filepath}")


def split_data(
    df: pd.DataFrame,
    train_ratio: float = None,
    val_ratio: float = None,
    seed: int = None,
    config: Config = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a DataFrame into train, validation, and test sets.

    Shuffles the entire DataFrame using the provided seed for reproducibility,
    then partitions by ratio. Test set is the remainder after train and val.

    Args:
        df (pd.DataFrame): Input DataFrame to split.
        train_ratio (float, optional): Fraction of data for training. Falls back
            to config.train_ratio if not provided. Defaults to None.
        val_ratio (float, optional): Fraction of data for validation. Falls back
            to config.val_ratio if not provided. Defaults to None.
            Remaining (1 - train_ratio - val_ratio) goes to test.
        seed (int, optional): Random seed for reproducibility. Falls back to
            config.seed if not provided. Defaults to None.
        config (Config, optional): Configuration object. If None, uses default
            config. Explicit parameters take priority over config values.

    Returns:
        tuple: (train_df, val_df, test_df) as pandas DataFrames.

    Examples:
        >>> train, val, test = split_data(df, train_ratio=0.8, val_ratio=0.1)
        >>> len(train), len(val), len(test)
        (800, 100, 100)
    """
    cfg = config if config is not None else get_default_config()
    train_ratio = train_ratio if train_ratio is not None else cfg.train_ratio
    val_ratio = val_ratio if val_ratio is not None else cfg.val_ratio
    seed = seed if seed is not None else cfg.seed

    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]
    return train_df, val_df, test_df


# (No train_test_split alias here; use `split_data`.)


def preprocess_base(
    raw_data_file: Path = None,
    train_file: Path = None,
    val_file: Path = None,
    test_file: Path = None,
    src_col: str = None,
    tgt_col: str = None,
    data_format: str = None,
    train_ratio: float = None,
    val_ratio: float = None,
    seed: int = None,
    config: Config = None,
):
    """Execute base preprocessing pipeline on raw data.

    Loads raw data from raw_data_file, renames columns if needed
    (auto-detects 2-column format), and splits into train/val/test using
    split_data(). Saves each split to its configured path.

    Args:
        raw_data_file (Path, optional): Path to raw data file. Falls back to
            config.raw_data_file if not provided. Defaults to None.
        train_file (Path, optional): Output path for training data. Falls back
            to config.train_file if not provided. Defaults to None.
        val_file (Path, optional): Output path for validation data. Falls back
            to config.val_file if not provided. Defaults to None.
        test_file (Path, optional): Output path for test data. Falls back to
            config.test_file if not provided. Defaults to None.
        src_col (str, optional): Source column name. Falls back to
            config.src_col if not provided. Defaults to None.
        tgt_col (str, optional): Target column name. Falls back to
            config.tgt_col if not provided. Defaults to None.
        data_format (str, optional): Output format (tsv, csv, etc). Falls back
            to config.data_format if not provided. Defaults to None.
        train_ratio (float, optional): Fraction of data for training. Falls back
            to config.train_ratio if not provided. Defaults to None.
        val_ratio (float, optional): Fraction of data for validation. Falls back
            to config.val_ratio if not provided. Defaults to None.
        seed (int, optional): Random seed for splitting. Falls back to
            config.seed if not provided. Defaults to None.
        config (Config, optional): Configuration object. If None, uses default
            config. Explicit parameters take priority over config values.

    Raises:
        ValueError: If data does not have exactly 2 columns or cannot be renamed.

    Side Effects:
        - Prints diagnostic messages about column renaming and completion.
        - Creates train_file, val_file, test_file.
    """
    cfg = config if config is not None else get_default_config()
    raw_data_file = raw_data_file if raw_data_file is not None else cfg.raw_data_file
    train_file = train_file if train_file is not None else cfg.train_file
    val_file = val_file if val_file is not None else cfg.val_file
    test_file = test_file if test_file is not None else cfg.test_file
    src_col = src_col if src_col is not None else cfg.src_col
    tgt_col = tgt_col if tgt_col is not None else cfg.tgt_col
    data_format = data_format if data_format is not None else cfg.data_format
    train_ratio = train_ratio if train_ratio is not None else cfg.train_ratio
    val_ratio = val_ratio if val_ratio is not None else cfg.val_ratio
    seed = seed if seed is not None else cfg.seed

    if not raw_data_file.exists():
        print(f"Error: Raw data file not found at {raw_data_file}")
        print(
            "Please create a TSV/CSV file with columns 'src' and 'tgt', or pass explicit source & target file paths."
        )
        return
    df = load_data(raw_data_file)
    if src_col not in df.columns or tgt_col not in df.columns:
        if len(df.columns) == 2:
            print(f"Renaming columns {df.columns.tolist()} to {src_col}, {tgt_col}")
            df.columns = [src_col, tgt_col]
        else:
            raise ValueError(f"Data must have columns '{src_col}' and '{tgt_col}'")
    train, val, test = split_data(
        df, train_ratio=train_ratio, val_ratio=val_ratio, seed=seed
    )
    save_data(train, train_file, data_format)
    save_data(val, val_file, data_format)
    save_data(test, test_file, data_format)
    print("Base preprocessing complete.")
