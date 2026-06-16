import graphene

import scraper


def name_to_ticker(name):
    for coin in scraper.get_coins().values():
        if coin['name'].lower() == name.lower():
            return coin['ticker']


def _to_graphql_coin(c):
    """Build a GraphQL Coin from a scraper.Coin or a coins dict row."""
    if isinstance(c, dict):
        return Coin(ticker=c['ticker'], name=c['name'], rank=c['rank'], usd=float(c['usd']))
    return Coin(ticker=c.ticker, name=c.name, rank=c.rank, usd=float(c.usd))


class Coin(graphene.ObjectType):
    ticker = graphene.String()
    name = graphene.String()
    rank = graphene.Int()
    usd = graphene.Float()


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
