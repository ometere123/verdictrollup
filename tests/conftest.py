import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


if os.name == "nt":
    # genlayer-test 0.29.2 replaces fd 0 with a temporary message file, then
    # unlinks it immediately. Windows cannot unlink a file while the duplicated
    # stdin handle is still open. Defer removal until Direct Mode restores stdin.
    from gltest.direct import loader as direct_loader
    from gltest.direct.vm import VMContext

    def _inject_message_to_fd0_windows(vm):
        from genlayer.py import calldata
        from genlayer.py.types import Address
        sender_addr = Address(vm.sender) if isinstance(vm.sender, bytes) else vm.sender
        contract_addr = (
            Address(vm._contract_address)
            if isinstance(vm._contract_address, bytes)
            else vm._contract_address
        )
        origin_addr = Address(vm.origin) if isinstance(vm.origin, bytes) else vm.origin
        message_data = {
            "contract_address": contract_addr,
            "sender_address": sender_addr,
            "origin_address": origin_addr,
            "stack": [],
            "value": vm._value,
            "datetime": vm._datetime,
            "is_init": False,
            "chain_id": vm._chain_id,
            "entry_kind": 0,
            "entry_data": b"",
            "entry_stage_data": None,
        }
        fd, path = tempfile.mkstemp()
        try:
            os.write(fd, calldata.encode(message_data))
            os.lseek(fd, 0, os.SEEK_SET)
            vm._original_stdin_fd = os.dup(0)
            os.dup2(fd, 0)
            vm._direct_mode_message_path = path
        except Exception:
            os.close(fd)
            os.unlink(path)
            raise
        os.close(fd)

    direct_loader._inject_message_to_fd0 = _inject_message_to_fd0_windows

    # genlayer-test 0.29.2 does not model Event emissions in Direct Mode.
    # Accept those no-op requests while leaving all other WASI behavior intact.
    from gltest.direct import wasi_mock

    _handle_gl_call = wasi_mock._handle_gl_call

    def _handle_gl_call_with_events(vm, request):
        if isinstance(request, dict) and "EmitEvent" in request:
            return {"ok": None}
        return _handle_gl_call(vm, request)

    wasi_mock._handle_gl_call = _handle_gl_call_with_events
    _vm_cleanup = VMContext._cleanup_after_deactivate

    def _cleanup_vm_message_file(self):
        _vm_cleanup(self)
        path = getattr(self, "_direct_mode_message_path", None)
        if path:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
            self._direct_mode_message_path = None

    VMContext._cleanup_after_deactivate = _cleanup_vm_message_file


@pytest.fixture(autouse=True)
def _reset_contract_registry():
    yield
    try:
        import genlayer.gl.genvm_contracts as contracts
    except ImportError:
        return
    contracts.__known_contract__ = None



