"""TMX ETF Sectors fetcher."""

from typing import Any, Dict, List, Optional

import pandas as pd
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.etf_sectors import (
    EtfSectorsData,
    EtfSectorsQueryParams,
)
from openbb_tmx.utils.helpers import get_all_etfs
from pydantic import Field
import warnings

_warn = warnings.warn


class TmxEtfSectorsQueryParams(EtfSectorsQueryParams):
    """TMX ETF Sectors Query Params"""


class TmxEtfSectorsData(EtfSectorsData):
    """TMX ETF Sectors Data."""

    __alias_dict__ = {
        "energy": "Energy",
        "materials": "Basic Materials",
        "industrials": "Industrials",
        "consumer_cyclical": "Consumer Cyclical",
        "consumer_defensive": "Consumer Defensive",
        "financial_services": "Financial Services",
        "technology": "Technology",
        "health_care": "Healthcare",
        "communication_services": "Communication Services",
        "utilities": "Utilities",
        "real_estate": "Real Estate",
    }

    other: Optional[float] = Field(
        description="Other Sector Weight.", alias="Other", default=None
    )


class TmxEtfSectorsFetcher(
    Fetcher[
        TmxEtfSectorsQueryParams,
        List[TmxEtfSectorsData],
    ]
):
    """Transform the query, extract and transform the data from the TMX endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> TmxEtfSectorsQueryParams:
        """Transform the query."""
        return TmxEtfSectorsQueryParams(**params)

    @staticmethod
    def extract_data(
        query: TmxEtfSectorsQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Return the raw data from the TMX endpoint."""

        symbols = (
            query.symbol.split(",") if "," in query.symbol else [query.symbol.upper()]
        )
        target = pd.DataFrame()
        _data = pd.DataFrame(get_all_etfs())
        symbol = symbols[0]
        if len(symbols) > 1:
            _warn(
                "Multiple symbols provided, but are not allowed, using the first one: "
                + symbol
            )
        if ".TO" in symbol:
            symbol = symbol.replace(".TO", "")  # noqa
        _target = _data[_data["symbol"] == symbol]["sectors"]
        if len(_target) > 0:
            target = pd.DataFrame.from_records(_target.iloc[0]).rename(
                columns={"name": "sector", "percent": "weight"}
            )
        return target.to_dict(orient="records")

    @staticmethod
    def transform_data(data: List[Dict], **kwargs: Any) -> List[TmxEtfSectorsData]:
        """Return the transformed data."""
        return [TmxEtfSectorsData.model_validate(d) for d in data]
