"""Polymarket fetchers (provider implementations)."""

from __future__ import annotations

from typing import Any

import httpx
from openbb_core.provider.abstract.fetcher import Fetcher

from openbb_polymarket.models import (
    PolymarketClobOrderbookQueryParams,
    PolymarketClobPricesHistoryQueryParams,
    PolymarketEventMarketsQueryParams,
    PolymarketEventsQueryParams,
    PolymarketMarketData,
    PolymarketOrderbookData,
    PolymarketPriceHistoryPoint,
    PolymarketCryptoMarketsQueryParams,
    PolymarketEventData,
)
from openbb_core.provider.abstract.annotated_result import AnnotatedResult


def _httpx_timeout(preferences: dict | None, default: float = 10.0) -> float:
    # OpenBB preferences uses `request_timeout` (seconds).
    if not preferences:
        return default
    try:
        v = preferences.get("request_timeout")
        return float(v) if v else default
    except Exception:
        return default


def _to_request_params(query: Any) -> dict[str, Any]:
    """Return request params using OpenBB QueryParams alias mapping if provided.

    We don't assume `QueryParams.model_dump()` will apply `__alias_dict__`, so we
    map it here to keep the provider self-contained and robust across versions.
    """
    params = query.model_dump(exclude_none=True)
    alias_dict = getattr(query, "__alias_dict__", None) or {}
    if not alias_dict:
        return params
    return {alias_dict.get(k, k): v for k, v in params.items()}


class PolymarketEventsFetcher(Fetcher[PolymarketEventsQueryParams, list[PolymarketEventData]]):
    """Fetch events from the Gamma public API (`GET /events`)."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PolymarketEventsQueryParams:
        return PolymarketEventsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: PolymarketEventsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        url = "https://gamma-api.polymarket.com/events"
        timeout = _httpx_timeout(kwargs.get("preferences"))
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, trust_env=True) as c:
            r = await c.get(url, params=_to_request_params(query))
            r.raise_for_status()
            # Gamma returns a list of events for this endpoint.
            return {"data": r.json()}

    @staticmethod
    def transform_data(
        query: PolymarketEventsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[PolymarketEventData]]:
        events_raw = data.get("data") or []
        events = [PolymarketEventData.model_validate(e) for e in events_raw]
        return AnnotatedResult(
            result=events,
            metadata={
                "source": "gamma_events",
                "tag_id": query.tag_id,
                "event_id": query.event_id,
            },
        )


class PolymarketEventMarketsFetcher(
    Fetcher[PolymarketEventMarketsQueryParams, list[PolymarketMarketData]]
):
    """Fetch markets by event id or a single market by id (Gamma)."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PolymarketEventMarketsQueryParams:
        return PolymarketEventMarketsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: PolymarketEventMarketsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        timeout = _httpx_timeout(kwargs.get("preferences"))
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, trust_env=True
        ) as c:
            if query.market_id is not None:
                r = await c.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={"id": query.market_id},
                )
                r.raise_for_status()
                return {"mode": "market", "data": r.json()}

            r = await c.get(
                "https://gamma-api.polymarket.com/events",
                params={"id": query.event_id},
            )
            r.raise_for_status()
            return {"mode": "event", "data": r.json()}

    @staticmethod
    def transform_data(
        query: PolymarketEventMarketsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[PolymarketMarketData]]:
        mode = data.get("mode")
        raw = data.get("data") or []

        if mode == "market":
            markets = [PolymarketMarketData.model_validate(m) for m in raw]
        else:
            ev = raw[0] if raw else {}
            markets_raw = ev.get("markets") or []
            markets = [PolymarketMarketData.model_validate(m) for m in markets_raw]

        return AnnotatedResult(
            result=markets,
            metadata={
                "source": "gamma_markets",
                "event_id": query.event_id,
                "market_id": query.market_id,
            },
        )


class PolymarketCryptoMarketsFetcher(
    Fetcher[PolymarketCryptoMarketsQueryParams, list[PolymarketEventData]]
):
    """Fetch crypto markets from polymarket.com `/api/crypto/markets`."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PolymarketCryptoMarketsQueryParams:
        return PolymarketCryptoMarketsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: PolymarketCryptoMarketsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        url = "https://polymarket.com/api/crypto/markets"
        timeout = _httpx_timeout(kwargs.get("preferences"))
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, trust_env=True) as c:
            r = await c.get(url, params=_to_request_params(query))
            r.raise_for_status()
            return r.json()

    @staticmethod
    def transform_data(
        query: PolymarketCryptoMarketsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[PolymarketEventData]]:
        events_raw = data.get("events") or []
        events = [PolymarketEventData.model_validate(e) for e in events_raw]
        return AnnotatedResult(
            result=events,
            metadata={
                "source": "polymarket_crypto_markets",
                "hasMore": data.get("hasMore"),
                "totalCount": data.get("totalCount"),
            },
        )


class PolymarketClobOrderbookFetcher(
    Fetcher[PolymarketClobOrderbookQueryParams, list[PolymarketOrderbookData]]
):
    """Fetch a token orderbook from the Polymarket CLOB public API."""

    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> PolymarketClobOrderbookQueryParams:
        return PolymarketClobOrderbookQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: PolymarketClobOrderbookQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        # Current public endpoint is `GET /book?token_id=...`.
        url = "https://clob.polymarket.com/book"
        timeout = _httpx_timeout(kwargs.get("preferences"))
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, trust_env=True
        ) as c:
            r = await c.get(url, params={"token_id": query.token_id})
            r.raise_for_status()
            return r.json()

    @staticmethod
    def transform_data(
        query: PolymarketClobOrderbookQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[PolymarketOrderbookData]]:
        ob = PolymarketOrderbookData.model_validate(data)
        # Normalize/echo token id for convenience when joining with Gamma markets.
        ob.asset_id = ob.asset_id or query.token_id
        return AnnotatedResult(
            result=[ob],
            metadata={
                "source": "clob_book",
                "token_id": query.token_id,
            },
        )


class PolymarketClobPricesHistoryFetcher(
    Fetcher[PolymarketClobPricesHistoryQueryParams, list[PolymarketPriceHistoryPoint]]
):
    """Fetch token historical prices from the Polymarket CLOB public API."""

    require_credentials = False

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> PolymarketClobPricesHistoryQueryParams:
        return PolymarketClobPricesHistoryQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: PolymarketClobPricesHistoryQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        url = "https://clob.polymarket.com/prices-history"
        timeout = _httpx_timeout(kwargs.get("preferences"))
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, trust_env=True
        ) as c:
            r = await c.get(url, params=_to_request_params(query))
            r.raise_for_status()
            return r.json()

    @staticmethod
    def transform_data(
        query: PolymarketClobPricesHistoryQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[PolymarketPriceHistoryPoint]]:
        history_raw = data.get("history") or []
        points = [PolymarketPriceHistoryPoint.model_validate(p) for p in history_raw]
        return AnnotatedResult(
            result=points,
            metadata={
                "source": "clob_prices_history",
                "token_id": query.token_id,
                "startTs": query.start_ts,
                "endTs": query.end_ts,
                "interval": query.interval,
                "fidelity": query.fidelity,
            },
        )
