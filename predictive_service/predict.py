import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sqlalchemy.orm import Session
from models import StockData, SentimentData
import pickle
import os

MODEL_PATH = "xgboost_model.pkl"

def fetch_training_data(db: Session, symbol: str):
    # Fetch stock data
    stock_query = db.query(StockData).filter(StockData.symbol == symbol).order_by(StockData.timestamp).all()
    stock_df = pd.DataFrame([(s.timestamp, s.close_price, s.volume) for s in stock_query], 
                            columns=["timestamp", "close_price", "volume"])
    
    # Fetch sentiment data
    sentiment_query = db.query(SentimentData).filter(SentimentData.symbol == symbol).all()
    sentiment_df = pd.DataFrame([(s.timestamp, s.sentiment_score) for s in sentiment_query], 
                                columns=["timestamp", "sentiment_score"])
    
    # Merge on timestamp (approximate nearest match)
    df = pd.merge_asof(stock_df.sort_values("timestamp"), 
                       sentiment_df.sort_values("timestamp"), 
                       on="timestamp", 
                       direction="nearest")
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