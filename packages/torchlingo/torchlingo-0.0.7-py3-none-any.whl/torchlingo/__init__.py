"""Top-level package for TorchLingo.

This package exposes the core modules (config, models, data_processing,
preprocessing) so codebases/tests can import `torchlingo` rather than top-level
module names. It mirrors the project layout used in the repository.
"""

__version__ = "0.0.7"

from . import config
from . import models
from . import data_processing
from . import preprocessing
from . import training
from . import inference

__all__ = [
    "__version__",
    "config",
    "models",
    "data_processing",
    "preprocessing",
    "training",
    "inference",
]
