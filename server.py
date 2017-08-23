from flask import Flask, jsonify

import requests

session = requests.Session()

MARKETCAP_ALL_URL = 'https://coinmarketcap-nexuist.rhcloud.com/api/all'
MARKETCAP_COIN_TEMPLATE = 'https://coinmarketcap-nexuist.rhcloud.com/api/{ticker}'

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
        print 'Fetching data on {}'
        self.name = j['name']
        self.rank = j['position']
        self._value = j['price']['usd']

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
    return ([Coin(k) for k in r.json().keys()])

def get_coin(ticker):
    return Coin(ticker)


all_coins = get_coins()

print(get_coin('btc').value('eth'))

app = Flask(__name__)


@app.route('/')
# @common.cache.cached(timeout=50)
def hello():
    return jsonify(urls=[
        {'/coins': 'Returns all known coins.'},
        {'/:coin': 'Returns current value and rank of given coin.'},
        {'/:coin/:coin': 'Returns current exchange rate of two given coins.'},
        {'/:coin/:coin/:n': 'Returns the current value n coins, in any other coin.'},
    ])


@app.route('/coins')
def coins():
    return jsonify(coins=[c.ticker for c in all_coins])


@app.route('/<coin>')
def get_coin(coin):
    c = Coin(coin)
    return jsonify(coin={
        'name': c.name,
        'ticker': c.ticker,
        'rank': c.rank,
        'value': c.usd
    })


@app.route('/<coin1>/<coin2>')
def get_exchange(coin1, coin2):
    c = Coin(coin1)
    return jsonify(coin={
        # 'name': c.name,
        # 'ticker': c.ticker,
        'value': c.value(coin2),
        'value.coin': coin2
    })

@app.route('/<coin1>/<coin2>/<n>')
def get_exchange_value(coin1, coin2, n):
    n = float(n)
    c = Coin(coin1)
    return jsonify(coin={
        # 'name': c.name,
        # 'ticker': c.ticker,
        'value': c.value(coin2) * n,
        'exchange_rate': c.value(coin2)
    })