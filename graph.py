import graphene

import scraper


def name_to_ticker(name):
    for coin in scraper.get_coins().values():
        if coin['name'].lower() == name.lower():
            return coin['ticker']


def _as_float(v):
    return float(v) if v is not None else None


def _to_graphql_coin(c):
    """Build a GraphQL Coin from a scraper.Coin or a coins dict row."""
    if not isinstance(c, dict):
        c = {
            'ticker': c.ticker, 'name': c.name, 'rank': c.rank, 'usd': c.usd,
            'market_cap': c.market_cap, 'volume_24h': c.volume_24h,
            'change_24h': c.change_24h, 'circulating_supply': c.circulating_supply,
            'total_supply': c.total_supply, 'ath': c.ath,
        }
    return Coin(
        ticker=c['ticker'], name=c['name'], rank=c['rank'], usd=_as_float(c['usd']),
        market_cap=_as_float(c.get('market_cap')),
        volume_24h=_as_float(c.get('volume_24h')),
        change_24h=_as_float(c.get('change_24h')),
        circulating_supply=_as_float(c.get('circulating_supply')),
        total_supply=_as_float(c.get('total_supply')),
        ath=_as_float(c.get('ath')),
    )


class Coin(graphene.ObjectType):
    ticker = graphene.String()
    name = graphene.String()
    rank = graphene.Int()
    usd = graphene.Float()
    market_cap = graphene.Float()
    volume_24h = graphene.Float()
    change_24h = graphene.Float()
    circulating_supply = graphene.Float()
    total_supply = graphene.Float()
    ath = graphene.Float()


class Query(graphene.ObjectType):
    coin = graphene.Field(Coin, name=graphene.String(), ticker=graphene.String())
    recent_top_coins = graphene.List(Coin)

    def resolve_coin(root, info, name=None, ticker=None):
        if name and not ticker:
            ticker = name_to_ticker(name)
        if not ticker:
            return None
        return _to_graphql_coin(scraper.Coin(ticker))

    def resolve_recent_top_coins(root, info):
        coins = list(scraper.get_coins().values())[:10]
        return [_to_graphql_coin(c) for c in coins]


schema = graphene.Schema(query=Query)
