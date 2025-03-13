import React from 'react';
import { Scatter } from 'react-chartjs-2';
import { Chart as ChartJS, PointElement, LinearScale, TimeScale, Title, Tooltip, Legend } from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(PointElement, LinearScale, TimeScale, Title, Tooltip, Legend);

const SentimentChart = ({ sentimentData }) => {
  if (!sentimentData || sentimentData.length === 0) {
    return <div>No sentiment data available</div>;
  }

  // Calculate the time span of sentiment data
  const timestamps = sentimentData.map(item => new Date(item.timestamp));
  const minDate = Math.min(...timestamps);
  const maxDate = Math.max(...timestamps);
  const timeSpanSeconds = (maxDate - minDate) / 1000; // Time span in seconds

  const data = {
    datasets: [
      {
        label: 'Sentiment Score',
        data: sentimentData.map(item => ({ x: new Date(item.timestamp), y: item.sentiment_score || 0 })),
        backgroundColor: 'green',
        pointRadius: 5,
        pointHoverRadius: 7,
      }
    ]
  };

  const options = {
    scales: {
      x: { 
        type: 'time',
        time: { 
          unit: timeSpanSeconds > 3600 ? 'hour' : timeSpanSeconds > 60 ? 'minute' : 'second',
          tooltipFormat: 'yyyy-MM-dd HH:mm:ss.SSS'
        },
        min: minDate,
        max: maxDate,
        title: { display: true, text: 'Date' },
        ticks: { source: 'data', maxTicksLimit: 10 }
      },
      y: { 
        title: { display: true, text: 'Sentiment Score' },
        min: -1,
        max: 1
      }
    },
    plugins: {
      legend: { position: 'top' },
      tooltip: {
        callbacks: {
          label: function(context) {
            // Ensure context.parsed.x is a Date object
            const date = new Date(context.parsed.x);
            return `Sentiment: ${context.parsed.y.toFixed(2)} at ${date.toISOString()}`;
          }
        }
      }
    }
  };

  return <Scatter data={data} options={options} />;
};

export default SentimentChart;