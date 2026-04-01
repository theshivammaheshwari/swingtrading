from fastapi import FastAPI
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
    # Provide the HTML directly from FastAPI so Vercel routing isn't confused
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Swing Trading Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background-color: #f8fafc; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif; }
        </style>
    </head>
    <body class="text-slate-800">
        <header class="bg-blue-600 text-white p-4 shadow-md">
            <div class="container mx-auto flex justify-between items-center">
                <h1 class="text-2xl font-bold">📊 Swing Trading Dashboard</h1>
                <p class="text-sm opacity-80">By Shivam Maheshwari</p>
            </div>
        </header>
        <main class="container mx-auto mt-6 px-4 space-y-8">
            <section id="indices-container" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="p-6 bg-white rounded-lg shadow animate-pulse">Loading Market Data...</div>
            </section>
            <section class="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
                <h2 class="text-xl font-bold mb-4">Stock Technical Analysis</h2>
                <div class="flex gap-2 mb-4">
                    <input type="text" id="ticker-input" placeholder="Enter Ticker (e.g. RELIANCE)" class="border p-2 rounded-md flex-grow focus:outline-blue-500 uppercase" />
                    <button onclick="analyzeStock()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-semibold transition">Analyze</button>
                </div>
                <div id="analysis-result" class="hidden grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded mt-4"></div>
            </section>
            <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-lg shadow border-t-4 border-green-500">
                    <h3 class="text-lg font-bold text-green-700 mb-4">🔥 Top Gainers</h3>
                    <div id="gainers-container" class="space-y-3">Loading...</div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow border-t-4 border-red-500">
                    <h3 class="text-lg font-bold text-red-700 mb-4">⚠️ Top Losers</h3>
                    <div id="losers-container" class="space-y-3">Loading...</div>
                </div>
            </section>
        </main>
        <footer class="text-center p-6 text-slate-500 text-sm mt-10">
            ⚠️ Disclaimer: This project is developed for educational and portfolio purposes only. Not financial advice.
        </footer>
        <script>
            async function fetchIndices() {
                try {
                    const res = await fetch('/api/market/indices');
                    const data = await res.json();
                    const container = document.getElementById('indices-container');
                    container.innerHTML = data.map(idx => `
                        <div class="p-5 bg-white rounded-lg shadow flex flex-col items-center justify-center border border-slate-100">
                            <h3 class="text-slate-500 text-sm uppercase font-bold tracking-wide">${idx.name}</h3>
                            <p class="text-2xl font-bold my-1">₹${idx.price.toLocaleString('en-IN')}</p>
                            <p class="font-semibold px-2 py-0.5 rounded text-sm ${idx.change >= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'}">
                                ${idx.change > 0 ? '+' : ''}${idx.change} (${idx.pct > 0 ? '+' : ''}${idx.pct}%)
                            </p>
                        </div>
                    `).join('');
                } catch(e) { console.error('Error fetching indices', e); }
            }
            async function fetchMovers() {
                try {
                    const res = await fetch('/api/market/movers');
                    const data = await res.json();
                    const render = (items, color) => items.map(item => `
                        <div class="flex justify-between items-center border-b pb-2 last:border-0 border-slate-100">
                            <div><span class="font-bold block">${item.Symbol}</span><span class="text-xs text-slate-500">${item.Company.substring(0,25)}</span></div>
                            <div class="text-right"><span class="block font-semibold">₹${item.Price}</span><span class="text-sm font-bold text-${color}-600">${item.Pct > 0 ? '+' : ''}${item.Pct}%</span></div>
                        </div>
                    `).join('');
                    if(data.gainers && data.gainers.length > 0) {
                        document.getElementById('gainers-container').innerHTML = render(data.gainers, 'green');
                        document.getElementById('losers-container').innerHTML = render(data.losers, 'red');
                    } else {
                        document.getElementById('gainers-container').innerHTML = "<p class='text-slate-500'>Data unavailable.</p>";
                        document.getElementById('losers-container').innerHTML = "<p class='text-slate-500'>Data unavailable.</p>";
                    }
                } catch(e) { console.error('Error fetching movers', e); }
            }
            async function analyzeStock() {
                const ticker = document.getElementById('ticker-input').value;
                if(!ticker) return;
                const btn = document.querySelector('button');
                const resultBox = document.getElementById('analysis-result');
                btn.innerHTML = 'Analyzing...';
                btn.disabled = true;
                resultBox.classList.remove('hidden');
                resultBox.innerHTML = '<p class="col-span-full text-center py-4 text-blue-600 font-medium animate-pulse">Crunching numbers with yFinance...</p>';
                try {
                    const res = await fetch(`/api/stock/analyze?ticker=${ticker}`);
                    const data = await res.json();
                    if (data.error) {
                        resultBox.innerHTML = `<p class="col-span-full text-red-500 text-center">${data.error}</p>`;
                    } else {
                        resultBox.innerHTML = `
                            <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">Stock</p><p class="font-bold text-lg text-blue-700">${data.symbol.toUpperCase()}</p></div>
                            <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">Price</p><p class="font-bold text-lg">₹${data.price}</p></div>
                            <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">RSI (14)</p><p class="font-bold text-lg ${data.rsi > 70 ? 'text-red-600' : data.rsi < 30 ? 'text-green-600' : 'text-slate-700'}">${data.rsi || 'N/A'}</p></div>
                            <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">MACD</p><p class="font-bold text-lg ${data.macd > 0 ? 'text-green-600' : 'text-red-600'}">${data.macd || 'N/A'}</p></div>
                        `;
                    }
                } catch(e) {
                    resultBox.innerHTML = `<p class="col-span-full text-red-500 text-center">Failed to fetch data.</p>`;
                } finally {
                    btn.innerHTML = 'Analyze';
                    btn.disabled = false;
                }
            }
            document.addEventListener('DOMContentLoaded', () => { fetchIndices(); fetchMovers(); });
        </script>
    </body>
    </html>
    """
    return html_content

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