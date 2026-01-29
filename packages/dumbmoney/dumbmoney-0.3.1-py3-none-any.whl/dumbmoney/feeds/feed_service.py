from datetime import date, datetime
from typing import List, Sequence, Optional

from .feed import AdjustType, BaseFeed
from ..core import OHLCVData


def _normalize_date(d) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.fromisoformat(d).date()
    raise ValueError(f"Invalid date type: {type(d)}")


class DataFeedService:
    """Service to feed data using multiple providers (potentially)."""

    def __init__(self, feeds: Sequence[BaseFeed]) -> None:
        if not feeds:
            raise ValueError("At least one provider must be provided.")
        self.feeds = list(feeds)

    def get_ohlcv(
        self,
        symbol: str,
        start,
        end,
        adjust: AdjustType = "forward",
        fields: Optional[List[str]] = None,
    ) -> OHLCVData:
        start_date = _normalize_date(start)
        end_date = _normalize_date(end)

        errors: List[str] = []

        for feed in self.feeds:
            try:
                df = feed.get_ohlcv(
                    symbol=symbol,
                    start=start_date,
                    end=end_date,
                    adjust=adjust,
                    fields=fields,
                )
                return df
            except Exception as e:
                errors.append(f"Feed {feed.name} failed: {e}")

        raise RuntimeError(
            f"All feeds failed for symbol: {symbol} "
            f"({start_date} → {end_date}): {'; '.join(errors)}"
        )
