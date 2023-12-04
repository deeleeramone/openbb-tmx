"""TMX Options Chains Model."""

from datetime import (
    datetime,
    date as dateType,
)
from typing import Any, Dict, List, Optional

from openbb_tmx.utils.helpers import download_eod_chains, get_current_options
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.options_chains import (
    OptionsChainsData,
    OptionsChainsQueryParams,
)
from openbb_core.provider.utils.descriptions import (
    QUERY_DESCRIPTIONS,
    DATA_DESCRIPTIONS,
)
from pydantic import Field, field_validator


class TmxOptionsChainsQueryParams(OptionsChainsQueryParams):
    """TMX Options Chains Query.

    Source: https://www.Tmx.com/
    """

    date: Optional[dateType] = Field(
        description=QUERY_DESCRIPTIONS.get("date", ""),
        default=None,
    )


class TmxOptionsChainsData(OptionsChainsData):
    """TMX Options Chains Data."""

    __alias_dict__ = {
        "eod_date": "date",
        "option_type": "optionType",
        "close": "lastPrice",
        "open_interest": "openInterest",
        "implied_volatility": "impliedVolatility",
        "close_bid": "bid",
        "bid_size": "bidSize",
        "close_ask": "ask",
        "ask_size": "askSize",
        "settlement_price": "settlementPrice",
        "total_value": "totalValue",
        "prev_close": "previousClose",
        "contract_symbol": "contractSymbol",
    }

    bid_size: Optional[int] = Field(description="Lot size for the bid.", default=None)
    ask_size: Optional[int] = Field(description="Lot size for the ask.", default=None)
    transactions: Optional[int] = Field(
        description="Number of transactions for the contract.", default=None
    )
    total_value: Optional[float] = Field(
        description="Total value of the transactions.", default=None
    )
    settlement_price: Optional[float] = Field(
        description="Settlement price on that date.", default=None
    )
    change: Optional[float] = Field(description="Change in price of the option.")
    prev_close: Optional[float] = Field(
        description=DATA_DESCRIPTIONS.get("prev_close", ""), default=None
    )
    underlying_price: Optional[float] = Field(
        description="Price of the underlying stock on that date.", default=None
    )
    dte: Optional[int] = Field(
        description="Days to expiration for the option.", default=None
    )

    @field_validator("expiration", mode="before", check_fields=False)
    @classmethod
    def date_validate(cls, v):  # pylint: disable=E0213
        """Return the datetime object from the date string"""
        return datetime.strptime(v, "%Y-%m-%d")


class TmxOptionsChainsFetcher(
    Fetcher[
        TmxOptionsChainsQueryParams,
        List[TmxOptionsChainsData],
    ]
):
    """Transform the query, extract and transform the data from the TMX endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> TmxOptionsChainsQueryParams:
        """Transform the query."""
        return TmxOptionsChainsQueryParams(**params)

    @staticmethod
    def extract_data(
        query: TmxOptionsChainsQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Return the data."""
        results = []
        if query.date is not None:
            chains = download_eod_chains(symbol=query.symbol, date=query.date)  # type: ignore
        else:
            chains = get_current_options(query.symbol)

        if not chains.empty:
            results = chains.to_dict(orient="records")

        return results

    @staticmethod
    def transform_data(
        query: TmxOptionsChainsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> List[TmxOptionsChainsData]:
        """Transform the data and validate the model."""
        return [TmxOptionsChainsData.model_validate(d) for d in data]
