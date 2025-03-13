# Predictive Service

## Overview
A Flask microservice that trains an XGBoost model on stock and sentiment data to predict next-day closing prices.

## Features
- Trains on historical close prices, volume, and sentiment scores.
- Predicts via REST API.

## Usage
- Start: `python main.py`
- Train: `curl http://127.0.0.1:5000/train/AAPL`
- Predict: `curl http://127.0.0.1:5000/predict/AAPL`

## Setup
- Install: `pip install flask sqlalchemy psycopg2-binary xgboost pandas numpy scikit-learn`

## Importance
Enables market trend forecasting, integrating data from ingestion and sentiment services.


## Notes

- Data: Ensure market_data_service and sentiment_service have run for your target ticker (e.g., AAPL) to populate the database.
- Model: XGBoost is simple and effective here. LSTM would need more data and preprocessing (e.g., time-series windowing).
- Prediction: Currently predicts next close price. You could modify to predict direction (up/down) with a classifier.