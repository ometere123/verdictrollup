"""High-signal stable-Studionet checks for VerdictRollup.

These tests deploy the real contract, create a bonded optimistic batch, and verify
that the exact off-chain Merkle commitment can be read and verified on-chain.
The adversarial semantic challenge lifecycle is intentionally kept as a separate
manual/live proof because it needs a second funded challenger account and live
validator web/LLM execution.
"""

from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded

from scripts.build_batch import build


CONTRACT = "verdictrollup.py"
TX_KW = {"consensus_max_rotations": 3, "wait_interval": 10000, "wait_retries": 20}
OPERATOR_BOND = 2_000
CHALLENGER_BOND = 1_000
CHALLENGE_PERIOD = 600

RULE = (
    "Classify a named release as APPROVED only when the cited source explicitly "
    "states that it is approved for production deployment. Classify it as REJECTED "
    "only when the cited source explicitly states that it is rejected or blocked "
    "for production deployment. Otherwise classify it as UNRESOLVED."
)


def manifest():
    return build(
        {
            "title": "VerdictRollup stable Studionet smoke batch",
            "decision_rule": RULE,
            "result_labels": ["APPROVED", "REJECTED", "UNRESOLVED"],
            "leaves": [
                {
                    "question": "What is the production decision for Project Aurora?",
                    "context": "Project Aurora release 2026.09",
                    "source_url": "https://raw.githubusercontent.com/ometere123/verdictrollup/main/fixtures/approved.txt",
                    "proposed_result": "APPROVED",
                }
            ],
        }
    )


def deploy_contract():
    factory = get_contract_factory(contract_file_path=CONTRACT)
    contract = factory.deploy(
        account=get_default_account(),
        consensus_max_rotations=3,
        wait_interval=10000,
        wait_retries=20,
    )
    assert contract.address
    return contract


def assert_success(receipt):
    assert tx_execution_succeeded(receipt), receipt


def test_deployment_and_status_dictionary():
    contract = deploy_contract()
    dictionary = contract.get_status_dictionary().call()
    assert dictionary["batch"]["OPEN"] == 0
    assert dictionary["batch"]["FINALIZED"] == 2
    assert dictionary["challenge"]["FRAUD_PROVEN"] == 2


def test_bonded_batch_commitment_round_trips_on_studionet():
    contract = deploy_contract()
    m = manifest()

    created = contract.create_batch(
        [
            m["title"],
            m["decision_rule"],
            m["result_labels_json"],
            m["merkle_root"],
            m["leaf_count"],
            CHALLENGE_PERIOD,
            CHALLENGER_BOND,
        ]
    ).transact(value=OPERATOR_BOND, **TX_KW)
    assert_success(created)

    batch = contract.get_batch([1]).call()
    leaf = m["leaves"][0]
    assert batch["status_name"] == "OPEN"
    assert batch["schema_hash"] == m["schema_hash"]
    assert batch["merkle_root"] == m["merkle_root"]
    assert batch["operator_bond_wei"] == OPERATOR_BOND
    assert batch["challenger_bond_wei"] == CHALLENGER_BOND

    assert contract.verify_leaf(
        [
            1,
            leaf["index"],
            leaf["question"],
            leaf["context"],
            leaf["source_url"],
            leaf["proposed_result"],
            leaf["proof_json"],
        ]
    ).call() is True

    # Membership is not optimistic finality while the challenge window is open.
    assert contract.is_final_leaf(
        [
            1,
            batch["definition_hash"],
            leaf["index"],
            leaf["question"],
            leaf["context"],
            leaf["source_url"],
            leaf["proposed_result"],
            leaf["proof_json"],
        ]
    ).call() is False
