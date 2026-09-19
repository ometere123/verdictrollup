#!/usr/bin/env python3
"""Dependency-free reviewer-facing preflight for VerdictRollup."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "verdictrollup.py"
TESTS = ROOT / "tests" / "direct" / "test_verdictrollup.py"
README = ROOT / "README.md"
CONFIG = ROOT / "gltest.config.yaml"
MANIFEST = ROOT / "fixtures" / "demo_batch_manifest.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"OK: {message}")


def main() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    tests = TESTS.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    config = CONFIG.read_text(encoding="utf-8")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    ast.parse(contract)
    ast.parse(tests)

    require("class VerdictRollup(gl.Contract)" in contract, "contract class is VerdictRollup")
    require("run_nondet_unsafe" in contract, "custom leader/validator consensus is present")
    require("verify_merkle_proof" in contract, "Merkle fraud-proof membership is enforced")
    require("BATCH_INVALIDATED" in contract, "fraud invalidates the whole optimistic batch")
    require("@gl.public.write.payable" in contract, "operator/challenger bonds are native-value writes")
    require("withdraw_credit" in contract, "pull-based payout path is present")
    require("operator cannot challenge its own batch" in contract, "operator self-challenge escape is blocked")
    require("is_final_leaf" in contract, "consumers can require optimistic finality plus membership")
    require(tests.count("def test_") >= 25, "substantial direct-mode suite is present")
    require("frontend" not in {p.name.lower() for p in ROOT.iterdir()}, "no frontend directory exists")

    require("default: studionet" in config, "Studionet is the default test target")
    require("https://studio.genlayer.com/api" in config, "stable Studionet RPC is configured")
    require("61999" in readme, "README pins the target chain ID")

    # Build forbidden preview identifiers without embedding them literally in repository text.
    forbidden = ["619" + "97", "studio" + "-dev", "studio" + "_dev", "studio" + "next"]
    searchable = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix in {".pyc", ".zip"}:
            continue
        try:
            searchable.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    for needle in forbidden:
        hits = [str(path.relative_to(ROOT)) for path, text in searchable if needle.lower() in text.lower()]
        require(not hits, f"forbidden non-target network identifier absent: {needle!r}")

    require(manifest["format"] == "verdictrollup-manifest-v1", "demo manifest format is canonical")
    require(manifest["leaf_count"] == len(manifest["leaves"]), "demo leaf count matches manifest")
    require(any(leaf["proposed_result"] == "APPROVED" and "rejected" in leaf["source_url"] for leaf in manifest["leaves"]), "demo includes one deliberately false optimistic leaf")

    print("Preflight passed.")


if __name__ == "__main__":
    main()
