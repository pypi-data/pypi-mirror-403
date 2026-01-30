import pytest

from tangogql.dev import app

from . import Any
from .testclient import AsyncioTestClient


@pytest.mark.asyncio
async def test_subscribe_attribute(pytango_databaseds):
    # This test requires running the app in an async context which the
    # normal TestClient somehow doesn't.
    async with AsyncioTestClient(app=app) as client:
        async with client.websocket_connect("/") as websocket:
            # Initialize the connection
            await websocket.send_json({"type": "connection_init"})
            await websocket.receive_json()

            # Set up a subscription
            query = {
                "id": "42",
                "type": "subscribe",
                "payload": {
                    "query": """
                    subscription Attributes($fullNames: [String]!) {
                        attributes(fullNames: $fullNames) {
                            device, attribute, value, writeValue, quality, timestamp
                        }
                    }
                    """,
                    "variables": {"fullNames": ["test/dummy/1/attr_float"]},
                },
            }
            await websocket.send_json(query)

            # Wait for the first event
            data = await websocket.receive_json()
            assert data == {
                "type": "next",
                "id": "42",
                "payload": {
                    "data": {
                        "attributes": {
                            "device": "test/dummy/1",
                            "attribute": "attr_float",
                            "value": Any(float),
                            "writeValue": None,
                            "quality": Any(str),
                            "timestamp": Any(float),
                        }
                    }
                },
            }


@pytest.mark.asyncio
async def test_subscribe_attribute_casing(pytango_databaseds):
    async with AsyncioTestClient(app=app) as client:
        async with client.websocket_connect("/") as websocket:
            # Initialize the connection
            await websocket.send_json({"type": "connection_init"})
            await websocket.receive_json()

            # Set up a subscription
            query = {
                "id": "42",
                "type": "subscribe",
                "payload": {
                    "query": """
                    subscription Attributes($fullNames: [String]!) {
                        attributes(fullNames: $fullNames) {
                            fullName, device, attribute, value, writeValue, quality, timestamp
                        }
                    }
                    """,
                    # Here, attribute name case is different from original
                    # Casing should not matter, since Tango is not case sensitive.
                    "variables": {"fullNames": ["test/dummy/1/attr_DIFFERENTcase"]},
                },
            }
            await websocket.send_json(query)

            # Wait for the first event
            data = await websocket.receive_json()
            assert data == {
                "type": "next",
                "id": "42",
                "payload": {
                    "data": {
                        "attributes": {
                            "fullName": "tango://127.0.0.1:11000/test/dummy/1/attr_differentcase",
                            "device": "test/dummy/1",
                            "attribute": "attr_differentcase",  # always lowercase
                            "value": Any(float),
                            "writeValue": None,
                            "quality": Any(str),
                            "timestamp": Any(float),
                        }
                    }
                },
            }


@pytest.mark.asyncio
async def test_subscribe_attribute_invalid_name(pytango_databaseds):
    async with AsyncioTestClient(app=app) as client:
        async with client.websocket_connect("/") as websocket:
            # Initialize the connection
            await websocket.send_json({"type": "connection_init"})
            await websocket.receive_json()

            # Set up a subscription
            query = {
                "id": "42",
                "type": "subscribe",
                "payload": {
                    "query": """
                    subscription Attributes($fullNames: [String]!) {
                        attributes(fullNames: $fullNames) {
                            fullName, error {desc}
                        }
                    }
                    """,
                    # This is an obviously invalid attribute name,
                    # the backend should not even try to subscribe
                    "variables": {"fullNames": ["test/dummy/1/some/thing/wrong"]},
                },
            }
            await websocket.send_json(query)

            data = await websocket.receive_json()
            assert data == {
                "type": "next",
                "id": "42",
                "payload": {
                    "data": {
                        "attributes": {
                            "fullName": "tango://127.0.0.1:11000/test/dummy/1/some/thing/wrong",
                            "error": {
                                "desc": Any(str),
                            },
                        }
                    }
                },
            }
            error_desc = data["payload"]["data"]["attributes"]["error"]["desc"]
            assert error_desc.startswith("Subscription failed")
            assert "test/dummy/1/some/thing/wrong" in error_desc


@pytest.mark.asyncio
async def test_subscribe_broken_attribute(pytango_databaseds):
    async with AsyncioTestClient(app=app) as client:
        async with client.websocket_connect("/") as websocket:
            # Initialize the connection
            await websocket.send_json({"type": "connection_init"})
            await websocket.receive_json()

            # Set up a subscription
            query = {
                "id": "42",
                "type": "subscribe",
                "payload": {
                    "query": """
                    subscription Attributes($fullNames: [String]!) {
                        attributes(fullNames: $fullNames) {
                            device, attribute, quality, timestamp, error {desc}
                        }
                    }
                    """,
                    "variables": {"fullNames": ["test/dummy/1/attr_broken"]},
                },
            }
            await websocket.send_json(query)

            # Wait for the first event
            data = await websocket.receive_json()
            print("data", data)
            assert data == {
                "type": "next",
                "id": "42",
                "payload": {
                    "data": {
                        "attributes": {
                            "device": "test/dummy/1",
                            "attribute": "attr_broken",
                            "quality": "ATTR_INVALID",
                            "timestamp": Any(float),
                            "error": {
                                "desc": "RuntimeError: Oops\n",
                            },
                        }
                    }
                },
            }


@pytest.mark.asyncio
async def test_subscribe_multiple_attributes(pytango_databaseds):
    async with AsyncioTestClient(app=app) as client:
        async with client.websocket_connect("/") as websocket:
            await websocket.send_json({"type": "connection_init"})
            await websocket.receive_json()

            # Set up a subscription
            attributes = [
                "test/dummy/1/attr_float",
                "test/dummy/1/attr_int",
            ]
            query = {
                "id": "37",
                "type": "subscribe",
                "payload": {
                    "query": """
                    subscription Attributes($fullNames: [String]!) {
                        attributes(fullNames: $fullNames) {
                            device, attribute, value, writeValue, quality, timestamp
                        }
                    }
                    """,
                    "variables": {"fullNames": attributes},
                },
            }
            await websocket.send_json(query)

            # Wait for events on each attribute
            received = set()
            while True:
                data = await websocket.receive_json()
                assert data == {
                    "type": "next",
                    "id": "37",
                    "payload": {
                        "data": {
                            "attributes": {
                                "device": "test/dummy/1",
                                "attribute": Any(str),
                                "value": Any(float),
                                "writeValue": None,
                                "quality": Any(str),
                                "timestamp": Any(float),
                            }
                        }
                    },
                }
                attr = data["payload"]["data"]["attributes"]
                received.add(f"{attr['device']}/{attr['attribute']}")
                if received == set(attributes):
                    break
                # TODO limit how long we wait for this to succeed?


@pytest.mark.asyncio
async def test_subscribe_multiple_attributes_some_raising_exception(pytango_databaseds):
    async with AsyncioTestClient(app=app) as client:
        async with client.websocket_connect("/") as websocket:
            await websocket.send_json({"type": "connection_init"})
            await websocket.receive_json()

            # Set up a subscription
            attributes = [
                "test/dummy/1/attr_float",
                "test/dummy/1/attr_raising",
            ]
            query = {
                "id": "37",
                "type": "subscribe",
                "payload": {
                    "query": """
                    subscription Attributes($fullNames: [String]!) {
                        attributes(fullNames: $fullNames) {
                            device, attribute, value, quality, error {desc}
                        }
                    }
                    """,
                    "variables": {"fullNames": attributes},
                },
            }
            await websocket.send_json(query)

            # Wait for events on each attribute, making sure that
            # we receive events for all of them
            received = set()
            while True:
                data = await websocket.receive_json()
                attr = data["payload"]["data"]["attributes"]
                match attr["attribute"]:
                    case "attr_raising":
                        assert attr["value"] is None
                        assert attr["quality"] == "ATTR_INVALID"
                        assert "oops" in attr["error"]["desc"]
                    case "attr_float":
                        assert attr["value"] == Any(float)
                        assert attr["quality"] == "ATTR_VALID"
                        assert not attr["error"]
                received.add("{device}/{attribute}".format(**attr))
                if received == set(attributes):
                    break
                # TODO limit how long we wait for this to succeed?


@pytest.mark.asyncio(scope="function")
async def test_subscribe_multiple_attributes_some_timing_out(pytango_databaseds):
    async with AsyncioTestClient(app=app) as client:
        async with client.websocket_connect("/") as websocket:
            await websocket.send_json({"type": "connection_init"})
            await websocket.receive_json()

            # Set up a subscription
            attributes = [
                "test/dummy/1/attr_int",
                "test/dummy/1/attr_slow",
            ]
            query = {
                "id": "37",
                "type": "subscribe",
                "payload": {
                    "query": """
                    subscription Attributes($fullNames: [String]!) {
                        attributes(fullNames: $fullNames) {
                            device, attribute, value, quality, error {desc}
                        }
                    }
                    """,
                    "variables": {"fullNames": attributes},
                },
            }
            await websocket.send_json(query)

            # Wait for events on each attribute, making sure that
            # we receive events for all of them
            received = set()
            while True:
                data = await websocket.receive_json()
                attr = data["payload"]["data"]["attributes"]
                match attr["attribute"]:
                    case "attr_slow":
                        assert attr["value"] is None
                        assert "TRANSIENT_CallTimedout" in attr["error"]["desc"]
                    case "attr_int":
                        # Note: this is a shortcoming of the listener implementation.
                        # See comment on the listener.DeviceTracker class.
                        assert attr["value"] is None
                        assert "TRANSIENT_CallTimedout" in attr["error"]["desc"]
                received.add("{device}/{attribute}".format(**attr))
                if received == set(attributes):
                    break
                # TODO limit how long we wait for this to succeed?
