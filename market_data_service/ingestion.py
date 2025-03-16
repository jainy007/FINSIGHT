import yfinance as yf
from datetime import datetime
from models import StockData
from sqlalchemy.orm import Session
import aiocache
import logging
import pandas as pd


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@aiocache.cached()
async def fetch_stock_data(symbol: str, period: str = "100d"):
    logger.debug(f"Fetching stock data for {symbol} with period {period}")
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)
    logger.debug(f"Data fetched: {data}")
    if data.empty:
        logger.error(f"No data found for symbol: {symbol}")
        raise ValueError(f"No data found for symbol: {symbol}")
    return data

async def save_stock_data(db: Session, symbol: str):
    data = await fetch_stock_data(symbol)
    for timestamp, row in data.iterrows():
        stock_entry = StockData(
            symbol=symbol,
            timestamp=timestamp,
            open_price=float(row["Open"]),
            high_price=float(row["High"]),
            low_price=float(row["Low"]),
            close_price=float(row["Close"]),
            volume=int(row["Volume"])
        )
        db.add(stock_entry)
    db.commit()