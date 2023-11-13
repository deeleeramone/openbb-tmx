"""TMX Helpers Module."""

from datetime import timedelta
from typing import Dict

import requests
import requests_cache
from random_user_agent.user_agent import UserAgent
from openbb_core.app.utils import get_user_cache_directory

cache_dir = get_user_cache_directory()


def get_random_agent() -> str:
    user_agent_rotator = UserAgent(limit=100)
    user_agent = user_agent_rotator.get_random_user_agent()
    return user_agent


# Only used for obtaining the directory of all valid company tickers.
tmx_companies_session = requests_cache.CachedSession(
    f"{cache_dir}/http/tmx_companies", expire_after=timedelta(days=9)
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
    """Gets a summary of the TMX Group ETFs universe.

    Returns
    -------
    pd.DataFrame
        DataFrame with a universe summary.
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
