// dashboard_service/src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import StockChart from './StockChart';
import SentimentChart from './SentimentChart';
import io from 'socket.io-client';

const Dashboard = () => {
  const [ticker, setTicker] = useState('AAPL');
  const [stockData, setStockData] = useState([]);
  const [sentimentData, setSentimentData] = useState([]);
  const [predictions, setPredictions] = useState({});

  // Initialize Socket.IO client
  const socket = io('http://localhost:8000', {
    path: '/socket.io',
    transports: ['websocket'],
    withCredentials: true,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
  });

  useEffect(() => {
    window.consoleMessages = [];
    const originalLog = console.log;
    console.log = function (...args) {
      window.consoleMessages.push(args.join(' '));
      originalLog.apply(console, args);
    };

    console.log('Socket connecting to:', 'http://localhost:8000/socket.io');
    socket.on('connect', () => {
      console.log('Socket connected!');
    });
    socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error.message);
    });
    socket.on('connect_response', (data) => {
      console.log('Server response:', data);
    });
    socket.on('stock_update', (data) => {
      console.log('Real-time stock update received:', data);
      setStockData((prevData) => {
        const newData = [...prevData, {
          timestamp: data.timestamp,
          close_price: data.price,
          volume: 0, // Placeholder
        }];
        console.log('Updated stock data:', newData);
        return newData;
      });
    });

    return () => {
      socket.disconnect();
    };
  }, [socket]);

  const fetchData = async () => {
    console.log('fetchData called with ticker:', ticker);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const stockResponse = await axios.get(`http://127.0.0.1:5000/db/stock/${ticker}`, { timeout: 15000 });
      console.log('Stock Data Response:', stockResponse.data);
      setStockData(stockResponse.data);

      const sentimentResponse = await axios.get(`http://127.0.0.1:5000/db/sentiment/${ticker}`, { timeout: 15000 });
      console.log('Sentiment Data Response:', sentimentResponse.data);
      setSentimentData(sentimentResponse.data);

      const predictionResponse = await axios.get(`http://127.0.0.1:8002/predict/${ticker}`, { headers, timeout: 15000 });
      console.log('Prediction Response:', predictionResponse.data);
      setPredictions(predictionResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error.message);
      if (error.response) {
        console.error('Error response:', error.response.data);
      }
    }
  };

  useEffect(() => {
    console.log('useEffect triggered for ticker:', ticker);
  }, [ticker]);

  useEffect(() => {
    console.log('Stock Data Updated:', stockData);
  }, [stockData]);

  useEffect(() => {
    console.log('Sentiment Data Updated:', sentimentData);
  }, [sentimentData]);

  useEffect(() => {
    console.log('Predictions Updated:', predictions);
  }, [predictions]);

  const handleFetchClick = () => {
    console.log('Fetch Data button clicked');
    fetchData();
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Financial Insights Dashboard</h2>
      <div>
        <input
          type="text"
          value={ticker}
          onChange={(e) => {
            console.log('Ticker changed to:', e.target.value.toUpperCase());
            setTicker(e.target.value.toUpperCase());
          }}
          placeholder="Enter ticker (e.g., AAPL)"
          style={{ marginRight: '10px', padding: '5px' }}
        />
        <button onClick={handleFetchClick} style={{ padding: '5px 10px' }}>
          Fetch Data
        </button>
      </div>
      <div style={{ marginTop: '20px' }}>
        <div className="stock-chart-container">
          <StockChart stockData={stockData} predictions={predictions} />
        </div>
        <SentimentChart sentimentData={sentimentData} />
        <div style={{ marginTop: '20px' }}>
          <h3>Raw Data</h3>
          <p id="stock-data">Stock Data: {stockData.length > 0 ? `${stockData.length} entries` : 'None'}</p>
          <p id="sentiment-data">Sentiment Data: {sentimentData.length > 0 ? `${sentimentData.length} entries` : 'None'}</p>
          <p id="predictions">Predictions: {predictions.predicted_close ? predictions.predicted_close : 'None'}</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;