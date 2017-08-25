import os

from scraper import get_coins, get_coin, Coin
from wallets import wallets

from flask import Flask, jsonify, render_template, request
from flask_sslify import SSLify

import maya
import requests
import records

API_KEYS = os.environ.get('API_KEYS', '').split(':')

db = records.Database()
pro_db = records.Database(os.environ['HEROKU_POSTGRESQL_TEAL_URL'])


app = Flask(__name__)
app.debug = True

sslify = SSLify(app)

@app.route('/')
def hello():

    lbc = get_coin('lbc')
    lbc_42 = get_value_int('lbc', 42.01)
    lbc_sc = get_exchange('lbc', 'sc')
    lbc_42_sc = get_exchange_value('lbc', 'sc', 42.01)

    return render_template('index.html', lbc=lbc, lbc_42=lbc_42, lbc_sc=lbc_sc, lbc_42_sc=lbc_42_sc, coins=get_coins().values())

@app.route('/thanks')
def thanks():
    return jsonify(wallets=wallets, note='Your donations are greatly appreciated!')


@app.route('/coins')
def all_coins():
    return jsonify(coins=get_coins())


@app.route('/<coin>')
def get_coin(coin):
    c = Coin(coin)

    return jsonify(coin={
        'name': c.name,
        'ticker': c.ticker,
        'rank': c.rank,
        'usd': c.usd,
        'btc': c.btc
    })


@app.route('/<coin>/<float:n>')
def get_value(coin, n):
    c = Coin(coin)
    return jsonify(coin={
        'usd': c.usd * n,
        'exchange_rate': c.usd
    })


@app.route('/<coin>/<int:n>')
def get_value_int(coin, n):
    return get_value(coin, n)


@app.route('/<coin>/history')
def get_history(coin):
    c = Coin(coin)

    q = "SELECT * from api_coin WHERE name=:coin ORDER BY date desc"

    if request.args.get('key') in API_KEYS:
        print('Pro request!')
        rows = pro_db.query(q, coin=c.name)
    else:
        rows = db.query(q, coin=c.name)




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
    v = c.value(coin2)

    return jsonify(coin={
        # 'name': c.name,
        # 'ticker': c.ticker,
        'value': float(v) * n,
        'value.coin': coin2,
        'exchange_rate': v
    })


@app.route('/<coin1>/<int:n>/to/<coin2>/')
def get_exchange_value_int(coin1, coin2, n):
    return get_exchange_value(coin1, coin2, n)
