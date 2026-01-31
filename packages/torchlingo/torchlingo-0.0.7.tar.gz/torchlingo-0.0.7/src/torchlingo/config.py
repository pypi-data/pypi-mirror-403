"""Project configuration for TorchLingo

This file provides a Config class for managing hyperparameters, paths, and
feature toggles. You can instantiate multiple configs for different experiments
and pass them to various functions.

Quick Start:
  # Default config
  from torchlingo.config import get_default_config
  cfg = get_default_config()

  # Custom config
  cfg = Config(batch_size=32, learning_rate=1e-5)

  # Change values on the fly
  cfg.batch_size = 128

Module-level constants are also available:
  from torchlingo import config
  print(config.BATCH_SIZE, config.LEARNING_RATE)
"""

import torch
from pathlib import Path
from copy import deepcopy
from typing import Optional, Dict, Any

# ============================================================================
# BASE DIRECTORIES
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
# BASE_DIR: Path — root directory of the project, derived from this file's location

DATA_DIR = BASE_DIR / "data"
# DATA_DIR: Path — directory where all data files (raw, processed, vocab) are stored

CHECKPOINT_DIR = BASE_DIR / "checkpoints"
# CHECKPOINT_DIR: Path — where trained model checkpoints are saved

OUTPUT_DIR = BASE_DIR / "outputs"
# OUTPUT_DIR: Path — where translation outputs and results are written

# Create directories if they don't exist (safe no-op if present)
DATA_DIR.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================================
# DATA AND FILE SETTINGS
# ============================================================================

DATA_FORMAT = "tsv"
# DATA_FORMAT: str
#   - Supported values: "tsv", "csv", "parquet", "json"
#   - Default: "tsv"
#   - Description: File format for train/val/test data files. Each file must
#     contain two columns: SRC_COL (source language) and TGT_COL (target language).
#     The suffix will be appended to train/val/test filenames automatically.

SRC_COL = "src"
# SRC_COL: str
#   - Type: str (column name)
#   - Default: "src"
#   - Description: Name of the column containing source language sentences in
#     the data files (e.g., English in an En->Spanish translation task).

TGT_COL = "tgt"
# TGT_COL: str
#   - Type: str (column name)
#   - Default: "tgt"
#   - Description: Name of the column containing target language sentences in
#     the data files (e.g., Spanish in an En->Spanish translation task).

SRC_TOK_COL = "src_tokenized"
# SRC_TOK_COL: str
#   - Type: str (column name)
#   - Default: "src_tokenized"
#   - Description: Name of the optional column containing pre-tokenized source

TGT_TOK_COL = "tgt_tokenized"
# TGT_TOK_COL: str
#   - Type: str (column name)
#   - Default: "tgt_tokenized"
#   - Description: Name of the optional column containing pre-tokenized target

TRAIN_FILE = DATA_DIR / f"train.{DATA_FORMAT}"
# TRAIN_FILE: Path
#   - Type: Path object
#   - Description: Path to the training data file. Used by train.py and dataset.py.
#     The file must exist before training and should contain parallel source/target pairs.

VAL_FILE = DATA_DIR / f"val.{DATA_FORMAT}"
# VAL_FILE: Path
#   - Type: Path object
#   - Description: Path to the validation data file. Used for model selection
#     during training (computed every VAL_INTERVAL steps).

TEST_FILE = DATA_DIR / f"test.{DATA_FORMAT}"
# TEST_FILE: Path
#   - Type: Path object
#   - Description: Path to the test data file (held-out set). Used for final
#     evaluation after training completes.

RAW_DATA_FILE = DATA_DIR / "raw_data.txt"
# RAW_DATA_FILE: Path
#   - Type: Path object
#   - Default: data/raw_data.txt
#   - Description: Path used for raw, unprocessed parallel data when needed.
#     Prefer using structured CSV/TSV/Parquet/JSON files with `src` and `tgt`
#     columns or passing explicit parallel files (src,tgt) to `load_data`.
#     Historically single-file pipe-separated (|||) format was supported but
#     this is deprecated in favor of explicit CSV/TSV files or two-file inputs.

# ============================================================================
# TOKENIZATION AND VOCABULARY SETTINGS
# ============================================================================

USE_SENTENCEPIECE = False
# USE_SENTENCEPIECE: bool
#   - Type: bool
#   - Default: False
#   - Choices: True or False
#   - Description: When True, use SentencePiece subword tokenization (BPE/Unigram)
#     instead of simple whitespace tokenization. Requires a trained .model file.
#     See https://github.com/google/sentencepiece for details.

SENTENCEPIECE_MODEL_PREFIX = str(DATA_DIR / "sp_model")
# SENTENCEPIECE_MODEL_PREFIX: str
#   - Type: str (path prefix)
#   - Default: "data/sp_model"
#   - Description: Prefix for SentencePiece model files. Training will create
#     <PREFIX>.model and <PREFIX>.vocab. Only used if USE_SENTENCEPIECE=True.

SENTENCEPIECE_MODEL = SENTENCEPIECE_MODEL_PREFIX + ".model"
# SENTENCEPIECE_MODEL: str
#   - Type: str (file path)
#   - Description: Full path to the trained SentencePiece .model file.
#     Auto-derived from SENTENCEPIECE_MODEL_PREFIX.

SENTENCEPIECE_VOCAB = SENTENCEPIECE_MODEL_PREFIX + ".vocab"
# SENTENCEPIECE_VOCAB: str
#   - Type: str (file path)
#   - Description: Full path to the SentencePiece .vocab file (human-readable vocab list).
#     Auto-derived from SENTENCEPIECE_MODEL_PREFIX.

# Optional distinct SentencePiece models for src/tgt (default: shared prefix)
SENTENCEPIECE_SRC_MODEL_PREFIX = SENTENCEPIECE_MODEL_PREFIX
SENTENCEPIECE_TGT_MODEL_PREFIX = SENTENCEPIECE_MODEL_PREFIX
SENTENCEPIECE_SRC_MODEL = SENTENCEPIECE_SRC_MODEL_PREFIX + ".model"
SENTENCEPIECE_TGT_MODEL = SENTENCEPIECE_TGT_MODEL_PREFIX + ".model"
SENTENCEPIECE_SRC_VOCAB = SENTENCEPIECE_SRC_MODEL_PREFIX + ".vocab"
SENTENCEPIECE_TGT_VOCAB = SENTENCEPIECE_TGT_MODEL_PREFIX + ".vocab"

VOCAB_SIZE = 32000
# VOCAB_SIZE: int
#   - Type: int (positive)
#   - Range: typically 4000–50000 for SentencePiece
#   - Default: 32000
#   - Description: Target vocabulary size when training a SentencePiece model.
#     Ignored if USE_SENTENCEPIECE=False.

MIN_FREQ = 2
# MIN_FREQ: int
#   - Type: int (positive)
#   - Typical values: 1, 2, 3, 5
#   - Default: 2
#   - Description: Minimum frequency threshold for including tokens in vocabulary.
#     Tokens appearing fewer than min_freq times are mapped to the UNK token index.

SP_MODEL_TYPE = "bpe"
# SP_MODEL_TYPE: str
#   - Type: str
#   - Choices: "bpe", "unigram", "char", "word"
#   - Default: "bpe"
#   - Description: Algorithm for SentencePiece training.
#     "bpe" = Byte-Pair Encoding (recommended for most cases).
#     "unigram" = Unigram LM (best for some CJK languages).
#     "char", "word" = character/word-level tokenization.
#     See https://github.com/google/sentencepiece

SP_CHARACTER_COVERAGE = 1.0
# SP_CHARACTER_COVERAGE: float
#   - Type: float in (0.0, 1.0]
#   - Range: (0.0, 1.0]
#   - Default: 1.0
#   - Description: Fraction of characters in the input to be covered by the model.
#     1.0 = cover all characters (no unknown chars in vocab).
#     0.9999 = allow rare chars to be encoded as <unk>.
#     See SentencePiece docs: https://github.com/google/sentencepiece

SP_NORMALIZATION_RULE_NAME = "nmt_nfkc"
# SP_NORMALIZATION_RULE_NAME: str
#   - Type: str
#   - Choices: "nmt_nfkc", "identity", "nfc", "nfkc", "nfd", "nfkd"
#   - Default: "nmt_nfkc"
#   - Description: Unicode normalization rule applied during SentencePiece training/inference.
#     "nmt_nfkc" is standard for NMT. See SentencePiece documentation for details.

# ============================================================================
# BACK-TRANSLATION AND MULTILINGUAL SETTINGS (ADVANCED)
# ============================================================================

BACK_TRANS_SRC = DATA_DIR / "train.back_trans.en"
# BACK_TRANS_SRC: Path
#   - Type: Path object
#   - Description: Path to source language sentences generated via back-translation
#    .

BACK_TRANS_TGT = DATA_DIR / "train.back_trans.x"
# BACK_TRANS_TGT: Path
#   - Type: Path object
#   - Description: Path to target language (original) sentences for back-translation data.

COMBINED_TRAIN_SRC = DATA_DIR / "train.combined.en"
# COMBINED_TRAIN_SRC: Path
#   - Type: Path object
#   - Description: Path to combined training data (original + back-translated).

COMBINED_TRAIN_TGT = DATA_DIR / "train.combined.x"
# COMBINED_TRAIN_TGT: Path
#   - Type: Path object
#   - Description: Path to combined training targets.

REVERSE_MODEL_CHECKPOINT = CHECKPOINT_DIR / "reverse_model_best.pt"
# REVERSE_MODEL_CHECKPOINT: Path
#   - Type: Path object
#   - Description: Path to checkpoint of the reverse model (X->En) used for back-translation.
#

MULTI_TRAIN_FILE = DATA_DIR / f"train.multi.{DATA_FORMAT}"
# MULTI_TRAIN_FILE: Path
#   - Type: Path object
#   - Description: Path to multilingual training data.

MULTI_VAL_FILE = DATA_DIR / f"val.multi.{DATA_FORMAT}"
# MULTI_VAL_FILE: Path
#   - Type: Path object
#   - Description: Path to multilingual validation data.

TEST_EN_X_FILE = DATA_DIR / f"test.en-x.{DATA_FORMAT}"
# TEST_EN_X_FILE: Path
#   - Type: Path object
#   - Description: Test set for En->X direction.

TEST_X_EN_FILE = DATA_DIR / f"test.x-en.{DATA_FORMAT}"
# TEST_X_EN_FILE: Path
#   - Type: Path object
#   - Description: Test set for X->En direction.

LANG_TAG_EN_TO_X = "<2X>"
# LANG_TAG_EN_TO_X: str
#   - Type: str
#   - Default: "<2X>"
#   - Description: Special token prepended to source for En->X direction in
#     multilingual models. Indicates "translate to X".

LANG_TAG_X_TO_EN = "<2E>"
# LANG_TAG_X_TO_EN: str
#   - Type: str
#   - Default: "<2E>"
#   - Description: Special token prepended to source for X->En direction in
#     multilingual models. Indicates "translate to English".

# ============================================================================
# MODEL ARCHITECTURE HYPERPARAMETERS
# ============================================================================

D_MODEL = 512
# D_MODEL: int
#   - Type: int (positive)
#   - Typical values: 128, 256, 512, 768, 1024
#   - Default: 512
#   - Description: Embedding dimension and internal representation size of the
#     Transformer model. Larger values increase model capacity but require more
#     memory. Must be divisible by N_HEADS.

N_HEADS = 8
# N_HEADS: int
#   - Type: int (positive)
#   - Typical values: 4, 8, 12, 16
#   - Default: 8
#   - Constraint: D_MODEL % N_HEADS == 0 (must divide evenly)
#   - Description: Number of attention heads in multi-head attention.
#     Each head operates on D_MODEL / N_HEADS dimensional subspaces.
#     See https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html

NUM_ENCODER_LAYERS = 6
# NUM_ENCODER_LAYERS: int
#   - Type: int (positive)
#   - Typical values: 2, 4, 6, 12
#   - Default: 6
#   - Description: Number of encoder layers (Transformer blocks) in the encoder stack.
#     Deeper models can capture more complex patterns but are slower to train.

NUM_DECODER_LAYERS = 6
# NUM_DECODER_LAYERS: int
#   - Type: int (positive)
#   - Typical values: 2, 4, 6, 12
#   - Default: 6
#   - Description: Number of decoder layers (Transformer blocks) in the decoder stack.
#     Usually kept equal to NUM_ENCODER_LAYERS for balanced architectures.

D_FF = 2048
# D_FF: int
#   - Type: int (positive)
#   - Typical values: 512, 1024, 2048, 4096
#   - Default: 2048
#   - Description: Hidden dimension of the feedforward (MLP) layers within
#     each Transformer block. Usually 4x D_MODEL. See
#     https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html

DROPOUT = 0.1
# DROPOUT: float
#   - Type: float in [0.0, 1.0)
#   - Range: [0.0, 1.0) — 0.0 = no dropout, >0.9 is very aggressive
#   - Default: 0.1
#   - Description: Dropout probability applied throughout the model (embeddings,
#     feedforward, attention). Higher values increase regularization but can slow
#     convergence. See https://docs.pytorch.org/docs/stable/generated/torch.nn.Dropout.html

MAX_SEQ_LENGTH = 512
# MAX_SEQ_LENGTH: int
#   - Type: int (positive)
#   - Typical values: 128, 256, 512, 1024
#   - Default: 512
#   - Description: Maximum sequence length supported by position encodings
#     (Rotary Embeddings in this codebase). Sequences longer than this will be
#     truncated. Increase for longer documents, decrease for faster training.

# ============================================================================
# LSTM MODEL HYPERPARAMETERS
# ============================================================================

LSTM_EMB_DIM = 256
# LSTM_EMB_DIM: int
#   - Type: int (positive)
#   - Typical values: 128, 256, 512
#   - Default: 256
#   - Description: Embedding dimension for LSTM models.

LSTM_HIDDEN_DIM = 512
# LSTM_HIDDEN_DIM: int
#   - Type: int (positive)
#   - Typical values: 256, 512, 1024
#   - Default: 512
#   - Description: Hidden dimension for LSTM layers.

LSTM_NUM_LAYERS = 2
# LSTM_NUM_LAYERS: int
#   - Type: int (positive)
#   - Typical values: 1, 2, 3, 4
#   - Default: 2
#   - Description: Number of LSTM layers in encoder and decoder.

LSTM_DROPOUT = 0.2
# LSTM_DROPOUT: float
#   - Type: float in [0.0, 1.0)
#   - Typical values: 0.1, 0.2, 0.3
#   - Default: 0.2
#   - Description: Dropout rate for LSTM models.

# ============================================================================
# PERFORMANCE AND EXPERIMENTAL TOGGLES (ADVANCED)
# ============================================================================

USE_PACKED_PROJECTION = False
# USE_PACKED_PROJECTION: bool
#   - Type: bool
#   - Choices: True or False
#   - Default: False
#   - Description: Internal optimization flag. When True, pack the Query/Key/Value
#     projections in self-attention into a single Linear layer (faster but less
#     flexible). Implementation-specific; may not be used depending on model code.

USE_SCALED_DOT_PRODUCT_ATTENTION = False
# USE_SCALED_DOT_PRODUCT_ATTENTION: bool
#   - Type: bool
#   - Choices: True or False
#   - Default: False
#   - Description: When True, use torch.nn.functional.scaled_dot_product_attention
#     (PyTorch 2.0+) instead of manual attention. Can be faster due to kernel fusion.
#     Requires PyTorch >= 2.0. See https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html

TIE_EMBEDDINGS = False
# TIE_EMBEDDINGS: bool
#   - Type: bool
#   - Choices: True or False
#   - Default: False
#   - Description: When True, the decoder's embedding matrix is shared with the
#     output projection matrix (reduces parameters). Only beneficial if
#     src_vocab_size == tgt_vocab_size.

USE_COMPILE = False
# USE_COMPILE: bool
#   - Type: bool
#   - Choices: True or False
#   - Default: False
#   - Description: When True, wrap the model with torch.compile() for JIT compilation
#     (PyTorch 2.0+ only). Can provide 20-50% speedup but requires PyTorch 2.0+.
#     See https://docs.pytorch.org/docs/stable/generated/torch.compile.html

# ============================================================================
# SPECIAL TOKENS AND INDICES
# ============================================================================
# NOTE: These are used throughout the codebase and in tests. Changing them
# without updating the entire codebase will break the system.

PAD_TOKEN = "<pad>"
# PAD_TOKEN: str
#   - Type: str (token string)
#   - Default: "<pad>"
#   - Description: String representation of the padding token. Used to pad
#     sequences to the same length in batches.

UNK_TOKEN = "<unk>"
# UNK_TOKEN: str
#   - Type: str (token string)
#   - Default: "<unk>"
#   - Description: String representation of the unknown/out-of-vocabulary token.
#     Assigned to words not in the vocabulary.

SOS_TOKEN = "<sos>"
# SOS_TOKEN: str
#   - Type: str (token string)
#   - Default: "<sos>"
#   - Description: Start-of-Sequence token. Prepended to target sequences during
#     training and decoding to signal the beginning of a sentence.

EOS_TOKEN = "<eos>"
# EOS_TOKEN: str
#   - Type: str (token string)
#   - Default: "<eos>"
#   - Description: End-of-Sequence token. Appended to sequences to signal the
#     end of a sentence. Decoding stops when this token is generated.

PAD_IDX = 0
# PAD_IDX: int
#   - Type: int (non-negative)
#   - Default: 0
#   - Description: Numeric index for the padding token. Used internally by the
#     model and loss function (e.g., ignore_index in CrossEntropyLoss).

UNK_IDX = 1
# UNK_IDX: int
#   - Type: int (non-negative)
#   - Default: 1
#   - Description: Numeric index for the unknown token.

SOS_IDX = 2
# SOS_IDX: int
#   - Type: int (non-negative)
#   - Default: 2
#   - Description: Numeric index for the start-of-sequence token.

EOS_IDX = 3
# EOS_IDX: int
#   - Type: int (non-negative)
#   - Default: 3
#   - Description: Numeric index for the end-of-sequence token.

# ============================================================================
# TRAINING HYPERPARAMETERS
# ============================================================================

BATCH_SIZE = 64
# BATCH_SIZE: int
#   - Type: int (positive)
#   - Typical values: 16, 32, 64, 128, 256
#   - Default: 64
#   - Description: Number of examples per training batch. Larger batches update
#     parameters less frequently but use more memory. Smaller batches update more
#     often but can be noisier. Adjust based on GPU memory availability.

NUM_STEPS = 100000
# NUM_STEPS: int
#   - Type: int (positive)
#   - Typical values: 10000, 50000, 100000, 500000
#   - Default: 100000
#   - Description: Total number of training steps (gradient updates). One step
#     corresponds to one batch. Can be used by learning rate schedulers and
#     early stopping logic.

LEARNING_RATE = 0.0001
# LEARNING_RATE: float
#   - Type: float (positive)
#   - Typical range: 1e-5 to 1e-3
#   - Default: 1e-4 (0.0001)
#   - Description: Initial learning rate for the Adam optimizer. Standard
#     Transformer baseline uses ~1e-4. Too high causes instability; too low
#     causes slow convergence.

ADAM_BETAS = (0.9, 0.98)
# ADAM_BETAS: tuple of two floats
#   - Type: (float, float)
#   - Range: both in [0.0, 1.0)
#   - Default: (0.9, 0.98)
#   - Description: (beta1, beta2) momentum coefficients for the Adam optimizer.
#     See https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html
#     beta1 (default 0.9) = exponential decay rate for 1st moment.
#     beta2 (default 0.999) = exponential decay rate for 2nd moment.

ADAM_EPS = 1e-9
# ADAM_EPS: float
#   - Type: float (small positive)
#   - Typical range: 1e-8 to 1e-10
#   - Default: 1e-9
#   - Description: Small constant added to the denominator in Adam to avoid
#     division by zero. See https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html

WARMUP_STEPS = 4000
# WARMUP_STEPS: int
#   - Type: int (non-negative)
#   - Typical values: 0, 1000, 4000, 10000
#   - Default: 4000
#   - Description: Number of steps for learning rate warmup schedule. Learning
#     rate increases linearly from 0 to LEARNING_RATE over WARMUP_STEPS, then
#     decays. Set to 0 to disable warmup.

LABEL_SMOOTHING = 0.1
# LABEL_SMOOTHING: float
#   - Type: float in [0.0, 1.0)
#   - Range: [0.0, 1.0) — 0.0 = no smoothing, 0.1-0.2 typical for NMT
#   - Default: 0.1
#   - Description: Label smoothing hyperparameter for cross-entropy loss.
#     Prevents the model from becoming overconfident. See
#     https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html

USE_BUCKETING = False
# USE_BUCKETING: bool
#   - Type: bool
#   - Choices: True or False
#   - Default: False
#   - Description: When True, group examples by length into buckets to reduce
#     padding overhead during training. Requires a custom sampler implementation.

BUCKET_BOUNDARIES = None
# BUCKET_BOUNDARIES: None or list of ints
#   - Type: None or list of ints (sorted, increasing)
#   - Example: [10, 20, 30, 50, 100, 150]
#   - Default: None (auto-calculate from data)
#   - Description: Length boundaries for bucketing. Only used if USE_BUCKETING=True.

GRAD_CLIP = 1.0
# GRAD_CLIP: float
#   - Type: float (non-negative)
#   - Typical values: 0.5, 1.0, 5.0, or 0/None for disabled
#   - Default: 1.0
#   - Description: Max norm for gradient clipping. Prevents exploding gradients.
#     Applied via torch.nn.utils.clip_grad_norm_. Set to 0 or None to disable.
#     See https://docs.pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad.clip_grad_norm_.html

VAL_INTERVAL = 1000
# VAL_INTERVAL: int
#   - Type: int (positive)
#   - Typical values: 100, 500, 1000, 5000
#   - Default: 1000
#   - Description: Number of training steps between validation evaluations.
#     Validation loss is computed on VAL_FILE every VAL_INTERVAL steps.

SAVE_INTERVAL = 5000
# SAVE_INTERVAL: int
#   - Type: int (positive)
#   - Typical values: 1000, 5000, 10000
#   - Default: 5000
#   - Description: Number of training steps between checkpoint saves.
#     Model checkpoints are saved every SAVE_INTERVAL steps.

LOG_INTERVAL = 100
# LOG_INTERVAL: int
#   - Type: int (positive)
#   - Typical values: 10, 100, 1000
#   - Default: 100
#   - Description: Number of training steps between logging of training metrics
#     (e.g., loss, perplexity). Logged to console and TensorBoard if enabled.

PATIENCE = 10
# PATIENCE: int
#   - Type: int (positive)
#   - Typical values: 3, 5, 10, 20
#   - Default: 10
#   - Description: Number of validation intervals (each VAL_INTERVAL steps) to
#     wait for validation loss improvement before early stopping. Set to a large
#     number to effectively disable early stopping.

CHECKPOINT_PATH = CHECKPOINT_DIR / "model_best.pt"
# CHECKPOINT_PATH: Path
#   - Type: Path object
#   - Description: Path to save the best model checkpoint (lowest validation loss).

LAST_CHECKPOINT_PATH = CHECKPOINT_DIR / "model_last.pt"
# LAST_CHECKPOINT_PATH: Path
#   - Type: Path object
#   - Description: Path to save the most recent model checkpoint (for resuming training).

STEP_LIMIT = None
# STEP_LIMIT: Optional[int]
#   - Type: int or None
#   - Default: None
#   - Description: Global maximum number of training steps to run across all
#     epochs. If set, training stops when this many optimizer steps have been
#     performed. Useful for quick experiments or CI runs.

# ============================================================================
# DECODING AND INFERENCE SETTINGS
# ============================================================================

BEAM_SIZE = 5
# BEAM_SIZE: int
#   - Type: int (positive)
#   - Typical values: 1, 3, 5, 10
#   - Default: 5
#   - Description: Beam width for beam search decoding. Larger values explore
#     more hypotheses (better quality but slower). Set to 1 for greedy decoding.

MAX_DECODE_LENGTH = 200
# MAX_DECODE_LENGTH: int
#   - Type: int (positive)
#   - Typical values: 50, 100, 200, 500
#   - Default: 200
#   - Description: Maximum number of tokens to generate during decoding.
#     Acts as a safety cap to prevent generating extremely long sequences.

LENGTH_PENALTY = 0.6
# LENGTH_PENALTY: float
#   - Type: float (non-negative)
#   - Typical range: 0.0 to 2.0
#   - Default: 0.6
#   - Description: Length penalty exponent in beam search scoring. Higher values
#     favor shorter translations.
#     A penalty of 0.0 = no length bias; 1.0 = linear length normalization.

USE_GREEDY = False
# USE_GREEDY: bool
#   - Type: bool
#   - Choices: True or False
#   - Default: False
#   - Description: When True, force greedy decoding (take the highest-probability
#     token at each step) regardless of BEAM_SIZE. Useful for faster inference
#     at the cost of translation quality.

OUTPUT_TRANSLATIONS = OUTPUT_DIR / "translations.txt"
# OUTPUT_TRANSLATIONS: Path
#   - Type: Path object
#   - Description: Path where translated output sentences are written by
#     translate.py. One translation per line.

OUTPUT_SCORES = OUTPUT_DIR / "translation_scores.txt"
# OUTPUT_SCORES: Path
#   - Type: Path object
#   - Description: Path where translation quality scores (e.g., BLEU) are written.

# ============================================================================
# DEVICE AND REPRODUCIBILITY SETTINGS
# ============================================================================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# DEVICE: str or torch.device
#   - Type: str or torch.device object
#   - Choices: "cpu", "cuda", "cuda:0", "cuda:1", etc., or torch.device(...)
#   - Default: "cuda" if available, else "cpu"
#   - Description: Which device to run computation on. "cuda" for NVIDIA GPUs,
#     "cpu" for CPU-only. Multi-GPU training requires custom DataParallel setup.

NUM_WORKERS = 4
# NUM_WORKERS: int
#   - Type: int (non-negative)
#   - Typical values: 0, 2, 4, 8
#   - Default: 4
#   - Description: Number of worker processes for data loading in DataLoader.
#     0 = load data in main thread (safer, easier to debug).
#     >0 = spawn subprocesses (faster on multi-core machines).
#     See https://docs.pytorch.org/docs/stable/data.html#torch.utils.data.DataLoader

SEED = 42
# SEED: int
#   - Type: int (any non-negative integer)
#   - Typical values: 42, 0, 1234
#   - Default: 42
#   - Description: Random seed for reproducibility. Set RNGs (torch, numpy, random)
#     at the start of training. Different seeds may yield slightly different
#     results due to floating-point nondeterminism and thread timing.

# ============================================================================
# DATA SPLITTING SETTINGS
# ============================================================================

TRAIN_RATIO = 0.8
# TRAIN_RATIO: float
#   - Type: float in (0.0, 1.0)
#   - Typical values: 0.7, 0.8, 0.9
#   - Default: 0.8
#   - Description: Fraction of data used for training split.

VAL_RATIO = 0.1
# VAL_RATIO: float
#   - Type: float in (0.0, 1.0)
#   - Typical values: 0.1, 0.15, 0.2
#   - Default: 0.1
#   - Description: Fraction of data used for validation split.
#     Remaining (1 - train_ratio - val_ratio) goes to test.

# ============================================================================
# EXPERIMENT TRACKING AND LOGGING SETTINGS
# ============================================================================

USE_TENSORBOARD = False
# USE_TENSORBOARD: bool
#   - Type: bool
#   - Choices: True or False
#   - Default: False
#   - Description: When True, log training metrics (loss, learning rate, etc.) to
#     TensorBoard. Requires torch.utils.tensorboard.SummaryWriter.
#     View logs with: tensorboard --logdir <TENSORBOARD_DIR>

TENSORBOARD_DIR = BASE_DIR / "runs"
# TENSORBOARD_DIR: Path
#   - Type: Path object
#   - Description: Directory where TensorBoard event files are written.

EXPERIMENT_NAME = "baseline"
# EXPERIMENT_NAME: str
#   - Type: str (short identifier)
#   - Default: "baseline"
#   - Description: Human-readable name for the experiment. Used in log filenames,
#     checkpoint names, and experiment tracking. Change this for each new experiment.


# ============================================================================
# CONFIG CLASS
# ============================================================================


class Config:
    """Instantiable configuration container for TorchLingo training/inference.

    This class allows you to create multiple independent config instances,
    each with its own hyperparameters and settings. Pass a Config instance
    to train(), evaluate(), or translate() functions.

    Note:
        All attributes correspond to the configuration parameters documented above.

    Examples:
        >>> # Default configuration
        >>> cfg = Config()

        >>> # Custom configuration with specific hyperparameters
        >>> cfg = Config(batch_size=32, learning_rate=1e-5, beam_size=3)

        >>> # Modify on the fly
        >>> cfg.batch_size = 128
        >>> cfg.dropout = 0.2

        >>> # Deep copy for experiments
        >>> cfg_exp1 = cfg.copy()
        >>> cfg_exp1.learning_rate = 5e-5
        >>> # cfg and cfg_exp1 are independent
    """

    def __init__(
        self,
        # Base directories
        base_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None,
        checkpoint_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        # Data and file settings
        data_format: str = "tsv",
        src_col: str = "src",
        tgt_col: str = "tgt",
        src_tok_col: str = "src_tokenized",
        tgt_tok_col: str = "tgt_tokenized",
        train_file: Optional[Path] = None,
        val_file: Optional[Path] = None,
        test_file: Optional[Path] = None,
        raw_data_file: Optional[Path] = None,
        # Tokenization and vocabulary
        use_sentencepiece: bool = False,
        sentencepiece_model_prefix: Optional[str] = None,
        sentencepiece_model: Optional[str] = None,
        sentencepiece_vocab: Optional[str] = None,
        sentencepiece_src_model_prefix: Optional[str] = None,
        sentencepiece_tgt_model_prefix: Optional[str] = None,
        sentencepiece_src_model: Optional[str] = None,
        sentencepiece_tgt_model: Optional[str] = None,
        sentencepiece_src_vocab: Optional[str] = None,
        sentencepiece_tgt_vocab: Optional[str] = None,
        vocab_size: int = 32000,
        min_freq: int = 2,
        sp_model_type: str = "bpe",
        sp_character_coverage: float = 1.0,
        sp_normalization_rule_name: str = "nmt_nfkc",
        # Back-translation and multilingual
        back_trans_src: Optional[Path] = None,
        back_trans_tgt: Optional[Path] = None,
        combined_train_src: Optional[Path] = None,
        combined_train_tgt: Optional[Path] = None,
        reverse_model_checkpoint: Optional[Path] = None,
        multi_train_file: Optional[Path] = None,
        multi_val_file: Optional[Path] = None,
        test_en_x_file: Optional[Path] = None,
        test_x_en_file: Optional[Path] = None,
        lang_tag_en_to_x: str = "<2X>",
        lang_tag_x_to_en: str = "<2E>",
        # Model architecture
        d_model: int = 512,
        n_heads: int = 8,
        num_encoder_layers: int = 6,
        num_decoder_layers: int = 6,
        d_ff: int = 2048,
        dropout: float = 0.1,
        max_seq_length: int = 512,
        # LSTM model hyperparameters
        lstm_emb_dim: int = 256,
        lstm_hidden_dim: int = 512,
        lstm_num_layers: int = 2,
        lstm_dropout: float = 0.2,
        # Experimental toggles
        use_packed_projection: bool = False,
        use_scaled_dot_product_attention: bool = False,
        tie_embeddings: bool = False,
        use_compile: bool = False,
        # Special tokens and indices
        pad_token: str = "<pad>",
        unk_token: str = "<unk>",
        sos_token: str = "<sos>",
        eos_token: str = "<eos>",
        pad_idx: int = 0,
        unk_idx: int = 1,
        sos_idx: int = 2,
        eos_idx: int = 3,
        # Training hyperparameters
        batch_size: int = 64,
        num_steps: int = 100000,
        step_limit: Optional[int] = None,
        learning_rate: float = 0.0001,
        adam_betas: tuple = (0.9, 0.98),
        adam_eps: float = 1e-9,
        warmup_steps: int = 4000,
        label_smoothing: float = 0.1,
        use_bucketing: bool = False,
        bucket_boundaries: Optional[list] = None,
        grad_clip: float = 1.0,
        val_interval: int = 1000,
        save_interval: int = 5000,
        log_interval: int = 100,
        patience: int = 10,
        checkpoint_path: Optional[Path] = None,
        last_checkpoint_path: Optional[Path] = None,
        # Decoding and inference
        beam_size: int = 5,
        max_decode_length: int = 200,
        length_penalty: float = 0.6,
        use_greedy: bool = False,
        output_translations: Optional[Path] = None,
        output_scores: Optional[Path] = None,
        # Device and reproducibility
        device: Optional[str] = None,
        num_workers: int = 4,
        seed: int = 42,
        # Data splitting
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        # Experiment tracking
        use_tensorboard: bool = False,
        tensorboard_dir: Optional[Path] = None,
        experiment_name: str = "baseline",
    ):
        """Initialize a Config instance with given parameters.

        All parameters are optional. If not provided, defaults from the
        module-level constants above are used.
        """
        # Base directories
        self.base_dir = base_dir or BASE_DIR
        self.data_dir = data_dir or (self.base_dir / "data")
        self.checkpoint_dir = checkpoint_dir or (self.base_dir / "checkpoints")
        self.output_dir = output_dir or (self.base_dir / "outputs")

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.checkpoint_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Data and file settings
        self.data_format = data_format
        self.src_col = src_col
        self.tgt_col = tgt_col
        self.src_tok_col = src_tok_col
        self.tgt_tok_col = tgt_tok_col
        self.train_file = train_file or (self.data_dir / f"train.{self.data_format}")
        self.val_file = val_file or (self.data_dir / f"val.{self.data_format}")
        self.test_file = test_file or (self.data_dir / f"test.{self.data_format}")
        self.raw_data_file = raw_data_file or (self.data_dir / "raw_data.txt")

        # Tokenization and vocabulary
        self.use_sentencepiece = use_sentencepiece
        self.sentencepiece_model_prefix = sentencepiece_model_prefix or str(
            self.data_dir / "sp_model"
        )
        self.sentencepiece_model = sentencepiece_model or (
            self.sentencepiece_model_prefix + ".model"
        )
        self.sentencepiece_vocab = sentencepiece_vocab or (
            self.sentencepiece_model_prefix + ".vocab"
        )
        self.sentencepiece_src_model_prefix = (
            sentencepiece_src_model_prefix or self.sentencepiece_model_prefix
        )
        self.sentencepiece_tgt_model_prefix = (
            sentencepiece_tgt_model_prefix or self.sentencepiece_model_prefix
        )
        self.sentencepiece_src_model = sentencepiece_src_model or (
            self.sentencepiece_src_model_prefix + ".model"
        )
        self.sentencepiece_tgt_model = sentencepiece_tgt_model or (
            self.sentencepiece_tgt_model_prefix + ".model"
        )
        self.sentencepiece_src_vocab = sentencepiece_src_vocab or (
            self.sentencepiece_src_model_prefix + ".vocab"
        )
        self.sentencepiece_tgt_vocab = sentencepiece_tgt_vocab or (
            self.sentencepiece_tgt_model_prefix + ".vocab"
        )
        self.vocab_size = vocab_size
        self.min_freq = min_freq
        self.sp_model_type = sp_model_type
        self.sp_character_coverage = sp_character_coverage
        self.sp_normalization_rule_name = sp_normalization_rule_name

        # Back-translation and multilingual
        self.back_trans_src = back_trans_src or (self.data_dir / "train.back_trans.en")
        self.back_trans_tgt = back_trans_tgt or (self.data_dir / "train.back_trans.x")
        self.combined_train_src = combined_train_src or (
            self.data_dir / "train.combined.en"
        )
        self.combined_train_tgt = combined_train_tgt or (
            self.data_dir / "train.combined.x"
        )
        self.reverse_model_checkpoint = reverse_model_checkpoint or (
            self.checkpoint_dir / "reverse_model_best.pt"
        )
        self.multi_train_file = multi_train_file or (
            self.data_dir / f"train.multi.{self.data_format}"
        )
        self.multi_val_file = multi_val_file or (
            self.data_dir / f"val.multi.{self.data_format}"
        )
        self.test_en_x_file = test_en_x_file or (
            self.data_dir / f"test.en-x.{self.data_format}"
        )
        self.test_x_en_file = test_x_en_file or (
            self.data_dir / f"test.x-en.{self.data_format}"
        )
        self.lang_tag_en_to_x = lang_tag_en_to_x
        self.lang_tag_x_to_en = lang_tag_x_to_en

        # Model architecture
        self.d_model = d_model
        self.n_heads = n_heads
        self.num_encoder_layers = num_encoder_layers
        self.num_decoder_layers = num_decoder_layers
        self.d_ff = d_ff
        self.dropout = dropout
        self.max_seq_length = max_seq_length

        # LSTM model hyperparameters
        self.lstm_emb_dim = lstm_emb_dim
        self.lstm_hidden_dim = lstm_hidden_dim
        self.lstm_num_layers = lstm_num_layers
        self.lstm_dropout = lstm_dropout

        # Experimental toggles
        self.use_packed_projection = use_packed_projection
        self.use_scaled_dot_product_attention = use_scaled_dot_product_attention
        self.tie_embeddings = tie_embeddings
        self.use_compile = use_compile

        # Special tokens and indices
        self.pad_token = pad_token
        self.unk_token = unk_token
        self.sos_token = sos_token
        self.eos_token = eos_token
        self.pad_idx = pad_idx
        self.unk_idx = unk_idx
        self.sos_idx = sos_idx
        self.eos_idx = eos_idx

        # Training hyperparameters (continued)
        self.batch_size = batch_size
        self.num_steps = num_steps
        # Optional global step limit (None means no limit)
        self.step_limit = step_limit

        # Training hyperparameters
        self.batch_size = batch_size
        self.num_steps = num_steps
        self.learning_rate = learning_rate
        self.adam_betas = adam_betas
        self.adam_eps = adam_eps
        self.warmup_steps = warmup_steps
        self.label_smoothing = label_smoothing
        self.use_bucketing = use_bucketing
        self.bucket_boundaries = bucket_boundaries
        self.grad_clip = grad_clip
        self.val_interval = val_interval
        self.save_interval = save_interval
        self.log_interval = log_interval
        self.patience = patience
        self.checkpoint_path = checkpoint_path or (
            self.checkpoint_dir / "model_best.pt"
        )
        self.last_checkpoint_path = last_checkpoint_path or (
            self.checkpoint_dir / "model_last.pt"
        )

        # Decoding and inference
        self.beam_size = beam_size
        self.max_decode_length = max_decode_length
        self.length_penalty = length_penalty
        self.use_greedy = use_greedy
        self.output_translations = output_translations or (
            self.output_dir / "translations.txt"
        )
        self.output_scores = output_scores or (
            self.output_dir / "translation_scores.txt"
        )

        # Device and reproducibility
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.num_workers = num_workers
        self.seed = seed

        # Data splitting
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio

        # Experiment tracking
        self.use_tensorboard = use_tensorboard
        self.tensorboard_dir = tensorboard_dir or (self.base_dir / "runs")
        self.experiment_name = experiment_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary for logging and serialization.

        Returns:
            Dictionary with all config attributes (excluding private attributes).
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def print(self) -> None:
        """Pretty-print this configuration instance.

        Useful for logging the exact configuration used in an experiment.
        """
        print("=" * 80)
        print("Configuration Settings")
        print("=" * 80)
        for key, value in sorted(self.to_dict().items()):
            print(f"{key:30s}: {value}")
        print("=" * 80)

    def copy(self):
        """Return a deep copy of this config.

        Modifications to the copy do not affect the original.

        Returns:
            A new Config instance with the same parameter values.
        """
        return deepcopy(self)

    def get(self, name: str) -> Any:
        """Getter for any config parameter by name."""
        return getattr(self, name)

    def set(self, name: str, value: Any) -> None:
        """Setter for any config parameter by name with validation."""
        setattr(self, name, value)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_path(value: Optional[Path], allow_none: bool = False) -> Path:
        if value is None:
            if allow_none:
                return value
            raise ValueError("Path value cannot be None")
        return value if isinstance(value, Path) else Path(value)

    @staticmethod
    def _ensure_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        raise TypeError("Expected a boolean value")

    @staticmethod
    def _ensure_str(value: Any, allow_empty: bool = False) -> str:
        if not isinstance(value, str):
            raise TypeError("Expected a string value")
        if not allow_empty and value == "":
            raise ValueError("String value cannot be empty")
        return value

    @staticmethod
    def _ensure_positive_int(value: Any, allow_zero: bool = False) -> int:
        if not isinstance(value, int):
            raise TypeError("Expected an integer value")
        if allow_zero and value < 0:
            raise ValueError("Integer value must be non-negative")
        if not allow_zero and value <= 0:
            raise ValueError("Integer value must be positive")
        return value

    @staticmethod
    def _ensure_float_in_range(
        value: Any, low: float, high: float, inclusive_high: bool = True
    ) -> float:
        if not isinstance(value, (float, int)):
            raise TypeError("Expected a float value")
        if value < low or (value > high if inclusive_high else value >= high):
            raise ValueError(
                f"Float value must be in range [{low}, {high}{']' if inclusive_high else ')'}"
            )
        return float(value)

    @staticmethod
    def _ensure_tuple_two_floats(value: Any) -> tuple:
        if not (isinstance(value, tuple) and len(value) == 2):
            raise TypeError("Expected a tuple of two floats")
        beta1, beta2 = value
        if not all(isinstance(b, (float, int)) for b in (beta1, beta2)):
            raise TypeError("Adam betas must be floats")
        if not (0.0 <= beta1 < 1.0 and 0.0 <= beta2 < 1.0):
            raise ValueError("Adam betas must be in [0, 1)")
        return (float(beta1), float(beta2))

    @staticmethod
    def _ensure_bucket_boundaries(value: Any) -> Optional[list]:
        if value is None:
            return None
        if not isinstance(value, list):
            raise TypeError(
                "bucket_boundaries must be a list of positive, increasing ints"
            )
        if not all(isinstance(v, int) and v > 0 for v in value):
            raise ValueError("bucket_boundaries must contain positive integers")
        if any(value[i] >= value[i + 1] for i in range(len(value) - 1)):
            raise ValueError("bucket_boundaries must be strictly increasing")
        return value

    @staticmethod
    def _ensure_device(value: Any) -> Any:
        if isinstance(value, (str, torch.device)):
            return value
        raise TypeError("device must be a string or torch.device")

    @staticmethod
    def _ensure_length_penalty(value: Any) -> float:
        if not isinstance(value, (float, int)):
            raise TypeError("length_penalty must be a float")
        if value < 0:
            raise ValueError("length_penalty must be non-negative")
        return float(value)

    def _ensure_n_heads(self, value: Any) -> int:
        val = self._ensure_positive_int(value)
        if hasattr(self, "d_model") and self.d_model % val != 0:
            raise ValueError("d_model must be divisible by n_heads")
        return val

    def _ensure_d_model(self, value: Any) -> int:
        val = self._ensure_positive_int(value)
        if hasattr(self, "n_heads") and val % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        return val

    @staticmethod
    def _ensure_sp_model_type(value: Any) -> str:
        allowed = {"bpe", "unigram", "char", "word"}
        val = Config._ensure_str(value)
        if val not in allowed:
            raise ValueError(f"sp_model_type must be one of {allowed}")
        return val

    @staticmethod
    def _ensure_data_format(value: Any) -> str:
        allowed = {"tsv", "csv", "parquet", "json"}
        val = Config._ensure_str(value)
        if val not in allowed:
            raise ValueError(f"data_format must be one of {allowed}")
        return val

    @staticmethod
    def _ensure_grad_clip(value: Any) -> Optional[float]:
        if value is None:
            return None
        if not isinstance(value, (float, int)):
            raise TypeError("grad_clip must be a float or None")
        if value < 0:
            raise ValueError("grad_clip must be non-negative")
        return float(value)

    def _validate_and_set(self, name: str, value: Any) -> None:
        validator = self._FIELD_VALIDATORS.get(name)
        if validator:
            value = validator(self, value)
        if self.__dict__.get(name) != value:
            self.__dict__[name] = value

    def _get_field(self, name: str) -> Any:
        """Read raw value from __dict__ with a clear error if unset.

        This centralizes the guard so all property getters can call it
        and raise AttributeError when a value hasn't been initialized yet.
        """
        val = self.__dict__.get(name, None)
        if val is None:
            raise AttributeError(f"{name} is not set yet")
        return val

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        if hasattr(self, "_FIELD_VALIDATORS") and name in self._FIELD_VALIDATORS:
            self._validate_and_set(name, value)
        else:
            super().__setattr__(name, value)

    # Validators for each field (bound as lambdas to allow self-aware checks)
    _FIELD_VALIDATORS = {
        "base_dir": lambda self, v: self._ensure_path(v),
        "data_dir": lambda self, v: self._ensure_path(v),
        "checkpoint_dir": lambda self, v: self._ensure_path(v),
        "output_dir": lambda self, v: self._ensure_path(v),
        "data_format": lambda self, v: self._ensure_data_format(v),
        "src_col": lambda self, v: self._ensure_str(v),
        "tgt_col": lambda self, v: self._ensure_str(v),
        "src_tok_col": lambda self, v: self._ensure_str(v),
        "tgt_tok_col": lambda self, v: self._ensure_str(v),
        "train_file": lambda self, v: self._ensure_path(v, allow_none=False),
        "val_file": lambda self, v: self._ensure_path(v, allow_none=False),
        "test_file": lambda self, v: self._ensure_path(v, allow_none=False),
        "raw_data_file": lambda self, v: self._ensure_path(v, allow_none=False),
        "use_sentencepiece": lambda self, v: self._ensure_bool(v),
        "sentencepiece_model_prefix": lambda self, v: self._ensure_str(v),
        "sentencepiece_model": lambda self, v: self._ensure_str(v),
        "sentencepiece_vocab": lambda self, v: self._ensure_str(v),
        "sentencepiece_src_model_prefix": lambda self, v: self._ensure_str(v),
        "sentencepiece_tgt_model_prefix": lambda self, v: self._ensure_str(v),
        "sentencepiece_src_model": lambda self, v: self._ensure_str(v),
        "sentencepiece_tgt_model": lambda self, v: self._ensure_str(v),
        "sentencepiece_src_vocab": lambda self, v: self._ensure_str(v),
        "sentencepiece_tgt_vocab": lambda self, v: self._ensure_str(v),
        "vocab_size": lambda self, v: self._ensure_positive_int(v),
        "min_freq": lambda self, v: self._ensure_positive_int(v),
        "sp_model_type": lambda self, v: self._ensure_sp_model_type(v),
        "sp_character_coverage": lambda self, v: self._ensure_float_in_range(
            v, 0.0, 1.0
        ),
        "sp_normalization_rule_name": lambda self, v: self._ensure_str(v),
        "back_trans_src": lambda self, v: self._ensure_path(v),
        "back_trans_tgt": lambda self, v: self._ensure_path(v),
        "combined_train_src": lambda self, v: self._ensure_path(v),
        "combined_train_tgt": lambda self, v: self._ensure_path(v),
        "reverse_model_checkpoint": lambda self, v: self._ensure_path(v),
        "multi_train_file": lambda self, v: self._ensure_path(v),
        "multi_val_file": lambda self, v: self._ensure_path(v),
        "test_en_x_file": lambda self, v: self._ensure_path(v),
        "test_x_en_file": lambda self, v: self._ensure_path(v),
        "lang_tag_en_to_x": lambda self, v: self._ensure_str(v),
        "lang_tag_x_to_en": lambda self, v: self._ensure_str(v),
        "d_model": lambda self, v: self._ensure_d_model(v),
        "n_heads": lambda self, v: self._ensure_n_heads(v),
        "num_encoder_layers": lambda self, v: self._ensure_positive_int(v),
        "num_decoder_layers": lambda self, v: self._ensure_positive_int(v),
        "d_ff": lambda self, v: self._ensure_positive_int(v),
        "dropout": lambda self, v: self._ensure_float_in_range(
            v, 0.0, 1.0, inclusive_high=False
        ),
        "max_seq_length": lambda self, v: self._ensure_positive_int(v),
        "lstm_emb_dim": lambda self, v: self._ensure_positive_int(v),
        "lstm_hidden_dim": lambda self, v: self._ensure_positive_int(v),
        "lstm_num_layers": lambda self, v: self._ensure_positive_int(v),
        "lstm_dropout": lambda self, v: self._ensure_float_in_range(
            v, 0.0, 1.0, inclusive_high=False
        ),
        "use_packed_projection": lambda self, v: self._ensure_bool(v),
        "use_scaled_dot_product_attention": lambda self, v: self._ensure_bool(v),
        "tie_embeddings": lambda self, v: self._ensure_bool(v),
        "use_compile": lambda self, v: self._ensure_bool(v),
        "pad_token": lambda self, v: self._ensure_str(v),
        "unk_token": lambda self, v: self._ensure_str(v),
        "sos_token": lambda self, v: self._ensure_str(v),
        "eos_token": lambda self, v: self._ensure_str(v),
        "pad_idx": lambda self, v: self._ensure_positive_int(v, allow_zero=True),
        "unk_idx": lambda self, v: self._ensure_positive_int(v, allow_zero=True),
        "sos_idx": lambda self, v: self._ensure_positive_int(v, allow_zero=True),
        "eos_idx": lambda self, v: self._ensure_positive_int(v, allow_zero=True),
        "batch_size": lambda self, v: self._ensure_positive_int(v),
        "num_steps": lambda self, v: self._ensure_positive_int(v),
        "learning_rate": lambda self, v: self._ensure_float_in_range(
            v, 0.0, float("inf")
        ),
        "adam_betas": lambda self, v: self._ensure_tuple_two_floats(v),
        "adam_eps": lambda self, v: self._ensure_float_in_range(v, 0.0, float("inf")),
        "warmup_steps": lambda self, v: self._ensure_positive_int(v, allow_zero=True),
        "label_smoothing": lambda self, v: self._ensure_float_in_range(
            v, 0.0, 1.0, inclusive_high=False
        ),
        "use_bucketing": lambda self, v: self._ensure_bool(v),
        "bucket_boundaries": lambda self, v: self._ensure_bucket_boundaries(v),
        "grad_clip": lambda self, v: self._ensure_grad_clip(v),
        "val_interval": lambda self, v: self._ensure_positive_int(v),
        "save_interval": lambda self, v: self._ensure_positive_int(v),
        "log_interval": lambda self, v: self._ensure_positive_int(v),
        "patience": lambda self, v: self._ensure_positive_int(v),
        "checkpoint_path": lambda self, v: self._ensure_path(v),
        "last_checkpoint_path": lambda self, v: self._ensure_path(v),
        "beam_size": lambda self, v: self._ensure_positive_int(v),
        "max_decode_length": lambda self, v: self._ensure_positive_int(v),
        "length_penalty": lambda self, v: self._ensure_length_penalty(v),
        "use_greedy": lambda self, v: self._ensure_bool(v),
        "output_translations": lambda self, v: self._ensure_path(v),
        "output_scores": lambda self, v: self._ensure_path(v),
        "device": lambda self, v: self._ensure_device(v),
        "num_workers": lambda self, v: self._ensure_positive_int(v, allow_zero=True),
        "seed": lambda self, v: self._ensure_positive_int(v, allow_zero=True),
        "train_ratio": lambda self, v: self._ensure_float_in_range(
            v, 0.0, 1.0, inclusive_high=False
        ),
        "val_ratio": lambda self, v: self._ensure_float_in_range(
            v, 0.0, 1.0, inclusive_high=False
        ),
        "use_tensorboard": lambda self, v: self._ensure_bool(v),
        "tensorboard_dir": lambda self, v: self._ensure_path(v),
        "experiment_name": lambda self, v: self._ensure_str(v),
    }

    # Explicit properties with docstrings so editors show hover help
    @property
    def base_dir(self) -> Path:
        """Return root directory of the project, derived from this file's location.

        Returns:
            Path: root directory of the project, derived from this file's location.
        """

        return self._get_field("base_dir")

    @base_dir.setter
    def base_dir(self, value: Path) -> None:
        """Set root directory of the project, derived from this file's location.

        Args:
            value (Path): root directory of the project, derived from this file's location.
        """
        self._validate_and_set("base_dir", value)

    @property
    def data_dir(self) -> Path:
        """Return directory where all data files (raw, processed, vocab) are stored.

        Returns:
            Path: directory where all data files (raw, processed, vocab) are stored.
        """

        return self._get_field("data_dir")

    @data_dir.setter
    def data_dir(self, value: Path) -> None:
        """Set directory where all data files (raw, processed, vocab) are stored.

        Args:
            value (Path): directory where all data files (raw, processed, vocab) are stored.
        """
        self._validate_and_set("data_dir", value)

    @property
    def checkpoint_dir(self) -> Path:
        """Return where trained model checkpoints are saved.

        Returns:
            Path: where trained model checkpoints are saved.
        """

        return self._get_field("checkpoint_dir")

    @checkpoint_dir.setter
    def checkpoint_dir(self, value: Path) -> None:
        """Set where trained model checkpoints are saved.

        Args:
            value (Path): where trained model checkpoints are saved.
        """
        self._validate_and_set("checkpoint_dir", value)

    @property
    def output_dir(self) -> Path:
        """Return where translation outputs and results are written.

        Returns:
            Path: where translation outputs and results are written.
        """

        return self._get_field("output_dir")

    @output_dir.setter
    def output_dir(self, value: Path) -> None:
        """Set where translation outputs and results are written.

        Args:
            value (Path): where translation outputs and results are written.
        """
        self._validate_and_set("output_dir", value)

    @property
    def data_format(self) -> str:
        """Return File format for train/val/test data files.

        Each file must contain two columns: SRC_COL (source language) and TGT_COL (target language). The suffix will be appended to train/val/test filenames automatically.

        Returns:
            str: File format for train/val/test data files. Each file must contain two columns: SRC_COL (source language) and TGT_COL (target language). The suffix will be appended to train/val/test filenames automatically.
        """

        return self._get_field("data_format")

    @data_format.setter
    def data_format(self, value: str) -> None:
        """Set File format for train/val/test data files.

        Args:
            value (str): File format for train/val/test data files. Each file must contain two columns: SRC_COL (source language) and TGT_COL (target language). The suffix will be appended to train/val/test filenames automatically.
        """
        self._validate_and_set("data_format", value)

    @property
    def src_col(self) -> str:
        """Return Name of the column containing source language sentences in the data files (e.g., English in an En->Spanish translation task).

        Returns:
            str (column name): Name of the column containing source language sentences in the data files (e.g., English in an En->Spanish translation task).
        """

        return self._get_field("src_col")

    @src_col.setter
    def src_col(self, value: str) -> None:
        """Set Name of the column containing source language sentences in the data files (e.g., English in an En->Spanish translation task).

        Args:
            value (str (column name)): Name of the column containing source language sentences in the data files (e.g., English in an En->Spanish translation task).
        """
        self._validate_and_set("src_col", value)

    @property
    def tgt_col(self) -> str:
        """Return Name of the column containing target language sentences in the data files (e.g., Spanish in an En->Spanish translation task).

        Returns:
            str (column name): Name of the column containing target language sentences in the data files (e.g., Spanish in an En->Spanish translation task).
        """

        return self._get_field("tgt_col")

    @tgt_col.setter
    def tgt_col(self, value: str) -> None:
        """Set Name of the column containing target language sentences in the data files (e.g., Spanish in an En->Spanish translation task).

        Args:
            value (str (column name)): Name of the column containing target language sentences in the data files (e.g., Spanish in an En->Spanish translation task).
        """
        self._validate_and_set("tgt_col", value)

    @property
    def src_tok_col(self) -> str:
        """Return Name of the optional column containing pre-tokenized source.

        Returns:
            str (column name): Name of the optional column containing pre-tokenized source.
        """

        return self._get_field("src_tok_col")

    @src_tok_col.setter
    def src_tok_col(self, value: str) -> None:
        """Set Name of the optional column containing pre-tokenized source.

        Args:
            value (str (column name)): Name of the optional column containing pre-tokenized source.
        """
        self._validate_and_set("src_tok_col", value)

    @property
    def tgt_tok_col(self) -> str:
        """Return Name of the optional column containing pre-tokenized target.

        Returns:
            str (column name): Name of the optional column containing pre-tokenized target.
        """

        return self._get_field("tgt_tok_col")

    @tgt_tok_col.setter
    def tgt_tok_col(self, value: str) -> None:
        """Set Name of the optional column containing pre-tokenized target.

        Args:
            value (str (column name)): Name of the optional column containing pre-tokenized target.
        """
        self._validate_and_set("tgt_tok_col", value)

    @property
    def train_file(self) -> Path:
        """Return path to the training data file.

        Used by train.py and dataset.py. The file must exist before training and should contain parallel source/target pairs.

        Returns:
            Path object: Path to the training data file. Used by train.py and dataset.py. The file must exist before training and should contain parallel source/target pairs.
        """

        return self._get_field("train_file")

    @train_file.setter
    def train_file(self, value: Path) -> None:
        """Set path to the training data file.

        Args:
            value (Path object): Path to the training data file. Used by train.py and dataset.py. The file must exist before training and should contain parallel source/target pairs.
        """
        self._validate_and_set("train_file", value)

    @property
    def val_file(self) -> Path:
        """Return path to the validation data file.

        Used for model selection during training (computed every VAL_INTERVAL steps).

        Returns:
            Path object: Path to the validation data file. Used for model selection during training (computed every VAL_INTERVAL steps).
        """

        return self._get_field("val_file")

    @val_file.setter
    def val_file(self, value: Path) -> None:
        """Set path to the validation data file.

        Args:
            value (Path object): Path to the validation data file. Used for model selection during training (computed every VAL_INTERVAL steps).
        """
        self._validate_and_set("val_file", value)

    @property
    def test_file(self) -> Path:
        """Return path to the test data file (held-out set).

        Used for final evaluation after training completes.

        Returns:
            Path object: Path to the test data file (held-out set). Used for final evaluation after training completes.
        """

        return self._get_field("test_file")

    @test_file.setter
    def test_file(self, value: Path) -> None:
        """Set path to the test data file (held-out set).

        Args:
            value (Path object): Path to the test data file (held-out set). Used for final evaluation after training completes.
        """
        self._validate_and_set("test_file", value)

    @property
    def raw_data_file(self) -> Path:
        """Return path used for raw, unprocessed parallel data when needed.

        Prefer using structured CSV/TSV/Parquet/JSON files with `src` and `tgt` columns or passing explicit parallel files (src,tgt) to `load_data`. Historically single-file pipe-separated (|||) format was supported but this is deprecated in favor of explicit CSV/TSV files or two-file inputs.

        Returns:
            Path object: Path used for raw, unprocessed parallel data when needed. Prefer using structured CSV/TSV/Parquet/JSON files with `src` and `tgt` columns or passing explicit parallel files (src,tgt) to `load_data`. Historically single-file pipe-separated (|||) format was supported but this is deprecated in favor of explicit CSV/TSV files or two-file inputs.
        """

        return self._get_field("raw_data_file")

    @raw_data_file.setter
    def raw_data_file(self, value: Path) -> None:
        """Set path used for raw, unprocessed parallel data when needed.

        Args:
            value (Path object): Path used for raw, unprocessed parallel data when needed. Prefer using structured CSV/TSV/Parquet/JSON files with `src` and `tgt` columns or passing explicit parallel files (src,tgt) to `load_data`. Historically single-file pipe-separated (|||) format was supported but this is deprecated in favor of explicit CSV/TSV files or two-file inputs.
        """
        self._validate_and_set("raw_data_file", value)

    @property
    def use_sentencepiece(self) -> bool:
        """Return When True, use SentencePiece subword tokenization (BPE/Unigram) instead of simple whitespace tokenization.

        Requires a trained .model file. See https://github.com/google/sentencepiece for details.

        Returns:
            bool: When True, use SentencePiece subword tokenization (BPE/Unigram) instead of simple whitespace tokenization. Requires a trained .model file. See https://github.com/google/sentencepiece for details.
        """

        return self._get_field("use_sentencepiece")

    @use_sentencepiece.setter
    def use_sentencepiece(self, value: bool) -> None:
        """Set When True, use SentencePiece subword tokenization (BPE/Unigram) instead of simple whitespace tokenization.

        Args:
            value (bool): When True, use SentencePiece subword tokenization (BPE/Unigram) instead of simple whitespace tokenization. Requires a trained .model file. See https://github.com/google/sentencepiece for details.
        """
        self._validate_and_set("use_sentencepiece", value)

    @property
    def sentencepiece_model_prefix(self) -> str:
        """Return Prefix for SentencePiece model files.

        Training will create <PREFIX>.model and <PREFIX>.vocab. Only used if USE_SENTENCEPIECE=True.

        Returns:
            str (path prefix): Prefix for SentencePiece model files. Training will create <PREFIX>.model and <PREFIX>.vocab. Only used if USE_SENTENCEPIECE=True.
        """

        return self._get_field("sentencepiece_model_prefix")

    @sentencepiece_model_prefix.setter
    def sentencepiece_model_prefix(self, value: str) -> None:
        """Set Prefix for SentencePiece model files.

        Args:
            value (str (path prefix)): Prefix for SentencePiece model files. Training will create <PREFIX>.model and <PREFIX>.vocab. Only used if USE_SENTENCEPIECE=True.
        """
        self._validate_and_set("sentencepiece_model_prefix", value)

    @property
    def sentencepiece_model(self) -> str:
        """Return Full path to the trained SentencePiece .model file.

        Auto-derived from SENTENCEPIECE_MODEL_PREFIX.

        Returns:
            str (file path): Full path to the trained SentencePiece .model file. Auto-derived from SENTENCEPIECE_MODEL_PREFIX.
        """

        return self._get_field("sentencepiece_model")

    @sentencepiece_model.setter
    def sentencepiece_model(self, value: str) -> None:
        """Set Full path to the trained SentencePiece .model file.

        Args:
            value (str (file path)): Full path to the trained SentencePiece .model file. Auto-derived from SENTENCEPIECE_MODEL_PREFIX.
        """
        self._validate_and_set("sentencepiece_model", value)

    @property
    def sentencepiece_vocab(self) -> str:
        """Return Full path to the SentencePiece .vocab file (human-readable vocab list).

        Auto-derived from SENTENCEPIECE_MODEL_PREFIX.

        Returns:
            str (file path): Full path to the SentencePiece .vocab file (human-readable vocab list). Auto-derived from SENTENCEPIECE_MODEL_PREFIX.
        """

        return self._get_field("sentencepiece_vocab")

    @sentencepiece_vocab.setter
    def sentencepiece_vocab(self, value: str) -> None:
        """Set Full path to the SentencePiece .vocab file (human-readable vocab list).

        Args:
            value (str (file path)): Full path to the SentencePiece .vocab file (human-readable vocab list). Auto-derived from SENTENCEPIECE_MODEL_PREFIX.
        """
        self._validate_and_set("sentencepiece_vocab", value)

    @property
    def sentencepiece_src_model_prefix(self) -> str:
        """Return prefix for source SentencePiece model files."""

        return self._get_field("sentencepiece_src_model_prefix")

    @sentencepiece_src_model_prefix.setter
    def sentencepiece_src_model_prefix(self, value: str) -> None:
        """Set prefix for source SentencePiece model files."""
        self._validate_and_set("sentencepiece_src_model_prefix", value)

    @property
    def sentencepiece_tgt_model_prefix(self) -> str:
        """Return prefix for target SentencePiece model files."""

        return self._get_field("sentencepiece_tgt_model_prefix")

    @sentencepiece_tgt_model_prefix.setter
    def sentencepiece_tgt_model_prefix(self, value: str) -> None:
        """Set prefix for target SentencePiece model files."""
        self._validate_and_set("sentencepiece_tgt_model_prefix", value)

    @property
    def sentencepiece_src_model(self) -> str:
        """Return path to the source SentencePiece model."""

        return self._get_field("sentencepiece_src_model")

    @sentencepiece_src_model.setter
    def sentencepiece_src_model(self, value: str) -> None:
        """Set path to the source SentencePiece model."""
        self._validate_and_set("sentencepiece_src_model", value)

    @property
    def sentencepiece_tgt_model(self) -> str:
        """Return path to the target SentencePiece model."""

        return self._get_field("sentencepiece_tgt_model")

    @sentencepiece_tgt_model.setter
    def sentencepiece_tgt_model(self, value: str) -> None:
        """Set path to the target SentencePiece model."""
        self._validate_and_set("sentencepiece_tgt_model", value)

    @property
    def sentencepiece_src_vocab(self) -> str:
        """Return path to the source SentencePiece vocab."""

        return self._get_field("sentencepiece_src_vocab")

    @sentencepiece_src_vocab.setter
    def sentencepiece_src_vocab(self, value: str) -> None:
        """Set path to the source SentencePiece vocab."""
        self._validate_and_set("sentencepiece_src_vocab", value)

    @property
    def sentencepiece_tgt_vocab(self) -> str:
        """Return path to the target SentencePiece vocab."""

        return self._get_field("sentencepiece_tgt_vocab")

    @sentencepiece_tgt_vocab.setter
    def sentencepiece_tgt_vocab(self, value: str) -> None:
        """Set path to the target SentencePiece vocab."""
        self._validate_and_set("sentencepiece_tgt_vocab", value)

    @property
    def vocab_size(self) -> int:
        """Return Target vocabulary size when training a SentencePiece model.

        Ignored if USE_SENTENCEPIECE=False.

        Returns:
            int (positive): Target vocabulary size when training a SentencePiece model. Ignored if USE_SENTENCEPIECE=False.
        """

        return self._get_field("vocab_size")

    @vocab_size.setter
    def vocab_size(self, value: int) -> None:
        """Set Target vocabulary size when training a SentencePiece model.

        Args:
            value (int (positive)): Target vocabulary size when training a SentencePiece model. Ignored if USE_SENTENCEPIECE=False.
        """
        self._validate_and_set("vocab_size", value)

    @property
    def min_freq(self) -> int:
        """Return minimum frequency threshold for vocabulary tokens.

        Tokens appearing fewer than min_freq times are mapped to the UNK token index.

        Returns:
            int: Minimum frequency threshold.
        """
        return self._get_field("min_freq")

    @min_freq.setter
    def min_freq(self, value: int) -> None:
        """Set minimum frequency threshold for vocabulary tokens.

        Args:
            value (int): Minimum frequency threshold.
        """
        self._validate_and_set("min_freq", value)

    @property
    def sp_model_type(self) -> str:
        """Return Algorithm for SentencePiece training.

        "bpe" = Byte-Pair Encoding (recommended for most cases). "unigram" = Unigram LM (best for some CJK languages). "char", "word" = character/word-level tokenization. See https://github.com/google/sentencepiece.

        Returns:
            str: Algorithm for SentencePiece training. "bpe" = Byte-Pair Encoding (recommended for most cases). "unigram" = Unigram LM (best for some CJK languages). "char", "word" = character/word-level tokenization. See https://github.com/google/sentencepiece.
        """

        return self._get_field("sp_model_type")

    @sp_model_type.setter
    def sp_model_type(self, value: str) -> None:
        """Set Algorithm for SentencePiece training.

        Args:
            value (str): Algorithm for SentencePiece training. "bpe" = Byte-Pair Encoding (recommended for most cases). "unigram" = Unigram LM (best for some CJK languages). "char", "word" = character/word-level tokenization. See https://github.com/google/sentencepiece.
        """
        self._validate_and_set("sp_model_type", value)

    @property
    def sp_character_coverage(self) -> float:
        """Return fraction of characters in the input to be covered by the model.

        1.0 = cover all characters (no unknown chars in vocab). 0.9999 = allow rare chars to be encoded as <unk>. See SentencePiece docs: https://github.com/google/sentencepiece.

        Returns:
            float in (0.0, 1.0]: Fraction of characters in the input to be covered by the model. 1.0 = cover all characters (no unknown chars in vocab). 0.9999 = allow rare chars to be encoded as <unk>. See SentencePiece docs: https://github.com/google/sentencepiece.
        """

        return self._get_field("sp_character_coverage")

    @sp_character_coverage.setter
    def sp_character_coverage(self, value: float) -> None:
        """Set fraction of characters in the input to be covered by the model.

        Args:
            value (float in (0.0, 1.0]): Fraction of characters in the input to be covered by the model. 1.0 = cover all characters (no unknown chars in vocab). 0.9999 = allow rare chars to be encoded as <unk>. See SentencePiece docs: https://github.com/google/sentencepiece.
        """
        self._validate_and_set("sp_character_coverage", value)

    @property
    def sp_normalization_rule_name(self) -> str:
        """Return Unicode normalization rule applied during SentencePiece training/inference.

        "nmt_nfkc" is standard for NMT. See SentencePiece documentation for details.

        Returns:
            str: Unicode normalization rule applied during SentencePiece training/inference. "nmt_nfkc" is standard for NMT. See SentencePiece documentation for details.
        """

        return self._get_field("sp_normalization_rule_name")

    @sp_normalization_rule_name.setter
    def sp_normalization_rule_name(self, value: str) -> None:
        """Set Unicode normalization rule applied during SentencePiece training/inference.

        Args:
            value (str): Unicode normalization rule applied during SentencePiece training/inference. "nmt_nfkc" is standard for NMT. See SentencePiece documentation for details.
        """
        self._validate_and_set("sp_normalization_rule_name", value)

    @property
    def back_trans_src(self) -> Path:
        """Return path to source language sentences generated via back-translation.

        Returns:
            Path object: Path to source language sentences generated via back-translation.
        """

        return self._get_field("back_trans_src")

    @back_trans_src.setter
    def back_trans_src(self, value: Path) -> None:
        """Set path to source language sentences generated via back-translation.

        Args:
            value (Path object): Path to source language sentences generated via back-translation.
        """
        self._validate_and_set("back_trans_src", value)

    @property
    def back_trans_tgt(self) -> Path:
        """Return path to target language (original) sentences for back-translation data.

        Returns:
            Path object: Path to target language (original) sentences for back-translation data.
        """

        return self._get_field("back_trans_tgt")

    @back_trans_tgt.setter
    def back_trans_tgt(self, value: Path) -> None:
        """Set path to target language (original) sentences for back-translation data.

        Args:
            value (Path object): Path to target language (original) sentences for back-translation data.
        """
        self._validate_and_set("back_trans_tgt", value)

    @property
    def combined_train_src(self) -> Path:
        """Return path to combined training data (original + back-translated).

        Returns:
            Path object: Path to combined training data (original + back-translated).
        """

        return self._get_field("combined_train_src")

    @combined_train_src.setter
    def combined_train_src(self, value: Path) -> None:
        """Set path to combined training data (original + back-translated).

        Args:
            value (Path object): Path to combined training data (original + back-translated).
        """
        self._validate_and_set("combined_train_src", value)

    @property
    def combined_train_tgt(self) -> Path:
        """Return path to combined training targets.

        Returns:
            Path object: Path to combined training targets.
        """

        return self._get_field("combined_train_tgt")

    @combined_train_tgt.setter
    def combined_train_tgt(self, value: Path) -> None:
        """Set path to combined training targets.

        Args:
            value (Path object): Path to combined training targets.
        """
        self._validate_and_set("combined_train_tgt", value)

    @property
    def reverse_model_checkpoint(self) -> Path:
        """Return path to checkpoint of the reverse model (X->En) used for back-translation.

        Returns:
            Path object: Path to checkpoint of the reverse model (X->En) used for back-translation.
        """

        return self._get_field("reverse_model_checkpoint")

    @reverse_model_checkpoint.setter
    def reverse_model_checkpoint(self, value: Path) -> None:
        """Set path to checkpoint of the reverse model (X->En) used for back-translation.

        Args:
            value (Path object): Path to checkpoint of the reverse model (X->En) used for back-translation.
        """
        self._validate_and_set("reverse_model_checkpoint", value)

    @property
    def multi_train_file(self) -> Path:
        """Return path to multilingual training data.

        Returns:
            Path object: Path to multilingual training data.
        """

        return self._get_field("multi_train_file")

    @multi_train_file.setter
    def multi_train_file(self, value: Path) -> None:
        """Set path to multilingual training data.

        Args:
            value (Path object): Path to multilingual training data.
        """
        self._validate_and_set("multi_train_file", value)

    @property
    def multi_val_file(self) -> Path:
        """Return path to multilingual validation data.

        Returns:
            Path object: Path to multilingual validation data.
        """

        return self._get_field("multi_val_file")

    @multi_val_file.setter
    def multi_val_file(self, value: Path) -> None:
        """Set path to multilingual validation data.

        Args:
            value (Path object): Path to multilingual validation data.
        """
        self._validate_and_set("multi_val_file", value)

    @property
    def test_en_x_file(self) -> Path:
        """Return Test set for En->X direction.

        Returns:
            Path object: Test set for En->X direction.
        """

        return self._get_field("test_en_x_file")

    @test_en_x_file.setter
    def test_en_x_file(self, value: Path) -> None:
        """Set Test set for En->X direction.

        Args:
            value (Path object): Test set for En->X direction.
        """
        self._validate_and_set("test_en_x_file", value)

    @property
    def test_x_en_file(self) -> Path:
        """Return Test set for X->En direction.

        Returns:
            Path object: Test set for X->En direction.
        """

        return self._get_field("test_x_en_file")

    @test_x_en_file.setter
    def test_x_en_file(self, value: Path) -> None:
        """Set Test set for X->En direction.

        Args:
            value (Path object): Test set for X->En direction.
        """
        self._validate_and_set("test_x_en_file", value)

    @property
    def lang_tag_en_to_x(self) -> str:
        """Return Special token prepended to source for En->X direction in multilingual models.

        Indicates "translate to X".

        Returns:
            str: Special token prepended to source for En->X direction in multilingual models. Indicates "translate to X".
        """

        return self._get_field("lang_tag_en_to_x")

    @lang_tag_en_to_x.setter
    def lang_tag_en_to_x(self, value: str) -> None:
        """Set Special token prepended to source for En->X direction in multilingual models.

        Args:
            value (str): Special token prepended to source for En->X direction in multilingual models. Indicates "translate to X".
        """
        self._validate_and_set("lang_tag_en_to_x", value)

    @property
    def lang_tag_x_to_en(self) -> str:
        """Return Special token prepended to source for X->En direction in multilingual models.

        Indicates "translate to English".

        Returns:
            str: Special token prepended to source for X->En direction in multilingual models. Indicates "translate to English".
        """

        return self._get_field("lang_tag_x_to_en")

    @lang_tag_x_to_en.setter
    def lang_tag_x_to_en(self, value: str) -> None:
        """Set Special token prepended to source for X->En direction in multilingual models.

        Args:
            value (str): Special token prepended to source for X->En direction in multilingual models. Indicates "translate to English".
        """
        self._validate_and_set("lang_tag_x_to_en", value)

    @property
    def d_model(self) -> int:
        """Return Embedding dimension and internal representation size of the Transformer model.

        Larger values increase model capacity but require more memory. Must be divisible by N_HEADS.

        Returns:
            int (positive): Embedding dimension and internal representation size of the Transformer model. Larger values increase model capacity but require more memory. Must be divisible by N_HEADS.
        """

        return self._get_field("d_model")

    @d_model.setter
    def d_model(self, value: int) -> None:
        """Set Embedding dimension and internal representation size of the Transformer model.

        Args:
            value (int (positive)): Embedding dimension and internal representation size of the Transformer model. Larger values increase model capacity but require more memory. Must be divisible by N_HEADS.
        """
        self._validate_and_set("d_model", value)

    @property
    def n_heads(self) -> int:
        """Return number of attention heads in multi-head attention.

        Each head operates on D_MODEL / N_HEADS dimensional subspaces. See https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html

        Returns:
            int (positive): Number of attention heads in multi-head attention. Each head operates on D_MODEL / N_HEADS dimensional subspaces. See https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html
        """

        return self._get_field("n_heads")

    @n_heads.setter
    def n_heads(self, value: int) -> None:
        """Set number of attention heads in multi-head attention.

        Args:
            value (int (positive)): Number of attention heads in multi-head attention. Each head operates on D_MODEL / N_HEADS dimensional subspaces. See https://docs.pytorch.org/docs/stable/generated/torch.nn.MultiheadAttention.html
        """
        self._validate_and_set("n_heads", value)

    @property
    def num_encoder_layers(self) -> int:
        """Return number of encoder layers (Transformer blocks) in the encoder stack.

        Deeper models can capture more complex patterns but are slower to train.

        Returns:
            int (positive): Number of encoder layers (Transformer blocks) in the encoder stack. Deeper models can capture more complex patterns but are slower to train.
        """

        return self._get_field("num_encoder_layers")

    @num_encoder_layers.setter
    def num_encoder_layers(self, value: int) -> None:
        """Set number of encoder layers (Transformer blocks) in the encoder stack.

        Args:
            value (int (positive)): Number of encoder layers (Transformer blocks) in the encoder stack. Deeper models can capture more complex patterns but are slower to train.
        """
        self._validate_and_set("num_encoder_layers", value)

    @property
    def num_decoder_layers(self) -> int:
        """Return number of decoder layers (Transformer blocks) in the decoder stack.

        Usually kept equal to NUM_ENCODER_LAYERS for balanced architectures.

        Returns:
            int (positive): Number of decoder layers (Transformer blocks) in the decoder stack. Usually kept equal to NUM_ENCODER_LAYERS for balanced architectures.
        """

        return self._get_field("num_decoder_layers")

    @num_decoder_layers.setter
    def num_decoder_layers(self, value: int) -> None:
        """Set number of decoder layers (Transformer blocks) in the decoder stack.

        Args:
            value (int (positive)): Number of decoder layers (Transformer blocks) in the decoder stack. Usually kept equal to NUM_ENCODER_LAYERS for balanced architectures.
        """
        self._validate_and_set("num_decoder_layers", value)

    @property
    def d_ff(self) -> int:
        """Return Hidden dimension of the feedforward (MLP) layers within each Transformer block.

        Usually 4x D_MODEL. See https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html

        Returns:
            int (positive): Hidden dimension of the feedforward (MLP) layers within each Transformer block. Usually 4x D_MODEL. See https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html
        """

        return self._get_field("d_ff")

    @d_ff.setter
    def d_ff(self, value: int) -> None:
        """Set Hidden dimension of the feedforward (MLP) layers within each Transformer block.

        Args:
            value (int (positive)): Hidden dimension of the feedforward (MLP) layers within each Transformer block. Usually 4x D_MODEL. See https://docs.pytorch.org/docs/stable/generated/torch.nn.TransformerEncoderLayer.html
        """
        self._validate_and_set("d_ff", value)

    @property
    def dropout(self) -> float:
        """Return Dropout probability applied throughout the model (embeddings, feedforward, attention).

        Higher values increase regularization but can slow convergence. See https://docs.pytorch.org/docs/stable/generated/torch.nn.Dropout.html

        Returns:
            float in [0.0, 1.0): Dropout probability applied throughout the model (embeddings, feedforward, attention). Higher values increase regularization but can slow convergence. See https://docs.pytorch.org/docs/stable/generated/torch.nn.Dropout.html
        """

        return self._get_field("dropout")

    @dropout.setter
    def dropout(self, value: float) -> None:
        """Set Dropout probability applied throughout the model (embeddings, feedforward, attention).

        Args:
            value (float in [0.0, 1.0)): Dropout probability applied throughout the model (embeddings, feedforward, attention). Higher values increase regularization but can slow convergence. See https://docs.pytorch.org/docs/stable/generated/torch.nn.Dropout.html
        """
        self._validate_and_set("dropout", value)

    @property
    def max_seq_length(self) -> int:
        """Return Maximum sequence length supported by position encodings (Rotary Embeddings in this codebase).

        Sequences longer than this will be truncated. Increase for longer documents, decrease for faster training.

        Returns:
            int (positive): Maximum sequence length supported by position encodings (Rotary Embeddings in this codebase). Sequences longer than this will be truncated. Increase for longer documents, decrease for faster training.
        """

        return self._get_field("max_seq_length")

    @max_seq_length.setter
    def max_seq_length(self, value: int) -> None:
        """Set Maximum sequence length supported by position encodings (Rotary Embeddings in this codebase).

        Args:
            value (int (positive)): Maximum sequence length supported by position encodings (Rotary Embeddings in this codebase). Sequences longer than this will be truncated. Increase for longer documents, decrease for faster training.
        """
        self._validate_and_set("max_seq_length", value)

    @property
    def lstm_emb_dim(self) -> int:
        """Return embedding dimension for LSTM models.

        Returns:
            int: Embedding dimension for LSTM models.
        """
        return self._get_field("lstm_emb_dim")

    @lstm_emb_dim.setter
    def lstm_emb_dim(self, value: int) -> None:
        """Set embedding dimension for LSTM models.

        Args:
            value (int): Embedding dimension for LSTM models.
        """
        self._validate_and_set("lstm_emb_dim", value)

    @property
    def lstm_hidden_dim(self) -> int:
        """Return hidden dimension for LSTM layers.

        Returns:
            int: Hidden dimension for LSTM layers.
        """
        return self._get_field("lstm_hidden_dim")

    @lstm_hidden_dim.setter
    def lstm_hidden_dim(self, value: int) -> None:
        """Set hidden dimension for LSTM layers.

        Args:
            value (int): Hidden dimension for LSTM layers.
        """
        self._validate_and_set("lstm_hidden_dim", value)

    @property
    def lstm_num_layers(self) -> int:
        """Return number of LSTM layers in encoder and decoder.

        Returns:
            int: Number of LSTM layers in encoder and decoder.
        """
        return self._get_field("lstm_num_layers")

    @lstm_num_layers.setter
    def lstm_num_layers(self, value: int) -> None:
        """Set number of LSTM layers in encoder and decoder.

        Args:
            value (int): Number of LSTM layers in encoder and decoder.
        """
        self._validate_and_set("lstm_num_layers", value)

    @property
    def lstm_dropout(self) -> float:
        """Return dropout rate for LSTM models.

        Returns:
            float: Dropout rate for LSTM models (in range [0.0, 1.0)).
        """
        return self._get_field("lstm_dropout")

    @lstm_dropout.setter
    def lstm_dropout(self, value: float) -> None:
        """Set dropout rate for LSTM models.

        Args:
            value (float): Dropout rate for LSTM models (in range [0.0, 1.0)).
        """
        self._validate_and_set("lstm_dropout", value)

    @property
    def use_packed_projection(self) -> bool:
        """Return Internal optimization flag.

        When True, pack the Query/Key/Value projections in self-attention into a single Linear layer (faster but less flexible). Implementation-specific; may not be used depending on model code.

        Returns:
            bool: Internal optimization flag. When True, pack the Query/Key/Value projections in self-attention into a single Linear layer (faster but less flexible). Implementation-specific; may not be used depending on model code.
        """

        return self._get_field("use_packed_projection")

    @use_packed_projection.setter
    def use_packed_projection(self, value: bool) -> None:
        """Set Internal optimization flag.

        Args:
            value (bool): Internal optimization flag. When True, pack the Query/Key/Value projections in self-attention into a single Linear layer (faster but less flexible). Implementation-specific; may not be used depending on model code.
        """
        self._validate_and_set("use_packed_projection", value)

    @property
    def use_scaled_dot_product_attention(self) -> bool:
        """Return When True, use torch.nn.functional.scaled_dot_product_attention (PyTorch 2.0+) instead of manual attention.

        Can be faster due to kernel fusion. Requires PyTorch >= 2.0. See https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html.

        Returns:
            bool: When True, use torch.nn.functional.scaled_dot_product_attention (PyTorch 2.0+) instead of manual attention. Can be faster due to kernel fusion. Requires PyTorch >= 2.0. See https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html.
        """

        return self._get_field("use_scaled_dot_product_attention")

    @use_scaled_dot_product_attention.setter
    def use_scaled_dot_product_attention(self, value: bool) -> None:
        """Set When True, use torch.nn.functional.scaled_dot_product_attention (PyTorch 2.0+) instead of manual attention.

        Args:
            value (bool): When True, use torch.nn.functional.scaled_dot_product_attention (PyTorch 2.0+) instead of manual attention. Can be faster due to kernel fusion. Requires PyTorch >= 2.0. See https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html.
        """
        self._validate_and_set("use_scaled_dot_product_attention", value)

    @property
    def tie_embeddings(self) -> bool:
        """Return When True, the decoder's embedding matrix is shared with the output projection matrix (reduces parameters).

        Only beneficial if src_vocab_size == tgt_vocab_size.

        Returns:
            bool: When True, the decoder's embedding matrix is shared with the output projection matrix (reduces parameters). Only beneficial if src_vocab_size == tgt_vocab_size.
        """

        return self._get_field("tie_embeddings")

    @tie_embeddings.setter
    def tie_embeddings(self, value: bool) -> None:
        """Set When True, the decoder's embedding matrix is shared with the output projection matrix (reduces parameters).

        Args:
            value (bool): When True, the decoder's embedding matrix is shared with the output projection matrix (reduces parameters). Only beneficial if src_vocab_size == tgt_vocab_size.
        """
        self._validate_and_set("tie_embeddings", value)

    @property
    def use_compile(self) -> bool:
        """Return When True, wrap the model with torch.compile() for JIT compilation (PyTorch 2.0+ only).

        Can provide 20-50% speedup but requires PyTorch 2.0+. See https://pytorch.org/docs/stable/generated/torch.compile.html.

        Returns:
            bool: When True, wrap the model with torch.compile() for JIT compilation (PyTorch 2.0+ only). Can provide 20-50% speedup but requires PyTorch 2.0+. See https://pytorch.org/docs/stable/generated/torch.compile.html.
        """

        return self._get_field("use_compile")

    @use_compile.setter
    def use_compile(self, value: bool) -> None:
        """Set When True, wrap the model with torch.compile() for JIT compilation (PyTorch 2.0+ only).

        Args:
            value (bool): When True, wrap the model with torch.compile() for JIT compilation (PyTorch 2.0+ only). Can provide 20-50% speedup but requires PyTorch 2.0+. See https://pytorch.org/docs/stable/generated/torch.compile.html.
        """
        self._validate_and_set("use_compile", value)

    @property
    def pad_token(self) -> str:
        """Return string representation of the padding token.

        Used to pad sequences to the same length in batches.

        Returns:
            str (token string): String representation of the padding token. Used to pad sequences to the same length in batches.
        """

        return self._get_field("pad_token")

    @pad_token.setter
    def pad_token(self, value: str) -> None:
        """Set string representation of the padding token.

        Args:
            value (str (token string)): String representation of the padding token. Used to pad sequences to the same length in batches.
        """
        self._validate_and_set("pad_token", value)

    @property
    def unk_token(self) -> str:
        """Return string representation of the unknown/out-of-vocabulary token.

        Assigned to words not in the vocabulary.

        Returns:
            str (token string): String representation of the unknown/out-of-vocabulary token. Assigned to words not in the vocabulary.
        """

        return self._get_field("unk_token")

    @unk_token.setter
    def unk_token(self, value: str) -> None:
        """Set string representation of the unknown/out-of-vocabulary token.

        Args:
            value (str (token string)): String representation of the unknown/out-of-vocabulary token. Assigned to words not in the vocabulary.
        """
        self._validate_and_set("unk_token", value)

    @property
    def sos_token(self) -> str:
        """Return start-of-Sequence token.

        Prepended to target sequences during training and decoding to signal the beginning of a sentence.

        Returns:
            str (token string): Start-of-Sequence token. Prepended to target sequences during training and decoding to signal the beginning of a sentence.
        """

        return self._get_field("sos_token")

    @sos_token.setter
    def sos_token(self, value: str) -> None:
        """Set start-of-Sequence token.

        Args:
            value (str (token string)): Start-of-Sequence token. Prepended to target sequences during training and decoding to signal the beginning of a sentence.
        """
        self._validate_and_set("sos_token", value)

    @property
    def eos_token(self) -> str:
        """Return end-of-Sequence token.

        Appended to sequences to signal the end of a sentence. Decoding stops when this token is generated.

        Returns:
            str (token string): End-of-Sequence token. Appended to sequences to signal the end of a sentence. Decoding stops when this token is generated.
        """

        return self._get_field("eos_token")

    @eos_token.setter
    def eos_token(self, value: str) -> None:
        """Set end-of-Sequence token.

        Args:
            value (str (token string)): End-of-Sequence token. Appended to sequences to signal the end of a sentence. Decoding stops when this token is generated.
        """
        self._validate_and_set("eos_token", value)

    @property
    def pad_idx(self) -> int:
        """Return Numeric index for the padding token.

        Used internally by the model and loss function (e.g., ignore_index in CrossEntropyLoss).

        Returns:
            int (non-negative): Numeric index for the padding token. Used internally by the model and loss function (e.g., ignore_index in CrossEntropyLoss).
        """

        return self._get_field("pad_idx")

    @pad_idx.setter
    def pad_idx(self, value: int) -> None:
        """Set Numeric index for the padding token.

        Args:
            value (int (non-negative)): Numeric index for the padding token. Used internally by the model and loss function (e.g., ignore_index in CrossEntropyLoss).
        """
        self._validate_and_set("pad_idx", value)

    @property
    def unk_idx(self) -> int:
        """Return Numeric index for the unknown token.

        Returns:
            int (non-negative): Numeric index for the unknown token.
        """

        return self._get_field("unk_idx")

    @unk_idx.setter
    def unk_idx(self, value: int) -> None:
        """Set Numeric index for the unknown token.

        Args:
            value (int (non-negative)): Numeric index for the unknown token.
        """
        self._validate_and_set("unk_idx", value)

    @property
    def sos_idx(self) -> int:
        """Return Numeric index for the start-of-sequence token.

        Returns:
            int (non-negative): Numeric index for the start-of-sequence token.
        """

        return self._get_field("sos_idx")

    @sos_idx.setter
    def sos_idx(self, value: int) -> None:
        """Set Numeric index for the start-of-sequence token.

        Args:
            value (int (non-negative)): Numeric index for the start-of-sequence token.
        """
        self._validate_and_set("sos_idx", value)

    @property
    def eos_idx(self) -> int:
        """Return Numeric index for the end-of-sequence token.

        Returns:
            int (non-negative): Numeric index for the end-of-sequence token.
        """

        return self._get_field("eos_idx")

    @eos_idx.setter
    def eos_idx(self, value: int) -> None:
        """Set Numeric index for the end-of-sequence token.

        Args:
            value (int (non-negative)): Numeric index for the end-of-sequence token.
        """
        self._validate_and_set("eos_idx", value)

    @property
    def batch_size(self) -> int:
        """Return number of examples per training batch.

        Larger batches update parameters less frequently but use more memory. Smaller batches update more often but can be noisier. Adjust based on GPU memory availability.

        Returns:
            int (positive): Number of examples per training batch. Larger batches update parameters less frequently but use more memory. Smaller batches update more often but can be noisier. Adjust based on GPU memory availability.
        """

        return self._get_field("batch_size")

    @batch_size.setter
    def batch_size(self, value: int) -> None:
        """Set number of examples per training batch.

        Args:
            value (int (positive)): Number of examples per training batch. Larger batches update parameters less frequently but use more memory. Smaller batches update more often but can be noisier. Adjust based on GPU memory availability.
        """
        self._validate_and_set("batch_size", value)

    @property
    def num_steps(self) -> int:
        """Return Total number of training steps (gradient updates).

        One step corresponds to one batch. Can be used by learning rate schedulers and early stopping logic.

        Returns:
            int (positive): Total number of training steps (gradient updates). One step corresponds to one batch. Can be used by learning rate schedulers and early stopping logic.
        """

        return self._get_field("num_steps")

    @num_steps.setter
    def num_steps(self, value: int) -> None:
        """Set Total number of training steps (gradient updates).

        Args:
            value (int (positive)): Total number of training steps (gradient updates). One step corresponds to one batch. Can be used by learning rate schedulers and early stopping logic.
        """
        self._validate_and_set("num_steps", value)

    @property
    def learning_rate(self) -> float:
        """Return Initial learning rate for the Adam optimizer.

        Standard Transformer baseline uses ~1e-4. Too high causes instability; too low causes slow convergence.

        Returns:
            float (positive): Initial learning rate for the Adam optimizer. Standard Transformer baseline uses ~1e-4. Too high causes instability; too low causes slow convergence.
        """

        return self._get_field("learning_rate")

    @learning_rate.setter
    def learning_rate(self, value: float) -> None:
        """Set Initial learning rate for the Adam optimizer.

        Args:
            value (float (positive)): Initial learning rate for the Adam optimizer. Standard Transformer baseline uses ~1e-4. Too high causes instability; too low causes slow convergence.
        """
        self._validate_and_set("learning_rate", value)

    @property
    def adam_betas(self) -> tuple:
        """Return (beta1, beta2) momentum coefficients for the Adam optimizer.

        See https://pytorch.org/docs/stable/generated/torch.optim.Adam.html beta1 (default 0.9) = exponential decay rate for 1st moment. beta2 (default 0.999) = exponential decay rate for 2nd moment.

        Returns:
            (float, float): (beta1, beta2) momentum coefficients for the Adam optimizer. See https://pytorch.org/docs/stable/generated/torch.optim.Adam.html beta1 (default 0.9) = exponential decay rate for 1st moment. beta2 (default 0.999) = exponential decay rate for 2nd moment.
        """

        return self._get_field("adam_betas")

    @adam_betas.setter
    def adam_betas(self, value: tuple) -> None:
        """Set (beta1, beta2) momentum coefficients for the Adam optimizer.

        Args:
            value ((float, float)): (beta1, beta2) momentum coefficients for the Adam optimizer. See https://pytorch.org/docs/stable/generated/torch.optim.Adam.html beta1 (default 0.9) = exponential decay rate for 1st moment. beta2 (default 0.999) = exponential decay rate for 2nd moment.
        """
        self._validate_and_set("adam_betas", value)

    @property
    def adam_eps(self) -> float:
        """Return Small constant added to the denominator in Adam to avoid division by zero.

        See https://pytorch.org/docs/stable/generated/torch.optim.Adam.html.

        Returns:
            float (small positive): Small constant added to the denominator in Adam to avoid division by zero. See https://pytorch.org/docs/stable/generated/torch.optim.Adam.html.
        """

        return self._get_field("adam_eps")

    @adam_eps.setter
    def adam_eps(self, value: float) -> None:
        """Set Small constant added to the denominator in Adam to avoid division by zero.

        Args:
            value (float (small positive)): Small constant added to the denominator in Adam to avoid division by zero. See https://pytorch.org/docs/stable/generated/torch.optim.Adam.html.
        """
        self._validate_and_set("adam_eps", value)

    @property
    def warmup_steps(self) -> int:
        """Return number of steps for learning rate warmup schedule.

        Learning rate increases linearly from 0 to LEARNING_RATE over WARMUP_STEPS, then decays. Set to 0 to disable warmup.

        Returns:
            int (non-negative): Number of steps for learning rate warmup schedule. Learning rate increases linearly from 0 to LEARNING_RATE over WARMUP_STEPS, then decays. Set to 0 to disable warmup.
        """

        return self._get_field("warmup_steps")

    @warmup_steps.setter
    def warmup_steps(self, value: int) -> None:
        """Set number of steps for learning rate warmup schedule.

        Args:
            value (int (non-negative)): Number of steps for learning rate warmup schedule. Learning rate increases linearly from 0 to LEARNING_RATE over WARMUP_STEPS, then decays. Set to 0 to disable warmup.
        """
        self._validate_and_set("warmup_steps", value)

    @property
    def label_smoothing(self) -> float:
        """Return Label smoothing hyperparameter for cross-entropy loss.

        Prevents the model from becoming overconfident. See https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html.

        Returns:
            float in [0.0, 1.0): Label smoothing hyperparameter for cross-entropy loss. Prevents the model from becoming overconfident. See https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html.
        """

        return self._get_field("label_smoothing")

    @label_smoothing.setter
    def label_smoothing(self, value: float) -> None:
        """Set Label smoothing hyperparameter for cross-entropy loss.

        Args:
            value (float in [0.0, 1.0)): Label smoothing hyperparameter for cross-entropy loss. Prevents the model from becoming overconfident. See https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html.
        """
        self._validate_and_set("label_smoothing", value)

    @property
    def use_bucketing(self) -> bool:
        """Return When True, group examples by length into buckets to reduce padding overhead during training.

        Requires a custom sampler implementation.

        Returns:
            bool: When True, group examples by length into buckets to reduce padding overhead during training. Requires a custom sampler implementation.
        """

        return self._get_field("use_bucketing")

    @use_bucketing.setter
    def use_bucketing(self, value: bool) -> None:
        """Set When True, group examples by length into buckets to reduce padding overhead during training.

        Args:
            value (bool): When True, group examples by length into buckets to reduce padding overhead during training. Requires a custom sampler implementation.
        """
        self._validate_and_set("use_bucketing", value)

    @property
    def bucket_boundaries(self) -> Optional[list]:
        """Return Length boundaries for bucketing.

        Only used if USE_BUCKETING=True.

        Returns:
            None or list of ints (sorted, increasing): Length boundaries for bucketing. Only used if USE_BUCKETING=True.
        """

        return self._get_field("bucket_boundaries")

    @bucket_boundaries.setter
    def bucket_boundaries(self, value: Optional[list]) -> None:
        """Set Length boundaries for bucketing.

        Args:
            value (None or list of ints (sorted, increasing)): Length boundaries for bucketing. Only used if USE_BUCKETING=True.
        """
        self._validate_and_set("bucket_boundaries", value)

    @property
    def grad_clip(self) -> Optional[float]:
        """Return Max norm for gradient clipping.

        Prevents exploding gradients. Applied via torch.nn.utils.clip_grad_norm_. Set to 0 or None to disable. See https://pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html.

        Returns:
            float (non-negative): Max norm for gradient clipping. Prevents exploding gradients. Applied via torch.nn.utils.clip_grad_norm_. Set to 0 or None to disable. See https://pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html.
        """

        return self._get_field("grad_clip")

    @grad_clip.setter
    def grad_clip(self, value: Optional[float]) -> None:
        """Set Max norm for gradient clipping.

        Args:
            value (float (non-negative)): Max norm for gradient clipping. Prevents exploding gradients. Applied via torch.nn.utils.clip_grad_norm_. Set to 0 or None to disable. See https://pytorch.org/docs/stable/generated/torch.nn.utils.clip_grad_norm_.html.
        """
        self._validate_and_set("grad_clip", value)

    @property
    def val_interval(self) -> int:
        """Return number of training steps between validation evaluations.

        Validation loss is computed on VAL_FILE every VAL_INTERVAL steps.

        Returns:
            int (positive): Number of training steps between validation evaluations. Validation loss is computed on VAL_FILE every VAL_INTERVAL steps.
        """

        return self._get_field("val_interval")

    @val_interval.setter
    def val_interval(self, value: int) -> None:
        """Set number of training steps between validation evaluations.

        Args:
            value (int (positive)): Number of training steps between validation evaluations. Validation loss is computed on VAL_FILE every VAL_INTERVAL steps.
        """
        self._validate_and_set("val_interval", value)

    @property
    def save_interval(self) -> int:
        """Return number of training steps between checkpoint saves.

        Model checkpoints are saved every SAVE_INTERVAL steps.

        Returns:
            int (positive): Number of training steps between checkpoint saves. Model checkpoints are saved every SAVE_INTERVAL steps.
        """

        return self._get_field("save_interval")

    @save_interval.setter
    def save_interval(self, value: int) -> None:
        """Set number of training steps between checkpoint saves.

        Args:
            value (int (positive)): Number of training steps between checkpoint saves. Model checkpoints are saved every SAVE_INTERVAL steps.
        """
        self._validate_and_set("save_interval", value)

    @property
    def log_interval(self) -> int:
        """Return number of training steps between logging of training metrics (e.g., loss, perplexity).

        Logged to console and TensorBoard if enabled.

        Returns:
            int (positive): Number of training steps between logging of training metrics (e.g., loss, perplexity). Logged to console and TensorBoard if enabled.
        """

        return self._get_field("log_interval")

    @log_interval.setter
    def log_interval(self, value: int) -> None:
        """Set number of training steps between logging of training metrics (e.g., loss, perplexity).

        Args:
            value (int (positive)): Number of training steps between logging of training metrics (e.g., loss, perplexity). Logged to console and TensorBoard if enabled.
        """
        self._validate_and_set("log_interval", value)

    @property
    def patience(self) -> int:
        """Return number of validation intervals (each VAL_INTERVAL steps) to wait for validation loss improvement before early stopping.

        Set to a large number to effectively disable early stopping.

        Returns:
            int (positive): Number of validation intervals (each VAL_INTERVAL steps) to wait for validation loss improvement before early stopping. Set to a large number to effectively disable early stopping.
        """

        return self._get_field("patience")

    @patience.setter
    def patience(self, value: int) -> None:
        """Set number of validation intervals (each VAL_INTERVAL steps) to wait for validation loss improvement before early stopping.

        Args:
            value (int (positive)): Number of validation intervals (each VAL_INTERVAL steps) to wait for validation loss improvement before early stopping. Set to a large number to effectively disable early stopping.
        """
        self._validate_and_set("patience", value)

    @property
    def checkpoint_path(self) -> Path:
        """Return path to save the best model checkpoint (lowest validation loss).

        Returns:
            Path object: Path to save the best model checkpoint (lowest validation loss).
        """

        return self._get_field("checkpoint_path")

    @checkpoint_path.setter
    def checkpoint_path(self, value: Path) -> None:
        """Set path to save the best model checkpoint (lowest validation loss).

        Args:
            value (Path object): Path to save the best model checkpoint (lowest validation loss).
        """
        self._validate_and_set("checkpoint_path", value)

    @property
    def last_checkpoint_path(self) -> Path:
        """Return path to save the most recent model checkpoint (for resuming training).

        Returns:
            Path object: Path to save the most recent model checkpoint (for resuming training).
        """

        return self._get_field("last_checkpoint_path")

    @last_checkpoint_path.setter
    def last_checkpoint_path(self, value: Path) -> None:
        """Set path to save the most recent model checkpoint (for resuming training).

        Args:
            value (Path object): Path to save the most recent model checkpoint (for resuming training).
        """
        self._validate_and_set("last_checkpoint_path", value)

    @property
    def beam_size(self) -> int:
        """Return Beam width for beam search decoding.

        Larger values explore more hypotheses (better quality but slower). Set to 1 for greedy decoding.

        Returns:
            int (positive): Beam width for beam search decoding. Larger values explore more hypotheses (better quality but slower). Set to 1 for greedy decoding.
        """

        return self._get_field("beam_size")

    @beam_size.setter
    def beam_size(self, value: int) -> None:
        """Set Beam width for beam search decoding.

        Args:
            value (int (positive)): Beam width for beam search decoding. Larger values explore more hypotheses (better quality but slower). Set to 1 for greedy decoding.
        """
        self._validate_and_set("beam_size", value)

    @property
    def max_decode_length(self) -> int:
        """Return Maximum number of tokens to generate during decoding.

        Acts as a safety cap to prevent generating extremely long sequences.

        Returns:
            int (positive): Maximum number of tokens to generate during decoding. Acts as a safety cap to prevent generating extremely long sequences.
        """

        return self._get_field("max_decode_length")

    @max_decode_length.setter
    def max_decode_length(self, value: int) -> None:
        """Set Maximum number of tokens to generate during decoding.

        Args:
            value (int (positive)): Maximum number of tokens to generate during decoding. Acts as a safety cap to prevent generating extremely long sequences.
        """
        self._validate_and_set("max_decode_length", value)

    @property
    def length_penalty(self) -> float:
        """Return Length penalty exponent in beam search scoring.

        Higher values favor shorter translations. A penalty of 0.0 = no length bias; 1.0 = linear length normalization.

        Returns:
            float (non-negative): Length penalty exponent in beam search scoring. Higher values favor shorter translations. A penalty of 0.0 = no length bias; 1.0 = linear length normalization.
        """

        return self._get_field("length_penalty")

    @length_penalty.setter
    def length_penalty(self, value: float) -> None:
        """Set Length penalty exponent in beam search scoring.

        Args:
            value (float (non-negative)): Length penalty exponent in beam search scoring. Higher values favor shorter translations. A penalty of 0.0 = no length bias; 1.0 = linear length normalization.
        """
        self._validate_and_set("length_penalty", value)

    @property
    def use_greedy(self) -> bool:
        """Return When True, force greedy decoding (take the highest-probability token at each step) regardless of BEAM_SIZE.

        Useful for faster inference at the cost of translation quality.

        Returns:
            bool: When True, force greedy decoding (take the highest-probability token at each step) regardless of BEAM_SIZE. Useful for faster inference at the cost of translation quality.
        """

        return self._get_field("use_greedy")

    @use_greedy.setter
    def use_greedy(self, value: bool) -> None:
        """Set When True, force greedy decoding (take the highest-probability token at each step) regardless of BEAM_SIZE.

        Args:
            value (bool): When True, force greedy decoding (take the highest-probability token at each step) regardless of BEAM_SIZE. Useful for faster inference at the cost of translation quality.
        """
        self._validate_and_set("use_greedy", value)

    @property
    def output_translations(self) -> Path:
        """Return path where translated output sentences are written by translate.py.

        One translation per line.

        Returns:
            Path object: Path where translated output sentences are written by translate.py. One translation per line.
        """

        return self._get_field("output_translations")

    @output_translations.setter
    def output_translations(self, value: Path) -> None:
        """Set path where translated output sentences are written by translate.py.

        Args:
            value (Path object): Path where translated output sentences are written by translate.py. One translation per line.
        """
        self._validate_and_set("output_translations", value)

    @property
    def output_scores(self) -> Path:
        """Return path where translation quality scores (e.g., BLEU) are written.

        Returns:
            Path object: Path where translation quality scores (e.g., BLEU) are written.
        """

        return self._get_field("output_scores")

    @output_scores.setter
    def output_scores(self, value: Path) -> None:
        """Set path where translation quality scores (e.g., BLEU) are written.

        Args:
            value (Path object): Path where translation quality scores (e.g., BLEU) are written.
        """
        self._validate_and_set("output_scores", value)

    @property
    def device(self) -> Any:
        """Return Which device to run computation on.

        "cuda" for NVIDIA GPUs, "cpu" for CPU-only. Multi-GPU training requires custom DataParallel setup.

        Returns:
            str or torch.device object: Which device to run computation on. "cuda" for NVIDIA GPUs, "cpu" for CPU-only. Multi-GPU training requires custom DataParallel setup.
        """

        return self._get_field("device")

    @device.setter
    def device(self, value: Any) -> None:
        """Set Which device to run computation on.

        Args:
            value (str or torch.device object): Which device to run computation on. "cuda" for NVIDIA GPUs, "cpu" for CPU-only. Multi-GPU training requires custom DataParallel setup.
        """
        self._validate_and_set("device", value)

    @property
    def num_workers(self) -> int:
        """Return number of worker processes for data loading in DataLoader.

        0 = load data in main thread (safer, easier to debug). >0 = spawn subprocesses (faster on multi-core machines). See https://pytorch.org/docs/stable/data.html#torch.utils.data.DataLoader.

        Returns:
            int (non-negative): Number of worker processes for data loading in DataLoader. 0 = load data in main thread (safer, easier to debug). >0 = spawn subprocesses (faster on multi-core machines). See https://pytorch.org/docs/stable/data.html#torch.utils.data.DataLoader.
        """

        return self._get_field("num_workers")

    @num_workers.setter
    def num_workers(self, value: int) -> None:
        """Set number of worker processes for data loading in DataLoader.

        Args:
            value (int (non-negative)): Number of worker processes for data loading in DataLoader. 0 = load data in main thread (safer, easier to debug). >0 = spawn subprocesses (faster on multi-core machines). See https://pytorch.org/docs/stable/data.html#torch.utils.data.DataLoader.
        """
        self._validate_and_set("num_workers", value)

    @property
    def seed(self) -> int:
        """Return Random seed for reproducibility.

        Set RNGs (torch, numpy, random) at the start of training. Different seeds may yield slightly different results due to floating-point nondeterminism and thread timing.

        Returns:
            int (any non-negative integer): Random seed for reproducibility. Set RNGs (torch, numpy, random) at the start of training. Different seeds may yield slightly different results due to floating-point nondeterminism and thread timing.
        """

        return self._get_field("seed")

    @seed.setter
    def seed(self, value: int) -> None:
        """Set Random seed for reproducibility.

        Args:
            value (int (any non-negative integer)): Random seed for reproducibility. Set RNGs (torch, numpy, random) at the start of training. Different seeds may yield slightly different results due to floating-point nondeterminism and thread timing.
        """
        self._validate_and_set("seed", value)

    @property
    def train_ratio(self) -> float:
        """Return fraction of data used for training split.

        Returns:
            float: Fraction of data used for training split (0.0, 1.0).
        """
        return self._get_field("train_ratio")

    @train_ratio.setter
    def train_ratio(self, value: float) -> None:
        """Set fraction of data used for training split.

        Args:
            value (float): Fraction of data used for training split (0.0, 1.0).
        """
        self._validate_and_set("train_ratio", value)

    @property
    def val_ratio(self) -> float:
        """Return fraction of data used for validation split.

        Returns:
            float: Fraction of data used for validation split (0.0, 1.0).
        """
        return self._get_field("val_ratio")

    @val_ratio.setter
    def val_ratio(self, value: float) -> None:
        """Set fraction of data used for validation split.

        Args:
            value (float): Fraction of data used for validation split (0.0, 1.0).
        """
        self._validate_and_set("val_ratio", value)

    @property
    def use_tensorboard(self) -> bool:
        """Return When True, log training metrics (loss, learning rate, etc.) to TensorBoard.

        Requires torch.utils.tensorboard.SummaryWriter. View logs with: tensorboard --logdir <TENSORBOARD_DIR>.

        Returns:
            bool: When True, log training metrics (loss, learning rate, etc.) to TensorBoard. Requires torch.utils.tensorboard.SummaryWriter. View logs with: tensorboard --logdir <TENSORBOARD_DIR>.
        """

        return self._get_field("use_tensorboard")

    @use_tensorboard.setter
    def use_tensorboard(self, value: bool) -> None:
        """Set When True, log training metrics (loss, learning rate, etc.) to TensorBoard.

        Args:
            value (bool): When True, log training metrics (loss, learning rate, etc.) to TensorBoard. Requires torch.utils.tensorboard.SummaryWriter. View logs with: tensorboard --logdir <TENSORBOARD_DIR>.
        """
        self._validate_and_set("use_tensorboard", value)

    @property
    def tensorboard_dir(self) -> Path:
        """Return directory where TensorBoard event files are written.

        Returns:
            Path object: Directory where TensorBoard event files are written.
        """

        return self._get_field("tensorboard_dir")

    @tensorboard_dir.setter
    def tensorboard_dir(self, value: Path) -> None:
        """Set directory where TensorBoard event files are written.

        Args:
            value (Path object): Directory where TensorBoard event files are written.
        """
        self._validate_and_set("tensorboard_dir", value)

    @property
    def experiment_name(self) -> str:
        """Return human-readable name for the experiment.

        Used in log filenames, checkpoint names, and experiment tracking. Change this for each new experiment.

        Returns:
            str (short identifier): Human-readable name for the experiment. Used in log filenames, checkpoint names, and experiment tracking. Change this for each new experiment.
        """

        return self._get_field("experiment_name")

    @experiment_name.setter
    def experiment_name(self, value: str) -> None:
        """Set human-readable name for the experiment.

        Args:
            value (str (short identifier)): Human-readable name for the experiment. Used in log filenames, checkpoint names, and experiment tracking. Change this for each new experiment.
        """
        self._validate_and_set("experiment_name", value)


_default_config = Config()


def get_default_config() -> Config:
    """Return a new Config object initialized with module-level defaults.

    For experiments that require isolated configs, this function now returns
    a fresh instance each call, seeded from the current module-level values.

    Returns:
        A new Config instance.
    """
    return _default_config.copy()


def get_config_dict() -> Dict[str, Any]:
    """Return all configuration as a dictionary for logging and display.

    Only returns top-level UPPERCASE names to avoid leaking modules or
    callables into log output. Uses the default config.

    Returns:
        Dictionary of all configuration parameters.
    """
    return {k: v for k, v in globals().items() if not k.startswith("_") and k.isupper()}


def print_config() -> None:
    """Pretty-print the default configuration for quick inspection.

    Useful to call at the start of experiments so logs capture the exact
    configuration used.
    """
    _default_config.print()
