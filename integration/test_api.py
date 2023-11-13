"""API integration tests for TMX extension."""

import pytest
import requests
from openbb_provider.utils.helpers import get_querystring

# pylint: disable=too-many-lines,redefined-outer-name


@pytest.fixture(scope="session")
def headers():
    return {}


@pytest.mark.parametrize(
    "params",
    [
        ({"symbol": "AAPL:US", "provider": "tmx"}),
        ({"symbol": "RY,GLXY", "provider": "tmx"}),
    ],
)
@pytest.mark.integration
def test_equity_profile(params, headers):
    params = {p: v for p, v in params.items() if v}

    query_str = get_querystring(params, [])
    url = f"http://0.0.0.0:8000/api/v1/equity/profile?{query_str}"
    result = requests.get(url, headers=headers, timeout=10)
    assert isinstance(result, requests.Response)
    assert result.status_code == 200
