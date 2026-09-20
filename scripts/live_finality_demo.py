#!/usr/bin/env python3
"""Create and finalize an honest Studionet batch, proving compact consumer finality."""

from __future__ import annotations

import argparse
import json
import time

from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest_cli.config.general import get_general_config
from gltest_cli.config.user import load_user_config

try:
    from scripts.build_batch import build
    from scripts.check_network import main as check_studionet
except ImportError:
    from build_batch import build
    from check_network import main as check_studionet


CONTRACT = "verdictrollup.py"
OPERATOR_BOND = 2_000
CHALLENGER_BOND = 1_000
CHALLENGE_PERIOD = 60
WAIT = {
    "consensus_max_rotations": 3,
    "wait_transaction_status": TransactionStatus.FINALIZED,
    "wait_interval": 5_000,
    "wait_retries": 60,
}


def compact_proof(leaf: dict) -> str:
    """Encode each sibling as one side byte ('L'/'R') plus 64 hex characters."""
    return "".join(step["side"] + step["hash"] for step in leaf["proof"])


def receipt_summary(receipt: dict) -> dict:
    leader_receipts = receipt.get("consensus_data", {}).get("leader_receipt", [])
    execution = leader_receipts[0].get("execution_result") if leader_receipts else None
    return {
        "tx_id": receipt.get("tx_id") or receipt.get("hash"),
        "status": receipt.get("status_name") or receipt.get("status"),
        "result": receipt.get("result_name"),
        "execution": execution or receipt.get("tx_execution_result_name"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-address", required=True)
    args = parser.parse_args()

    # Fail closed before the first write; this script is Studionet-only.
    check_studionet()
    # Standalone invocation does not run pytest's gltest config plugin.
    get_general_config().user_config = load_user_config("gltest.config.yaml")
    account = get_default_account()
    factory = get_contract_factory(contract_file_path=CONTRACT)
    contract = factory.build_contract(args.contract_address, account=account)

    manifest = build(
        {
            "title": "VerdictRollup compact finality consumer proof",
            "decision_rule": (
                "Use the committed proposal when it is one of the frozen result labels."
            ),
            "result_labels": ["APPROVED", "REJECTED", "UNRESOLVED"],
            "leaves": [
                {
                    "question": "What is the decision for item alpha?",
                    "context": "Finality consumer demonstration",
                    "source_url": "https://example.com/verdictrollup/alpha",
                    "proposed_result": "APPROVED",
                },
                {
                    "question": "What is the decision for item beta?",
                    "context": "Finality consumer demonstration",
                    "source_url": "https://example.com/verdictrollup/beta",
                    "proposed_result": "REJECTED",
                },
            ],
        }
    )

    create = contract.create_batch(
        args=[
            manifest["title"],
            manifest["decision_rule"],
            manifest["result_labels_json"],
            manifest["merkle_root"],
            manifest["leaf_count"],
            CHALLENGE_PERIOD,
            CHALLENGER_BOND,
        ]
    ).transact(value=OPERATOR_BOND, **WAIT)
    if not tx_execution_succeeded(create):
        raise SystemExit(f"create_batch execution failed: {create!r}")
    created_batch = contract.get_batch([1]).call()
    leaf = manifest["leaves"][0]
    proof = compact_proof(leaf)
    definition_int = int(created_batch["definition_hash"], 16)
    leaf_hash_int = int(leaf["leaf_hash"], 16)

    membership_open = contract.verify_leaf(
        [
            1,
            leaf["index"],
            leaf["question"],
            leaf["context"],
            leaf["source_url"],
            leaf["proposed_result"],
            leaf["proof_json"],
        ]
    ).call()
    compact_open = contract.is_final_leaf_hash(
        [1, definition_int, leaf_hash_int, proof]
    ).call()
    if membership_open is not True or compact_open is not False:
        raise SystemExit("pre-finality invariant failed")

    # Wait longer than the on-chain challenge interval before finalizing.
    time.sleep(CHALLENGE_PERIOD + 5)
    finalize = contract.finalize_batch([1]).transact(**WAIT)
    if not tx_execution_succeeded(finalize):
        raise SystemExit(f"finalize_batch execution failed: {finalize!r}")

    finalized_batch = contract.get_batch([1]).call()
    compact_final = contract.is_final_leaf_hash(
        [1, definition_int, leaf_hash_int, proof]
    ).call()
    wrong_definition = contract.is_final_leaf_hash(
        [1, 0, leaf_hash_int, proof]
    ).call()
    wrong_leaf = contract.is_final_leaf_hash(
        [1, definition_int, 0, proof]
    ).call()
    if (
        finalized_batch["status_name"] != "FINALIZED"
        or compact_final is not True
        or wrong_definition is not False
        or wrong_leaf is not False
    ):
        raise SystemExit("finality, definition pin, or membership invariant failed")

    print(
        json.dumps(
            {
                "network": "Studionet",
                "chain_id": 61999,
                "contract": args.contract_address,
                "create_batch": receipt_summary(create),
                "finalize_batch": receipt_summary(finalize),
                "batch_id": 1,
                "definition_hash": finalized_batch["definition_hash"],
                "merkle_root": finalized_batch["merkle_root"],
                "leaf_hash": leaf["leaf_hash"],
                "compact_proof": proof,
                "membership_while_open": membership_open,
                "compact_finality_while_open": compact_open,
                "batch_status_after_finalize": finalized_batch["status_name"],
                "compact_finality_after_finalize": compact_final,
                "wrong_definition_hash": wrong_definition,
                "uncommitted_leaf_hash": wrong_leaf,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
