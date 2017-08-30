import scraper

import graphene


def name_to_ticker(name):
    for coin in scraper.get_coins().values():
        if coin['name'].lower() == name.lower():
            return coin['ticker']



class Coin(graphene.ObjectType):
    ticker = graphene.String()
    name = graphene.String()
    rank = graphene.Int()
    usd = graphene.Float()

    @classmethod
    def from_coin(klass, c):

        klass.ticker = c.ticker
        klass.name = c.name
        klass.rank = c.rank
        klass.usd = c.usd

        return klass


class Query(graphene.ObjectType):
    coin = graphene.Field(Coin, name=graphene.String())
    # recent_top_packages = graphene.List(Package)

    @graphene.resolve_only_args
    def resolve_coin(self, name=None, ticker=None):
        if name and not ticker:
            ticker = name_to_ticker(name)

        c = Coin.from_coin(scraper.Coin(ticker))

        c.name = name
        return c

schema = graphene.Schema(query=Query)