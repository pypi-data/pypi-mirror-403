import base64
import logging

import numpy
import tango
from ariadne import ScalarType
from starlette.requests import Request

from .loaders import get_loaders

logger = logging.getLogger(__name__)

scalar_types = ScalarType("ScalarTypes")

# Define a formal threshold for "big int" (2^53 is commonly used for JSON precision)
BIGINT_THRESHOLD = 2**53 - 1


@scalar_types.serializer
def serialize_scalar_value(v: tango.DeviceAttribute):
    """
    Make sure the various things we can get from tango are JSON compatible
    """
    if isinstance(v, tango._tango.DevState):
        logger.debug(f"Serializing tango.DevState: {v}")
        return str(v)
    if isinstance(v, bytes):
        # Binary data, got to return a string
        logger.debug(f"Serializing bytes: {v}")
        return base64.encodebytes(v).decode()
    if isinstance(v, tuple):
        # DevEncoded
        logger.debug(f"Serializing tuple: {v}")
        try:
            return (v[0], v[1].decode())
        except ValueError as e:
            # "DevEncoded" values can contain anything, not necessarily compatible with
            # JSON. If so, we could consider base64 encoding. But for now, we just don't
            # support it. Those encodings would require specific support in the frontend
            # anyway.
            logger.debug(f"Failed to decode encoded value as string: {e}")
            return (v[0], None)
    if isinstance(v, int):
        # If it's a large integer (positive or negative), return as a string
        # JSON does not support arbitrary-precision integers and commonly limits
        # safe integer values to a max of 2^53-1. Numbers beyond this threshold
        # can lose precision when serialized to JSON. When Javascript parses such
        # large integers to strings, we ensure precision is preserved when the
        # GraphQL response is parsed by the frontend.
        if abs(v) > BIGINT_THRESHOLD:  # Formal check for large integers
            logger.debug(f"Serializing large int as string: {v}")
            return str(v)
    if isinstance(v, tango.StdStringVector):
        return list(v)  # Convert to list for serialization
    if isinstance(v, numpy.ndarray):
        return v.tolist()
    return v


def get_context_value(request: Request):
    # Context value function will be called for every request to GraphQL server
    # It's retrievable as "context" attribute of resolver's second argument
    return {
        "request": request,
        **get_loaders(),
    }
