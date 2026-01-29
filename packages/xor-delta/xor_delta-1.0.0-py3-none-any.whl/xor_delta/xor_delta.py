from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Sequence

AnchorSide = Literal["first", "last"]


@dataclass(frozen=True, slots=True)
class XorDeltaEncoded:
    anchor: int
    diffs: List[int]
    anchor_side: AnchorSide


def xor_delta_encode_ints(values: Sequence[int], *, anchor_side: AnchorSide = "first") -> XorDeltaEncoded:
    if not values:
        raise ValueError("values must be non-empty")
    if any(v < 0 for v in values):
        raise ValueError("values must be non-negative")
    if anchor_side not in ("first", "last"):
        raise ValueError("invalid anchor_side")

    diffs = [values[i] ^ values[i + 1] for i in range(len(values) - 1)]
    anchor = values[0] if anchor_side == "first" else values[-1]
    return XorDeltaEncoded(anchor, diffs, anchor_side)


def xor_delta_decode_ints(encoded: XorDeltaEncoded) -> List[int]:
    n = len(encoded.diffs) + 1
    if n == 1:
        return [encoded.anchor]

    out = [0] * n
    if encoded.anchor_side == "first":
        out[0] = encoded.anchor
        for i, d in enumerate(encoded.diffs):
            out[i + 1] = out[i] ^ d
    else:
        out[-1] = encoded.anchor
        for i in range(n - 2, -1, -1):
            out[i] = out[i + 1] ^ encoded.diffs[i]
    return out


def xor_delta_encode_bytes(data: bytes, *, anchor_side: AnchorSide = "first") -> tuple[int, bytes, AnchorSide]:
    if not data:
        raise ValueError("data must be non-empty")
    diffs = bytes(data[i] ^ data[i + 1] for i in range(len(data) - 1))
    anchor = data[0] if anchor_side == "first" else data[-1]
    return anchor, diffs, anchor_side


def xor_delta_decode_bytes(anchor: int, diffs: bytes, anchor_side: AnchorSide) -> bytes:
    n = len(diffs) + 1
    out = bytearray(n)
    if anchor_side == "first":
        out[0] = anchor
        for i, d in enumerate(diffs):
            out[i + 1] = out[i] ^ d
    else:
        out[-1] = anchor
        for i in range(n - 2, -1, -1):
            out[i] = out[i + 1] ^ diffs[i]
    return bytes(out)