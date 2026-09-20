# VerdictRollup — observed Studionet live evidence

This record preserves evidence from both the original deployment and the compact-consumer deployment. All writes below were made on Studionet chain `61999` (`https://studio.genlayer.com/api`); the network guard checks `eth_chainId` before remote writes.

## Current canonical deployment and compact finality proof

- Network: GenLayer Studionet, chain ID `61999`; RPC `https://studio.genlayer.com/api`.
- Explorer: `https://explorer-studio.genlayer.com`.
- Contract: [`0x87467736FD4243B4c927a0a8CC446Eb266FD6AEa`](https://explorer-studio.genlayer.com/address/0x87467736FD4243B4c927a0a8CC446Eb266FD6AEa).
- Deployment tx: [`0x5d3c414c0df994ca573bb7984a004d72b9a68bb7b3e37ef0062c7109bf36654`](https://explorer-studio.genlayer.com/tx/0x5d3c414c0df994ca573bb7984a004d72b9a68bb7b3e37ef0062c7109bf36654) — `FINALIZED / MAJORITY_AGREE / SUCCESS`.
- Source commit: `84769eb44cdb567d103247645b8ecedeb05e2203`; 40,650 bytes; SHA-256 `6b047e8aebf8ce3b077c22776ad4fe616c0da6f763ba2b364e0ca06ba1af6c69`.
- CLI: local GenLayer CLI `0.39.1`; `eth_chainId` returned `0xf22f` (61999) before deployment and live writes.

An honest two-leaf batch was created on this deployment and finalized after its 60-second challenge window. Create tx [`0x5c11e112bf2c5b49faac98efb4cb7cae377093e2b475b8e4843fb995e15af59a`](https://explorer-studio.genlayer.com/tx/0x5c11e112bf2c5b49faac98efb4cb7cae377093e2b475b8e4843fb995e15af59a) and finalize tx [`0xcd248150bce940966a339d326704f080c72406f74ab041c98bc5c63acada23`](https://explorer-studio.genlayer.com/tx/0xcd248150bce940966a339d326704f080c72406f74ab041c98bc5c63acada23) both returned `FINALIZED / MAJORITY_AGREE / SUCCESS`.

- Batch ID `1`; final state readback `FINALIZED`.
- Definition hash `c1954a03d35c048528df8036bac0601f37c8a0fc8daf47a737a01f3026fc8f2b`.
- Merkle root `29cfb78d4001646327aa91bf4e90bd290d283095f2cac017c41fa1fca155c36d`.
- Leaf hash `08fb0400904570543ad27423c13cdca93a7abbd41ddb6a0f4ae2feeee984a7ef`.
- Before finalization: full `verify_leaf == true`; compact finality view `== false`.
- After finalization: `is_final_leaf_hash(batch_id=1, pinned_definition_hash, leaf_hash, compact_proof) == true`.
- Wrong definition hash returned `false`; zero/nonmember leaf hash returned `false`.
- Compact proof: `Rb65629504a251687ede977cb8bb912717c3445d03a3bd60c0892d9437744da5d8`.
- Create call value was the 2,000-unit operator bond, not a transaction-fee figure. Settled fee consumption/refund were not available in the observed receipt response and are not claimed.
- Demo signer funding tx: [`0x9b0c3f31013cd65a6c2c64900be696f074fcab37b3cd4520b35b519cdb2f5d89`](https://explorer-studio.genlayer.com/tx/0x9b0c3f31013cd65a6c2c64900be696f074fcab37b3cd4520b35b519cdb2f5d89), transfer of 0.0001 GEN to the temporary demo signer.

### RLP investigation

The earlier failure was not determined by argument count alone or by one particular dynamic field. A short eight-argument call to the old view decoded and returned `false`; short-data membership reads worked. Increasing dynamic payload size caused RLP surplus-byte or undersized-list errors. Passing proof JSON as a string did not eliminate it. CLI and Python SDK calls showed the same failure class. This establishes a payload-size-sensitive issue in the live Studionet RPC/transaction decoding path, but the available evidence does not identify whether RLP framing or the subsequent GenVM ABI decoder is the precise defective layer. The compact view avoids repeating dynamic leaf-preimage fields and directly verifies definition-pinned Merkle membership plus `FINALIZED` state.

## Earlier deployment — historical evidence

## Deployment

- Network: GenLayer Studionet, chain ID `61999`
- RPC: `https://studio.genlayer.com/api`
- Explorer: `https://explorer-studio.genlayer.com`
- Contract: [`0x0d921292939A28d41d9BE4a304b725dcd3A76af0`](https://explorer-studio.genlayer.com/address/0x0d921292939A28d41d9BE4a304b725dcd3A76af0)
- Source commit: `982eb86315be92aeb9a61f9c8210b81ac496518b`
- Source SHA-256: `7365ddd848e5e99f9cb39d708943769589e90fe0d9da71158d30f5bd0c572a97` (39,935 bytes)
- Deployer: `0x951e6B75530774fF82321a5ae54e14F778F0C855`
- Deployment tx: [`0x64703c09a112f4c4ab447397898bac78b1af6789ce802e94ede04b33784638f1`](https://explorer-studio.genlayer.com/tx/0x64703c09a112f4c4ab447397898bac78b1af6789ce802e94ede04b33784638f1)
- Receipt: `FINALIZED / MAJORITY_AGREE`; leader execution `SUCCESS`; all five validators agreed.
- CLI used: GenLayer CLI `0.39.1`, explicit local executable `.../node_modules/genlayer/dist/index.js`.

## Fraud-proof lifecycle — batch 1

Canonical demo root: `e46676e2a49441e0c702a964cd9537249f44bf73cea92d1765620ef533faccc5`. Leaf 1 is committed as `APPROVED`, while its public source states `REJECTED`.

| Action | Transaction | Observed state |
|---|---|---|
| Create and bond batch 1 | [`0xb4c49a9a220e05e21599d89157f2639cc63bbcf9e4624f8ea7114680c0987f9b`](https://explorer-studio.genlayer.com/tx/0xb4c49a9a220e05e21599d89157f2639cc63bbcf9e4624f8ea7114680c0987f9b) | `FINALIZED / MAJORITY_AGREE / SUCCESS`; batch `OPEN`; 2,000 operator bond; definition hash `9d4cf2d7b0461ac268bbdec15ca8de09c54b687beb5070a0bec1c37faba08ad4` |
| Challenge leaf 1 from independent challenger | [`0xbd25d9fda8e10efb810a3baa2ca0db81cef2d46103a7463d25186ee2e08b5197`](https://explorer-studio.genlayer.com/tx/0xbd25d9fda8e10efb810a3baa2ca0db81cef2d46103a7463d25186ee2e08b5197) | `FINALIZED / MAJORITY_AGREE / SUCCESS`; 1,000 challenger bond; semantic result `REJECTED`; `FRAUD_PROVEN`; batch `INVALIDATED` |

- Batch ID: `1`; challenge ID: `1`; leaf index: `1`.
- Operator: `0x951e6B75530774fF82321a5ae54e14F778F0C855`.
- Challenger: `0xB845a69860ba4CDf19CfDC5AfbAF2e20b6bE86b0`.
- Independently returned excerpt: `Project Borealis release 2026.09 is REJECTED for production deployment`.
- Reason: `Source explicitly states the release is REJECTED for production deployment`.
- Batch readback: status `INVALIDATED`, remaining bond `0`, successful challenge ID `1`.
- Challenge readback: outcome `FRAUD_PROVEN`, consensus `REJECTED`, payout credit `3000`.
- `get_credit(challenger)` independently returned `3000`; this equals the 1,000 challenger bond plus 2,000 remaining operator bond. Credit is recorded internally; no withdrawal is claimed.

## Honest finality lifecycle — batch 2

- Create tx: [`0x691b70fd3f34d96869b367176abfcb7db87551e0a73ec8104baa0db8e7d8c5d7`](https://explorer-studio.genlayer.com/tx/0x691b70fd3f34d96869b367176abfcb7db87551e0a73ec8104baa0db8e7d8c5d7) — `FINALIZED / MAJORITY_AGREE / SUCCESS`; 2,000 operator bond; 60-second challenge period.
- Finalize tx: [`0x42b1dc3a5e987674f49d48fe60a690c4b6475a35736b575634b92756345ba678`](https://explorer-studio.genlayer.com/tx/0x42b1dc3a5e987674f49d48fe60a690c4b6475a35736b575634b92756345ba678) — `FINALIZED / MAJORITY_AGREE / SUCCESS` after the deadline.
- Batch ID: `2`; final readback status `FINALIZED`; resolved timestamp `1789861114`.
- Definition hash: `b0d18d4d73e500b92e5a801cf31e6f68c8edbad96991f90f920ae49409c20526`.
- Merkle root / one-leaf hash: `2ec2157d889a9b7327385af7b145228d1dccedbc7c6445533edf37519feab45f`.
- The approved fixture leaf was present before finalization (`verify_leaf == true`) while batch 2 was `OPEN`; after finalization, `verify_leaf == true` and state readback was `FINALIZED`.

### Live read limitation

On the original deployment, the schema exposed `is_final_leaf` with the expected eight parameters. At that time, both GenLayer CLI `0.39.1` and `genlayer-py`/`gltest` read calls to this eight-argument method fail at the Studionet RPC layer with `RLP string ends with 308 superfluous bytes` (the earlier integration run reported 283 bytes for its call). Those same clients successfully read `get_batch`, `get_challenge`, `get_credit`, and the seven-argument `verify_leaf`. Therefore no live `is_final_leaf == true` result was claimed for that original address. Direct Mode covers the distinction: membership is true while `OPEN` and finality false until finalization. The live writes and terminal state are finalized, but the full-preimage read limitation on that original address remains part of this historical record; the compact consumer is proven live above.

## Reproduction and source boundary

Run the documented offline checks and Direct Mode tests first, then use the exact contract/fixture manifest and two funded Studionet accounts. Check chain ID `61999` immediately before every write. The CLI's signer is separate from the Python integration accounts; public addresses only are recorded here. No private wallet material is in this repository.

The CLI receipt for the challenge contains the leader's grounded result and validator agreement; idle validators were cancelled after quorum, not treated as execution failures. No fee amount is claimed here: the displayed transaction `value` is the protocol bond, not outer transaction fee accounting.
