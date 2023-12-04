"""TMX Helpers Module."""

from io import StringIO
from datetime import datetime, timedelta, date as dateType
from typing import Dict, Literal, Optional

import requests
import requests_cache
import pandas as pd
import pandas_market_calendars as mcal
from pandas.tseries.holiday import next_workday
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


def check_weekday(date) -> str:
    """Helper function to check if the input date is a weekday, and if not, returns the next weekday.

    Parameters
    ----------
    date: str
        The date to check in YYYY-MM-DD format.

    Returns
    -------
    str
        Date in YYYY-MM-DD format.  If the date is a weekend, returns the date of the next weekday.
    """

    if pd.to_datetime(date).weekday() not in range(0, 5):
        date_ = next_workday(pd.to_datetime(date)).strftime("%Y-%m-%d")
        date = date_
    return date


def get_all_options_tickers() -> pd.DataFrame:
    """Returns a DataFrame with all valid ticker symbols."""

    r = tmx_companies_session.get(
        "https://www.m-x.ca/en/trading/data/options-list", timeout=5
    )
    if r.status_code == 200:
        options_listings = pd.read_html(StringIO(r.text))
        listings = pd.concat(options_listings)
        listings = listings.set_index("Option Symbol").drop_duplicates().sort_index()
        symbols = listings[:-1]
        symbols = symbols.fillna(value="")
        symbols["Underlying Symbol"] = (
            symbols["Underlying Symbol"].str.replace(" u", ".UN").str.replace("––", "")
        )
        return symbols
    raise RuntimeError(f"Error with the request:  {r.status_code}")


def get_current_options(symbol: str) -> pd.DataFrame:
    """Gets the current quotes for the complete options chain."""

    SYMBOLS = get_all_options_tickers()
    data = pd.DataFrame()
    symbol = symbol.upper()

    # Remove echange  identifiers from the symbol.
    if ".TO" in symbol:
        symbol = symbol.replace(".TO", "")
    if ".TSX" in symbol:
        symbol = symbol.replace(".TSX", "")

    # Underlying symbol may have a different ticker symbol than the ticker used to lookup options.
    if len(SYMBOLS[SYMBOLS["Underlying Symbol"].str.contains(symbol)]) == 1:
        symbol = SYMBOLS[SYMBOLS["Underlying Symbol"] == symbol].index.values[0]
    # Check if the symbol has options trading.
    if symbol not in SYMBOLS.index and not SYMBOLS.empty:
        raise ValueError(
            f"The symbol, {symbol}, is not a valid listing or does not trade options."
        )

    QUOTES_URL = f"https://www.m-x.ca/en/trading/data/quotes?symbol={symbol}"

    cols = [
        "expiration",
        "strike",
        "bid",
        "ask",
        "lastPrice",
        "change",
        "openInterest",
        "volume",
        "optionType",
    ]

    r = requests.get(QUOTES_URL, timeout=5)
    data = pd.read_html(StringIO(r.text))[0]
    data = data.iloc[:-1]

    expirations = (
        data["Unnamed: 0_level_0"]["Expiry date"].astype(str).rename("expiration")
    )

    expirations = expirations.str.strip("(Weekly)")

    strikes = (
        data["Unnamed: 7_level_0"]
        .dropna()
        .sort_values("Strike")  # type: ignore
        .rename(columns={"Strike": "strike"})
    )

    calls = pd.concat([expirations, strikes, data["Calls"]], axis=1)
    calls["expiration"] = pd.DatetimeIndex(calls["expiration"]).astype(str)
    calls["optionType"] = "call"
    calls.columns = cols
    calls = calls.set_index(["expiration", "strike", "optionType"])

    puts = pd.concat([expirations, strikes, data["Puts"]], axis=1)
    puts["expiration"] = pd.DatetimeIndex(puts["expiration"]).astype(str)
    puts["optionType"] = "put"
    puts.columns = cols
    puts = puts.set_index(["expiration", "strike", "optionType"])

    chains = pd.concat([calls, puts])
    chains["openInterest"] = chains["openInterest"].astype("int64")
    chains["volume"] = chains["volume"].astype("int64")
    chains["change"] = chains["change"].astype(float)
    chains["lastPrice"] = chains["lastPrice"].astype(float)
    chains["bid"] = chains["bid"].astype(float)
    chains["ask"] = chains["ask"].astype(float)
    chains = chains.sort_index()
    chains = chains.reset_index()
    now = datetime.now()
    temp = pd.DatetimeIndex(chains.expiration)
    temp_ = (temp - now).days + 1  # type: ignore
    chains["dte"] = temp_

    chains["contract_symbol"] = (
        symbol
        + pd.to_datetime(chains["expiration"]).dt.strftime("%y%m%d")
        + (chains["optionType"].replace("call", "C").replace("put", "P"))
        + chains["strike"].astype(str)
    )

    return chains


def download_eod_chains(symbol: str, date: Optional[dateType] = None):
    """Downloads EOD chains data for a given symbol and date."""

    symbol = symbol.upper()
    SYMBOLS = get_all_options_tickers()
    # Remove echange  identifiers from the symbol.
    if ".TO" in symbol:
        symbol = symbol.replace(".TO", "")
    if ".TSX" in symbol:
        symbol = symbol.replace(".TSX", "")

    # Underlying symbol may have a different ticker symbol than the ticker used to lookup options.
    if len(SYMBOLS[SYMBOLS["Underlying Symbol"].str.contains(symbol)]) == 1:
        symbol = SYMBOLS[SYMBOLS["Underlying Symbol"] == symbol].index.values[0]
    # Check if the symbol has options trading.
    if symbol not in SYMBOLS.index and not SYMBOLS.empty:
        raise ValueError(
            f"The symbol, {symbol}, is not a valid listing or does not trade options."
        )

    BASE_URL = "https://www.m-x.ca/en/trading/data/historical?symbol="

    cal = mcal.get_calendar(name="TSX")
    holidays = list(cal.regular_holidays.holidays().strftime("%Y-%m-%d"))  # type: ignore

    if date is None:
        EOD_URL = BASE_URL + f"{symbol}" "&dnld=1#quotes"
    if date is not None:
        date = check_weekday(date)  # type: ignore
        if date in holidays:
            date = (pd.to_datetime(date) + timedelta(days=1)).strftime("%Y-%m-%d")  # type: ignore
        date = check_weekday(date)  # type: ignore
        if date in holidays:
            date = (pd.to_datetime(date) + timedelta(days=1)).strftime("%Y-%m-%d")  # type: ignore

        EOD_URL = (
            BASE_URL + f"{symbol}" "&from=" f"{date}" "&to=" f"{date}" "&dnld=1#quotes"
        )

    r = requests.get(EOD_URL, timeout=5)  # type: ignore

    if r.status_code != 200:
        raise RuntimeError(f"Error with the request:  {r.status_code}")

    data = pd.read_csv(StringIO(r.text))
    if data.empty:
        raise ValueError(
            f"No data found for, {symbol}, on, {date}. The symbol may not have been listed, or traded options, before that date."
        )

    contractSymbol = []

    for i in data.index:
        contractSymbol.append(data["Symbol"].iloc[i].replace(" ", ""))
    data["contractSymbol"] = contractSymbol

    data["optionType"] = data["Call/Put"].replace(0, "call").replace(1, "put")

    data = data.drop(
        columns=[
            "Symbol",
            "Class Symbol",
            "Root Symbol",
            "Underlying Symbol",
            "Ins. Type",
            "Call/Put",
        ]
    )

    cols = [
        "date",
        "strike",
        "expiration",
        "bid",
        "ask",
        "bidSize",
        "askSize",
        "lastPrice",
        "volume",
        "previousClose",
        "change",
        "open",
        "high",
        "low",
        "totalValue",
        "transactions",
        "settlementPrice",
        "openInterest",
        "impliedVolatility",
        "contractSymbol",
        "optionType",
    ]

    data.columns = cols

    data["expiration"] = pd.to_datetime(data["expiration"], format="%Y-%m-%d")
    data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d")
    data["impliedVolatility"] = 0.01 * data["impliedVolatility"]

    date_ = data["date"]
    temp = pd.DatetimeIndex(data.expiration)
    temp_ = temp - date_  # type: ignore
    data["dte"] = [pd.Timedelta(_temp_).days for _temp_ in temp_]

    data = data.set_index(["expiration", "strike", "optionType"]).sort_index()
    data["date"] = data["date"].astype(str)
    underlying_price = data.iloc[-1]["lastPrice"]
    data["underlyingPrice"] = underlying_price
    data = data.reset_index()
    data = data[data["strike"] != 0]

    return data
