import tempfile
import unittest
from pathlib import Path

import pandas as pd
import sentencepiece as spm
import torch

from torchlingo.config import Config
from torchlingo.preprocessing.sentencepiece import (
    apply_sentencepiece,
    preprocess_sentencepiece,
    train_sentencepiece,
)
from torchlingo.data_processing.vocab import SentencePieceVocab


def _make_parallel(df_dir: Path, n: int = 12) -> tuple[Path, Path, Path]:
    """Create tiny train/val/test TSVs under df_dir with predictable text."""
    data = {
        "src": [f"hello world {i}" for i in range(n)],
        "tgt": [f"hola mundo {i}" for i in range(n)],
    }
    df = pd.DataFrame(data)
    train = df.iloc[: n // 2]
    val = df.iloc[n // 2 : n // 2 + max(1, n // 4)]
    test = df.iloc[n // 2 + max(1, n // 4) :]
    df_dir.mkdir(parents=True, exist_ok=True)
    train_path = df_dir / "train.tsv"
    val_path = df_dir / "val.tsv"
    test_path = df_dir / "test.tsv"
    train.to_csv(train_path, sep="\t", index=False)
    val.to_csv(val_path, sep="\t", index=False)
    test.to_csv(test_path, sep="\t", index=False)
    return train_path, val_path, test_path


def _example_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "example.tsv"


def _train_dual_models(tmp: Path):
    cfg_src = Config(
        data_dir=tmp,
        sentencepiece_model_prefix=str(tmp / "sp_src"),
        vocab_size=32,
    )
    cfg_tgt = Config(
        data_dir=tmp,
        sentencepiece_model_prefix=str(tmp / "sp_tgt"),
        vocab_size=32,
    )
    train_file, _, _ = _make_parallel(tmp, n=8)
    train_sentencepiece(
        [train_file],
        cfg_src.sentencepiece_model_prefix,
        columns=[cfg_src.src_col],
        config=cfg_src,
    )
    train_sentencepiece(
        [train_file],
        cfg_tgt.sentencepiece_model_prefix,
        columns=[cfg_tgt.tgt_col],
        config=cfg_tgt,
    )
    return cfg_src, cfg_tgt, train_file


class TrainSentencepieceTests(unittest.TestCase):
    def test_creates_model_with_special_ids(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_special"),
                vocab_size=64,
                pad_idx=5,
                unk_idx=6,
                sos_idx=7,
                eos_idx=8,
            )
            train_file, _, _ = _make_parallel(tmp)

            train_sentencepiece(
                [train_file], cfg.sentencepiece_model_prefix, config=cfg
            )

            proc = spm.SentencePieceProcessor()
            proc.load(cfg.sentencepiece_model)
            self.assertEqual(proc.pad_id(), cfg.pad_idx)
            self.assertEqual(proc.unk_id(), cfg.unk_idx)
            self.assertEqual(proc.bos_id(), cfg.sos_idx)
            self.assertEqual(proc.eos_id(), cfg.eos_idx)

    def test_respects_columns_filter(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_cols"),
                vocab_size=24,
            )
            df = pd.DataFrame(
                {
                    "src": ["src_only_token"] * 5,
                    "tgt": ["TGTONLY"] * 5,
                }
            )
            train_path = tmp / "train.tsv"
            df.to_csv(train_path, sep="\t", index=False)

            train_sentencepiece(
                [train_path],
                cfg.sentencepiece_model_prefix,
                columns=[cfg.src_col],
                config=cfg,
            )

            proc = spm.SentencePieceProcessor()
            proc.load(cfg.sentencepiece_model)
            vocab_pieces = {proc.id_to_piece(i) for i in range(proc.get_piece_size())}
            # Ensure the tgt-only string did not get added
            self.assertTrue(all("TGTONLY" not in p for p in vocab_pieces))
            # Encoding the src token should not hit unk
            ids = proc.encode("src_only_token")
            self.assertTrue(all(i != proc.unk_id() for i in ids))

    def test_uses_vocab_size_limit(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_size"),
                vocab_size=32,
            )
            train_file, _, _ = _make_parallel(tmp, n=20)

            train_sentencepiece(
                [train_file], cfg.sentencepiece_model_prefix, config=cfg
            )

            proc = spm.SentencePieceProcessor()
            proc.load(cfg.sentencepiece_model)
            self.assertLessEqual(proc.get_piece_size(), cfg.vocab_size + 4)


class ApplySentencepieceTests(unittest.TestCase):
    def test_writes_tokenized_file(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(data_dir=tmp)
            cfg_src, cfg_tgt, train_file = _train_dual_models(tmp)
            out_path = tmp / "tokenized.tsv"

            apply_sentencepiece(
                train_file,
                out_path,
                cfg_src.sentencepiece_model,
                cfg_tgt.sentencepiece_model,
                config=cfg,
            )

            self.assertTrue(out_path.exists())
            df_tok = pd.read_csv(out_path, sep="\t")
            self.assertEqual(list(df_tok.columns), [cfg.src_col, cfg.tgt_col])
            self.assertTrue(all(" " in s for s in df_tok[cfg.src_col]))
            self.assertTrue(all(" " in s for s in df_tok[cfg.tgt_col]))

    def test_uses_distinct_models(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(data_dir=tmp)
            cfg_src, cfg_tgt, train_file = _train_dual_models(tmp)
            out_path = tmp / "tokenized_dual.tsv"

            apply_sentencepiece(
                train_file,
                out_path,
                cfg_src.sentencepiece_model,
                cfg_tgt.sentencepiece_model,
                config=cfg,
            )

            df_tok = pd.read_csv(out_path, sep="\t")
            self.assertTrue(
                any(a != b for a, b in zip(df_tok[cfg.src_col], df_tok[cfg.tgt_col]))
            )

    def test_accepts_loaded_processors(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(data_dir=tmp)
            cfg_src, cfg_tgt, train_file = _train_dual_models(tmp)
            out_path = tmp / "tokenized_loaded.tsv"

            src_proc = spm.SentencePieceProcessor()
            src_proc.load(cfg_src.sentencepiece_model)
            tgt_proc = spm.SentencePieceProcessor()
            tgt_proc.load(cfg_tgt.sentencepiece_model)

            apply_sentencepiece(train_file, out_path, src_proc, tgt_proc, config=cfg)

            df_tok = pd.read_csv(out_path, sep="\t")
            self.assertGreater(len(df_tok), 0)


class PreprocessSentencepieceTests(unittest.TestCase):
    def test_shared_model_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            train_file, val_file, test_file = _make_parallel(tmp, n=10)
            cfg = Config(data_dir=tmp, vocab_size=32)

            preprocess_sentencepiece(
                train_file=train_file,
                val_file=val_file,
                test_file=test_file,
                config=cfg,
            )

            tokenized_dir = tmp / "tokenized"
            for split in ["train", "val", "test"]:
                tok_file = tokenized_dir / f"{split}.{cfg.data_format}"
                self.assertTrue(tok_file.exists())
                df_tok = pd.read_csv(tok_file, sep="\t")
                self.assertIn(cfg.src_col, df_tok.columns)
                self.assertIn(cfg.tgt_col, df_tok.columns)

            self.assertTrue(Path(cfg.sentencepiece_model).exists())

    def test_separate_models_pipeline(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            train_file, val_file, test_file = _make_parallel(tmp, n=10)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_src_model_prefix=str(tmp / "sp_src_sep"),
                sentencepiece_tgt_model_prefix=str(tmp / "sp_tgt_sep"),
                sentencepiece_src_model=str(tmp / "sp_src_sep.model"),
                sentencepiece_tgt_model=str(tmp / "sp_tgt_sep.model"),
                vocab_size=32,
            )

            preprocess_sentencepiece(
                train_file=train_file,
                val_file=val_file,
                test_file=test_file,
                config=cfg,
            )

            self.assertTrue(Path(cfg.sentencepiece_src_model).exists())
            self.assertTrue(Path(cfg.sentencepiece_tgt_model).exists())
            self.assertNotEqual(
                cfg.sentencepiece_src_model, cfg.sentencepiece_tgt_model
            )

    def test_respects_vocab_size_bound(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            train_file, val_file, test_file = _make_parallel(tmp, n=15)
            cfg = Config(data_dir=tmp, vocab_size=24)

            preprocess_sentencepiece(
                train_file=train_file,
                val_file=val_file,
                test_file=test_file,
                config=cfg,
            )

            proc = spm.SentencePieceProcessor()
            proc.load(cfg.sentencepiece_model)
            self.assertLessEqual(proc.get_piece_size(), cfg.vocab_size + 4)


class SentencePieceVocabDecodeTests(unittest.TestCase):
    def test_decode_preserves_space_count_on_example_subset(self):
        data_path = _example_path()
        self.assertTrue(data_path.exists())

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_example"),
                vocab_size=256,
            )

            train_sentencepiece(
                [data_path],
                cfg.sentencepiece_model_prefix,
                columns=[cfg.src_col, cfg.tgt_col],
                config=cfg,
            )

            vocab = SentencePieceVocab(cfg.sentencepiece_model, config=cfg)
            df = pd.read_csv(data_path, sep="\t")
            samples = list(df[cfg.src_col].head(4)) + list(df[cfg.tgt_col].head(4))

            for text in samples:
                encoded = vocab.encode(text)
                decoded = vocab.decode(encoded)
                self.assertIsInstance(decoded, str)
                self.assertEqual(decoded.count(" "), text.count(" "))

    def test_decode_single_sequence(self):
        data_path = _example_path()
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_single"),
                vocab_size=256,
            )

            train_sentencepiece(
                [data_path],
                cfg.sentencepiece_model_prefix,
                columns=[cfg.src_col],
                config=cfg,
            )

            vocab = SentencePieceVocab(cfg.sentencepiece_model, config=cfg)
            df = pd.read_csv(data_path, sep="\t")
            text = df[cfg.src_col].iloc[0]
            encoded = vocab.encode(text)
            decoded = vocab.decode(encoded)

            self.assertIsInstance(decoded, str)
            self.assertEqual(decoded.count(" "), text.count(" "))

    def test_decode_batch_as_list_of_lists(self):
        data_path = _example_path()
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_batch_list"),
                vocab_size=256,
            )

            train_sentencepiece(
                [data_path],
                cfg.sentencepiece_model_prefix,
                columns=[cfg.src_col],
                config=cfg,
            )

            vocab = SentencePieceVocab(cfg.sentencepiece_model, config=cfg)
            df = pd.read_csv(data_path, sep="\t")
            texts = list(df[cfg.src_col].head(3))
            batch_encoded = [vocab.encode(text) for text in texts]
            batch_decoded = vocab.decode(batch_encoded)

            self.assertIsInstance(batch_decoded, list)
            self.assertEqual(len(batch_decoded), len(texts))
            for decoded, original in zip(batch_decoded, texts):
                self.assertIsInstance(decoded, str)
                self.assertEqual(decoded.count(" "), original.count(" "))

    def test_decode_batch_as_2d_tensor(self):
        data_path = _example_path()
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_batch_tensor"),
                vocab_size=256,
            )

            train_sentencepiece(
                [data_path],
                cfg.sentencepiece_model_prefix,
                columns=[cfg.src_col],
                config=cfg,
            )

            vocab = SentencePieceVocab(cfg.sentencepiece_model, config=cfg)
            df = pd.read_csv(data_path, sep="\t")
            texts = list(df[cfg.src_col].head(3))
            batch_encoded = [vocab.encode(text) for text in texts]

            max_len = max(len(seq) for seq in batch_encoded)
            padded = []
            for seq in batch_encoded:
                padded.append(seq + [cfg.pad_idx] * (max_len - len(seq)))
            batch_tensor = torch.tensor(padded, dtype=torch.long)

            batch_decoded = vocab.decode(batch_tensor)

            self.assertIsInstance(batch_decoded, list)
            self.assertEqual(len(batch_decoded), len(texts))
            for decoded, original in zip(batch_decoded, texts):
                self.assertIsInstance(decoded, str)
                self.assertEqual(decoded.count(" "), original.count(" "))

    def test_decode_1d_tensor(self):
        data_path = _example_path()
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            cfg = Config(
                data_dir=tmp,
                sentencepiece_model_prefix=str(tmp / "sp_1d_tensor"),
                vocab_size=256,
            )

            train_sentencepiece(
                [data_path],
                cfg.sentencepiece_model_prefix,
                columns=[cfg.src_col],
                config=cfg,
            )

            vocab = SentencePieceVocab(cfg.sentencepiece_model, config=cfg)
            df = pd.read_csv(data_path, sep="\t")
            text = df[cfg.src_col].iloc[0]
            encoded = vocab.encode(text)
            tensor_1d = torch.tensor(encoded, dtype=torch.long)

            decoded = vocab.decode(tensor_1d)

            self.assertIsInstance(decoded, str)
            self.assertEqual(decoded.count(" "), text.count(" "))


if __name__ == "__main__":
    unittest.main()
