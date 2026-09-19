#!/usr/bin/env python3
"""Run the flagship two-account fraud-proof demo on stable Studionet.

Prerequisites:
- repository fixtures are already public on GitHub;
- at least two configured/funded Studionet accounts;
- genlayer-test v0.29.2 from requirements-test.txt.

The script deploys a fresh contract, posts the canonical three-leaf demo batch,
and challenges the deliberately false second leaf from a different account.
"""

from __future__ import annotations

import json
from pathlib import Path

from gltest import get_accounts, get_contract_factory
from gltest.assertions import tx_execution_succeeded

from build_batch import build
from check_network import main as check_network

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "fixtures" / "demo_batch_input.json"
OPERATOR_BOND = 2_000
CHALLENGER_BOND = 1_000
CHALLENGE_PERIOD = 600
TX_KW = {"consensus_max_rotations": 3, "wait_interval": 10000, "wait_retries": 30}


def ok(receipt, label: str) -> None:
    if not tx_execution_succeeded(receipt):
        raise SystemExit(f"{label} failed: {receipt}")
    print(f"{label}: {receipt}")


def main() -> None:
    check_network()
    accounts = get_accounts()
    if len(accounts) < 2:
        raise SystemExit("two configured Studionet accounts are required")
    operator, challenger = accounts[0], accounts[1]

    manifest = build(json.loads(INPUT.read_text(encoding="utf-8")))
    fraudulent = manifest["leaves"][1]

    factory = get_contract_factory(contract_file_path="verdictrollup.py")
    operator_contract = factory.deploy(account=operator, **TX_KW)
    print(f"contract={operator_contract.address}")

    created = operator_contract.create_batch(
        [
            manifest["title"],
            manifest["decision_rule"],
            manifest["result_labels_json"],
            manifest["merkle_root"],
            manifest["leaf_count"],
            CHALLENGE_PERIOD,
            CHALLENGER_BOND,
        ]
    ).transact(value=OPERATOR_BOND, **TX_KW)
    ok(created, "create_batch")

    before = operator_contract.get_batch([1]).call()
    print("batch_before=", json.dumps(before, sort_keys=True))

    challenger_contract = factory.build_contract(
        contract_address=operator_contract.address,
        account=challenger,
    )
    challenged = challenger_contract.challenge_leaf(
        [
            1,
            fraudulent["index"],
            fraudulent["question"],
            fraudulent["context"],
            fraudulent["source_url"],
            fraudulent["proposed_result"],
            fraudulent["proof_json"],
        ]
    ).transact(value=CHALLENGER_BOND, **TX_KW)
    ok(challenged, "challenge_leaf")

    after = operator_contract.get_batch([1]).call()
    challenge = operator_contract.get_challenge([1]).call()
    print("batch_after=", json.dumps(after, sort_keys=True))
    print("challenge=", json.dumps(challenge, sort_keys=True))

    if after["status_name"] != "INVALIDATED":
        raise SystemExit("expected the deliberately fraudulent batch to invalidate")
    if challenge["outcome_name"] != "FRAUD_PROVEN":
        raise SystemExit("expected FRAUD_PROVEN for the deliberately false second leaf")
    if challenge["consensus_result"] != "REJECTED":
        raise SystemExit("expected the public fixture to resolve to REJECTED")

    print("Flagship fraud-proof demo passed.")


if __name__ == "__main__":
    main()
