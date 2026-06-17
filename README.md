# ₿ Coinbin.org

### The Human–Friendly API Service for Crypto Currency Information.

This free web service exists to provide information on "coins". Supports all crypto–currencies.

### Example API Endpoints

`$ curl https://coinbin.org/lbc`

```json
{
  "coin": {
    "name": "LBRY Credits",
    "ticker": "lbc",
    "rank": 100,
    "usd": 0.429737,
    "btc": 0.00000717,
    "market_cap": 28000000,
    "volume_24h": 150000,
    "change_24h": -2.31,
    "circulating_supply": 650000000,
    "total_supply": 1000000000,
    "ath": 1.07,
    "last_updated": "2026-06-16T20:00:00Z"
  }
}
```

The `/<coin>` endpoint now also returns market cap, 24h volume, 24h change,
supply, and all-time high — data the upstream API already provides. Exchange
rates are computed via USD (crypto is USD/stablecoin-quoted now) rather than
routed through BTC.

#### Quote currencies (`?vs=`)

Price and value endpoints accept an optional `?vs=<currency>` (e.g. `eur`,
`gbp`, `jpy`, `btc`) to add a non-USD quote. The `usd` fields are always
present and unchanged, so existing clients are unaffected:

```console
$ curl "https://coinbin.org/eth?vs=eur"
{ "coin": { "usd": 3000.0, "vs": "eur", "vs_price": 2700.0, ... } }

$ curl "https://coinbin.org/eth/2?vs=eur"
{ "coin": { "usd": 6000.0, "vs": "eur", "vs_exchange_rate": 2700.0, "vs_value": 5400.0 } }
```

Unsupported currencies return `400`.
      

`$ curl https://coinbin.org/lbc/42.01`

```json
{
  "coin": {
    "exchange_rate": 0.429737, 
    "value": 18.053251369999998, 
    "value.currency": "USD"
  }
}
```
      

`$ curl https://coinbin.org/lbc/to/sc`

```
{
  "coin": {
    "exchange_rate": 61.98696034733942
  }
}
```
      

`$ curl https://coinbin.org/lbc/42.01/to/sc`

```json
{
  "coin": {
    "exchange_rate": 61.98696034733942, 
    "value": 2604.072204191729, 
    "value.coin": "sc"
  }
}
```

`$ curl https://coinbin.org/lbc/history`

```json
{
  "history": [
    {
      "timestamp": "2017-08-24T04:00:55.932092Z",
      "value": 0.3404,
      "value.currency": "USD",
      "when": "today"
    }, ...

... {
      "timestamp": "2016-07-12T04:01:09.167162Z",
      "value": 0.239634,
      "value.currency": "USD",
      "when": "Jul 12 2016"
    }
  ]
}
```

## Running it

Dependencies are managed with [uv](https://docs.astral.sh/uv/):

```console
$ uv sync
$ uv run gunicorn server:app -k gthread --threads 4
```

Live price data comes from a JSON price API (CoinGecko by default — no key
required). The app boots and serves the live price/conversion endpoints with no
further configuration.

### Deploying (Docker / Dokploy)

The included `Dockerfile` builds a uv-based image and serves with gunicorn on
`$PORT` (default `8000`):

```console
$ docker build -t coinbin .
$ docker run -p 8000:8000 coinbin
```

On [Dokploy](https://dokploy.com/), create an **Application**, point it at this
repo with build type **Dockerfile**, set the container port to `8000`, and add
any of the variables below as environment variables.

### Configuration

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres for `/history` (optional; empty history is returned if unset). |
| `COINGECKO_DEMO_API_KEY` | CoinGecko Demo (free) key — recommended; keyless access is rate-limited and often blocked from datacenter IPs. |
| `COINGECKO_API_KEY` | CoinGecko Pro key (auto-targets `pro-api.coingecko.com`). |
| `COINGECKO_API_BASE` | Override the API base URL (e.g. a proxy). |
| `COINGECKO_PAGES` | Number of 250-coin pages to fetch (default `4`). |
| `API_KEYS` | Colon-separated keys for the "pro" history database. |
| `FORECASTS_ENABLED` | Set to `1` to enable the (heavy) `/forecast` endpoints. |
| `SENTRY_DSN` | Optional error reporting. |
| `DEBUG` | Disable forced HTTPS for local development. |

### Price history & the ingestion cron

`/history` and `/forecast` read from the `api_coin` table (see `schema.sql`),
which is populated by `ingest.py`. Run it locally with:

```console
$ DATABASE_URL=postgres://... uv run python ingest.py
```

On Dokploy, add a **Schedule** to the application (Schedules tab) so it runs
inside the app container:

- **Schedule (cron):** `*/10 * * * *`  (every 10 minutes)
- **Command:** `python ingest.py`
- **Service:** the coinbin app service

`ingest.py` creates the table from `schema.sql` on first run and reuses the
app's `DATABASE_URL` (and `INGEST_PRO_URL` / `HEROKU_POSTGRESQL_TEAL_URL` if
you mirror into a "pro" database).

### Forecasts

`/forecast` additionally needs the optional, heavyweight `prophet` stack and
`FORECASTS_ENABLED=1`. Build the image with the extra included:

```console
$ docker build --build-arg INSTALL_FORECAST=true -t coinbin .
```

(or locally: `uv sync --extra forecast`). Then set `FORECASTS_ENABLED=1`.
Forecasts also require the `api_coin` table to already contain history.

> **Note:** prophet's `cmdstanpy` backend needs a compiled CmdStan and a C++
> toolchain, which the slim base image does not include. Enabling forecasts in
> Docker therefore also requires adding `build-essential` and running
> `python -m cmdstanpy.install_cmdstan` in the image. This is why forecasting
> is opt-in.

## More Resources

- [Awesome Crypto Currency Tools & Algorithms (Guide)](https://github.com/kennethreitz/awesome-coins)
