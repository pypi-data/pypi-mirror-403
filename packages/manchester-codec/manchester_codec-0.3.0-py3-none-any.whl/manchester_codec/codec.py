from __future__ import annotations

from enum import Enum
from typing import Iterable, Iterator, List, Sequence, Tuple, Union

Bit = int
BitInput = Union[int, bool, str]
ByteLike = Union[bytes, bytearray, memoryview]


class ManchesterEncodingError(ValueError):
    """Raised when encoding or decoding fails because of invalid input."""


class ManchesterStandard(str, Enum):
    """Supported Manchester line coding conventions."""

    IEEE = "ieee"
    THOMAS = "thomas"

    @classmethod
    def coerce(cls, value: Union["ManchesterStandard", str]) -> "ManchesterStandard":
        if isinstance(value, cls):
            return value
        lowered = str(value).strip().lower()
        for member in cls:
            if member.value == lowered:
                return member
        raise ManchesterEncodingError(f"Unsupported Manchester standard: {value!r}")


_ENCODE_TABLE = {
    ManchesterStandard.IEEE: {0: (1, 0), 1: (0, 1)},
    ManchesterStandard.THOMAS: {0: (0, 1), 1: (1, 0)},
}

_DECODE_TABLE = {
    standard: {pair: bit for bit, pair in mapping.items()}
    for standard, mapping in _ENCODE_TABLE.items()
}


def encode_bits(
    bits: Iterable[BitInput],
    *,
    standard: Union[ManchesterStandard, str] = ManchesterStandard.IEEE,
) -> List[Bit]:
    """
    Encode a sequence of bits into Manchester symbols.

    Args:
        bits: Iterable containing bool/int bits or a string of 0s and 1s.
        standard: Either ``"ieee"`` or ``"thomas"``.

    Returns:
        List of Manchester-encoded bits where each input bit expands to two
        output bits.
    """
    normalized_bits = _normalize_bits(bits)
    standard_enum = ManchesterStandard.coerce(standard)
    mapping = _ENCODE_TABLE[standard_enum]
    encoded: List[Bit] = []
    for bit in normalized_bits:
        encoded.extend(mapping[bit])
    return encoded


def decode_bits(
    encoded_bits: Sequence[BitInput],
    *,
    standard: Union[ManchesterStandard, str] = ManchesterStandard.IEEE,
) -> List[Bit]:
    """
    Decode a Manchester-encoded sequence.

    Args:
        encoded_bits: Pairwise Manchester symbols (ints, bools, or string).
        standard: Either ``"ieee"`` or ``"thomas"``.

    Returns:
        List with the decoded binary sequence.
    """
    normalized = _normalize_bits(encoded_bits)
    if len(normalized) % 2 != 0:
        raise ManchesterEncodingError("Manchester stream length must be even")

    standard_enum = ManchesterStandard.coerce(standard)
    reverse_map = _DECODE_TABLE[standard_enum]
    decoded: List[Bit] = []
    for i in range(0, len(normalized), 2):
        pair = (normalized[i], normalized[i + 1])
        bit = reverse_map.get(pair)
        if bit is None:
            raise ManchesterEncodingError(
                f"Invalid symbol pair {pair} for {standard_enum.value} Manchester coding"
            )
        decoded.append(bit)
    return decoded


def encode_bytes(
    data: ByteLike,
    *,
    standard: Union[ManchesterStandard, str] = ManchesterStandard.IEEE,
    msb_first: bool = True,
) -> bytes:
    """
    Encode a byte payload.

    Args:
        data: Raw bytes.
        standard: Encoding variant.
        msb_first: Whether to treat the MSB as the first bit when unpacking.
    """
    bits = bits_from_bytes(data, msb_first=msb_first)
    encoded = encode_bits(bits, standard=standard)
    return bits_to_bytes(encoded, msb_first=msb_first)


def decode_bytes(
    encoded_bytes: ByteLike,
    *,
    standard: Union[ManchesterStandard, str] = ManchesterStandard.IEEE,
    msb_first: bool = True,
) -> bytes:
    """
    Decode a Manchester-encoded byte payload.

    Args:
        encoded_bytes: Manchester symbols represented as packed bytes.
        standard: Encoding variant.
        msb_first: Whether to interpret MSB-first when packing decoded bits.
    """
    bits = bits_from_bytes(encoded_bytes, msb_first=msb_first)
    decoded = decode_bits(bits, standard=standard)
    return bits_to_bytes(decoded, msb_first=msb_first)


def bits_from_bytes(data: ByteLike, *, msb_first: bool = True) -> List[Bit]:
    """Expand a bytes-like payload into individual bits."""
    byte_data = bytes(data)
    bit_list: List[Bit] = []
    for byte in byte_data:
        shifts = range(7, -1, -1) if msb_first else range(8)
        for shift in shifts:
            bit = (byte >> shift) & 1
            bit_list.append(bit)
    return bit_list


def bits_to_bytes(bits: Iterable[BitInput], *, msb_first: bool = True) -> bytes:
    """Pack a bit sequence into bytes."""
    normalized = _normalize_bits(bits)
    if len(normalized) % 8 != 0:
        raise ManchesterEncodingError("Bit sequence length must be a multiple of 8")

    shifts = range(7, -1, -1) if msb_first else range(8)
    shift_order = list(shifts)

    output = bytearray()
    for chunk_start in range(0, len(normalized), 8):
        chunk = normalized[chunk_start : chunk_start + 8]
        value = 0
        for bit, shift in zip(chunk, shift_order):
            value |= bit << shift
        output.append(value)
    return bytes(output)


def _normalize_bits(bits: Iterable[BitInput]) -> List[Bit]:
    normalized: List[Bit] = []
    iterator = _iterate_bits(bits)
    for value in iterator:
        if isinstance(value, bool):
            normalized.append(int(value))
            continue
        if isinstance(value, int):
            if value not in (0, 1):
                raise ManchesterEncodingError(f"Invalid bit value: {value!r}")
            normalized.append(value)
            continue
        raise ManchesterEncodingError(f"Invalid bit value: {value!r}")
    return normalized


def _iterate_bits(bits: Iterable[BitInput]) -> Iterator[BitInput]:
    if isinstance(bits, str):
        for char in bits:
            if char in " \t\r\n_":
                continue
            if char not in "01":
                raise ManchesterEncodingError(f"Invalid bit character: {char!r}")
            yield int(char)
        return
    if isinstance(bits, (bytes, bytearray, memoryview)):
        raise ManchesterEncodingError(
            "Byte sequences are not allowed here; use bits_from_bytes or encode_bytes."
        )
    for value in bits:
        yield value
