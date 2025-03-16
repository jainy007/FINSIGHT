# FINSIGHT Setup Guide

This guide outlines the steps to set up the FINSIGHT project using Docker Compose. FINSIGHT is a microservices-based financial insights platform with services for market data, sentiment analysis, predictive modeling, and a dashboard frontend.

## Prerequisites

- **Docker**: Ensure Docker is installed (version 20.10 or later recommended).
- **Docker Compose**: Ensure Docker Compose is installed (version 2.x recommended).
- **Git**: For cloning the repository.
- **Internet Access**: Required for downloading dependencies and stock data.

## Project Structure
FINSIGHT/
├── market_data_service/
│   ├── Dockerfile
│   ├── main.py
│   ├── ingest.py
│   ├── database.py
│   ├── models.py
│   └── requirements.txt
├── sentiment_service/
│   ├── Dockerfile
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── requirements.txt
├── predictive_service/
│   ├── Dockerfile
│   ├── main.py
│   ├── predict.py
│   ├── database.py
│   ├── models.py
│   └── requirements.txt
├── dashboard_service/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   └── public/
├── docker-compose.yml
└── README.md



## Setup Steps

1. **Clone the Repository**
```bash
   git clone <repository-url>
   cd FINSIGHT
```
2. Build Docker images
```bash
docker compose build
```
This builds images for all services based on their Dockerfiles.

3. **Start the Services**
```bash
docker-compose up -d
``` 

Runs all services in detached mode. Wait a minute for initialization.

4. **Verify Services**

- Check running containers:

``` docker ps ```

Expected: postgres, redis, market_data_service, sentiment_service, predictive_service, dashboard_service.

5. **Check logs for errors:**

``` docker compose logs ``` for all services
``` docker comopse logs predictive_service``` filtered logs for predictive service only

6. **Initialize Data**
- Ingest stock data for AAPL:

``` curl http://localhost:8000/ingest/AAPL ```
- Analyze sentiment for AAPL:

``` curl http://localhost:8001/analyze/AAPL ```

- Train the predictive model:

``` curl http://localhost:5000/train/AAPL``` 

## Troubleshooting
- Service Fails to Start: Check logs (docker compose logs <service_name>).
- No Data: Ensure ingestion endpoints are called and check the database:
```
docker exec -it <postgres_container_name> psql -U postgres -d market_data
SELECT COUNT(*) FROM stock_data WHERE symbol = 'AAPL';
```

- Cache Issues: Clear Redis cache:

``` docker exec -it <redis_container_name> redis-cli FLUSHALL``` 