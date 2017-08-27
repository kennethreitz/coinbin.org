import records
import os

import maya
import numpy as np
import pandas as pd
import requests
from fbprophet import Prophet

from scraper import Coin


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


@MWT(timeout=120)
def get_predictions(coin):

    c = Coin(coin.lower())

    q = "SELECT date as ds, value as y from api_coin WHERE name=:coin"
    usd = requests.get('https://coinbin.org/btc').json()['coin']['usd']

    pro_db = records.Database(os.environ['HEROKU_POSTGRESQL_TEAL_URL'])
    rows = pro_db.query(q, coin='NEO')

    df = rows.export('df')

    df['y_orig'] = df['y']  # to save a copy of the original data..you'll see why shortly. 

    # log-transform y
    df['y'] = np.log(df['y'])

    model = Prophet(weekly_seasonality=True)
    model.fit(df)

    future_data = model.make_future_dataframe(periods=6, freq='h')
    forecast_data = model.predict(future_data)
    print(forecast_data[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

    forecast_data_orig = forecast_data  # make sure we save the original forecast data
    forecast_data_orig['yhat'] = np.exp(forecast_data_orig['yhat'])
    forecast_data_orig['yhat_lower'] = np.exp(forecast_data_orig['yhat_lower'])
    forecast_data_orig['yhat_upper'] = np.exp(forecast_data_orig['yhat_upper'])

    df['y_log'] = df['y']  #copy the log-transformed data to another column
    df['y'] = df['y_orig']  #copy the original data to 'y'

    # print(forecast_data_orig)
    d = forecast_data_orig['yhat'].to_dict()
    predictions = []
    for i, k in enumerate(list(d.keys())[-6:]):
        w = maya.when(f'{61*i} minutes from now')
        predictions.append({
            'when': d.slang_time(),
            'timestamp': w.iso8601(),
            'usd': d[k],
        })
    return predictions


# results = list(zip(*[forecast_data_orig[c].values.tolist() for c in forecast_data_orig]))[-6:]
# for result in results:
#     dt = maya.MayaDT(result[0])
#     _min = result[7]
#     _max = result[8]
#     _prediction = result[16]
#     print(dt.slang_time(), _min, _max, _prediction)
