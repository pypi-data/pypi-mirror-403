from ariadne import ObjectType

device_property = ObjectType("DeviceProperty")


@device_property.field("device")
def resolve_device(obj, _) -> str:
    return obj[0]


@device_property.field("name")
def resolve_name(obj, _) -> str:
    return obj[1]


@device_property.field("value")
def resolve_value(obj, _) -> list[str]:
    return obj[2]


types = [device_property]
