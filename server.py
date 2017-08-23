from flask import Flask, jsonify

import maya
import requests
import records

session = requests.Session()

MARKETCAP_ALL_URL = 'https://coinmarketcap-nexuist.rhcloud.com/api/all'
MARKETCAP_COIN_TEMPLATE = 'https://coinmarketcap-nexuist.rhcloud.com/api/{ticker}'

db = records.Database()

class Coin():
    """A Coin, unlike Mario's."""

    def __init__(self, ticker):
        self.ticker = ticker
        self.name = None
        self.rank = None
        self._value = None

        self.update()

    def _get(self):
        url = MARKETCAP_COIN_TEMPLATE.format(ticker=self.ticker)
        r = session.get(url)
        return r.json()

    def update(self):
        j = self._get()
        print(f'Fetching data on {self.ticker}')
        try:
            self.name = j['name']
            self.rank = j['position']
            self._value = j['price']['usd']
        except KeyError:
            print(j)

    @property
    def usd(self):
        return self._value

    def value(self, coin):
        """Example: BTC -> ETH"""
        return (self.usd / Coin(coin).usd)

    def __repr__(self):
        return f'<Coin ticker={self.ticker!r}>'


def get_coins():
    r = session.get(MARKETCAP_ALL_URL)
    return [k for k in r.json().keys()]


def get_coin(ticker):
    return Coin(ticker)


all_coins = get_coins()

print(get_coin('btc').value('eth'))

app = Flask(__name__)


@app.route('/')
# @common.cache.cached(timeout=50)
def hello():
    return jsonify(urls=[
        {'/coins': 'Returns all known coin names.'},
        {'/:coin': 'Returns current value and rank of the given coin.'},
        {'/:coin/history': 'Returns the value history of the given coin.'},
        {'/:coin/:n': 'Returns current value of n coins.'},
        {'/:coin/to/:coin': 'Returns current exchange rate of two given coins.'},
        {'/:coin/:n/to/:coin/': 'Returns the current value n coins, in any other coin.'},
        {'/thanks': 'Send us coins for running this free service!'}
    ])

@app.route('/thanks')
def thanks():
    return jsonify(wallets={
        'btc': '1PYZH8SCXQF7c2qgpsQ8kDgKixXeYvVsKv',
        'ltc': 'LXPtxt68njDdTBdu1ZvHUbARhHsPm9T3Zq',
        'doge': 'DRDjoTo3zg64QHpq3xgrVVJnerLAvVzMbc',
        'vtc': 'VvNd9XoYKavHagE6VkLNPeAazFmpgMZgQ5',
        'ppc': 'PMQWpq15QxT4dR6h6NrvrJMNtehcmRVxYW',
        'ftc': '6zDLXZmoNBdz87ZMvtK2JF7C3NRuKu2nVr',
        'rdd': 'RudBYrzAQeYmDXHhMXs7hPsYJc7n1C7Trt',
        'nxt': {'message': '64e086b979514034946628b937ce3fcb2f0e34c84823402ab9f41a4940a6cff4', 'address': 'NXT-97H4-KRWL-A53G-7GVRG'},
        'dash': 'XvtKBmKUhiEPQyEgNxvSRt9hyHBCN8Mia7',
        'pot': 'PTjS6cpqGoUUbEKyUWMqHk92ymvXMi84Ti',

    }, note='Your donations are greatly appreciated!')

@app.route('/coins')
def coins():
    return jsonify(coins=all_coins)


@app.route('/<coin>')
def get_coin(coin):
    c = Coin(coin)
    return jsonify(coin={
        'name': c.name,
        'ticker': c.ticker,
        'rank': c.rank,
        'value': c.usd,
        'value.currency': 'USD'
    })


@app.route('/<coin>/<float:n>')
def get_value(coin, n):
    c = Coin(coin)
    return jsonify(coin={
        'value': c.usd * n,
        'value.currency': 'USD',
        'exchange_rate': c.usd
    })


@app.route('/<coin>/<int:n>')
def get_value_int(coin, n):
    return get_value(coin, n)


@app.route('/<coin>/history')
def get_history(coin):
    c = Coin(coin)
    rows = db.query("SELECT * from api_coin WHERE name=:coin ORDER BY date desc", coin=c.name)

    return jsonify(history=[
        {
            'value': r.value,
            'value.currency': 'USD',
            'timestamp': maya.MayaDT.from_datetime(r.date).iso8601(),
            'when': maya.MayaDT.from_datetime(r.date).slang_date()
        } for r in rows]
    )

@app.route('/<coin1>/to/<coin2>')
def get_exchange(coin1, coin2):
    c = Coin(coin1)
    return jsonify(coin={
        # 'name': c.name,
        # 'ticker': c.ticker,
        'exchange_rate': c.value(coin2),
    })


@app.route('/<coin1>/<float:n>/to/<coin2>/')
def get_exchange_value(coin1, coin2, n):
    c = Coin(coin1)
    return jsonify(coin={
        # 'name': c.name,
        # 'ticker': c.ticker,
        'value': c.value(coin2) * n,
        'value.currency': 'USD',
        'exchange_rate': c.value(coin2)
    })


@app.route('/<coin1>/<int:n>/to/<coin2>/')
def get_exchange_value_int(coin1, coin2, n):
    return get_exchange_value(coin1, coin2, n)
