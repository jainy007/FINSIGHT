import requests
from transformers import pipeline
from datetime import datetime, timedelta
from models import SentimentData
from sqlalchemy.orm import Session

NEWS_API_KEY = "720051823bdb4405908c88c049dbbf9d"
SENTIMENT_ANALYZER = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def fetch_news(symbol: str):
    url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}&language=en&sortBy=publishedAt&pageSize=5"
    response = requests.get(url).json()
    if response.get("status") != "ok":
        raise ValueError(f"Failed to fetch news for {symbol}")
    return response["articles"]

def analyze_sentiment(news_articles):
    results = []
    for article in news_articles:
        title = article["title"]
        result = SENTIMENT_ANALYZER(title)[0]
        score = result["score"] if result["label"] == "POSITIVE" else -result["score"]
        results.append({"title": title, "score": score})
    return results

def save_sentiment(db: Session, symbol: str, mock_date=None):
    articles = fetch_news(symbol)
    sentiments = analyze_sentiment(articles)
    for sentiment in sentiments:
        # Use mock_date if provided, else use current time
        timestamp = mock_date if mock_date else datetime.utcnow()
        sentiment_entry = SentimentData(
            symbol=symbol,
            news_title=sentiment["title"],
            sentiment_score=sentiment["score"],
            timestamp=timestamp
        )
        db.add(sentiment_entry)
    db.commit()

def get_sentiment_scores(symbol: str):
    try:
        articles = fetch_news(symbol)
        sentiments = analyze_sentiment(articles)
        avg_score = sum(s["score"] for s in sentiments) / len(sentiments) if sentiments else 0
        return avg_score
    except Exception as e:
        print(f"Error for {symbol}: {e}")
        return 0