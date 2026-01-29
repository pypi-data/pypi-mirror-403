import pytest

from ppio_sandbox.core import AsyncSandbox


@pytest.mark.skip_debug()
@pytest.mark.asyncio
async def test_reset_instances(template):
    sbx = await AsyncSandbox.create(template, timeout=300)
    try:
        await sbx.reset(resume=True, timeout=150)
        assert await sbx.is_running() is True
    finally:
        await sbx.kill()


@pytest.mark.skip_debug()
@pytest.mark.asyncio
async def test_reset_static_returns_instances(template):
    sbx = await AsyncSandbox.create(template, timeout=300)
    try:
        await AsyncSandbox.reset(sbx.sandbox_id, resume=True, timeout=150)
        assert await sbx.is_running() is True
    finally:
        await sbx.kill()


