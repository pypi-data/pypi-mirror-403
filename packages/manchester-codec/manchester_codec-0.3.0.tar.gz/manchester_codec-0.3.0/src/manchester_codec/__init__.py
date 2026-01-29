"""Manchester coding helpers for IEEE and Thomas variants."""

from .codec import (
    ManchesterEncodingError,
    ManchesterStandard,
    bits_from_bytes,
    bits_to_bytes,
    decode_bits,
    decode_bytes,
    encode_bits,
    encode_bytes,
)

__all__ = [
    "ManchesterEncodingError",
    "ManchesterStandard",
    "encode_bits",
    "decode_bits",
    "encode_bytes",
    "decode_bytes",
    "bits_from_bytes",
    "bits_to_bytes",
]

__version__ = "0.1.0"
