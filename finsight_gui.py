import matplotlib
matplotlib.use('QtAgg')  # Set Qt6 backend explicitly

import sys
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # Use QtAgg for PySide6
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar
from PySide6.QtCore import Qt
import numpy as np
from datetime import datetime

class FinsightGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FINSIGHT GUI")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Input section
        input_layout = QHBoxLayout()
        self.ticker_label = QLabel("Ticker:")
        input_layout.addWidget(self.ticker_label)
        self.ticker_input = QLineEdit("AAPL")
        input_layout.addWidget(self.ticker_input)
        self.fetch_button = QPushButton("Fetch Data")
        self.fetch_button.clicked.connect(self.fetch_data)
        input_layout.addWidget(self.fetch_button)
        layout.addLayout(input_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Canvas for graphs
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.stock_data = []
        self.sentiment_data = []
        self.prediction = None

    def fetch_data(self):
        ticker = self.ticker_input.text().upper()
        self.status_label.setText(f"Fetching data for {ticker}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
            # Fetch stock data
            self.progress_bar.setValue(33)
            stock_response = requests.get(f"http://localhost:5000/db/stock/{ticker}")
            stock_response.raise_for_status()
            self.stock_data = stock_response.json()
            self.progress_bar.setValue(66)

            # Fetch sentiment data
            sentiment_response = requests.get(f"http://localhost:5000/db/sentiment/{ticker}")
            sentiment_response.raise_for_status()
            self.sentiment_data = sentiment_response.json()
            self.progress_bar.setValue(100)

            # Fetch prediction
            predict_response = requests.get(f"http://localhost:5000/predict/{ticker}")
            predict_response.raise_for_status()
            self.prediction = predict_response.json()["predicted_close"]

            self.plot_data()
            self.status_label.setText(f"Data fetched for {ticker} successfully!")

        except requests.RequestException as e:
            self.status_label.setText(f"Error fetching data: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def plot_data(self):
        self.ax1.clear()
        self.ax2.clear()

        # Stock Prediction Graph
        if self.stock_data:
            timestamps = [datetime.fromisoformat(d["timestamp"]) for d in self.stock_data]
            close_prices = [d["close_price"] for d in self.stock_data]
            self.ax1.plot(timestamps, close_prices, label="Historical Close Price")
            self.ax1.axhline(y=self.prediction, color='r', linestyle='--', label=f"Predicted: {self.prediction:.2f}")
            self.ax1.set_title("Stock Price Prediction")
            self.ax1.set_xlabel("Date")
            self.ax1.set_ylabel("Price (USD)")
            self.ax1.legend()
            self.ax1.grid(True)

        # Sentiment Graph
        if self.sentiment_data:
            timestamps = [datetime.fromisoformat(d["timestamp"]) for d in self.sentiment_data]
            sentiment_scores = [d["sentiment_score"] for d in self.sentiment_data]
            self.ax2.plot(timestamps, sentiment_scores, label="Sentiment Score", color='g')
            self.ax2.set_title("Sentiment Analysis")
            self.ax2.set_xlabel("Date")
            self.ax2.set_ylabel("Sentiment Score")
            self.ax2.legend()
            self.ax2.grid(True)

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinsightGUI()
    window.show()
    sys.exit(app.exec())