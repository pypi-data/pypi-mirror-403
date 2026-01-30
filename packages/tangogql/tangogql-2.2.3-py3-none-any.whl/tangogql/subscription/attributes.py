import asyncio
import logging
import re
from collections.abc import AsyncIterator
from functools import lru_cache
from time import time

import tango

from .listener import get_listener

logger = logging.getLogger(__name__)


@lru_cache(1)
def get_attr_prefix():
    tango_host = tango.ApiUtil.get_env_var("TANGO_HOST")
    attr_prefix = f"tango://{tango_host}/"
    return attr_prefix


@lru_cache(None)
def split_name(full_name):
    "Get just the device name"
    m = re.match(r"^(tango://[^:]+:\d+/)([^/]+/[^/]+/[^/]+)/([^/]+)$", full_name)
    if m is None:
        raise RuntimeError(f"Invalid attribute name '{full_name}'")
    return m.groups()


@lru_cache(None)
def get_full_name(maybe_full_name):
    "Get the full Tango 'URL' for the attribute"
    # TODO is this too naive?
    if maybe_full_name.startswith("tango://"):
        return maybe_full_name
    attr_prefix = get_attr_prefix()
    return f"{attr_prefix}{maybe_full_name}"


async def attributes_generator(_, __, fullNames: list[str]) -> AsyncIterator[dict]:
    """
    Async generator of "real time" values for a bunch of attributes.
    """
    logger.info("Subscribing to attributes: %r", fullNames)
    names = [get_full_name(name).lower() for name in fullNames]
    # Discard broken attribute names
    valid_names = []
    for name in names:
        try:
            split_name(name)
        except RuntimeError as e:
            # Send an error event.
            yield {
                "fullName": name,
                "timestamp": time(),
                "error": {"desc": f"Subscription failed: {e}"},
            }
        else:
            valid_names.append(name)
    if not valid_names:
        # No valid names found, nothing more to do.
        return
    queue = asyncio.Queue()
    listener = get_listener()
    await listener.add_listeners(valid_names, queue)
    while True:
        try:
            attr, data = await queue.get()
            _, device, name = split_name(attr)
            if isinstance(data, tango.DeviceAttribute):
                if data.has_failed:
                    errors = data.get_err_stack()
                    yield {
                        "device": device,
                        "fullName": attr,
                        "attribute": data.name.lower(),
                        "quality": tango.AttrQuality.values[data.quality],
                        "timestamp": time(),  # TODO we don't get a time in this case..?
                        # TODO maybe do something more sophisticated here; it may depend
                        # on the situation which item in the args is more informational...
                        "error": errors[0],
                    }
                else:
                    yield {
                        "device": device,
                        "fullName": attr,
                        "attribute": data.name.lower(),
                        "value": data.value,
                        "writeValue": data.w_value,
                        "quality": tango.AttrQuality.values[data.quality],
                        "timestamp": data.time.totime(),
                    }
            elif isinstance(data, tango.DevFailed):
                yield {
                    "device": device,
                    "fullName": attr,
                    "attribute": name,
                    # TODO maybe do something more sophisticated here; it may depend
                    # on the situation which item in the args is more informational...
                    "error": data.args[0],
                    "timestamp": time(),  # TODO get the real timestamp
                }
        except asyncio.CancelledError:
            break

    # Keep listeners around for a little while. The most likely new subscription
    # is probably the same attributes again.
    await asyncio.sleep(10)

    for name in valid_names:
        await listener.remove_listener(name, queue)

    raise asyncio.CancelledError()
