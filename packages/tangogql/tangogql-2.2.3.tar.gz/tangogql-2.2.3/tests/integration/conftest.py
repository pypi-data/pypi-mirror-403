import logging
import os
import subprocess
import sys
import time

import pytest
import tango

from tangogql.subscription.listener import get_listener

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(autouse=True)
def clear_listener_cache():
    "Ensure that each test uses a fresh listener"
    get_listener.cache_clear()


PYTANGO_TANGO_HOST = "127.0.0.1:11000"
# By default, just store the DB in RAM. If there's a need to inspect the database
# after running tests, you can override this by setting the env var with a filename
# e.g. "export PYTANGO_DATABASE_NAME=tango_database.db"
PYTANGO_DATABASE_NAME = os.environ.get("PYTANGO_DATABASE_NAME", ":memory:")


@pytest.fixture(scope="function")
def pytango_databaseds():
    """
    Runs a pytango database server that we can run the tests against.
    This eliminates the need for MySQL etc.
    Also creates and starts a "dummy" test device.
    """
    # TODO get a free port
    try:
        os.environ["TANGO_HOST"] = PYTANGO_TANGO_HOST

        databaseds = subprocess.Popen(
            [sys.executable, "-m", "databaseds.database", "2"],
            stderr=subprocess.PIPE,
            env={
                "TANGO_HOST": PYTANGO_TANGO_HOST,
                "PYTANGO_DATABASE_NAME": PYTANGO_DATABASE_NAME,
            },
        )

        waited = 0
        dt = 0.3
        while True:
            time.sleep(dt)
            waited += dt
            if databaseds.poll() is not None:
                stderr = databaseds.stderr.read().decode()
                print(stderr)
                raise RuntimeError(f"Database stopped: {databaseds.returncode}")
            try:
                db = tango.Database()
                db.get_info()
                break
            except tango.DevFailed as e:
                if waited > 10:
                    raise RuntimeError("Tired of waiting for database...") from e
            except AssertionError:
                pass

        device = "test/dummy/1"
        dev_info = tango.DbDevInfo()
        dev_info.name = device
        dev_info._class = "Dummy"
        dev_info.server = "Dummy/1"
        db.add_server(dev_info.server, dev_info, with_dserver=True)
        db.put_device_property(device, {"graphql_test": ["abc", "def"]})

        # Start our dummy device
        dummy = subprocess.Popen(
            [sys.executable, "tests/integration/dummy.py", "1"], stderr=subprocess.PIPE
        )
        waited = 0
        dt = 0.3
        while True:
            time.sleep(dt)
            waited += dt
            if dummy.poll() is not None:
                stderr = dummy.stderr.read().decode()
                print(stderr)
                raise RuntimeError(f"Dummy device stopped: {dummy.returncode}")
            try:
                proxy = tango.DeviceProxy(
                    device, green_mode=tango.GreenMode.Synchronous
                )
                proxy.ping()
                if proxy.read_attribute("State").value == tango.DevState.RUNNING:
                    break
            except tango.DevFailed as e:
                if waited > 10:
                    raise RuntimeError("Tired of waiting for device proxy...") from e
            except AssertionError:
                pass

        yield device
    finally:
        # Clean up
        try:
            dummy.kill()
            db.delete_server(dev_info.server)
        except Exception:
            pass
        try:
            databaseds.kill()
        except Exception:
            pass

        del os.environ["TANGO_HOST"]


@pytest.fixture(scope="session")
def tangodb():
    """
    This fixture is only useful if you already have a Tango DB set up
    in your environment. Normally it should be fine to use the pytango
    database server fixture above.

    Assuming we start with a 'vanilla' Tango DB, this will add some
    configuration used by the tests, as well as a dummy tango device.
    """
    device = "test/dummy/1"
    db = tango.Database()
    dev_info = tango.DbDevInfo()
    dev_info.name = device
    dev_info._class = "Dummy"
    dev_info.server = "Dummy/1"
    db.add_server(dev_info.server, dev_info, with_dserver=True)
    db.put_device_property(device, {"graphql_test": ["abc", "def"]})

    # Start our dummy device
    dummy = subprocess.Popen(
        ["python", "tests/integration/dummy.py", "1"], stderr=subprocess.PIPE
    )
    waited = 0
    dt = 0.3
    while True:
        time.sleep(dt)
        waited += dt
        if dummy.poll() is not None:
            stderr = dummy.stderr.read().decode()
            print(stderr)
            raise RuntimeError(f"Dummy device stopped: {dummy.returncode}")
        try:
            proxy = tango.DeviceProxy(device, green_mode=tango.GreenMode.Synchronous)
            proxy.ping()
            break
        except tango.DevFailed:
            if waited > 10:
                raise RuntimeError("Tired of waiting for device proxy...") from None
        except AssertionError:
            pass

    yield device

    # Clean up
    dummy.kill()
    db.delete_server(dev_info.server)
