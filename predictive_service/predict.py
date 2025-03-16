import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sqlalchemy.orm import Session
from models import StockData, SentimentData
import pickle
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MODEL_PATH = "xgboost_model.pkl"

def fetch_training_data(db: Session, symbol: str):
    # Fetch stock data
    stock_query = db.query(StockData).filter(StockData.symbol == symbol).order_by(StockData.timestamp).all()
    if not stock_query:
        logger.warning(f"No stock data found for {symbol}")
        raise ValueError(f"No stock data found for {symbol}")
    stock_data = [(float(s.timestamp.timestamp()), float(s.close_price), int(s.volume)) for s in stock_query]
    stock_df = pd.DataFrame(stock_data, columns=["timestamp", "close_price", "volume"])
    logger.info(f"Stock DF dtypes: {stock_df.dtypes}")
    logger.info(f"Stock DF sample: {stock_df.head().to_dict()}")

    # Fetch sentiment data
    sentiment_query = db.query(SentimentData).filter(SentimentData.symbol == symbol).all()
    if not sentiment_query:
        logger.warning(f"No sentiment data found for {symbol}")
        raise ValueError(f"No sentiment data found for {symbol}")
    sentiment_data = [(float(s.timestamp.timestamp()), float(s.sentiment_score)) for s in sentiment_query]
    sentiment_df = pd.DataFrame(sentiment_data, columns=["timestamp", "sentiment_score"])
    logger.info(f"Sentiment DF dtypes: {sentiment_df.dtypes}")
    logger.info(f"Sentiment DF sample: {sentiment_df.head().to_dict()}")

    # Merge on timestamp (approximate nearest match)
    df = pd.merge_asof(stock_df.sort_values("timestamp"), 
                       sentiment_df.sort_values("timestamp"), 
                       on="timestamp", 
                       direction="nearest")
    logger.info(f"Merged DF dtypes: {df.dtypes}")
    logger.info(f"Merged DF sample: {df.head().to_dict()}")
    return df

def train_model(db: Session, symbol: str):
    df = fetch_training_data(db, symbol)
    if len(df) < 2:
        raise ValueError(f"Not enough data for {symbol} to train model")
    
    # Features: lagged close price, volume, sentiment
    df["lag1_close"] = df["close_price"].shift(1)
    df["lag1_sentiment"] = df["sentiment_score"].shift(1)
    df = df.dropna()
    
    X = df[["lag1_close", "volume", "lag1_sentiment"]]
    y = df["close_price"]
    
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    
    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model

def predict_next_price(db: Session, symbol: str):
    if not os.path.exists(MODEL_PATH):
        model = train_model(db, symbol)
    else:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    
    df = fetch_training_data(db, symbol)
    if len(df) < 1:
        raise ValueError(f"No data for {symbol} to predict")
    
    latest = df.iloc[-1]
    X_new = np.array([[latest["close_price"], latest["volume"], latest["sentiment_score"]]])
    prediction = model.predict(X_new)[0]
    return prediction