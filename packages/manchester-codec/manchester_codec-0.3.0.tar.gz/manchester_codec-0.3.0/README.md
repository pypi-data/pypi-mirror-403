# manchester_codec

Manchester line coding utilities with first-class support for the IEEE 802.3 and G.E. Thomas variants. The library exposes predictable helpers for bit-level and byte-level workflows so it can be embedded inside larger communication stacks or used interactively for quick experiments.

## Features

- Encode or decode Manchester symbols with a single function call.
- Supports both IEEE (low→high transition represents `1`) and Thomas (high→low represents `1`) conventions.
- Helper utilities to convert between bit sequences and byte payloads.
- Fully typed, documented, and covered by tests to make PyPI publishing straightforward.

## Installation

```bash
pip install manchester_codec
```

Until the project is uploaded to PyPI you can install it from a local checkout:

```bash
pip install .
```

## Usage

```python
from manchester_codec import (
    ManchesterStandard,
    encode_bits,
    decode_bits,
    encode_bytes,
    decode_bytes,
)

data_bits = "10110011"
encoded = encode_bits(data_bits, standard=ManchesterStandard.IEEE)
decoded = decode_bits(encoded, standard="ieee")  # standard can also be a string
assert "".join(str(bit) for bit in decoded) == data_bits

payload = bytes.fromhex("a5")
encoded_bytes = encode_bytes(payload, standard="thomas")
decoded_bytes = decode_bytes(encoded_bytes, standard="thomas")
assert decoded_bytes == payload
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .[dev]
pytest
```

## Additional resources

- Documentation & tutorials: https://github.com/eneserginth/manchester_codec
- Project homepage: https://www.fevaris.com

## License

MIT License. See `LICENSE` for details.
