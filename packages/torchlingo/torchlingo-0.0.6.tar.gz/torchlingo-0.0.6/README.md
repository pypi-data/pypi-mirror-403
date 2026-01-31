# TorchLingo

[![PyPI version](https://img.shields.io/pypi/v/torchlingo.svg?color=0073b7)](https://pypi.org/project/torchlingo/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.en.html)

**TorchLingo** is an educational PyTorch library for Neural Machine Translation (NMT). Designed for students and instructors, it provides a clean, well-documented implementation of the Transformer architecture for learning and experimentation.

## Features

- 🎓 **Educational Focus**: Clean, readable code designed for learning
- 🔄 **Transformer Architecture**: Full encoder-decoder implementation with multi-head attention
- 📝 **SentencePiece Tokenization**: BPE and Unigram subword models
- 🔁 **Back-Translation**: Data augmentation for improved translation quality
- 🌍 **Multilingual Support**: Train a single model for multiple language pairs
- 📊 **TensorBoard Integration**: Monitor training progress in real-time

## Installation

```bash
pip install torchlingo
```

For development:

```bash
pip install torchlingo[dev]
```

## Documentation

For full documentation, tutorials, and API reference, visit:
- [Getting Started Guide](https://byu-matrix-lab.github.io/torchlingo/getting-started/installation/)
- [API Reference](https://byu-matrix-lab.github.io/torchlingo/reference/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

This project was initially developed by [Josh Christensen](https://josh.christen.se) as part of his undergraduate work at BYU.

> *"I hope that TorchLingo will be a valuable resource for students learning about neural machine translation, and that they will consider improving this project and the entire world with the knowledge they gain."*  
> — Josh Christensen