import logging

import tango
from ariadne import ObjectType

from ..common import scalar_types

logger = logging.getLogger(__name__)


device_attribute = ObjectType("DeviceAttribute")


@device_attribute.field("name")
async def _(full_name: str, info) -> str:
    attr_info = await info.context["attribute_info_loader"].load(full_name)
    return attr_info.name


@device_attribute.field("device")
def _(full_name: str, _) -> str:
    return full_name.rsplit("/", 1)[0]


@device_attribute.field("datatype")
async def _(full_name: str, info) -> str:
    attr_info = await info.context["attribute_info_loader"].load(full_name)
    try:
        return tango.CmdArgType.values[attr_info.data_type]
    except (AttributeError, KeyError):
        pass


@device_attribute.field("dataformat")
async def _(full_name: str, info) -> str:
    attr_info = await info.context["attribute_info_loader"].load(full_name)
    return tango.AttrDataFormat.values[attr_info.data_format]


@device_attribute.field("label")
async def _(full_name: str, info) -> str:
    attr_info = await info.context["attribute_info_loader"].load(full_name)
    # tangogql compatibility
    # TODO this is weird; we should return none if there's no label?
    # UI should use name as fallback
    return getattr(attr_info, "label", None) or attr_info.name


# tangogql compatibility
# TODO change the schema to keep the underscores?
PARAM_LOOKUP = {
    "maxvalue": "max_value",
    "minvalue": "min_value",
    "minalarm": "min_alarm",
    "maxalarm": "max_alarm",
    "displevel": "disp_level",
}

# Values that Tango returns for unset config parameters
CONFIG_PLACEHOLDERS = {
    "format": "Not specified",
    "description": "No description",
    "min_value": "Not specified",
    "max_value": "Not specified",
    "min_alarm": "Not specified",
    "max_alarm": "Not specified",
}


async def device_attribute_config_field(full_name, info) -> str:
    """Handle device attribute config fields"""

    attr_info = await info.context["attribute_info_loader"].load(full_name)
    tango_name = PARAM_LOOKUP.get(info.field_name, info.field_name)
    value = getattr(attr_info, tango_name)
    # We want to return None instead of Tango's placeholders
    placeholder = CONFIG_PLACEHOLDERS.get(tango_name)
    if placeholder and value == placeholder:
        return None
    return value


device_attribute.field("format")(device_attribute_config_field)
device_attribute.field("unit")(device_attribute_config_field)
device_attribute.field("description")(device_attribute_config_field)
device_attribute.field("displevel")(device_attribute_config_field)
device_attribute.field("maxvalue")(device_attribute_config_field)
device_attribute.field("minvalue")(device_attribute_config_field)
device_attribute.field("maxalarm")(device_attribute_config_field)
device_attribute.field("minalarm")(device_attribute_config_field)
device_attribute.field("writable")(device_attribute_config_field)


# ==== Attribute read ====


@device_attribute.field("value")
async def _(full_name, info):
    dev_attr = await info.context["attribute_value_loader"].load(full_name)
    try:
        return dev_attr.value
    except AttributeError:
        pass


@device_attribute.field("writevalue")
async def _(full_name, info):
    dev_attr = await info.context["attribute_value_loader"].load(full_name)
    try:
        return dev_attr.w_value
    except AttributeError:
        pass


@device_attribute.field("quality")
async def _(full_name: str, info):
    dev_attr = await info.context["attribute_value_loader"].load(full_name)
    return dev_attr.quality


@device_attribute.field("timestamp")
async def _(full_name: str, info):
    dev_attr = await info.context["attribute_value_loader"].load(full_name)
    return dev_attr.time.totime()


@device_attribute.field("enumLabels")
async def _(full_name: str, info) -> list[str]:
    dev_attr = await info.context["attribute_info_loader"].load(full_name)
    return dev_attr.enum_labels


types = [device_attribute, scalar_types]
