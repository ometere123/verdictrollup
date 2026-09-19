# VerdictRollup — stable Studionet deployment evidence

## Canonical target

- Network: GenLayer Studionet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com/`
- Contract: `contracts/verdictrollup.py`

## Evidence status

**No live deployment is claimed in this file yet.**

The repository was built and statically validated in an execution environment that does not have a GenLayer signing wallet or direct outbound Studionet transaction access. Rather than fabricate a contract address, transaction hash or test result, the repository includes `scripts/check_network.py`, `scripts/deploy_studionet.py`, hosted-network integration tests and `scripts/live_fraud_demo.py` so the final signing/deployment run can be performed reproducibly from a funded Studionet environment.

When the live run is performed, replace this section with the verified values below.

## Deployment record to fill from the real run

```text
Repository commit:
Contract SHA-256:
Deployer:
Contract address:
Deployment transaction:
Deployment UTC:
Deployment status:
Execution result:
```

Verification requirement: record the same complete contract source hash that was deployed and verify the transaction's execution result, not only its outer/finalized status.

## Flagship fraud-proof record to fill

The canonical demo manifest root is:

```text
e46676e2a49441e0c702a964cd9537249f44bf73cea92d1765620ef533faccc5
```

The second leaf is intentionally committed as `APPROVED` while the public source states `REJECTED`.

```text
Batch ID:
Batch definition hash:
Create-batch transaction:
Challenge ID:
Challenger:
Challenge transaction:
Committed result: APPROVED
Consensus result:
Challenge outcome:
Final batch status:
Challenger credit:
```

The expected proof is `consensus result == REJECTED`, `challenge outcome == FRAUD_PROVEN`, and `batch status == INVALIDATED`. Record those values only after the live state reads confirm them.

## Honest finality record to fill

Create a separate all-correct batch and record:

```text
Batch ID:
Definition hash:
Merkle root:
Finalize transaction:
Final status:
verify_leaf after finalization:
is_final_leaf with correct definition hash:
is_final_leaf with wrong definition hash:
```

## Commands

```bash
python scripts/check_network.py
python scripts/preflight.py
python scripts/merkle.py
python scripts/verify_manifest.py fixtures/demo_batch_manifest.json
pytest tests/direct -v
genvm-lint check contracts/verdictrollup.py
gltest tests/integration/ -v -s --network studionet
```

For the two-account fraud lifecycle:

```bash
python scripts/live_fraud_demo.py
```

See `docs/LIVE_DEMO.md` for the exact evidence-capture path.
