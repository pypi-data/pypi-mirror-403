"""Polymarket models (QueryParams + Data) used by the provider.

We keep these models independent of any gateway code so the package can be
installed into any OpenBB Platform environment.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field, field_validator, model_validator


def _parse_json_list(value: Any) -> list[Any] | None:
    """Parse a list that may be a JSON-encoded string or already a list."""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            parsed = json.loads(s)
        except Exception:
            return None
        return parsed if isinstance(parsed, list) else None
    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return float(s)
        except Exception:
            return None
    return None


class PolymarketOutcomeToken(Data):
    """Outcome-level token mapping (token_id <-> outcome <-> current probability/price)."""

    outcome: str
    token_id: str
    price: float | None = None


class PolymarketMarketData(Data):
    """A single Polymarket market under an event."""

    id: str | None = None
    question: str | None = None
    slug: str | None = None

    condition_id: str | None = Field(default=None, alias="conditionId")
    question_id: str | None = Field(default=None, alias="questionID")

    start_date: datetime | None = Field(default=None, alias="startDate")
    end_date: datetime | None = Field(default=None, alias="endDate")

    active: bool | None = None
    closed: bool | None = None
    archived: bool | None = None
    restricted: bool | None = None

    liquidity: float | None = None
    volume: float | None = None
    volume_24hr: float | None = Field(default=None, alias="volume24hr")
    liquidity_clob: float | None = Field(default=None, alias="liquidityClob")
    volume_24hr_clob: float | None = Field(default=None, alias="volume24hrClob")

    enable_order_book: bool | None = Field(default=None, alias="enableOrderBook")
    accepting_orders: bool | None = Field(default=None, alias="acceptingOrders")

    spread: float | None = None
    best_bid: float | None = Field(default=None, alias="bestBid")
    best_ask: float | None = Field(default=None, alias="bestAsk")
    last_trade_price: float | None = Field(default=None, alias="lastTradePrice")
    one_hour_price_change: float | None = Field(default=None, alias="oneHourPriceChange")
    one_day_price_change: float | None = Field(default=None, alias="oneDayPriceChange")
    one_week_price_change: float | None = Field(default=None, alias="oneWeekPriceChange")

    order_min_size: float | None = Field(default=None, alias="orderMinSize")
    order_price_min_tick_size: float | None = Field(
        default=None, alias="orderPriceMinTickSize"
    )

    outcomes: list[str] | None = None
    outcome_prices: list[float] | None = Field(default=None, alias="outcomePrices")
    clob_token_ids: list[str] | None = Field(default=None, alias="clobTokenIds")

    tokens: list[PolymarketOutcomeToken] = Field(default_factory=list)

    @field_validator(
        "liquidity",
        "volume",
        "volume_24hr",
        "liquidity_clob",
        "volume_24hr_clob",
        "spread",
        "best_bid",
        "best_ask",
        "last_trade_price",
        "one_hour_price_change",
        "one_day_price_change",
        "one_week_price_change",
        "order_min_size",
        "order_price_min_tick_size",
        mode="before",
    )
    @classmethod
    def _coerce_float(cls, v: Any) -> Any:
        return _to_float(v) if isinstance(v, str) else v

    @field_validator("outcomes", mode="before")
    @classmethod
    def _parse_outcomes(cls, v: Any) -> Any:
        parsed = _parse_json_list(v)
        return parsed if parsed is not None else v

    @field_validator("outcome_prices", mode="before")
    @classmethod
    def _parse_outcome_prices(cls, v: Any) -> Any:
        parsed = _parse_json_list(v)
        if parsed is None:
            return v
        out: list[float] = []
        for item in parsed:
            f = _to_float(item)
            if f is not None:
                out.append(f)
        return out

    @field_validator("clob_token_ids", mode="before")
    @classmethod
    def _parse_token_ids(cls, v: Any) -> Any:
        parsed = _parse_json_list(v)
        if parsed is None:
            return v
        return [str(x) for x in parsed]

    @model_validator(mode="after")
    def _build_tokens(self) -> "PolymarketMarketData":
        if self.tokens:
            return self
        if not self.outcomes or not self.clob_token_ids:
            return self
        prices = self.outcome_prices or []
        built: list[PolymarketOutcomeToken] = []
        for i, outcome in enumerate(self.outcomes):
            token_id = self.clob_token_ids[i] if i < len(self.clob_token_ids) else ""
            if not token_id:
                continue
            price = prices[i] if i < len(prices) else None
            built.append(PolymarketOutcomeToken(outcome=outcome, token_id=token_id, price=price))
        self.tokens = built
        return self


class PolymarketEventData(Data):
    """Event-level object returned by Polymarket surfaces (Gamma + polymarket.com)."""

    id: str
    ticker: str | None = None
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    resolution_source: str | None = Field(default=None, alias="resolutionSource")

    start_date: datetime | None = Field(default=None, alias="startDate")
    end_date: datetime | None = Field(default=None, alias="endDate")
    creation_date: datetime | None = Field(default=None, alias="creationDate")

    active: bool | None = None
    closed: bool | None = None
    archived: bool | None = None
    restricted: bool | None = None
    featured: bool | None = None
    new: bool | None = None

    liquidity: float | None = None
    volume: float | None = None
    open_interest: float | None = Field(default=None, alias="openInterest")
    competitive: float | None = None
    volume_24hr: float | None = Field(default=None, alias="volume24hr")
    volume_1wk: float | None = Field(default=None, alias="volume1wk")
    volume_1mo: float | None = Field(default=None, alias="volume1mo")
    volume_1yr: float | None = Field(default=None, alias="volume1yr")
    enable_order_book: bool | None = Field(default=None, alias="enableOrderBook")
    liquidity_clob: float | None = Field(default=None, alias="liquidityClob")
    comment_count: int | None = Field(default=None, alias="commentCount")

    markets: list[PolymarketMarketData] = Field(default_factory=list)

    @field_validator(
        "liquidity",
        "volume",
        "open_interest",
        "competitive",
        "volume_24hr",
        "volume_1wk",
        "volume_1mo",
        "volume_1yr",
        "liquidity_clob",
        mode="before",
    )
    @classmethod
    def _coerce_float(cls, v: Any) -> Any:
        return _to_float(v) if isinstance(v, str) else v


class PolymarketEventsQueryParams(QueryParams):
    """Query parameters for Gamma `GET /events`."""

    __alias_dict__ = {"event_id": "id"}

    event_id: str | None = Field(
        default=None, description="Event id (filters to a specific event)."
    )
    tag_id: int | None = Field(
        default=None, description="Optional tag id filter (e.g. 120 for finance)."
    )
    limit: int = Field(default=20, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    archived: bool = False
    order: str = Field(default="volume24hr", description="Order field (Gamma).")
    ascending: bool = False
    active: bool = True
    closed: bool = False


class PolymarketEventMarketsQueryParams(QueryParams):
    """Query parameters for fetching markets.

    - event_id: resolve via `GET /events?id=...` and return its embedded markets.
    - market_id: resolve directly via `GET /markets?id=...`.
    """

    event_id: str | None = Field(default=None, description="Event id.")
    market_id: int | None = Field(default=None, description="Market id.")

    @model_validator(mode="after")
    def _require_selector(self) -> "PolymarketEventMarketsQueryParams":
        if not self.event_id and self.market_id is None:
            raise ValueError("Provide either event_id or market_id.")
        return self


class PolymarketCryptoMarketsQueryParams(QueryParams):
    """Query parameters for polymarket.com `api/crypto/markets` feed."""

    __alias_dict__ = {
        "category": "_c",
        "sort": "_s",
        "status": "_sts",
        "limit": "_l",
        "offset": "_offset",
    }

    category: Literal["crypto"] = "crypto"
    sort: str = Field(default="volume_24hr", description="Sort field.")
    status: str = Field(default="active", description="Status filter.")
    limit: int = Field(default=20, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class PolymarketClobOrderbookQueryParams(QueryParams):
    """Query parameters for Polymarket CLOB `GET /orderbook/{tokenID}`."""

    token_id: str = Field(description="CLOB token id (asset_id).")


class PolymarketClobPricesHistoryQueryParams(QueryParams):
    """Query parameters for Polymarket CLOB `GET /prices-history`."""

    __alias_dict__ = {
        "token_id": "market",
        "start_ts": "startTs",
        "end_ts": "endTs",
    }

    token_id: str = Field(description="CLOB token id (asset_id).")
    start_ts: int | None = Field(default=None, ge=0, description="Unix timestamp (UTC).")
    end_ts: int | None = Field(default=None, ge=0, description="Unix timestamp (UTC).")
    interval: Literal["1m", "1h", "6h", "1d", "1w", "max"] | None = Field(
        default=None,
        description="Duration ending now (mutually exclusive with start_ts/end_ts).",
    )
    fidelity: int | None = Field(
        default=None, ge=1, description="Resolution of the data, in minutes."
    )


class PolymarketOrderSummary(Data):
    """Aggregated orderbook level."""

    price: float
    size: float

    @field_validator("price", "size", mode="before")
    @classmethod
    def _coerce_float(cls, v: Any) -> Any:
        return _to_float(v) if isinstance(v, str) else v


class PolymarketOrderbookData(Data):
    """CLOB orderbook snapshot."""

    market: str | None = None
    asset_id: str | None = Field(default=None, alias="asset_id")
    timestamp: datetime | None = None
    bids: list[PolymarketOrderSummary] = Field(default_factory=list)
    asks: list[PolymarketOrderSummary] = Field(default_factory=list)
    min_order_size: float | None = None
    tick_size: float | None = None
    neg_risk: bool | None = None
    hash: str | None = None
    last_trade_price: float | None = None

    @field_validator("min_order_size", "tick_size", mode="before")
    @classmethod
    def _coerce_float_fields(cls, v: Any) -> Any:
        return _to_float(v) if isinstance(v, str) else v

    @field_validator("last_trade_price", mode="before")
    @classmethod
    def _coerce_ltp(cls, v: Any) -> Any:
        return _to_float(v) if isinstance(v, str) else v

    @field_validator("timestamp", mode="before")
    @classmethod
    def _parse_timestamp(cls, v: Any) -> Any:
        # CLOB `/book` uses epoch milliseconds (as str/int). Convert to UTC datetime.
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, (int, float)):
            ts = int(v)
        elif isinstance(v, str) and v.strip().isdigit():
            ts = int(v.strip())
        else:
            return v

        # Heuristic: >= 1e12 is ms, else seconds.
        seconds = ts / 1000.0 if ts >= 1_000_000_000_000 else float(ts)
        return datetime.fromtimestamp(seconds, tz=timezone.utc)


class PolymarketPriceHistoryPoint(Data):
    """A single (timestamp, price) point from the CLOB time series."""

    t: int
    p: float

    @field_validator("p", mode="before")
    @classmethod
    def _coerce_price(cls, v: Any) -> Any:
        return _to_float(v) if isinstance(v, str) else v
