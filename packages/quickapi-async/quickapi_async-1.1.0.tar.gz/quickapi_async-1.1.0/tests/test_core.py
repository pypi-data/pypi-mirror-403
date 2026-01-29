from quickapi_async import QuickAPIAsync
import pytest

USE_IGNORE_SSL = False  # ⚠️ True is only for dev/testing with self-signed certificates

@pytest.mark.asyncio
async def test_get():
    res = await QuickAPIAsync() \
        .get("https://jsonplaceholder.typicode.com/posts/1") \
        .json(ignore_ssl=USE_IGNORE_SSL)

    assert res.status == 200
    assert "userId" in res.data