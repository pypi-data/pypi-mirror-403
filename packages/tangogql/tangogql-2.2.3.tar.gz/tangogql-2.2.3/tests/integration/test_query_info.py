"""
Integration test for query
    Before running this test, make sure tangdb graphiql
    is up and running on http://localhost:5004/db

The test will be skipped if the WEBSERVER_TESTS environment variable is not set
"""

import os

import pytest
import requests


@pytest.fixture
def graphql_endpoint():
    return "http://localhost:5004/db"


@pytest.mark.skipif(
    not os.environ.get("WEBSERVER_TESTS"),
    reason="WEBSERVER_TESTS not set in environment",
)
def test_info_query(graphql_endpoint):
    query = """
        query {
            info
        }
    """

    headers = {"Content-Type": "application/json"}

    response = requests.post(graphql_endpoint, headers=headers, json={"query": query})
    result = response.json()
    assert "data" in result
    assert "info" in result["data"]
    assert "info" in result["data"]
    assert "TANGO Database" in result["data"]["info"]
