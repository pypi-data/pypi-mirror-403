"""Data loading and batching utilities for neural machine translation.

Provides tools for creating efficient data loaders with optional bucketing by
sequence length. Bucketing groups sequences of similar lengths together to
minimize padding overhead and improve training efficiency.

Key Components:

1. **collate_fn**: Pads sequences to the same length within a batch using
   the PAD token.

2. **BucketBatchSampler**: Groups sequences into length buckets and creates
   batches with similar-length sequences. Automatically computes bucket
   boundaries based on sequence length distribution percentiles.

3. **create_dataloaders**: Convenience function to build train/val DataLoaders
   with optional SentencePiece tokenization and bucketing.
"""

from functools import partial
from typing import List, Tuple, Optional, Iterator, Union
from pathlib import Path
import random
import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Sampler
from ..config import Config, get_default_config
from .dataset import NMTDataset
from .vocab import BaseVocab, SentencePieceVocab


def collate_fn(
    batch: List[Tuple[torch.Tensor, torch.Tensor]],
    pad_idx: Optional[int] = None,
    config: Optional[Config] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Collate a batch of (source, target) tensor pairs with padding.

    Pads all sequences in the batch to the same length (the length of the
    longest sequence) along the sequence dimension.

    Args:
        batch (list[tuple[torch.Tensor, torch.Tensor]]): List of (src, tgt)
            pairs where src and tgt are 1D long tensors of variable length.
        pad_idx (int, optional): Padding index value. Defaults to config.pad_idx.
        config (Config, optional): Configuration object. Defaults to
            get_default_config().

    Returns:
        tuple[torch.Tensor, torch.Tensor]: A tuple containing:
            - src_batch (torch.Tensor): Padded source batch with shape
              (batch_size, max_src_len).
            - tgt_batch (torch.Tensor): Padded target batch with shape
              (batch_size, max_tgt_len).

    Notes:
        Used as the collate_fn for PyTorch DataLoaders. Padding is applied
        with batch_first=True so sequences are in (batch, seq_len) order.
    """
    cfg = config if config is not None else get_default_config()
    pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx

    src_batch, tgt_batch = zip(*batch)
    src_batch_t = pad_sequence(list(src_batch), batch_first=True, padding_value=pad_idx)
    tgt_batch_t = pad_sequence(list(tgt_batch), batch_first=True, padding_value=pad_idx)
    return src_batch_t, tgt_batch_t


class BucketBatchSampler(Sampler):
    """Groups dataset samples into length buckets to minimize padding in batches.

    Assigns each sample to a bucket based on its source sequence length.
    When iterated, yields batches where all samples come from the same bucket,
    reducing padding waste. Bucket boundaries are automatically computed from
    the data distribution if not provided.

    Bucketing is particularly effective for datasets with large sequence length
    variance, e.g., 10-500 tokens. It reduces computational waste from padding
    longer samples with many pad tokens.

    Args:
        dataset (NMTDataset): The dataset to sample from.
        batch_size (int): Number of samples per batch.
        bucket_boundaries (list[int], optional): Bucket upper boundaries in
            ascending order. Defaults to None, in which case boundaries are
            computed automatically from sequence length percentiles.

    Attributes:
        buckets (list[list[int]]): Per-bucket list of sample indices.
        num_batches (int): Total number of batches that will be yielded.
        bucket_boundaries (list[int]): Upper length boundary for each bucket.
    """

    def __init__(
        self,
        dataset: NMTDataset,
        batch_size: int,
        bucket_boundaries: Optional[List[int]] = None,
    ) -> None:
        """Initialize the sampler and assign samples to buckets.

        Args:
            dataset (NMTDataset): The dataset to sample from.
            batch_size (int): Number of samples per batch.
            bucket_boundaries (list[int], optional): Pre-specified bucket
                boundaries. If None, computed automatically. Defaults to None.
        """
        self.dataset = dataset
        self.batch_size = batch_size
        if bucket_boundaries is None:
            bucket_boundaries = self._calculate_bucket_boundaries()
        self.bucket_boundaries = sorted(bucket_boundaries)
        self.buckets: List[List[int]] = [[] for _ in range(len(bucket_boundaries) + 1)]
        for idx in range(len(dataset)):
            src_tensor, _ = dataset[idx]
            src_len = len(src_tensor)
            b = self._get_bucket(src_len)
            self.buckets[b].append(idx)
        self._compute_num_batches()

    def _calculate_bucket_boundaries(self) -> List[int]:
        """Compute bucket boundaries automatically from sequence length distribution.

        Uses sequence length percentiles (20, 40, 60, 80, 95) to determine
        bucket boundaries. For very large datasets, samples a subset of indices
        to estimate the distribution instead of scanning the entire dataset.

        Returns:
            list[int]: Sorted list of bucket boundary lengths (exclusive upper bounds).

        Notes:
            - Time complexity is O(m log m) where m is the number of lengths
              actually inspected (either full dataset size or the sample size).
            - Sampling is used when the dataset is large to avoid expensive full scans.
        """
        total = len(self.dataset)
        if total == 0:
            return [10, 20, 40]

        # Thresholds for when to sample instead of scanning the whole dataset.
        MAX_FULL_SCAN = 50_000
        # When sampling, inspect at most SAMPLE_MAX items and at least SAMPLE_MIN items,
        # or ~SAMPLE_FRAC fraction of the dataset (whichever is between min/max).
        SAMPLE_MAX = 50_000
        SAMPLE_MIN = 1_000
        SAMPLE_FRAC = 0.05  # 5%

        if total > MAX_FULL_SCAN:
            sample_size = min(SAMPLE_MAX, max(SAMPLE_MIN, int(total * SAMPLE_FRAC)))
            # random.sample on a range is efficient and avoids constructing a large list.
            sample_indices = random.sample(range(total), sample_size)
            lengths: List[int] = [len(self.dataset[i][0]) for i in sample_indices]
        else:
            lengths = [len(self.dataset[i][0]) for i in range(total)]

        lengths.sort()
        percentiles = [20, 40, 60, 80, 95]
        boundaries: List[int] = []
        m = len(lengths)
        for p in percentiles:
            # use (m-1) to map percentiles into valid index range [0, m-1]
            idx = int((m - 1) * p / 100)
            boundary = lengths[min(max(idx, 0), m - 1)]
            boundaries.append(boundary)

        # remove duplicates and sort
        boundaries = sorted(list(set(boundaries)))

        # If there aren't enough distinct boundaries, fall back to reasonable defaults
        # based on the observed max length (from the inspected set).
        if len(boundaries) < 3:
            max_len = lengths[-1]
            if max_len <= 20:
                boundaries = [10, 15]
            elif max_len <= 50:
                boundaries = [10, 20, 30, 40]
            elif max_len <= 100:
                boundaries = [10, 20, 40, 60, 80]
            else:
                boundaries = [10, 20, 40, 80, 120, 200]
        return boundaries

    def _get_bucket(self, length: int) -> int:
        """Determine which bucket a sequence of given length belongs to.

        Finds the first bucket boundary that is >= length.

        Args:
            length (int): Sequence length in tokens.

        Returns:
            int: Bucket index. Always in range [0, num_buckets] where
                num_buckets = len(bucket_boundaries) + 1.
        """
        for i, boundary in enumerate(self.bucket_boundaries):
            if length <= boundary:
                return i
        return len(self.bucket_boundaries)

    def _compute_num_batches(self) -> None:
        """Compute and cache the total number of batches.

        Counts the number of complete batches from each bucket (discards
        incomplete final batches in each bucket).
        """
        self.num_batches = sum(
            len(bucket) // self.batch_size for bucket in self.buckets
        )

    def __iter__(self) -> Iterator[List[int]]:
        """Iterate over batches of sample indices.

        Yields batches by:
        1. Shuffling samples within each bucket independently.
        2. Creating batches from each bucket (discarding incomplete batches).
        3. Shuffling the list of batches.
        4. Yielding batches of sample indices.

        Yields:
            list[int]: Each batch is a list of sample indices, length = batch_size.

        Notes:
            - Incomplete batches (fewer than batch_size samples) are dropped.
            - Batch order is randomized for better training dynamics.
            - Within-bucket samples are shuffled for better gradient estimates.
        """
        for bucket in self.buckets:
            random.shuffle(bucket)
        all_batches: List[List[int]] = []
        for bucket in self.buckets:
            for i in range(
                0, len(bucket) - len(bucket) % self.batch_size, self.batch_size
            ):
                all_batches.append(bucket[i : i + self.batch_size])
        random.shuffle(all_batches)
        for batch in all_batches:
            yield batch

    def __len__(self) -> int:
        """Return the number of complete batches.

        Returns:
            int: Total number of batches that will be yielded. Incomplete
                batches (fewer than batch_size samples) are not counted.
        """
        return self.num_batches


def create_dataloaders(
    train_file: Union[Path, NMTDataset],
    val_file: Optional[Union[Path, NMTDataset]] = None,
    batch_size: Optional[int] = None,
    num_workers: Optional[int] = None,
    use_sentencepiece: bool = False,
    sp_model_path: Optional[str] = None,
    sp_tgt_model_path: Optional[str] = None,
    use_bucketing: bool = False,
    bucket_boundaries: Optional[List[int]] = None,
    device: Optional[str] = None,
    pad_idx: Optional[int] = None,
    config: Optional[Config] = None,
) -> Tuple[DataLoader, Optional[DataLoader], BaseVocab, BaseVocab]:
    """Create PyTorch DataLoaders for training and validation.

    Constructs train and optional validation DataLoaders from structured data
    files. Supports two tokenization modes: simple token-based (SimpleVocab) or
    SentencePiece subword. Optionally uses bucketing by sequence length to
    minimize padding overhead.

    Data must be in structured format (TSV/CSV/JSON/Parquet) with configurable
    source and target columns. Parallel .txt files should be merged into a
    single file first (see preprocessing.base.parallel_txt_to_dataframe).

    Args:
        train_file (Path | NMTDataset): Path to training data file or a prebuilt
            NMTDataset instance.
        val_file (Path | NMTDataset, optional): Path to validation data file or
            a prebuilt NMTDataset instance. If None, no validation loader is
            created. Defaults to None.
        batch_size (int, optional): Batch size for loaders. Defaults to
            config.batch_size.
        num_workers (int, optional): Number of worker processes for data loading.
            Defaults to config.num_workers.
        use_sentencepiece (bool, optional): If True, use SentencePiece models for
            tokenization. If False, use simple token-based vocabularies. Defaults
            to False.
        sp_model_path (str, optional): Path to SentencePiece source model file.
            Required if use_sentencepiece=True. Defaults to
            config.sentencepiece_src_model.
        sp_tgt_model_path (str, optional): Path to SentencePiece target model file.
            If None with use_sentencepiece=True, uses the configured target path
            or sp_model_path when identical. Defaults to None.
        use_bucketing (bool, optional): If True, use BucketBatchSampler to group
            sequences by length. Reduces padding overhead for datasets with
            variable sequence lengths. Defaults to False.
        bucket_boundaries (list[int], optional): Pre-specified bucket boundaries
            for BucketBatchSampler. If None with use_bucketing=True, boundaries
            are computed automatically from the training data. Defaults to None.
        device (str, optional): Device string (e.g., 'cuda', 'cpu'). Used for
            pin_memory optimization. Defaults to config.device.
        pad_idx (int, optional): Padding index value. Defaults to config.pad_idx.
        config (Config, optional): Configuration object. Defaults to
            get_default_config().

    Returns:
        tuple: A 4-tuple containing:
            - train_loader (DataLoader): Training data loader.
            - val_loader (DataLoader or None): Validation data loader, or None
              if val_file is not provided.
            - src_vocab (BaseVocab): Source vocabulary.
            - tgt_vocab (BaseVocab): Target vocabulary.

    Raises:
        AssertionError: If use_sentencepiece=True but sp_model_path is None.
        ValueError: If data files have incorrect format or missing columns.

    Examples:
        >>> train_loader, val_loader, src_vocab, tgt_vocab = create_dataloaders(
        ...     train_file="data/train.tsv",
        ...     val_file="data/val.tsv",
        ...     batch_size=32,
        ...     use_bucketing=True
        ... )
        >>> for src_batch, tgt_batch in train_loader:
        ...     print(src_batch.shape, tgt_batch.shape)
        ...     break
        torch.Size([32, 45]) torch.Size([32, 48])

        >>> train_ds = NMTDataset("data/train.tsv")
        >>> val_ds = NMTDataset("data/val.tsv", src_vocab=train_ds.src_vocab, tgt_vocab=train_ds.tgt_vocab)
        >>> train_loader, val_loader, src_vocab, tgt_vocab = create_dataloaders(
        ...     train_file=train_ds,
        ...     val_file=val_ds,
        ...     batch_size=32,
        ... )

    Notes:
        - DataLoader pin_memory is enabled for CUDA devices to speed up transfers.
        - Training loader always shuffles (or uses bucket-based shuffling).
        - Validation loader does not shuffle.
        - Incomplete batches are dropped.
    """
    cfg = config if config is not None else get_default_config()
    batch_size = batch_size if batch_size is not None else cfg.batch_size
    num_workers = num_workers if num_workers is not None else cfg.num_workers
    device = device if device is not None else cfg.device
    pad_idx = pad_idx if pad_idx is not None else cfg.pad_idx

    # Create collate function with resolved pad_idx
    collate = partial(collate_fn, pad_idx=pad_idx)

    if isinstance(train_file, NMTDataset):
        train_dataset = train_file
        src_vocab = train_dataset.src_vocab
        tgt_vocab = train_dataset.tgt_vocab
        assert src_vocab is not None and tgt_vocab is not None, (
            "Provided train_dataset must have src_vocab and tgt_vocab initialized"
        )
    else:
        train_data = train_file
        if use_sentencepiece:
            sp_model_path = (
                sp_model_path
                if sp_model_path is not None
                else cfg.sentencepiece_src_model
            )
            sp_tgt_model_path = (
                sp_tgt_model_path
                if sp_tgt_model_path is not None
                else cfg.sentencepiece_tgt_model
            )
            assert sp_model_path is not None, (
                "Must provide sp_model_path when using SentencePiece"
            )
            src_vocab = SentencePieceVocab(sp_model_path)
            if sp_tgt_model_path and sp_tgt_model_path != sp_model_path:
                tgt_vocab = SentencePieceVocab(sp_tgt_model_path)
            else:
                tgt_vocab = src_vocab
        else:
            tmp = NMTDataset(train_data)
            src_vocab = tmp.src_vocab
            tgt_vocab = tmp.tgt_vocab
            assert src_vocab is not None and tgt_vocab is not None
        train_dataset = NMTDataset(train_data, src_vocab=src_vocab, tgt_vocab=tgt_vocab)

    val_dataset: Optional[NMTDataset]
    if val_file is not None:
        if isinstance(val_file, NMTDataset):
            val_dataset = val_file
            # Ensure vocab objects are shared with the training dataset
            val_dataset.src_vocab = src_vocab
            val_dataset.tgt_vocab = tgt_vocab
        else:
            val_dataset = NMTDataset(val_file, src_vocab=src_vocab, tgt_vocab=tgt_vocab)
    else:
        val_dataset = None
    if use_bucketing:
        train_sampler = BucketBatchSampler(
            train_dataset, batch_size=batch_size, bucket_boundaries=bucket_boundaries
        )
        train_loader = DataLoader(
            train_dataset,
            batch_sampler=train_sampler,
            num_workers=num_workers,
            collate_fn=collate,
            pin_memory=True if device == "cuda" else False,
        )
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            collate_fn=collate,
            pin_memory=True if device == "cuda" else False,
        )
    if val_dataset is not None:
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            collate_fn=collate,
            pin_memory=True if device == "cuda" else False,
        )
    else:
        val_loader = None
    return train_loader, val_loader, src_vocab, tgt_vocab
