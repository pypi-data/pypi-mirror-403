from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

import pandas as pd

from market_data.providers.base import BaseProvider
from market_data.normalize.symbols import normalize_symbol
from market_data.types import Bar, iter_month_starts, parse_ts

logger = logging.getLogger("market_data.providers.polygon")


@dataclass(frozen=True, slots=True)
class PolygonConfig:
    api_key: Optional[str] = None
    base_url: str = "https://api.polygon.io"
    # Retry configuration for rate limiting
    max_retries: int = 5
    backoff_factor: float = 2.0  # Exponential backoff: 2, 4, 8, 16, 32 seconds


class PolygonProvider(BaseProvider):
    """
    Polygon provider using `polygon-api-client`.

    Notes:
    - No env var lookups (caller passes `PolygonConfig(api_key=...)`).
    - No network calls at import-time.
    - Handles rate limiting (429) with exponential backoff.
    """

    def __init__(self, config: PolygonConfig):
        if not config.api_key:
            raise ValueError("PolygonConfig.api_key is required")
        self._config = config

        # Lazy-ish: constructing the client is cheap; calls happen only in fetch methods.
        from polygon import RESTClient

        self._client = RESTClient(api_key=config.api_key, base=config.base_url)

        # Configure retry strategy for rate limiting
        self._configure_retry()

    def _configure_retry(self) -> None:
        """Configure urllib3 retry strategy for rate limiting."""
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            retry_strategy = Retry(
                total=self._config.max_retries,
                backoff_factor=self._config.backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],  # Only retry GET requests
                raise_on_status=False,  # Don't raise immediately, let us handle it
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)

            # The polygon client uses a requests session internally
            if hasattr(self._client, "_session"):
                self._client._session.mount("https://", adapter)
                self._client._session.mount("http://", adapter)
                logger.debug(
                    f"Configured retry strategy: max_retries={self._config.max_retries}, "
                    f"backoff_factor={self._config.backoff_factor}"
                )
            else:
                logger.warning("Could not configure retry strategy: polygon client has no _session attribute")
        except Exception as e:
            logger.warning(f"Failed to configure retry strategy: {e}")

    def fetch_1m_bars(self, symbol: str, *, start: pd.Timestamp, end: pd.Timestamp) -> Iterable[Bar]:
        sym = normalize_symbol(symbol)
        start_ts = parse_ts(start)
        end_ts = parse_ts(end)
        if end_ts <= start_ts:
            return []

        logger.debug(f"Fetching {sym} bars from {start_ts} to {end_ts}")

        out: list[Bar] = []
        # Fetch in month-sized chunks to avoid large-range truncation and reduce requests.
        for month_start in iter_month_starts(start_ts, end_ts):
            if month_start >= end_ts:
                break
            month_end = (month_start + pd.offsets.MonthBegin(1)).normalize()
            if month_end > end_ts:
                month_end = end_ts

            # Polygon aggregates are day-based; request full days for the month chunk
            # then filter to [start,end).
            try:
                aggs = self._client.get_aggs(
                    ticker=sym,
                    multiplier=1,
                    timespan="minute",
                    from_=month_start.strftime("%Y-%m-%d"),
                    to=month_end.strftime("%Y-%m-%d"),
                    limit=50000,
                )
            except Exception as e:
                # Check if this is a rate limit error that exhausted retries
                error_str = str(e).lower()
                if "429" in error_str or "rate" in error_str or "too many" in error_str:
                    logger.error(
                        f"Rate limit exceeded for {sym} ({month_start.strftime('%Y-%m-%d')} to "
                        f"{month_end.strftime('%Y-%m-%d')}) after {self._config.max_retries} retries: {e}"
                    )
                    raise RuntimeError(
                        f"Polygon rate limit exceeded for {sym} after {self._config.max_retries} retries. "
                        f"Try again later or reduce request frequency."
                    ) from e
                else:
                    logger.error(f"Failed to fetch {sym} bars: {e}")
                    raise

            for bar in aggs or []:
                # Polygon timestamps are epoch milliseconds (UTC).
                ts = pd.Timestamp(bar.timestamp, unit="ms", tz="UTC")
                if ts < start_ts or ts >= end_ts:
                    continue
                out.append(
                    Bar(
                        symbol=sym,
                        ts=ts,
                        open=float(bar.open),
                        high=float(bar.high),
                        low=float(bar.low),
                        close=float(bar.close),
                        volume=int(bar.volume),
                    )
                )

        logger.debug(f"Fetched {len(out)} bars for {sym}")
        # Deterministic order.
        out.sort(key=lambda b: (b.symbol, b.ts))
        return out

