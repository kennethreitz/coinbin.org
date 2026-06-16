# ₿ Coinbin.org

### The Human–Friendly API Service for Crypto Currency Information.

This free web service exists to provide information on "coins". Supports all crypto–currencies.

### Example API Endpoints

`$ curl https://coinbin.org/lbc`

```json
{
  "coin": {
    "name": "LBRY Credits", 
    "rank": "100", 
    "ticker": "lbc", 
    "value": 0.429737, 
    "value.currency": "USD"
  }
}
```
      

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

### Price history & forecasts

`/history` and `/forecast` read from the `api_coin` table (see `schema.sql`).
Populate it on a schedule with the ingestion worker:

```console
$ DATABASE_URL=postgres://... uv run python ingest.py
```

Forecasting (`/forecast`) additionally needs the optional, heavyweight
`prophet` stack and `FORECASTS_ENABLED=1`:

```console
$ uv sync --extra forecast    # prophet, pandas, numpy, matplotlib, mpld3
```

## More Resources

- [Awesome Crypto Currency Tools & Algorithms (Guide)](https://github.com/kennethreitz/awesome-coins)
