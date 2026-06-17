"""Price-history ingestion worker.

Fetches current prices via scraper.get_coins() and appends them to the
`api_coin` table that powers /history and /forecast. Run it on a schedule
(e.g. Heroku Scheduler, cron, or a clock dyno):

    python ingest.py

Set DATABASE_URL to the target Postgres instance. Set INGEST_PRO_URL (or
HEROKU_POSTGRESQL_TEAL_URL) to also mirror into the "pro" database. The
`api_coin` schema is created from schema.sql if it does not already exist.
"""

import os
import datetime

import records

from scraper import get_coins


def _ensure_schema(db):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'schema.sql')) as f:
        db.query(f.read())


def _insert_coins(db, coins, when):
    insert = "INSERT INTO api_coin (name, value, date) VALUES (:name, :value, :date)"
    for coin in coins.values():
        try:
            value = float(coin['usd'])
        except (TypeError, ValueError):
            continue
        db.query(insert, name=coin['name'], value=value, date=when)


def ingest():
    when = datetime.datetime.now(datetime.timezone.utc)
    coins = get_coins()

    targets = [os.environ.get('DATABASE_URL')]
    pro_url = os.environ.get('INGEST_PRO_URL') or os.environ.get('HEROKU_POSTGRESQL_TEAL_URL')
    if pro_url:
        targets.append(pro_url)

    for url in targets:
        db = records.Database(url) if url else records.Database()
        _ensure_schema(db)
        _insert_coins(db, coins, when)
        print('Ingested {} coins at {}'.format(len(coins), when.isoformat()))


if __name__ == '__main__':
    ingest()
