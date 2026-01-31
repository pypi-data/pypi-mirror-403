import unittest
import tempfile
import torch
import pandas as pd
from pathlib import Path
from torchlingo.data_processing.dataset import NMTDataset
from torchlingo.data_processing.vocab import SimpleVocab
from torchlingo import config
from torchlingo.config import Config


class TestNMTDatasetInitialization(unittest.TestCase):
    """Test NMTDataset initialization."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["hello world", "this is a test"],
            "tgt": ["hola mundo", "esto es una prueba"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dataset_init_creates_vocab(self):
        """Dataset should create vocabularies if not provided."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        self.assertIsNotNone(dataset.src_vocab)
        self.assertIsNotNone(dataset.tgt_vocab)
        self.assertIsInstance(dataset.src_vocab, SimpleVocab)
        self.assertIsInstance(dataset.tgt_vocab, SimpleVocab)

    def test_dataset_init_uses_provided_vocab(self):
        """Dataset should use provided vocabularies."""
        src_vocab = SimpleVocab(min_freq=1)
        tgt_vocab = SimpleVocab(min_freq=1)
        src_vocab.build_vocab(["hello world"])
        tgt_vocab.build_vocab(["hola mundo"])
        dataset = NMTDataset(
            self.data_file,
            src_col="src",
            tgt_col="tgt",
            src_vocab=src_vocab,
            tgt_vocab=tgt_vocab,
        )
        self.assertIs(dataset.src_vocab, src_vocab)
        self.assertIs(dataset.tgt_vocab, tgt_vocab)

    def test_dataset_init_default_column_names(self):
        """Dataset should use default column names from config."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.src_col, config.SRC_COL)
        self.assertEqual(dataset.tgt_col, config.TGT_COL)

    def test_dataset_init_custom_column_names(self):
        """Dataset should accept custom column names."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        self.assertEqual(dataset.src_col, "src")
        self.assertEqual(dataset.tgt_col, "tgt")

    def test_dataset_init_default_max_length(self):
        """Dataset should use default max_length from config."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.max_length, config.MAX_SEQ_LENGTH)

    def test_dataset_init_custom_max_length(self):
        """Dataset should accept custom max_length."""
        dataset = NMTDataset(self.data_file, max_length=50)
        self.assertEqual(dataset.max_length, 50)


class TestNMTDatasetLoading(unittest.TestCase):
    """Test NMTDataset data loading."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["hello world", "this is a test"],
            "tgt": ["hola mundo", "esto es una prueba"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dataset_length(self):
        """Dataset length should match number of examples."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        self.assertEqual(len(dataset), 2)

    def test_dataset_loads_sentences_correctly(self):
        """Dataset should load source and target sentences."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        self.assertEqual(dataset.src_sentences[0], "hello world")
        self.assertEqual(dataset.tgt_sentences[0], "hola mundo")

    def test_dataset_converts_to_string(self):
        """Dataset should convert non-string values to strings."""
        data_file = Path(self.temp_dir.name) / "numeric.tsv"
        data = {"src": [123, 456], "tgt": [789, 101]}
        pd.DataFrame(data).to_csv(data_file, sep="\t", index=False)
        dataset = NMTDataset(data_file, src_col="src", tgt_col="tgt")
        self.assertIsInstance(dataset.src_sentences[0], str)


class TestNMTDatasetGetItem(unittest.TestCase):
    """Test NMTDataset __getitem__ method."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["hello world", "this is a test"],
            "tgt": ["hola mundo", "esto es una prueba"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_getitem_returns_tensors(self):
        """__getitem__ should return torch tensors."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        src, tgt = dataset[0]
        self.assertIsInstance(src, torch.Tensor)
        self.assertIsInstance(tgt, torch.Tensor)

    def test_getitem_tensor_dtype(self):
        """Returned tensors should have dtype long."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        src, tgt = dataset[0]
        self.assertEqual(src.dtype, torch.long)
        self.assertEqual(tgt.dtype, torch.long)

    def test_getitem_includes_special_tokens(self):
        """__getitem__ should add SOS and EOS tokens."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        src, tgt = dataset[0]
        # "hello world" -> SOS + 2 tokens + EOS = 4
        self.assertEqual(len(src), 4)
        self.assertEqual(src[0].item(), config.SOS_IDX)
        self.assertEqual(src[-1].item(), config.EOS_IDX)

    def test_getitem_all_indices(self):
        """Should be able to access all dataset indices."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        for i in range(len(dataset)):
            src, tgt = dataset[i]
            self.assertIsInstance(src, torch.Tensor)
            self.assertIsInstance(tgt, torch.Tensor)


class TestNMTDatasetTruncation(unittest.TestCase):
    """Test NMTDataset sequence truncation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["hello world", "this is a test"],
            "tgt": ["hola mundo", "esto es una prueba"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_truncation_respects_max_length(self):
        """Sequences should be truncated to max_length."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt", max_length=3)
        src, tgt = dataset[0]
        self.assertLessEqual(len(src), 3)
        self.assertLessEqual(len(tgt), 3)

    def test_truncation_preserves_eos(self):
        """Truncated sequences should end with EOS token."""
        dataset = NMTDataset(self.data_file, src_col="src", tgt_col="tgt", max_length=3)
        src, tgt = dataset[0]
        self.assertEqual(src[-1].item(), config.EOS_IDX)
        self.assertEqual(tgt[-1].item(), config.EOS_IDX)

    def test_no_truncation_for_short_sequences(self):
        """Short sequences should not be affected by max_length."""
        dataset = NMTDataset(
            self.data_file, src_col="src", tgt_col="tgt", max_length=100
        )
        src, tgt = dataset[0]
        # "hello world" -> SOS + 2 + EOS = 4
        self.assertEqual(len(src), 4)


class TestNMTDatasetVocabSharing(unittest.TestCase):
    """Test vocabulary sharing between datasets."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["hello world", "this is a test"],
            "tgt": ["hola mundo", "esto es una prueba"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_shared_vocab_is_reused(self):
        """Provided vocabularies should be used by dataset."""
        dataset1 = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        shared_src = dataset1.src_vocab
        shared_tgt = dataset1.tgt_vocab
        dataset2 = NMTDataset(
            self.data_file,
            src_col="src",
            tgt_col="tgt",
            src_vocab=shared_src,
            tgt_vocab=shared_tgt,
        )
        self.assertIs(dataset2.src_vocab, shared_src)
        self.assertIs(dataset2.tgt_vocab, shared_tgt)

    def test_separate_datasets_have_separate_vocabs(self):
        """Datasets without shared vocab should have independent vocabs."""
        dataset1 = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        dataset2 = NMTDataset(self.data_file, src_col="src", tgt_col="tgt")
        self.assertIsNot(dataset1.src_vocab, dataset2.src_vocab)
        self.assertIsNot(dataset1.tgt_vocab, dataset2.tgt_vocab)


class TestNMTDatasetErrors(unittest.TestCase):
    """Test error handling in NMTDataset."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_columns_raises_error(self):
        """Missing required columns should raise ValueError."""
        bad_file = Path(self.temp_dir.name) / "bad.tsv"
        pd.DataFrame({"a": ["x"], "b": ["y"]}).to_csv(bad_file, sep="\t", index=False)
        with self.assertRaises(ValueError):
            NMTDataset(bad_file, src_col="src", tgt_col="tgt")

    def test_missing_src_column_raises_error(self):
        """Missing source column should raise ValueError."""
        bad_file = Path(self.temp_dir.name) / "bad.tsv"
        pd.DataFrame({"tgt": ["y"]}).to_csv(bad_file, sep="\t", index=False)
        with self.assertRaises(ValueError) as cm:
            NMTDataset(bad_file, src_col="src", tgt_col="tgt")
        self.assertIn("src", str(cm.exception))

    def test_missing_tgt_column_raises_error(self):
        """Missing target column should raise ValueError."""
        bad_file = Path(self.temp_dir.name) / "bad.tsv"
        pd.DataFrame({"src": ["x"]}).to_csv(bad_file, sep="\t", index=False)
        with self.assertRaises(ValueError) as cm:
            NMTDataset(bad_file, src_col="src", tgt_col="tgt")
        self.assertIn("tgt", str(cm.exception))


class TestNMTDatasetEdgeCases(unittest.TestCase):
    """Test edge cases in NMTDataset."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_empty_sentences(self):
        """Dataset should skip empty sentences."""
        data_file = Path(self.temp_dir.name) / "empty.tsv"
        data = {"src": ["hello", "", "world"], "tgt": ["hola", "", "mundo"]}
        pd.DataFrame(data).to_csv(data_file, sep="\t", index=False)
        dataset = NMTDataset(data_file, src_col="src", tgt_col="tgt")
        # Empty line should be removed, leaving only non-empty rows
        self.assertEqual(len(dataset), 2)

    def test_single_example_dataset(self):
        """Dataset should work with single example."""
        data_file = Path(self.temp_dir.name) / "single.tsv"
        data = {"src": ["hello"], "tgt": ["hola"]}
        pd.DataFrame(data).to_csv(data_file, sep="\t", index=False)
        dataset = NMTDataset(data_file, src_col="src", tgt_col="tgt")
        self.assertEqual(len(dataset), 1)
        src, tgt = dataset[0]
        self.assertIsInstance(src, torch.Tensor)

    def test_long_sentences(self):
        """Dataset should handle very long sentences."""
        data_file = Path(self.temp_dir.name) / "long.tsv"
        long_src = " ".join(["word"] * 100)
        long_tgt = " ".join(["palabra"] * 100)
        data = {"src": [long_src], "tgt": [long_tgt]}
        pd.DataFrame(data).to_csv(data_file, sep="\t", index=False)
        dataset = NMTDataset(data_file, src_col="src", tgt_col="tgt", max_length=50)
        src, tgt = dataset[0]
        self.assertLessEqual(len(src), 50)


class TestNMTDatasetConfigOverride(unittest.TestCase):
    """Test config override behavior for NMTDataset."""

    def setUp(self):
        """Create temp test data file."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "data.tsv"
        data = {
            "src": ["hello world", "this is a test"],
            "tgt": ["hola mundo", "esto es una prueba"],
            "source": ["hello world", "this is a test"],
            "target": ["hola mundo", "esto es una prueba"],
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_file, sep="\t", index=False)

    def tearDown(self):
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # Tests for src_col config override
    # -------------------------------------------------------------------------
    def test_dataset_uses_default_config_src_col(self):
        """NMTDataset should use default config src_col when not specified."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.src_col, config.SRC_COL)

    def test_dataset_explicit_src_col_overrides_default(self):
        """Explicit src_col should override default config."""
        dataset = NMTDataset(self.data_file, src_col="source", tgt_col="target")
        self.assertEqual(dataset.src_col, "source")

    def test_dataset_uses_passed_config_src_col(self):
        """NMTDataset should use passed config src_col."""
        custom_cfg = Config(src_col="source", tgt_col="target")
        dataset = NMTDataset(self.data_file, config=custom_cfg)
        self.assertEqual(dataset.src_col, "source")

    def test_dataset_explicit_overrides_passed_config_src_col(self):
        """Explicit src_col should override passed config."""
        custom_cfg = Config(src_col="source", tgt_col="target")
        dataset = NMTDataset(
            self.data_file, src_col="src", tgt_col="tgt", config=custom_cfg
        )
        self.assertEqual(dataset.src_col, "src")

    # -------------------------------------------------------------------------
    # Tests for tgt_col config override
    # -------------------------------------------------------------------------
    def test_dataset_uses_default_config_tgt_col(self):
        """NMTDataset should use default config tgt_col when not specified."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.tgt_col, config.TGT_COL)

    def test_dataset_explicit_tgt_col_overrides_default(self):
        """Explicit tgt_col should override default config."""
        dataset = NMTDataset(self.data_file, src_col="source", tgt_col="target")
        self.assertEqual(dataset.tgt_col, "target")

    def test_dataset_uses_passed_config_tgt_col(self):
        """NMTDataset should use passed config tgt_col."""
        custom_cfg = Config(src_col="source", tgt_col="target")
        dataset = NMTDataset(self.data_file, config=custom_cfg)
        self.assertEqual(dataset.tgt_col, "target")

    def test_dataset_explicit_overrides_passed_config_tgt_col(self):
        """Explicit tgt_col should override passed config."""
        custom_cfg = Config(src_col="source", tgt_col="target")
        dataset = NMTDataset(
            self.data_file, src_col="src", tgt_col="tgt", config=custom_cfg
        )
        self.assertEqual(dataset.tgt_col, "tgt")

    # -------------------------------------------------------------------------
    # Tests for max_length config override
    # -------------------------------------------------------------------------
    def test_dataset_uses_default_config_max_length(self):
        """NMTDataset should use default config max_seq_length when not specified."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.max_length, config.MAX_SEQ_LENGTH)

    def test_dataset_explicit_max_length_overrides_default(self):
        """Explicit max_length should override default config."""
        dataset = NMTDataset(self.data_file, max_length=100)
        self.assertEqual(dataset.max_length, 100)

    def test_dataset_uses_passed_config_max_length(self):
        """NMTDataset should use passed config max_seq_length."""
        custom_cfg = Config(max_seq_length=256)
        dataset = NMTDataset(self.data_file, config=custom_cfg)
        self.assertEqual(dataset.max_length, 256)

    def test_dataset_explicit_overrides_passed_config_max_length(self):
        """Explicit max_length should override passed config."""
        custom_cfg = Config(max_seq_length=256)
        dataset = NMTDataset(self.data_file, max_length=50, config=custom_cfg)
        self.assertEqual(dataset.max_length, 50)

    # -------------------------------------------------------------------------
    # Tests for eos_idx config override
    # -------------------------------------------------------------------------
    def test_dataset_uses_default_config_eos_idx(self):
        """NMTDataset should use default config eos_idx when not specified."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.eos_idx, config.EOS_IDX)

    def test_dataset_explicit_eos_idx_overrides_default(self):
        """Explicit eos_idx should override default config."""
        dataset = NMTDataset(self.data_file, eos_idx=5)
        self.assertEqual(dataset.eos_idx, 5)

    def test_dataset_uses_passed_config_eos_idx(self):
        """NMTDataset should use passed config eos_idx."""
        custom_cfg = Config(eos_idx=7)
        dataset = NMTDataset(self.data_file, config=custom_cfg)
        self.assertEqual(dataset.eos_idx, 7)

    def test_dataset_explicit_overrides_passed_config_eos_idx(self):
        """Explicit eos_idx should override passed config."""
        custom_cfg = Config(eos_idx=7)
        dataset = NMTDataset(self.data_file, eos_idx=9, config=custom_cfg)
        self.assertEqual(dataset.eos_idx, 9)

    # -------------------------------------------------------------------------
    # Tests for src_tok_col config override
    # -------------------------------------------------------------------------
    def test_dataset_uses_default_config_src_tok_col(self):
        """NMTDataset should use default config src_tok_col when not specified."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.src_tok_col, config.SRC_TOK_COL)

    def test_dataset_explicit_src_tok_col_overrides_default(self):
        """Explicit src_tok_col should override default config."""
        dataset = NMTDataset(self.data_file, src_tok_col="custom_src_tok")
        self.assertEqual(dataset.src_tok_col, "custom_src_tok")

    def test_dataset_uses_passed_config_src_tok_col(self):
        """NMTDataset should use passed config src_tok_col."""
        custom_cfg = Config(src_tok_col="my_src_tok")
        dataset = NMTDataset(self.data_file, config=custom_cfg)
        self.assertEqual(dataset.src_tok_col, "my_src_tok")

    def test_dataset_explicit_overrides_passed_config_src_tok_col(self):
        """Explicit src_tok_col should override passed config."""
        custom_cfg = Config(src_tok_col="my_src_tok")
        dataset = NMTDataset(self.data_file, src_tok_col="other_tok", config=custom_cfg)
        self.assertEqual(dataset.src_tok_col, "other_tok")

    # -------------------------------------------------------------------------
    # Tests for tgt_tok_col config override
    # -------------------------------------------------------------------------
    def test_dataset_uses_default_config_tgt_tok_col(self):
        """NMTDataset should use default config tgt_tok_col when not specified."""
        dataset = NMTDataset(self.data_file)
        self.assertEqual(dataset.tgt_tok_col, config.TGT_TOK_COL)

    def test_dataset_explicit_tgt_tok_col_overrides_default(self):
        """Explicit tgt_tok_col should override default config."""
        dataset = NMTDataset(self.data_file, tgt_tok_col="custom_tgt_tok")
        self.assertEqual(dataset.tgt_tok_col, "custom_tgt_tok")

    def test_dataset_uses_passed_config_tgt_tok_col(self):
        """NMTDataset should use passed config tgt_tok_col."""
        custom_cfg = Config(tgt_tok_col="my_tgt_tok")
        dataset = NMTDataset(self.data_file, config=custom_cfg)
        self.assertEqual(dataset.tgt_tok_col, "my_tgt_tok")

    def test_dataset_explicit_overrides_passed_config_tgt_tok_col(self):
        """Explicit tgt_tok_col should override passed config."""
        custom_cfg = Config(tgt_tok_col="my_tgt_tok")
        dataset = NMTDataset(self.data_file, tgt_tok_col="other_tok", config=custom_cfg)
        self.assertEqual(dataset.tgt_tok_col, "other_tok")


if __name__ == "__main__":
    unittest.main()
