# Threat model

VerdictRollup assumes an adversarial operator, adversarial challengers, adversarial source content, potentially faulty leaders and ordinary web availability failures.

## Malicious operator commits a wrong result

Mitigation: every public leaf has a deterministic Merkle proof and can be challenged. A determinate consensus result that differs from the committed proposal invalidates the whole batch and transfers the remaining operator bond to the successful challenger.

## Operator tries to challenge its own known fraud

If self-challenge were allowed, a dishonest operator could intentionally prove its own bad leaf before another party and recover the bond to itself. `challenge_leaf` therefore rejects the batch operator as challenger.

## Challenger invents a leaf that was never committed

Mitigation: the contract reconstructs the canonical leaf hash and verifies the complete Merkle proof before any semantic adjudication occurs.

## Challenger changes one field of a real leaf

Question, context, source URL, proposed label, index and schema hash all contribute to the leaf digest. Any changed committed field changes the digest and invalidates the original proof.

## Leader simply agrees with the operator

The proposed operator label is not passed to the semantic adjudication prompt. Validators independently fetch and classify the source and require exact agreement with the leader's label.

## Leader returns a fabricated quote

For every determinate label, the excerpt must occur in the leader's source snapshot. Validators independently fetch the source and require the same excerpt to occur in their own snapshot as well.

## Source contains prompt injection

Question/context/rules are constrained to passive inputs and obvious control phrases are rejected. More importantly, the prompt explicitly treats source material as hostile data. Independent validator execution limits a single model's ability to convert source instructions into accepted state.

VerdictRollup does not claim prompt injection is mathematically eliminated. A consumer should choose public evidence surfaces appropriate to its domain.

## Source disappears during a valid challenge

Unavailability resolves to `UNRESOLVED`, not fraud. When a determinate operator proposal can no longer be re-adjudicated safely, the challenger's bond is refunded and the batch stays open.

This does mean data availability matters economically: a batch whose sources disappear could survive if no determinate fraud proof can be obtained before expiry. The protocol is intended for publicly inspectable sources that remain available during the challenge window.

## Operator commits an `UNRESOLVED` result to hide a known answer

A challenger may still challenge that leaf. If consensus reaches a determinate allowed label, the committed `UNRESOLVED` differs from consensus and fraud is proven.

## Spam challenges

Every challenge requires the exact configured bond. A rejected challenge transfers that bond to the operator. Inconclusive challenges are refunded because charging a challenger for source/consensus uncertainty would create a griefing vector in the opposite direction.

Repeated inconclusive challenges still consume protocol fees and do not alter batch finality or the operator bond.

## Reentrancy/value-transfer concerns

Challenge settlement and finalization write only to an internal credit ledger. `withdraw_credit()` sets the credit to zero before emitting the finalized native-value transfer. External value transfer is therefore separated from the semantic challenge transaction.

## Weakly bonded batch

The definition hash includes both operator and challenger bond values as well as the challenge period. A downstream consumer can pin the exact definition hash rather than accepting any batch with the same root.

VerdictRollup does not tell consumers what bond is sufficient for their economic risk. That is a consumer-policy decision.

## Wrong Merkle implementation off-chain

`scripts/merkle.py` is dependency-free, self-tests Ethereum-style Keccak-256, and `scripts/verify_manifest.py` re-verifies every generated leaf proof. Direct tests compare off-chain builder hashes with contract hashes.

## Finality confused with membership

The API intentionally separates `verify_leaf` and `is_final_leaf`. Reviewer tests prove that membership may be true while optimistic finality is false.

## Network confusion

This submission's configuration targets stable Studionet chain `61999` at `https://studio.genlayer.com/api`. `scripts/check_network.py` checks the RPC chain ID before remote deployment/testing. Repository preflight also rejects non-target Studio-preview identifiers.
