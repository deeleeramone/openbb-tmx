"""TMX fetchers tests."""

from datetime import date

import pytest
from openbb_core.app.service.user_service import UserService
from openbb_tmx.models.equity_profile import TmxEquityProfileFetcher

test_credentials = UserService().default_user_settings.credentials.model_dump()


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": [("User-Agent", None)],
        "filter_query_parameters": [
            None,
        ],
    }


@pytest.mark.record_http
def test_tmx_equity_profile_fetcher(credentials=test_credentials):
    params = {"symbol": "RY,NTR"}

    fetcher = TmxEquityProfileFetcher()
    result = fetcher.test(params, credentials)
    assert result is None
