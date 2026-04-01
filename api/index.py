from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

# Fix Vercel Serverless read-only file system error for yfinance
os.environ["YFINANCE_CACHE_DIR"] = "/tmp"

import yfinance as yf
import pandas as pd
import numpy as np
import ta

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
    # Return the HTML directly so Vercel doesn't have filesystem path issues
    html_content = """<!DOCTYPE html>
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

    <!-- Navigation Tabs -->
    <div class="container mx-auto mt-4 px-4 border-b">
        <nav class="-mb-px flex space-x-8" aria-label="Tabs">
            <button onclick="switchTab('home')" id="tab-home" class="border-blue-500 text-blue-600 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">Stock Analysis</button>
            <button onclick="switchTab('compare')" id="tab-compare" class="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">🔀 Compare Stocks</button>
        </nav>
    </div>

    <main class="container mx-auto mt-6 px-4 pb-12">
        <div id="view-home">
            <!-- Indices Board -->
            <section id="indices-container" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div class="p-6 bg-white rounded-lg shadow animate-pulse">Loading Market Data...</div>
            </section>

            <!-- Technical Analysis Search -->
            <section class="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500 mb-8 relative">
                <h2 class="text-xl font-bold mb-4">Stock Technical Analysis (Signal generated)</h2>
                <div class="flex gap-2 mb-4 relative">
                    <input type="text" id="ticker-input" autocomplete="off" oninput="searchSuggestions()" placeholder="Type Ticker (e.g. RELIANCE, TCS)" class="border p-2 rounded-md flex-grow focus:outline-blue-500 uppercase" />
                    <button onclick="analyzeStock()" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-semibold transition">Analyze</button>
                    
                    <!-- Autocomplete dropdown -->
                    <div id="autocomplete-list" class="absolute z-10 w-full bg-white border border-gray-300 rounded-md top-12 mt-1 hidden shadow-lg max-h-48 overflow-y-auto"></div>
                </div>
                
                <div id="analysis-result" class="hidden grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 p-4 bg-slate-50 rounded mt-4">
                    <!-- Content injected here -->
                </div>
            </section>

            <!-- Top Movers -->
            <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-lg shadow border-t-4 border-green-500">
                    <h3 class="text-lg font-bold text-green-700 mb-4">🔥 Top Gainers (Nifty)</h3>
                    <div id="gainers-container" class="space-y-3">Loading...</div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow border-t-4 border-red-500">
                    <h3 class="text-lg font-bold text-red-700 mb-4">⚠️ Top Losers (Nifty)</h3>
                    <div id="losers-container" class="space-y-3">Loading...</div>
                </div>
            </section>
        </div>

        <!-- Compare View -->
        <div id="view-compare" class="hidden">
            <section class="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
                <h2 class="text-xl font-bold mb-2">Compare Stocks (Max 5)</h2>
                <p class="text-sm text-gray-500 mb-4">Enter comma-separated tickers (e.g. RELIANCE, TCS, INFY)</p>
                <div class="flex gap-2 mb-6">
                    <input type="text" id="compare-input" placeholder="RELIANCE, TCS" class="border p-2 rounded-md flex-grow focus:outline-purple-500 uppercase" />
                    <button onclick="compareStocks()" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-md font-semibold transition">Compare</button>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="min-w-full text-left text-sm whitespace-nowrap">
                        <thead class="uppercase tracking-wider border-b-2 bg-slate-50">
                            <tr>
                                <th class="px-6 py-4">Symbol</th>
                                <th class="px-6 py-4">Price</th>
                                <th class="px-6 py-4">Signal</th>
                                <th class="px-6 py-4">RSI (14)</th>
                                <th class="px-6 py-4">MACD</th>
                                <th class="px-6 py-4">EMA 10 / 20</th>
                            </tr>
                        </thead>
                        <tbody id="compare-result">
                            <tr><td colspan="6" class="text-center py-4 text-gray-500">Enter tickers and click Compare</td></tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    </main>

    <footer class="text-center p-6 text-slate-500 text-sm mt-10 bg-white border-t">
        <p>⚠️ <strong>Disclaimer / अस्वीकरण:</strong></p>
        <p class="mt-1">This project is developed for educational and portfolio purposes only. Not financial advice. Please consult a SEBI-registered adviser before investing.</p>
        <p class="mt-1">यह प्रोजेक्ट केवल शैक्षिक और पोर्टफोलियो उद्देश्यों के लिए बनाया गया है। यह निवेश या वित्तीय सलाह नहीं है। कृपया निवेश से पहले SEBI-रजिस्टर्ड सलाहकार से परामर्श करें।</p>
        
        <div class="mt-4">
            <a href="https://theshivammaheshwari.github.io/swingtrading/support.html" target="_blank" class="inline-block bg-yellow-400 hover:bg-yellow-500 text-black px-4 py-2 rounded-full font-bold shadow-md transition">
                ☕ Support the Developer / डेवलपर को सपोर्ट करें
            </a>
        </div>
    </footer>

    <script>
        // --- Navigation ---
        function switchTab(tab) {
            document.getElementById('view-home').classList.add('hidden');
            document.getElementById('view-compare').classList.add('hidden');
            document.getElementById('tab-home').className = "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm";
            document.getElementById('tab-compare').className = "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm";
            
            document.getElementById(`view-${tab}`).classList.remove('hidden');
            if (tab === 'home') document.getElementById('tab-home').className = "border-blue-500 text-blue-600 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm";
            if (tab === 'compare') document.getElementById('tab-compare').className = "border-purple-500 text-purple-600 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm";
        }

        // --- Autocomplete ---
        let debounceTimer;
        async function searchSuggestions() {
            clearTimeout(debounceTimer);
            const q = document.getElementById('ticker-input').value;
            const list = document.getElementById('autocomplete-list');
            if(q.length < 2) { list.classList.add('hidden'); return; }
            
            debounceTimer = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/stock/search?q=${q}`);
                    const data = await res.json();
                    if(data.length > 0) {
                        list.innerHTML = data.map(item => `<div class="cursor-pointer p-2 hover:bg-blue-100" onclick="selectSuggestion('${item.symbol}')">${item.symbol}</div>`).join('');
                        list.classList.remove('hidden');
                    } else {
                        list.classList.add('hidden');
                    }
                } catch(e) {}
            }, 300);
        }
        function selectSuggestion(sym) {
            document.getElementById('ticker-input').value = sym;
            document.getElementById('autocomplete-list').classList.add('hidden');
        }
        document.addEventListener('click', (e) => {
            const list = document.getElementById('autocomplete-list');
            if(e.target.id !== 'ticker-input' && list) list.classList.add('hidden');
        });

        // --- Fetch Market Data ---
        async function fetchIndices() {
            try {
                const res = await fetch('/api/market/indices');
                const data = await res.json();
                document.getElementById('indices-container').innerHTML = data.map(idx => `
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
                    <div class="flex justify-between items-center border-b pb-2 last:border-0 border-slate-100 mt-2">
                        <div><span class="font-bold block">${item.Symbol}</span><span class="text-xs text-slate-500">${item.Company.substring(0,25)}</span></div>
                        <div class="text-right"><span class="block font-semibold">₹${item.Price}</span><span class="text-sm font-bold text-${color}-600">${item.Pct > 0 ? '+' : ''}${item.Pct}%</span></div>
                    </div>
                `).join('');
                if(data.gainers.length) {
                    document.getElementById('gainers-container').innerHTML = render(data.gainers, 'green');
                    document.getElementById('losers-container').innerHTML = render(data.losers, 'red');
                }
            } catch(e) { }
        }

        // --- Single Stock Analysis ---
        async function analyzeStock() {
            const ticker = document.getElementById('ticker-input').value;
            if(!ticker) return;
            const btn = document.querySelector('button');
            const resultBox = document.getElementById('analysis-result');
            btn.innerHTML = '...'); btn.disabled = true;
            resultBox.classList.remove('hidden');
            resultBox.innerHTML = '<p class="col-span-full text-center py-4 text-blue-600 animate-pulse">Running Technical Analysis...</p>';
            try {
                const res = await fetch(`/api/stock/analyze?ticker=${ticker}`);
                const data = await res.json();
                if (data.error) { resultBox.innerHTML = `<p class="col-span-full text-red-500 text-center">${data.error}</p>`; } 
                else {
                    resultBox.innerHTML = `
                        <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">Stock</p><p class="font-bold text-lg text-blue-800">${data.symbol}</p></div>
                        <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">Price</p><p class="font-bold text-lg">₹${data.price}</p></div>
                        <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">Rec / Signal</p><p class="font-bold text-lg ${data.signal.includes('Buy') ? 'text-green-600' : data.signal.includes('Sell') ? 'text-red-600' : 'text-yellow-600'}">${data.signal}</p></div>
                        <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">RSI (14)</p><p class="font-bold text-lg ${data.rsi > 70 ? 'text-red-600' : data.rsi < 30 ? 'text-green-600' : 'text-slate-700'}">${data.rsi || 'N/A'}</p></div>
                        <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">MACD</p><p class="font-bold text-lg ${data.macd > 0 ? 'text-green-600' : 'text-red-600'}">${data.macd || 'N/A'}</p></div>
                        <div class="p-3 bg-white rounded border shadow-sm text-center"><p class="text-xs text-slate-500 font-bold uppercase mb-1">EMA 10 / 20</p><p class="font-bold text-md">${data.ema10} / ${data.ema20}</p></div>
                    `;
                }
            } catch(e) { resultBox.innerHTML = `<p class="col-span-full text-red-500">Failed to fetch data.</p>`; } 
            finally { btn.innerHTML = 'Analyze'; btn.disabled = false; }
        }

        // --- Compare Stocks ---
        async function compareStocks() {
            const tickers = document.getElementById('compare-input').value;
            if(!tickers) return;
            const resBody = document.getElementById('compare-result');
            resBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-purple-600 animate-pulse">Comparing stocks...</td></tr>`;
            try {
                const res = await fetch(`/api/stocks/compare?tickers=${tickers}`);
                const data = await res.json();
                resBody.innerHTML = data.map(row => {
                    if(row.error) return `<tr class="border-b"><td class="px-6 py-4 font-bold">${row.symbol}</td><td colspan="5" class="text-red-500 px-6 py-4">${row.error}</td></tr>`;
                    let sigColor = row.signal.includes('Buy') ? 'text-green-600 font-bold bg-green-50' : row.signal.includes('Sell') ? 'text-red-600 font-bold bg-red-50' : 'text-yellow-600 font-bold bg-yellow-50';
                    return `
                        <tr class="border-b hover:bg-slate-50">
                            <td class="px-6 py-4 font-bold border-r">${row.symbol}</td>
                            <td class="px-6 py-4">₹${row.price}</td>
                            <td class="px-6 py-4 ${sigColor} rounded">${row.signal}</td>
                            <td class="px-6 py-4">${row.rsi}</td>
                            <td class="px-6 py-4">${row.macd}</td>
                            <td class="px-6 py-4 text-xs text-gray-600">${row.ema10} <br> ${row.ema20}</td>
                        </tr>
                    `;
                }).join('');
            } catch(e) {
                resBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-red-500">Error comparing stocks</td></tr>`;
            }
        }

        // Initialize Home Data
        document.addEventListener('DOMContentLoaded', () => { fetchIndices(); fetchMovers(); });
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/api/market/indices")
def get_indices():
    try:
        symbols = ["^NSEI", "^NSEBANK", "^BSESN"]
        names = {"^NSEI": "NIFTY 50", "^NSEBANK": "BANK NIFTY", "^BSESN": "SENSEX"}
        r = []
        data = yf.download(symbols, period="5d", group_by="ticker", threads=True, progress=False)
        
        for s in symbols:
            try:
                # Based on yfinance version, single ticker 'Close' is a Series or DataFrame column
                if isinstance(data.columns, pd.MultiIndex):
                    h = data[s]['Close'].dropna()
                else:
                    if len(symbols) == 1:
                        h = data['Close'].dropna()
                    else:
                        h = data.xs(s, level='Ticker', axis=1)['Close'].dropna() if 'Ticker' in data.columns.names else data[s]['Close'].dropna()
                
                # Check for enough days backward
                if len(h) >= 2:
                    current_price = float(h.iloc[-1])
                    prev_price = float(h.iloc[-2])
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    r.append({'name': names[s], 'price': round(current_price, 2), 'change': round(change, 2), 'pct': round(change_pct, 2)})
            except Exception as e:
                print(f"Error parsing index {s}: {e}")
                pass
        
        # Fallback if bulk download fails formats
        if not r:
            for s in symbols:
                t = yf.Ticker(s)
                h = t.history(period="5d")
                if len(h) >= 2:
                    c, p = float(h['Close'].iloc[-1]), float(h['Close'].iloc[-2])
                    r.append({'name': names[s], 'price': round(c, 2), 'change': round(c-p, 2), 'pct': round(((c-p)/p)*100, 2)})
        
        if not r:
            return [{"name": "Error", "price": 0, "change": 0, "pct": 0, "error": "No data returned from YFinance"}]
        return r
    except Exception as e:
        return [{"name": "Failed", "price": 0, "change": 0, "pct": 0, "error": str(e)}]

@app.get("/api/market/movers")
def get_top_movers():
    try:
        nifty50_symbols = [
                "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
                "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS"
        ]
        data_list = []
        data = yf.download(nifty50_symbols, period="5d", group_by="ticker", threads=True, progress=False)
        
        for symbol in nifty50_symbols:
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    h = data[symbol]['Close'].dropna()
                else:
                    h = data[symbol]['Close'].dropna()
                
                if len(h) >= 2:
                    current_price = float(h.iloc[-1])
                    prev_price = float(h.iloc[-2])
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    data_list.append({
                        'Symbol': symbol.replace('.NS', ''),
                        'Company': symbol.replace('.NS', ''), # simplified for speed since info loop takes too long
                        'Price': round(current_price, 2),
                        'Change': round(change, 2),
                        'Pct': round(change_pct, 2)
                    })
            except Exception as e:
                print(f"Error parsing mover {symbol}: {e}")
                
        # If bulk fails, fallback to simple loop for 3
        if not data_list:
            for s in nifty50_symbols[:3]:
                t = yf.Ticker(s)
                h = t.history(period="5d")
                if len(h) >= 2:
                    current_price = float(h['Close'].iloc[-1])
                    prev_price = float(h['Close'].iloc[-2])
                    data_list.append({
                        'Symbol': s.replace('.NS', ''),
                        'Company': s.replace('.NS', ''),
                        'Price': round(current_price, 2),
                        'Change': round(current_price - prev_price, 2),
                        'Pct': round(((current_price - prev_price) / prev_price) * 100, 2)
                    })

        df = pd.DataFrame(data_list)
        if df.empty: return {"gainers": [{"Symbol": "No Data", "Company": "Error", "Price": 0, "Pct": 0, "Change": 0}], "losers": []}
        
        df_sorted = df.sort_values('Pct', ascending=False)
        gainers = df_sorted.head(5).to_dict(orient="records")
        losers = df_sorted.tail(5).sort_values('Pct').to_dict(orient="records")
        
        return {"gainers": gainers, "losers": losers}
    except Exception as e:
        return {"error": str(e), "gainers": [], "losers": []}

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