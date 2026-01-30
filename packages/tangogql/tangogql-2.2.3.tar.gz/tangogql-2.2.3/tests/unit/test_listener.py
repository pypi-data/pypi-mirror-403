import asyncio
from random import random
from time import time
from unittest.mock import AsyncMock, MagicMock

import pytest
import tango
from tango import DevFailed

from tangogql.subscription.listener import DeviceTracker, Listener


class MockDeviceProxy:
    def __init__(self, devicename, allow_subscription=False):
        self.name = devicename
        self.allow_subscription = allow_subscription

    async def read_attributes(self, attributes, extract_as=None):
        results = []
        for attribute in attributes:
            da = tango.DeviceAttribute()
            da.name = attribute
            da.value = random()
            da.timestamp = tango.TimeVal(time())
            da.quality = tango.AttrQuality.ATTR_VALID
            da.has_failed = False
            results.append(da)
        return results

    async def subscribe_event(self, attribute, event_type, callback, extract_as=None):
        if self.allow_subscription:
            pass  # TODO
        else:
            raise tango.DevFailed(tango.DevError())


class MockDatabase:
    def get_db_host(self):
        return "my.tango.host"

    def get_db_port(self):
        return 10000


# Updated async get_device_proxy functions
async def get_device_proxy_no_subs(devname):
    return MockDeviceProxy(devname)


@pytest.mark.asyncio
async def test_attribute_tracker_polled_immediate_read():
    queue = asyncio.Queue()

    async def get_device_proxy(devname):
        return MockDeviceProxy(devname)

    tracker = DeviceTracker(
        "tango://my.tango.host:10000/my/test/device",
        queue,
        poll_period=0.1,
        get_device_proxy=get_device_proxy,
    )
    await tracker.start()
    await tracker.add_attributes(["attr_a"])

    full_name, dev_attr = await queue.get()
    assert full_name == "tango://my.tango.host:10000/my/test/device/attr_a"

    # No more data
    assert queue.empty()

    await tracker.stop()


@pytest.mark.asyncio
async def test_listener_basic():
    async def get_device_proxy(devname):
        return MockDeviceProxy(devname)

    listener = Listener(
        get_db=lambda: MockDatabase(), get_device_proxy=get_device_proxy
    )

    devname = "my/test/device"
    attrnames = ["attr_a", "attr_b", "attrc"]
    attributes = [f"{devname}/{attr}" for attr in attrnames]

    listener.start()
    events = []
    async for attr, _ in listener.listen(attributes):
        # We should get one event per attribute, initially
        events.append(attr)
        if len(events) == 3:
            break
    assert len(set(events)) == 3


@pytest.mark.asyncio
async def test_listener_multiple_devices():
    async def get_device_proxy(devname):
        return MockDeviceProxy(devname)

    listener = Listener(
        get_db=lambda: MockDatabase(), get_device_proxy=get_device_proxy
    )

    dev1 = "my/test/device1"
    dev2 = "my/test/device2"
    attrnames1 = ["attr_a", "attr_b"]
    attrnames2 = ["attr_x", "attr_y"]
    attributes = [f"{dev1}/{attr}" for attr in attrnames1] + [
        f"{dev2}/{attr}" for attr in attrnames2
    ]

    listener.start()
    events = []
    async for attr, _ in listener.listen(attributes):
        events.append(attr)
        if len(events) == 4:
            break

    assert len(set(events)) == 4
    assert any(f"{dev1}/attr_a" in ev for ev in events)
    assert any(f"{dev2}/attr_x" in ev for ev in events)


@pytest.mark.asyncio
async def test_listener_throttle_mechanism():
    async def get_device_proxy(devname):
        return MockDeviceProxy(devname)

    listener = Listener(
        get_db=lambda: MockDatabase(), get_device_proxy=get_device_proxy
    )

    devname = "my/test/device"
    attrnames = ["attr_a", "attr_b"]
    attributes = [f"{devname}/{attr}" for attr in attrnames]

    listener.start()
    queue = asyncio.Queue()
    await listener.add_listeners(attributes, queue)

    events = []
    async for attr, _ in listener.listen(attributes, throttle=True):
        events.append(attr)
        if len(events) == 2:
            break

    assert len(events) == 2


@pytest.mark.asyncio
async def test_attribute_with_none_value():
    class NoneValueMockDeviceProxy(MockDeviceProxy):
        async def read_attributes(self, attributes, extract_as=None):
            results = []
            for attribute in attributes:
                da = tango.DeviceAttribute()
                da.name = attribute
                da.value = None  # Simulate None value
                da.timestamp = tango.TimeVal(time())
                da.quality = tango.AttrQuality.ATTR_VALID
                da.has_failed = False
                results.append(da)
            return results

    async def get_device_proxy(devname):
        return NoneValueMockDeviceProxy(devname)

    queue = asyncio.Queue()
    tracker = DeviceTracker(
        "tango://my.tango.host:10000/my/test/device",
        queue,
        poll_period=0.1,
        get_device_proxy=get_device_proxy,
    )

    await tracker.start()
    await tracker.add_attributes(["attr_a"])

    full_name, dev_attr = await queue.get()
    assert dev_attr.value is None

    await tracker.stop()


@pytest.mark.asyncio
async def test_device_tracker_multiple_attributes():
    queue = asyncio.Queue()

    async def get_device_proxy(devname):
        return MockDeviceProxy(devname)

    tracker = DeviceTracker(
        "tango://my.tango.host:10000/my/test/device",
        queue,
        poll_period=0.1,
        get_device_proxy=get_device_proxy,
    )
    await tracker.start()
    await tracker.add_attributes(["attr_a", "attr_b", "attr_c"])

    results = []
    for _ in range(3):
        full_name, dev_attr = await queue.get()
        results.append(full_name)

    assert len(set(results)) == 3
    await tracker.stop()


@pytest.mark.asyncio
async def test_device_tracker_initialization():
    queue = asyncio.Queue()
    tracker = DeviceTracker(devicename="test/device", queue=queue)

    assert tracker.devicename == "test/device"
    assert tracker.queue == queue
    assert tracker.empty


@pytest.mark.asyncio
async def test_add_and_remove_attribute(mock_device_tracker):
    tracker, queue = mock_device_tracker
    await tracker.add_attributes(["attr1"])
    await tracker.remove_attribute("attr1")
    assert "attr1" not in tracker.attributes


@pytest.mark.asyncio
async def test_add_attributes_success(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    await tracker.add_attributes(["attr1", "attr2"])

    assert "attr1" in tracker.attributes
    assert "attr2" in tracker.attributes
    assert tracker.subs["attr1"] is not None
    assert tracker.subs["attr2"] is not None


@pytest.mark.asyncio
async def test_remove_attribute_success(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)
    await tracker.add_attributes(["attr1"])

    await tracker.remove_attribute("attr1")

    assert "attr1" not in tracker.attributes
    assert tracker.subs.get("attr1") is None


@pytest.mark.asyncio
async def test_remove_attribute_not_found(mock_device_tracker):
    tracker, queue = mock_device_tracker
    await tracker.remove_attribute("attr1")  # Should not raise

    assert "attr1" not in tracker.attributes


@pytest.mark.asyncio
async def test_subscribe_event_success(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    await tracker._subscribe("attr1")

    assert "attr1" in tracker.subs
    assert tracker.subs["attr1"] is not None


@pytest.mark.asyncio
async def test_add_attributes_no_event_success(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    # Mocking the proxy and the subscribe_event method
    tracker.proxy = AsyncMock()
    tracker.proxy.subscribe_event = AsyncMock(return_value=MagicMock())

    # Test adding attributes
    await tracker.add_attributes(["attr1", "attr2"])

    assert "attr1" in tracker.attributes
    assert "attr2" in tracker.attributes
    assert queue.qsize() == 0  # No events should be published yet


@pytest.mark.asyncio
async def test_add_attributes_failure(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    # Mocking the proxy and simulating a subscription failure
    tracker.proxy = AsyncMock()
    tracker.proxy.subscribe_event.side_effect = DevFailed("Subscription failed")

    # Test adding attributes with failure
    await tracker.add_attributes(["attr1"])

    assert "attr1" in tracker.attributes
    # Since the subscription failed, it should have polled the attribute
    tracker.proxy.read_attributes.assert_called_once_with(
        ["attr1"], extract_as=tango.ExtractAs.List
    )


@pytest.mark.asyncio
async def test_remove_attribute(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    # Mocking the proxy and adding an attribute
    tracker.proxy = AsyncMock()
    await tracker.add_attributes(["attr1"])

    # Test removing the attribute
    await tracker.remove_attribute("attr1")

    assert "attr1" not in tracker.attributes
    tracker.proxy.unsubscribe_event.assert_called_once()  # Ensure unsubscribe was called


@pytest.mark.asyncio
async def test_subscribe_event_failure(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    # Mocking the proxy and simulating a subscription failure
    tracker.proxy = AsyncMock()
    tracker.proxy.subscribe_event.side_effect = DevFailed(tango.DevError())

    # Attempt to subscribe an attribute and ensure it raises an exception
    with pytest.raises(DevFailed):
        await tracker._subscribe("attr1")


@pytest.mark.asyncio
async def test_add_attribute_duplicate(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    tracker.proxy = AsyncMock()
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    await tracker.add_attributes(["attr1"])

    # Attempt to add the same attribute again
    await tracker.add_attributes(["attr1"])

    assert len(tracker.attributes) == 1


@pytest.mark.asyncio
async def test_device_tracker_stop_without_start(mock_device_tracker):
    tracker, queue = mock_device_tracker
    tracker.proxy.subscribe_event = AsyncMock(return_value=1)

    # Ensure stopping doesn't raise an error if start wasn't called
    await tracker.stop()
    assert tracker.empty is True


@pytest.mark.asyncio
async def test_attribute_removal_when_not_subscribed(mock_device_tracker):
    queue = asyncio.Queue()
    tracker = DeviceTracker("test/device", queue)

    await tracker.add_attributes(["attr1"])
    await tracker.remove_attribute("attr2")

    assert "attr1" in tracker.attributes  # attr1 should still be there


@pytest.mark.asyncio
async def test_remove_non_existent_attribute(mock_device_tracker):
    queue = asyncio.Queue()
    tracker = DeviceTracker("test/device", queue)

    tracker.proxy = AsyncMock()
    await tracker.add_attributes(["attr1"])

    # Try to remove a non-existent attribute and ensure it does not raise an error
    await tracker.remove_attribute("attr_non_existent")

    assert "attr1" in tracker.attributes  # attr1 should still be there
