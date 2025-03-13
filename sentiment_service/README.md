# Sentiment Analysis Service

## Overview
A FastAPI microservice that fetches financial news for a stock ticker, analyzes sentiment using a lightweight LLM (DistilBERT), and stores results in PostgreSQL.

## Features
- Fetches news via NewsAPI.
- Analyzes sentiment with DistilBERT (scores: -1 to 1).
- Stores data linked to stock data from `market_data_service`.

## Usage
- Start: `uvicorn main:app --reload --port 8001`
- Endpoint: `curl http://127.0.0.1:8001/analyze/AAPL`

## Setup
- Install: `pip install fastapi uvicorn sqlalchemy psycopg2-binary requests transformers torch`
- Set `NEWS_API_KEY` in `sentiment.py`.

## Importance
Enables correlation of news sentiment with market trends, enhancing predictive insights.


## Notes
- LLM Choice: DistilBERT is used for simplicity. For LLaMA 2 or GPT-Neo, you’d need more setup (e.g., GPU support, model weights).
- NewsAPI: Free tier limits to 100 requests/day. Consider alternatives (e.g., web scraping) if needed.
- Correlation: stock_data_id is nullable for now; we’ll link it later when integrating services.