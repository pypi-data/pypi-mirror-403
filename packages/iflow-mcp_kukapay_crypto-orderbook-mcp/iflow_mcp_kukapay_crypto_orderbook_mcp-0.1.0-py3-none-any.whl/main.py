import ccxt.async_support as ccxt
import asyncio
from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, List, Optional, Tuple
import json
import pandas as pd

# Initialize FastMCP server
mcp = FastMCP("CryptoOrderbookMCP", dependencies=["ccxt", "pandas"])

# Supported exchanges
SUPPORTED_EXCHANGES = ['binance', 'kraken', 'coinbase', 'bitfinex', 'okx', 'bybit']

async def fetch_order_book_data(exchange_id: str, symbol: str, depth_percentage: float, ctx: Context) -> Tuple[Optional[ccxt.Exchange], Optional[Dict], Optional[float], Optional[float], Optional[str]]:
    """
    Common function to validate inputs, fetch order book, and calculate mid-price and price range.
    
    Args:
        exchange_id: The exchange identifier (e.g., 'binance', 'kraken')
        symbol: The trading pair (e.g., 'BTC/USDT')
        depth_percentage: Percentage range from mid-price (default: 1.0%)
        ctx: MCP context for error reporting
    
    Returns:
        Tuple containing (exchange object, order book, mid_price, price_range, error) or (None, None, None, None, error) on error.
    """
    # Validate exchange
    if exchange_id.lower() not in SUPPORTED_EXCHANGES:
        await ctx.error(f"Unsupported exchange: {exchange_id}")
        return None, None, None, None, f"Unsupported exchange: {exchange_id}"
    
    # Validate depth percentage
    if depth_percentage <= 0 or depth_percentage > 10:
        await ctx.error("Depth percentage must be between 0 and 10")
        return None, None, None, None, "Depth percentage must be between 0 and 10"

    # Initialize exchange
    try:
        exchange = getattr(ccxt, exchange_id.lower())()
    except AttributeError:
        await ctx.error(f"Failed to initialize exchange: {exchange_id}")
        return None, None, None, None, f"Failed to initialize exchange: {exchange_id}"

    try:
        # Validate symbol
        try:
            markets = await exchange.load_markets()
            if symbol not in markets:
                await ctx.error(f"Invalid symbol {symbol} for exchange {exchange_id}")
                return None, None, None, None, f"Invalid symbol {symbol} for exchange {exchange_id}"
        except Exception as e:
            await ctx.error(f"Error validating symbol {symbol}: {str(e)}")
            return None, None, None, None, f"Error validating symbol {symbol}: {str(e)}"

        # Fetch order book
        try:
            order_book = await exchange.fetch_order_book(symbol, limit=100)
        except ccxt.BaseError as e:
            await ctx.error(f"Failed to fetch order book for {symbol}: {str(e)}")
            return None, None, None, None, f"Failed to fetch order book for {symbol}: {str(e)}"

        # Calculate mid-price
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        if not bids or not asks:
            await ctx.error("Empty order book")
            return None, None, None, None, "Empty order book"

        mid_price = (bids[0][0] + asks[0][0]) / 2
        price_range = mid_price * (depth_percentage / 100)

        return exchange, order_book, mid_price, price_range, None

    except Exception as e:
        await ctx.error(f"Error fetching order book data: {str(e)}")
        return None, None, None, None, f"Error fetching order book data: {str(e)}"

@mcp.tool()
async def calculate_orderbook(exchange_id: str, symbol: str, depth_percentage: float = 1.0, ctx: Context = None) -> Dict:
    """
    Calculate the order book depth and imbalance for a given trading pair on a specified exchange.
    
    Args:
        exchange_id: The exchange identifier (e.g., 'binance', 'kraken')
        symbol: The trading pair (e.g., 'BTC/USDT')
        depth_percentage: Percentage range from mid-price to calculate depth and imbalance (default: 1.0%)
    
    Returns:
        Dictionary containing bid depth, ask depth, imbalance, mid-price, and timestamp.
    """
    exchange, order_book, mid_price, price_range, error = await fetch_order_book_data(exchange_id, symbol, depth_percentage, ctx)
    
    if error:
        return {"error": error}

    try:
        # Calculate depth and imbalance, handling both [price, vol] and [price, vol, 0] formats
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        bid_volume = sum(entry[1] for entry in bids if len(entry) >= 2 and entry[0] >= mid_price - price_range)
        ask_volume = sum(entry[1] for entry in asks if len(entry) >= 2 and entry[0] <= mid_price + price_range)

        # Calculate imbalance: (bid_volume - ask_volume) / (bid_volume + ask_volume)
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            await ctx.error("Zero total volume in order book")
            return {"error": "Zero total volume in order book"}

        imbalance = (bid_volume - ask_volume) / total_volume

        return {
            "exchange": exchange_id,
            "symbol": symbol,
            "bid_depth": bid_volume,
            "ask_depth": ask_volume,
            "imbalance": imbalance,
            "mid_price": mid_price,
            "timestamp": order_book['timestamp'] or int(asyncio.get_event_loop().time() * 1000)
        }

    except Exception as e:
        await ctx.error(f"Error calculating order book metrics: {str(e)}")
        return {"error": f"Error calculating order book metrics: {str(e)}"}
    finally:
        if exchange:
            await exchange.close()

@mcp.tool()
async def compare_orderbook(symbol: str, depth_percentage: float = 1.0, exchanges: List[str] = None, ctx: Context = None) -> str:
    """
    Compare order book depth and imbalance for a trading pair across multiple exchanges, returning a Markdown table.
    
    Args:
        symbol: The trading pair (e.g., 'BTC/USDT')
        depth_percentage: Percentage range from mid-price to calculate depth and imbalance (default: 1.0%)
        exchanges: List of exchange IDs to compare (default: all supported exchanges)
    
    Returns:
        String containing a Markdown table with exchanges as rows and bid/ask depths and imbalance as columns.
    """
    # Use all supported exchanges if none specified
    exchanges = exchanges or SUPPORTED_EXCHANGES

    # Validate inputs
    if not exchanges:
        await ctx.error("No exchanges specified")
        return json.dumps({"error": "No exchanges specified"})

    invalid_exchanges = [ex for ex in exchanges if ex.lower() not in SUPPORTED_EXCHANGES]
    if invalid_exchanges:
        await ctx.error(f"Unsupported exchanges: {invalid_exchanges}")
        return json.dumps({"error": f"Unsupported exchanges: {invalid_exchanges}"})

    if depth_percentage <= 0 or depth_percentage > 10:
        await ctx.error("Depth percentage must be between 0 and 10")
        return json.dumps({"error": "Depth percentage must be between 0 and 10"})

    results = []
    for exchange_id in exchanges:
        result = await calculate_orderbook(exchange_id, symbol, depth_percentage, ctx)
        if "error" not in result:
            results.append(result)

    # Create DataFrame for pivot table
    if not results:
        await ctx.error("No valid order book data retrieved")
        return json.dumps({"error": "No valid order book data retrieved"})

    df = pd.DataFrame(results)
    pivot_table = pd.pivot_table(
        df,
        values=['bid_depth', 'ask_depth', 'imbalance'],
        index='exchange',
        aggfunc='first'
    )

    # Convert pivot table to Markdown
    return pivot_table.to_markdown(floatfmt=(".2f", ".2f", ".4f"))

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
    