import unittest
import torch
from torchlingo import config
from torchlingo.config import Config
from torchlingo.models.positional import RotaryPositionalEmbedding, RoPEEmbedding


class TestRotaryPositionalEmbedding(unittest.TestCase):
    """Tests for RotaryPositionalEmbedding."""

    def test_init_and_cached_len(self):
        rope = RotaryPositionalEmbedding(dim=8, max_seq_len=16)
        self.assertEqual(rope.dim, 8)
        self.assertEqual(rope.max_seq_len, 16)
        self.assertEqual(rope.cached_seq_len, 16)
        self.assertTrue(hasattr(rope, "inv_freq"))

    def test_build_cache_extends(self):
        rope = RotaryPositionalEmbedding(dim=8, max_seq_len=8)
        q = torch.randn(2, 4, 8)  # (batch, seq, dim)
        k = torch.randn(2, 4, 8)
        _ = rope(q, k)
        # Extend cache when sequence length grows
        q2 = torch.randn(2, 16, 8)
        k2 = torch.randn(2, 16, 8)
        _ = rope(q2, k2)
        self.assertGreaterEqual(rope.cached_seq_len, 16)

    def test_apply_rotary_pos_emb_shapes(self):
        rope = RotaryPositionalEmbedding(dim=8, max_seq_len=32)
        q = torch.randn(3, 5, 8)  # (batch, seq, dim)
        k = torch.randn(3, 5, 8)
        q_rot, k_rot = rope(q, k)
        self.assertEqual(q_rot.shape, q.shape)
        self.assertEqual(k_rot.shape, k.shape)

    def test_apply_rotary_pos_emb_multihead_shape(self):
        rope = RotaryPositionalEmbedding(dim=8, max_seq_len=32)
        q = torch.randn(2, 4, 3, 8)  # (batch, seq, heads, dim)
        k = torch.randn(2, 4, 3, 8)
        q_rot, k_rot = rope(q, k)
        self.assertEqual(q_rot.shape, q.shape)
        self.assertEqual(k_rot.shape, k.shape)


class TestRoPEEmbedding(unittest.TestCase):
    """Tests for RoPEEmbedding wrapper."""

    def test_forward_preserves_shape(self):
        rope_emb = RoPEEmbedding(d_model=12, max_seq_len=32)
        x = torch.randn(2, 5, 12)
        y = rope_emb(x)
        self.assertEqual(y.shape, x.shape)

    def test_forward_rotates_first_even_dims(self):
        # With d_model=10 -> first 10 dims rotate (since rotary splits in half twice)
        d_model = 10
        rope_emb = RoPEEmbedding(d_model=d_model, max_seq_len=16)
        x = torch.ones(1, 4, d_model)
        y = rope_emb(x)
        # Values should change in first rotated part, but trailing remainder preserved
        self.assertFalse(
            torch.allclose(y[..., : (d_model // 2) * 2], x[..., : (d_model // 2) * 2])
        )
        if d_model % 2 != 0:
            self.assertTrue(
                torch.allclose(
                    y[..., (d_model // 2) * 2 :], x[..., (d_model // 2) * 2 :]
                )
            )


class TestRotaryPositionalEmbeddingConfigOverride(unittest.TestCase):
    """Tests for RotaryPositionalEmbedding config override behavior."""

    def test_rotary_uses_default_dim(self):
        """RotaryPositionalEmbedding should use default config d_model for dim."""
        rope = RotaryPositionalEmbedding()
        self.assertEqual(rope.dim, config.D_MODEL)

    def test_rotary_explicit_dim_overrides_default(self):
        """Explicit dim should override default."""
        rope = RotaryPositionalEmbedding(dim=128)
        self.assertEqual(rope.dim, 128)

    def test_rotary_uses_passed_config_dim(self):
        """RotaryPositionalEmbedding should use passed config d_model for dim."""
        custom_cfg = Config(d_model=256, n_heads=8)
        rope = RotaryPositionalEmbedding(config=custom_cfg)
        self.assertEqual(rope.dim, 256)

    def test_rotary_explicit_dim_overrides_passed_config(self):
        """Explicit dim should override passed config."""
        custom_cfg = Config(d_model=256, n_heads=8)
        rope = RotaryPositionalEmbedding(dim=64, config=custom_cfg)
        self.assertEqual(rope.dim, 64)

    def test_rotary_uses_default_max_seq_len(self):
        """RotaryPositionalEmbedding should use default config max_seq_length."""
        rope = RotaryPositionalEmbedding()
        self.assertEqual(rope.max_seq_len, config.MAX_SEQ_LENGTH)

    def test_rotary_explicit_max_seq_len_overrides_default(self):
        """Explicit max_seq_len should override default."""
        rope = RotaryPositionalEmbedding(max_seq_len=1024)
        self.assertEqual(rope.max_seq_len, 1024)

    def test_rotary_uses_passed_config_max_seq_len(self):
        """RotaryPositionalEmbedding should use passed config max_seq_length."""
        custom_cfg = Config(d_model=256, n_heads=8, max_seq_length=2048)
        rope = RotaryPositionalEmbedding(config=custom_cfg)
        self.assertEqual(rope.max_seq_len, 2048)

    def test_rotary_explicit_max_seq_len_overrides_passed_config(self):
        """Explicit max_seq_len should override passed config."""
        custom_cfg = Config(d_model=256, n_heads=8, max_seq_length=2048)
        rope = RotaryPositionalEmbedding(max_seq_len=128, config=custom_cfg)
        self.assertEqual(rope.max_seq_len, 128)


class TestRoPEEmbeddingConfigOverride(unittest.TestCase):
    """Tests for RoPEEmbedding config override behavior."""

    def test_rope_uses_default_d_model(self):
        """RoPEEmbedding should use default config d_model."""
        rope = RoPEEmbedding()
        self.assertEqual(rope.d_model, config.D_MODEL)

    def test_rope_explicit_d_model_overrides_default(self):
        """Explicit d_model should override default."""
        rope = RoPEEmbedding(d_model=128)
        self.assertEqual(rope.d_model, 128)

    def test_rope_uses_passed_config_d_model(self):
        """RoPEEmbedding should use passed config d_model."""
        custom_cfg = Config(d_model=256, n_heads=8)
        rope = RoPEEmbedding(config=custom_cfg)
        self.assertEqual(rope.d_model, 256)

    def test_rope_explicit_d_model_overrides_passed_config(self):
        """Explicit d_model should override passed config."""
        custom_cfg = Config(d_model=256, n_heads=8)
        rope = RoPEEmbedding(d_model=64, config=custom_cfg)
        self.assertEqual(rope.d_model, 64)

    def test_rope_uses_default_max_seq_len(self):
        """RoPEEmbedding should use default config max_seq_length."""
        rope = RoPEEmbedding()
        self.assertEqual(rope.max_seq_len, config.MAX_SEQ_LENGTH)

    def test_rope_explicit_max_seq_len_overrides_default(self):
        """Explicit max_seq_len should override default."""
        rope = RoPEEmbedding(max_seq_len=1024)
        self.assertEqual(rope.max_seq_len, 1024)

    def test_rope_uses_passed_config_max_seq_len(self):
        """RoPEEmbedding should use passed config max_seq_length."""
        custom_cfg = Config(d_model=256, n_heads=8, max_seq_length=2048)
        rope = RoPEEmbedding(config=custom_cfg)
        self.assertEqual(rope.max_seq_len, 2048)

    def test_rope_explicit_max_seq_len_overrides_passed_config(self):
        """Explicit max_seq_len should override passed config."""
        custom_cfg = Config(d_model=256, n_heads=8, max_seq_length=2048)
        rope = RoPEEmbedding(max_seq_len=128, config=custom_cfg)
        self.assertEqual(rope.max_seq_len, 128)


if __name__ == "__main__":
    unittest.main()
