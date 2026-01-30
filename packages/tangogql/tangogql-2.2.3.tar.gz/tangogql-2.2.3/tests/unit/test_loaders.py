"""
Unit tests for dataloaders.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
import tango

from tangogql import loaders
from tangogql.utils import DbDeviceInfo


class FakeDatabase:
    "Tango Database client spec"

    async def command_inout(self, cmd, args):
        pass


@pytest.mark.asyncio
async def test__get_server_instances(monkeypatch):
    mockdb = AsyncMock(FakeDatabase)
    mockdb.command_inout.return_value = (
        [],
        ["Bananas/a", "TestServer/1", "TestServer/2"],
    )
    monkeypatch.setattr(loaders, "get_db", lambda: mockdb)

    results = await loaders.get_server_instances(["TestServer", "Bananas"])

    assert len(results) == 2
    # Order must correspond to arguments
    assert results[0] == ["1", "2"]
    assert results[1] == ["a"]


@pytest.mark.asyncio
async def test__get_device_infos_from_db(monkeypatch):
    mockdb = AsyncMock(FakeDatabase)
    mockdb.command_inout.return_value = (
        [],
        [
            "test/dummy/1",
            "",
            "1",
            "123321232",
            "test.host",
            "Dummy/1",
            "123",
            "Dummy",
            "5",
            "2024-09-06T12:01:15",
            "2024-09-06T10:21:35",
            "test/dummy/2",
            "alias2",
            "1",
            "399128319",
            "test.host",
            "Dummy/1",
            "123",
            "Dummy",
            "5",
            "2024-09-03T11:23:15",
            "2024-08-08T02:24:00",
        ],
    )
    monkeypatch.setattr(loaders, "get_db", lambda: mockdb)

    results = await loaders.get_device_infos_from_db(["test/dummy/1", "test/dummy/2"])
    assert len(results) == 2
    # Order must correspond to arguments
    info1 = results[0]
    assert isinstance(info1, DbDeviceInfo)
    assert info1.name == "test/dummy/1"
    info2 = results[1]
    assert isinstance(info2, DbDeviceInfo)
    assert info2.name == "test/dummy/2"


@pytest.mark.asyncio
async def test__get_device_properties_from_db(monkeypatch):
    mockdb = AsyncMock(FakeDatabase)
    mockdb.command_inout.return_value = (
        [],
        [
            "test/dummy/1",
            "prop1",
            "dev1prop1row1",
            "test/dummy/1",
            "prop1",
            "dev1prop1row2",
            "TEST/DUMMY/1",
            "prop2",
            "dev1prop2row1",
            "test/dummy/2",
            "prop1",
            "dev2prop1row1",
            "test/dummy/2",
            "prop2",
            "dev2prop2row1",
        ],
    )
    monkeypatch.setattr(loaders, "get_db", lambda: mockdb)

    result = await loaders.get_device_properties_from_db(
        ["test/dummy/1", "test/dummy/2"]
    )

    assert len(result) == 2
    # Order must correspond to arguments
    dev1 = result[0]
    assert len(dev1) == 2
    assert dev1[0] == ("test/dummy/1", "prop1", ["dev1prop1row1", "dev1prop1row2"])
    assert dev1[1] == ("TEST/DUMMY/1", "prop2", ["dev1prop2row1"])
    dev2 = result[1]
    assert dev2[0] == ("test/dummy/2", "prop1", ["dev2prop1row1"])
    assert dev2[1] == ("test/dummy/2", "prop2", ["dev2prop2row1"])


class FakeDeviceProxy:
    async def get_attribute_config_ex(self, attr):
        pass

    def attribute_list_query_ex(self, attr):
        pass

    async def read_attributes(self, attrs):
        pass


@pytest.mark.asyncio
async def test__get_device_attribute_infos__one(monkeypatch):
    mockproxy = AsyncMock(FakeDeviceProxy)
    attr_info = MagicMock(tango.AttributeInfoEx)
    attr_info.name = "test_attr"
    mockproxy.get_attribute_config_ex.return_value = [attr_info]

    async def get_mock_proxy(_):
        return mockproxy

    monkeypatch.setattr(loaders, "get_device_proxy", get_mock_proxy)

    results = await loaders.get_device_attribute_infos(["test/dummy/1/test_attr"])
    assert len(results) == 1
    assert results[0].name == "test_attr"


@pytest.mark.asyncio
async def test__get_device_attribute_infos__several(monkeypatch):
    mockproxy = AsyncMock(FakeDeviceProxy)
    attr_info1 = MagicMock(tango.AttributeInfoEx)
    attr_info1.name = "test_attr1"
    attr_info2 = MagicMock(tango.AttributeInfoEx)
    attr_info2.name = "test_attr2"
    mockproxy.attribute_list_query_ex.return_value = [attr_info1, attr_info2]

    async def get_mock_proxy(_):
        return mockproxy

    monkeypatch.setattr(loaders, "get_device_proxy", get_mock_proxy)

    results = await loaders.get_device_attribute_infos(
        ["test/dummy/1/test_attr1", "test/dummy/1/test_attr2"]
    )
    assert len(results) == 2
    # Order must correspond to arguments
    assert results[0].name == "test_attr1"
    assert results[1].name == "test_attr2"


@pytest.mark.asyncio
async def test__read_device_attribute_values(monkeypatch):
    mockproxy1 = AsyncMock(FakeDeviceProxy)
    dev1_value1 = MagicMock(tango.DeviceAttribute)
    dev1_value2 = MagicMock(tango.DeviceAttribute)
    mockproxy1.read_attributes.return_value = [dev1_value1, dev1_value2]

    mockproxy2 = AsyncMock(FakeDeviceProxy)
    dev2_value1 = MagicMock(tango.DeviceAttribute)
    mockproxy2.read_attributes.return_value = [dev2_value1]

    async def get_mock_proxy(name):
        return {
            "test/dummy/1": mockproxy1,
            "test/dummy/2": mockproxy2,
        }[name]

    monkeypatch.setattr(loaders, "get_device_proxy", get_mock_proxy)

    results = await loaders.read_device_attributes(
        ["test/dummy/1/attr1", "test/dummy/1/attr2", "test/dummy/2/attr1"]
    )

    assert len(results) == 3
    # Order must correspond to arguments
    assert results[0] == dev1_value1
    assert results[1] == dev1_value2
    assert results[2] == dev2_value1
