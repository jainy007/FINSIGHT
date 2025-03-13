from fastapi import FastAPI, Depends, HTTPException
from database import Base, engine, get_db
from sentiment import save_sentiment
from sqlalchemy.orm import Session

app = FastAPI(title="Sentiment Analysis Service")
Base.metadata.create_all(bind=engine)

@app.get("/analyze/{symbol}")
async def analyze_news(symbol: str, db: Session = Depends(get_db)):
    try:
        save_sentiment(db, symbol)
        return {"message": f"Sentiment for {symbol} analyzed and saved"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))