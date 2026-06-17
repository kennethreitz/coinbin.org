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
#
# CoinGecko has two hosts/keys:
#   - Demo (free):  https://api.coingecko.com/api/v3      header x-cg-demo-api-key
#   - Pro (paid):   https://pro-api.coingecko.com/api/v3  header x-cg-pro-api-key
# Keyless access still works but is heavily rate-limited and often blocked from
# datacenter IPs, so a Demo key is recommended in production. The base URL is
# auto-selected from whichever key is set; override with COINGECKO_API_BASE.
PUBLIC_API_BASE = 'https://api.coingecko.com/api/v3'
PRO_API_BASE = 'https://pro-api.coingecko.com/api/v3'

API_KEY = os.environ.get('COINGECKO_API_KEY')           # Pro key
DEMO_API_KEY = os.environ.get('COINGECKO_DEMO_API_KEY')  # Demo (free) key

if os.environ.get('COINGECKO_API_BASE'):
    API_BASE = os.environ['COINGECKO_API_BASE']
elif API_KEY:
    API_BASE = PRO_API_BASE
else:
    API_BASE = PUBLIC_API_BASE

# Number of 250-coin pages to pull (ordered by market cap).
PAGES = int(os.environ.get('COINGECKO_PAGES', '4'))
PER_PAGE = 250

session = requests.Session()
session.headers.update({
    'User-Agent': 'coinbin.org/2 (+https://coinbin.org)',
    'Accept': 'application/json',
})
if API_KEY:
    session.headers['x-cg-pro-api-key'] = API_KEY
elif DEMO_API_KEY:
    session.headers['x-cg-demo-api-key'] = DEMO_API_KEY


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
    """Format a number as a Decimal.

    Uses 8 decimal places for normal magnitudes (back-compatible), but keeps
    significant figures for very small "sub-satoshi" prices, which are common
    with the high-supply / meme tokens that didn't exist when this was written.
    Without this, a price like 1.2e-10 would round to 0.00000000.
    """
    if f is None:
        return None
    d = Decimal(str(f))
    if d == 0:
        return Decimal('0')
    if abs(d) >= Decimal('0.00000001'):
        return d.quantize(Decimal('0.00000001'))
    # Sub-1e-8: preserve ~6 significant figures instead of truncating to zero.
    return d.quantize(Decimal(1).scaleb(d.adjusted() - 5))


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

        data = coins[self.ticker]
        self.name = data['name']
        self.rank = data['rank']
        self._usd = data['usd']

        # Richer market data that modern crypto APIs expose (and clients expect).
        self.market_cap = data.get('market_cap')
        self.volume_24h = data.get('volume_24h')
        self.change_24h = data.get('change_24h')
        self.circulating_supply = data.get('circulating_supply')
        self.total_supply = data.get('total_supply')
        self.ath = data.get('ath')
        self.last_updated = data.get('last_updated')

    @property
    def usd(self):
        return self._usd

    @property
    def btc(self):
        coins = get_coins()
        rate = coins['btc']['usd']
        if not rate:
            return convert_to_decimal(0)
        return convert_to_decimal(self.usd / rate)

    def value(self, coin):
        """Exchange rate from this coin to another (e.g. BTC -> ETH).

        Computed via USD rather than via BTC: crypto is USD/stablecoin-quoted
        now, and going through USD avoids breaking when a BTC price is missing.
        """
        other = Coin(coin)
        if not other.usd:
            return convert_to_decimal(0)
        return convert_to_decimal(self.usd / other.usd)

    def __repr__(self):
        return '<Coin ticker={!r}>'.format(self.ticker)


def _fetch_markets(vs_currency='usd'):
    """Yield raw market rows from the price API, highest market cap first."""
    rows = []
    for page in range(1, PAGES + 1):
        r = session.get(
            '{}/coins/markets'.format(API_BASE),
            params={
                'vs_currency': vs_currency,
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
            # Richer fields the API already returns; cheap to keep, expected now.
            'market_cap': row.get('market_cap'),
            'volume_24h': row.get('total_volume'),
            'change_24h': row.get('price_change_percentage_24h'),
            'circulating_supply': row.get('circulating_supply'),
            'total_supply': row.get('total_supply'),
            'ath': row.get('ath'),
            'last_updated': row.get('last_updated'),
        }

    return coins_db


def get_coin(ticker):
    return Coin(ticker)


@MWT(timeout=300)
def _prices_in(vs_currency):
    """Map ticker -> current price in an arbitrary quote currency.

    The main USD path (get_coins) is left untouched; this is a separate,
    independently-cached fetch used only for non-USD `?vs=` lookups.
    """
    prices = {}
    for row in _fetch_markets(vs_currency):
        ticker = (row.get('symbol') or '').lower()
        if ticker and ticker not in prices:
            prices[ticker] = row.get('current_price') or 0
    return prices


def price_in(ticker, vs_currency):
    """Current price of a coin in the given quote currency, or None."""
    return _prices_in(vs_currency.lower()).get(ticker.lower())


@MWT(timeout=3600)
def supported_vs_currencies():
    """Set of quote currencies the upstream API supports (best-effort)."""
    try:
        r = session.get(
            '{}/simple/supported_vs_currencies'.format(API_BASE), timeout=30,
        )
        r.raise_for_status()
        return set(x.lower() for x in r.json())
    except Exception:
        return set()


if __name__ == '__main__':
    print(get_coins())
