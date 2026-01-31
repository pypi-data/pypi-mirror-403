"""Model package aggregating available architectures for the torchlingo package.

Exposes a factory `get_model(name, **kwargs)` to instantiate models.
"""

from .transformer_simple import SimpleTransformer
from .lstm_simple import SimpleSeq2SeqLSTM

_MODEL_MAP = {
    "transformer_simple": SimpleTransformer,
    "lstm_simple": SimpleSeq2SeqLSTM,
}


def get_model(name: str, **kwargs):
    if name not in _MODEL_MAP:
        raise ValueError(
            f"Unknown model '{name}'. Available: {list(_MODEL_MAP.keys())}"
        )
    return _MODEL_MAP[name](**kwargs)


__all__ = ["SimpleTransformer", "SimpleSeq2SeqLSTM", "get_model"]
