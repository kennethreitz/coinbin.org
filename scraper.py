import pandas
import requests

from pyquery import PyQuery as pq

import time
from collections import OrderedDict
from decimal import Decimal

url = 'https://coinmarketcap.com/currencies/views/all/'
session = requests.Session()


class MWT(object):
    """Memoize With Timeout"""
    _caches = {}
    _timeouts = {}

    def __init__(self, timeout=2):
        self.timeout = timeout

    def collect(self):
        """Clear cache of results which have timed out"""
        for func in self._caches:
            cache = {}
            for key in self._caches[func]:
                if (time.time() - self._caches[func][key][1]) < self._timeouts[func]:
                    cache[key] = self._caches[func][key]
            self._caches[func] = cache

    def __call__(self, f):
        self.cache = self._caches[f] = {}
        self._timeouts[f] = self.timeout

        def func(*args, **kwargs):
            kw = sorted(kwargs.items())
            key = (args, tuple(kw))
            try:
                v = self.cache[key]
                if (time.time() - v[1]) > self.timeout:
                    raise KeyError
            except KeyError:
                v = self.cache[key] = f(*args, **kwargs), time.time()
            return v[0]
        func.func_name = f.__name__

        return func


def convert_to_decimal(f):
    return Decimal("{0:.8f}".format(f))


class Coin():
    """A Coin, unlike Mario's."""

    def __init__(self, ticker):
        self.ticker = ticker
        self.name = None
        self.rank = None
        self._value = None

        self.update()

    def update(self):
        coins = get_coins()
        print(f'Fetching data on {self.ticker}')

        self.name = coins[self.ticker]['name']
        self.rank = coins[self.ticker]['rank']
        self._usd = coins[self.ticker]['usd']

    @property
    def usd(self):
        return self._usd

    @property
    def btc(self):
        coins = get_coins()
        rate = coins['btc']['usd']
        return convert_to_decimal(self.usd / rate)

    def value(self, coin):
        """Example: BTC -> ETH"""
        return convert_to_decimal(self.btc / Coin(coin).btc)

    def __repr__(self):
        return f'<Coin ticker={self.ticker!r}>'


@MWT(timeout=300)
def get_coins():
    coins_db = OrderedDict()

    r = session.get(url)
    html = pq(pq(r.content)('table')[0]).html()
    df = pandas.read_html("<table>{}</table>".format(html))
    df = pandas.concat(df)

    btc_value = float(df.to_dict()['Price'][0][1:].replace(',', ''))

    for row in df.itertuples():

        rank = int(row[1])
        name = row[2]
        ticker = row[3].lower()
        usd = float(row[5][1:].replace(',', ''))
        btc = convert_to_decimal(usd / btc_value)

        coins_db.update({ticker: {'rank': rank, 'name': name, 'ticker': ticker, 'usd': usd, 'btc': btc}})

    return coins_db


def get_coin(ticker):
    return Coin(ticker)
