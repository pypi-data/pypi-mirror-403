# OpenBB Polymarket Extension

This package adds Polymarket as an OpenBB provider + a small router that exposes
Polymarket endpoints via the OpenBB REST API.

## Install (editable)

```bash
pip install -e ./openbb_polymarket
```

## Run OpenBB API

```bash
uvicorn openbb_core.api.rest_api:app --host 0.0.0.0 --port 8000
```

Then open:
- `http://127.0.0.1:8000/docs`

You should see Polymarket endpoints under:
- `/api/v1/polymarket/events`
- `/api/v1/polymarket/markets`
- `/api/v1/polymarket/orderbook`
- `/api/v1/polymarket/prices_history`

Example:

```bash
curl -s 'http://127.0.0.1:8000/api/v1/polymarket/events?provider=polymarket&limit=5'
```

Event -> markets -> token -> orderbook + price history (official CLOB public API):

```bash
EVENT_ID='45883'

curl -s \"http://127.0.0.1:8000/api/v1/polymarket/markets?provider=polymarket&event_id=${EVENT_ID}\"

TOKEN_ID='11862165566757345985240476164489718219056735011698825377388402888080786399275'
curl -s \"http://127.0.0.1:8000/api/v1/polymarket/orderbook?provider=polymarket&token_id=${TOKEN_ID}\"
curl -s \"http://127.0.0.1:8000/api/v1/polymarket/prices_history?provider=polymarket&token_id=${TOKEN_ID}&interval=1d&fidelity=60\"
```

Fetch a single market by id:

```bash
curl -s 'http://127.0.0.1:8000/api/v1/polymarket/markets?provider=polymarket&market_id=601697'
```

## Proxy

HTTP(S) proxy works via standard environment variables (e.g. `http_proxy` / `https_proxy`).
