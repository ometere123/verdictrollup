# VerdictRollup — observed Studionet live evidence

This evidence was collected on 2026-09-20 from the existing deployment. Network was checked immediately before writes using `eth_chainId`; it returned `0xf22f` (61999). No contract was redeployed.

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

The deployed schema exposes `is_final_leaf` with the expected eight parameters. However, both GenLayer CLI `0.39.1` and `genlayer-py`/`gltest` read calls to this eight-argument method fail at the Studionet RPC layer with `RLP string ends with 308 superfluous bytes` (the earlier integration run reported 283 bytes for its call). The same clients successfully read `get_batch`, `get_challenge`, `get_credit`, and the seven-argument `verify_leaf`. Therefore the live `is_final_leaf == true` result is **not claimed**. Direct Mode covers the distinction: membership is true while `OPEN` and finality false until finalization. The live writes and terminal state are finalized, but the external RPC call-path issue remains unresolved.

## Reproduction and source boundary

Run the documented offline checks and Direct Mode tests first, then use the exact contract/fixture manifest and two funded Studionet accounts. Check chain ID `61999` immediately before every write. The CLI's signer is separate from the Python integration accounts; public addresses only are recorded here. No private wallet material is in this repository.

The CLI receipt for the challenge contains the leader's grounded result and validator agreement; idle validators were cancelled after quorum, not treated as execution failures. No fee amount is claimed here: the displayed transaction `value` is the protocol bond, not outer transaction fee accounting.
