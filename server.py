import os

from flask import Flask, jsonify, render_template
from flask_sslify import SSLify

import maya
import requests
import records

session = requests.Session()

MARKETCAP_ALL_URL = 'https://coinmarketcap-nexuist.rhcloud.com/api/all'
MARKETCAP_COIN_TEMPLATE = 'https://coinmarketcap-nexuist.rhcloud.com/api/{ticker}'

API_KEYS = os.environ.get('API_KEYS', '').split(':')

db = records.Database()
pro_db = records.Database(os.environ['HEROKU_POSTGRESQL_TEAL'])

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
sslify = SSLify(app)

@app.route('/')
# @common.cache.cached(timeout=50)
def hello():

    lbc = get_coin('lbc')
    lbc_42 = get_value_int('lbc', 42.01)
    lbc_sc = get_exchange('lbc', 'sc')
    lbc_42_sc = get_exchange_value('lbc', 'sc', 42.01)

    return render_template('index.html', lbc=lbc, lbc_42=lbc_42, lbc_sc=lbc_sc, lbc_42_sc=lbc_42_sc, coins=all_coins)

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
        'dash': 'XvtKBmKUhiEPQyEgNxvSRt9hyHBCN8Mia7',
        'pot': 'PTjS6cpqGoUUbEKyUWMqHk92ymvXMi84Ti',
        'blk': 'BKNihHBXHy24q7wWM6A45xnDWTvcKrcmXN',
        'emc2': 'EbMSP6TnLgfiJEnL1SUf4N8tjSHsY2L8zA',
        'xmy': 'MQPjf1pCpKQDVabTXe3do4JTQ9A81oJyHp',
        'aur': 'AVdVKHAvQij7QWmZ8p8P3qArK1eunrUukK',
        'gld': 'E6UVrbrd4VnvspMuDqDw7FfMhGAqj26dZE',
        'fair': 'fVkBYTPiQpcWCmFGSTtxhug2yW2nDZw6x7',
        'slr': '8WUGQdSjo6XikocLF54KfHfBJ2HQqwtE3t',
        'ptc': 'LJ7NefEUuJ9DC8qneEW2541p5iJzxNMqyQ',
        'grs': 'FZg2ceLVCRFaV48C1BViKd1ersC9pxcHeb',
        'nlg': 'GTEBkz4H73YJgTNhAVtwvwZwUgTsEezVjR',
        'xwc': 'WXiGQuL7YNhDj93GMdRWJK3gdPMJfQWB8e',
        'mona': 'MSE8zn8b7tdHnCL45em7nes5BtTQfPuSwc',
        'enrg': 'eBzzqNtRCsxYLDyKkBT4CSiu2c6hFK8N5X',
        'rby': 'RRcRzBTcz8HhfNncH9rbKM1hppwMB4EpPj',
        'thc': 'HMemWrgjEfmgutjkM7C2zMqgpj97SJtW7g',
        'erc': 'EWeL8eYZRJJZnMFrwMvhidxJsXDcfsELgL',
        'vrc': 'VUmKQQdfVdsNfSzGtWZddWnv1gD1VuYPSa',
        'cure': 'BE1rrjqnMPXnLbsTXdbhe13wuRRN1q5qTy',
        'cloak': 'BtMtdrXRWBw6YMfSsxtkBiRP1wYeFH2Xrk',
        'bsd': 'iPcwLWBxp2BYfDCyGYbvHbjRCzGL7rjE2U',
        'start': 'sdvC9GSopsBmJ8VtVmNxKf1xwcGtY9bzwz',
        'kore': 'K8iJwoL5ojPWw2kjhnWJrNwm1rsoWewErb',
        'trust': 'TUFooWK6jqDYHKUggZyREvPAeK6nhSYHAX',
        'nav': 'NUBRSjHJ8h52bqF2d2U4iXzEF3v6fgskw4',
        'xst': 'S6L8FQGNLhpGEhcZzt4YMYNHq1H98QKkmK',
        'btcd': 'RCJPmNM6BaNBTiomfJ83c2hEjMpnLjFghe',
        'via': 'Vcd9Be6s1NePuci1LvC16K21kBytYmRf1t',
        'uno': 'uZsGhq6VfNpYPUtNqg9fdushmsuc6B9GMA',
        'pink': '2EjF3ACSNJqudSKZaEeSHvkGqVFg4JtUSA',
        'ioc': 'iZmhHdNtPGfEVwswTkaLEDEuxrHQFDGD77',
        'cann': 'CemM7gxYYJK9weV6Ed8sw4B7fvPQgY8hfW',
        'sys': 'SUNH2SNQqaZvxqqPvuQcBVNdZshPRq2ZTv',
        'neos': 'NTM232LiTUz8tgXmAWg8TxbrKtcAkDW9Mr',
        'dgb': 'DA2eLVocFESdqVETtgVLP6k1m319o4g4Yq',
        'excl': 'EPdycUjUzcYvFFGvTPC8z9NriZ8EgxLL7P',
        'dope': 'D6NTRES89hzLNYx55AEuqWuAs8rUsR3sVc',
        'block': 'Ba3yDhGLkiqN28YXoMYgBPuSjKht4a2ZGK',
        'aby': 'AMbFZwYzjMJHtjJL3fHti2k2JtpfqrX7Ud',
        'byc': 'BGD2TfaNbN6wq6CZXHMG9fSEWdniVZhJzn',
        'blitz': 'oWZsQvU3T9FU25FdmRnAousz5CpzXjd6Eg',
        'bay': 'BFDi3ZSZorDPX17iYrmhRFRSQK5DniqG4v',
        'spr': 'SYeuSdejAg8jbhrC6pYmwMMPn99egVmyaP',
        'vtr': 'xr14J4LzdL4jYfRNpP5WdPjtq5dC2YNXiZA27ZayWqC87o4B4UwibZFWr6U5B3B3T7gdjfCqsN5c3btYhFSzBCf2fDL9Bvj1LAPqYQ',
        'game': 'GMn4k4jXVDjVbSMCWabNguczwADkQxnnRu',
        'nxs': '2RQbTTGVYJB1qkghsoZunueS71EPfc6KfCbhJqXveLJFCCK4U35',
        'bitb': '2UjoiH7RmYhvdzJRGXAt5SVeP1iw9MP3Ka',
        'xvg': 'DAtQMkVj14Vs4jUww8EcnurUGz1c92pBV9',
        'geo': 'GR7Zj1EsHWc7M3KU5BDhTCSx4y9QR9nEEo',
        'flo': 'FMSEzFyS9dWhb69ch72VF1ETePnXnb2qxY',
        'nbt': 'BBijzpMJo92pT4dp1NxwGXY1kBJGxz1QJr',
        'grc': 'S1t5Jr2WwxZSeSNn8p5RkAAycHa2ZraShi',
        'mue': '7bSsG2TBa4645qitQsfBPj9Gp7ZW8QTa87',
        'xvc': 'VpYaBkNXNCtYg3HTP7onhdvhTqtvGBwBCo',
        'clam': 'xVJ7ySQNPfN3XKmAykTYapuZzZun23xsr5',
        'dmd': 'dGRJXSHNiF9SoAatLeuoKYxmCbKJ8aXkga',
        'gam': 'GSqe2k3G2EQQy3QNPwGyyyW33m7eEr6Df6',
        'sphr': 'BPpGQCDR63NcN6Po9Lvo2D8nqQbhpiSHcE',
        'ok': 'PGuDs5iu3sEaeAr1kMnMSwNCwJW2xUMTwA',
        'snrg': 'SYkCDBer4Kap91ftY4cdDfrjnTh3nRvNqk',
        'pkb': 'PLvXxUE6NrJqvoP1imR8sS23hDCmXoWcxz',
        'cpc': 'CYWUbfBTAVW9H4zAPRe6yckWWBVRXaznT1',
        'eth': '0xcf4c939ccae5c0ecc8b63505cce1513e5ef0d567',
        'gcr': 'GRxryTQ43RET8xfzm38L42wYchim9H3cHf',
        'tx': 'TixtGQBFrzfFH5Z1ouKjM4UDGqkKXcyw8p',
        'exp': '0xbc4ee321e752cdd8ca54e4405de71c5f4f5b5f24',
        'infx': 'iBJzRkcQk6coYUE4UFFDzvfi8Y1URMzyyA',
        'omni': '15rebjRT6mESSbHU9yyLTh8oADdC4x4RWg',
        'usdt': '1Ne3DYc5tJSAjS3rwqDt3GSN1FYMrHLPWr',
        'amp': '13f3KoRoFD5iJw1zdQBw5Hum5EYRs9pB3x',
        'agrs': '16EPWtBErUnT6fEsKmJfB4gxnJx5qndMCJ',
        'bta': 'BJD3NHuuiibB85FrxYULSHTgJmye25PRKF',
        'club': 'Ce9MJXxjasVSbVPntihwote3SjMbfqnvDJ',
        'vox': 'VV5QjvbWFC9rvWtLyxMvsJDT1FFk9jgbWa',
        'emc': 'EgPN6YhGXqgTL7np3UtAM2UReMs7eWVD8K',
        'fct': 'FA3EuMt78kTLHdJsfS65r15xE4acVRtARBfUnKTqfMmGUyTzcNtP',
        'maid': '1gUbRQjyQX2uJkezY8WY7KSEGGEmD9Zme',
        'egc': 'EZYWa2KKhzUstJnTZG1SA8zp7stiyrt2Up',
        'sls': 'SZVpV5LtN9WXdafou3BoHsacDhMcmCjUzr',
        'rads': 'XcML29TJXQihsV5JmphEVbTPcS6xPkcZFj',
        'dcr': 'DsUcYM48ZravjWaLCoeAxYQvTcNigqYaQVf',
        'safex': '1jTMyxf2iP9NxNzMDAZVhQVQskj7zvDj9',
        'pivx': 'DU6uyNH7E5VPse3hh4RZr4A12VQtM2E3Ue',
        'meme': 'PCXXZ3NKQUMA26GsX5cjozE48yvM5uUnrR',
        '2give': 'GpG7ygLvdd3GKsbAUvPRZbMR8GtXa7JizS',
        'lsk': '3548326455915242856L',
        'pdc': '12ZeM7mrPnZBM5rZWXh9QpNbe6eSTykxCr',
        'dgd': '0x7e7cec0a54cbda02b44e6c24a298b2d89b8f3c31',
        'brk': 'brfTVJS9JGtNX8prmKQBaQtWbtj1b1WJB7X',
        'waves': '3P6H2V28Zzs9qX3U86Rs5hzTFkcCJrbDJEm',
        'lbc': 'bVQKmE9tkLHxkjnu97SSe8eQHT9q4c69Zb',
        'brx': 'bxVriVBdAZ1jXkKFvBAA3zQkS819kZFqWVd',
        'etc': '0xb52c0534da8d758943e8604916b6be70071bc6d3',
        'strat': 'Sf8iKKeaAFRX772JA5TWXDwZMJZkJNwmSZ',
        'unb': '13izqwELn1jTt1j7umfoJKUPRUBBPmwpHv',
        'ebst': 'e91xYCEFKh2J2VogvUraooeCFUUcCbrUnM',
        'vrm': 'VXYWrM5h6YE7pU1zPjFpXYcGVoYnLAETyK',
        'xaur': '0x1253295779080ec136551724a27143e4470073a2',
        'seq': 'Se8Eg7u1k6izqAW3nmKAwuBewiJu1G2fbD',
        'sngls': '0x6f4f433ff62347998785e4ed30f3048a2281fd98',
        'rep': '0x16169642de5a4c43a5f3bcbc5eea36ca767ecc4d',
        'shift': '3548326455915242856S',
        'xzc': 'a3vmJpgzqDu4Yg6FPt9uj27m3sBAbMwtRs',
        'neo': 'AG2dY41SYEMmZLLy5dS1gNwHkWEAshE3ft',
        'zec': 't1fnCgLKXy7Q1ovFD5obWcH1Vmpp6ivVhJu',
        'zcl': 't1bHV2hFD8mVoVH2S7KVSfAmdTX615xXGgy',
        'iop': 'pEP4niYzA8eiPUfCcy5pnPxoETu7zx6n4G',
        'ubq': '0x98b3ffb0a988308304b32077ba31e5b300be1567',
        'hkg': '0x1567685a30ee1d1ace1f1e6291b727b1e2ca5eea',
        'sib': 'Sicrwdsg9mVMCACVJJq23RfqSXiNfH7H2f',
        'ion': 'ia2ts12ZrprJ9GjsuJChY1HmzeFnwy6k5x',
        'lmc': 'LZFKYiQRjX3zLaBRMTzF6kaRReoAqsTGgX',
        'qwark': '0xe4f1f6665f68489f6ff512194553918df13a1ae6',
        'crw': '12rCC2LwBBuue46KELC9zE9H75Tq9ff492',
        'swt': '0xaef9799c36cc1459d7876b56383a4a2107bc4b66',
        'time': '0x1ddcfde92c5c82f5fc919b69478ce65db5446483',
        'mln': '0x8c1d250c58133ff94b224390c3137d8dc4bf02bc',
        'tks': '3PESLYrs1s5sNYGBHD8bZnqWvB3pW3BMcWd',
        'ark': 'AJrDLieoPW46gg3XRANt3J8emDFdQPDUmq',
        'music': '0x9248334cf30082b5e301bef6fa29642c3170e2e4',
        'incnt': '3PEuNUJZpE4mjqhHZDCmisGabd4g1qzAeve',
        'gbyte': 'RYLB7TCEBR4WK3ZEBMGOSLHOPU2COVMZ',
        'gnt': '0x7da2d058575c81a0b5658878a3b3efed0de142d4',
        'nxc': '0x06e1d5c1e7dded4b9e32f45845e1d352c0cf8bc5',
        'edg': '0xdc8e6d7de95fb75774f2b3be2d03efd29d9242e8',
        'lgd': '0xce7591232523f66b14189c4cec4679e3ab7b3d8e',
        'trst': '0xa60ff29d26d373a88afbe74f6dbcab3aeca677e6',
        'wings': '0xb4466e1575882d28388820a719516d1dff412961',
        'rlc': '0xab916ef71e19c56c98de93d0dba99469b1283db1',
        'bcc': '1LVojXegSH5EhrNQncWfxg7ErVh4N9HCAL',
        'qtum': '0x1646d7c096047756ab0b1cb636cf5dd5d36959d2',
        'part': 'Ph9oGH1vwtsFTHmAwYh3iS9J1vcVhoLXFk',
        'cvc': '0x584827cad4a2cb47582ebd5a5ee6e4fd5ea63255',
        'omg': '0xef24cccdad02b96e8bd3c68757c1aab5547ecda7',
        'adx': '0x36f8b284fa87405389e672d74898d0bf2930a5d9',
        'storj': '0x05feda4008e2d9253bc339332a29a5a862c8c5d2',
        'mtl': '0x7b610ddc59fd76c1e8a23ff69904e5d4898bbf78',
        'pay': '0x3a957df561559587b43eb77b4266c8f0063ec948',
        'fun': '0xd9a996f367802920aa7bb5bce48de183f45eeb54',
        'adt': '0x7853d58160a73d538e89278bb036d2b80e00c351',
        'mco': '0xf3959d90b9b880ee29e62f1210a37fe9b54ce0c1',
        'snt': '0x3f6526ddd2e452ca6f93033653f0f39ace19f71e',
        'nmr': '0xcb83ccdd55939de0653b455d7aebf21982357320',
        'bnt': '0x3363f5a728901533511427d27f3151fe9df152a0',
        'cfi': '0xa27c5edf5d5ca32a3f3926f7d46d4dcbea43241d',
        'myst': '0x9dfe066e10215254e7e62c86a30fd0aea1884be3',
        'ptoy': '0x5bc546675be2ea8b3a56eab0161e7f8c6615930a',
        'crb': '0x3e12bb90fffebdab71dffca9557a81587d32862f',
        'qrl': '0x7e4b07296fc5a54031ca133b98546d350c0cd293',
        '1st': '0x919865c75dd7949fb061e7a2102290b79e4d9150',
        'bat': '0x04db9cf3de9183f8e5d5b7609c5793e4448c9bf6',
        'sc': '6197b45062c2d75d8d94d7c7fe4a6530cc6fe6422e0edd9f285d237646b2392541c03005947d',
        'zen': 'znmGXVrq1UcF3r59C8V75t6zqFkmqMzC4YY',
        'ant': '0xd54c9c210d286e5bae0e5f59ca8817e9dc2378de',
        'hmq': '0x0c3a58dc40e933b2031d0cbfe08cf0738f55a17d',
        'tkn': '0x5a020b51b748b21274078e42b10a7eb3988e89e1',
        'apx': '0x2c4588d7d92700966fc6101af9b1af4181ab5358',
        'lun': '0x12c38554537d9677aef623cf7bd9b9460d51045b',
        'gup': '0xf4b6b5fce73e455e93f80190b7f7e5999864a3de',
        'gno': '0x8e2118d168713e639b624851958cc5fa46ebce2a',
        'rlc': '0xab916ef71e19c56c98de93d0dba99469b1283db1'
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

    q = "SELECT * from api_coin WHERE name=:coin ORDER BY date desc"

    if request.args.get('key') in API_KEYS:
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
        'value': v * n,
        'value.coin': coin2,
        'exchange_rate': v
    })


@app.route('/<coin1>/<int:n>/to/<coin2>/')
def get_exchange_value_int(coin1, coin2, n):
    return get_exchange_value(coin1, coin2, n)
