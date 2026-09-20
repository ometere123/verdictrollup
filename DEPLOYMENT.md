# VerdictRollup — Studionet deployment and live evidence

## Canonical deployment

- Network: GenLayer Studionet
- Chain ID: `61999`
- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com`
- Contract: [`0x87467736FD4243B4c927a0a8CC446Eb266FD6AEa`](https://explorer-studio.genlayer.com/address/0x87467736FD4243B4c927a0a8CC446Eb266FD6AEa)
- Deployment transaction: [`0x5d3c414c0df994ca573bb7984a004d72b9a68bb7b3e37ef0062c7109bf36654`](https://explorer-studio.genlayer.com/tx/0x5d3c414c0df994ca573bb7984a004d72b9a68bb7b3e37ef0062c7109bf36654)
- Result: `FINALIZED / MAJORITY_AGREE / SUCCESS`
- Source commit: `84769eb44cdb567d103247645b8ecedeb05e2203`
- Deployed source: 40,650 bytes; SHA-256 `6b047e8aebf8ce3b077c22776ad4fe616c0da6f763ba2b364e0ca06ba1af6c69`
- CLI: GenLayer CLI `0.39.1`; local executable; RPC chain ID independently checked before deployment.

## Live compact finality-consumer proof

The old full-preimage `is_final_leaf` view remains in the contract. A compact public consumer view, `is_final_leaf_hash(batch_id, expected_definition_hash, leaf_hash, compact_proof)`, was added without changing storage or protocol transitions. It requires the batch to be `FINALIZED`, pins the stored definition hash, and verifies the committed leaf hash against the stored Merkle root using a bounded compact sibling proof. A consumer that needs the original leaf fields can separately validate their preimage against `leaf_hash`.

A separate honest two-leaf batch was created and finalized on this deployment:

| Action | Transaction | Final result |
|---|---|---|
| Create/bond batch 1 | [`0x5c11e112bf2c5b49faac98efb4cb7cae377093e2b475b8e4843fb995e15af59a`](https://explorer-studio.genlayer.com/tx/0x5c11e112bf2c5b49faac98efb4cb7cae377093e2b475b8e4843fb995e15af59a) | `FINALIZED / MAJORITY_AGREE / SUCCESS`; batch `OPEN`; operator bond 2,000; challenge bond 1,000; challenge period 60 seconds |
| Finalize after challenge window | [`0xcd248150bce940966a339d326704f080c72406f74ab041c98bc5c63acada23`](https://explorer-studio.genlayer.com/tx/0xcd248150bce940966a339d326704f080c72406f74ab041c98bc5c63acada23) | `FINALIZED / MAJORITY_AGREE / SUCCESS`; batch state read back as `FINALIZED` |

Readback for batch `1`:

- Definition hash: `c1954a03d35c048528df8036bac0601f37c8a0fc8daf47a737a01f3026fc8f2b`
- Merkle root: `29cfb78d4001646327aa91bf4e90bd290d283095f2cac017c41fa1fca155c36d`
- Tested leaf hash: `08fb0400904570543ad27423c13cdca93a7abbd41ddb6a0f4ae2feeee984a7ef`
- While `OPEN`: `verify_leaf == true`; compact finality view `== false`.
- After finalization: compact finality view with the committed definition and proof `== true`.
- Wrong definition hash: `false`; nonmember leaf hash: `false`.
- Both writes returned `FINALIZED / MAJORITY_AGREE / SUCCESS`; the live runner observed the state and view results above.

The batch transaction carried a 2,000-unit protocol bond; this is not a transaction-fee figure. The RPC/CLI receipt path did not provide a reliable settled fee-consumed/refund breakdown, so none is claimed here. A temporary demo signer was funded with 0.0001 GEN for the run; transfer tx: `0x9b0c3f31013cd65a6c2c64900be696f074fcab37b3cd4520b35b519cdb2f5d89`.

## RLP issue investigation

The failure is payload-size-dependent, not simply caused by the eight-argument arity or one uniquely bad dynamic parameter. Short eight-argument calls to the old view decoded and returned `false`; a seven-argument membership call with short data also worked. Increasing dynamic calldata (including the `context` string) crossed a threshold and produced RLP surplus-byte / undersized-list errors. Explicitly passing `proof_json` as a string did not remove the failure. CLI and Python SDK calls exhibited the same class of error on Studionet. The available evidence localizes this to the live RPC/transaction decoding path for larger dynamic payloads; it does not establish whether the precise defect is in RPC RLP framing or the downstream GenVM ABI decoder.

The compact interface removes repeated dynamic leaf preimage fields from the live consumer call while preserving definition pinning and Merkle-root membership.

## Historical deployment and lifecycle

The earlier deployment remains documented, not erased: [`docs/STUDIONET_LIVE_EVIDENCE.md`](docs/STUDIONET_LIVE_EVIDENCE.md) preserves its deployment, fraud-proof challenge, honest-batch evidence and the original RLP failure. That deployment is superseded for current consumer integration by the compact-view deployment above. Its fraud-proof lifecycle remains valid historical evidence for the earlier contract address; it is not attributed to this new address.

## Reproduction

```bash
python scripts/check_network.py
python scripts/preflight.py
python scripts/merkle.py
python scripts/verify_manifest.py fixtures/demo_batch_manifest.json
python -m pytest tests/direct -v
GENVM_VERSION=v0.2.16 genvm-lint check contracts/verdictrollup.py
python scripts/live_finality_demo.py --contract-address 0x87467736FD4243B4c927a0a8CC446Eb266FD6AEa
```
