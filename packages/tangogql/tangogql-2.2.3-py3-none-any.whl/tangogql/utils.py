import asyncio
import fnmatch
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from inspect import ismethod
from itertools import islice

import graphql
import tango
from aiocache import cached
from tango.asyncio import DeviceProxy

logger = logging.getLogger(__name__)


# TODO cache database calls


@lru_cache(1)
def get_db():
    return tango.Database()


class AsyncTangoDatabase:
    def __init__(self, db=None):
        self.db = None
        self.done = asyncio.Event()

    async def init(self):
        logger.debug("Creating AsyncTangoDatabase")
        loop = asyncio.get_event_loop()
        self.db = await loop.run_in_executor(None, tango.Database)
        self.done.set()
        return self

    async def get(self):
        await self.done.wait()
        return self

    def __getattr__(self, attr):
        cmd = getattr(self.db, attr)

        if ismethod(cmd) and not asyncio.iscoroutine(cmd):

            def wrapper(*args):
                logger.debug(f"Async DB call: {attr} {args}")
                return loop.run_in_executor(None, cmd, *args)

            loop = asyncio.get_event_loop()
            # return lambda *args: loop.run_in_executor(None, cmd, *args)
            return wrapper


_db: AsyncTangoDatabase | None = None


def get_async_db():
    """
    Get an async DB object.
    Make sure we only create the DB once, and return the same object
    on any subsequent calls. Even if the DB is not done when the next
    call comes in. It can take ~1s to connect to the Tango DB.
    """
    global _db
    if _db is None:
        _db = AsyncTangoDatabase()
        return _db.init()
    elif _db:
        return _db.get()


@cached()
async def get_device_proxy(devname):
    return await DeviceProxy(devname)


@lru_cache(1000)
def get_filter_rule(pattern: str) -> re.Pattern:
    "Turn a simple wildcard pattern (using *) into a regex pattern"
    return re.compile(fnmatch.translate(pattern), re.IGNORECASE)


def selected_field_names(selection_set: graphql.SelectionSetNode) -> Iterator[str]:
    """
    Get the names of fields selected.
    """
    assert isinstance(selection_set, graphql.SelectionSetNode)

    for node in selection_set.selections:
        # Field
        if isinstance(node, graphql.FieldNode):
            yield node.name.value
        else:
            # This is a naive implementation that will only work for simple fields
            raise NotImplementedError(
                f"Sorry, field type not implemented: {type(node)}"
            )


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    # Note: there will be a 'batched' function included in python 3.12
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


@dataclass
class DbDeviceInfo:
    name: str
    alias: str
    exported: int
    ior: str
    host: str
    server: str
    pid: int
    class_name: str
    version: str
    started: datetime
    stopped: datetime

    def __init__(self, row):
        self.name = row[0]
        self.alias = row[1]
        self.exported = int(row[2])
        self.ior = row[3]
        self.host = row[4]
        self.server = row[5]
        self.pid = int(row[6])
        self.class_name = row[7]
        self.version = row[8]
        try:
            self.started = datetime.fromisoformat(row[9]) if row[9] else None
        except ValueError:
            # There may be broken values like "0000-00-00 00:00:00" in the DB
            self.started = None
        try:
            self.stopped = datetime.fromisoformat(row[10]) if row[10] else None
        except ValueError:
            self.stopped = None
