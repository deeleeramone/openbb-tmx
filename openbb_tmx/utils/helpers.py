"""TMX Helpers Module."""

from datetime import timedelta
from typing import Dict, Literal

import requests
import requests_cache
import pandas as pd
from random_user_agent.user_agent import UserAgent
from openbb_core.app.utils import get_user_cache_directory

cache_dir = get_user_cache_directory()


def get_random_agent() -> str:
    user_agent_rotator = UserAgent(limit=100)
    user_agent = user_agent_rotator.get_random_user_agent()
    return user_agent


# Only used for obtaining the directory of all valid company tickers.
tmx_companies_session = requests_cache.CachedSession(
    f"{cache_dir}/http/tmx_companies", expire_after=timedelta(days=2)
)

# Only used for obtaining the directory of all valid indices.
tmx_indices_session = requests_cache.CachedSession(
    f"{cache_dir}/http/tmx_indices", expire_after=timedelta(days=10), use_cache_dir=True
)

# Only used for obtaining the all ETFs JSON file.
tmx_etfs_session = requests_cache.CachedSession(
    f"{cache_dir}/http/tmx_etfs", expire_after=timedelta(hours=4)
)


def get_all_etfs(use_cache: bool = True) -> Dict:
    """Gets a summary of the TMX ETF universe.

    Returns
    -------
    Dict
        Dictionary with all TMX-listed ETFs.
    """

    url = "https://dgr53wu9i7rmp.cloudfront.net/etfs/etfs.json"

    r = (
        tmx_etfs_session.get(url, timeout=10)
        if use_cache is True
        else requests.get(url, timeout=10)
    )
    if r.status_code != 200:
        raise RuntimeError(r.status_code)

    return r.json()


def get_tmx_tickers(
    exchange: Literal["tsx", "tsxv"] = "tsx", use_cache: bool = True
) -> Dict:
    """Gets a dictionary of either TSX or TSX-V symbols and names."""

    tsx_json_url = "https://www.tsx.com/json/company-directory/search"
    url = f"{tsx_json_url}/{exchange}/*"
    r = (
        tmx_companies_session.get(url, timeout=5)
        if use_cache is True
        else requests.get(url, timeout=5)
    )
    data = (
        pd.DataFrame.from_records(r.json()["results"])[["symbol", "name"]]
        .set_index("symbol")
        .sort_index()
    )
    results = data.to_dict()["name"]
    return results


def get_all_tmx_companies(use_cache: bool = True) -> Dict:
    """Merges TSX and TSX-V listings into a single dictionary."""
    all_tmx = {}
    tsx_tickers = get_tmx_tickers(use_cache=use_cache)
    tsxv_tickers = get_tmx_tickers("tsxv", use_cache=use_cache)
    all_tmx.update(tsxv_tickers)
    all_tmx.update(tsx_tickers)
    return all_tmx
