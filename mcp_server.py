"""Coinbin MCP server.

Exposes the same keyless crypto data as MCP tools so LLM agents can use it
directly. Run it over stdio:

    uv run --extra agent python mcp_server.py

Requires the optional `agent` dependency group (the `mcp` SDK).
"""

from scraper import Coin, get_coins, price_in, convert_to_decimal

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    raise SystemExit(
        "The MCP SDK is not installed. Install the agent extra:\n"
        "    uv sync --extra agent"
    )


mcp = FastMCP("coinbin")


@mcp.tool()
def get_price(coin: str, vs: str = "usd") -> dict:
    """Current price and market data for a coin (e.g. 'btc'), in USD by default.

    Pass `vs` (e.g. 'eur', 'gbp', 'btc') to also get the price in another
    currency.
    """
    c = Coin(coin.lower())
    result = {
        "ticker": c.ticker,
        "name": c.name,
        "rank": c.rank,
        "usd": float(c.usd) if c.usd is not None else None,
        "btc": float(c.btc) if c.btc is not None else None,
        "market_cap": c.market_cap,
        "volume_24h": c.volume_24h,
        "change_24h": c.change_24h,
        "ath": c.ath,
    }
    vs = vs.lower()
    if vs != "usd":
        p = price_in(coin.lower(), vs)
        if p is not None:
            result["vs"] = vs
            result["vs_price"] = float(convert_to_decimal(p))
    return result


@mcp.tool()
def convert(amount: float, from_coin: str, to_coin: str) -> dict:
    """Convert an amount of one coin into another (e.g. 2 btc -> eth)."""
    c = Coin(from_coin.lower())
    rate = c.value(to_coin.lower())
    return {
        "from": from_coin.lower(),
        "to": to_coin.lower(),
        "amount": amount,
        "exchange_rate": float(rate),
        "value": float(convert_to_decimal(rate * convert_to_decimal(amount))),
    }


@mcp.tool()
def list_coins(limit: int = 50) -> list:
    """List the top coins by market cap (ticker, name, rank, usd)."""
    coins = list(get_coins().values())[:limit]
    return [
        {
            "ticker": c["ticker"],
            "name": c["name"],
            "rank": c["rank"],
            "usd": float(c["usd"]) if c["usd"] is not None else None,
        }
        for c in coins
    ]


if __name__ == "__main__":
    mcp.run()
