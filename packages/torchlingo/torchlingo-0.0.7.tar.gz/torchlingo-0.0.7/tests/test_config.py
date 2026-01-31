import unittest
from pathlib import Path
from torchlingo import config
from torchlingo.config import Config


class TestConfigConstants(unittest.TestCase):
    """Test module-level configuration constants."""

    def test_special_token_values(self):
        """Verify special token string values."""
        self.assertEqual(config.PAD_TOKEN, "<pad>")
        self.assertEqual(config.UNK_TOKEN, "<unk>")
        self.assertEqual(config.SOS_TOKEN, "<sos>")
        self.assertEqual(config.EOS_TOKEN, "<eos>")

    def test_special_token_indices(self):
        """Verify special token index values."""
        self.assertEqual(config.PAD_IDX, 0)
        self.assertEqual(config.UNK_IDX, 1)
        self.assertEqual(config.SOS_IDX, 2)
        self.assertEqual(config.EOS_IDX, 3)

    def test_special_token_indices_unique(self):
        """Verify all special token indices are unique."""
        indices = [config.PAD_IDX, config.UNK_IDX, config.SOS_IDX, config.EOS_IDX]
        self.assertEqual(len(indices), len(set(indices)))

    def test_base_directories_exist(self):
        """Verify base directories are Path objects."""
        self.assertIsInstance(config.BASE_DIR, Path)
        self.assertIsInstance(config.DATA_DIR, Path)
        self.assertIsInstance(config.CHECKPOINT_DIR, Path)
        self.assertIsInstance(config.OUTPUT_DIR, Path)

    def test_data_format_valid(self):
        """Verify data format is a supported type."""
        self.assertIn(config.DATA_FORMAT, ["tsv", "csv", "parquet", "json", "txt"])

    def test_column_names_are_strings(self):
        """Verify column names are strings."""
        self.assertIsInstance(config.SRC_COL, str)
        self.assertIsInstance(config.TGT_COL, str)
        self.assertGreater(len(config.SRC_COL), 0)
        self.assertGreater(len(config.TGT_COL), 0)


class TestConfigHyperparameters(unittest.TestCase):
    """Test hyperparameter value constraints."""

    def test_batch_size_positive(self):
        """Batch size must be positive."""
        self.assertGreater(config.BATCH_SIZE, 0)
        self.assertIsInstance(config.BATCH_SIZE, int)

    def test_learning_rate_positive(self):
        """Learning rate must be positive."""
        self.assertGreater(config.LEARNING_RATE, 0)
        self.assertIsInstance(config.LEARNING_RATE, (int, float))

    def test_model_dimensions_positive(self):
        """Model dimensions must be positive integers."""
        self.assertGreater(config.D_MODEL, 0)
        self.assertIsInstance(config.D_MODEL, int)
        self.assertGreater(config.D_FF, 0)
        self.assertIsInstance(config.D_FF, int)

    def test_num_heads_divides_d_model(self):
        """Number of heads must divide d_model evenly."""
        self.assertEqual(config.D_MODEL % config.N_HEADS, 0)

    def test_num_layers_positive(self):
        """Number of layers must be positive."""
        self.assertGreater(config.NUM_ENCODER_LAYERS, 0)
        self.assertGreater(config.NUM_DECODER_LAYERS, 0)
        self.assertIsInstance(config.NUM_ENCODER_LAYERS, int)
        self.assertIsInstance(config.NUM_DECODER_LAYERS, int)

    def test_dropout_in_valid_range(self):
        """Dropout must be in [0, 1)."""
        self.assertGreaterEqual(config.DROPOUT, 0.0)
        self.assertLess(config.DROPOUT, 1.0)

    def test_label_smoothing_in_valid_range(self):
        """Label smoothing must be in [0, 1)."""
        self.assertGreaterEqual(config.LABEL_SMOOTHING, 0.0)
        self.assertLess(config.LABEL_SMOOTHING, 1.0)

    def test_max_seq_length_positive(self):
        """Max sequence length must be positive."""
        self.assertGreater(config.MAX_SEQ_LENGTH, 0)
        self.assertIsInstance(config.MAX_SEQ_LENGTH, int)

    def test_beam_size_positive(self):
        """Beam size must be positive."""
        self.assertGreater(config.BEAM_SIZE, 0)
        self.assertIsInstance(config.BEAM_SIZE, int)

    def test_adam_betas_valid(self):
        """Adam betas must be in [0, 1)."""
        self.assertEqual(len(config.ADAM_BETAS), 2)
        for beta in config.ADAM_BETAS:
            self.assertGreaterEqual(beta, 0.0)
            self.assertLess(beta, 1.0)


class TestConfigClass(unittest.TestCase):
    """Test the Config class."""

    def test_config_initialization_defaults(self):
        """Config should initialize with default values."""
        cfg = Config()
        self.assertEqual(cfg.batch_size, config.BATCH_SIZE)
        self.assertEqual(cfg.learning_rate, config.LEARNING_RATE)
        self.assertEqual(cfg.d_model, config.D_MODEL)

    def test_config_initialization_custom_values(self):
        """Config should accept custom values on initialization."""
        cfg = Config(batch_size=32, learning_rate=0.001, d_model=256)
        self.assertEqual(cfg.batch_size, 32)
        self.assertEqual(cfg.learning_rate, 0.001)
        self.assertEqual(cfg.d_model, 256)

    def test_config_modification(self):
        """Config attributes should be modifiable."""
        cfg = Config()
        original_batch_size = cfg.batch_size
        cfg.batch_size = 128
        self.assertEqual(cfg.batch_size, 128)
        self.assertNotEqual(cfg.batch_size, original_batch_size)

    def test_config_copy_independence(self):
        """Copied configs should be independent."""
        cfg1 = Config(batch_size=64)
        cfg2 = cfg1.copy()
        cfg2.batch_size = 32
        self.assertEqual(cfg1.batch_size, 64)
        self.assertEqual(cfg2.batch_size, 32)

    def test_config_has_special_tokens(self):
        """Config should have special token attributes."""
        cfg = Config()
        self.assertEqual(cfg.pad_token, "<pad>")
        self.assertEqual(cfg.unk_token, "<unk>")
        self.assertEqual(cfg.sos_token, "<sos>")
        self.assertEqual(cfg.eos_token, "<eos>")

    def test_config_has_special_indices(self):
        """Config should have special token index attributes."""
        cfg = Config()
        self.assertEqual(cfg.pad_idx, 0)
        self.assertEqual(cfg.unk_idx, 1)
        self.assertEqual(cfg.sos_idx, 2)
        self.assertEqual(cfg.eos_idx, 3)

    def test_config_paths_are_paths(self):
        """Config paths should be Path objects."""
        cfg = Config()
        self.assertIsInstance(cfg.data_dir, Path)
        self.assertIsInstance(cfg.checkpoint_dir, Path)
        self.assertIsInstance(cfg.output_dir, Path)


class TestConfigDeviceSettings(unittest.TestCase):
    """Test device configuration."""

    def test_device_is_valid(self):
        """Device should be either cpu or cuda."""
        self.assertIn(config.DEVICE, ["cpu", "cuda"])

    def test_num_workers_non_negative(self):
        """Number of workers must be non-negative."""
        self.assertGreaterEqual(config.NUM_WORKERS, 0)
        self.assertIsInstance(config.NUM_WORKERS, int)

    def test_seed_is_integer(self):
        """Seed must be an integer."""
        self.assertIsInstance(config.SEED, int)


class TestConfigSentencePieceSettings(unittest.TestCase):
    """Test SentencePiece configuration."""

    def test_sentencepiece_model_type_valid(self):
        """SentencePiece model type must be valid."""
        valid_types = ["bpe", "unigram", "char", "word"]
        self.assertIn(config.SP_MODEL_TYPE, valid_types)

    def test_character_coverage_in_valid_range(self):
        """Character coverage must be in (0, 1]."""
        self.assertGreater(config.SP_CHARACTER_COVERAGE, 0.0)
        self.assertLessEqual(config.SP_CHARACTER_COVERAGE, 1.0)

    def test_vocab_size_positive(self):
        """Vocabulary size must be positive."""
        self.assertGreater(config.VOCAB_SIZE, 0)
        self.assertIsInstance(config.VOCAB_SIZE, int)

    def test_sentencepiece_src_tgt_defaults_shared(self):
        """Src/tgt SentencePiece defaults should share the same paths."""
        self.assertEqual(
            config.SENTENCEPIECE_SRC_MODEL_PREFIX, config.SENTENCEPIECE_MODEL_PREFIX
        )
        self.assertEqual(
            config.SENTENCEPIECE_TGT_MODEL_PREFIX, config.SENTENCEPIECE_MODEL_PREFIX
        )
        self.assertEqual(config.SENTENCEPIECE_SRC_MODEL, config.SENTENCEPIECE_MODEL)
        self.assertEqual(config.SENTENCEPIECE_TGT_MODEL, config.SENTENCEPIECE_MODEL)

    def test_config_accepts_distinct_sentencepiece_models(self):
        """Config should allow different src/tgt SentencePiece models."""
        cfg = Config(
            sentencepiece_src_model_prefix="src_path",
            sentencepiece_tgt_model_prefix="tgt_path",
        )
        self.assertEqual(cfg.sentencepiece_src_model, "src_path.model")
        self.assertEqual(cfg.sentencepiece_tgt_model, "tgt_path.model")
        self.assertNotEqual(cfg.sentencepiece_src_model, cfg.sentencepiece_tgt_model)


class TestConfigIntervalSettings(unittest.TestCase):
    """Test training interval settings."""

    def test_val_interval_positive(self):
        """Validation interval must be positive."""
        self.assertGreater(config.VAL_INTERVAL, 0)
        self.assertIsInstance(config.VAL_INTERVAL, int)

    def test_save_interval_positive(self):
        """Save interval must be positive."""
        self.assertGreater(config.SAVE_INTERVAL, 0)
        self.assertIsInstance(config.SAVE_INTERVAL, int)

    def test_log_interval_positive(self):
        """Log interval must be positive."""
        self.assertGreater(config.LOG_INTERVAL, 0)
        self.assertIsInstance(config.LOG_INTERVAL, int)

    def test_patience_positive(self):
        """Patience must be positive."""
        self.assertGreater(config.PATIENCE, 0)
        self.assertIsInstance(config.PATIENCE, int)


class TestConfigGetDefault(unittest.TestCase):
    """Test get_default_config function."""

    def test_get_default_config_returns_config(self):
        """get_default_config should return a Config instance."""
        cfg = config.get_default_config()
        self.assertIsInstance(cfg, Config)

    def test_get_default_config_has_correct_values(self):
        """get_default_config should have module-level default values."""
        cfg = config.get_default_config()
        self.assertEqual(cfg.batch_size, config.BATCH_SIZE)
        self.assertEqual(cfg.learning_rate, config.LEARNING_RATE)

    def test_get_default_config_creates_new_instance(self):
        """Each call to get_default_config should create a new instance."""
        cfg1 = config.get_default_config()
        cfg2 = config.get_default_config()
        self.assertIsNot(cfg1, cfg2)
        cfg1.batch_size = 999
        self.assertNotEqual(cfg2.batch_size, 999)


if __name__ == "__main__":
    unittest.main()
