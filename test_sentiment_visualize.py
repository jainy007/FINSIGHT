import subprocess
import time
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
SERVICE_DIR = "sentiment_service"
BASE_URL = "http://127.0.0.1:8001/analyze/"
DB_CONFIG = {
    "dbname": "market_data",
    "user": "postgres",
    "password": "password",  # Replace with your PostgreSQL password
    "host": "localhost",
    "port": "5432"
}
FINANCE_TICKERS = {
    "Finance": [
        "JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK", "SCHW", "TROW"
    ]
}

def start_service():
    """Start the sentiment_service in a subprocess."""
    print("Starting Sentiment Analysis Service...")
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--reload", "--port", "8001"],
        cwd=SERVICE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5)  # Wait for server to initialize
    return process

def ingest_sentiment_data():
    """Ingest sentiment data for finance tickers via API."""
    print("\nIngesting sentiment data for Finance NASDAQ tickers...")
    tickers = FINANCE_TICKERS["Finance"]
    for ticker in tickers:
        url = f"{BASE_URL}{ticker}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"Success: {ticker} - {response.json()['message']}")
            else:
                print(f"Failed: {ticker} - Status {response.status_code}")
        except requests.RequestException as e:
            print(f"Error for {ticker}: {e}")
    print("Data ingestion complete.")

def fetch_sentiment_data():
    """Fetch avg sentiment and most decisive news title per ticker from PostgreSQL."""
    print("\nFetching sentiment data from database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        tickers = FINANCE_TICKERS["Finance"]
        placeholders = ",".join(["%s"] * len(tickers))
        
        # Query avg sentiment and most decisive news title
        query = f"""
            WITH ranked AS (
                SELECT 
                    symbol,
                    news_title,
                    sentiment_score,
                    ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ABS(sentiment_score) DESC) as rn
                FROM sentiment_data
                WHERE symbol IN ({placeholders})
            )
            SELECT 
                r.symbol,
                AVG(r.sentiment_score) as avg_sentiment,
                MAX(CASE WHEN r.rn = 1 THEN r.news_title END) as decisive_title,
                MAX(CASE WHEN r.rn = 1 THEN r.sentiment_score END) as decisive_score
            FROM ranked r
            GROUP BY r.symbol
        """
        cursor.execute(query, tickers)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if not rows:
            print("No data found in database for finance tickers.")
        return rows
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return []

def prepare_heatmap_data(sentiment_data):
    """Prepare data for heatmap visualization and extract decisive titles."""
    if not sentiment_data:
        return None, {}
    df = pd.DataFrame(sentiment_data)
    df.columns = ["Ticker", "Sentiment", "DecisiveTitle", "DecisiveScore"]  # Rename columns
    
    # Map tickers to sector
    df["Sector"] = "Finance"
    
    # Pivot for heatmap (only sentiment scores)
    pivot = df.pivot(index="Sector", columns="Ticker", values="Sentiment")
    
    # Extract decisive titles and scores
    decisive_info = dict(zip(df["Ticker"], zip(df["DecisiveTitle"], df["DecisiveScore"])))
    return pivot, decisive_info

def plot_heatmap(pivot, decisive_info):
    """Plot the sentiment heatmap and display decisive news titles."""
    if pivot is None:
        print("No data to plot.")
        return
    
    plt.figure(figsize=(14, 4))
    sns.heatmap(
        pivot,
        annot=True,
        cmap="RdYlGn",
        vmin=-1, vmax=1,
        fmt=".2f",
        linewidths=0.5
    )
    plt.title("Sentiment Heatmap for Finance NASDAQ Tickers")
    plt.xlabel("Ticker")
    plt.ylabel("Sector")
    plt.tight_layout()
    
    # Print decisive news titles below the plot
    print("\nMost Decisive News Titles:")
    for ticker, (title, score) in decisive_info.items():
        print(f"{ticker}: {title} (Score: {score:.2f})")
    
    plt.show()

def main():
    """Automate the full test and visualization process."""
    # Start the service
    process = start_service()

    # Ingest sentiment data
    ingest_sentiment_data()

    # Fetch data from database
    sentiment_data = fetch_sentiment_data()

    # Prepare and plot heatmap
    pivot, decisive_info = prepare_heatmap_data(sentiment_data)
    plot_heatmap(pivot, decisive_info)

    # Keep service running until interrupted
    print("\nService is running. Press Ctrl+C to stop.")
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        print("Service stopped.")

if __name__ == "__main__":
    main()