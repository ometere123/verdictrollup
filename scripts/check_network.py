#!/usr/bin/env python3
"""Fail closed unless the configured remote is stable GenLayer Studionet."""

from __future__ import annotations

import json
import sys
import urllib.request

RPC = "https://studio.genlayer.com/api"
EXPECTED_CHAIN_ID = 61999


def main() -> None:
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []}
    ).encode("utf-8")
    request = urllib.request.Request(
        RPC,
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise SystemExit(f"network check failed: {exc}") from exc

    raw = body.get("result")
    if not isinstance(raw, str):
        raise SystemExit(f"network check failed: unexpected response {body!r}")
    actual = int(raw, 16)
    if actual != EXPECTED_CHAIN_ID:
        raise SystemExit(
            f"refusing to continue: expected chain {EXPECTED_CHAIN_ID}, got {actual}"
        )
    print(f"Studionet verified: chain_id={actual} rpc={RPC}")


if __name__ == "__main__":
    main()
