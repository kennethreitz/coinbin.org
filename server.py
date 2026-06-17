import os
import decimal

from flask import Flask, jsonify, render_template, request
from flask.json.provider import DefaultJSONProvider
from flask_caching import Cache
from flask_sslify import SSLify

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
    return jsonify(coins=get_coins())


@app.route('/<coin>')
def get_coin(coin):
    c = Coin(coin.lower())

    return jsonify(coin={
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
    })


@app.route('/<coin>/forecast')
def get_forecast(coin):
    return jsonify(forecast=get_predictions(coin.lower()))


@app.route('/<coin>/forecast/graph')
def get_forecast_graph(coin):
    return get_predictions(coin.lower(), render=True)


@app.route('/<coin>/<float:n>')
def get_value(coin, n):
    c = Coin(coin.lower())
    return jsonify(coin={
        'usd': convert_to_decimal(c.usd * n),
        'exchange_rate': c.usd,
    })


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
    return jsonify(coin={
        'exchange_rate': c.value(coin2.lower()),
    })


@app.route('/<coin1>/<float:n>/to/<coin2>/')
def get_exchange_value(coin1, coin2, n):
    c = Coin(coin1.lower())
    v = c.value(coin2.lower())
    n = convert_to_decimal(n)

    return jsonify(coin={
        'value': convert_to_decimal(v * n),
        'value.coin': coin2,
        'exchange_rate': v,
    })


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
