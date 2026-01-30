"""
'Data loaders' are a way to optimize getting data, in this case
from the tango control system. This allows batching and caching of
database queries and proxy calls in an easy way, as loaders handle
it under the hood.

The main thing to be aware of is that the loader functions must
take a list of arguments, and return a list of results.
Each result corresponds to one argument, in the same order.

Loaders live only during the context of a single query, so the
caching is only to avoid fetching the same data twice in a row.

For more info see https://ariadnegraphql.org/docs/dataloaders
"""

import asyncio
import logging
from collections.abc import Sequence
from itertools import groupby
from operator import itemgetter

import tango
from aiodataloader import DataLoader

from .utils import DbDeviceInfo, batched, get_db, get_device_proxy

logger = logging.getLogger(__name__)


SERVER_INSTANCES_QUERY = """
    SELECT DISTINCT server
    FROM device
    WHERE server LIKE '{}'
    ORDER BY server
"""


async def get_server_instances(servers: Sequence[str]) -> Sequence[str]:
    logger.debug("get_server_instances(%r)", servers)
    db = get_db()
    patterns = (f"{server}/%" for server in servers)
    sql_query = SERVER_INSTANCES_QUERY.format("|".join(patterns))
    _, lvalues = await db.command_inout("DbMySQLSelect", sql_query)
    server_instance = [server.split("/") for server in lvalues]
    instances_by_server = groupby(server_instance, itemgetter(0))
    data = {
        server.lower(): [inst for _, inst in grp] for server, grp in instances_by_server
    }
    return [data.get(server.lower(), []) for server in servers]


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

DEVICES_QUERY = f"SELECT {', '.join(DEVICE_FIELDS)} FROM device WHERE name IN({{}})"


async def get_device_infos_from_db(
    device_names: Sequence[str],
) -> Sequence[DbDeviceInfo]:
    logger.debug("get_device_infos_from_db(%r)", device_names)
    # db_proxy = await get_device_proxy(get_db().dev_name())
    db = get_db()
    dev_array = ",".join(f"'{name}'" for name in device_names)
    sql_query = DEVICES_QUERY.format(dev_array)
    _, lvalues = await db.command_inout("DbMySQLSelect", sql_query)
    data = {
        row[0].lower(): DbDeviceInfo(row)
        for row in batched(lvalues, len(DEVICE_FIELDS))
    }
    return [
        data.get(name.lower(), ValueError(f"Device {name} does not exist"))
        for name in device_names
    ]


PROPERTIES_QUERY = """
    SELECT device, name, value
    FROM property_device
    WHERE device IN({})
    ORDER BY device, name, count
"""


async def get_device_properties_from_db(
    device_names: Sequence[str],
) -> Sequence[list[str]]:
    logger.debug("get_device_properties_from_db(%r)", device_names)
    db = get_db()
    dev_array = ",".join(f"'{name}'" for name in set(device_names))
    # TODO we load all properties for the given devices. Should be possible to
    # get only the properties requested, but not sure it is worth it.
    sql_query = PROPERTIES_QUERY.format(dev_array)
    _, lvalues = await db.command_inout("DbMySQLSelect", sql_query)
    results = batched(lvalues, 3)
    by_device_name = groupby(results, itemgetter(0, 1))
    props_by_device = {}
    for (device, name), grp in by_device_name:
        # using device.lower() as the key so that all properties are included
        # even if they are linked to a device using inconsistent casing
        value = [row for _, _, row in grp]
        props_by_device.setdefault(device.lower(), []).append((device, name, value))
    return [props_by_device.get(device.lower(), []) for device in device_names]


def make_empty_attrinfo(name):
    """
    Since there are 'normal' situations where we are unable to access attributes
    (e.g. the device may not be running) we instead return an empty object.
    """
    info = tango.AttributeInfoEx()
    info.name = name
    return info


async def _get_attr_infos(device, attrs):
    """Get info for some attributes on a given device"""
    try:
        proxy = await get_device_proxy(device)
    except tango.DevFailed as e:
        if e.args[0].reason == "DB_DeviceNotDefined":
            # This is a "real" error; device doesn't even exist
            logger.error(f"Failed to get proxy for {device}:, {e.args[0]}")
            infos = [ValueError(e.args[0].desc)] * len(attrs)
        else:
            # This just happens to fail, maybe the device is not running?
            infos = [make_empty_attrinfo(a) for a in attrs]
    else:
        if len(attrs) == 1:
            # get info for one attribute
            try:
                infos = await proxy.get_attribute_config_ex(attrs[0])
            except tango.DevFailed as e:
                if e.args[0].reason == "API_AttrNotFound":
                    # Real error; attribute doesn't exist
                    logger.error("Could not get info for attr: %r", e.args[0].desc)
                    infos = [ValueError(e.args[0].desc)]
                else:
                    # Again, this could just be because the device isn't up
                    infos = [make_empty_attrinfo(attrs[0])]
        else:
            # get info for all attributes, and pick the ones we need
            all_infos = proxy.attribute_list_query_ex()
            lookup = {attr.lower(): None for attr in attrs}
            for info in all_infos:
                lower_name = info.name.lower()
                if lower_name in lookup:
                    lookup[lower_name] = info
            infos = lookup.values()
    return device, attrs, infos


async def get_device_attribute_infos(
    attribute_names: Sequence[str],
) -> Sequence[tango.AttributeInfoEx]:
    logger.debug("get_device_attribute_infos(%r)", attribute_names)
    device_attr = (name.rsplit("/", 1) for name in attribute_names)
    by_device = groupby(device_attr, key=itemgetter(0))
    # Get info for all attributes concurrently
    device_infos = await asyncio.gather(
        *(
            _get_attr_infos(device, [attr for _, attr in grp])
            for device, grp in by_device
        )
    )
    infos_by_name = {}
    for device, attrs, infos in device_infos:
        infos_by_name.update(
            (f"{device}/{attr}".lower(), info or make_empty_attrinfo(attr))
            for attr, info in zip(attrs, infos, strict=True)
        )
    # Return infos in original order
    return [infos_by_name[name.lower()] for name in attribute_names]


async def _read_attributes(device, group):
    attrs = [attr for _, attr in group]
    try:
        proxy = await get_device_proxy(device)
    except tango.DevFailed as e:
        if e.args[0].reason == "DB_DeviceNotDefined":
            logger.debug(f"Devuce {device} not found: {e.args[0]}")
            # This is a "real" error; device doesn't even exist
            return device, attrs, ValueError(e.args[0].desc)
        else:
            # This just happens to fail, maybe the device is not running?
            infos = [make_empty_devattr(a) for a in attrs]
            return device, attrs, infos
    try:
        result = await proxy.read_attributes(attrs, extract_as=tango.ExtractAs.List)
        return device, attrs, result
    except tango.DevFailed as e:
        return device, attrs, e


def make_empty_devattr(name):
    da = tango.DeviceAttribute()
    da.name = name
    da.value = None
    da.w_value = None
    return da


async def read_device_attributes(
    attribute_names: Sequence[str],
) -> Sequence[tango.DeviceAttribute]:
    logger.debug("read_device_attribute_values(%r)", attribute_names)
    device_attr = (name.rsplit("/", 1) for name in attribute_names)
    by_device = groupby(device_attr, key=itemgetter(0))
    results_by_name = {}
    reads = (_read_attributes(device, list(group)) for device, group in by_device)
    results = await asyncio.gather(*reads, return_exceptions=True)
    for device, attrs, result in results:
        if isinstance(result, tango.DevFailed):
            results_by_name.update((f"{device}/{attr}", result) for attr in attrs)
        else:
            results_by_name.update(
                (f"{device}/{attr}", value)
                for attr, value in zip(attrs, result, strict=True)
            )
    return [results_by_name[name] for name in attribute_names]


def get_loaders():
    return {
        "server_instance_loader": DataLoader(get_server_instances),
        "device_loader": DataLoader(get_device_infos_from_db),
        "device_property_loader": DataLoader(get_device_properties_from_db),
        "attribute_info_loader": DataLoader(get_device_attribute_infos),
        "attribute_value_loader": DataLoader(read_device_attributes),
    }
