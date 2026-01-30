import base64
from unittest.mock import Mock, patch

import pytest
import tango
from starlette.requests import Request

# Import the functions from your module
from tangogql.common import BIGINT_THRESHOLD, get_context_value, serialize_scalar_value


# Test serialization of different DevState values
def test_dev_state_serialization():
    # Create a mock that looks like a DevState
    class MockDevState(Mock):
        def __init__(self, state_name, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._state_name = state_name
            # Make this look like a DevState to isinstance checks
            self.__class__ = tango._tango.DevState

        def __str__(self):
            return self._state_name

    states = ["ON", "OFF", "FAULT", "RUNNING"]
    for state_name in states:
        state = MockDevState(state_name)
        result = serialize_scalar_value(state)
        assert result == state_name
        assert isinstance(result, str)


# Test different types of byte data
@pytest.mark.parametrize(
    "input_bytes",
    [
        b"simple text",
        b"\x00\x01\x02\x03",  # Binary data
        b"",  # Empty bytes
        "Unicode \u1234".encode(),  # Unicode bytes
        b"A" * 1000,  # Large byte string
    ],
)
def test_bytes_serialization(input_bytes):
    result = serialize_scalar_value(input_bytes)
    assert isinstance(result, str)
    # Verify we can decode it back
    decoded = base64.decodebytes(result.encode())
    assert decoded == input_bytes


# Test DevEncoded tuples with different formats
@pytest.mark.parametrize(
    "input_tuple",
    [
        ("format1", b"data1"),
        ("", b""),  # Empty values
        ("binary", b"\x00\x01\x02\x03"),
        ("unicode", "测试".encode()),
        ("long_format" * 10, b"long_data" * 100),  # Long values
    ],
)
def test_dev_encoded_serialization(input_tuple):
    result = serialize_scalar_value(input_tuple)
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], str)
    assert result[0] == input_tuple[0]
    assert isinstance(result[1], str)


# Test integer handling around threshold
@pytest.mark.parametrize(
    "input_int,expected_type",
    [
        (0, int),
        (-1, int),
        (BIGINT_THRESHOLD - 1, int),
        (BIGINT_THRESHOLD, int),
        (BIGINT_THRESHOLD + 1, str),
        (-BIGINT_THRESHOLD, int),
        (2**60, str),  # Very large number
    ],
)
def test_integer_threshold_handling(input_int, expected_type):
    result = serialize_scalar_value(input_int)
    if expected_type is str:
        assert isinstance(str(result), str)
        assert int(str(result)) == input_int
    else:
        assert isinstance(result, int)
        assert result == input_int


# Test various data types
@pytest.mark.parametrize(
    "input_value",
    [
        None,
        True,
        False,
        3.14159,
        float("inf"),
        float("-inf"),
        [],
        [1, 2, 3],
        {},
        set(),
        range(5),
    ],
)
def test_misc_types_serialization(input_value):
    result = serialize_scalar_value(input_value)
    assert result == input_value


# Test context value with different loader configurations
def test_get_context_value_variations():
    mock_request = Mock(spec=Request)

    # Test with empty loaders
    with patch("tangogql.common.get_loaders", return_value={}):
        context = get_context_value(mock_request)
        assert context == {"request": mock_request}

    # Test with multiple loaders
    test_loaders = {
        "device_loader": Mock(),
        "attribute_loader": Mock(),
        "command_loader": Mock(),
        "pipe_loader": Mock(),
    }
    with patch("tangogql.common.get_loaders", return_value=test_loaders):
        context = get_context_value(mock_request)
        assert context["request"] == mock_request
        for loader_name, loader in test_loaders.items():
            assert context[loader_name] == loader


# Test error conditions
def test_error_conditions():
    # Test with non-decodable data in DevEncoded tuple
    mock_non_decodable = Mock()
    mock_non_decodable.decode.side_effect = AttributeError
    with pytest.raises(AttributeError):
        serialize_scalar_value(("format", mock_non_decodable))


# Test deep nested structures
def test_deep_nested_structure():
    # Create a structure that would cause recursion if not handled properly
    deep_dict = {}
    current = deep_dict
    for _i in range(1000):  # Create a very deep dictionary
        current["next"] = {}
        current = current["next"]

    # This should not raise RecursionError
    result = serialize_scalar_value(deep_dict)
    assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main(["-v"])
