"""
Taurus based attribute event subscriber. Subscribes to a bunch
of attributes, and generates events for all of them.

Taurus transparently handles client polling and Tango events, so
we don't have to care about it. It also knows what is already
subscribed, and re-uses it so we don't get duplicated tango subs.
Lastly, it will unsubscribe automatically when we aren't listening
any more.

TODO:
- error handling
- configuration of polling period
- not sending new events if value doesn't change?
- capped event frequency?
- performance tests
"""

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from functools import lru_cache

import tango
from taurus import Manager
from taurus.core.tango import TangoAttribute
from taurus.core.taurusbasetypes import TaurusEventType

logger = logging.getLogger("subscription")


# TODO use config
manager = Manager()
manager.changeDefaultPollingPeriod(3000)


async def attributes_generator(
    _, __, fullNames: list[str]
) -> AsyncIterator[tuple[str, tango.EventData]]:
    "Async generator of events for a bunch of tango attributes, using Taurus"

    # We need to keep references to Attributes, so they don't get cleaned up
    # until we exit this generator.
    attributes = {}

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    @lru_cache(None)
    def get_device_name(full_name):
        "Get just the device name"
        # Maybe Taurus has a way to get this but I didn't find it
        m = re.match(r"(tango://[^:]+:\d+/)([^/]+/[^/]+/[^/]+)/(.*)", full_name)
        return m.group(2)

    def event_callback(attr, event_type, event_value):
        "Callback that receives attribute data and puts it on the queue"
        logger.debug("event_callback: %r, %r, %r", attr, event_type, event_value)
        if event_type in {TaurusEventType.Change, TaurusEventType.Periodic}:
            # Not sure if Taurus subscribes to periodic events, so
            # I think periodic means client polling here.
            dev_attr = event_value._pytango_dev_attr
            # TODO maybe not optimal since all subscriptions may not care about
            # all this. OTOH it avoids some overhead in calling resolvers I guess.
            # Do some performance tests to see which is best.
            event = {
                "device": get_device_name(attr.fullname),  # TODO
                "fullName": attr.fullname,  # or just name?
                "attribute": dev_attr.name.lower(),
                "value": dev_attr.value,
                "writeValue": dev_attr.w_value,
                "quality": tango.AttrQuality.values[dev_attr.quality],
                "timestamp": dev_attr.time.totime(),
            }
            loop.call_soon_threadsafe(queue.put_nowait, event)
        # TODO config events (not really part of TangoGQL for now)
        # TODO error events? Don't think Taranta cares about those but maybe it should.

    tango_host = tango.ApiUtil.get_env_var("TANGO_HOST")

    logger.info(f"Subscribing to {len(fullNames)} attributes: {', '.join(fullNames)}")
    names = set(fullNames)
    while names:
        name = names.pop()
        logger.debug(f"Subscribing to {name}")
        tango_uri = "tango://" + tango_host + "/" + name
        try:
            # Use a thread pool to set up taurus subscriptions, it can be a bit slow
            # and we don't want to block the whole server
            attr = await loop.run_in_executor(
                None, manager.getObject, TangoAttribute, tango_uri
            )
            attr.addListener(event_callback)
            logger.debug(f"Subscribed to {name}")
        except AttributeError:
            # TODO a weird bug in Taurus (?) sometimes causes the first attribute
            # to throw an exception. Probably has to do with threading.
            # Remove this except clause to see it.
            # To work around it, we put it back and continue.
            logger.debug(f"Failed to subscribe to {name}, retrying later")
            names.add(name)
            await asyncio.sleep(0.1)
            continue
        attributes[name] = attr

    while True:
        try:
            yield await queue.get()
        except asyncio.CancelledError:
            logger.info(f"Exit subscription for attributes: {', '.join(fullNames)}")
            break

    # Keep the listeners for a little while, saving time if they are needed again
    await asyncio.sleep(10)
