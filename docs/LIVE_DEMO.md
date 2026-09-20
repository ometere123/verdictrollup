# Stable Studionet live proof

The submission target is stable GenLayer Studionet:

```text
chain ID: 61999
RPC:      https://studio.genlayer.com/api
```

Do not record a deployment here until its transaction has actually finalized and the contract execution result has been verified.

## 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Verify the network before signing anything

```bash
python scripts/check_network.py
```

Expected output begins:

```text
Studionet verified: chain_id=61999
```

If that check fails, stop. Do not substitute another Studio environment.

## 3. Run the deterministic suite

```bash
python scripts/merkle.py
python scripts/verify_manifest.py fixtures/demo_batch_manifest.json
python scripts/preflight.py
python -m compileall contracts tests examples scripts
pytest tests/direct -v
genvm-lint check contracts/verdictrollup.py
```

## 4. Hosted-network smoke test

```bash
gltest tests/integration/ -v -s --network studionet
```

The original fraud-proof lifecycle below is historical evidence for `0x0d921292939A28d41d9BE4a304b725dcd3A76af0`. The current canonical deployment is `0x87467736FD4243B4c927a0a8CC446Eb266FD6AEa`; its successful compact finality-consumer proof is recorded in [`../DEPLOYMENT.md`](../DEPLOYMENT.md) and [`STUDIONET_LIVE_EVIDENCE.md`](STUDIONET_LIVE_EVIDENCE.md).

## 5. Historical flagship fraud-proof run

The repository contains one intentionally bad leaf. The second leaf is committed as `APPROVED`, while its public source file says the release is `REJECTED`.

Fund/configure two Studionet accounts: one operator and one independent challenger. Then run:

```bash
python scripts/live_fraud_demo.py --contract-address 0x0d921292939A28d41d9BE4a304b725dcd3A76af0
```

The expected lifecycle is:

```text
operator posts root + operator bond
        |
        v
batch = OPEN
        |
challenger proves leaf 1 membership and posts challenger bond
        |
        v
validators independently fetch fixtures/rejected.txt
        |
        v
consensus result = REJECTED
committed result = APPROVED
        |
        v
FRAUD_PROVEN
        |
        v
batch = INVALIDATED
operator remaining bond -> challenger credit
challenger bond -> challenger credit
```

Capture, in full:

- contract address;
- deployment transaction hash;
- create-batch transaction hash;
- challenge transaction hash;
- batch definition hash;
- batch Merkle root;
- challenge record;
- final `INVALIDATED` state;
- challenger credit;
- finalized transaction statuses.

Do not shorten hashes in the canonical evidence record.

## 6. Current compact honest-batch finality proof

The live compact finality proof on the current canonical deployment was run with `python scripts/live_finality_demo.py --contract-address 0x87467736FD4243B4c927a0a8CC446Eb266FD6AEa`. It creates an honest two-leaf batch, reads membership and compact non-finality while OPEN, waits past the challenge deadline, finalizes, then proves the definition-pinned leaf hash check returns true.

The compact consumer checks the finalized state, pinned definition hash, and a compact Merkle proof over the committed leaf hash. Wrong definition hashes and a nonmember leaf hash return false. The full-preimage view remains available, but its larger dynamic payload can hit the documented Studionet RLP decoding limitation; use the compact method for this consumer path.

Direct Mode and the live Studionet proof both demonstrate that membership can be true while the batch is OPEN but finality remains false until the challenge window closes and the batch reaches FINALIZED.
