"""
Test mutations
"""

import pytest
from ariadne import graphql
from pytest import param

import tangogql
from tangogql import settings
from tangogql.common import get_context_value
from tangogql.schema import schema

from . import Any

# Test parameters
QUERY_PARAMS = [
    param(
        # GraphQL query
        """
        mutation {
            putDeviceProperty(device: "test/dummy/1", name: "sommar", value: "solig") {
                ok
                message
            }
        }
        """,
        # Expected result
        {
            "putDeviceProperty": {
                "ok": True,
                "message": None,
            }
        },
        # Test identifier
        id="PUT_DEVICE_PROPERTY",
    ),
    param(
        """
        mutation {
            deleteDeviceProperty(device: "test/dummy/1", name: "sommar") {
                ok
                message
            }
        }
        """,
        {
            "deleteDeviceProperty": {
                "ok": True,
                "message": None,
            }
        },
        id="DELETE_DEVICE_PROPERTY",
    ),
    param(
        """
        mutation {
            executeCommand(device: "test/dummy/1", command: "CommandInt", argin: 1) {
                ok
                message
                output
            }
        }
        """,
        {
            "executeCommand": {
                "ok": True,
                "message": None,
                "output": True,
            }
        },
        id="EXECUTE_DEVICE_COMMAND",
    ),
    param(
        """
        mutation{
            executeCommand(device : "test/dummy/1", command: "CommandInt", argin: "sdfsdf") {
                ok
                message
                output
            }
        }
        """,
        {
            "executeCommand": {
                "ok": False,
                "message": Any(list),
                "output": None,
            }
        },
        id="EXECUTE_DEVICE_COMMAND_WRONG_INPUT_TYPE",
    ),
    param(
        """
        mutation {
            executeCommand(device: "test/dummy/1", command:, "dfg", argin: 1) {
                ok
                message
                output
            }
        }
        """,
        {
            "executeCommand": {
                "ok": False,
                "message": Any(list),
                "output": None,
            }
        },
        id="EXECUTE_DEVICE_COMMAND_NONEXISTING",
    ),
    param(
        """
        mutation {
            setAttributeValue(device: "test/dummy/1", name: "attr_int_writable", value: 17) {
                ok,
                message,
            }
        }
        """,
        {
            "setAttributeValue": {
                "ok": True,
                "message": None,
            }
        },
        id="SET_ATTRIBUTE_VALUE",
    ),
    param(
        """
        mutation {
            setAttributeValue(device: "test/dummy/1", name: "attr_int_writable", value: "dsf") {
                ok,
                message,
            }
        }
        """,
        {
            "setAttributeValue": {
                "ok": False,
                "message": Any(list),
            }
        },
        id="SET_ATTRIBUTE_VALUE_WRONG_TYPE",
    ),
    param(
        """
        mutation {
            setAttributeValue(device: "test/dummy/1", name: "i_dont_exist", value: 1) {
                ok,
                message,
            }
        }
        """,
        {
            "setAttributeValue": {
                "ok": False,
                "message": Any(list),
            }
        },
        id="SET_ATTRIBUTE_VALUE_NONEXISTING_ATTR",
    ),
    param(
        """
        mutation {
            setAttributeValue(device: "sys/notexists/1", name: "ampli", value: 1) {
                ok,
                message,
            }
        }
        """,
        {
            "setAttributeValue": {
                "ok": False,
                "message": Any(list),
            }
        },
        id="SET_ATTRIBUTE_VALUE_NOEXISTING_DEVICE",
    ),
    param(
        """
    mutation {
        setAttributeValue(device: "test/dummy/1", 
        name: "attr_int_writable", 
        value: 9223372036854775808) {
            ok,
            message,
        }
    }
    """,
        {
            "setAttributeValue": {
                "ok": False,
                "message": Any(list),
            }
        },
        id="SET_ATTRIBUTE_VALUE_OUT_OF_RANGE",
    ),
    param(
        """
    mutation {
        executeCommand(device: "test/dummy/1", command: "CommandInt", argin: [1, 2, 3]) {
            ok
            message
            output
        }
    }
    """,
        {
            "executeCommand": {
                "ok": False,
                "message": Any(list),
                "output": None,
            }
        },
        id="EXECUTE_COMMAND_WRONG_ARGIN_TYPE",
    ),
    param(
        """
    mutation {
        setAttributeValue(device: "test/dummy/1", name: "attr_int_writable", value: "") {
            ok,
            message,
        }
    }
    """,
        {
            "setAttributeValue": {
                "ok": False,
                "message": Any(list),
            }
        },
        id="SET_ATTRIBUTE_VALUE_EMPTY_STRING",
    ),
    param(
        """
    mutation {
        executeCommand(device: "test/dummy/1", command: "CommandInt", argin: "true") {
            ok
            message
            output
        }
    }
    """,
        {
            "executeCommand": {
                "ok": False,
                "message": Any(list),
                "output": None,
            }
        },
        id="EXECUTE_COMMAND_BOOLEAN_STRING_TO_INT",
    ),
    param(
        """
    mutation {
        executeCommand(device: "test/dummy/1", command: "CommandInt", argin: 3.14159) {
            ok
            message
            output
        }
    }
    """,
        {
            "executeCommand": {
                "ok": False,
                "message": Any(list),
                "output": None,
            }
        },
        id="EXECUTE_COMMAND_FLOAT_TO_INT",
    ),
    param(
        """
    mutation {
        executeCommand(device: "test/dummy/1",
                       command: "DevVarLongStringArray") {
            ok
            output
        }
    }
    """,
        {
            "executeCommand": {
                "ok": True,
                "output": [[1, 2, 3], ["a", "b", "c"]],
            }
        },
        id="EXECUTE_COMMAND_DEVVARLONGSTRINGARRAY",
    ),
    param(
        """
    mutation {
        setAttributeValue(device: "test/dummy/1", 
        name: "attr_int_writable", 
        value: -9223372036854775809) {
            ok,
            message,
        }
    }
    """,
        {
            "setAttributeValue": {
                "ok": False,
                "message": Any(list),
            }
        },
        id="SET_ATTRIBUTE_VALUE_BELOW_MIN_INT64",
    ),
    param(
        """
    mutation {
        setAttributeValue(device: "test/dummy/1", name: "attr_int_writable", value: 42) {
            ok
            message
        }
    }
    """,
        {"setAttributeValue": {"ok": True, "message": None}},
        id="SET_ATTRIBUTE_VALUE_SIMPLE",
    ),
    param(
        """
    mutation {
        putDeviceProperty(device: "test/dummy/1", name: "test_prop", value: ["test"]) {
            ok
            message
        }
    }
    """,
        {
            "putDeviceProperty": {
                "ok": True,
                "message": None,
            }
        },
        id="PUT_DEVICE_PROPERTY_SINGLE_VALUE",
    ),
    param(
        """
    mutation {
        executeCommand(device: "test/dummy/1", command: "State", argin: "") {
            ok
            message
            output
        }
    }
    """,
        {
            "executeCommand": {
                "ok": False,
                "message": Any(list),
                "output": None,
            }
        },
        id="EXECUTE_COMMAND_INVALID_ARGIN_TYPE",
    ),
    param(
        """
    mutation {
        setAttributeValue(device: "test/dummy/1", 
        name: "long_scalar_w", 
        value: 9223372036854775808) {
            ok
            message
        }
    }
    """,
        {"setAttributeValue": {"ok": False, "message": Any(list)}},
        id="SET_ATTRIBUTE_VALUE_OVERFLOW",
    ),
    param(
        """
        mutation {
            setAttributeValue(device: "test/dummy/1", name: "attr_int_writable", value: 123) {
                ok
                message
                valueBefore
                attribute {
                    device
                    label
                    name
                    value
                    writevalue
                    timestamp
                    quality
                }
            }
        }
        """,
        {
            "setAttributeValue": {
                "ok": True,
                "message": None,
                "valueBefore": 0,
                "attribute": {
                    "device": "test/dummy/1",
                    "label": "Hello!",
                    "name": "attr_int_writable",
                    "value": 123,
                    "writevalue": 123,
                    "timestamp": Any(float),
                    "quality": "ATTR_VALID",
                },
            }
        },
        id="SET_ATTRIBUTE_READ_BACK",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected", QUERY_PARAMS)
async def test_mutation(pytango_databaseds, query, expected, monkeypatch):
    # TODO not very pretty way to disable auth
    NO_AUTH_SETTINGS = settings.Settings()
    NO_AUTH_SETTINGS.no_auth = True
    monkeypatch.setattr(tangogql.auth, "settings", NO_AUTH_SETTINGS)
    ok, result = await graphql(
        schema=schema, data={"query": query}, context_value=get_context_value(None)
    )
    assert ok
    assert "errors" not in result
    assert result["data"] == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected", QUERY_PARAMS)
async def test_mutation_without_auth_fails(
    pytango_databaseds, query, expected, monkeypatch
):
    NO_AUTH_SETTINGS = settings.Settings()
    NO_AUTH_SETTINGS.no_auth = False
    monkeypatch.setattr(tangogql.auth, "settings", NO_AUTH_SETTINGS)
    ok, result = await graphql(
        schema=schema, data={"query": query}, context_value=get_context_value(None)
    )
    assert "errors" in result
    assert result["errors"][0]["message"] == "User is not logged in"
