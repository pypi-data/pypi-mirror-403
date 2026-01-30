from collections.abc import Iterator

import tango
from ariadne import QueryType

from ..utils import (
    DbDeviceInfo,
    batched,
    get_async_db,
    get_db,
    get_device_proxy,
    get_filter_rule,
)

query = QueryType()


@query.field("info")
async def resolve_info(*_) -> str:
    adb = await get_async_db()
    return await adb.get_info()


@query.field("servers")
async def resolve_servers(*_, pattern: str = "*") -> Iterator[str]:
    adb = await get_async_db()
    servers = await adb.get_server_name_list()
    rule = get_filter_rule(pattern)
    return [srv for srv in servers if rule.match(srv)]


@query.field("instances")
async def resolve_instances(*_, pattern: str = "*") -> Iterator[str]:
    adb = await get_async_db()
    servers = await adb.get_server_list(pattern)
    return [srv.split("/") for srv in servers]


dev_info = tuple[str | None, str | None, str | None, list[str]]


@query.field("classes")
async def resolve_classes(*_, pattern: str = "*") -> Iterator[dev_info]:
    adb = await get_async_db()
    classes = await adb.get_class_list(pattern)
    return [
        (None, None, devclass, await adb.get_device_exported_for_class(devclass))
        for devclass in classes
    ]


@query.field("device")
def resolve_device(_, info, name: str) -> DbDeviceInfo:
    return info.context["device_loader"].load(name)


DEVICE_FIELDS = [
    "name",
    "alias",
    "exported",
    "ior",
    "host",
    "server",
    "pid",
    "class",
    "version",
    "started",
    "stopped",
]

DEVICES_QUERY = f"SELECT {', '.join(DEVICE_FIELDS)} FROM device WHERE name LIKE '{{}}'"


@query.field("devices")
async def resolve_devices(*_, pattern: str = "*") -> Iterator[tango.DbDevFullInfo]:
    db_proxy = await get_device_proxy(get_db().dev_name())
    sql_query = DEVICES_QUERY.format(pattern.replace("*", "%"))
    svalues, lvalues = await db_proxy.command_inout("DbMySQLSelect", sql_query)
    return [DbDeviceInfo(row) for row in batched(lvalues, len(DEVICE_FIELDS))]


@query.field("attributes")
async def resolve_attributes(_, info, fullNames: list[str]) -> Iterator[str]:
    return fullNames


@query.field("metrics")
def resolve_metrics(*_):
    return ""


@query.field("tangoHost")
def resolve_tangohost(*_):
    tango_host = tango.ApiUtil.get_env_var("TANGO_HOST")
    return tango_host


types = [query]
