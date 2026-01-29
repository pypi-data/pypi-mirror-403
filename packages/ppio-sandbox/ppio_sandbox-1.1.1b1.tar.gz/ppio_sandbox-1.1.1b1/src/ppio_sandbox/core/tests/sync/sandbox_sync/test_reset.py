import pytest

from ppio_sandbox.core import Sandbox


@pytest.mark.skip_debug()
def test_reset_returns_instances(template):
    sbx = Sandbox.create(template, timeout=300)
    try:
        sbx.reset(resume=True, timeout=150)
        assert sbx.is_running() is True
    finally:
        sbx.kill()


@pytest.mark.skip_debug()
def test_reset_static_returns_instances(template):
    sbx = Sandbox.create(template, timeout=300)
    try:
        Sandbox.reset(sbx.sandbox_id, resume=True, timeout=150)
        assert sbx.is_running() is True
    finally:
        sbx.kill()


