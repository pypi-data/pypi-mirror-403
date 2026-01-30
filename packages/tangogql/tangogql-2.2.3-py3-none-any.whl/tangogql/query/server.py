from itertools import groupby

from ariadne import ObjectType

from ..utils import get_async_db, get_filter_rule

server = ObjectType("Server")


@server.field("name")
def resolve_name(name, _):
    return name


@server.field("instances")
async def resolve_instances(server, info, pattern: str = "*"):
    instances = await info.context["server_instance_loader"].load(server)
    rule = get_filter_rule(pattern)
    return [(server, instance) for instance in instances if rule.match(instance)]


server_instance = ObjectType("ServerInstance")


@server_instance.field("name")
def resolve_instance_name(obj, _):
    _, instance = obj
    return instance


@server_instance.field("server")
def resolve_server(obj, _):
    server, _ = obj
    return server


@server_instance.field("classes")
async def resolve_server_classes(data, _, pattern: str = "*"):
    server, instance = data
    adb = await get_async_db()
    devices_classes = await adb.get_device_class_list(f"{server}/{instance}")
    rule = get_filter_rule(pattern)
    devs_per_class = groupby(
        sorted(zip(devices_classes[1::2], devices_classes[::2], strict=True)),
        key=lambda pair: pair[0],
    )
    return [
        (server, instance, clss, [d for _, d in devices])
        for clss, devices in devs_per_class
        if rule.match(clss)
    ]


device_class = ObjectType("DeviceClass")


@device_class.field("server")
def resolve_server2(obj, _):
    server, _, _, _ = obj
    return server


@device_class.field("instance")
def resolve_instance(obj, _):
    _, instance, _, _ = obj
    return instance


@device_class.field("name")
def resolve_class_name(obj, _):
    _, _, name, _ = obj
    return name


@device_class.field("devices")
def resolve_devices(obj, info, pattern: str = "*"):
    _, _, _, devices = obj
    return [info.context["device_loader"].load(device) for device in devices]


types = [server, server_instance, device_class]
