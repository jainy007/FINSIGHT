import argparse
import requests
import pandas as pd
import matplotlib.pyplot as plt
import psycopg2
from psycopg2.extras import RealDictCursor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
import numpy as np
from datetime import timedelta
from matplotlib.dates import DateFormatter

# Configuration
PREDICTIVE_URL = "http://127.0.0.1:5000/predict/"
DB_CONFIG = {
    "dbname": "market_data",
    "user": "postgres",
    "password": "password",  # Replace with your PostgreSQL password
    "host": "localhost",
    "port": "5432"
}

def fetch_actual_data(ticker):
    """Fetch historical stock data from PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT timestamp, close_price, volume 
            FROM stock_data 
            WHERE symbol = %s 
            ORDER BY timestamp ASC
        """
        cursor.execute(query, (ticker,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not rows:
            print(f"No historical data found for {ticker}")
            return None
        return pd.DataFrame(rows)
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None

def fetch_sentiment_data(ticker):
    """Fetch sentiment data from PostgreSQL."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT timestamp, sentiment_score 
            FROM sentiment_data 
            WHERE symbol = %s 
            ORDER BY timestamp ASC
        """
        cursor.execute(query, (ticker,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not rows:
            print(f"No sentiment data found for {ticker}")
            return pd.DataFrame({"timestamp": [], "sentiment_score": []})
        return pd.DataFrame(rows)
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return pd.DataFrame({"timestamp": [], "sentiment_score": []})

def train_and_predict(df_stock, df_sentiment, train_end_idx):
    """Train model on data up to train_end_idx and predict the next day."""
    # Merge stock and sentiment data
    df = pd.merge_asof(df_stock.sort_values("timestamp"), 
                       df_sentiment.sort_values("timestamp"), 
                       on="timestamp", 
                       direction="nearest", 
                       tolerance=pd.Timedelta("7d"))  # Relaxed to 7 days
    print(f"After merge for idx {train_end_idx}, df shape: {df.shape}")
    
    # Fill missing sentiment scores with 0 (neutral)
    df["sentiment_score"] = df["sentiment_score"].fillna(0)
    
    if train_end_idx >= len(df) - 1:
        print(f"Index {train_end_idx} exceeds data length {len(df)}")
        return None
    
    # Training data up to train_end_idx
    train_df = df.iloc[:train_end_idx + 1].copy()
    test_df = df.iloc[train_end_idx + 1].copy()
    
    # Features: lagged close price, volume, sentiment
    train_df["lag1_close"] = train_df["close_price"].shift(1)
    train_df["lag1_sentiment"] = train_df["sentiment_score"].shift(1)
    
    # Fill missing lagged values with the first available value or 0
    train_df["lag1_close"] = train_df["lag1_close"].fillna(train_df["close_price"].iloc[0])
    train_df["lag1_sentiment"] = train_df["lag1_sentiment"].fillna(0)
    
    print(f"Training data shape for idx {train_end_idx}: {train_df.shape}")
    
    if len(train_df) < 1:
        print("Not enough data after lagging")
        return None
    
    X_train = train_df[["lag1_close", "volume", "lag1_sentiment"]]
    y_train = train_df["close_price"]
    
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)
    
    # Predict the next day
    X_test = np.array([[test_df["close_price"], test_df["volume"], test_df["sentiment_score"]]])
    prediction = model.predict(X_test)[0]
    print(f"Prediction for idx {train_end_idx}: {prediction}")
    return prediction

def plot_sanity_check(actual_df, predicted_prices, ticker):
    """Plot actual data and overlay all predicted prices."""
    if actual_df is None or not predicted_prices:
        print("Cannot plot due to missing data.")
        return
    
    actual_df["timestamp"] = pd.to_datetime(actual_df["timestamp"])
    
    # Align predicted prices with timestamps (shifted one day forward)
    predicted_timestamps = actual_df["timestamp"].iloc[1:].values
    # Ensure predicted_prices matches the length of predicted_timestamps
    predicted_prices = predicted_prices[:len(predicted_timestamps)]
    
    plt.figure(figsize=(12, 6))
    
    # Plot actual closing prices
    plt.plot(actual_df["timestamp"], actual_df["close_price"], 
             color="blue", label="Actual Close Price", marker="o", markersize=5)
    
    # Plot predicted prices
    plt.plot(predicted_timestamps, predicted_prices, 
             color="red", label="Predicted Close Price", linestyle="--", marker="*", markersize=10)
    
    # Add a vertical line to mark the prediction start
    plt.axvline(x=actual_df["timestamp"].iloc[0], color="gray", linestyle=":", label="Prediction Start", alpha=0.5)
    
    # Customize plot
    plt.title(f"Stock Price Trend and Predictions for {ticker}", fontsize=14, pad=20)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Close Price", fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # Calculate and print MAE
    mae = mean_absolute_error(actual_df["close_price"].iloc[1:], predicted_prices)
    print(f"Mean Absolute Error (MAE): {mae:.2f}")

def main():
    """Run the sanity check for a given ticker with 100-day predictions."""
    # Parse command-line argument
    parser = argparse.ArgumentParser(description="Sanity check for stock price predictions over 100 days.")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol (e.g., AAPL)")
    args = parser.parse_args()
    ticker = args.ticker.upper()

    # Ensure predictive_service is running
    print(f"Assuming predictive_service is running at {PREDICTIVE_URL[:-1]}...")
    print(f"Fetching data and generating predictions for {ticker}...")

    # Fetch actual data
    actual_df = fetch_actual_data(ticker)
    if actual_df is None:
        return
    
    # Fetch sentiment data
    sentiment_df = fetch_sentiment_data(ticker)
    
    # Generate predictions for each day
    predicted_prices = []
    for i in range(len(actual_df) - 1):  # -1 because we predict the next day
        prediction = train_and_predict(actual_df, sentiment_df, i)
        if prediction is not None:
            predicted_prices.append(prediction)
        else:
            predicted_prices.append(np.nan)  # Handle cases with insufficient data
    
    # Plot the result
    plot_sanity_check(actual_df, predicted_prices, ticker)

if __name__ == "__main__":
    main()