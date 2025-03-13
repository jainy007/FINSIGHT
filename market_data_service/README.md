# Market Data Ingestion Service

## Overview
The Market Data Ingestion Service is a microservice built with **FastAPI** that collects historical and live stock market data from external APIs (e.g., Yahoo Finance via `yfinance`) and stores it in a **PostgreSQL** database. This service is the foundational data pipeline for the Financial Insights Platform, enabling downstream analysis like sentiment scoring and market trend predictions.

## Importance
Data Foundation: This service provides the raw market data essential for real-time financial insights, sentiment analysis, and predictive modeling.
Scalability: Using PostgreSQL ensures the platform can handle large datasets, making it suitable for expansion (e.g., multiple tickers, historical data).
Microservices Design: As a standalone service, it decouples data ingestion from other components, improving modularity and maintainability.

## SETUP

1. **Install Deps**
```pip install fastapi uvicorn sqlalchemy psycopg2-binary requests yfinance```

2. **Configure PostgreSQL**
- Create a database: CREATE DATABASE market_data;
- Update DATABASE_URL in database.py with your credentials.

3. **Run**:
- Ensure PostgreSQL is running.
- Start the service with uvicorn.

## Features
- **Data Source**: Fetches stock data (open, high, low, close, volume) using Yahoo Finance.
- **Database**: Stores data in PostgreSQL for durability and scalability.
- **API Endpoint**: Exposes a RESTful endpoint (`/ingest/{symbol}`) to trigger data ingestion for a given stock ticker.
- **Error Handling**: Returns meaningful errors if data for a ticker is unavailable.

## Usage
1. **Start the Service**:
   ```bash
   uvicorn main:app --reload

2. **Ingest Data**:

    ```URL: http://127.0.0.1:8000/ingest/{symbol}```
    
Example: curl http://127.0.0.1:8000/ingest/AAPL
Replace {symbol} with a valid stock ticker (e.g., "AAPL" for Apple).