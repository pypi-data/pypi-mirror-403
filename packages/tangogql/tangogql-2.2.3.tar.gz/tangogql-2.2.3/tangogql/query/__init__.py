from . import (
    device,
    device_attribute,
    device_command,
    device_property,
    metrics,
    query,
    server,
)

types = [
    *query.types,
    *device.types,
    *device_property.types,
    *device_attribute.types,
    *device_command.types,
    *server.types,
    *metrics.types,
]
