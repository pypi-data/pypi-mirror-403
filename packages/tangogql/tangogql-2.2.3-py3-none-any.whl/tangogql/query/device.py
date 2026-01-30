import asyncio
from collections.abc import Iterator

import tango
from ariadne import ObjectType
from graphql.type import GraphQLResolveInfo

from ..utils import DbDeviceInfo, get_device_proxy, get_filter_rule

device = ObjectType("Device")


# @device.field("alias")
# async def resolve_alias(info: DbDeviceInfo, _) -> str:
#     return info.alias


# @device.field("pid")
# async def resolve_pid(info: DbDeviceInfo, _) -> str:
#     return info.pid


@device.field("deviceClass")
def resolve_dev_class(dev_info: DbDeviceInfo, _) -> str:
    return dev_info.class_name


@device.field("state")
async def resolve_state(dev_info: DbDeviceInfo, info) -> str:
    state = await info.context["attribute_value_loader"].load(f"{dev_info.name}/state")
    if isinstance(state, tango.DeviceAttribute):
        return state.value


@device.field("startedDate")
def resolve_started_date(dev_info: DbDeviceInfo, _) -> str:
    return dev_info.started


@device.field("stoppedDate")
def resolve_stopped_date(dev_info: DbDeviceInfo, _) -> str:
    return dev_info.stopped


@device.field("connected")
async def resolve_connected(dev_info: DbDeviceInfo, _) -> bool:
    try:
        # Let's not wait for too long here, it will make the query time out.
        # If we can't contact the device in 3 seconds, it's probably not there...
        await asyncio.wait_for(_ping_device(dev_info.name), timeout=3)
        return True
    except asyncio.TimeoutError:
        return False
    except tango.DevFailed:
        return False


async def _ping_device(name):
    proxy = await get_device_proxy(name)
    return await proxy.ping()


@device.field("server")
def resolve_server(dev_info: DbDeviceInfo, _) -> DbDeviceInfo:
    return dev_info


@device.field("properties")
async def resolve_properties(
    dev_info: DbDeviceInfo, info, pattern: str = "*"
) -> Iterator[tuple[str, str, list[str]]]:
    # The loader gives us all props for the device, we filter it here
    all_props = await info.context["device_property_loader"].load(dev_info.name)
    rule = get_filter_rule(pattern)
    return ((dev, name, value) for dev, name, value in all_props if rule.match(name))


@device.field("attributes")
async def resolve_attributes(
    dev_info: DbDeviceInfo, info: GraphQLResolveInfo, pattern: str = "*"
) -> Iterator[str]:
    try:
        proxy = await get_device_proxy(dev_info.name)
    except tango.DevFailed:
        return []
    loop = asyncio.get_event_loop()

    # Read attribute info
    # Note: we can't filter this call, so we'll have to get all of them and
    # filter the list afterwards.
    try:
        all_attribute_names = await loop.run_in_executor(None, proxy.get_attribute_list)
        rule = get_filter_rule(pattern)
        attr_names = (name for name in all_attribute_names if rule.match(name))
        return [f"{dev_info.name}/{attr}" for attr in attr_names]
    except tango.DevFailed:
        return []


@device.field("commands")
async def resolve_commands(
    dev_info: tango.DbDevFullInfo, _, pattern: str = "*"
) -> Iterator[tuple[str, tango.CommandInfo]]:
    proxy = await get_device_proxy(dev_info.name)
    loop = asyncio.get_event_loop()
    command_infos = await loop.run_in_executor(None, proxy.command_list_query)
    rule = get_filter_rule(pattern)
    for cmd_info in command_infos:
        if rule.match(cmd_info.cmd_name):
            yield dev_info.name, cmd_info


# Actually server info... rename?
device_info = ObjectType("DeviceInfo")


@device_info.field("id")
def resolve_id(info: tango.DbDevFullInfo, _) -> str:
    return info.server


@device_info.field("host")
def resolve_host(info: DbDeviceInfo, _) -> str:
    return info.host


types = [device, device_info]
