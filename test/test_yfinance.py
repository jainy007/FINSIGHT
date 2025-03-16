import yfinance as yf

symbol = "AAPL"
stock = yf.Ticker(symbol)
data = stock.history(period="1d")
print(data)