import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable, Sequence
from functools import lru_cache
from itertools import groupby
from operator import itemgetter
from random import random

import tango  # type: ignore

from ..settings import get_settings
from ..utils import get_db, get_device_proxy

logger = logging.getLogger(__name__)


TANGO_HOST = tango.ApiUtil.get_env_var("TANGO_HOST")
ATTR_PREFIX = f"tango://{TANGO_HOST}/"


class DeviceTracker:
    """
    Tracks attributes on a given Tango device. It's used by the
    Listener class.

    Uses events if possible, but falls back to periodic client
    polling if not. It will retry subscribing periodically.

    The behavior is as follows, when adding an attribute:
    - Try to subscribe to change events
      - if successful, start publishing events
      - if it fails, try periodic events
        - if successful, start publishing events
        - if it fails, fall back to polling.
          - All polled attributes are read and published
            periodically, controlled by the "poll_period" argument

    Now and then, a task checks if it's possible to subscribe
    to any polled attribute, basically starting over. This
    is controlled by the "sub_retry_period" argument

    Note:
    The polled attributes are read using read_attributes(),
    all in one call. This is done for performance as it's a lot
    faster to read many attributes this way. However, if a single
    attribute should be slow to read, causing a timeout, this
    prevents *any* attribute from being read.

    Not sure if this behavior is acceptable. But attributes
    should never time out, if the device is working.
    It's usually a sign that the device is broken, e.g. the
    process has hanged. So likely it would not be possible
    to get any useful info from it anyway...
    """

    def __init__(
        self,
        devicename: str,
        queue: asyncio.Queue,
        poll_period: float = 3.0,
        sub_retry_period: float = 60.0,
        extract_as=tango.ExtractAs.List,
        get_device_proxy=get_device_proxy,
        poll_sleep: Callable[[float], Awaitable] = asyncio.sleep,
        resub_sleep: Callable[[float], Awaitable] = asyncio.sleep,
    ):
        self.devicename = devicename
        self.proxy = None
        self.queue = queue
        self.poll_period = poll_period
        self.sub_retry_period = sub_retry_period
        self.extract_as = extract_as
        self.get_device_proxy = get_device_proxy
        self.poll_sleep = poll_sleep
        self.resub_sleep = resub_sleep

        self.last_sub_attempt: dict[str, float] = {}
        self.attributes: set[str] = set()
        self.new_attributes: set[str] = set()
        self.subs: dict[str, int | None] = {}
        self.subs_type: dict[str, tango.EventType] = {}
        self.conf_subs: dict[str, int] = {}
        self.polled: set[str] = set()
        self.poll_task = None
        self.sub_task = None

        self.attr_lock = asyncio.Lock()
        self.wait_event = asyncio.Event()
        self.logger = logger.getChild(f"DeviceTracker({devicename})")
        self.polling_exception = None

    @property
    def empty(self) -> bool:
        return len(self.attributes) == 0

    def event_type(self, attr_name) -> tango.EventType:
        return self.subs_type.get(attr_name, -1)  # POLLED

    def _publish_event(self, attr_name: str, attr_value: tango.DeviceAttribute):
        self.queue.put_nowait((attr_name, attr_value))

    async def _handle_event(self, event: tango.EventData):
        if event.err:
            name = event.attr_name.rsplit("/", 1)[1]
            self.logger.debug(
                f"Subscription error for {name}: {event.errors[0]} {event.errors[0].desc}"
            )
            # TODO maybe we should not immediately fall back to polling
            # on *all* errors...
            self.polled.add(name)
            self.last_sub_attempt[name] = time.time()
            event_name = event.attr_name.lower()
            if event_name.startswith(self.devicename):
                attr_name = event_name
            else:
                attr_name = f"{self.devicename}/{event.attr_value.name}".lower()
            self._publish_event(attr_name, tango.DevFailed(*event.errors))
            # Note: subscribe_event can succeed, but the first, synchronous event
            # is an error. This can happen e.g. when the attribute times out.
            # We set the sub to None to signal this.
            # TODO: does this necessarily mean that the subscription is bad?
            # Answer: Seems not. But do we want to complicate things here?
            if name not in self.subs:
                self.subs[name] = None
            else:
                await self._unsubscribe(name)
        else:
            # TODO it's not possible to trust event.attr_name to have the same
            # prefix as the device. Weird!
            event_name = event.attr_name.lower()
            if event_name.startswith(self.devicename):
                attr_name = event_name
            else:
                attr_name = f"{self.devicename}/{event.attr_value.name}".lower()
            self._publish_event(attr_name, event.attr_value)

    async def add_attributes(self, attributes: Sequence[str]):
        async with self.attr_lock:
            failed = []
            new_attributes = set(attributes) - self.attributes
            if new_attributes:
                self.logger.info("Adding attributes %r", new_attributes)
                tasks = (self._subscribe(attr) for attr in new_attributes)
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for attribute, result in zip(new_attributes, results, strict=True):
                    if result is not None:
                        failed.append(attribute)
                if failed:
                    await self._poll_attributes(failed)
                self.attributes.update(new_attributes)

    async def remove_attribute(self, attribute: str):
        try:
            self.attributes.remove(attribute)
            if attribute in self.subs:
                await self._unsubscribe(attribute)
            self.logger.debug("Removed %r", attribute)
        except KeyError:
            self.logger.warning(
                f"Failed to find attribute {attribute} in {self.attributes}!?"
            )

    async def start(self):
        """
        Publish values continally for some attributes on a given device.
        This may be via subscriptions, or by client side polling.
        The set of attributes may change during runtime.
        """
        try:
            # TODO this can take quite some time, up to 20 seconds and
            # still succeed (though it will most likely not work)
            self.proxy = await self.get_device_proxy(self.devicename)
        except tango.DevFailed as e:
            self.logger.debug(f"Failed to set up tracker: {e.args[0].desc}")
            # TODO Handle! This probably means the device is not even
            # defined, so it is unlikely to start working. But we
            # should perhaps retry periodically?
            raise
        else:
            self.logger.debug("Created proxy; starting tracker")
            self.poll_task = asyncio.create_task(self._poller())
            self.sub_task = asyncio.create_task(self._subscriber())

    async def stop(self):
        self.logger.info("Stopping")
        for attr in list(self.attributes):
            await self._unsubscribe(attr)
        if self.poll_task:
            self.poll_task.cancel()
        if self.sub_task:
            self.sub_task.cancel()

    async def _subscribe(self, attribute: str):
        try:
            self.logger.debug("Attempting change_event subscription for %r", attribute)
            sub = await self.proxy.subscribe_event(
                attribute,
                tango.EventType.CHANGE_EVENT,
                self._handle_event,
                extract_as=self.extract_as,
            )
            self.subs_type[attribute] = tango.EventType.CHANGE_EVENT
        except tango.DevFailed as e:
            # try to subscribe to PERIODIC_EVENT
            self.logger.debug(
                "Subscription to change_event for %r failed: %r",
                attribute,
                e.args[0].desc,
            )
            self.logger.debug(
                "Attempting periodic_event subscription for %r", attribute
            )
            sub = await self.proxy.subscribe_event(
                attribute,
                tango.EventType.PERIODIC_EVENT,
                self._handle_event,
                extract_as=self.extract_as,
            )
            self.subs_type[attribute] = tango.EventType.PERIODIC_EVENT
        if attribute not in self.subs:
            self.subs[attribute] = sub
            logger.debug(
                "Subscribed to %s/%s (%s)",
                self.devicename,
                attribute,
                self.subs_type[attribute],
            )
        else:
            # This means we got an immediate error event, let's unsub
            await self.proxy.unsubscribe_event(sub)
            self.subs.pop(attribute, None)
            self.subs_type.pop(attribute, None)

    async def _unsubscribe(self, attribute: str):
        change_sub = self.subs.pop(attribute, None)

        # Safely remove from subs_type, if it exists
        self.subs_type.pop(attribute, None)

        if change_sub:
            try:
                await self.proxy.unsubscribe_event(change_sub)
            except KeyError:
                logger.exception(
                    f"Error unsubscribing to {self.devicename}/{attribute}"
                )
            logger.debug(f"Unsubscribed from {self.devicename}/{attribute}")
        else:
            logger.debug(
                f"Not subscribed to {self.devicename}/{attribute},"
                + " can't unsubscribe"
            )

    async def _subscriber(self, period=60):
        """
        Handle subscription retries and cleanup
        """
        while True:
            limit = time.time() - self.sub_retry_period
            polled = self.attributes - set(self.subs)
            for attribute in polled:
                t = self.last_sub_attempt.get(attribute)
                if t is None or t < limit:
                    self.logger.debug(f"Trying to subscribe to {attribute}")
                    await self._subscribe(attribute)

            old_subscriptions = set(self.subs) - self.attributes
            for attribute in old_subscriptions:
                await self._unsubscribe(attribute)
                self.logger.debug(f"Dropped old subscription to {attribute}")

            await self.resub_sleep(period)

    async def _poll_attributes(self, attrs: Sequence[str]):
        """Read some attributes and publish the results"""
        if not self.proxy:
            return
        self.logger.debug("_poll_attributes %r", attrs)
        try:
            results = await self.proxy.read_attributes(
                attrs, extract_as=self.extract_as
            )
        except tango.DevFailed as e:
            self.logger.debug(f"Could not read attributes {attrs}: {e.args[0].desc}")
            self.polling_exception = e
            # Device could not be reached, or some attribute(s) timed out
            # TODO put off polling a bit and retry later?
            for attr in attrs:
                await self.queue.put((self._get_full_attr(attr), e))
        else:
            self.polling_exception = None
            for device_attribute in results:
                if device_attribute.has_failed:
                    self.logger.debug(
                        "Failed to read attribute %r", device_attribute.name
                    )
                name = self._get_full_attr(device_attribute.name)
                self.logger.debug("Publish %r", name)
                self._publish_event(name, device_attribute)

    async def _poller(self) -> None:
        logger.debug("tracking device %s", self.devicename)

        # Random wait, to prevent listeners from polling in step
        await self.poll_sleep(self.poll_period * random())

        try:
            # TODO?
            while True:
                # This loop will run as long as the tracker is active
                # It periodically reads attributes that aren't subscribed.
                t0 = time.time()
                polled = self.attributes - set(self.subs)
                if polled:
                    self.logger.debug("Polled: %r, Subbed: %r", polled, self.subs)
                    await self._poll_attributes(list(polled))

                dt = time.time() - t0
                if dt > self.poll_period:
                    # TODO automatic adaptation, e.g. lengthening period by 50%, and then
                    # later try shortening again
                    self.logger.debug(
                        "Poll period too short; did not have time for everything"
                    )
                await self.poll_sleep(max(0.1, self.poll_period - dt))

        except Exception:
            self.logger.exception("Unhandled error")

        self.logger.debug("Exit tracker")

    def _get_full_attr(self, attribute):
        return f"{self.devicename}/{attribute}".lower()

    def __repr__(self):
        return (
            f"DeviceTracker[{self.devicename}, attributes={self.attributes},"
            + f" polled={self.polled}]"
        )


class Listener:
    """
    This thing handles getting realtime values from Tango attributes and
    distributing it to "listeners". It uses subscriptions if available
    or else falls back to client polling. The idea is to create one of these
    for an entire app, to prevent duplication of work, something like
    how Taurus TangoAttribute works. But here there's nothing preventing
    from creating several ones. There should just be no reason to do it.

    Probably the "listen" method is the most convenient to use, as it returns
    an async iterator of events for any number of attributes.

    Somewhat tested, but so far only at small scale.

    Technically it creates one DeviceTracker instance per *device* monitored
    (each of which handles all attributes on that device). All events from
    a tracker come in on a queue, that are put on a central event_queue.
    Anyone can listen to attributes, and they will get the corresponding
    events from the event_queue.
    """

    def __init__(
        self, poll_period: float = 3.0, get_device_proxy=get_device_proxy, get_db=get_db
    ) -> None:
        self.poll_period = poll_period
        self.get_device_proxy = get_device_proxy
        self.get_db = get_db
        self.event_queue: asyncio.Queue = asyncio.Queue()
        # TODO maybe use weakref here, so that we can automatically clean up
        # listeners that no longer exist?
        self.listeners: dict[
            str, list[asyncio.Queue[tuple[str, tango.DeviceAttribute]]]
        ] = {}
        self.device_trackers: dict[str, DeviceTracker] = {}
        self.tracker_locks: dict[str, asyncio.Lock] = {}
        self._task = None
        self._latest_data: dict[str, tango.DeviceAttribute] = {}

    def start(self):
        "Start working"
        self._task = asyncio.create_task(self._start())

    async def get_attributes(self) -> Sequence[dict]:
        """
        Returns the currently tracked attributes, as a list of dicts with
        information.
        """

        # Collect attribute info
        attrs_per_device = defaultdict(list)

        for tracker in self.device_trackers.values():
            for attribute in tracker.attributes:
                name = f"{tracker.devicename}/{attribute}"
                parts = tracker.devicename.rsplit("/", 3)
                server, domain, member = parts[-3], parts[-2], parts[-1]
                device_attribute_name = f"{server}/{domain}/{member}/{attribute}"
                listeners = self.listeners.get(name)
                event_type = tracker.event_type(attribute)
                info = {
                    "name": device_attribute_name,
                    "attribute": attribute,
                    "listeners": len(listeners),
                    "eventType": event_type,
                }
                attrs_per_device[tracker.devicename].append(info)
        # Check device accessibility
        trackers = list(self.device_trackers.values())
        coros = (tracker.proxy.ping() for tracker in trackers)
        pings = await asyncio.gather(*coros, return_exceptions=True)
        results = []
        for tracker, ping in zip(trackers, pings, strict=True):
            attrs = attrs_per_device.get(tracker.devicename, [])
            for attr_info in attrs:
                results.append({**attr_info, "deviceAccessible": isinstance(ping, int)})
        return results

    async def _start(self):
        try:
            while True:
                key, value = await self.event_queue.get()
                if listeners := self.listeners.get(key):
                    for listener in listeners:
                        listener.put_nowait((key, value))
                    self._latest_data[key] = value
                elif listeners is not None:
                    logger.debug(f"No listeners for {key}, cleaning up")
                    self.listeners.pop(key)
        except RuntimeError:
            # Event loop probably closed, time to exit
            pass
        except Exception:
            logger.exception("Unhandled error in start task")
            raise

    def add_attrs(self, attributes: Sequence[str]):
        if not self._task:
            self.start()
        split_attrs = (attribute.rsplit("/", 1) for attribute in attributes)
        attrs_per_dev = groupby(
            sorted(split_attrs, key=itemgetter(0)), key=itemgetter(0)
        )
        tasks = []
        for dev, grp in attrs_per_dev:
            _, attrs = zip(*grp, strict=True)
            task = asyncio.create_task(self._update_tracker(dev, attrs))
            tasks.append(task)
        return asyncio.wait(tasks)

    async def _update_tracker(self, dev, attrs):
        lock = self.tracker_locks.get(dev)
        if lock is None:
            lock = self.tracker_locks[dev] = asyncio.Lock()
        async with lock:
            if dev in self.device_trackers:
                tracker = self.device_trackers[dev]
            else:
                logger.info("Adding tracker for %s", dev)
                tracker = DeviceTracker(
                    dev,
                    self.event_queue,
                    poll_period=self.poll_period,
                    get_device_proxy=self.get_device_proxy,
                )
                try:
                    await tracker.start()
                except tango.DevFailed as e:
                    # This should only happen if the device doesn't exist
                    logger.error(
                        f"Could not set up listener for {dev}: {e.args[0].desc}"
                    )
                    # Send fake error events to listeners, they must be informed
                    for attr in attrs:
                        full_name = f"{dev}/{attr}"
                        self.event_queue.put_nowait(
                            (full_name, tango.DevFailed(*e.args))
                        )
                    return
                self.device_trackers[dev] = tracker
            logger.info("Adding attributes %s to dev %s", attrs, dev)
            await tracker.add_attributes(attrs)

    async def remove_attr(self, attribute: str):
        dev, attr = attribute.rsplit("/", 1)
        tracker = self.device_trackers.get(dev)
        if tracker:
            lock = self.tracker_locks[dev]
            logger.debug("Removing attribute %s", attribute)
            async with lock:
                await tracker.remove_attribute(attr)
                if tracker.empty:
                    logger.info("Tracker for %s is empty; removing", dev)
                    await tracker.stop()
                    del self.device_trackers[dev]
        self._latest_data.pop(attribute, None)

    async def add_listeners(
        self,
        attrs: Sequence[str],
        queue: asyncio.Queue[tuple[str, tango.DeviceAttribute]],
    ):
        "Add attributes to be monitored, events will be put on the queue"
        for attr in attrs:
            self.listeners.setdefault(attr, []).append(queue)
            if latest_data := self._latest_data.get(attr):
                queue.put_nowait((attr, latest_data))
        await self.add_attrs(attrs)

    async def remove_listener(
        self, attr: str, queue: asyncio.Queue[tuple[str, tango.DeviceAttribute]]
    ):
        "Remove a listener queue"
        logger.debug("Remove listener %r", attr)
        try:
            queues = self.listeners.get(attr)
            if queues:
                try:
                    queues.remove(queue)
                    if not queues:
                        # No more listeners to this attr, clean up
                        self.listeners.pop(attr)
                        await self.remove_attr(attr)
                    else:
                        pass
                except ValueError:
                    pass
        except Exception:
            logger.exception("Failed to remove listener")

    async def listen(
        self, attributes: Sequence[str], delay=0.1, throttle=True, cleanup_after=60
    ):
        """
        Create an async iterator for events from some attributes.

        Attributes must be given as full "tango resource locations", i.e.
        "tango://{TANGO_HOST}/{device}/{attr}"
        """
        logger.debug("Start listening to %r", attributes)
        queue: asyncio.Queue[tuple[str, tango.DeviceAttribute]] = asyncio.Queue()
        asyncio.create_task(self.add_listeners(attributes, queue))
        while True:
            try:
                if throttle:
                    # Just send the latest event
                    events = {}
                    while not queue.empty():
                        key, data = await queue.get()
                        events[key] = data
                    for event in events.items():
                        yield event
                else:
                    # Send all events
                    while not queue.empty():
                        yield await queue.get()
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                # This means whoever created the listener is done with it
                break

        # TODO this is an unsophisticated way to manage listeners exiting.
        # The idea is to keep listeners around for a few seconds, since
        # the most likely attributes to be used again are the same ones.
        # I think this is not the best place to do it though.
        try:
            await asyncio.sleep(cleanup_after)
        finally:
            for attr in attributes:
                await self.remove_listener(attr, queue)
        logger.debug("Stopped listening to %r", attributes)


@lru_cache(1)
def get_listener():
    """
    Since there should be a single Listener instance per app, always
    use this cached getter to get it.
    """
    settings = get_settings()
    return Listener(poll_period=settings.attribute_poll_period)


async def main(attrs):
    logger.setLevel(logging.DEBUG)
    "Takes a list of (full) attribute names, and monitors them"
    h = Listener()
    # We get the (full) name of the attribute, and the data
    # which may be a DeviceAttribute or a DevFailed
    async for attr, data in h.listen(attrs):
        print(f"--------{attr}--------")
        if isinstance(data, tango.DevFailed):
            print(data)
        else:
            print(data.value)


if __name__ == "__main__":
    # E.g. python listener.py sys/tg_test/1/double_scalar sys/tg_test/1/ampli
    # Should work whether they are configured with polling and change events,
    # or not, and handle this changing during runtime

    import sys

    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(sys.argv[1:]))
