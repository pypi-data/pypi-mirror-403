from __future__ import annotations

import argparse
import bz2
import hashlib
import lzma
import sys
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from xor_delta import xor_delta_encode_bytes

DEFAULT_CACHE_DIR = Path("corpus_cache")
GUTENBERG_PRESETS: dict[str, str] = {
    "shakespeare": "https://www.gutenberg.org/cache/epub/100/pg100.txt",
    "pg100": "https://www.gutenberg.org/cache/epub/100/pg100.txt",
}  # I know other corpora, I swear
# They just go to a different school
#
# In canada
# <_<   >_>


@dataclass(frozen=True, slots=True)
class Sizes:
    raw: int
    zlib: int
    bz2: int
    lzma: int


def sizes(data: bytes) -> Sizes:
    return Sizes(
        raw=len(data),
        zlib=len(zlib.compress(data, level=6)),
        bz2=len(bz2.compress(data, compresslevel=9)),
        lzma=len(lzma.compress(data, preset=6)),
    )


def xor_adjacent(data: bytes) -> bytes:
    if not data:
        return b""
    a, d, _ = xor_delta_encode_bytes(data, anchor_side="first")
    return bytes([a]) + d


def iter_inputs(args: Iterable[str]) -> list[Path]:
    out: list[Path] = []
    for s in args:
        p = Path(s)
        if p.is_dir():
            out.extend([c for c in p.rglob("*") if c.is_file()])
        else:
            out.append(p)
    return out


def fmt_ratio(raw: int, comp: int) -> str:
    if raw == 0:
        return "n/a"
    return f"{comp / raw:.3f}x"


def print_one(label: str, raw_s: Sizes, xd_s: Sizes) -> None:
    def line(tag: str, s: Sizes) -> str:
        return (
            f"  {tag:<8} raw={s.raw:,}  "
            f"zlib={s.zlib:,} ({fmt_ratio(s.raw, s.zlib)})  "
            f"bz2={s.bz2:,} ({fmt_ratio(s.raw, s.bz2)})  "
            f"lzma={s.lzma:,} ({fmt_ratio(s.raw, s.lzma)})"
        )

    def delta(a: int, b: int) -> str:
        if a == 0:
            return "n/a"
        pct = (b - a) / a * 100.0
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.2f}%"

    print(f"\n{label}")
    print(line("RAW", raw_s))
    print(line("XOR", xd_s))
    print(
        "  xor-vs-raw  "
        f"zlib {delta(raw_s.zlib, xd_s.zlib)}   "
        f"bz2 {delta(raw_s.bz2, xd_s.bz2)}   "
        f"lzma {delta(raw_s.lzma, xd_s.lzma)}"
    )


def _safe_filename_from_url(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    tail = url.split("/")[-1] or "download"
    return f"{tail}.{h}"


def download_to_cache(url: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    dst = cache_dir / _safe_filename_from_url(url)

    if dst.exists() and dst.stat().st_size > 0:
        return dst

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "xor-delta-bench/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r:
            total = r.headers.get("Content-Length")
            total_bytes = int(total) if total and total.isdigit() else None

            with tqdm(
                total=total_bytes,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"Downloading {dst.name}",
                leave=False,
                disable=not sys.stderr.isatty(),
            ) as bar:
                buf = bytearray()
                while True:
                    chunk = r.read(1024 * 64)
                    if not chunk:
                        break
                    buf.extend(chunk)
                    bar.update(len(chunk))
                data = bytes(buf)

    except urllib.error.URLError as e:
        raise SystemExit(f"Download failed: {url}\n{e}") from e

    if not data:
        raise SystemExit(f"Downloaded empty file from: {url}")

    dst.write_bytes(data)
    return dst


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Benchmark compressors on raw bytes vs XOR-adjacent (anchor+diffs) transform.",
    )
    p.add_argument(
        "paths",
        nargs="*",
        help="File(s) or directory(ies) to benchmark (directories are scanned recursively).",
    )
    p.add_argument(
        "--gutenberg",
        choices=sorted(GUTENBERG_PRESETS.keys()),
        help="Download a well-known Gutenberg text into cache and benchmark it (e.g., shakespeare).",
    )
    p.add_argument(
        "--gutenberg-url",
        help="Download an arbitrary URL into cache and benchmark it (expects a direct text file URL).",
    )
    p.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help=f"Cache directory for downloaded corpora (default: {DEFAULT_CACHE_DIR}).",
    )
    p.add_argument(
        "--byte-progress-threshold",
        type=int,
        default=1024 * 1024,
        help="For files >= this size (bytes), show per-stage progress weighted by bytes (default: 1 MiB).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv
    args = build_argparser().parse_args(argv[1:])

    # Default workload, whether 'tis nobler in the mind remains TBD
    if not args.paths and not args.gutenberg and not args.gutenberg_url:
        args.gutenberg = "shakespeare"

    cache_dir = Path(args.cache_dir)

    extra_paths: list[Path] = []
    if args.gutenberg:
        url = GUTENBERG_PRESETS[args.gutenberg]
        extra_paths.append(download_to_cache(url, cache_dir))
    if args.gutenberg_url:
        extra_paths.append(download_to_cache(args.gutenberg_url, cache_dir))

    paths = iter_inputs(args.paths) + extra_paths

    missing = [p for p in paths if not p.exists()]
    paths = [p for p in paths if p.exists() and p.is_file()]

    if missing:
        print("Skipping missing paths:", file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)

    if not paths:
        print("No readable files found.", file=sys.stderr)
        return 2

    total_raw = Sizes(0, 0, 0, 0)
    total_xd = Sizes(0, 0, 0, 0)

    def add(a: Sizes, b: Sizes) -> Sizes:
        return Sizes(a.raw + b.raw, a.zlib + b.zlib, a.bz2 + b.bz2, a.lzma + b.lzma)

    outer = tqdm(
        sorted(paths),
        desc="Benchmarking",
        unit="file",
        disable=not sys.stderr.isatty(),
    )

    for p in outer:
        try:
            file_size = p.stat().st_size
        except OSError:
            file_size = 0

        try:
            data = p.read_bytes()
        except Exception as e:
            print(f"\n{p}\n  ERROR reading file: {e}", file=sys.stderr)
            continue

        # For big files, show a more granular, byte-weighted stage bar.
        if sys.stderr.isatty() and len(data) >= args.byte_progress_threshold:
            stage_total = len(data) * 7
            with tqdm(
                total=stage_total,
                desc=f"{p.name}",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                leave=False,
            ) as stage:
                raw_len = len(data)

                z_raw = zlib.compress(data, level=6)
                stage.update(raw_len)

                b_raw = bz2.compress(data, compresslevel=9)
                stage.update(raw_len)

                l_raw = lzma.compress(data, preset=6)
                stage.update(raw_len)

                xd = xor_adjacent(data)
                stage.update(raw_len)

                z_xd = zlib.compress(xd, level=6)
                stage.update(raw_len)

                b_xd = bz2.compress(xd, compresslevel=9)
                stage.update(raw_len)

                l_xd = lzma.compress(xd, preset=6)
                stage.update(raw_len)

                raw_s = Sizes(raw=raw_len, zlib=len(z_raw), bz2=len(b_raw), lzma=len(l_raw))
                xd_s = Sizes(raw=raw_len, zlib=len(z_xd), bz2=len(b_xd), lzma=len(l_xd))
        else:
            raw_s = sizes(data)
            xd_s = sizes(xor_adjacent(data))

        print_one(str(p), raw_s, xd_s)

        total_raw = add(total_raw, raw_s)
        total_xd = add(total_xd, xd_s)

    if len(paths) > 1:
        print_one(f"TOTAL ({len(paths)} files)", total_raw, total_xd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
