import React from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, LineElement, PointElement, LinearScale, TimeScale, Title, Tooltip, Legend } from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Title, Tooltip, Legend);

const StockChart = ({ stockData, predictions }) => {
  if (!stockData || stockData.length === 0) {
    return <div>No stock data available</div>;
  }

  // Determine the time range for stock data
  const timestamps = stockData.map(item => new Date(item.timestamp));
  const minDate = Math.min(...timestamps);
  const maxDate = Math.max(...timestamps);

  // Calculate the price range for the y-axis
  const closePrices = stockData.map(item => item.close_price || 0);
  const predictedClose = predictions?.predicted_close || 0;
  const allPrices = [...closePrices, predictedClose].filter(price => price !== 0);
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);

  // Add padding to stretch the y-axis range
  const padding = (maxPrice - minPrice) * 0.1; // 10% padding
  const yMin = minPrice - padding;
  const yMax = maxPrice + padding;

  // Extend maxDate by approximately 2 months (60 days)
  const twoMonthsInMs = 60 * 86_400_000; // 5,184,000,000 ms (60 days)

  // Create the predicted date (1 day after maxDate) and set time to 4:00 PM
  const lastDate = new Date(stockData[stockData.length - 1].timestamp);
  const predictedDate = new Date(lastDate.getTime() + 86400000); // 1 day after maxDate
  predictedDate.setHours(16, 0, 0, 0); // Set to 4:00 PM (16:00)

  const data = {
    datasets: [
      {
        label: 'Actual Close Price',
        data: stockData.map(item => ({ x: new Date(item.timestamp), y: item.close_price || 0 })),
        borderColor: 'blue',
        fill: false,
        pointRadius: 2,
      },
      {
        label: 'Predicted Close Price',
        data: stockData.length > 0 ? [
          ...stockData.slice(-1).map(item => ({ x: new Date(item.timestamp), y: item.close_price || 0 })),
          { x: predictedDate, y: predictions.predicted_close || 0 }
        ] : [],
        borderColor: 'red',
        borderDash: [5, 5],
        fill: false,
        pointRadius: 5,
      }
    ]
  };

  const options = {
    maintainAspectRatio: false,
    scales: {
      x: { 
        type: 'time', 
        time: { 
          unit: 'day',
          tooltipFormat: 'MMM d, yyyy h:mm a' // Display date and time in tooltip (e.g., Mar 8, 2025 4:00 PM)
        },
        min: minDate,
        max: maxDate + twoMonthsInMs,
        title: { display: true, text: 'Date' }
      },
      y: { 
        title: { display: true, text: 'Price' },
        beginAtZero: false,
        min: yMin,
        max: yMax
      }
    },
    plugins: { legend: { position: 'top' } }
  };

  return <Line data={data} options={options} />;
};

export default StockChart;