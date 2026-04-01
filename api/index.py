from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/market/indices")
def get_indices():
    r = []
    for s, n in [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY"), ("^BSESN", "SENSEX")]:
        try:
            t = yf.Ticker(s)
            h = t.history(period="5d")
            if len(h) >= 2:
                c, p = float(h['Close'].iloc[-1]), float(h['Close'].iloc[-2])
                chg, chgp = c-p, ((c-p)/p)*100
                r.append({'name': n, 'price': round(c, 2), 'change': round(chg, 2), 'pct': round(chgp, 2)})
        except:
            pass
    return r

@app.get("/api/market/movers")
def get_top_movers():
    nifty50_symbols = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
            "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS"
    ] # Simplified for fast Vercel load time, otherwise 50 takes > 10s easily 
    
    data_list = []
    
    for symbol in nifty50_symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
                
                info = ticker.info
                company_name = info.get('longName', info.get('shortName', symbol.replace('.NS', '')))
                
                data_list.append({
                    'Symbol': symbol.replace('.NS', ''),
                    'Company': company_name,
                    'Price': round(current_price, 2),
                    'Change': round(change, 2),
                    'Pct': round(change_pct, 2)
                })
        except:
            continue
            
    df = pd.DataFrame(data_list)
    if df.empty: return {"gainers": [], "losers": []}
    
    df_sorted = df.sort_values('Pct', ascending=False)
    gainers = df_sorted.head(5).to_dict(orient="records")
    losers = df_sorted.tail(5).sort_values('Pct').to_dict(orient="records")
    
    return {"gainers": gainers, "losers": losers}

@app.get("/api/stock/analyze")
def analyze_stock(ticker: str):
    try:
        sym = f"{ticker.upper()}.NS"
        stock = yf.Ticker(sym)
        hist = stock.history(period="6mo", interval="1d")
        
        if hist.empty:
            return {"error": "No data found"}
            
        hist["RSI"] = ta.momentum.RSIIndicator(close=hist["Close"], window=14).rsi()
        macd_ind = ta.trend.MACD(close=hist["Close"])
        hist["MACD"] = macd_ind.macd()
        
        latest = hist.iloc[-1]
        
        return {
            "symbol": ticker,
            "price": round(latest["Close"], 2),
            "rsi": round(latest["RSI"], 2) if not np.isnan(latest["RSI"]) else None,
            "macd": round(latest["MACD"], 2) if not np.isnan(latest["MACD"]) else None
        }
    except Exception as e:
        return {"error": str(e)}