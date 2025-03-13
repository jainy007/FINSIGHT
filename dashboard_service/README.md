# Dashboard Service

## Overview
A React-based dashboard to visualize stock data, sentiment trends, and predictions.

## Features
- Interactive stock price chart with predictions.
- Sentiment trend chart.
- Ticker selection via input.

## Usage
- Start: `npm run dev`
- Visit: `http://localhost:5173`

## Setup
- Install Node.js and npm.
- Run: `npm install && npm install axios react-chartjs-2 chart.js`
- Ensure other services are running.

## Importance
Provides a user-friendly interface to monitor financial insights in real-time.

## Notes

- Data: Ensure your database has data for the ticker (run ingestion for AAPL if needed).
- Enhancements: You can add more charts (e.g., volume, future predictions from Step 3’s 10-day extrapolation) or improve styling.
- Real-Time: For true real-time updates, you’d need WebSockets (Step 8).