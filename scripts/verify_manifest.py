#!/usr/bin/env python3
"""Verify every leaf proof in a generated VerdictRollup manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .merkle import verify_proof
except ImportError:  # script execution
    from merkle import verify_proof


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = data["merkle_root"]
    leaves = data["leaves"]
    for leaf in leaves:
        if not verify_proof(leaf["leaf_hash"], leaf["proof"], root):
            raise SystemExit(f"invalid proof for leaf {leaf['index']}")
    print(f"verified {len(leaves)} leaves against root {root}")


if __name__ == "__main__":
    main()
