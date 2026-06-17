import os
import decimal

from flask import Flask, jsonify, render_template, request, Response
from flask.json.provider import DefaultJSONProvider
from flask_caching import Cache
from flask_sslify import SSLify

import scraper
from scraper import get_coins, get_coin, Coin, convert_to_decimal
from predictions import get_predictions
from graph import schema


API_KEYS = os.environ.get('API_KEYS', '').split(':')


class CoinJSONProvider(DefaultJSONProvider):
    """Flask 3's JSON provider can't serialize Decimal; coerce to float."""

    @staticmethod
    def default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return DefaultJSONProvider.default(obj)


app = Flask(__name__)
app.json = CoinJSONProvider(app)
app.debug = 'DEBUG' in os.environ

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 60})

# Only force HTTPS in production; SSLify would break plain-HTTP local dev.
if not app.debug:
    sslify = SSLify(app)

# Optional error reporting.
if os.environ.get('SENTRY_DSN'):
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], integrations=[FlaskIntegration()])
    except ImportError:
        pass


# Lazily-opened price-history databases. These are optional: the live price
# endpoints work without them; only /history needs them.
_dbs = {}


def _get_db(env_var=None):
    """Return a records.Database for the given env var, or None if unavailable."""
    key = env_var or 'DATABASE_URL'
    if key in _dbs:
        return _dbs[key]

    url = os.environ.get(env_var) if env_var else os.environ.get('DATABASE_URL')
    if env_var and not url:
        _dbs[key] = None
        return None

    try:
        import records
        _dbs[key] = records.Database(url) if url else records.Database()
    except Exception:
        _dbs[key] = None
    return _dbs[key]


def _augment_vs(payload, coin, n=None):
    """Optionally add a non-USD quote (?vs=eur) to a coin payload.

    Additive: the existing USD fields are always present and unchanged. Returns
    an error response tuple if the requested currency is unsupported, else None.
    """
    vs = (request.args.get('vs') or '').lower()
    if not vs or vs == 'usd':
        return None

    supported = scraper.supported_vs_currencies()
    if supported and vs not in supported:
        return jsonify(error='Unsupported vs currency: {!r}'.format(vs)), 400

    price = scraper.price_in(coin, vs)
    if price is None:
        return None

    payload['vs'] = vs
    if n is None:
        payload['vs_price'] = convert_to_decimal(price)
    else:
        payload['vs_exchange_rate'] = convert_to_decimal(price)
        payload['vs_value'] = convert_to_decimal(price * n)
    return None


# ---------------------------------------------------------------------------
# Response formatting: JSON (default), plain text, or CSV.
#
# coinbin's value is ergonomics, so make the same data trivially usable from a
# shell (`curl coinbin.org/btc?format=text` -> a bare number) and from
# spreadsheets (`=IMPORTDATA("coinbin.org/coins?format=csv")`). JSON stays the
# default so existing clients are unaffected.
# ---------------------------------------------------------------------------

def _num(x):
    """Render a number as a clean plain string (no trailing zeros / 60000.0)."""
    if x is None:
        return ''
    d = x if isinstance(x, decimal.Decimal) else decimal.Decimal(str(x))
    if d == 0:
        return '0'
    return format(d.normalize(), 'f')


def _requested_format(default='json'):
    fmt = (request.args.get('format') or '').lower()
    if fmt in ('json', 'csv'):
        return fmt
    if fmt in ('text', 'txt', 'plain'):
        return 'text'
    accept = request.headers.get('Accept', '')
    if 'text/csv' in accept:
        return 'csv'
    if 'text/plain' in accept and 'application/json' not in accept and '*/*' not in accept:
        return 'text'
    return default


def _csv(rows):
    import io
    import csv as csvmod
    rows = list(rows)
    fieldnames = list(rows[0].keys()) if rows else []
    buf = io.StringIO()
    writer = csvmod.DictWriter(buf, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for r in rows:
        writer.writerow({
            k: '' if r.get(k) is None else (
                float(r[k]) if isinstance(r[k], decimal.Decimal) else r[k]
            )
            for k in fieldnames
        })
    return buf.getvalue()


def respond(key, payload, scalar=None, rows=None):
    """Return payload as JSON (default), plain-text scalar, or CSV."""
    fmt = _requested_format()
    if fmt == 'text' and scalar is not None:
        return Response(_num(scalar) + '\n', mimetype='text/plain')
    if fmt == 'csv' or (fmt == 'text' and scalar is None):
        data_rows = rows if rows is not None else [payload]
        return Response(_csv(data_rows), mimetype='text/csv')
    return jsonify(**{key: payload})


def _xml_escape(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def _human_price(x):
    if x is None:
        return 'n/a'
    f = float(x)
    if f >= 1000:
        return '{:,.0f}'.format(f)
    if f >= 1:
        return '{:,.2f}'.format(f)
    return _num(x)


def _render_badge(label, value, color):
    """A shields.io-style flat SVG badge (no dependencies)."""
    def width(s):
        return int(len(s) * 6.5) + 12
    lw, vw = width(label), width(value)
    total = lw + vw
    label_e, value_e = _xml_escape(label), _xml_escape(value)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" '
        'role="img" aria-label="{label}: {value}">'
        '<linearGradient id="s" x2="0" y2="100%">'
        '<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        '<stop offset="1" stop-opacity=".1"/></linearGradient>'
        '<rect rx="3" width="{total}" height="20" fill="#555"/>'
        '<rect rx="3" x="{lw}" width="{vw}" height="20" fill="{color}"/>'
        '<rect rx="3" width="{total}" height="20" fill="url(#s)"/>'
        '<g fill="#fff" text-anchor="middle" '
        'font-family="Verdana,DejaVu Sans,Geneva,sans-serif" font-size="11">'
        '<text x="{lx}" y="14">{label}</text>'
        '<text x="{vx}" y="14">{value}</text></g></svg>'
    ).format(total=total, lw=lw, vw=vw, color=color, label=label_e, value=value_e,
             lx=lw // 2, vx=lw + vw // 2)


@app.route('/')
@cache.cached(timeout=60)
def hello():
    lbc = get_coin('lbc')
    lbc_42 = get_value_int('lbc', 42.01)
    lbc_sc = get_exchange('lbc', 'sc')
    lbc_42_sc = get_exchange_value('lbc', 'sc', 42.01)
    lbc_forecast = get_forecast('lbc')

    return render_template(
        'index.html',
        lbc=lbc, lbc_42=lbc_42, lbc_sc=lbc_sc, lbc_42_sc=lbc_42_sc,
        coins=get_coins().values(), lbc_forecast=lbc_forecast,
    )


@app.route('/coins')
def all_coins():
    coins = get_coins()
    return respond('coins', coins, rows=list(coins.values()))


@app.route('/<coin>/badge.svg')
def badge(coin):
    coin = coin.lower()
    c = Coin(coin)
    vs = (request.args.get('vs') or 'usd').lower()

    if vs != 'usd':
        supported = scraper.supported_vs_currencies()
        if supported and vs not in supported:
            svg = _render_badge(coin, 'bad vs', '#9f9f9f')
            return Response(svg, mimetype='image/svg+xml', status=400)
        price = scraper.price_in(coin, vs)
    else:
        price = c.usd

    label = (request.args.get('label') or coin).strip() or coin
    symbol = {'usd': '$', 'eur': '€', 'gbp': '£', 'jpy': '¥'}.get(vs, '')
    if symbol:
        value_text = '{}{}'.format(symbol, _human_price(price))
    else:
        value_text = '{} {}'.format(_human_price(price), vs.upper())

    change = c.change_24h
    if change is None:
        color = '#007ec6'   # blue
    elif change >= 0:
        color = '#4c1'      # green
    else:
        color = '#e05d44'   # red

    svg = _render_badge(label, value_text, color)
    return Response(svg, mimetype='image/svg+xml',
                    headers={'Cache-Control': 'public, max-age=60'})


@app.route('/<coin>')
def get_coin(coin):
    c = Coin(coin.lower())

    payload = {
        'name': c.name,
        'ticker': c.ticker,
        'rank': c.rank,
        'usd': c.usd,
        'btc': c.btc,
        'market_cap': c.market_cap,
        'volume_24h': c.volume_24h,
        'change_24h': c.change_24h,
        'circulating_supply': c.circulating_supply,
        'total_supply': c.total_supply,
        'ath': c.ath,
        'last_updated': c.last_updated,
    }
    err = _augment_vs(payload, coin.lower())
    if err:
        return err
    scalar = payload.get('vs_price', payload.get('usd'))
    return respond('coin', payload, scalar=scalar)


@app.route('/<coin>/forecast')
def get_forecast(coin):
    return jsonify(forecast=get_predictions(coin.lower()))


@app.route('/<coin>/forecast/graph')
def get_forecast_graph(coin):
    return get_predictions(coin.lower(), render=True)


@app.route('/<coin>/<float:n>')
def get_value(coin, n):
    c = Coin(coin.lower())
    payload = {
        'usd': convert_to_decimal(c.usd * n),
        'exchange_rate': c.usd,
    }
    err = _augment_vs(payload, coin.lower(), n=n)
    if err:
        return err
    scalar = payload.get('vs_value', payload.get('usd'))
    return respond('coin', payload, scalar=scalar)


@app.route('/<coin>/<int:n>')
def get_value_int(coin, n):
    return get_value(coin, n)


@app.route('/<coin>/history')
def get_history(coin):
    c = Coin(coin.lower())

    q = "SELECT * from api_coin WHERE name=:coin ORDER BY date desc"

    if request.args.get('key') in API_KEYS and request.args.get('key'):
        db = _get_db('HEROKU_POSTGRESQL_TEAL_URL') or _get_db()
    else:
        db = _get_db()

    if db is None:
        return jsonify(history=[])

    import maya
    rows = db.query(q, coin=c.name)

    return jsonify(history=[
        {
            'value': r.value,
            'value.currency': 'USD',
            'timestamp': maya.MayaDT.from_datetime(r.date).subtract(hours=4).iso8601(),
            'when': maya.MayaDT.from_datetime(r.date).subtract(hours=4).slang_time(),
        } for r in rows]
    )


@app.route('/<coin1>/to/<coin2>')
def get_exchange(coin1, coin2):
    c = Coin(coin1.lower())
    rate = c.value(coin2.lower())
    return respond('coin', {'exchange_rate': rate}, scalar=rate)


@app.route('/<coin1>/<float:n>/to/<coin2>/')
def get_exchange_value(coin1, coin2, n):
    c = Coin(coin1.lower())
    v = c.value(coin2.lower())
    n = convert_to_decimal(n)

    value = convert_to_decimal(v * n)
    return respond('coin', {
        'value': value,
        'value.coin': coin2,
        'exchange_rate': v,
    }, scalar=value)


@app.route('/<coin1>/<int:n>/to/<coin2>/')
def get_exchange_value_int(coin1, coin2, n):
    return get_exchange_value(coin1.lower(), coin2, n)


# GraphQL endpoint. flask-graphql is unmaintained and incompatible with
# graphene 3, so we execute against the schema directly.
@app.route('/graphql', methods=['GET', 'POST'])
def graphql_view():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        query = data.get('query') or request.args.get('query')
        variables = data.get('variables')
    else:
        query = request.args.get('query')
        variables = None

    if not query:
        return jsonify(errors=[{'message': 'Provide a GraphQL query.'}]), 400

    result = schema.execute(query, variables=variables)

    payload = {}
    if result.errors:
        payload['errors'] = [{'message': str(e)} for e in result.errors]
    if result.data is not None:
        payload['data'] = result.data
    status = 200 if not result.errors else 400
    return jsonify(payload), status


# ---------------------------------------------------------------------------
# Machine/agent discovery: an OpenAPI spec and an llms.txt so LLM tools and
# agents can consume the API with zero auth and zero guesswork.
# ---------------------------------------------------------------------------

def _base_url():
    return request.url_root.rstrip('/')


@app.route('/openapi.json')
def openapi():
    base = _base_url()
    spec = {
        'openapi': '3.0.3',
        'info': {
            'title': 'Coinbin',
            'description': 'Human-friendly, keyless crypto currency data. '
                           'No API key, no rate limit. Append ?format=text for a '
                           'bare number or ?format=csv for spreadsheets.',
            'version': '2.0.0',
        },
        'servers': [{'url': base}],
        'paths': {
            '/coins': {'get': {
                'operationId': 'listCoins',
                'summary': 'All known coins keyed by ticker.',
                'responses': {'200': {'description': 'OK'}},
            }},
            '/{coin}': {'get': {
                'operationId': 'getCoin',
                'summary': 'Price and market data for a coin (e.g. btc).',
                'parameters': [
                    {'name': 'coin', 'in': 'path', 'required': True,
                     'schema': {'type': 'string'}, 'example': 'btc'},
                    {'name': 'vs', 'in': 'query', 'required': False,
                     'schema': {'type': 'string'}, 'example': 'eur',
                     'description': 'Optional non-USD quote currency.'},
                    {'name': 'format', 'in': 'query', 'required': False,
                     'schema': {'type': 'string', 'enum': ['json', 'text', 'csv']}},
                ],
                'responses': {'200': {'description': 'OK'}},
            }},
            '/{coin}/{amount}': {'get': {
                'operationId': 'getValue',
                'summary': 'USD value of an amount of a coin.',
                'parameters': [
                    {'name': 'coin', 'in': 'path', 'required': True,
                     'schema': {'type': 'string'}, 'example': 'btc'},
                    {'name': 'amount', 'in': 'path', 'required': True,
                     'schema': {'type': 'number'}, 'example': 2},
                ],
                'responses': {'200': {'description': 'OK'}},
            }},
            '/{from}/to/{to}': {'get': {
                'operationId': 'getExchangeRate',
                'summary': 'Exchange rate from one coin to another.',
                'parameters': [
                    {'name': 'from', 'in': 'path', 'required': True,
                     'schema': {'type': 'string'}, 'example': 'btc'},
                    {'name': 'to', 'in': 'path', 'required': True,
                     'schema': {'type': 'string'}, 'example': 'eth'},
                ],
                'responses': {'200': {'description': 'OK'}},
            }},
            '/{coin}/badge.svg': {'get': {
                'operationId': 'getBadge',
                'summary': 'An embeddable SVG price badge.',
                'parameters': [
                    {'name': 'coin', 'in': 'path', 'required': True,
                     'schema': {'type': 'string'}, 'example': 'btc'},
                ],
                'responses': {'200': {'description': 'SVG image'}},
            }},
        },
    }
    return jsonify(spec)


@app.route('/llms.txt')
def llms_txt():
    base = _base_url()
    text = (
        '# Coinbin\n\n'
        '> Human-friendly, keyless crypto currency data. No API key, no rate '
        'limit. Responses are JSON by default; add ?format=text for a bare '
        'number or ?format=csv for spreadsheets.\n\n'
        '## Endpoints\n'
        '- {b}/coins : all coins keyed by ticker\n'
        '- {b}/btc : price + market data for a coin\n'
        '- {b}/btc?vs=eur : quote in another currency\n'
        '- {b}/btc?format=text : just the number (great for shells)\n'
        '- {b}/btc/2 : USD value of an amount\n'
        '- {b}/btc/to/eth : exchange rate between two coins\n'
        '- {b}/btc/2/to/eth/ : value of an amount converted to another coin\n'
        '- {b}/btc/badge.svg : embeddable SVG price badge\n'
        '- {b}/openapi.json : machine-readable API spec\n'
        '- {b}/graphql : GraphQL endpoint\n'
    ).format(b=base)
    return Response(text, mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
