"""
xor_delta package public API.
"""

from .xor_delta import (
    XorDeltaEncoded,
    xor_delta_decode_bytes,
    xor_delta_decode_ints,
    xor_delta_encode_bytes,
    xor_delta_encode_ints,
)

__all__ = [
    "XorDeltaEncoded",
    "xor_delta_encode_ints",
    "xor_delta_decode_ints",
    "xor_delta_encode_bytes",
    "xor_delta_decode_bytes",
]
