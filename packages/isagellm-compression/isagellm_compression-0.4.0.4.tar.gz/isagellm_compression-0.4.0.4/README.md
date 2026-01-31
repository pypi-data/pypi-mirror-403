# sagellm-compression

## Protocol Compliance (Mandatory)

- MUST follow Protocol v0.1: https://github.com/intellistream/sagellm-docs/blob/main/docs/specs/protocol_v0.1.md
- Any globally shared definitions (fields, error codes, metrics, IDs, schemas) MUST be added to Protocol first.

[![CI](https://github.com/intellistream/sagellm-compression/actions/workflows/ci.yml/badge.svg)](https://github.com/intellistream/sagellm-compression/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/isagellm-compression.svg)](https://badge.fury.io/py/isagellm-compression)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/intellistream/sagellm-compression/branch/main/graph/badge.svg)](https://codecov.io/gh/intellistream/sagellm-compression)

Inference acceleration tools for LLM: quantization, sparsity, speculative decoding, kernel fusion, and more.

## Features

- Quantization (INT8/INT4)
- Sparsity (structured and unstructured pruning)
- Speculative decoding
- Kernel fusion
- Chain-of-Thought acceleration

## Installation

```bash
pip install isagellm-compression
```

## Quick Start

```python
from sagellm_compression import QuantizationConfig, apply_quantization

config = QuantizationConfig(method="int8", per_channel=True)
quantized_model = apply_quantization(model, config)
```

## Development

```bash
git clone git@github.com:intellistream/sagellm-compression.git
cd sagellm-compression
./quickstart.sh

pip install -e ".[dev]"
pytest tests/ -v
```

## Documentation

- [docs/](docs/)

## License

Private - IntelliStream Research Project
