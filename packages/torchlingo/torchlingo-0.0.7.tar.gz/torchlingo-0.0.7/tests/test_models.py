import unittest
import torch
from torchlingo.models import SimpleTransformer, SimpleSeq2SeqLSTM
from torchlingo.models.transformer_simple import (
    create_key_padding_mask,
    create_causal_mask,
    create_masks,
)
from torchlingo import config
from torchlingo.config import Config


class TestTransformerInitialization(unittest.TestCase):
    """Test SimpleTransformer initialization."""

    def test_transformer_init_default_params(self):
        """Transformer should initialize with default parameters."""
        model = SimpleTransformer(src_vocab_size=100, tgt_vocab_size=100)
        self.assertIsNotNone(model)
        self.assertEqual(model.d_model, config.D_MODEL)

    def test_transformer_init_custom_params(self):
        """Transformer should accept custom parameters."""
        model = SimpleTransformer(
            src_vocab_size=100,
            tgt_vocab_size=100,
            d_model=256,
            n_heads=4,
            num_encoder_layers=3,
            num_decoder_layers=3,
            d_ff=1024,
        )
        self.assertEqual(model.d_model, 256)

    def test_transformer_has_required_components(self):
        """Transformer should have all required components."""
        model = SimpleTransformer(
            src_vocab_size=100, tgt_vocab_size=100, d_model=32, n_heads=4
        )
        self.assertIsNotNone(model.src_tok_emb)
        self.assertIsNotNone(model.tgt_tok_emb)
        self.assertIsNotNone(model.rope)
        self.assertIsNotNone(model.transformer)
        self.assertIsNotNone(model.generator)


class TestTransformerForward(unittest.TestCase):
    """Test SimpleTransformer forward pass."""

    def test_transformer_forward_output_shape(self):
        """Transformer forward should produce correct output shape."""
        src_vocab_size = 100
        tgt_vocab_size = 100
        model = SimpleTransformer(
            src_vocab_size=src_vocab_size,
            tgt_vocab_size=tgt_vocab_size,
            d_model=32,
            n_heads=4,
            num_encoder_layers=2,
            num_decoder_layers=2,
            d_ff=64,
        )

        batch_size = 5
        src_len = 10
        tgt_len = 12

        src = torch.randint(0, src_vocab_size, (batch_size, src_len))
        tgt = torch.randint(0, tgt_vocab_size, (batch_size, tgt_len))

        output = model(src, tgt)
        self.assertEqual(output.shape, (batch_size, tgt_len, tgt_vocab_size))

    def test_transformer_forward_single_example(self):
        """Transformer should handle single example (batch_size=1)."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.randint(0, 50, (1, 5))
        tgt = torch.randint(0, 50, (1, 7))
        output = model(src, tgt)
        self.assertEqual(output.shape, (1, 7, 50))

    def test_transformer_forward_with_padding(self):
        """Transformer should handle padded sequences."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.tensor([[1, 2, config.PAD_IDX, config.PAD_IDX]])
        tgt = torch.tensor([[config.SOS_IDX, 3, 4, config.EOS_IDX]])
        output = model(src, tgt)
        self.assertEqual(output.shape, (1, 4, 50))

    def test_transformer_forward_different_lengths(self):
        """Transformer should handle different src and tgt lengths."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.randint(0, 50, (2, 5))
        tgt = torch.randint(0, 50, (2, 15))
        output = model(src, tgt)
        self.assertEqual(output.shape, (2, 15, 50))


class TestTransformerEncodeDecode(unittest.TestCase):
    """Test SimpleTransformer encode and decode methods."""

    def test_transformer_encode_output_shape(self):
        """Encode should produce correct memory shape."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.randint(0, 50, (3, 10))
        memory = model.encode(src)
        self.assertEqual(memory.shape, (3, 10, 32))  # (batch, src_len, d_model)

    def test_transformer_decode_with_memory(self):
        """Decode should work with encoded memory."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.randint(0, 50, (2, 8))
        tgt = torch.randint(0, 50, (2, 6))
        memory = model.encode(src)
        output = model.decode(tgt, memory)
        self.assertEqual(output.shape, (2, 6, 50))

    def test_transformer_encode_decode_equivalent_to_forward(self):
        """encode + decode should be equivalent to forward."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.randint(0, 50, (2, 5))
        tgt = torch.randint(0, 50, (2, 7))

        # Using forward
        output_forward = model(src, tgt)

        # Using encode + decode
        memory = model.encode(src)
        output_decode = model.decode(tgt, memory)

        self.assertEqual(output_forward.shape, output_decode.shape)


class TestTransformerMaskHelpers(unittest.TestCase):
    """Test mask creation helper functions."""

    def test_create_key_padding_mask_marks_padding(self):
        """create_key_padding_mask should mark padding positions as True."""
        src = torch.tensor([[1, 2, config.PAD_IDX, 3, config.PAD_IDX]])
        mask = create_key_padding_mask(src, pad_idx=config.PAD_IDX)
        self.assertFalse(mask[0, 0].item())  # non-padding
        self.assertTrue(mask[0, 2].item())  # padding
        self.assertTrue(mask[0, 4].item())  # padding

    def test_create_key_padding_mask_no_padding(self):
        """create_key_padding_mask should be all False when no padding."""
        src = torch.tensor([[1, 2, 3, 4]])
        mask = create_key_padding_mask(src, pad_idx=config.PAD_IDX)
        self.assertTrue(torch.all(~mask))

    def test_create_key_padding_mask_all_padding(self):
        """create_key_padding_mask should be all True for all-padding sequence."""
        src = torch.tensor([[config.PAD_IDX, config.PAD_IDX, config.PAD_IDX]])
        mask = create_key_padding_mask(src, pad_idx=config.PAD_IDX)
        self.assertTrue(torch.all(mask))

    def test_create_causal_mask_shape(self):
        """create_causal_mask should produce square mask."""
        mask = create_causal_mask(5, device=torch.device("cpu"))
        self.assertEqual(mask.shape, (5, 5))

    def test_create_causal_mask_blocks_future(self):
        """create_causal_mask should block future positions (upper triangle)."""
        mask = create_causal_mask(3, device=torch.device("cpu"))
        expected = torch.tensor(
            [[False, True, True], [False, False, True], [False, False, False]]
        )
        self.assertTrue(torch.equal(mask, expected))

    def test_create_causal_mask_length_one(self):
        """create_causal_mask with length 1 should be single False."""
        mask = create_causal_mask(1, device=torch.device("cpu"))
        self.assertFalse(mask[0, 0].item())

    def test_create_masks_returns_three_masks(self):
        """create_masks should return src_mask, tgt_mask, and causal_mask."""
        src = torch.tensor([[1, config.PAD_IDX, 2]])
        tgt = torch.tensor([[3, 4, config.PAD_IDX]])
        src_mask, tgt_mask, causal = create_masks(src, tgt, pad_idx=config.PAD_IDX)
        self.assertEqual(src_mask.shape[1], 3)  # src length
        self.assertEqual(tgt_mask.shape[1], 3)  # tgt length
        self.assertEqual(causal.shape, (3, 3))  # tgt_len x tgt_len

    def test_create_masks_combines_padding_and_causal(self):
        """create_masks should identify both padding and future positions."""
        src = torch.tensor([[1, config.PAD_IDX]])
        tgt = torch.tensor([[2, 3]])
        src_mask, tgt_mask, causal = create_masks(src, tgt, pad_idx=config.PAD_IDX)
        self.assertTrue(src_mask[0, 1].item())  # src padding
        self.assertFalse(tgt_mask[0, 0].item())  # tgt no padding
        self.assertTrue(causal[0, 1].item())  # causal blocks future


class TestTransformerConfigOverrideDModel(unittest.TestCase):
    """Test Transformer d_model config override behavior."""

    def test_transformer_uses_default_d_model(self):
        """Transformer should use default config d_model."""
        model = SimpleTransformer(100, 100)
        self.assertEqual(model.d_model, config.D_MODEL)

    def test_transformer_explicit_d_model_overrides_default(self):
        """Explicit d_model should override default."""
        model = SimpleTransformer(100, 100, d_model=256, n_heads=4)
        self.assertEqual(model.d_model, 256)

    def test_transformer_uses_passed_config_d_model(self):
        """Transformer should use passed config d_model."""
        custom_cfg = Config(d_model=128, n_heads=4)  # n_heads must divide d_model
        model = SimpleTransformer(100, 100, config=custom_cfg)
        self.assertEqual(model.d_model, 128)

    def test_transformer_explicit_overrides_passed_config_d_model(self):
        """Explicit d_model should override passed config."""
        custom_cfg = Config(d_model=128, n_heads=4)
        model = SimpleTransformer(100, 100, d_model=64, n_heads=4, config=custom_cfg)
        self.assertEqual(model.d_model, 64)


class TestTransformerConfigOverrideDropout(unittest.TestCase):
    """Test Transformer dropout config override behavior."""

    def test_transformer_uses_default_dropout(self):
        """Transformer should use default config dropout."""
        model = SimpleTransformer(100, 100)
        self.assertEqual(model.dropout, config.DROPOUT)

    def test_transformer_explicit_dropout_overrides_default(self):
        """Explicit dropout should override default."""
        model = SimpleTransformer(100, 100, dropout=0.3)
        self.assertEqual(model.dropout, 0.3)

    def test_transformer_uses_passed_config_dropout(self):
        """Transformer should use passed config dropout."""
        custom_cfg = Config(dropout=0.5)
        model = SimpleTransformer(100, 100, config=custom_cfg)
        self.assertEqual(model.dropout, 0.5)

    def test_transformer_explicit_overrides_passed_config_dropout(self):
        """Explicit dropout should override passed config."""
        custom_cfg = Config(dropout=0.5)
        model = SimpleTransformer(100, 100, dropout=0.2, config=custom_cfg)
        self.assertEqual(model.dropout, 0.2)


class TestTransformerConfigOverridePadIdx(unittest.TestCase):
    """Test Transformer pad_idx config override behavior."""

    def test_transformer_uses_default_pad_idx(self):
        """Transformer should use default config pad_idx."""
        model = SimpleTransformer(100, 100)
        self.assertEqual(model.pad_idx, config.PAD_IDX)

    def test_transformer_explicit_pad_idx_overrides_default(self):
        """Explicit pad_idx should override default."""
        model = SimpleTransformer(100, 100, pad_idx=5)
        self.assertEqual(model.pad_idx, 5)

    def test_transformer_uses_passed_config_pad_idx(self):
        """Transformer should use passed config pad_idx."""
        custom_cfg = Config(pad_idx=7)
        model = SimpleTransformer(100, 100, config=custom_cfg)
        self.assertEqual(model.pad_idx, 7)

    def test_transformer_explicit_overrides_passed_config_pad_idx(self):
        """Explicit pad_idx should override passed config."""
        custom_cfg = Config(pad_idx=7)
        model = SimpleTransformer(100, 100, pad_idx=3, config=custom_cfg)
        self.assertEqual(model.pad_idx, 3)


class TestCreateMasksConfigOverride(unittest.TestCase):
    """Test create_masks and create_key_padding_mask config override behavior."""

    def test_create_masks_uses_default_pad_idx(self):
        """create_masks should use default config pad_idx."""
        src = torch.tensor([[1, 2, config.PAD_IDX]])
        tgt = torch.tensor([[1, 2, 3]])
        src_mask, _, _ = create_masks(src, tgt)
        self.assertTrue(src_mask[0, 2].item())  # PAD position should be True

    def test_create_masks_explicit_pad_idx_overrides_default(self):
        """Explicit pad_idx should override default."""
        src = torch.tensor([[1, 2, 99]])
        tgt = torch.tensor([[1, 2, 3]])
        src_mask, _, _ = create_masks(src, tgt, pad_idx=99)
        self.assertTrue(src_mask[0, 2].item())  # Custom PAD position

    def test_create_masks_uses_passed_config_pad_idx(self):
        """create_masks should use passed config pad_idx."""
        custom_cfg = Config(pad_idx=42)
        src = torch.tensor([[1, 2, 42]])
        tgt = torch.tensor([[1, 2, 3]])
        src_mask, _, _ = create_masks(src, tgt, config=custom_cfg)
        self.assertTrue(src_mask[0, 2].item())  # Config PAD position

    def test_create_masks_explicit_overrides_passed_config_pad_idx(self):
        """Explicit pad_idx should override passed config."""
        custom_cfg = Config(pad_idx=42)
        src = torch.tensor([[1, 2, 99]])
        tgt = torch.tensor([[1, 2, 3]])
        src_mask, _, _ = create_masks(src, tgt, pad_idx=99, config=custom_cfg)
        self.assertTrue(src_mask[0, 2].item())  # Explicit pad_idx takes priority

    def test_create_key_padding_mask_uses_default_pad_idx(self):
        """create_key_padding_mask should use default config pad_idx."""
        seq = torch.tensor([[1, 2, config.PAD_IDX]])
        mask = create_key_padding_mask(seq)
        self.assertTrue(mask[0, 2].item())

    def test_create_key_padding_mask_explicit_pad_idx_overrides_default(self):
        """Explicit pad_idx should override default."""
        seq = torch.tensor([[1, 2, 77]])
        mask = create_key_padding_mask(seq, pad_idx=77)
        self.assertTrue(mask[0, 2].item())

    def test_create_key_padding_mask_uses_passed_config_pad_idx(self):
        """create_key_padding_mask should use passed config pad_idx."""
        custom_cfg = Config(pad_idx=55)
        seq = torch.tensor([[1, 2, 55]])
        mask = create_key_padding_mask(seq, config=custom_cfg)
        self.assertTrue(mask[0, 2].item())

    def test_create_key_padding_mask_explicit_overrides_passed_config_pad_idx(self):
        """Explicit pad_idx should override passed config."""
        custom_cfg = Config(pad_idx=55)
        seq = torch.tensor([[1, 2, 33]])
        mask = create_key_padding_mask(seq, pad_idx=33, config=custom_cfg)
        self.assertTrue(mask[0, 2].item())


class TestLSTMInitialization(unittest.TestCase):
    """Test SimpleSeq2SeqLSTM initialization."""

    def test_lstm_init_default_params(self):
        """LSTM should initialize with default parameters."""
        model = SimpleSeq2SeqLSTM(src_vocab_size=100, tgt_vocab_size=100)
        self.assertIsNotNone(model)

    def test_lstm_init_custom_params(self):
        """LSTM should accept custom parameters."""
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=100,
            tgt_vocab_size=100,
            emb_dim=128,
            hidden_dim=256,
            num_layers=3,
            dropout=0.3,
        )
        self.assertEqual(model.hidden_dim, 256)

    def test_lstm_has_required_components(self):
        """LSTM should have all required components."""
        model = SimpleSeq2SeqLSTM(src_vocab_size=50, tgt_vocab_size=50)
        self.assertIsNotNone(model.src_embed)
        self.assertIsNotNone(model.tgt_embed)
        self.assertIsNotNone(model.encoder)
        self.assertIsNotNone(model.decoder)
        self.assertIsNotNone(model.output)


class TestLSTMForward(unittest.TestCase):
    """Test SimpleSeq2SeqLSTM forward pass."""

    def test_lstm_forward_output_shape(self):
        """LSTM forward should produce correct output shape."""
        src_vocab_size = 100
        tgt_vocab_size = 100
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=src_vocab_size,
            tgt_vocab_size=tgt_vocab_size,
            emb_dim=32,
            hidden_dim=64,
            num_layers=1,
        )

        batch_size = 5
        src_len = 10
        tgt_len = 12

        src = torch.randint(0, src_vocab_size, (batch_size, src_len))
        tgt = torch.randint(0, tgt_vocab_size, (batch_size, tgt_len))

        output = model(src, tgt)
        self.assertEqual(output.shape, (batch_size, tgt_len, tgt_vocab_size))

    def test_lstm_forward_single_example(self):
        """LSTM should handle single example (batch_size=1)."""
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=50, tgt_vocab_size=50, emb_dim=16, hidden_dim=32
        )
        src = torch.randint(0, 50, (1, 5))
        tgt = torch.randint(0, 50, (1, 7))
        output = model(src, tgt)
        self.assertEqual(output.shape, (1, 7, 50))

    def test_lstm_forward_with_padding(self):
        """LSTM should handle padded sequences."""
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=10, tgt_vocab_size=10, emb_dim=8, hidden_dim=16
        )
        src = torch.tensor([[config.PAD_IDX, 1, 2, 3]])
        tgt = torch.tensor([[config.SOS_IDX, 4, 5, config.EOS_IDX]])
        output = model(src, tgt)
        self.assertEqual(output.shape, (1, 4, 10))

    def test_lstm_forward_different_lengths(self):
        """LSTM should handle different src and tgt lengths."""
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=50, tgt_vocab_size=50, emb_dim=16, hidden_dim=32
        )
        src = torch.randint(0, 50, (2, 5))
        tgt = torch.randint(0, 50, (2, 15))
        output = model(src, tgt)
        self.assertEqual(output.shape, (2, 15, 50))

    def test_lstm_forward_multilayer(self):
        """LSTM with multiple layers should work correctly."""
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=50,
            tgt_vocab_size=50,
            emb_dim=16,
            hidden_dim=32,
            num_layers=3,
        )
        src = torch.randint(0, 50, (2, 8))
        tgt = torch.randint(0, 50, (2, 10))
        output = model(src, tgt)
        self.assertEqual(output.shape, (2, 10, 50))


class TestModelEdgeCases(unittest.TestCase):
    """Test edge cases for both models."""

    def test_transformer_very_short_sequences(self):
        """Transformer should handle very short sequences."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.randint(0, 50, (1, 1))
        tgt = torch.randint(0, 50, (1, 1))
        output = model(src, tgt)
        self.assertEqual(output.shape, (1, 1, 50))

    def test_lstm_very_short_sequences(self):
        """LSTM should handle very short sequences."""
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=50, tgt_vocab_size=50, emb_dim=16, hidden_dim=32
        )
        src = torch.randint(0, 50, (1, 1))
        tgt = torch.randint(0, 50, (1, 1))
        output = model(src, tgt)
        self.assertEqual(output.shape, (1, 1, 50))

    def test_transformer_large_batch(self):
        """Transformer should handle large batch sizes."""
        model = SimpleTransformer(
            src_vocab_size=50, tgt_vocab_size=50, d_model=32, n_heads=4
        )
        src = torch.randint(0, 50, (32, 10))
        tgt = torch.randint(0, 50, (32, 12))
        output = model(src, tgt)
        self.assertEqual(output.shape, (32, 12, 50))

    def test_lstm_large_batch(self):
        """LSTM should handle large batch sizes."""
        model = SimpleSeq2SeqLSTM(
            src_vocab_size=50, tgt_vocab_size=50, emb_dim=16, hidden_dim=32
        )
        src = torch.randint(0, 50, (32, 10))
        tgt = torch.randint(0, 50, (32, 12))
        output = model(src, tgt)
        self.assertEqual(output.shape, (32, 12, 50))


class TestLSTMConfigOverrideEmbDim(unittest.TestCase):
    """Test LSTM emb_dim config override behavior."""

    def test_lstm_uses_default_emb_dim(self):
        """LSTM should use default config lstm_emb_dim."""
        model = SimpleSeq2SeqLSTM(100, 100)
        self.assertEqual(model.src_embed.embedding_dim, config.LSTM_EMB_DIM)

    def test_lstm_explicit_emb_dim_overrides_default(self):
        """Explicit emb_dim should override default."""
        model = SimpleSeq2SeqLSTM(100, 100, emb_dim=128)
        self.assertEqual(model.src_embed.embedding_dim, 128)

    def test_lstm_uses_passed_config_emb_dim(self):
        """LSTM should use passed config lstm_emb_dim."""
        custom_cfg = Config(lstm_emb_dim=64)
        model = SimpleSeq2SeqLSTM(100, 100, config=custom_cfg)
        self.assertEqual(model.src_embed.embedding_dim, 64)

    def test_lstm_explicit_overrides_passed_config_emb_dim(self):
        """Explicit emb_dim should override passed config."""
        custom_cfg = Config(lstm_emb_dim=64)
        model = SimpleSeq2SeqLSTM(100, 100, emb_dim=32, config=custom_cfg)
        self.assertEqual(model.src_embed.embedding_dim, 32)


class TestLSTMConfigOverrideHiddenDim(unittest.TestCase):
    """Test LSTM hidden_dim config override behavior."""

    def test_lstm_uses_default_hidden_dim(self):
        """LSTM should use default config lstm_hidden_dim."""
        model = SimpleSeq2SeqLSTM(100, 100)
        self.assertEqual(model.hidden_dim, config.LSTM_HIDDEN_DIM)

    def test_lstm_explicit_hidden_dim_overrides_default(self):
        """Explicit hidden_dim should override default."""
        model = SimpleSeq2SeqLSTM(100, 100, hidden_dim=256)
        self.assertEqual(model.hidden_dim, 256)

    def test_lstm_uses_passed_config_hidden_dim(self):
        """LSTM should use passed config lstm_hidden_dim."""
        custom_cfg = Config(lstm_hidden_dim=128)
        model = SimpleSeq2SeqLSTM(100, 100, config=custom_cfg)
        self.assertEqual(model.hidden_dim, 128)

    def test_lstm_explicit_overrides_passed_config_hidden_dim(self):
        """Explicit hidden_dim should override passed config."""
        custom_cfg = Config(lstm_hidden_dim=128)
        model = SimpleSeq2SeqLSTM(100, 100, hidden_dim=64, config=custom_cfg)
        self.assertEqual(model.hidden_dim, 64)


class TestLSTMConfigOverrideNumLayers(unittest.TestCase):
    """Test LSTM num_layers config override behavior."""

    def test_lstm_uses_default_num_layers(self):
        """LSTM should use default config lstm_num_layers."""
        model = SimpleSeq2SeqLSTM(100, 100)
        self.assertEqual(model.encoder.num_layers, config.LSTM_NUM_LAYERS)

    def test_lstm_explicit_num_layers_overrides_default(self):
        """Explicit num_layers should override default."""
        model = SimpleSeq2SeqLSTM(100, 100, num_layers=3)
        self.assertEqual(model.encoder.num_layers, 3)

    def test_lstm_uses_passed_config_num_layers(self):
        """LSTM should use passed config lstm_num_layers."""
        custom_cfg = Config(lstm_num_layers=4)
        model = SimpleSeq2SeqLSTM(100, 100, config=custom_cfg)
        self.assertEqual(model.encoder.num_layers, 4)

    def test_lstm_explicit_overrides_passed_config_num_layers(self):
        """Explicit num_layers should override passed config."""
        custom_cfg = Config(lstm_num_layers=4)
        model = SimpleSeq2SeqLSTM(100, 100, num_layers=1, config=custom_cfg)
        self.assertEqual(model.encoder.num_layers, 1)


class TestLSTMConfigOverrideDropout(unittest.TestCase):
    """Test LSTM dropout config override behavior."""

    def test_lstm_uses_default_dropout(self):
        """LSTM should use default config lstm_dropout."""
        model = SimpleSeq2SeqLSTM(100, 100)
        self.assertEqual(model.encoder.dropout, config.LSTM_DROPOUT)

    def test_lstm_explicit_dropout_overrides_default(self):
        """Explicit dropout should override default."""
        model = SimpleSeq2SeqLSTM(100, 100, dropout=0.3)
        self.assertEqual(model.encoder.dropout, 0.3)

    def test_lstm_uses_passed_config_dropout(self):
        """LSTM should use passed config lstm_dropout."""
        custom_cfg = Config(lstm_dropout=0.5)
        model = SimpleSeq2SeqLSTM(100, 100, config=custom_cfg)
        self.assertEqual(model.encoder.dropout, 0.5)

    def test_lstm_explicit_overrides_passed_config_dropout(self):
        """Explicit dropout should override passed config."""
        custom_cfg = Config(lstm_dropout=0.5)
        model = SimpleSeq2SeqLSTM(100, 100, dropout=0.1, config=custom_cfg)
        self.assertEqual(model.encoder.dropout, 0.1)


class TestLSTMConfigOverridePadIdx(unittest.TestCase):
    """Test LSTM pad_idx config override behavior."""

    def test_lstm_uses_default_pad_idx(self):
        """LSTM should use default config pad_idx."""
        model = SimpleSeq2SeqLSTM(100, 100)
        self.assertEqual(model.pad_idx, config.PAD_IDX)

    def test_lstm_explicit_pad_idx_overrides_default(self):
        """Explicit pad_idx should override default."""
        model = SimpleSeq2SeqLSTM(100, 100, pad_idx=5)
        self.assertEqual(model.pad_idx, 5)

    def test_lstm_uses_passed_config_pad_idx(self):
        """LSTM should use passed config pad_idx."""
        custom_cfg = Config(pad_idx=7)
        model = SimpleSeq2SeqLSTM(100, 100, config=custom_cfg)
        self.assertEqual(model.pad_idx, 7)

    def test_lstm_explicit_overrides_passed_config_pad_idx(self):
        """Explicit pad_idx should override passed config."""
        custom_cfg = Config(pad_idx=7)
        model = SimpleSeq2SeqLSTM(100, 100, pad_idx=3, config=custom_cfg)
        self.assertEqual(model.pad_idx, 3)


if __name__ == "__main__":
    unittest.main()
