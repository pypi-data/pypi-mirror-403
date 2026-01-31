"""Polymarket router (core extension) for OpenBB REST API."""

from openbb_core.app.model.command_context import CommandContext
from openbb_core.app.model.example import APIEx
from openbb_core.app.model.obbject import OBBject
from openbb_core.app.provider_interface import ExtraParams, ProviderChoices, StandardParams
from openbb_core.app.query import Query
from openbb_core.app.router import Router


# Note: core extensions are mounted under `/{entrypoint_name}` by OpenBB itself.
# Keep the top-level prefix empty to avoid `/polymarket/polymarket/...` paths.
router = Router(prefix="", description="Polymarket prediction market data.")


@router.command(
    model="PolymarketEvents",
    path="/events",
    examples=[
        APIEx(
            description="List active events across all tags (optionally filter by tag_id).",
            parameters={
                "limit": 20,
                "offset": 0,
                "active": True,
                "closed": False,
                "order": "volume24hr",
                "ascending": False,
            },
        ),
        APIEx(
            description="Fetch a single event by id (includes markets + token ids).",
            parameters={"event_id": "45883"},
        ),
    ],
)
async def events(
    cc: CommandContext,
    provider_choices: ProviderChoices,
    standard_params: StandardParams,
    extra_params: ExtraParams,
) -> OBBject:
    """List events (Gamma `GET /events`)."""
    return await OBBject.from_query(Query(**locals()))


@router.command(
    model="PolymarketEventMarkets",
    path="/markets",
    examples=[
        APIEx(
            description="List markets for an event id (returns token ids in each market).",
            parameters={"event_id": "45883"},
        ),
        APIEx(
            description="Fetch a single market by market id.",
            parameters={"market_id": 601697},
        ),
    ],
)
async def markets(
    cc: CommandContext,
    provider_choices: ProviderChoices,
    standard_params: StandardParams,
    extra_params: ExtraParams,
) -> OBBject:
    """List markets for an event (Gamma `GET /events?id=...` -> markets)."""
    return await OBBject.from_query(Query(**locals()))


@router.command(
    model="PolymarketClobOrderbook",
    path="/orderbook",
    examples=[
        APIEx(
            description="Orderbook snapshot for a token id (asset_id).",
            parameters={
                "token_id": "11862165566757345985240476164489718219056735011698825377388402888080786399275",
            },
        )
    ],
)
async def orderbook(
    cc: CommandContext,
    provider_choices: ProviderChoices,
    standard_params: StandardParams,
    extra_params: ExtraParams,
) -> OBBject:
    """Get CLOB orderbook for a token (official `GET /book?token_id=...`)."""
    return await OBBject.from_query(Query(**locals()))


@router.command(
    model="PolymarketClobPricesHistory",
    path="/prices_history",
    examples=[
        APIEx(
            description="Token price history using a relative interval.",
            parameters={
                "token_id": "11862165566757345985240476164489718219056735011698825377388402888080786399275",
                "interval": "1d",
                "fidelity": 60,
            },
        )
    ],
)
async def prices_history(
    cc: CommandContext,
    provider_choices: ProviderChoices,
    standard_params: StandardParams,
    extra_params: ExtraParams,
) -> OBBject:
    """Get token price history (official `GET /prices-history`)."""
    return await OBBject.from_query(Query(**locals()))
