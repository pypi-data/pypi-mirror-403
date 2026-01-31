"""Multilingual preprocessing for bidirectional neural machine translation.

This module handles data preparation for multilingual models by adding language
tags to source text and creating bidirectional (X↔EN) training pairs. It
supports training on paired language directions (EN→X and X→EN simultaneously).
"""

from pathlib import Path

import pandas as pd

from ..config import Config, get_default_config
from .base import load_data, save_data


def add_language_tags(
    df: pd.DataFrame,
    tag: str,
    src_col: str = None,
    config: Config = None,
) -> pd.DataFrame:
    """Prepend a language tag to all source sentences.

    Creates a copy of the input DataFrame and prepends a language identifier
    token to the source column. Used to signal target language to multilingual
    models.

    Args:
        df (pd.DataFrame): Input DataFrame with source/target columns.
        tag (str): Language tag to prepend (e.g., '<en>', '<es>').
        src_col (str, optional): Source column name. Falls back to config.src_col.
            Defaults to None.
        config (Config, optional): Configuration object. Defaults to default config.

    Returns:
        pd.DataFrame: Copy of df with language tag prepended to src_col.

    Examples:
        >>> df = pd.DataFrame({'src': ['hello'], 'tgt': ['hola']})
        >>> tagged = add_language_tags(df, '<es>')
        >>> tagged['src'].iloc[0]
        '<es> hello'
    """
    cfg = config if config is not None else get_default_config()
    src_col = src_col if src_col is not None else cfg.src_col

    df = df.copy()
    df[src_col] = tag + " " + df[src_col].astype(str)
    return df


def preprocess_multilingual(
    train_file: Path = None,
    val_file: Path = None,
    test_file: Path = None,
    src_col: str = None,
    tgt_col: str = None,
    lang_tag_en_to_x: str = None,
    lang_tag_x_to_en: str = None,
    seed: int = None,
    multi_train_file: Path = None,
    multi_val_file: Path = None,
    test_en_x_file: Path = None,
    test_x_en_file: Path = None,
    data_format: str = None,
    config: Config = None,
):
    """Execute multilingual preprocessing pipeline.

    Loads train/val/test splits created by preprocess_base(), creates
    bidirectional pairs (EN→X and X→EN), tags each direction with appropriate
    language tags, and saves to multilingual-specific output files.

    Requires base preprocessing to have completed (train_file, etc. exist).

    Args:
        train_file (Path, optional): Path to training data. Falls back to config.train_file.
        val_file (Path, optional): Path to validation data. Falls back to config.val_file.
        test_file (Path, optional): Path to test data. Falls back to config.test_file.
        src_col (str, optional): Source column name. Falls back to config.src_col.
        tgt_col (str, optional): Target column name. Falls back to config.tgt_col.
        lang_tag_en_to_x (str, optional): Language tag for EN→X direction.
            Falls back to config.lang_tag_en_to_x.
        lang_tag_x_to_en (str, optional): Language tag for X→EN direction.
            Falls back to config.lang_tag_x_to_en.
        seed (int, optional): Random seed for shuffling. Falls back to config.seed.
        multi_train_file (Path, optional): Output path for multilingual training data.
            Falls back to config.multi_train_file.
        multi_val_file (Path, optional): Output path for multilingual validation data.
            Falls back to config.multi_val_file.
        test_en_x_file (Path, optional): Output path for EN→X test set.
            Falls back to config.test_en_x_file.
        test_x_en_file (Path, optional): Output path for X→EN test set.
            Falls back to config.test_x_en_file.
        data_format (str, optional): Output file format. Falls back to config.data_format.
        config (Config, optional): Configuration object. Defaults to default config.

    Creates:
        - multi_train_file: Combined and shuffled EN→X and X→EN pairs.
        - multi_val_file: Combined and shuffled EN→X and X→EN pairs.
        - test_en_x_file: Test set for EN→X direction.
        - test_x_en_file: Test set for X→EN direction.

    Side Effects:
        Prints status message on completion. Shuffles training/validation
        using seed for reproducibility. Saves files per specified paths.

    Examples:
        >>> preprocess_multilingual()
        Multilingual preprocessing complete.
    """
    cfg = config if config is not None else get_default_config()
    train_file = train_file if train_file is not None else cfg.train_file
    val_file = val_file if val_file is not None else cfg.val_file
    test_file = test_file if test_file is not None else cfg.test_file
    src_col = src_col if src_col is not None else cfg.src_col
    tgt_col = tgt_col if tgt_col is not None else cfg.tgt_col
    lang_tag_en_to_x = (
        lang_tag_en_to_x if lang_tag_en_to_x is not None else cfg.lang_tag_en_to_x
    )
    lang_tag_x_to_en = (
        lang_tag_x_to_en if lang_tag_x_to_en is not None else cfg.lang_tag_x_to_en
    )
    seed = seed if seed is not None else cfg.seed
    multi_train_file = (
        multi_train_file if multi_train_file is not None else cfg.multi_train_file
    )
    multi_val_file = (
        multi_val_file if multi_val_file is not None else cfg.multi_val_file
    )
    test_en_x_file = (
        test_en_x_file if test_en_x_file is not None else cfg.test_en_x_file
    )
    test_x_en_file = (
        test_x_en_file if test_x_en_file is not None else cfg.test_x_en_file
    )
    data_format = data_format if data_format is not None else cfg.data_format

    if not train_file.exists():
        print("Run base preprocessing first to generate train/val/test.")
        return
    train_df = load_data(train_file)
    val_df = load_data(val_file)
    test_df = load_data(test_file)
    train_en_x = train_df.copy()
    val_en_x = val_df.copy()
    test_en_x = test_df.copy()
    train_x_en = train_df.rename(columns={src_col: tgt_col, tgt_col: src_col})
    val_x_en = val_df.rename(columns={src_col: tgt_col, tgt_col: src_col})
    test_x_en = test_df.rename(columns={src_col: tgt_col, tgt_col: src_col})
    train_en_x = add_language_tags(train_en_x, lang_tag_en_to_x, src_col=src_col)
    train_x_en = add_language_tags(train_x_en, lang_tag_x_to_en, src_col=src_col)
    val_en_x = add_language_tags(val_en_x, lang_tag_en_to_x, src_col=src_col)
    val_x_en = add_language_tags(val_x_en, lang_tag_x_to_en, src_col=src_col)
    test_en_x = add_language_tags(test_en_x, lang_tag_en_to_x, src_col=src_col)
    test_x_en = add_language_tags(test_x_en, lang_tag_x_to_en, src_col=src_col)
    combined_train = (
        pd.concat([train_en_x, train_x_en])
        .sample(frac=1, random_state=seed)
        .reset_index(drop=True)
    )
    combined_val = (
        pd.concat([val_en_x, val_x_en])
        .sample(frac=1, random_state=seed)
        .reset_index(drop=True)
    )
    save_data(combined_train, multi_train_file, data_format)
    save_data(combined_val, multi_val_file, data_format)
    save_data(test_en_x, test_en_x_file, data_format)
    save_data(test_x_en, test_x_en_file, data_format)
    print("Multilingual preprocessing complete.")
