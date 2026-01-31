import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from torchlingo.preprocessing.base import (
    load_data,
    save_data,
    split_data,
    parallel_txt_to_dataframe,
)
from torchlingo.preprocessing.multilingual import add_language_tags
from torchlingo import config
from torchlingo.config import Config


class TestLoadDataParallelFiles(unittest.TestCase):
    """Test load_data with parallel text files."""

    def test_load_parallel_txt_files(self):
        """load_data should load parallel .txt files."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.txt"
            tgt = Path(tmp) / "tgt.txt"
            src.write_text("hello\nworld\n", encoding="utf-8")
            tgt.write_text("hola\nmundo\n", encoding="utf-8")
            df = parallel_txt_to_dataframe(src, tgt)
            self.assertEqual(len(df), 2)
            self.assertIn(config.SRC_COL, df.columns)
            self.assertIn(config.TGT_COL, df.columns)
            self.assertEqual(df.iloc[0][config.SRC_COL], "hello")
            self.assertEqual(df.iloc[0][config.TGT_COL], "hola")

    def test_load_parallel_txt_mismatched_lines_raises(self):
        """load_data should raise error when parallel files have different lengths."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.txt"
            tgt = Path(tmp) / "tgt.txt"
            src.write_text("a\nb\n", encoding="utf-8")
            tgt.write_text("a\n", encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                parallel_txt_to_dataframe(src, tgt)
            self.assertIn("different number of lines", str(cm.exception))

    def test_load_parallel_txt_preserves_empty_lines(self):
        """load_data should preserve empty lines in parallel files."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.txt"
            tgt = Path(tmp) / "tgt.txt"
            src.write_text("hello\n \nworld\n", encoding="utf-8")
            tgt.write_text("hola\n\n mundo\n", encoding="utf-8")
            df = parallel_txt_to_dataframe(src, tgt)
            self.assertEqual(len(df), 3)
            self.assertEqual(df.iloc[1][config.SRC_COL], "")
            self.assertEqual(df.iloc[1][config.TGT_COL], "")

    def test_load_parallel_txt_strips_newlines(self):
        """load_data should strip trailing newlines."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.txt"
            tgt = Path(tmp) / "tgt.txt"
            src.write_text("hello\n", encoding="utf-8")
            tgt.write_text("hola\n", encoding="utf-8")
            df = parallel_txt_to_dataframe(src, tgt)
            self.assertEqual(df.iloc[0][config.SRC_COL], "hello")
            self.assertNotIn("\n", df.iloc[0][config.SRC_COL])


class TestLoadDataStructuredFormats(unittest.TestCase):
    """Test load_data with structured formats (TSV, CSV, etc.)."""

    def test_load_tsv_file(self):
        """load_data should load TSV files."""
        with tempfile.TemporaryDirectory() as tmp:
            tsv_file = Path(tmp) / "data.tsv"
            data = {
                config.SRC_COL: ["hello", "world"],
                config.TGT_COL: ["hola", "mundo"],
            }
            pd.DataFrame(data).to_csv(tsv_file, sep="\t", index=False)
            df = load_data(tsv_file, format="tsv")
            self.assertEqual(len(df), 2)
            self.assertEqual(df.iloc[0][config.SRC_COL], "hello")

    def test_load_csv_file(self):
        """load_data should load CSV files."""
        with tempfile.TemporaryDirectory() as tmp:
            csv_file = Path(tmp) / "data.csv"
            data = {
                config.SRC_COL: ["hello", "world"],
                config.TGT_COL: ["hola", "mundo"],
            }
            pd.DataFrame(data).to_csv(csv_file, index=False)
            df = load_data(csv_file, format="csv")
            self.assertEqual(len(df), 2)

    def test_load_json_file(self):
        """load_data should load JSON files."""
        with tempfile.TemporaryDirectory() as tmp:
            json_file = Path(tmp) / "data.json"
            data = {
                config.SRC_COL: ["hello", "world"],
                config.TGT_COL: ["hola", "mundo"],
            }
            pd.DataFrame(data).to_json(json_file, orient="records", lines=True)
            df = load_data(json_file, format="json")
            self.assertEqual(len(df), 2)

    def test_load_parquet_file(self):
        """load_data should load Parquet files."""
        with tempfile.TemporaryDirectory() as tmp:
            parquet_file = Path(tmp) / "data.parquet"
            data = {
                config.SRC_COL: ["hello", "world"],
                config.TGT_COL: ["hola", "mundo"],
            }
            pd.DataFrame(data).to_parquet(parquet_file, index=False)
            df = load_data(parquet_file, format="parquet")
            self.assertEqual(len(df), 2)

    def test_load_infers_format_from_extension(self):
        """load_data should infer format from file extension."""
        with tempfile.TemporaryDirectory() as tmp:
            tsv_file = Path(tmp) / "data.tsv"
            data = {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]}
            pd.DataFrame(data).to_csv(tsv_file, sep="\t", index=False)
            df = load_data(tsv_file)  # No format specified
            self.assertEqual(len(df), 1)


class TestLoadDataErrors(unittest.TestCase):
    """Test error handling in load_data."""

    def test_load_unsupported_format_raises(self):
        """load_data should raise error for unsupported formats."""
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "data.xyz"
            file.write_text("data", encoding="utf-8")
            with self.assertRaises(ValueError) as cm:
                load_data(file, format="xyz")
            self.assertIn("Unsupported format", str(cm.exception))

    def test_load_list_input_raises_type_error(self):
        """load_data should reject list inputs (parallel handled upstream)."""
        with tempfile.TemporaryDirectory() as tmp:
            files = [Path(tmp) / "f1.txt", Path(tmp) / "f2.txt"]
            for f in files:
                f.write_text("data", encoding="utf-8")
            with self.assertRaises(TypeError):
                load_data(files)


class TestSaveData(unittest.TestCase):
    """Test save_data function."""

    def test_save_data_tsv(self):
        """save_data should save TSV files."""
        with tempfile.TemporaryDirectory() as tmp:
            tsv_file = Path(tmp) / "output.tsv"
            data = {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]}
            df = pd.DataFrame(data)
            save_data(df, tsv_file, format="tsv")
            self.assertTrue(tsv_file.exists())
            loaded = pd.read_csv(tsv_file, sep="\t")
            self.assertEqual(len(loaded), 1)

    def test_save_data_csv(self):
        """save_data should save CSV files."""
        with tempfile.TemporaryDirectory() as tmp:
            csv_file = Path(tmp) / "output.csv"
            data = {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]}
            df = pd.DataFrame(data)
            save_data(df, csv_file, format="csv")
            self.assertTrue(csv_file.exists())

    def test_save_data_infers_format(self):
        """save_data should infer format from file extension."""
        with tempfile.TemporaryDirectory() as tmp:
            tsv_file = Path(tmp) / "output.tsv"
            data = {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]}
            df = pd.DataFrame(data)
            save_data(df, tsv_file)  # No format specified
            self.assertTrue(tsv_file.exists())

    def test_save_data_creates_directory(self):
        """save_data should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmp:
            nested_file = Path(tmp) / "subdir" / "output.tsv"
            data = {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]}
            df = pd.DataFrame(data)
            save_data(df, nested_file, format="tsv")
            self.assertTrue(nested_file.exists())


class TestSplitData(unittest.TestCase):
    """Test split_data function."""

    def test_split_data_default_ratios(self):
        """split_data should split with default ratios."""
        data = {
            config.SRC_COL: [f"src{i}" for i in range(100)],
            config.TGT_COL: [f"tgt{i}" for i in range(100)],
        }
        df = pd.DataFrame(data)
        train, val, test = split_data(df)
        self.assertEqual(len(train), 80)
        self.assertEqual(len(val), 10)
        self.assertEqual(len(test), 10)

    def test_split_data_custom_ratios(self):
        """split_data should accept custom ratios with integer rounding."""
        n = 100
        data = {
            config.SRC_COL: [f"src{i}" for i in range(n)],
            config.TGT_COL: [f"tgt{i}" for i in range(n)],
        }
        df = pd.DataFrame(data)
        train_ratio, val_ratio = 0.7, 0.2
        train, val, test = split_data(df, train_ratio=train_ratio, val_ratio=val_ratio)
        # Allow for integer rounding effects
        self.assertEqual(len(train), int(n * train_ratio))
        self.assertEqual(
            len(val), int(n * (train_ratio + val_ratio)) - int(n * train_ratio)
        )
        self.assertEqual(len(test), n - len(train) - len(val))

    def test_split_data_no_overlap(self):
        """split_data should produce non-overlapping splits."""
        data = {
            config.SRC_COL: [f"src{i}" for i in range(100)],
            config.TGT_COL: [f"tgt{i}" for i in range(100)],
        }
        df = pd.DataFrame(data)
        train, val, test = split_data(df, seed=42)
        train_indices = set(train.index)
        val_indices = set(val.index)
        test_indices = set(test.index)
        self.assertEqual(len(train_indices & val_indices), 0)
        self.assertEqual(len(val_indices & test_indices), 0)
        self.assertEqual(len(train_indices & test_indices), 0)

    def test_split_data_reproducible(self):
        """split_data should produce same splits with same seed."""
        data = {
            config.SRC_COL: [f"src{i}" for i in range(100)],
            config.TGT_COL: [f"tgt{i}" for i in range(100)],
        }
        df = pd.DataFrame(data)
        train1, val1, test1 = split_data(df, seed=42)
        train2, val2, test2 = split_data(df, seed=42)
        self.assertTrue(train1.equals(train2))
        self.assertTrue(val1.equals(val2))
        self.assertTrue(test1.equals(test2))


class TestAddLanguageTags(unittest.TestCase):
    """Test add_language_tags function."""

    def test_add_language_tags_prepends_tag(self):
        """add_language_tags should prepend tag to source column."""
        data = {config.SRC_COL: ["hello", "world"], config.TGT_COL: ["hola", "mundo"]}
        df = pd.DataFrame(data)
        tagged = add_language_tags(df, "<2X>")
        self.assertTrue(tagged.iloc[0][config.SRC_COL].startswith("<2X>"))
        self.assertIn("hello", tagged.iloc[0][config.SRC_COL])

    def test_add_language_tags_preserves_target(self):
        """add_language_tags should not modify target column."""
        data = {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]}
        df = pd.DataFrame(data)
        tagged = add_language_tags(df, "<2X>")
        self.assertEqual(tagged.iloc[0][config.TGT_COL], "hola")

    def test_add_language_tags_custom_column(self):
        """add_language_tags should work with custom source column."""
        data = {"my_src": ["hello"], config.TGT_COL: ["hola"]}
        df = pd.DataFrame(data)
        tagged = add_language_tags(df, "<2X>", src_col="my_src")
        self.assertTrue(tagged.iloc[0]["my_src"].startswith("<2X>"))

    def test_add_language_tags_returns_copy(self):
        """add_language_tags should return a copy, not modify original."""
        data = {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]}
        df = pd.DataFrame(data)
        original_value = df.iloc[0][config.SRC_COL]
        tagged = add_language_tags(df, "<2X>")
        self.assertEqual(df.iloc[0][config.SRC_COL], original_value)
        self.assertNotEqual(tagged.iloc[0][config.SRC_COL], original_value)

    def test_add_language_tags_handles_numeric_values(self):
        """add_language_tags should convert numeric values to string."""
        data = {config.SRC_COL: [123], config.TGT_COL: ["hola"]}
        df = pd.DataFrame(data)
        tagged = add_language_tags(df, "<2X>")
        self.assertIn("123", tagged.iloc[0][config.SRC_COL])


class TestPreprocessingEdgeCases(unittest.TestCase):
    """Test edge cases in preprocessing functions."""

    def test_load_empty_parallel_files(self):
        """load_data should handle empty parallel files."""
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.txt"
            tgt = Path(tmp) / "tgt.txt"
            src.write_text("", encoding="utf-8")
            tgt.write_text("", encoding="utf-8")
            df = parallel_txt_to_dataframe(src, tgt)
            self.assertEqual(len(df), 0)

    def test_split_small_dataset(self):
        """split_data should handle very small datasets."""
        data = {config.SRC_COL: ["a", "b", "c"], config.TGT_COL: ["x", "y", "z"]}
        df = pd.DataFrame(data)
        train, val, test = split_data(df, seed=42)
        # Should still split, even if some splits are very small
        self.assertGreaterEqual(len(train), 0)
        self.assertEqual(len(train) + len(val) + len(test), 3)


class TestSplitDataConfigOverride(unittest.TestCase):
    """Test config override behavior for split_data function."""

    def setUp(self):
        """Set up test data."""
        self.data = {
            config.SRC_COL: [f"src{i}" for i in range(100)],
            config.TGT_COL: [f"tgt{i}" for i in range(100)],
        }
        self.df = pd.DataFrame(self.data)

    def test_split_data_uses_default_train_ratio(self):
        """split_data should use default config train_ratio (0.8)."""
        train, val, test = split_data(self.df)
        # Default train_ratio is 0.8
        self.assertEqual(len(train), 80)

    def test_split_data_uses_default_val_ratio(self):
        """split_data should use default config val_ratio (0.1)."""
        train, val, test = split_data(self.df)
        # Default val_ratio is 0.1
        self.assertEqual(len(val), 10)

    def test_split_data_uses_default_seed(self):
        """split_data should use default config seed (42)."""
        train1, val1, test1 = split_data(self.df)
        train2, val2, test2 = split_data(self.df, seed=42)
        # Both should produce identical results since default seed is 42
        self.assertTrue(train1.equals(train2))
        self.assertTrue(val1.equals(val2))
        self.assertTrue(test1.equals(test2))

    def test_split_data_explicit_train_ratio_overrides_default(self):
        """Explicit train_ratio should override default config value."""
        train, val, test = split_data(self.df, train_ratio=0.7)
        # Explicit train_ratio=0.7 should override default 0.8
        self.assertEqual(len(train), 70)

    def test_split_data_explicit_val_ratio_overrides_default(self):
        """Explicit val_ratio should override default config value."""
        train, val, test = split_data(self.df, val_ratio=0.2)
        # Explicit val_ratio=0.2 should override default 0.1
        self.assertEqual(len(val), 20)

    def test_split_data_explicit_seed_overrides_default(self):
        """Explicit seed should override default config value."""
        train1, val1, test1 = split_data(self.df, seed=123)
        train2, val2, test2 = split_data(self.df, seed=456)
        # Different seeds should produce different splits
        self.assertFalse(train1.equals(train2))

    def test_split_data_config_train_ratio_overrides_module_default(self):
        """Config train_ratio should override module-level default."""
        custom_cfg = Config(train_ratio=0.6, val_ratio=0.2)
        train, val, test = split_data(self.df, config=custom_cfg)
        self.assertEqual(len(train), 60)

    def test_split_data_config_val_ratio_overrides_module_default(self):
        """Config val_ratio should override module-level default."""
        custom_cfg = Config(train_ratio=0.7, val_ratio=0.15)
        train, val, test = split_data(self.df, config=custom_cfg)
        self.assertEqual(len(val), 15)

    def test_split_data_config_seed_overrides_module_default(self):
        """Config seed should override module-level default."""
        custom_cfg = Config(seed=999)
        train1, val1, test1 = split_data(self.df, config=custom_cfg)
        train2, val2, test2 = split_data(self.df, seed=999)
        # Both should produce identical results
        self.assertTrue(train1.equals(train2))

    def test_split_data_explicit_train_ratio_overrides_config(self):
        """Explicit train_ratio should override config value."""
        custom_cfg = Config(train_ratio=0.5)
        train, val, test = split_data(self.df, train_ratio=0.9, config=custom_cfg)
        # Explicit parameter should win over config
        self.assertEqual(len(train), 90)

    def test_split_data_explicit_val_ratio_overrides_config(self):
        """Explicit val_ratio should override config value."""
        custom_cfg = Config(val_ratio=0.05)
        train, val, test = split_data(self.df, val_ratio=0.15, config=custom_cfg)
        # Explicit parameter should win over config
        self.assertEqual(len(val), 15)

    def test_split_data_explicit_seed_overrides_config(self):
        """Explicit seed should override config value."""
        custom_cfg = Config(seed=111)
        train1, val1, test1 = split_data(self.df, seed=222, config=custom_cfg)
        train2, val2, test2 = split_data(self.df, seed=222)
        # Explicit seed should be used, not config seed
        self.assertTrue(train1.equals(train2))


class TestAddLanguageTagsConfigOverride(unittest.TestCase):
    """Test config override behavior for add_language_tags function."""

    def test_add_language_tags_uses_default_src_col(self):
        """add_language_tags should use default config src_col."""
        df = pd.DataFrame({config.SRC_COL: ["hello"], config.TGT_COL: ["hola"]})
        result = add_language_tags(df, "<en>")
        self.assertIn(config.SRC_COL, result.columns)
        self.assertTrue(result[config.SRC_COL].iloc[0].startswith("<en>"))

    def test_add_language_tags_explicit_src_col_overrides_default(self):
        """Explicit src_col should override default."""
        df = pd.DataFrame({"source": ["hello"], "target": ["hola"]})
        result = add_language_tags(df, "<en>", src_col="source")
        self.assertTrue(result["source"].iloc[0].startswith("<en>"))

    def test_add_language_tags_uses_passed_config(self):
        """add_language_tags should use passed config src_col."""
        custom_cfg = Config(src_col="my_src")
        df = pd.DataFrame({"my_src": ["hello"], "tgt": ["hola"]})
        result = add_language_tags(df, "<en>", config=custom_cfg)
        self.assertTrue(result["my_src"].iloc[0].startswith("<en>"))

    def test_add_language_tags_explicit_overrides_passed_config(self):
        """Explicit src_col should override passed config."""
        custom_cfg = Config(src_col="my_src")
        df = pd.DataFrame({"other": ["hello"], "tgt": ["hola"]})
        result = add_language_tags(df, "<en>", src_col="other", config=custom_cfg)
        self.assertTrue(result["other"].iloc[0].startswith("<en>"))

    def test_add_language_tags_config_src_col_overrides_module_default(self):
        """Config src_col should override module-level default."""
        custom_cfg = Config(src_col="custom_source")
        df = pd.DataFrame({"custom_source": ["hello"], "tgt": ["hola"]})
        result = add_language_tags(df, "<2X>", config=custom_cfg)
        self.assertIn("custom_source", result.columns)
        self.assertTrue(result["custom_source"].iloc[0].startswith("<2X>"))

    def test_add_language_tags_preserves_other_columns(self):
        """add_language_tags should not modify columns other than src_col."""
        df = pd.DataFrame(
            {config.SRC_COL: ["hello"], config.TGT_COL: ["hola"], "extra": ["data"]}
        )
        result = add_language_tags(df, "<en>")
        self.assertEqual(result[config.TGT_COL].iloc[0], "hola")
        self.assertEqual(result["extra"].iloc[0], "data")


class TestParallelTxtToDataframeConfigOverride(unittest.TestCase):
    """Test config override behavior for parallel_txt_to_dataframe function."""

    def setUp(self):
        """Set up temp files."""
        self.tmpdir = tempfile.mkdtemp()
        self.src_path = Path(self.tmpdir) / "src.txt"
        self.tgt_path = Path(self.tmpdir) / "tgt.txt"
        self.src_path.write_text("hello\nworld\n", encoding="utf-8")
        self.tgt_path.write_text("hola\nmundo\n", encoding="utf-8")

    def tearDown(self):
        """Clean up temp files."""
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_parallel_txt_uses_default_src_col(self):
        """parallel_txt_to_dataframe should use default config src_col."""
        df = parallel_txt_to_dataframe(self.src_path, self.tgt_path)
        # Default src_col is 'src'
        self.assertIn("src", df.columns)

    def test_parallel_txt_uses_default_tgt_col(self):
        """parallel_txt_to_dataframe should use default config tgt_col."""
        df = parallel_txt_to_dataframe(self.src_path, self.tgt_path)
        # Default tgt_col is 'tgt'
        self.assertIn("tgt", df.columns)

    def test_parallel_txt_explicit_src_col_overrides_default(self):
        """Explicit src_col should override default config value."""
        df = parallel_txt_to_dataframe(self.src_path, self.tgt_path, src_col="source")
        self.assertIn("source", df.columns)
        self.assertNotIn("src", df.columns)

    def test_parallel_txt_explicit_tgt_col_overrides_default(self):
        """Explicit tgt_col should override default config value."""
        df = parallel_txt_to_dataframe(self.src_path, self.tgt_path, tgt_col="target")
        self.assertIn("target", df.columns)
        self.assertNotIn("tgt", df.columns)

    def test_parallel_txt_config_src_col_overrides_module_default(self):
        """Config src_col should override module-level default."""
        custom_cfg = Config(src_col="english")
        df = parallel_txt_to_dataframe(self.src_path, self.tgt_path, config=custom_cfg)
        self.assertIn("english", df.columns)

    def test_parallel_txt_config_tgt_col_overrides_module_default(self):
        """Config tgt_col should override module-level default."""
        custom_cfg = Config(tgt_col="spanish")
        df = parallel_txt_to_dataframe(self.src_path, self.tgt_path, config=custom_cfg)
        self.assertIn("spanish", df.columns)

    def test_parallel_txt_explicit_src_col_overrides_config(self):
        """Explicit src_col should override config value."""
        custom_cfg = Config(src_col="config_src")
        df = parallel_txt_to_dataframe(
            self.src_path, self.tgt_path, src_col="explicit_src", config=custom_cfg
        )
        self.assertIn("explicit_src", df.columns)
        self.assertNotIn("config_src", df.columns)

    def test_parallel_txt_explicit_tgt_col_overrides_config(self):
        """Explicit tgt_col should override config value."""
        custom_cfg = Config(tgt_col="config_tgt")
        df = parallel_txt_to_dataframe(
            self.src_path, self.tgt_path, tgt_col="explicit_tgt", config=custom_cfg
        )
        self.assertIn("explicit_tgt", df.columns)
        self.assertNotIn("config_tgt", df.columns)


class TestTrainSentencepieceConfigOverride(unittest.TestCase):
    """Test config override behavior for train_sentencepiece function."""

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_uses_default_vocab_size(self, mock_load, mock_train):
        """train_sentencepiece should use default config vocab_size."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})

        train_sentencepiece([Path("/fake/train.tsv")], "model_prefix")

        # Default vocab_size is 32000
        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["vocab_size"], 32000)

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_explicit_vocab_size_overrides_default(
        self, mock_load, mock_train
    ):
        """Explicit vocab_size should override default config value."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})

        train_sentencepiece([Path("/fake/train.tsv")], "model_prefix", vocab_size=8000)

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["vocab_size"], 8000)

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_config_vocab_size_overrides_module_default(
        self, mock_load, mock_train
    ):
        """Config vocab_size should override module-level default."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})
        custom_cfg = Config(vocab_size=16000)

        train_sentencepiece(
            [Path("/fake/train.tsv")], "model_prefix", config=custom_cfg
        )

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["vocab_size"], 16000)

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_explicit_vocab_size_overrides_config(
        self, mock_load, mock_train
    ):
        """Explicit vocab_size should override config value."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})
        custom_cfg = Config(vocab_size=16000)

        train_sentencepiece(
            [Path("/fake/train.tsv")],
            "model_prefix",
            vocab_size=4000,
            config=custom_cfg,
        )

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["vocab_size"], 4000)

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_uses_default_model_type(self, mock_load, mock_train):
        """train_sentencepiece should use default config model_type."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})

        train_sentencepiece([Path("/fake/train.tsv")], "model_prefix")

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        # Default model_type is 'bpe'
        self.assertEqual(call_kwargs["model_type"], "bpe")

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_explicit_model_type_overrides_default(
        self, mock_load, mock_train
    ):
        """Explicit model_type should override default config value."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})

        train_sentencepiece(
            [Path("/fake/train.tsv")], "model_prefix", model_type="unigram"
        )

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["model_type"], "unigram")

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_config_model_type_overrides_module_default(
        self, mock_load, mock_train
    ):
        """Config model_type should override module-level default."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})
        custom_cfg = Config(sp_model_type="char")

        train_sentencepiece(
            [Path("/fake/train.tsv")], "model_prefix", config=custom_cfg
        )

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["model_type"], "char")

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_explicit_model_type_overrides_config(
        self, mock_load, mock_train
    ):
        """Explicit model_type should override config value."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})
        custom_cfg = Config(sp_model_type="char")

        train_sentencepiece(
            [Path("/fake/train.tsv")],
            "model_prefix",
            model_type="word",
            config=custom_cfg,
        )

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["model_type"], "word")

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_uses_default_character_coverage(
        self, mock_load, mock_train
    ):
        """train_sentencepiece should use default config character_coverage."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})

        train_sentencepiece([Path("/fake/train.tsv")], "model_prefix")

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        # Default character_coverage is 1.0
        self.assertEqual(call_kwargs["character_coverage"], 1.0)

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_config_character_coverage_overrides_default(
        self, mock_load, mock_train
    ):
        """Config character_coverage should override module-level default."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})
        custom_cfg = Config(sp_character_coverage=0.9995)

        train_sentencepiece(
            [Path("/fake/train.tsv")], "model_prefix", config=custom_cfg
        )

        mock_train.assert_called_once()
        call_kwargs = mock_train.call_args[1]
        self.assertEqual(call_kwargs["character_coverage"], 0.9995)

    @patch("torchlingo.preprocessing.sentencepiece.spm.SentencePieceTrainer.train")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_train_sentencepiece_uses_config_src_col(self, mock_load, mock_train):
        """train_sentencepiece should use config src_col for column selection."""
        from torchlingo.preprocessing.sentencepiece import train_sentencepiece

        mock_load.return_value = pd.DataFrame(
            {"english": ["hello"], "spanish": ["hola"]}
        )
        custom_cfg = Config(src_col="english", tgt_col="spanish")

        train_sentencepiece(
            [Path("/fake/train.tsv")], "model_prefix", config=custom_cfg
        )

        mock_train.assert_called_once()


class TestApplySentencepieceConfigOverride(unittest.TestCase):
    """Test config override behavior for apply_sentencepiece function."""

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_uses_default_src_col(self, mock_load, mock_save):
        """apply_sentencepiece should use default config src_col."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["hel", "lo"]

        apply_sentencepiece(Path("/fake/input.tsv"), Path("/fake/output.tsv"), mock_sp)

        # Should process 'src' column (default)
        mock_load.assert_called_once()
        mock_save.assert_called_once()

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_explicit_src_col_overrides_default(
        self, mock_load, mock_save
    ):
        """Explicit src_col should override default config value."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame({"english": ["hello"], "tgt": ["hola"]})
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["hel", "lo"]

        apply_sentencepiece(
            Path("/fake/input.tsv"),
            Path("/fake/output.tsv"),
            mock_sp,
            src_col="english",
        )

        mock_save.assert_called_once()
        saved_df = mock_save.call_args[0][0]
        # The 'english' column should have been processed
        self.assertIn("english", saved_df.columns)

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_config_src_col_overrides_module_default(
        self, mock_load, mock_save
    ):
        """Config src_col should override module-level default."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame({"source": ["hello"], "target": ["hola"]})
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["hel", "lo"]
        custom_cfg = Config(src_col="source", tgt_col="target")

        apply_sentencepiece(
            Path("/fake/input.tsv"),
            Path("/fake/output.tsv"),
            mock_sp,
            config=custom_cfg,
        )

        mock_save.assert_called_once()
        saved_df = mock_save.call_args[0][0]
        self.assertIn("source", saved_df.columns)
        self.assertIn("target", saved_df.columns)

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_explicit_src_col_overrides_config(
        self, mock_load, mock_save
    ):
        """Explicit src_col should override config value."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame(
            {"explicit_src": ["hello"], "tgt": ["hola"]}
        )
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["hel", "lo"]
        custom_cfg = Config(src_col="config_src")

        apply_sentencepiece(
            Path("/fake/input.tsv"),
            Path("/fake/output.tsv"),
            mock_sp,
            src_col="explicit_src",
            config=custom_cfg,
        )

        mock_save.assert_called_once()
        saved_df = mock_save.call_args[0][0]
        self.assertIn("explicit_src", saved_df.columns)

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_uses_default_tgt_col(self, mock_load, mock_save):
        """apply_sentencepiece should use default config tgt_col."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "tgt": ["hola"]})
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["ho", "la"]

        apply_sentencepiece(Path("/fake/input.tsv"), Path("/fake/output.tsv"), mock_sp)

        mock_save.assert_called_once()
        saved_df = mock_save.call_args[0][0]
        self.assertIn("tgt", saved_df.columns)

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_explicit_tgt_col_overrides_default(
        self, mock_load, mock_save
    ):
        """Explicit tgt_col should override default config value."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "spanish": ["hola"]})
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["ho", "la"]

        apply_sentencepiece(
            Path("/fake/input.tsv"),
            Path("/fake/output.tsv"),
            mock_sp,
            tgt_col="spanish",
        )

        mock_save.assert_called_once()
        saved_df = mock_save.call_args[0][0]
        self.assertIn("spanish", saved_df.columns)

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_config_tgt_col_overrides_module_default(
        self, mock_load, mock_save
    ):
        """Config tgt_col should override module-level default."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame({"src": ["hello"], "target": ["hola"]})
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["ho", "la"]
        custom_cfg = Config(tgt_col="target")

        apply_sentencepiece(
            Path("/fake/input.tsv"),
            Path("/fake/output.tsv"),
            mock_sp,
            config=custom_cfg,
        )

        mock_save.assert_called_once()
        saved_df = mock_save.call_args[0][0]
        self.assertIn("target", saved_df.columns)

    @patch("torchlingo.preprocessing.sentencepiece.save_data")
    @patch("torchlingo.preprocessing.sentencepiece.load_data")
    def test_apply_sentencepiece_explicit_tgt_col_overrides_config(
        self, mock_load, mock_save
    ):
        """Explicit tgt_col should override config value."""
        from torchlingo.preprocessing.sentencepiece import apply_sentencepiece

        mock_load.return_value = pd.DataFrame(
            {"src": ["hello"], "explicit_tgt": ["hola"]}
        )
        mock_sp = MagicMock()
        mock_sp.encode.return_value = ["ho", "la"]
        custom_cfg = Config(tgt_col="config_tgt")

        apply_sentencepiece(
            Path("/fake/input.tsv"),
            Path("/fake/output.tsv"),
            mock_sp,
            tgt_col="explicit_tgt",
            config=custom_cfg,
        )

        mock_save.assert_called_once()
        saved_df = mock_save.call_args[0][0]
        self.assertIn("explicit_tgt", saved_df.columns)


if __name__ == "__main__":
    unittest.main()
