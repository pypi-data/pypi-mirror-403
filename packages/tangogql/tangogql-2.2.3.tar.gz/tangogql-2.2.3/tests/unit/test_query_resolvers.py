from unittest.mock import AsyncMock, patch

import pytest

from tangogql.query.query import resolve_info


@pytest.fixture
def async_mock_db():
    mock_db = AsyncMock()
    mock_db.get_info.return_value = "Mocked tango db info"
    return mock_db


@pytest.mark.asyncio
async def test_resolve_info(async_mock_db):
    async def mocked_get_async_db():
        return async_mock_db

    with patch("tangogql.query.query.get_async_db", side_effect=mocked_get_async_db):
        result = await resolve_info(None, None)
        assert result == "Mocked tango db info"
