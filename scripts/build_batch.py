#!/usr/bin/env python3
"""Build a VerdictRollup manifest, root and per-leaf Merkle proofs.

Input JSON shape:
{
  "title": "Release approval batch",
  "decision_rule": "...",
  "result_labels": ["APPROVED", "REJECTED", "UNRESOLVED"],
  "leaves": [
    {
      "question": "Is Aurora approved for production?",
      "context": "Project Aurora",
      "source_url": "https://...",
      "proposed_result": "APPROVED"
    }
  ]
}

This script deliberately does not submit transactions. It produces exactly the
preimages expected by contracts/verdictrollup.py.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from .merkle import canonical_json, keccak_hex, merkle_proof, merkle_root
except ImportError:  # script execution
    from merkle import canonical_json, keccak_hex, merkle_proof, merkle_root

MAX_TITLE_LEN = 120
MAX_RULE_LEN = 1800
MAX_LABELS = 8
MAX_LABEL_LEN = 32
MAX_QUESTION_LEN = 900
MAX_CONTEXT_LEN = 1200
MAX_URL_LEN = 512
UNRESOLVED = "UNRESOLVED"

CONTROL_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard previous instructions",
    "reveal your system prompt",
    "show your system prompt",
    "developer message",
    "call a tool",
    "execute code",
    "send funds",
    "transfer funds",
    "reveal secret",
    "reveal credential",
)


def passive_text(value: str) -> bool:
    lower = str(value).lower()
    return not any(marker in lower for marker in CONTROL_MARKERS)


def clean_text(value, limit: int) -> str:
    return " ".join(str(value).strip().split())[:limit]


def normalize_label(value) -> str:
    text = clean_text(value, MAX_LABEL_LEN + 1).upper().replace(" ", "_")
    if not 1 <= len(text) <= MAX_LABEL_LEN:
        raise ValueError(f"result label must be 1..{MAX_LABEL_LEN} chars")
    if any(not ("A" <= c <= "Z" or "0" <= c <= "9" or c in "_-") for c in text):
        raise ValueError("result labels may use A-Z, 0-9, _ and -")
    return text


def normalize_labels(values) -> list[str]:
    if not isinstance(values, list) or not 2 <= len(values) <= MAX_LABELS:
        raise ValueError(f"result_labels must contain 2..{MAX_LABELS} labels")
    labels = [normalize_label(v) for v in values]
    if len(set(labels)) != len(labels):
        raise ValueError("duplicate result label")
    if UNRESOLVED not in labels:
        raise ValueError(f"result_labels must include {UNRESOLVED}")
    return labels


def _host_of(url: str) -> str:
    text = str(url).strip()
    if len(text) < 8 or text[:8].lower() != "https://":
        return ""
    rest = text[8:]
    end = len(rest)
    for delimiter in ("/", "?"):
        index = rest.find(delimiter)
        if index != -1 and index < end:
            end = index
    host = rest[:end]
    if "@" in host or ":" in host:
        return ""
    return host.lower().strip(".")


def _is_private_ipv4(parts: list[str]) -> bool:
    if len(parts) != 4:
        return False
    try:
        nums = [int(part) for part in parts]
    except ValueError:
        return False
    if not all(0 <= number <= 255 for number in nums):
        return False
    if nums[0] in (0, 10, 127):
        return True
    if nums[0] == 169 and nums[1] == 254:
        return True
    if nums[0] == 172 and 16 <= nums[1] <= 31:
        return True
    if nums[0] == 192 and nums[1] == 168:
        return True
    return False


def normalize_url(value: str) -> str:
    # Mirrors contracts/verdictrollup.py exactly so manifest preimages agree.
    text = str(value).strip()
    if not text or len(text) > MAX_URL_LEN:
        raise ValueError(f"source_url must be 1..{MAX_URL_LEN} chars")
    if len(text) < 8 or text[:8].lower() != "https://":
        raise ValueError("source_url must use https")
    if "%" in text or "\\" in text:
        raise ValueError("ambiguous URL encoding is rejected")
    if "#" in text:
        text = text.split("#", 1)[0]

    host = _host_of(text)
    if not host or len(host) > 253 or "." not in host:
        raise ValueError("invalid public DNS host")
    if host.endswith(".local") or host.endswith(".internal") or host.endswith(".localhost"):
        raise ValueError("local/private hosts are rejected")

    labels = host.split(".")
    for label in labels:
        if not label or len(label) > 63 or label[0] == "-" or label[-1] == "-":
            raise ValueError("invalid public DNS host")
        if not re.fullmatch(r"[a-z0-9-]+", label):
            raise ValueError("invalid public DNS host")

    if all(label.isdigit() for label in labels):
        raise ValueError("numeric hosts are rejected")
    if len(labels) >= 4 and all(part.isdigit() for part in labels[:4]):
        if any(len(part) > 1 and part.startswith("0") for part in labels[:4]):
            raise ValueError("ambiguous IP-like host is rejected")
        if _is_private_ipv4(labels[:4]):
            raise ValueError("private IP-like host is rejected")

    rest = text[8:]
    host_end = len(rest)
    for delimiter in ("/", "?"):
        index = rest.find(delimiter)
        if index != -1 and index < host_end:
            host_end = index
    suffix = rest[host_end:] or "/"
    return "https://" + host + suffix


def schema_hash(title: str, decision_rule: str, labels: list[str]) -> str:
    return keccak_hex(
        canonical_json(
            {
                "title": title,
                "decision_rule": decision_rule,
                "result_labels": labels,
            }
        )
    )


def leaf_hash(schema: str, index: int, leaf: dict) -> str:
    return keccak_hex(
        canonical_json(
            {
                "schema_hash": schema,
                "leaf_index": index,
                "question": leaf["question"],
                "context": leaf["context"],
                "source_url": leaf["source_url"],
                "proposed_result": leaf["proposed_result"],
            }
        )
    )


def normalize_input(raw: dict) -> dict:
    title = clean_text(raw.get("title", ""), MAX_TITLE_LEN + 1)
    rule = clean_text(raw.get("decision_rule", ""), MAX_RULE_LEN + 1)
    if not 1 <= len(title) <= MAX_TITLE_LEN:
        raise ValueError("title is outside contract limits")
    if not 1 <= len(rule) <= MAX_RULE_LEN:
        raise ValueError("decision_rule is outside contract limits")
    if not passive_text(title) or not passive_text(rule):
        raise ValueError("title and decision_rule must be passive data")
    labels = normalize_labels(raw.get("result_labels"))

    raw_leaves = raw.get("leaves")
    if not isinstance(raw_leaves, list) or not raw_leaves:
        raise ValueError("at least one leaf is required")
    if len(raw_leaves) > 65536:
        raise ValueError("leaf count exceeds contract limit")

    leaves = []
    for item in raw_leaves:
        if not isinstance(item, dict):
            raise ValueError("each leaf must be an object")
        question = clean_text(item.get("question", ""), MAX_QUESTION_LEN + 1)
        context = clean_text(item.get("context", ""), MAX_CONTEXT_LEN + 1)
        if not 1 <= len(question) <= MAX_QUESTION_LEN:
            raise ValueError("leaf question is outside contract limits")
        if len(context) > MAX_CONTEXT_LEN:
            raise ValueError("leaf context is outside contract limits")
        if not passive_text(question) or not passive_text(context):
            raise ValueError("question and context must be passive data")
        source_url = normalize_url(item.get("source_url", ""))
        proposed = normalize_label(item.get("proposed_result", ""))
        if proposed not in labels:
            raise ValueError(f"proposed result {proposed} is not in result_labels")
        leaves.append(
            {
                "question": question,
                "context": context,
                "source_url": source_url,
                "proposed_result": proposed,
            }
        )

    return {
        "title": title,
        "decision_rule": rule,
        "result_labels": labels,
        "leaves": leaves,
    }


def build(raw: dict) -> dict:
    data = normalize_input(raw)
    schema = schema_hash(data["title"], data["decision_rule"], data["result_labels"])
    hashes = [leaf_hash(schema, idx, leaf) for idx, leaf in enumerate(data["leaves"])]
    root = merkle_root(hashes)

    leaves = []
    for idx, leaf in enumerate(data["leaves"]):
        proof = merkle_proof(hashes, idx)
        leaves.append(
            {
                "index": idx,
                **leaf,
                "leaf_hash": hashes[idx],
                "proof": proof,
                "proof_json": json.dumps(proof, separators=(",", ":")),
            }
        )

    return {
        "format": "verdictrollup-manifest-v1",
        "title": data["title"],
        "decision_rule": data["decision_rule"],
        "result_labels": data["result_labels"],
        "result_labels_json": json.dumps(data["result_labels"], separators=(",", ":")),
        "schema_hash": schema,
        "merkle_root": root,
        "leaf_count": len(leaves),
        "leaves": leaves,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    manifest = build(raw)
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
