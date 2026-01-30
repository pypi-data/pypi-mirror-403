"""
Test basic queries
"""

import pytest
from ariadne import graphql
from pytest import param

from tangogql.common import get_context_value
from tangogql.schema import schema

from . import Any

# Test parameters
QUERY_PARAMS = [
    param(
        # GraphQL query
        'query{device(name: "test/dummy/1"){name}}',
        # Expected result
        {"device": {"name": "test/dummy/1"}},
        # Test identifier
        id="DEVICE_NAME",
    ),
    param(
        'query{devices(pattern: "test/dummy/1"){name}}',
        {"devices": [{"name": "test/dummy/1"}]},
        id="DEVICES_NAME",
    ),
    param(
        'query{devices(pattern: "test/dummy/1"){state}}',
        {"devices": [{"state": "RUNNING"}]},
        id="DEVICE_STATE_QUERY",
    ),
    param(
        """
        query {
            classes(pattern: "DataBase") {
                name
                devices { name }
            }
        }
        """,
        {"classes": [{"name": "DataBase", "devices": [{"name": "sys/database/2"}]}]},
        id="CLASS_AND_DEVICE_QUERY",
    ),
    param(
        """
        query{
            devices(pattern: "test/dummy/1") {
                properties(pattern: "graphql_test") {
                    name, device, value
                }
             }
        }
        """,
        {
            "devices": [
                {
                    "properties": [
                        {
                            "name": "graphql_test",
                            "value": [
                                "abc",
                                "def",
                            ],
                            "device": "test/dummy/1",
                        }
                    ]
                }
            ]
        },
        id="DEVICE_PROPERTIES_QUERY",
    ),
    param(
        """
        query{
            devices(pattern: "test/dummy/1"){
                attributes(pattern:"attr_float") {
                    name,
                    device,
                    datatype,
                    format,
                    dataformat,
                    writable,
                    label,
                    unit,
                    description,
                    displevel,
                    value,
                    writevalue,
                    quality,
                    minvalue,
                    maxvalue,
                    minalarm,
                    maxalarm,
                    enumLabels,
                    timestamp
                }
            }
        }
        """,
        {
            "devices": [
                {
                    "attributes": [
                        {
                            "name": "attr_float",
                            "device": "test/dummy/1",
                            "datatype": "DevDouble",
                            "format": "%6.2f",
                            "dataformat": "SCALAR",
                            "writable": "READ",
                            "label": "attr_float",
                            "unit": "mm",
                            "description": None,
                            "displevel": "OPERATOR",
                            "quality": "ATTR_VALID",
                            "minvalue": None,
                            "maxvalue": None,
                            "minalarm": None,
                            "maxalarm": None,
                            "enumLabels": [],
                            "value": 17.3,
                            "writevalue": None,
                            "timestamp": Any(float),
                        }
                    ]
                }
            ]
        },
        id="DEVICE_ATTRIBUTES_QUERY",
    ),
    param(
        """
        query{
            attributes(fullNames:["test/dummy/1/attr_float_array"]) {
                    name,
                    device,
                    datatype,
                    format,
                    dataformat,
                    writable,
                    label,
                    unit,
                    description,
                    displevel,
                    value,
                    writevalue,
                    quality,
                    minvalue,
                    maxvalue,
                    minalarm,
                    maxalarm,
                    enumLabels,
                    timestamp
            }
        }
        """,
        {
            "attributes": [
                {
                    "name": "attr_float_array",
                    "device": "test/dummy/1",
                    "datatype": "DevDouble",
                    "format": "%6.2f",
                    "dataformat": "SPECTRUM",
                    "writable": "READ",
                    "label": "attr_float_array",
                    "unit": "cm",
                    "description": None,
                    "displevel": "OPERATOR",
                    "quality": "ATTR_VALID",
                    "minvalue": None,
                    "maxvalue": None,
                    "minalarm": None,
                    "maxalarm": None,
                    "enumLabels": [],
                    "value": [1.2, 3.4, 5.6],
                    "writevalue": [],
                    "timestamp": Any(float),
                }
            ]
        },
        id="ATTRIBUTES_QUERY",
    ),
    param(
        """
        query{
            devices(pattern: "test/dummy/1") {
                commands(pattern:"CommandInt") {
                    name,
                    tag
                    displevel,
                    intype,
                    intypedesc,
                    outtype,
                    outtypedesc
                }
            }
        }
        """,
        {
            "devices": [
                {
                    "commands": [
                        {
                            "name": "CommandInt",
                            "displevel": "OPERATOR",
                            "intype": "DevLong64",
                            "intypedesc": "in",
                            "outtype": "DevLong64",
                            "outtypedesc": "out",
                            "tag": None,
                        }
                    ]
                }
            ]
        },
        id="DEVICE_COMMANDS_QUERY",
    ),
    param(
        'query{devices(pattern: "test/dummy/1"){server{id,host},deviceClass}}',
        {
            "devices": [
                {"server": {"id": "Dummy/1", "host": Any(str)}, "deviceClass": "Dummy"}
            ]
        },
        id="DEVICE_SERVER_QUERY",
    ),
    param(
        """query{devices(pattern: "test/dummy/1"){deviceClass}}""",
        {"devices": [{"deviceClass": "Dummy"}]},
        id="DEVICE_CLASS_QUERY",
    ),
    param(
        """query{devices(pattern: "test/dummy/1"){pid}}""",
        {"devices": [{"pid": Any(int)}]},
        id="DEVICE_PID_QUERY",
    ),
    param(
        """ query{devices(pattern: "test/dummy/1"){startedDate}} """,
        {"devices": [{"startedDate": Any(str)}]},  # TODO check timestamp format?
        id="DEVICE_STARTED_DATE_QUERY",
    ),
    param(
        """ query{devices(pattern: "test/dummy/1"){stoppedDate}} """,
        {"devices": [{"stoppedDate": None}]},  # Device has never been stopped
        id="DEVICE_STOPPED_DATE_QUERY",
    ),
    # Domain/family/member not yet supported (and does not seem to be used by Taranta)
    param(
        """ query{domains(pattern: "sys*"){name}} """,
        {"domains": [{"name": "sys"}]},
        id="DOMAIN_NAME_QUERY",
        marks=[pytest.mark.skip],
    ),
    param(
        """
        query {
            domains(pattern: "sys") {
                families(pattern: "database*") {
                    name,
                    domain,
                    members(pattern:"*") {
                        name,
                        state,
                        pid,
                        startedDate,
                        stoppedDate,
                        exported,
                        domain,
                        family
                    }
                }
            }
        }
        """,
        {
            "domains": [
                {
                    "name": "sys",
                    "families": [
                        {
                            "name": "database",
                            "domain": "sys",
                            "members": [
                                {
                                    "name": "2",
                                    "state": Any(str),
                                    "pid": Any(int),
                                    "startedDate": Any(str),
                                    "stoppedDate": Any(str),
                                    "exported": True,
                                    "domain": "sys",
                                    "family": "database",
                                }
                            ],
                        }
                    ],
                }
            ]
        },
        id="DOMAIN_FAMILIES",
        marks=[pytest.mark.skip],
    ),
    param(
        'query{members(domain:"sys" family:"tg_test"){name}}',
        {},
        id="MEMBER_NAME",
        marks=[pytest.mark.skip],
    ),
    param(
        """
        query{
            servers(pattern: "Dummy"){
                name, instances {
                    name, classes {
                        name, devices {name}
                    }
                }
            }
        }
        """,
        {
            "servers": [
                {
                    "name": "Dummy",
                    "instances": [
                        {
                            "name": "1",
                            "classes": [
                                {
                                    "name": "DServer",
                                    "devices": [{"name": "dserver/Dummy/1"}],
                                },
                                {
                                    "name": "Dummy",
                                    "devices": [{"name": "test/dummy/1"}],
                                },
                            ],
                        }
                    ],
                }
            ]
        },
        id="SERVER_INSTANCES_QUERY",
    ),
]


@pytest.mark.parametrize("query,expected", QUERY_PARAMS)
@pytest.mark.asyncio
async def test_query(pytango_databaseds, query, expected):
    ok, result = await graphql(
        schema=schema, data={"query": query}, context_value=get_context_value(None)
    )
    assert ok
    assert "error" not in result
    assert result["data"] == expected
