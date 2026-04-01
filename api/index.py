from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import requests
from bs4 import BeautifulSoup
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def read_root():
    # Read the HTML file from the public directory
    try:
        with open("public/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        return f"Error loading index.html: {str(e)}"

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
    ]
    
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

@app.get("/api/stock/search")
def search_stock(q: str = Query("")):
    try:
        # Load simple mapping or first few matches from CSV if exists
        if os.path.exists("nse_stock_list.csv"):
            df = pd.read_csv("nse_stock_list.csv")
            # First column is usually SYMBOL in NSE
            if len(df.columns) > 0:
                col_sym = df.columns[0]
                q_upper = q.upper()
                df_str = df[col_sym].astype(str)
                matches = df[df_str.str.contains(q_upper, na=False)].head(10)
                return [{"symbol": s} for s in matches[col_sym].tolist()]
    except Exception as e:
        print("Search error:", str(e))
    
    # Fallback default list
    defaults = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "BAJFINANCE"]
    return [{"symbol": s} for s in defaults if q.upper() in s]


def get_stock_analysis_logic(ticker: str):
    sym = f"{ticker.upper()}.NS"
    stock = yf.Ticker(sym)
    hist = stock.history(period="6mo", interval="1d")
    
    if hist.empty:
        return {"error": f"No data found for {ticker}"}
        
    hist["RSI"] = ta.momentum.RSIIndicator(close=hist["Close"], window=14).rsi()
    macd_ind = ta.trend.MACD(close=hist["Close"])
    hist["MACD"] = macd_ind.macd()
    hist["MACD_Signal"] = macd_ind.macd_signal()
    hist["EMA10"] = hist["Close"].ewm(span=10).mean()
    hist["EMA20"] = hist["Close"].ewm(span=20).mean()
    
    latest = hist.iloc[-1]
    
    # Generate Buy/Sell Signal
    signal = "Neutral 🟡"
    points = 0
    if not np.isnan(latest["RSI"]):
        if latest["RSI"] < 40: points += 1
        if latest["RSI"] > 70: points -= 1
    if not np.isnan(latest["MACD"]) and not np.isnan(latest["MACD_Signal"]):
        if latest["MACD"] > latest["MACD_Signal"]: points += 1
        if latest["MACD"] < latest["MACD_Signal"]: points -= 1
    if not np.isnan(latest["EMA10"]) and not np.isnan(latest["EMA20"]):
        if latest["EMA10"] > latest["EMA20"]: points += 1
        if latest["EMA10"] < latest["EMA20"]: points -= 1
    
    if points >= 2: signal = "Strong Buy 🟢"
    elif points == 1: signal = "Buy 🟢"
    elif points <= -2: signal = "Strong Sell 🔴"
    elif points == -1: signal = "Sell 🔴"
    
    return {
        "symbol": ticker.upper(),
        "price": round(latest["Close"], 2),
        "rsi": round(latest["RSI"], 2) if not np.isnan(latest["RSI"]) else None,
        "macd": round(latest["MACD"], 2) if not np.isnan(latest["MACD"]) else None,
        "ema10": round(latest["EMA10"], 2) if not np.isnan(latest["EMA10"]) else None,
        "ema20": round(latest["EMA20"], 2) if not np.isnan(latest["EMA20"]) else None,
        "signal": signal
    }

@app.get("/api/stock/analyze")
def analyze_stock(ticker: str):
    try:
        data = get_stock_analysis_logic(ticker)
        if "error" in data:
            return data
        return data
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/stocks/compare")
def compare_stocks(tickers: str):
    symbols = [t.strip() for t in tickers.split(",") if t.strip()]
    results = []
    for sym in symbols[:5]: # limit to 5 to avoid Vercel timeout
        try:
            data = get_stock_analysis_logic(sym)
            results.append(data)
        except Exception as e:
            results.append({"symbol": sym, "error": str(e)})
    return results