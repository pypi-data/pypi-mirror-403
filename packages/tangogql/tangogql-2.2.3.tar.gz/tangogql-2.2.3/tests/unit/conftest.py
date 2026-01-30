import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from tangogql.subscription.listener import DeviceTracker

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def get_device_proxy():
    async def mock_get_device_proxy(devname):
        proxy = AsyncMock()
        proxy.devname = devname
        proxy.subscribe_event = AsyncMock(return_value=MagicMock())
        return proxy

    return mock_get_device_proxy


@pytest.fixture
def mock_device_tracker(get_device_proxy):
    queue = asyncio.Queue()
    tracker = DeviceTracker("test/device", queue, get_device_proxy=get_device_proxy)
    tracker.proxy = AsyncMock()
    return tracker, queue
