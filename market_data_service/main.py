from fastapi import FastAPI, Depends, HTTPException
from database import Base, engine, get_db
from ingestion import save_stock_data, fetch_stock_data
from sqlalchemy.orm import Session
import aiocache
import asyncio
import socketio
from datetime import datetime
import random

# Create FastAPI app for HTTP endpoints
app = FastAPI(title="Market Data Service")
Base.metadata.create_all(bind=engine)

# Configure aiocache with Redis
aiocache.caches.set_config({
    "default": {
        "cache": "aiocache.RedisCache",
        "endpoint": "localhost",
        "port": 6379,
        "timeout": 300
    }
})

# Create Socket.IO server for WebSocket events
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
# Wrap the FastAPI app with Socket.IO
app.mount('/socket.io', socketio.ASGIApp(sio, other_asgi_app=app))

# HTTP endpoint for ingesting stock data
@app.get("/ingest/{symbol}")
async def ingest_data(symbol: str, db: Session = Depends(get_db)):
    try:
        await save_stock_data(db, symbol)
        return {"message": f"Data for {symbol} ingested successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# WebSocket event handlers for debugging
@sio.event
async def connect(sid, environ):
    origin = environ.get('HTTP_ORIGIN', 'Unknown')
    print(f"Client connected: {sid}, Origin: {origin}")
    await sio.emit('connect_response', {'message': 'Connected to server'}, to=sid)
    return True  # Explicitly allow the connection

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

# Simulate real-time stock price updates via WebSocket
async def simulate_stock_updates(symbol, db):
    print(f"Starting stock update simulation for {symbol}...")
    while True:
        try:
            print(f"Fetching stock data for {symbol}...")
            data = await fetch_stock_data(symbol)
            latest_price = data['Close'].iloc[-1]
            fluctuation = latest_price * 0.001 * (0.5 - random.random())  # ±0.1%
            new_price = latest_price + fluctuation
            timestamp = datetime.utcnow().isoformat()
            print(f"Emitting stock update: {symbol}, Price: {new_price}, Timestamp: {timestamp}")
            await sio.emit('stock_update', {'symbol': symbol, 'price': new_price, 'timestamp': timestamp})
            await asyncio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            print(f"Error in stock update simulation: {str(e)}")
            await asyncio.sleep(5)

# Run the simulation when the app starts
@app.on_event("startup")
async def startup_event():
    print("Starting WebSocket simulation on startup...")
    asyncio.create_task(simulate_stock_updates("AAPL", next(get_db())))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)