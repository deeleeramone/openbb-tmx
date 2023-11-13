"""TMX Equity Search fetcher."""

from typing import Any, Dict, List, Optional

import pandas as pd
from openbb_provider.abstract.fetcher import Fetcher
from openbb_provider.standard_models.equity_search import (
    EquitySearchData,
    EquitySearchQueryParams,
)
from openbb_tmx.utils.helpers import get_all_tmx_companies

from pydantic import Field


class TmxEquitySearchQueryParams(EquitySearchQueryParams):
    """TMX Equity Search query.

    Source: https://www.tmx.com/
    """

    use_cache: bool = Field(
        default=True,
        description="Whether to use a cached request. The list of companies is cached for two days.",
    )


class TmxEquitySearchData(EquitySearchData):
    """TMX Equity Search Data."""


class TmxEquitySearchFetcher(
    Fetcher[
        TmxEquitySearchQueryParams,
        List[TmxEquitySearchData],
    ]
):
    """Transform the query, extract and transform the data from the TMX endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> TmxEquitySearchQueryParams:
        """Transform the query."""
        return TmxEquitySearchQueryParams(**params)

    @staticmethod
    def extract_data(
        query: TmxEquitySearchQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Return the raw data from the TMX endpoint."""

        companies = get_all_tmx_companies(use_cache=query.use_cache)
        results = pd.DataFrame(
            index=companies, data=companies.values(), columns=["name"]
        )
        results = results.reset_index().rename(columns={"index": "symbol"})

        if query:
            results = results[
                results["name"].str.contains(query.query, case=False)
                | results["symbol"].str.contains(query.query, case=False)
            ]

        return results.reset_index(drop=True).astype(str).to_dict("records")

    @staticmethod
    def transform_data(data: List[Dict], **kwargs: Any) -> List[TmxEquitySearchData]:
        """Transform the data to the standard format."""
        return [TmxEquitySearchData.model_validate(d) for d in data]
