# Reviewer guide

VerdictRollup is easiest to review in five layers.

## 1. Verify the batch builder independently

```bash
python scripts/merkle.py
python scripts/build_batch.py fixtures/demo_batch_input.json -o /tmp/verdictrollup.json
python scripts/verify_manifest.py /tmp/verdictrollup.json
```

Compare the resulting root to `fixtures/demo_batch_manifest.json`.

## 2. Read the deterministic protocol first

Start with these functions in `contracts/verdictrollup.py`:

- `create_batch`
- `verify_merkle_proof`
- `challenge_leaf`
- `finalize_batch`
- `is_final_leaf` and compact `is_final_leaf_hash`
- `withdraw_credit`

The economic state machine does not depend on LLM prose.

## 3. Inspect the consensus boundary

Then inspect:

- `adjudication_prompt`
- `inspect_leaf_once`
- `_adjudicate_consensus`

The proposed operator label is excluded from the adjudication prompt. The validator independently re-fetches and re-classifies the exact source.

## 4. Inspect the deliberately fraudulent fixture

`fixtures/demo_batch_input.json` deliberately commits the second leaf as `APPROVED` while `fixtures/rejected.txt` explicitly says `REJECTED`.

Its proof is included in `fixtures/demo_batch_manifest.json`. This gives reviewers a deterministic leaf to use for the live fraud path.

## 5. Check the negative properties

The direct suite explicitly tests that:

- a non-member leaf cannot trigger adjudication;
- changing a committed label breaks membership;
- a malicious leader classification is rejected;
- fabricated evidence is rejected;
- an empty/unavailable source becomes inconclusive rather than fraud;
- the operator cannot self-challenge;
- a fraud proof invalidates the entire batch;
- an invalidated batch cannot finalize;
- an open batch may prove membership but not finality;
- a wrong batch definition hash cannot satisfy either finality interface; compact `is_final_leaf_hash` is the live-verified consumer route.

Run `python scripts/preflight.py` for a dependency-free structural audit.
