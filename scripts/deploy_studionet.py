#!/usr/bin/env python3
"""Deploy VerdictRollup to stable Studionet after an explicit chain check."""

from __future__ import annotations

from gltest import get_contract_factory, get_default_account

from check_network import main as check_network


TX_KW = {"consensus_max_rotations": 3, "wait_interval": 10000, "wait_retries": 30}


def main() -> None:
    check_network()
    factory = get_contract_factory(contract_file_path="verdictrollup.py")
    contract = factory.deploy(account=get_default_account(), **TX_KW)
    if not contract.address:
        raise SystemExit("deployment returned no contract address")
    print(f"VerdictRollup deployed: {contract.address}")
    print("Record the deployment transaction and finalized execution result in DEPLOYMENT.md.")


if __name__ == "__main__":
    main()
