import tango
from ariadne import ObjectType

device_command = ObjectType("DeviceCommand")


@device_command.field("name")
def resolve_name(obj: tuple[str, tango.CommandInfo], _) -> str:
    cmd_info = obj[1]
    return cmd_info.cmd_name


@device_command.field("device")
def resolve_device(obj: tuple[str, tango.CommandInfo], _) -> str:
    dev_name = obj[0]
    return dev_name


# TODO change schema to keep underscores
CMD_LOOKUP = {
    "displevel": "disp_level",
    "intypedesc": "in_type_desc",
    "outtypedesc": "out_type_desc",
    "intype": "in_type",
    "outtype": "out_type",
}


@device_command.field("displevel")
@device_command.field("intypedesc")
@device_command.field("outtypedesc")
def resolve_disp_level(obj: tuple[str, tango.CommandInfo], info) -> str:
    cmd_info = obj[1]
    return str(getattr(cmd_info, CMD_LOOKUP[info.field_name]))


@device_command.field("intype")
@device_command.field("outtype")
def resolve_in_out_types(obj: tuple[str, tango.CommandInfo], info) -> str:
    cmd_info = obj[1]
    value = getattr(cmd_info, CMD_LOOKUP[info.field_name])
    return tango.CmdArgType.values[value]


types = [device_command]
