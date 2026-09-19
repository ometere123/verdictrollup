# VerdictRollup protocol

## 1. Objects

A **schema** defines one bounded semantic decision family: title, decision rule and allowed labels. `UNRESOLVED` is mandatory.

A **leaf** binds the schema hash, index, exact question, exact context, normalized public source URL and operator-proposed label.

A **batch** binds one Merkle root plus the economic/challenge parameters that secure that root.

A **challenge** proves a committed leaf, re-adjudicates only that leaf under GenLayer consensus, and applies a deterministic economic outcome.

## 2. Canonical hashes

The protocol uses compact, sorted, ASCII JSON and Ethereum-style Keccak-256.

```text
schema_hash = keccak(canonical(schema))
leaf_hash = keccak(canonical(leaf))
merkle_root = merkle(leaf_hashes)
definition_hash = keccak(canonical(batch security definition))
```

The definition hash intentionally contains economic parameters. A consumer that pins only a root cannot distinguish a strongly bonded batch from the same root posted under a weaker challenge configuration.

## 3. Merkle rule

Leaves preserve list order. At every level, an odd final node is duplicated. Proof entries carry `L` or `R`; sorted-pair hashing is not used.

This makes the preimage and proof construction unambiguous and permits the contract to reject malformed membership claims before performing nondeterministic work.

## 4. Batch state machine

```text
                 fraud proved
              +-----------------> INVALIDATED
              |
OPEN ---------+
  |
  | challenge deadline passes
  | and no fraud was proved
  v
FINALIZED
```

Both terminal states are irreversible.

A finalized batch cannot be challenged. An invalidated batch cannot finalize.

## 5. Challenge state machine

After Merkle membership succeeds, validators independently re-fetch the public source and classify the leaf using the frozen schema.

```text
consensus == proposed result
    -> REJECTED
    -> batch stays OPEN
    -> challenger's bond becomes operator credit

consensus == UNRESOLVED and proposed != UNRESOLVED
    -> INCONCLUSIVE
    -> batch stays OPEN
    -> challenger receives its bond back as credit

determinate consensus != proposed result
    -> FRAUD_PROVEN
    -> entire batch becomes INVALIDATED
    -> challenger receives challenger bond + remaining operator bond
```

If the committed proposal itself is `UNRESOLVED` and consensus independently returns `UNRESOLVED`, the challenge is `REJECTED` because the committed leaf matches the consensus result.

## 6. Why unresolved is not fraud

Web access can fail. A page can disappear. A source can be ambiguous. Validators can honestly be unable to establish one allowed determinate label.

Treating that as fraud would let availability failures steal operator bonds. Treating it as an operator win would let availability failures confiscate challenger bonds.

VerdictRollup therefore makes `UNRESOLVED` a first-class outcome and refunds the challenger when an originally determinate proposal cannot be safely re-adjudicated.

## 7. Why whole-batch invalidation

v0.1.0 does not patch one leaf in place. The Merkle root is the batch commitment. If any exact committed leaf is proven wrong, that root is no longer allowed to reach optimistic finality.

The operator must publish a fresh corrected root under a fresh bond.

This trades throughput for simple consumer semantics and prevents an operator from repeatedly repairing a low-quality root during its challenge period.

## 8. Validator duties

The leader:

1. renders the exact committed public source;
2. receives only the frozen question/context/rule/label set, not the operator's proposed label;
3. chooses one allowed label;
4. returns a brief reason;
5. for determinate outcomes, returns one short contiguous excerpt from the source.

A validator independently repeats the source fetch and semantic classification. It rejects the leader unless:

- the leader result has the expected shape;
- the independent label exactly matches;
- a determinate leader excerpt occurs in the validator's own fetched source; and
- `UNRESOLVED` contains no fabricated evidence excerpt.

This is substantive re-adjudication, not JSON-format validation.

## 9. Economic invariants

- `challenger_bond > 0`.
- operator bond is at least twice the challenger bond.
- a challenge must send the exact configured amount.
- the operator cannot challenge its own batch.
- a fraud payout can consume the operator bond only once because fraud terminally invalidates the batch.
- withdrawals follow checks/effects/interactions: credit is zeroed before the finalized value transfer is emitted.
- batch finalization returns only the still-remaining operator bond.

## 10. Consumer invariant

`verify_leaf(...) == true` means only:

> this canonical leaf is in this batch's committed root.

`is_final_leaf(...) == true` means:

> this canonical leaf is in the committed root, the batch survived its challenge protocol and finalized, and the caller supplied the exact frozen batch definition hash.

Consumer contracts that depend on optimistic finality should use the latter.
