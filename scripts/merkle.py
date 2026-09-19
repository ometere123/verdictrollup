"""Dependency-free Keccak-256 and Merkle helpers for VerdictRollup.

The contract uses GenLayer's Keccak256. This module implements Ethereum-style
Keccak-256 (not NIST SHA3-256) so manifests can be prepared without web3 or
other third-party packages.
"""

from __future__ import annotations

import json
from typing import Iterable

MASK64 = (1 << 64) - 1
RATE_BYTES = 136  # Keccak-256 rate = 1088 bits

ROTATION = (
    (0, 36, 3, 41, 18),
    (1, 44, 10, 45, 2),
    (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56),
    (27, 20, 39, 8, 14),
)

ROUND_CONSTANTS = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)


def _rol64(value: int, shift: int) -> int:
    value &= MASK64
    if shift == 0:
        return value
    return ((value << shift) | (value >> (64 - shift))) & MASK64


def _keccak_f1600(state: list[int]) -> None:
    for rc in ROUND_CONSTANTS:
        # Theta
        c = [
            state[x]
            ^ state[x + 5]
            ^ state[x + 10]
            ^ state[x + 15]
            ^ state[x + 20]
            for x in range(5)
        ]
        d = [c[(x - 1) % 5] ^ _rol64(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= d[x]

        # Rho + Pi
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rol64(
                    state[x + 5 * y], ROTATION[x][y]
                )

        # Chi
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = (
                    b[x + 5 * y]
                    ^ ((~b[(x + 1) % 5 + 5 * y]) & b[(x + 2) % 5 + 5 * y])
                ) & MASK64

        # Iota
        state[0] ^= rc


def keccak256(data: bytes) -> bytes:
    """Return Ethereum/Keccak-256 digest bytes."""
    state = [0] * 25
    padded = bytearray(data)
    padded.append(0x01)  # Keccak domain separator, not SHA3's 0x06
    while len(padded) % RATE_BYTES != RATE_BYTES - 1:
        padded.append(0x00)
    padded.append(0x80)

    for offset in range(0, len(padded), RATE_BYTES):
        block = padded[offset : offset + RATE_BYTES]
        for i in range(RATE_BYTES // 8):
            lane = int.from_bytes(block[i * 8 : (i + 1) * 8], "little")
            state[i] ^= lane
        _keccak_f1600(state)

    out = bytearray()
    while len(out) < 32:
        for i in range(RATE_BYTES // 8):
            out.extend(state[i].to_bytes(8, "little"))
            if len(out) >= 32:
                break
        if len(out) < 32:
            _keccak_f1600(state)
    return bytes(out[:32])


def keccak_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return keccak256(data).hex()


def normalize_hash(value: str) -> str:
    text = value.strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError("expected 32-byte hex hash")
    return text


def hash_parent(left_hex: str, right_hex: str) -> str:
    left = bytes.fromhex(normalize_hash(left_hex))
    right = bytes.fromhex(normalize_hash(right_hex))
    return keccak_hex(left + right)


def merkle_root(leaves: Iterable[str]) -> str:
    level = [normalize_hash(item) for item in leaves]
    if not level:
        raise ValueError("at least one leaf is required")
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [hash_parent(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def merkle_proof(leaves: list[str], index: int) -> list[dict[str, str]]:
    level = [normalize_hash(item) for item in leaves]
    if index < 0 or index >= len(level):
        raise IndexError(index)
    proof: list[dict[str, str]] = []
    position = index
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        sibling_index = position - 1 if position % 2 else position + 1
        side = "L" if position % 2 else "R"
        proof.append({"side": side, "hash": level[sibling_index]})
        next_level = [hash_parent(level[i], level[i + 1]) for i in range(0, len(level), 2)]
        position //= 2
        level = next_level
    return proof


def verify_proof(leaf_hash: str, proof: list[dict[str, str]], root: str) -> bool:
    current = normalize_hash(leaf_hash)
    for item in proof:
        side = str(item["side"]).upper()
        sibling = normalize_hash(item["hash"])
        if side == "L":
            current = hash_parent(sibling, current)
        elif side == "R":
            current = hash_parent(current, sibling)
        else:
            return False
    return current == normalize_hash(root)


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


if __name__ == "__main__":
    # Canonical Ethereum Keccak-256 vector.
    expected = "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    actual = keccak_hex(b"")
    if actual != expected:
        raise SystemExit(f"Keccak self-test failed: {actual} != {expected}")
    print("Keccak self-test passed.")
