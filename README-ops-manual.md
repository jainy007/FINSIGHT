# FINSIGHT Operations Manual

This manual provides instructions for manually running the FINSIGHT application using Docker Compose, opening the browser, and interacting with the dashboard.

## Prerequisites

- FINSIGHT project set up via `readme_setup.md`.
- Docker and Docker Compose running.
- A modern web browser (e.g., Chrome, Firefox).

## Running the Application using Docker compose

1. **Start Docker Compose Services**
   - Navigate to the project directory:
     
    ```cd FINSIGHT```

2 **Launch all services:**
    ``` docker compose up --build -d ``` OR ``` docker compose up --build ``` (for RT logs)

- Wait ~1 minute for services to initialize.

- Verify Services Are Running
- Check container status:

    ```docker ps```
    - Look for:
    ```
        finsight-postgres-1
        finsight-redis-1
        finsight-market_data_service-1 (port 8000)
        finsight-sentiment_service-1 (port 8001)
        finsight-predictive_service-1 (port 5000)
        finsight-dashboard_service-1 (port 5173)
    ```
3. **View logs if needed:**

    ```docker-compose logs```

4. **Opening the Dashboard (WEBAPP)**

- Open your preferred web browser (e.g., Chrome, Firefox).
- Navigate to: http://localhost:5173
- The dashboard should load, displaying the "Financial Insights" title (verify in browser tab).
- Enter a Ticker Symbol (AAPL, TSLA)
- Fetch Data -> Click it to retrieve market data, sentiment, and predictions for AAPL.
- ***Expected:***
    -Charts (e.g., stock price, sentiment) should appear.
    -Real-time updates may start (via WebSocket from market_data_service).
    -View Results
    -Stock Data: Displays historical prices and volumes.
    -Sentiment Data: Shows sentiment scores over time.
    -Prediction: Indicates the predicted next closing price.
    

## Troubleshooting
- Dashboard Blank: Ensure all services are running and data is ingested.
- No Prediction: Check /predict/AAPL response and logs:

    ```docker compose logs predictive_service```
- Real-Time Updates Missing: Verify WebSocket logs:

    ```docker compose logs market_data_service```

## Running the Application by manually starting each microservice

1. **Redis Server**

```
redis-server --port 6379
```
```
---- Verify : 
        $ redis-cli ping
        PONG
```

2. **Market Data Service**
```
cd market_data_service
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. **Sentiment Service**
```
cd sentiment_service
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001
```

--- Verify
```
    curl http://localhost:8001/analyze/AAPL
```    
Expected: {"symbol":"AAPL","sentiment_score":0.5,...} (or similar)

4. **Predictive Service**

```
cd predictive_service
python main.py
```

--- Verify
```
    curl http://localhost:5000/predict/AAPL
```
Expected: {"symbol":"AAPL","predicted_close":220.92349243164062}

5. **Dashboard Service** BACKEND

```
cd dashboard_service
uvicorn main:app --host 0.0.0.0 --port 8002
```
--- Verify
```
    curl http://localhost:8002/health
```
Expected: {"status":"healthy"}

6. **Dashboard Service** FRONTEND

```
npm run dev
```

--- Verify

- Open `http://localhost:5173` in a browser
- Log in with testuser/testpassword (or sign up).
- After logging in, you should be redirected to the dashboard (/dashboard), where you can enter a ticker (e.g., AAPL) and fetch data

**Notes**
- The dashboard uses http://localhost:<port> for API calls (e.g., 5000 for predictions).
- Timestamps may differ between services; ensure ingestion runs before training/predicting.
- For additional symbols, replace AAPL with another ticker (e.g., MSFT).

<p align="center"><b>🚀 Enjoy exploring financial insights with FINSIGHT! ✨</b></p>