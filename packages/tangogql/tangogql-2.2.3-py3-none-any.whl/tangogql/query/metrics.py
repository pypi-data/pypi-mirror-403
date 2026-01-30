"""
Some runtime metrics about the TangoGQL server.
"""

import tango
from ariadne import ObjectType

from ..subscription.listener import get_listener

metrics = ObjectType("Metrics")


@metrics.field("subscribedAttrs")
async def resolve_subscribed_attrs(*_):
    listener = get_listener()
    attrs = await listener.get_attributes()
    return attrs


subscribed_attr = ObjectType("SubscribedAttr")

EVENT_TYPES = {
    -1: "POLLING",
    tango.EventType.CHANGE_EVENT: "CHANGE_EVENT",
    tango.EventType.PERIODIC_EVENT: "PERIODIC_EVENT",
}


@subscribed_attr.field("eventType")
def resolve_event_type(obj, _):
    event_type_value = obj["eventType"]
    return EVENT_TYPES.get(event_type_value, "UNKNOWN_EVENT")


types = [metrics, subscribed_attr]
