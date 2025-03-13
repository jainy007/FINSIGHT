from flask import Flask, jsonify
from flask_cors import CORS
from flask_caching import Cache
from database import Base, engine, get_db
from predict import predict_next_price, train_model
from models import StockData, SentimentData
from sqlalchemy.orm import Session

app = Flask(__name__)
CORS(app, resources={r"/db/*": {"origins": "http://localhost:5173"}, r"/predict/*": {"origins": "http://localhost:5173"}})
cache = Cache(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379'})

Base.metadata.create_all(bind=engine)

@app.route("/train/<symbol>", methods=["GET"])
@cache.cached(timeout=3600)
def train(symbol):
    db = next(get_db())
    try:
        train_model(db, symbol)
        return jsonify({"message": f"Model trained for {symbol}"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/predict/<symbol>", methods=["GET"])
@cache.cached(timeout=300)
def predict(symbol):
    db = next(get_db())
    try:
        prediction = predict_next_price(db, symbol)
        return jsonify({"symbol": symbol, "predicted_close": float(prediction)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/db/stock/<symbol>", methods=["GET"])
@cache.cached(timeout=600)
def get_stock_data(symbol):
    db = next(get_db())
    try:
        data = db.query(StockData).filter(StockData.symbol == symbol).all()
        return jsonify([{
            "timestamp": d.timestamp.isoformat(),
            "close_price": d.close_price,
            "volume": d.volume
        } for d in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/db/sentiment/<symbol>", methods=["GET"])
@cache.cached(timeout=600)
def get_sentiment_data(symbol):
    db = next(get_db())
    try:
        data = db.query(SentimentData).filter(SentimentData.symbol == symbol).all()
        return jsonify([{
            "timestamp": d.timestamp.isoformat(),
            "sentiment_score": d.sentiment_score
        } for d in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)