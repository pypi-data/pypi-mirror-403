import asyncio
import logging

import pytest
from aiocache import caches

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="session")
def event_loop():
    "Need this or the loop gets closed after first test"
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def before_each_test():
    # Ensure that the cache is cleared of stuff from previous tests
    await caches.get("default").clear()
