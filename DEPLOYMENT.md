# VerdictRollup — stable Studionet deployment evidence

> **Current observed live evidence is recorded in [`docs/STUDIONET_LIVE_EVIDENCE.md`](docs/STUDIONET_LIVE_EVIDENCE.md).** The blank fields and "no live deployment" text later in this file are the original pre-deployment template and are superseded by that record. The live contract was deployed on Studionet 61999; this evidence adds no contract changes or redeployment.

Current canonical contract: [`0x0d921292939A28d41d9BE4a304b725dcd3A76af0`](https://explorer-studio.genlayer.com/address/0x0d921292939A28d41d9BE4a304b725dcd3A76af0). Deployment: [`0x64703c09a112f4c4ab447397898bac78b1af6789ce802e94ede04b33784638f1`](https://explorer-studio.genlayer.com/tx/0x64703c09a112f4c4ab447397898bac78b1af6789ce802e94ede04b33784638f1), finalized with successful execution.

The live fraud proof and honest finalization were also verified. The eight-argument `is_final_leaf` read currently fails at the RPC with an RLP surplus-bytes error; see the linked record. Do not infer or claim a successful live return from the batch state alone.


## Canonical target

- Network: GenLayer Studionet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com/`
- Contract: `contracts/verdictrollup.py`

## Evidence status

**Superseded:** this pre-deployment template is retained for historical context only. The live values are in `docs/STUDIONET_LIVE_EVIDENCE.md`.

Historical note: this paragraph described the pre-deployment environment only. The contract has since been deployed and the verified evidence is in `docs/STUDIONET_LIVE_EVIDENCE.md`; live signing and Studionet access were used for the evidence collected there.

The following blank fields are historical template fields and are not current deployment evidence.

## Historical deployment record template

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

## Historical flagship fraud-proof record template

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

## Historical honest-finality record template

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
