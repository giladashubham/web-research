from __future__ import annotations

from webresearch.tui.widgets.confirm_cancel import ConfirmCancelDialog


def test_confirm_cancel_dialog_constructs() -> None:
    assert ConfirmCancelDialog() is not None
