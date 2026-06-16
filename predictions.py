import os

from scraper import Coin, MWT, convert_to_decimal


PERIODS = 30
GRAPH_PERIODS = 365

# Forecasting pulls in a heavy, hard-to-build stack (prophet + cmdstanpy,
# pandas, numpy, matplotlib, mpld3) and needs the price-history database to be
# populated, so it is opt-in. Enable with FORECASTS_ENABLED=1 once those
# dependencies are installed (see the [forecast] extras in the Pipfile).
FORECASTS_ENABLED = os.environ.get('FORECASTS_ENABLED', '').lower() in ('1', 'true', 'yes')

_DISABLED_MESSAGE = {
    'enabled': False,
    'message': 'Forecasting is currently disabled on this instance.',
}


def _build_predictions(coin, render=False):
    """The real forecasting routine; only imported when enabled."""
    import records
    import maya
    import numpy as np

    # Matplotlib must pick a headless backend before pyplot is imported.
    import matplotlib
    matplotlib.use('agg')
    import mpld3
    from prophet import Prophet

    c = Coin(coin)

    q = "SELECT date as ds, value as y from api_coin WHERE name=:coin"

    db = records.Database()
    rows = db.query(q, coin=c.name)

    df = rows.export('df')

    df['y_orig'] = df['y']  # to save a copy of the original data..you'll see why shortly.

    # log-transform y
    df['y'] = np.log(df['y'])

    model = Prophet(weekly_seasonality=True, yearly_seasonality=True)
    model.fit(df)

    periods = PERIODS if not render else GRAPH_PERIODS

    future_data = model.make_future_dataframe(periods=periods, freq='d')
    forecast_data = model.predict(future_data)

    if render:
        matplotlib.pyplot.gcf()
        fig = model.plot(forecast_data, xlabel='Date', ylabel='log($)')
        return mpld3.fig_to_html(fig)

    forecast_data_orig = forecast_data  # make sure we save the original forecast data
    forecast_data_orig['yhat'] = np.exp(forecast_data_orig['yhat'])
    forecast_data_orig['yhat_lower'] = np.exp(forecast_data_orig['yhat_lower'])
    forecast_data_orig['yhat_upper'] = np.exp(forecast_data_orig['yhat_upper'])

    df['y_log'] = df['y']  # copy the log-transformed data to another column
    df['y'] = df['y_orig']  # copy the original data to 'y'

    d = forecast_data_orig['yhat'].to_dict()
    predictions = []

    for i, k in enumerate(list(d.keys())[-PERIODS:]):
        w = maya.when('{} days from now'.format(i + 1))
        predictions.append({
            'when': w.slang_time(),
            'timestamp': w.iso8601(),
            'usd': convert_to_decimal(d[k]),
        })

    return predictions


@MWT(timeout=300)
def get_predictions(coin, render=False):
    """Returns a list of predictions, unless render is True.
    Otherwise, returns rendered HTML.

    When forecasting is disabled (the default) or its optional dependencies are
    missing, returns a small explanatory payload instead of raising.
    """
    if not FORECASTS_ENABLED:
        if render:
            return '<p>Forecasting is currently disabled on this instance.</p>'
        return _DISABLED_MESSAGE

    try:
        return _build_predictions(coin, render=render)
    except ImportError:
        if render:
            return '<p>Forecasting dependencies are not installed.</p>'
        return {
            'enabled': False,
            'message': 'Forecasting dependencies are not installed.',
        }


if __name__ == '__main__':
    print(get_predictions('btc'))
