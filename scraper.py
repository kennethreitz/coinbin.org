import pandas
import requests

from pyquery import PyQuery as pq

import time
from collections import OrderedDict

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


@MWT(timeout=300)
def get_coins():
    coins_db = OrderedDict()

    r = session.get(url)
    html = pq(pq(r.content)('table')[0]).html()
    df = pandas.read_html("<table>{}</table>".format(html))
    df = pandas.concat(df)
    for row in df.itertuples():

        rank = int(row[1])
        name = row[2]
        ticker = row[3].lower()
        usd = float(row[5][1:].replace(',', ''))

        coins_db.update({ticker: {'rank': rank, 'name': name, 'ticker': ticker, 'usd': usd}})

    return coins_db


