"""TMX provider module."""

from openbb_provider.abstract.provider import Provider
from openbb_tmx.models.equity_profile import TmxEquityProfileFetcher

tmx_provider = Provider(
    name="tmx",
    website="https://www.tmx.com/",
    description="""
        TMX Group Companies
         - Toronto Stock Exchange
         - TSX Venture Exchange
         - TSX Trust
         - Montréal Exchange
         - TSX Alpha Exchange
         - Shorcan
         - CDCC
         - CDS
         - TMX Datalinx
         - Trayport
    """,
    required_credentials=None,
    fetcher_dict={
        "EquityInfo": TmxEquityProfileFetcher,
    },
)
