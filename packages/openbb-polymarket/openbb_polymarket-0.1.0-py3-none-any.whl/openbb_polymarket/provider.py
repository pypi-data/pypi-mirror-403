"""Polymarket provider entrypoint for OpenBB."""

from __future__ import annotations

from openbb_core.provider.abstract.provider import Provider

from openbb_polymarket.fetchers import (
    PolymarketClobOrderbookFetcher,
    PolymarketClobPricesHistoryFetcher,
    PolymarketCryptoMarketsFetcher,
    PolymarketEventMarketsFetcher,
    PolymarketEventsFetcher,
)


polymarket_provider = Provider(
    name="polymarket",
    website="https://polymarket.com",
    description="Polymarket prediction market data (public Gamma + CLOB/website surfaces).",
    credentials=None,  # Public endpoints; no API key required.
    fetcher_dict={
        # New preferred models (single events endpoint + event->markets).
        "PolymarketEvents": PolymarketEventsFetcher,
        "PolymarketEventMarkets": PolymarketEventMarketsFetcher,

        # Backwards-compatible alias for older router path naming.
        "PolymarketFinanceEvents": PolymarketEventsFetcher,
        "PolymarketCryptoMarkets": PolymarketCryptoMarketsFetcher,
        "PolymarketClobOrderbook": PolymarketClobOrderbookFetcher,
        "PolymarketClobPricesHistory": PolymarketClobPricesHistoryFetcher,
    },
    repr_name="Polymarket",
)
