import logging

import numpy as np
import tango
from ariadne import ObjectType

from .auth import check_auth
from .utils import get_async_db, get_device_proxy

logger = logging.getLogger(__name__)


mutation = ObjectType("Mutations")


@mutation.field("putDeviceProperty")
@check_auth
async def resolve_put_device_property(
    _, info, device: str, name: str, value: list[str]
):
    adb = await get_async_db()
    try:
        await adb.put_device_property(device, {name: value})
    except tango.DevFailed as e:
        logger.debug(
            f"Failed to put device property {device}, {name}, {value}", exc_info=True
        )
        return {"ok": False, "message": [e.args[0].desc]}
    return {"ok": True}


put_device_property = ObjectType("PutDeviceProperty")


@mutation.field("deleteDeviceProperty")
@check_auth
async def resolve_delete_device_property(_, info, device: str, name: str):
    adb = await get_async_db()
    try:
        await adb.delete_device_property(device, name)
        return {"ok": True}
    except tango.DevFailed as e:
        logger.debug(
            f"Failed to delete device property {device}, {name}", exc_info=True
        )
        return {"ok": False, "message": [e.args[0].desc]}


delete_device_property = ObjectType("DeleteDeviceProperty")


@mutation.field("setAttributeValue")
@check_auth
async def resolve_write_attribute(
    _, info, device: str, name: str, value: int | float | bool | str
):
    try:
        proxy = await get_device_proxy(device)
        fields = {
            n.name.value for f in info.field_nodes for n in f.selection_set.selections
        }
        if "valueBefore" in fields:
            # We only do this extra read if the query requested it
            old_result = await proxy.read_attribute(name)
            old_value = old_result.value
        else:
            old_value = None
        await proxy.write_attribute(name, value)
        return {
            "ok": True,
            "valueBefore": old_value,
            "attribute": {"name": name, "device": device},
        }
    except tango.DevFailed as e:
        logger.debug(
            f"Failed to write attribute {device}, {name}, {value}", exc_info=True
        )
        return {
            "ok": False,
            "message": [e.args[0].desc],
            "attribute": {"name": name, "device": device},
        }
    except TypeError as e:
        logger.debug(
            f"Failed to write attribute {device}, {name}, {value}", exc_info=True
        )
        return {
            "ok": False,
            "message": [str(e)],
            "attribute": {"name": name, "device": device},
        }


write_attribute = ObjectType("SetAttributeValue")


@write_attribute.field("attribute")
async def resolve_attribute(data, _):
    return "{device}/{name}".format(**data["attribute"])


@mutation.field("executeCommand")
@check_auth
async def resolve_execute_command(
    *_, device: str, command: str, argin: [int | float | bool | str | list] = None
):
    try:
        proxy = await get_device_proxy(device)
        # TODO is this safe? I guess None is not really a possible tango value
        # anyway...
        if argin is None:
            result = await proxy.command_inout(command)
        else:
            result = await proxy.command_inout(command, argin)

        # If the command out type is DevVar*StringArray, we will receive
        # a list of two elements, of which the first is a numpy array.
        if isinstance(result, list):
            if isinstance(result[0], np.ndarray):
                result = [result[0].tolist(), result[1]]
        return {"ok": True, "output": result}
    except tango.DevFailed as e:
        # TODO argin could be huge...
        logger.debug(
            f"Failed to run command {device}, {command}, {argin}", exc_info=True
        )
        return {"ok": False, "message": [e.args[0].desc]}
    except TypeError as e:
        logger.debug(
            f"Failed to run command {device}, {command}, {argin}", exc_info=True
        )
        return {"ok": False, "message": [str(e)]}


execute_command = ObjectType("ExecuteDeviceCommand")


types = [mutation, put_device_property, write_attribute, execute_command]
