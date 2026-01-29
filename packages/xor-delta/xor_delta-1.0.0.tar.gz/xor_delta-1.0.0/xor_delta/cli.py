from __future__ import annotations

import argparse

from . import bench_files


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="xor_delta", description="xor-delta tools")
    sub = p.add_subparsers(dest="cmd", required=True)

    bench = sub.add_parser("bench-files", help="Benchmark raw vs XOR-adjacent on files/dirs or Gutenberg")
    bench.add_argument("args", nargs="*", help="Arguments passed through to file benchmark script")

    ns = p.parse_args(argv)

    if ns.cmd == "bench-files":
        # Pass-through: reuse the benchmark’s argparse exactly
        return bench_files.main(["bench-files"] + ns.args)

    raise SystemExit("Unknown command")
