import os
import time
from collections import OrderedDict
from decimal import Decimal

import requests

try:
    import crayons
except ImportError:  # crayons is only used for pretty logging
    crayons = None


# CoinMarketCap removed the free `/currencies/views/all/` HTML page this code
# used to scrape, so the data layer now talks to a JSON price API instead.
# CoinGecko is the default because it needs no API key; set COINGECKO_API_BASE
# (and optionally COINGECKO_API_KEY) to point at a different/pro instance.
API_BASE = os.environ.get('COINGECKO_API_BASE', 'https://api.coingecko.com/api/v3')
API_KEY = os.environ.get('COINGECKO_API_KEY')
# Number of 250-coin pages to pull (ordered by market cap).
PAGES = int(os.environ.get('COINGECKO_PAGES', '4'))
PER_PAGE = 250

session = requests.Session()
session.headers.update({'User-Agent': 'coinbin.org/2 (+https://coinbin.org)'})
if API_KEY:
    session.headers.update({'x-cg-pro-api-key': API_KEY})


def _log(msg):
    if crayons is not None:
        print(msg)


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
        func.__name__ = f.__name__

        return func


def convert_to_decimal(f):
    return Decimal("{0:.8f}".format(f))


class Coin():
    """A Coin, unlike Mario's."""

    def __init__(self, ticker):
        self.ticker = ticker
        self.name = None
        self.rank = None
        self._usd = None

        self.update()

    def update(self):
        coins = get_coins()
        if crayons is not None:
            print('Fetching data on {}...'.format(crayons.cyan(self.ticker)))

        if self.ticker not in coins:
            raise KeyError('Unknown coin: {!r}'.format(self.ticker))

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
        return '<Coin ticker={!r}>'.format(self.ticker)


def _fetch_markets():
    """Yield raw market rows from the price API, highest market cap first."""
    rows = []
    for page in range(1, PAGES + 1):
        r = session.get(
            '{}/coins/markets'.format(API_BASE),
            params={
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': PER_PAGE,
                'page': page,
            },
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < PER_PAGE:
            break
    return rows


@MWT(timeout=300)
def get_coins():
    coins_db = OrderedDict()

    if crayons is not None:
        print(crayons.yellow('Fetching coin data...'))

    rows = _fetch_markets()

    # We need BTC's price to express every coin's value in BTC.
    btc_value = None
    for row in rows:
        if (row.get('symbol') or '').lower() == 'btc':
            btc_value = row.get('current_price')
            break

    for row in rows:
        ticker = (row.get('symbol') or '').lower()
        if not ticker or ticker in coins_db:
            # Symbols are not unique across coins; keep the highest-market-cap
            # entry (rows arrive in market-cap order) and ignore later dupes.
            continue

        name = row.get('name') or ticker
        rank = row.get('market_cap_rank')
        usd = row.get('current_price') or 0

        if btc_value:
            btc = convert_to_decimal(usd / btc_value)
        else:
            btc = convert_to_decimal(0)

        coins_db[ticker] = {
            'rank': rank,
            'name': name,
            'ticker': ticker,
            'usd': usd,
            'btc': btc,
        }

    return coins_db


def get_coin(ticker):
    return Coin(ticker)


if __name__ == '__main__':
    print(get_coins())
