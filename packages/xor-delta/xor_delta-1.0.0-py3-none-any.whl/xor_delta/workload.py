from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import BinaryIO

MAGIC = b"XDEL"
VERSION = 1

MODE_ENCODED_BYTES = 1
ANCHOR_FIRST = 0


def _read_exact(f: BinaryIO, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = f.read(n - len(buf))
        if not chunk:
            raise ValueError("Unexpected EOF")
        buf.extend(chunk)
    return bytes(buf)


def encode_file(fin: BinaryIO, fout: BinaryIO, *, chunk_size: int = 1024 * 1024) -> None:
    """Encode bytes from fin to fout using adjacent XOR differencing (streaming).

    Output format:
      MAGIC(4) VERSION(1) MODE(1) ANCHOR_SIDE(1) ANCHOR(1) DIFFS...
    """
    first = fin.read(1)
    if not first:
        raise ValueError("Input is empty; cannot encode")

    prev = first[0]

    fout.write(MAGIC)
    fout.write(bytes([VERSION, MODE_ENCODED_BYTES, ANCHOR_FIRST, prev]))

    while True:
        chunk = fin.read(chunk_size)
        if not chunk:
            break

        out = bytearray(len(chunk))
        for i, b in enumerate(chunk):
            out[i] = prev ^ b
            prev = b
        fout.write(out)


def decode_file(fin: BinaryIO, fout: BinaryIO, *, chunk_size: int = 1024 * 1024) -> None:
    """Decode bytes from fin to fout for the streaming XOR-delta file format."""
    magic = _read_exact(fin, 4)
    if magic != MAGIC:
        raise ValueError(f"Bad magic: expected {MAGIC!r}, got {magic!r}")

    ver, mode, anchor_side = _read_exact(fin, 3)
    if ver != VERSION:
        raise ValueError(f"Unsupported version: {ver}")
    if mode != MODE_ENCODED_BYTES:
        raise ValueError("Unsupported mode")
    if anchor_side != ANCHOR_FIRST:
        raise ValueError("Unsupported anchor side (only 'first' supported)")

    anchor = _read_exact(fin, 1)[0]
    fout.write(bytes([anchor]))

    prev = anchor
    while True:
        diffs = fin.read(chunk_size)
        if not diffs:
            break

        out = bytearray(len(diffs))
        for i, d in enumerate(diffs):
            out[i] = prev ^ d
            prev = out[i]
        fout.write(out)


def _open_in(path: str) -> BinaryIO:
    if path == "-":
        return sys.stdin.buffer
    return Path(path).open("rb")


def _open_out(path: str) -> BinaryIO:
    if path == "-":
        return sys.stdout.buffer
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p.open("wb")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="xor-delta", description="XOR-adjacent delta workload tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="Encode a file/stream to .xdel format")
    enc.add_argument("-i", "--input", default="-", help="Input file path, or '-' for stdin")
    enc.add_argument("-o", "--output", default="-", help="Output file path, or '-' for stdout")
    enc.add_argument("--chunk-size", type=int, default=1024 * 1024, help="Chunk size in bytes (default: 1 MiB)")

    dec = sub.add_parser("decode", help="Decode a .xdel file/stream back to original bytes")
    dec.add_argument("-i", "--input", default="-", help="Input file path, or '-' for stdin")
    dec.add_argument("-o", "--output", default="-", help="Output file path, or '-' for stdout")
    dec.add_argument("--chunk-size", type=int, default=1024 * 1024, help="Chunk size in bytes (default: 1 MiB)")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        with _open_in(args.input) as fin, _open_out(args.output) as fout:
            if args.cmd == "encode":
                encode_file(fin, fout, chunk_size=args.chunk_size)
            else:
                decode_file(fin, fout, chunk_size=args.chunk_size)
    except BrokenPipeError:
        return 0
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    return 0
