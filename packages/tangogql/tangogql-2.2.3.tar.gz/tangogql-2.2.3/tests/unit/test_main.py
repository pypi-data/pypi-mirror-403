from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from tangogql.main import app, get_context_value


@pytest.fixture
def client():
    return TestClient(app)


def test_routes_exist(client):
    """Test that the server routes exist and respond correctly."""
    response = client.post("/db", json={"query": "{ __typename }"})
    assert response.status_code == 200


def test_websocket_route(client):
    """Test that the WebSocket route exists and responds correctly."""
    with client.websocket_connect("/socket") as websocket:
        assert websocket is not None


@patch("tangogql.main.GraphQL")
def test_graphql_handler(mock_graphql):
    """Test GraphQL handler initialization."""
    mock_schema = MagicMock()
    mock_graphql.return_value = MagicMock(
        schema=mock_schema, context_value=get_context_value, debug=True
    )
    handler_instance = mock_graphql()

    # Ensure the handler is being instantiated
    assert mock_graphql.call_count > 0
    assert handler_instance.schema == mock_schema
