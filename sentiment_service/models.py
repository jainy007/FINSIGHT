from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from database import Base

# Define StockData (duplicate from market_data_service for now)
class StockData(Base):
    __tablename__ = "stock_data"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)

# Define SentimentData with foreign key to StockData
class SentimentData(Base):
    __tablename__ = "sentiment_data"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    news_title = Column(String)
    sentiment_score = Column(Float)  # -1 (negative) to 1 (positive)
    timestamp = Column(DateTime)
    stock_data_id = Column(Integer, ForeignKey("stock_data.id"), nullable=True)