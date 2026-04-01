from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import requests
import json
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time

def fetch_yf_data(symbol, range_val="6mo", interval="1d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_val}&interval={interval}&_={int(time.time())}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()["chart"]["result"][0]
            meta = data.get("meta", {})
            quotes = data["indicators"]["quote"][0]
            closes = quotes.get("close", [])
            valid_closes = [c for c in closes if c is not None]
            
            current_price = meta.get("regularMarketPrice", 0)
            if current_price and valid_closes and valid_closes[-1] != current_price:
                # Append live price to closes array so indicators show current reality
                valid_closes.append(current_price)

            return {"meta": meta, "closes": valid_closes}
    except:
        pass
    return {"meta": {}, "closes": []}

def calc_ema(data, span):
    if len(data) < span: return None
    mult = 2 / (span + 1)
    ema = sum(data[:span]) / span
    for val in data[span:]:
        ema = (val - ema) * mult + ema
    return ema

def calc_macd(data):
    if len(data) < 26: return None, None
    ema12_list = []
    ema26_list = []
    mult12 = 2 / (12 + 1)
    e12 = sum(data[:12]) / 12
    for val in data[12:]:
        e12 = (val - e12) * mult12 + e12
        ema12_list.append(e12)
    mult26 = 2 / (26 + 1)
    e26 = sum(data[:26]) / 26
    for val in data[26:]:
        e26 = (val - e26) * mult26 + e26
        ema26_list.append(e26)
    macd_line = []
    diff = len(ema12_list) - len(ema26_list)
    for i in range(len(ema26_list)):
        macd_line.append(ema12_list[i+diff] - ema26_list[i])
    if len(macd_line) < 9: return None, None
    macd_signal = calc_ema(macd_line, 9)
    return macd_line[-1], macd_signal

def calc_rsi(data, period=14):
    if len(data) < period + 1: return None
    gains = []
    losses = []
    for i in range(1, len(data)):
        change = data[i] - data[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

@app.get("/api/market/indices")
def get_indices():
    results = []
    indices = [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY"), ("^BSESN", "SENSEX")]
    for sym, name in indices:
        response = fetch_yf_data(sym, "5d", "1d")
        meta = response.get("meta", {})
        
        current = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose")
        
        # fallback to closes array if meta prices not fetched
        closes = response.get("closes", [])
        if not current and closes: current = closes[-1]
        if not prev and len(closes) > 1: prev = closes[-2]
            
        if current and prev:
            chg = current - prev
            pct = (chg / prev) * 100
            results.append({"name": name, "price": round(current, 2), "change": round(chg, 2), "pct": round(pct, 2)})
    return results

@app.get("/api/market/movers")
def get_top_movers():
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "SBIN", "BHARTIARTL", "BAJFINANCE"]
    data_list = []
    for s in symbols:
        response = fetch_yf_data(f"{s}.NS", "5d", "1d")
        meta = response.get("meta", {})
        
        cur = meta.get("regularMarketPrice")
        prv = meta.get("chartPreviousClose")
        
        # fallback to closes array if meta prices not fetched
        closes = response.get("closes", [])
        if not cur and closes: cur = closes[-1]
        if not prv and len(closes) > 1: prv = closes[-2]
            
        if cur and prv:
            change = cur - prv
            pct = (change / prv) * 100
            data_list.append({"Symbol": s, "Company": s, "Price": round(cur, 2), "Change": round(change, 2), "Pct": round(pct, 2)})
    if not data_list: return {"gainers": [], "losers": []}
    data_list.sort(key=lambda x: x["Pct"], reverse=True)
    return {"gainers": data_list[:5], "losers": sorted(data_list[-5:], key=lambda x: x["Pct"])}

@app.get("/api/stock/search")
def search_stock(q: str = Query("")):
    defaults = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "LT", "BAJFINANCE"]
    return [{"symbol": s} for s in defaults if q.upper() in s]

def get_stock_analysis_logic(ticker: str):
    response = fetch_yf_data(f"{ticker.upper()}.NS", "6mo", "1d")
    closes = response.get("closes", [])
    meta = response.get("meta", {})
    
    if not closes or len(closes) < 30:
        return {"error": f"No data for {ticker}"}
        
    latest_price = meta.get("regularMarketPrice", closes[-1])
    rsi = calc_rsi(closes)
    macd, macd_sig = calc_macd(closes)
    ema10 = calc_ema(closes, 10)
    ema20 = calc_ema(closes, 20)
    
    signal = "Neutral 🟡"
    points = 0
    if rsi:
        if rsi < 40: points += 1
        if rsi > 70: points -= 1
    if macd and macd_sig:
        if macd > macd_sig: points += 1
        if macd < macd_sig: points -= 1
    if ema10 and ema20:
        if ema10 > ema20: points += 1
        if ema10 < ema20: points -= 1
    if points >= 2: signal = "Strong Buy 🟢"
    elif points == 1: signal = "Buy 🟢"
    elif points <= -2: signal = "Strong Sell 🔴"
    elif points == -1: signal = "Sell 🔴"
    
    return {
        "symbol": ticker.upper(),
        "price": round(latest_price, 2),
        "rsi": round(rsi, 2) if rsi else "N/A",
        "macd": round(macd, 2) if macd else "N/A",
        "ema10": round(ema10, 2) if ema10 else "N/A",
        "ema20": round(ema20, 2) if ema20 else "N/A",
        "signal": signal
    }

@app.get("/api/stock/analyze")
def analyze_stock(ticker: str):
    try: return get_stock_analysis_logic(ticker)
    except Exception as e: return {"error": str(e)}

@app.get("/api/stocks/compare")
def compare_stocks(tickers: str):
    symbols = [t.strip() for t in tickers.split(",") if t.strip()][:5]
    results = []
    for sym in symbols:
        try: results.append(get_stock_analysis_logic(sym))
        except Exception as e: results.append({"symbol": sym, "error": str(e)})
    return results

@app.get("/", response_class=HTMLResponse)
def read_root():
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
                if(data.gainers && data.gainers.length) {
                    document.getElementById('gainers-container').innerHTML = render(data.gainers, 'green');
                    document.getElementById('losers-container').innerHTML = render(data.losers, 'red');
                } else {
                    document.getElementById('gainers-container').innerHTML = '<p class="text-slate-500">No data could be extracted.</p>';
                    document.getElementById('losers-container').innerHTML = '<p class="text-slate-500">No data could be extracted.</p>';
                }
            } catch(e) { }
        }

        // --- Single Stock Analysis ---
        async function analyzeStock() {
            const ticker = document.getElementById('ticker-input').value;
            if(!ticker) return;
            const btn = document.querySelector('button');
            const resultBox = document.getElementById('analysis-result');
            btn.innerHTML = '...'; btn.disabled = true;
            resultBox.classList.remove('hidden');
            resultBox.innerHTML = '<p class="col-span-full text-center py-4 text-blue-600 animate-pulse">Running Technical Analysis without Ta-Lib...</p>';
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