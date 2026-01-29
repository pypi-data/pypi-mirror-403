from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from typing import Optional, List, Union, Literal

import pandas as pd

from tigeropen.common.consts import (
    Language,
    BarPeriod,
    QuoteRight,
)
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.quote.quote_client import QuoteClient

from .feed import AdjustType, BaseFeed, StockMarket
from ..core import OHLCVData, normalize_ohlcv
from ..logger import logger


@dataclass
class TigerConfig:
    private_key: str
    tiger_id: str
    account: str
    license: str
    secret_key: Optional[str] = None
    language: Language = Language.en_US
    timezone: str = "US/Eastern"


@lru_cache(maxsize=1, typed=True)
def get_tiger_client(
    private_key: str,
    tiger_id: str,
    account: str,
    license: str,
    secret_key: Optional[str] = None,
    language: Language = Language.en_US,
    timezone: str = "US/Eastern",
) -> QuoteClient:
    tiger_config = TigerOpenClientConfig()
    tiger_config.private_key = private_key
    tiger_config.tiger_id = tiger_id
    tiger_config.account = account
    tiger_config.license = license
    tiger_config.secret_key = secret_key
    tiger_config.language = language
    tiger_config.timezone = timezone
    return QuoteClient(tiger_config)


@dataclass
class TigerFeed(BaseFeed):
    """Data feed backed by Tiger Brokers."""

    config: Optional[TigerConfig] = field(default=None)

    name: str = "Tiger"

    tiger_client: QuoteClient = field(init=False)

    rename_map = {
        "time": "date",
    }

    adjust_map = {
        "none": QuoteRight.NR,
        "forward": None,
        "backward": QuoteRight.BR,
    }

    def __post_init__(self):
        if self.config is None:
            raise ValueError("TigerConfig must be provided for TigerFeed.")
        self.tiger_client = get_tiger_client(
            self.config.private_key,
            self.config.tiger_id,
            self.config.account,
            self.config.license,
            self.config.secret_key,
            self.config.language,
            self.config.timezone,
        )
        logger.debug("TigerFeed initialized.")

    @classmethod
    def markets(cls) -> Union[List[StockMarket], Literal["*"]]:
        return "*"

    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        adjust: AdjustType = "forward",
        fields: Optional[List[str]] = None,
    ) -> OHLCVData:
        code, _ = self.check_symbol(symbol)

        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        logger.debug(
            f"Tiger: fetching {symbol} from {start_str} to {end_str} with adjust={adjust}"
        )

        bars = self.tiger_client.get_bars(
            symbols=code,
            period=BarPeriod.DAY,
            begin_time=start_str,
            end_time=end_str,
            right=self.adjust_map[adjust],
        )

        df = bars.rename(columns=self.rename_map)
        df["date"] = pd.to_datetime(df["date"], unit="ms")

        if df["next_page_token"].notnull().any():
            logger.warning(
                f"Data for {symbol} from Tiger has more pages. Only the first page is fetched."
            )

        return normalize_ohlcv(pd.DataFrame(df), fields=fields)
