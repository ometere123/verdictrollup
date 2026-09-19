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

Record the deployment transaction(s), contract address, finalized status and state reads in `DEPLOYMENT.md`.

## 5. Flagship fraud-proof run

The repository contains one intentionally bad leaf. The second leaf is committed as `APPROVED`, while its public source file says the release is `REJECTED`.

Fund/configure two Studionet accounts: one operator and one independent challenger. Then run:

```bash
python scripts/live_fraud_demo.py
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

## 6. Optional honest-batch finality run

For a finality proof, build a separate batch whose committed labels match the public fixtures, use a short but valid challenge period, wait until it expires, then call `finalize_batch`.

Prove both of these reads:

```text
verify_leaf(...)  == true
is_final_leaf(...) == true
```

Also show before finalization that membership is already true while `is_final_leaf(...)` remains false. This demonstrates that VerdictRollup does not confuse a Merkle inclusion proof with optimistic finality.
