# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Minimal consumer showing how another IC can require a finalized rollup leaf.

This example is intentionally not part of VerdictRollup's deployed primitive.
It demonstrates the consumer boundary without turning the repository into an app.
"""

from genlayer import *


@gl.contract_interface
class IVerdictRollupConsumer:
    class View:
        def is_final_leaf_hash(
            self, batch_id: u256, expected_definition_hash: u256,
            leaf_hash_value: u256, compact_proof: str,
        ) -> bool: ...

    class Write:
        pass


class FinalLeafGate(gl.Contract):
    rollup_address: Address
    consumed: TreeMap[str, bool]

    def __init__(self, rollup_address: Address):
        self.rollup_address = rollup_address

    @gl.public.write
    def consume(
        self,
        action_hash: str,
        batch_id: u256,
        expected_definition_hash: u256,
        leaf_hash_value: u256,
        compact_proof: str,
    ) -> None:
        key = str(action_hash).strip().lower()
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise gl.vm.UserError("EXPECTED: action_hash must be 32-byte lowercase hex")
        if self.consumed.get(key) is True:
            raise gl.vm.UserError("EXPECTED: action already consumed")

        rollup = IVerdictRollupConsumer(self.rollup_address)
        if not rollup.view().is_final_leaf_hash(
            batch_id,
            expected_definition_hash,
            leaf_hash_value,
            compact_proof,
        ):
            raise gl.vm.UserError("EXPECTED: rollup leaf is not finalized and valid")
        self.consumed[key] = True

    @gl.public.view
    def was_consumed(self, action_hash: str) -> bool:
        return self.consumed.get(str(action_hash).strip().lower()) is True
