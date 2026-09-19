# VerdictRollup — submission notes

## Category

Standalone GenLayer Intelligent Contract / reusable primitive. No frontend.

## One-line description

VerdictRollup lets many public semantic decisions share one bonded Merkle commitment while any committed leaf can trigger independent GenLayer consensus and invalidate a fraudulent batch.

## Why it matters

Ordinary Intelligent Contracts run consensus for every semantic decision. VerdictRollup introduces an optimistic alternative for large publicly inspectable batches: the operator computes proposed decisions off-chain, commits the complete batch under a Merkle root and posts GEN. Only challenged leaves invoke GenLayer's web/LLM consensus. A determinate wrong leaf invalidates the whole root and transfers the operator bond to the challenger. An unchallenged root may finalize after its challenge window.

This is intentionally not a thin `AI decides X` wrapper. GenLayer judgement is one component inside a larger deterministic protocol containing canonical hashing, Merkle membership, challenge windows, bonds, fraud invalidation, pull-based settlement, terminal batch state and consumer finality proofs.

## Consensus design

The challenged leaf has an exact source URL, question, context, schema and allowed labels already committed in the root.

The leader independently fetches the source and classifies it without being shown the operator's proposed result. A determinate leader result must include a short contiguous excerpt from the fetched source.

Validators independently re-fetch and re-classify the exact same source under the frozen rule. Acceptance requires an exact label match. For determinate labels, the leader's excerpt must also occur in the validator's own source snapshot.

`UNRESOLVED` is first-class. An unavailable or genuinely ambiguous source is not automatically fraud and does not let the operator confiscate the challenger's bond.

## Deterministic protocol logic

The contract, not the model, controls:

- schema and leaf canonicalization;
- Ethereum-style Keccak-256 hashes;
- Merkle membership;
- challenge deadline;
- exact bond requirements;
- operator self-challenge prevention;
- challenge outcome mapping;
- whole-batch invalidation;
- terminal finalization;
- definition-hash pinning;
- payout credits; and
- consumer finality checks.

## Reusability

A producer can use `scripts/build_batch.py` to build a canonical manifest and proofs without third-party crypto dependencies.

A consumer can call `is_final_leaf(...)` and pin the batch `definition_hash` so it depends on both the exact leaf and the exact economic security envelope. `examples/final_leaf_gate.py` shows the minimal downstream pattern.

## Reviewer path

1. Run `python scripts/preflight.py`.
2. Run `python scripts/merkle.py` and verify the canonical demo manifest.
3. Run `pytest tests/direct -v` after installing `requirements-test.txt`.
4. Inspect the malicious-leader and forged-evidence regressions.
5. Run the stable-Studionet integration suite.
6. Use `scripts/live_fraud_demo.py` with two funded accounts to challenge the intentionally false second demo leaf.

## Network

Submission target: stable GenLayer Studionet, chain ID `61999`, RPC `https://studio.genlayer.com/api`.

## Current evidence status

The contract is live on Studionet 61999. A real bonded adversarial challenge finalized as `FRAUD_PROVEN`, invalidated its batch, and credited the independent challenger. A separate honest batch finalized after its challenge period; membership was verified both before and after finalization. Exact deployment, challenge, finalization transactions and readbacks are in [`docs/STUDIONET_LIVE_EVIDENCE.md`](docs/STUDIONET_LIVE_EVIDENCE.md).

The live RPC currently fails when reading the eight-argument `is_final_leaf` view with an RLP surplus-bytes error. Accordingly, the live `is_final_leaf == true` result is not claimed. See the evidence record for detail.
