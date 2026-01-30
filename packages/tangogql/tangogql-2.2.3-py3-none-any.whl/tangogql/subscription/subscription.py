import logging

import tango
from ariadne import ObjectType, SubscriptionType

from ..common import scalar_types

# There are two implementations of the attribute subscription mechanism
# right now; one based on Taurus which is likely quite reliable, but has
# a large dependency, and a experimental pure pytango asyncio based one.
# TODO make this a config flag?
# try:
#     from .taurus_attributes import attributes_generator
# except ImportError:
#     logging.info("Taurus is not installed; using experimental subscription implementation.")
from .attributes import attributes_generator

logger = logging.getLogger(__name__)


subscription = SubscriptionType()
subscription.set_source("attributes", attributes_generator)


EventInfo = tuple[str, tango.DeviceAttribute]


@subscription.field("attributes")
def resolve_attribute(info: EventInfo, _, fullNames: list[str]) -> EventInfo:
    return info


attribute_frame = ObjectType("AttributeFrame")


types = [subscription, attribute_frame, scalar_types]
