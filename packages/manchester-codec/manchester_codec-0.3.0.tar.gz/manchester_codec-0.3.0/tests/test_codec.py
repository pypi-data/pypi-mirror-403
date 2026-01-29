import pytest

from manchester_codec import (
    ManchesterEncodingError,
    ManchesterStandard,
    bits_from_bytes,
    bits_to_bytes,
    decode_bits,
    decode_bytes,
    encode_bits,
    encode_bytes,
)


@pytest.mark.parametrize(
    "standard,bits,expected",
    [
        (ManchesterStandard.IEEE, [1, 0, 1], [0, 1, 1, 0, 0, 1]),
        ("thomas", [1, 0, 1], [1, 0, 0, 1, 1, 0]),
    ],
)
def test_encode_bits(standard, bits, expected):
    assert encode_bits(bits, standard=standard) == expected


@pytest.mark.parametrize(
    "standard,encoded,expected",
    [
        (ManchesterStandard.IEEE, [0, 1, 1, 0, 0, 1], [1, 0, 1]),
        ("thomas", [1, 0, 0, 1, 1, 0], [1, 0, 1]),
    ],
)
def test_decode_bits(standard, encoded, expected):
    assert decode_bits(encoded, standard=standard) == expected


def test_round_trip_bytes():
    payload = bytes.fromhex("deadbeef")
    for standard in (ManchesterStandard.IEEE, ManchesterStandard.THOMAS):
        encoded = encode_bytes(payload, standard=standard)
        decoded = decode_bytes(encoded, standard=standard)
        assert decoded == payload


def test_bits_converters():
    payload = bytes([0b10100101])
    bits = bits_from_bytes(payload)
    assert bits == [1, 0, 1, 0, 0, 1, 0, 1]
    rebuilt = bits_to_bytes(bits)
    assert rebuilt == payload


def test_decode_invalid_pair():
    with pytest.raises(ManchesterEncodingError):
        decode_bits([0, 0], standard="ieee")


def test_bits_to_bytes_requires_full_bytes():
    with pytest.raises(ManchesterEncodingError):
        bits_to_bytes([1, 0, 1])


def test_encode_bits_rejects_bytes_like_sequence():
    with pytest.raises(ManchesterEncodingError):
        encode_bits(b"01")
