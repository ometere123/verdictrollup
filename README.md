# VerdictRollup

**An optimistic rollup primitive for batches of semantic decisions on GenLayer.**

VerdictRollup lets an operator commit many proposed semantic decisions under one Merkle root, back the batch with GEN, and expose every leaf to a public challenge window. GenLayer consensus runs only when a committed leaf is challenged. A confirmed wrong leaf invalidates the whole batch and transfers the operator's remaining bond to the successful challenger. If the challenge window closes without proven fraud, the batch finalizes and other Intelligent Contracts can consume individual leaves with Merkle proofs.

This repository is deliberately **contract-only**. There is no frontend, hosted backend, database, wallet UI, or product flow. The reusable primitive is the submission.

## Target network

VerdictRollup targets **GenLayer Studionet only** for this submission:

- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com/`
- `gltest` network: `studionet`

The repository's test configuration defaults to that network. `scripts/check_network.py` fails closed unless the endpoint reports chain ID `61999`.

## Why this primitive exists

A normal Intelligent Contract evaluates one semantic question per consensus transaction. That is appropriate when each decision deserves immediate consensus, but it scales poorly when another protocol needs hundreds or thousands of similar public decisions.

VerdictRollup changes the cost model:

```text
many semantic questions
        |
        v
operator proposes all results off-chain
        |
        v
canonical leaves -> Merkle root
        |
        v
bonded optimistic batch
        |
        +-------------------------+
        |                         |
  no proven fraud          one leaf challenged
        |                         |
        |                  GenLayer consensus
        |                         |
        |              +----------+----------+
        |              |          |          |
        |            same     unresolved   different
        |              |          |          |
        |         challenge    refund     fraud proven
        |          rejected     bond          |
        |                                    v
        |                              batch invalidated
        v
challenge window closes
        |
        v
batch finalized
        |
        v
consumer proves individual leaf membership
```

The important distinction is that **a Merkle proof establishes membership, not truth or finality**. `verify_leaf(...)` can succeed while a batch is still open. A downstream contract that wants an economically finalized result should use `is_final_leaf(...)`, which requires:

1. the batch to be `FINALIZED`;
2. the caller to pin the exact batch `definition_hash`; and
3. the leaf to verify against the committed Merkle root.

## What GenLayer consensus actually does

The model does not build the batch, compute the Merkle tree, select payouts, choose economic parameters, or decide finality.

For a challenged leaf only, validators independently:

1. fetch the leaf's frozen public HTTPS source;
2. apply the batch's frozen semantic decision rule;
3. choose exactly one label from the batch's frozen label set;
4. require a grounded contiguous source excerpt for every determinate result;
5. independently re-fetch and re-classify rather than trusting the leader's prose.

The leader's proposed batch result is **not shown to the adjudication prompt**. That avoids asking the model to merely confirm or reject the operator's claim.

If independent validators cannot safely resolve the source, the consensus result is `UNRESOLVED`. That outcome does not prove fraud and does not allow the operator to win the challenger's bond: the challenger's bond is returned as an internal credit and the batch stays open.

## Economic protocol

When creating a batch the operator sends GEN with the payable `create_batch(...)` call.

The contract requires:

```text
operator bond >= 2 * challenger bond
```

The multiplier is intentionally simple and deterministic in v0.1.0. It is not an LLM decision.

A challenge must send the **exact** challenger bond. The operator may not challenge its own batch, preventing an operator from deliberately proving its own fraud merely to recover its bond before an independent challenger can claim it.

Challenge outcomes:

| Outcome | Meaning | Batch | Bond result |
|---|---|---|---|
| `REJECTED` | consensus agrees with the committed leaf | remains open | challenger bond credited to operator |
| `INCONCLUSIVE` | consensus returns `UNRESOLVED` | remains open | challenger bond returned to challenger |
| `FRAUD_PROVEN` | consensus reaches a different determinate label | invalidated | challenger gets its bond back plus the operator's remaining batch bond |

Payouts use an internal credit ledger rather than immediate push transfers. `withdraw_credit()` zeroes the account's credit before emitting the finalized native-value transfer.

## Whole-batch invalidation is intentional

VerdictRollup v0.1.0 treats a false committed leaf as proof that the submitted Merkle root is not trustworthy as a finalized semantic batch. The whole batch therefore becomes `INVALIDATED` after the first determinate fraud proof.

That makes the primitive conservative and easy for consumers to reason about:

```text
OPEN         -> individual membership is provable, finality is false
INVALIDATED  -> no leaf can become final
FINALIZED    -> membership + pinned definition hash can satisfy is_final_leaf
```

There is no partial patching of a fraudulent root. The operator must publish a new corrected batch with a new root and new bond.

## Canonical leaf format

The schema is frozen at batch creation:

```json
{
  "title": "Production approval batch",
  "decision_rule": "...",
  "result_labels": ["APPROVED", "REJECTED", "UNRESOLVED"]
}
```

Its canonical JSON is Keccak-256 hashed into `schema_hash`.

Every leaf commits to:

```json
{
  "schema_hash": "...",
  "leaf_index": 0,
  "question": "...",
  "context": "...",
  "source_url": "https://...",
  "proposed_result": "APPROVED"
}
```

The canonical JSON uses sorted keys, compact separators and ASCII escaping. The leaf digest is Ethereum-style Keccak-256.

`source_url` normalization is performed identically by the contract and `scripts/build_batch.py`: HTTPS only, fragments stripped, hostname lower-cased, and private/local/ambiguous host forms rejected.

## Merkle construction

`scripts/merkle.py` is dependency-free and implements Ethereum-style Keccak-256 rather than NIST SHA3-256. It self-tests against the canonical empty-string Keccak vector.

At each Merkle level, an odd final node is duplicated. Proof entries explicitly carry whether the sibling is on the left or right:

```json
[
  {"side":"R","hash":"..."},
  {"side":"L","hash":"..."}
]
```

The contract caps proof depth and verifies the complete proof before invoking any nondeterministic adjudication. A malformed or non-member leaf therefore cannot force unnecessary LLM/web work.

## Batch definition pinning

The immutable `definition_hash` commits to:

- `schema_hash`;
- Merkle root;
- leaf count;
- challenge period;
- challenger bond; and
- operator bond.

Consumers should pin this hash rather than only a batch ID. Two economically different batches can contain the same semantic leaves but do not represent the same security envelope.

## Contract interface

### Writes

`create_batch(...)` — payable; creates the bonded optimistic batch.

`challenge_leaf(...)` — payable; proves membership first, then invokes independent GenLayer adjudication of the challenged leaf.

`finalize_batch(batch_id)` — finalizes an uninvalidated batch after the challenge deadline and credits the remaining operator bond back to the operator.

`withdraw_credit()` — withdraws the caller's accumulated payout credit through a finalized native-value transfer.

### Views

`preview_schema_hash(...)` — computes the exact schema hash before batch creation.

`compute_leaf_hash(...)` — computes a leaf hash using the stored batch schema.

`verify_leaf(...)` — verifies Merkle membership only.

`is_final_leaf(...)` — verifies finalized batch state, pinned definition hash and Merkle membership together.

`get_batch(...)`, `get_challenge(...)`, `get_credit(...)`, `get_status_dictionary()` — reviewer/consumer state reads.

## Demo batch

`fixtures/demo_batch_input.json` contains three leaves:

1. an `APPROVED` leaf whose source says approved;
2. a deliberately fraudulent `APPROVED` leaf whose source explicitly says rejected;
3. an `UNRESOLVED` leaf whose source gives no decision.

Build it:

```bash
python scripts/build_batch.py fixtures/demo_batch_input.json \
  -o fixtures/demo_batch_manifest.json
python scripts/verify_manifest.py fixtures/demo_batch_manifest.json
```

The committed demo root currently is:

```text
e46676e2a49441e0c702a964cd9537249f44bf73cea92d1765620ef533faccc5
```

The deliberately false second leaf is useful for the live fraud-proof demonstration: once that exact leaf and its Merkle proof are challenged, validators should independently read the rejected fixture and produce `REJECTED`, which differs from the committed `APPROVED` result. The expected protocol consequence is whole-batch invalidation and the challenge payout credit.

## Tests

### Dependency-free checks

```bash
python scripts/merkle.py
python scripts/verify_manifest.py fixtures/demo_batch_manifest.json
python scripts/preflight.py
python -m compileall contracts tests examples scripts
```

### Direct Mode

```bash
pip install -r requirements-test.txt
pytest tests/direct -v
```

The suite covers the optimistic state machine, exact off-chain/on-chain hashing, Merkle tampering, malicious leader results, ungrounded evidence, unresolved sources, exact bonds, operator self-challenge prevention, early/late challenge boundaries, whole-batch invalidation, finality separation and economic-definition pinning.

### Stable Studionet

Before any remote action:

```bash
python scripts/check_network.py
```

Then:

```bash
gltest tests/integration/ -v -s --network studionet
```

The integration suite deploys the contract, creates a bonded batch, reads the stored commitment back and verifies a canonical leaf on the hosted network. The full two-account semantic fraud-proof lifecycle is documented in `docs/LIVE_DEMO.md` because it requires separate funded operator and challenger accounts.

## Security boundaries

VerdictRollup deliberately does **not** claim any of the following:

- An unchallenged leaf was individually re-adjudicated by GenLayer.
- A finalized batch is universally true. Finality means it survived the declared optimistic challenge protocol.
- A public webpage is authoritative merely because it is public.
- An `UNRESOLVED` challenge proves the operator correct or incorrect.
- A Merkle proof means a batch has finalized.
- The contract can recover an omitted leaf that was never committed to the root.

The primitive assumes that challengers have reason and opportunity to inspect the public manifest during the challenge window. An operator can only obtain optimistic finality after accepting the risk of a bonded fraud proof.

See `docs/THREAT_MODEL.md` for the full attack analysis.

## Repository layout

```text
contracts/verdictrollup.py              core Intelligent Contract
scripts/build_batch.py                  canonical manifest/root/proof builder
scripts/merkle.py                       dependency-free Keccak + Merkle implementation
scripts/verify_manifest.py              offline manifest audit
scripts/check_network.py                stable Studionet chain guard
scripts/preflight.py                     reviewer-facing static checks
fixtures/                               public demo evidence + canonical manifest
tests/direct/                           fast adversarial protocol tests
tests/integration/                      real hosted-network smoke tests
examples/final_leaf_gate.py             minimal downstream consumer example
docs/PROTOCOL.md                        state machine and invariants
docs/THREAT_MODEL.md                    adversarial analysis
docs/LIVE_DEMO.md                       exact live proof path
SUBMISSION.md                           reviewer-facing summary
DEPLOYMENT.md                           canonical deployment evidence record
```

## Scope

VerdictRollup is an optimistic semantic decision primitive. It is not a generic data-availability layer, a validity rollup, a frontend product, a prediction market, a dispute application, or an escrow. Its narrow job is to let many publicly inspectable semantic decisions share one bonded commitment while preserving a permissionless path for a single committed leaf to trigger full GenLayer consensus and invalidate a fraudulent batch.

## Live Studionet evidence

The canonical deployment and live batch/challenge readbacks are recorded in [docs/STUDIONET_LIVE_EVIDENCE.md](docs/STUDIONET_LIVE_EVIDENCE.md). The contract is deployed on Studionet chain `61999` at [`0x0d921292939A28d41d9BE4a304b725dcd3A76af0`](https://explorer-studio.genlayer.com/address/0x0d921292939A28d41d9BE4a304b725dcd3A76af0). The demo proves a finalized `FRAUD_PROVEN` challenge invalidates batch 1 and credits the challenger, and an honest batch 2 reaches `FINALIZED` after its challenge window.

**Live-read limitation:** the current Studionet RPC rejects the eight-argument `is_final_leaf` view with an RLP surplus-bytes error through both CLI and Python SDK. This return is not claimed as live evidence; details and successful adjacent readbacks are documented in the evidence record.

No frontend has been added.
