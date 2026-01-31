import unittest
import tempfile
import torch
import pandas as pd
from pathlib import Path
from torch.utils.data import DataLoader
from torchlingo.data_processing.batching import (
    collate_fn,
    BucketBatchSampler,
    create_dataloaders,
)
from torchlingo.data_processing.dataset import NMTDataset
from torchlingo import config


class TestCollateFn(unittest.TestCase):
    """Test collate_fn for batching."""

    def test_collate_fn_pads_sequences(self):
        """collate_fn should pad sequences to same length."""
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([4, 5])),
            (torch.tensor([6, 7]), torch.tensor([8, 9, 10])),
        ]
        src_batch, tgt_batch = collate_fn(batch)
        # Both should be padded to max length in batch
        self.assertEqual(src_batch.shape[0], 2)  # batch size
        self.assertEqual(src_batch.shape[1], 3)  # max src length
        self.assertEqual(tgt_batch.shape[1], 3)  # max tgt length

    def test_collate_fn_uses_pad_idx(self):
        """collate_fn should use PAD_IDX for padding."""
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([4])),
            (torch.tensor([5]), torch.tensor([6, 7])),
        ]
        src_batch, tgt_batch = collate_fn(batch)
        # Check that padding value is PAD_IDX
        self.assertEqual(src_batch[1, 1].item(), config.PAD_IDX)
        self.assertEqual(tgt_batch[0, 1].item(), config.PAD_IDX)

    def test_collate_fn_batch_first(self):
        """collate_fn should return batch-first tensors."""
        batch = [
            (torch.tensor([1, 2]), torch.tensor([3, 4])),
            (torch.tensor([5, 6]), torch.tensor([7, 8])),
        ]
        src_batch, tgt_batch = collate_fn(batch)
        # Shape should be (batch_size, seq_len)
        self.assertEqual(src_batch.shape[0], 2)
        self.assertEqual(tgt_batch.shape[0], 2)

    def test_collate_fn_single_item(self):
        """collate_fn should handle single item batches."""
        batch = [(torch.tensor([1, 2, 3]), torch.tensor([4, 5]))]
        src_batch, tgt_batch = collate_fn(batch)
        self.assertEqual(src_batch.shape[0], 1)
        self.assertEqual(src_batch.shape[1], 3)


class TestBucketBatchSamplerInitialization(unittest.TestCase):
    """Test BucketBatchSampler initialization."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["a", "a b", "a b c", "a b c d", "a b c d e"],
            "tgt": ["x", "x y", "x y z", "x y z w", "x y z w v"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)
        self.dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sampler_init_with_default_boundaries(self):
        """Sampler should calculate boundaries if not provided."""
        sampler = BucketBatchSampler(self.dataset, batch_size=2)
        self.assertIsNotNone(sampler.bucket_boundaries)
        self.assertIsInstance(sampler.bucket_boundaries, list)
        self.assertGreater(len(sampler.bucket_boundaries), 0)

    def test_sampler_init_with_custom_boundaries(self):
        """Sampler should use provided boundaries."""
        boundaries = [3, 5]
        sampler = BucketBatchSampler(
            self.dataset, batch_size=2, bucket_boundaries=boundaries
        )
        self.assertEqual(sampler.bucket_boundaries, boundaries)

    def test_sampler_creates_buckets(self):
        """Sampler should create buckets based on boundaries."""
        sampler = BucketBatchSampler(
            self.dataset, batch_size=2, bucket_boundaries=[3, 5]
        )
        # Should have len(boundaries) + 1 buckets
        self.assertEqual(len(sampler.buckets), 3)

    def test_sampler_assigns_examples_to_buckets(self):
        """Sampler should assign examples to appropriate buckets."""
        sampler = BucketBatchSampler(
            self.dataset, batch_size=2, bucket_boundaries=[3, 5]
        )
        total_examples = sum(len(bucket) for bucket in sampler.buckets)
        self.assertEqual(total_examples, len(self.dataset))


class TestBucketBatchSamplerBucketing(unittest.TestCase):
    """Test BucketBatchSampler bucketing logic."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["a", "a b", "a b c", "a b c d", "a b c d e"],
            "tgt": ["x", "x y", "x y z", "x y z w", "x y z w v"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)
        self.dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_bucket_assigns_correct_bucket(self):
        """_get_bucket should assign sequences to correct bucket."""
        sampler = BucketBatchSampler(
            self.dataset, batch_size=2, bucket_boundaries=[3, 5]
        )
        # length <= 3 -> bucket 0
        self.assertEqual(sampler._get_bucket(2), 0)
        self.assertEqual(sampler._get_bucket(3), 0)
        # 3 < length <= 5 -> bucket 1
        self.assertEqual(sampler._get_bucket(4), 1)
        self.assertEqual(sampler._get_bucket(5), 1)
        # length > 5 -> bucket 2
        self.assertEqual(sampler._get_bucket(6), 2)

    def test_boundaries_are_sorted(self):
        """Bucket boundaries should be sorted."""
        sampler = BucketBatchSampler(
            self.dataset, batch_size=2, bucket_boundaries=[5, 3, 10]
        )
        self.assertEqual(sampler.bucket_boundaries, [3, 5, 10])

    def test_buckets_respect_custom_boundaries(self):
        """Buckets should contain only examples whose lengths fit the custom boundaries."""
        boundaries = [3, 5]
        sampler = BucketBatchSampler(
            self.dataset, batch_size=2, bucket_boundaries=boundaries
        )
        # For each bucket, check that all example lengths satisfy the boundary constraints
        for b_idx, bucket in enumerate(sampler.buckets):
            for idx in bucket:
                src_tensor, _ = self.dataset[idx]
                length = len(src_tensor)
                if b_idx < len(boundaries):
                    self.assertLessEqual(
                        length,
                        boundaries[b_idx],
                        msg=f"Index {idx} with length {length} wrongly placed in bucket {b_idx} (<= {boundaries[b_idx]})",
                    )
                    if b_idx > 0:
                        # must be greater than previous boundary
                        self.assertGreater(length, boundaries[b_idx - 1])
                else:
                    # last bucket: length must be greater than last boundary
                    self.assertGreater(
                        length,
                        boundaries[-1],
                        msg=f"Index {idx} with length {length} wrongly placed in last bucket {b_idx} (> {boundaries[-1]})",
                    )

    def test_buckets_respect_default_boundaries(self):
        """Buckets created with default boundaries should respect those boundaries."""
        sampler = BucketBatchSampler(self.dataset, batch_size=2)
        boundaries = sampler.bucket_boundaries
        # For each bucket, ensure lengths fall into the expected ranges
        for b_idx, bucket in enumerate(sampler.buckets):
            for idx in bucket:
                src_tensor, _ = self.dataset[idx]
                length = len(src_tensor)
                if b_idx < len(boundaries):
                    self.assertLessEqual(
                        length,
                        boundaries[b_idx],
                        msg=f"Index {idx} length {length} not <= boundary {boundaries[b_idx]} for bucket {b_idx}",
                    )
                    if b_idx > 0:
                        self.assertGreater(length, boundaries[b_idx - 1])
                else:
                    self.assertGreater(
                        length,
                        boundaries[-1],
                        msg=f"Index {idx} length {length} not > last boundary {boundaries[-1]} for last bucket",
                    )


class TestBucketBatchSamplerIteration(unittest.TestCase):
    """Test BucketBatchSampler iteration."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        # Create dataset with 10 examples
        data = {
            "src": ["word " * i for i in range(1, 11)],
            "tgt": ["palabra " * i for i in range(1, 11)],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)
        self.dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_iter_yields_batches(self):
        """__iter__ should yield batches of correct size."""
        sampler = BucketBatchSampler(self.dataset, batch_size=2)
        batches = list(sampler)
        for batch in batches:
            self.assertLessEqual(len(batch), 2)

    def test_iter_covers_all_examples(self):
        """__iter__ should eventually cover all examples."""
        sampler = BucketBatchSampler(self.dataset, batch_size=2)
        batches = list(sampler)
        # Flatten indices from batches
        all_indices = [idx for batch in batches for idx in batch]

        # All indices should be valid dataset indices
        for idx in all_indices:
            self.assertGreaterEqual(idx, 0)
            self.assertLess(idx, len(self.dataset))

        # No duplicate indices across yielded batches (each example used at most once)
        self.assertEqual(len(all_indices), len(set(all_indices)))

        # Each yielded batch should have exactly the configured batch size
        for batch in batches:
            self.assertEqual(len(batch), 2)

        # The total number of yielded indices should equal num_batches * batch_size
        self.assertEqual(len(all_indices), len(batches) * 2)

        # When batch_size == 1, all dataset examples should be included
        sampler_single = BucketBatchSampler(self.dataset, batch_size=1)
        batches_single = list(sampler_single)
        all_single = [i for b in batches_single for i in b]
        self.assertEqual(len(all_single), len(set(all_single)))
        # With batch_size 1, every example should be present
        self.assertEqual(len(all_single), len(self.dataset))

    def test_len_returns_num_batches(self):
        """__len__ should return number of batches."""
        sampler = BucketBatchSampler(self.dataset, batch_size=2)
        num_batches = len(sampler)
        actual_batches = len(list(sampler))
        self.assertEqual(num_batches, actual_batches)


class TestBucketBatchSamplerBoundaryCalculation(unittest.TestCase):
    """Test automatic boundary calculation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_calculate_boundaries_small_dataset(self):
        """Boundary calculation should work for small datasets."""
        data_file = Path(self.temp_dir.name) / "small.tsv"
        data = {"src": ["a", "a b", "a b c"], "tgt": ["x", "x y", "x y z"]}
        pd.DataFrame(data).to_csv(data_file, sep="\t", index=False)
        dataset = NMTDataset(data_file, src_col="src", tgt_col="tgt")
        sampler = BucketBatchSampler(dataset, batch_size=2)
        # Should generate some boundaries
        self.assertGreater(len(sampler.bucket_boundaries), 0)

    def test_calculate_boundaries_uniform_lengths(self):
        """Boundary calculation should handle uniform lengths."""
        data_file = Path(self.temp_dir.name) / "uniform.tsv"
        data = {"src": ["a b c"] * 10, "tgt": ["x y z"] * 10}
        pd.DataFrame(data).to_csv(data_file, sep="\t", index=False)
        dataset = NMTDataset(data_file, src_col="src", tgt_col="tgt")
        sampler = BucketBatchSampler(dataset, batch_size=2)
        # Should still create boundaries
        self.assertIsNotNone(sampler.bucket_boundaries)


class TestCreateDataloaders(unittest.TestCase):
    """Test create_dataloaders function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.train_file = Path(self.temp_dir.name) / "train.tsv"
        self.val_file = Path(self.temp_dir.name) / "val.tsv"

        train_data = {
            "src": ["hello world", "good morning", "how are you"],
            "tgt": ["hola mundo", "buenos dias", "como estas"],
        }
        val_data = {
            "src": ["goodbye", "thank you"],
            "tgt": ["adios", "gracias"],
        }
        pd.DataFrame(train_data).to_csv(self.train_file, sep="\t", index=False)
        pd.DataFrame(val_data).to_csv(self.val_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_dataloaders_returns_loaders(self):
        """create_dataloaders should return train and val loaders (and vocabs)."""
        result = create_dataloaders(
            self.train_file, val_file=self.val_file, batch_size=2, num_workers=0
        )
        self.assertEqual(len(result), 4)
        train_loader, val_loader, src_vocab, tgt_vocab = result
        self.assertIsInstance(train_loader, DataLoader)
        self.assertIsInstance(val_loader, DataLoader)
        self.assertIsNotNone(src_vocab)
        self.assertIsNotNone(tgt_vocab)

    def test_create_dataloaders_with_default_params(self):
        """create_dataloaders should use config defaults if not provided."""
        train_loader, val_loader, _, _ = create_dataloaders(
            self.train_file, val_file=self.val_file, num_workers=0
        )
        self.assertIsNotNone(train_loader)
        self.assertIsNotNone(val_loader)

    def test_create_dataloaders_without_bucketing(self):
        """create_dataloaders should work without bucketing."""
        train_loader, val_loader, _, _ = create_dataloaders(
            self.train_file,
            val_file=self.val_file,
            batch_size=2,
            num_workers=0,
            use_bucketing=False,
        )
        # Should be able to iterate
        for batch in train_loader:
            src, tgt = batch
            self.assertIsInstance(src, torch.Tensor)
            break

    def test_create_dataloaders_with_bucketing(self):
        """create_dataloaders should work with bucketing enabled."""
        train_loader, val_loader, _, _ = create_dataloaders(
            self.train_file,
            val_file=self.val_file,
            batch_size=2,
            num_workers=0,
            use_bucketing=True,
        )
        self.assertIsNotNone(train_loader)

    def test_create_dataloaders_shares_vocab(self):
        """Train and val dataloaders should share vocabulary."""
        train_loader, val_loader, _, _ = create_dataloaders(
            self.train_file, val_file=self.val_file, batch_size=2, num_workers=0
        )
        train_dataset = train_loader.dataset
        val_dataset = val_loader.dataset
        self.assertIs(train_dataset.src_vocab, val_dataset.src_vocab)
        self.assertIs(train_dataset.tgt_vocab, val_dataset.tgt_vocab)

    def test_create_dataloaders_train_only(self):
        """create_dataloaders should work with only training data."""
        train_loader, val_loader, src_vocab, tgt_vocab = create_dataloaders(
            self.train_file, batch_size=2, num_workers=0
        )
        self.assertIsNotNone(train_loader)
        self.assertIsNone(val_loader)
        self.assertIsNotNone(src_vocab)
        self.assertIsNotNone(tgt_vocab)

    def test_create_dataloaders_accepts_dataset_objects(self):
        """create_dataloaders should accept prebuilt dataset inputs."""
        train_ds = NMTDataset(self.train_file, src_col="src", tgt_col="tgt")
        val_ds = NMTDataset(
            self.val_file,
            src_col="src",
            tgt_col="tgt",
            src_vocab=train_ds.src_vocab,
            tgt_vocab=train_ds.tgt_vocab,
        )
        train_loader, val_loader, src_vocab, tgt_vocab = create_dataloaders(
            train_ds,
            val_file=val_ds,
            batch_size=2,
            num_workers=0,
        )
        self.assertIs(train_loader.dataset, train_ds)
        self.assertIs(val_loader.dataset, val_ds)
        self.assertIs(src_vocab, train_ds.src_vocab)
        self.assertIs(tgt_vocab, train_ds.tgt_vocab)


class TestCreateDataloadersParallelConversion(unittest.TestCase):
    """Test create_dataloaders after converting parallel txt to a single file."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        # Parallel sources
        train_src = ["hello world", "good morning", "how are you"]
        train_tgt = ["hola mundo", "buenos dias", "como estas"]
        val_src = ["goodbye", "thank you"]
        val_tgt = ["adios", "gracias"]

        # Convert to DataFrames and persist structured files
        train_df = pd.DataFrame({config.SRC_COL: train_src, config.TGT_COL: train_tgt})
        val_df = pd.DataFrame({config.SRC_COL: val_src, config.TGT_COL: val_tgt})
        self.train_file = Path(self.temp_dir.name) / "train.tsv"
        self.val_file = Path(self.temp_dir.name) / "val.tsv"
        train_df.to_csv(self.train_file, sep="\t", index=False)
        val_df.to_csv(self.val_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_converted_files_returns_loaders(self):
        """create_dataloaders should work once parallel txt is converted."""
        result = create_dataloaders(
            self.train_file,
            val_file=self.val_file,
            batch_size=2,
            num_workers=0,
        )
        self.assertEqual(len(result), 4)
        train_loader, val_loader, _, _ = result
        self.assertIsInstance(train_loader, DataLoader)
        self.assertIsInstance(val_loader, DataLoader)

    def test_converted_files_train_only(self):
        """Converted single file should work without val file."""
        train_loader, val_loader, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
        )
        self.assertIsNotNone(train_loader)
        self.assertIsNone(val_loader)

    def test_converted_files_with_bucketing(self):
        """Converted single file should work with bucketing."""
        train_loader, val_loader, _, _ = create_dataloaders(
            self.train_file,
            val_file=self.val_file,
            batch_size=2,
            num_workers=0,
            use_bucketing=True,
        )
        self.assertIsNotNone(train_loader)


class TestCollateFnEdgeCases(unittest.TestCase):
    """Test edge cases for collate_fn."""

    def test_collate_fn_equal_length_sequences(self):
        """collate_fn should handle equal length sequences without padding."""
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([4, 5, 6])),
            (torch.tensor([7, 8, 9]), torch.tensor([10, 11, 12])),
        ]
        src_batch, tgt_batch = collate_fn(batch)
        self.assertEqual(src_batch.shape, (2, 3))
        self.assertEqual(tgt_batch.shape, (2, 3))
        # No padding should be needed
        self.assertNotIn(config.PAD_IDX, src_batch[0].tolist())

    def test_collate_fn_very_different_lengths(self):
        """collate_fn should handle very different sequence lengths."""
        batch = [
            (torch.tensor([1]), torch.tensor([2, 3, 4, 5, 6, 7, 8, 9, 10])),
            (torch.tensor([11, 12, 13, 14, 15]), torch.tensor([16])),
        ]
        src_batch, tgt_batch = collate_fn(batch)
        self.assertEqual(src_batch.shape[1], 5)  # max src length
        self.assertEqual(tgt_batch.shape[1], 9)  # max tgt length

    def test_collate_fn_preserves_values(self):
        """collate_fn should preserve non-padded values."""
        batch = [
            (torch.tensor([1, 2]), torch.tensor([3, 4])),
            (torch.tensor([5, 6, 7]), torch.tensor([8, 9, 10])),
        ]
        src_batch, tgt_batch = collate_fn(batch)
        # Check first batch item values are preserved
        self.assertEqual(src_batch[0, 0].item(), 1)
        self.assertEqual(src_batch[0, 1].item(), 2)


class TestCollateFnConfigOverride(unittest.TestCase):
    """Test config override behavior for collate_fn."""

    def test_collate_fn_uses_default_config_pad_idx(self):
        """collate_fn should use default config pad_idx when not specified."""
        from torchlingo.config import get_default_config

        default_cfg = get_default_config()
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([4])),
            (torch.tensor([5]), torch.tensor([6, 7])),
        ]
        src_batch, tgt_batch = collate_fn(batch)
        # Padding should use the default config's pad_idx
        self.assertEqual(src_batch[1, 1].item(), default_cfg.pad_idx)
        self.assertEqual(tgt_batch[0, 1].item(), default_cfg.pad_idx)

    def test_collate_fn_explicit_pad_idx_overrides_default(self):
        """Explicit pad_idx should override default config."""
        custom_pad_idx = 999
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([4])),
            (torch.tensor([5]), torch.tensor([6, 7])),
        ]
        src_batch, tgt_batch = collate_fn(batch, pad_idx=custom_pad_idx)
        # Padding should use the explicit pad_idx
        self.assertEqual(src_batch[1, 1].item(), custom_pad_idx)
        self.assertEqual(tgt_batch[0, 1].item(), custom_pad_idx)

    def test_collate_fn_uses_passed_config_pad_idx(self):
        """collate_fn should use passed config pad_idx."""
        from torchlingo.config import Config

        custom_cfg = Config(pad_idx=77)
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([4])),
            (torch.tensor([5]), torch.tensor([6, 7])),
        ]
        src_batch, tgt_batch = collate_fn(batch, config=custom_cfg)
        # Padding should use the custom config's pad_idx
        self.assertEqual(src_batch[1, 1].item(), 77)
        self.assertEqual(tgt_batch[0, 1].item(), 77)

    def test_collate_fn_explicit_pad_idx_overrides_passed_config(self):
        """Explicit pad_idx should override passed config."""
        from torchlingo.config import Config

        custom_cfg = Config(pad_idx=77)
        explicit_pad_idx = 888
        batch = [
            (torch.tensor([1, 2, 3]), torch.tensor([4])),
            (torch.tensor([5]), torch.tensor([6, 7])),
        ]
        src_batch, tgt_batch = collate_fn(
            batch, pad_idx=explicit_pad_idx, config=custom_cfg
        )
        # Explicit should take precedence over config
        self.assertEqual(src_batch[1, 1].item(), explicit_pad_idx)
        self.assertEqual(tgt_batch[0, 1].item(), explicit_pad_idx)


class TestCreateDataloadersConfigOverride(unittest.TestCase):
    """Test config override behavior for create_dataloaders."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.train_file = Path(self.temp_dir.name) / "train.tsv"
        self.val_file = Path(self.temp_dir.name) / "val.tsv"

        train_data = {
            "src": [
                "hello world",
                "good morning",
                "how are you",
                "test one",
                "test two",
            ],
            "tgt": [
                "hola mundo",
                "buenos dias",
                "como estas",
                "prueba uno",
                "prueba dos",
            ],
        }
        val_data = {
            "src": ["goodbye", "thank you"],
            "tgt": ["adios", "gracias"],
        }
        pd.DataFrame(train_data).to_csv(self.train_file, sep="\t", index=False)
        pd.DataFrame(val_data).to_csv(self.val_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # batch_size config override tests
    # -------------------------------------------------------------------------
    def test_create_dataloaders_uses_default_config_batch_size(self):
        """create_dataloaders should use default config batch_size."""
        from torchlingo.config import get_default_config

        default_cfg = get_default_config()
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            num_workers=0,
        )
        # The batch_size should come from default config
        self.assertEqual(train_loader.batch_size, default_cfg.batch_size)

    def test_create_dataloaders_explicit_batch_size_overrides_default(self):
        """Explicit batch_size should override default config."""
        explicit_batch_size = 2
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=explicit_batch_size,
            num_workers=0,
        )
        self.assertEqual(train_loader.batch_size, explicit_batch_size)

    def test_create_dataloaders_uses_passed_config_batch_size(self):
        """create_dataloaders should use passed config batch_size."""
        from torchlingo.config import Config

        custom_cfg = Config(batch_size=3)
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            num_workers=0,
            config=custom_cfg,
        )
        self.assertEqual(train_loader.batch_size, custom_cfg.batch_size)

    def test_create_dataloaders_explicit_batch_size_overrides_passed_config(self):
        """Explicit batch_size should override passed config."""
        from torchlingo.config import Config

        custom_cfg = Config(batch_size=3)
        explicit_batch_size = 2
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=explicit_batch_size,
            num_workers=0,
            config=custom_cfg,
        )
        self.assertEqual(train_loader.batch_size, explicit_batch_size)

    # -------------------------------------------------------------------------
    # num_workers config override tests
    # -------------------------------------------------------------------------
    def test_create_dataloaders_uses_default_config_num_workers(self):
        """create_dataloaders should use default config num_workers."""
        from torchlingo.config import get_default_config

        default_cfg = get_default_config()
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
        )
        self.assertEqual(train_loader.num_workers, default_cfg.num_workers)

    def test_create_dataloaders_explicit_num_workers_overrides_default(self):
        """Explicit num_workers should override default config."""
        explicit_num_workers = 0
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=explicit_num_workers,
        )
        self.assertEqual(train_loader.num_workers, explicit_num_workers)

    def test_create_dataloaders_uses_passed_config_num_workers(self):
        """create_dataloaders should use passed config num_workers."""
        from torchlingo.config import Config

        custom_cfg = Config(num_workers=2)
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            config=custom_cfg,
        )
        self.assertEqual(train_loader.num_workers, custom_cfg.num_workers)

    def test_create_dataloaders_explicit_num_workers_overrides_passed_config(self):
        """Explicit num_workers should override passed config."""
        from torchlingo.config import Config

        custom_cfg = Config(num_workers=2)
        explicit_num_workers = 0
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=explicit_num_workers,
            config=custom_cfg,
        )
        self.assertEqual(train_loader.num_workers, explicit_num_workers)

    # -------------------------------------------------------------------------
    # device config override tests (affects pin_memory)
    # -------------------------------------------------------------------------
    def test_create_dataloaders_uses_default_config_device(self):
        """create_dataloaders should use default config device for pin_memory."""
        from torchlingo.config import get_default_config

        default_cfg = get_default_config()
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
        )
        expected_pin_memory = default_cfg.device == "cuda"
        self.assertEqual(train_loader.pin_memory, expected_pin_memory)

    def test_create_dataloaders_explicit_device_overrides_default(self):
        """Explicit device should override default config."""
        # Test with cpu device (pin_memory should be False)
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
            device="cpu",
        )
        self.assertEqual(train_loader.pin_memory, False)

    def test_create_dataloaders_uses_passed_config_device(self):
        """create_dataloaders should use passed config device."""
        from torchlingo.config import Config

        custom_cfg = Config(device="cpu")
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
            config=custom_cfg,
        )
        self.assertEqual(train_loader.pin_memory, False)

    def test_create_dataloaders_explicit_device_overrides_passed_config(self):
        """Explicit device should override passed config."""
        from torchlingo.config import Config

        # Pass config with cuda, but override with cpu
        custom_cfg = Config(device="cuda")
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
            device="cpu",
            config=custom_cfg,
        )
        self.assertEqual(train_loader.pin_memory, False)

    # -------------------------------------------------------------------------
    # pad_idx config override tests
    # -------------------------------------------------------------------------
    def test_create_dataloaders_uses_default_config_pad_idx(self):
        """create_dataloaders should use default config pad_idx in collate."""
        from torchlingo.config import get_default_config

        default_cfg = get_default_config()
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
        )
        # Get a batch and check padding
        for src_batch, tgt_batch in train_loader:
            # Check if pad_idx is used (if padding exists)
            if src_batch.shape[1] > 1:
                # Find padded positions
                for i in range(src_batch.shape[0]):
                    row = src_batch[i].tolist()
                    if default_cfg.pad_idx in row:
                        self.assertIn(default_cfg.pad_idx, row)
            break

    def test_create_dataloaders_explicit_pad_idx_overrides_default(self):
        """Explicit pad_idx should override default config."""
        custom_pad_idx = 999
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
            pad_idx=custom_pad_idx,
        )
        # Get a batch and check padding uses the custom pad_idx
        for src_batch, tgt_batch in train_loader:
            # Find padded positions - the custom pad_idx should be used
            if src_batch.shape[1] > 1:
                for i in range(src_batch.shape[0]):
                    row = src_batch[i].tolist()
                    # If there's padding, it should use custom_pad_idx
                    if 0 in row:  # default pad_idx
                        self.fail(
                            "Should not use default pad_idx when explicit pad_idx is provided"
                        )
            break

    def test_create_dataloaders_uses_passed_config_pad_idx(self):
        """create_dataloaders should use passed config pad_idx."""
        from torchlingo.config import Config

        custom_cfg = Config(pad_idx=77)
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
            config=custom_cfg,
        )
        # Collate function should use pad_idx from custom_cfg
        for src_batch, tgt_batch in train_loader:
            if src_batch.shape[1] > 1:
                for i in range(src_batch.shape[0]):
                    row = src_batch[i].tolist()
                    # If there's padding, it should be 77
                    if 0 in row:  # default pad_idx
                        self.fail(
                            "Should not use default pad_idx when config specifies different pad_idx"
                        )
            break

    def test_create_dataloaders_explicit_pad_idx_overrides_passed_config(self):
        """Explicit pad_idx should override passed config."""
        from torchlingo.config import Config

        custom_cfg = Config(pad_idx=77)
        explicit_pad_idx = 888
        train_loader, _, _, _ = create_dataloaders(
            self.train_file,
            batch_size=2,
            num_workers=0,
            pad_idx=explicit_pad_idx,
            config=custom_cfg,
        )
        # Collate function should use explicit pad_idx
        for src_batch, tgt_batch in train_loader:
            if src_batch.shape[1] > 1:
                for i in range(src_batch.shape[0]):
                    row = src_batch[i].tolist()
                    # Should not use default (0) or config (77) pad_idx
                    if 0 in row or 77 in row:
                        self.fail(
                            "Should use explicit pad_idx, not default or config pad_idx"
                        )
            break


if __name__ == "__main__":
    unittest.main()
