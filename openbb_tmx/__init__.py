"""TMX Provider Module."""

from openbb_core.provider.abstract.provider import Provider
from openbb_tmx.models.equity_profile import TmxEquityProfileFetcher
from openbb_tmx.models.equity_search import TmxEquitySearchFetcher
from openbb_tmx.models.options_chains import TmxOptionsChainsFetcher

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
    fetcher_dict={
        "EquityProfile": TmxEquityProfileFetcher,
        "EquitySearch": TmxEquitySearchFetcher,
        "OptionsChains": TmxOptionsChainsFetcher,
    },
)
