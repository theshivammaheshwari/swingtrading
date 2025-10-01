import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import re
from datetime import datetime

# Optional Plotly import (fallback safe if missing)
PLOTLY_AVAILABLE = True
try:
    import plotly.graph_objects as go
except Exception:
    PLOTLY_AVAILABLE = False

# Optional AgGrid import for pinned columns (fallback if missing)
AGGRID_AVAILABLE = True
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
except Exception:
    AGGRID_AVAILABLE = False

# ================= Streamlit Config =================
st.set_page_config(page_title="Swing Trading + Fundamentals Dashboard", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    div.stButton > button { width: 100%; margin-top: 0.55rem; }
    th, td { white-space: nowrap; }
    </style>
""", unsafe_allow_html=True)
st.title("📊 Swing Trading + Fundamentals Dashboard")

# ---------------- Sidebar: Developer + Settings ----------------
with st.sidebar:
    st.markdown("### 👨‍💻 Developer Info")
    st.markdown("**Mr. Shivam Maheshwari**")
    st.write("🔗 [LinkedIn](https://www.linkedin.com/in/theshivammaheshwari)")
    st.write("📸 [Instagram](https://www.instagram.com/theshivammaheshwari)")
    st.write("📘 [Facebook](https://www.facebook.com/theshivammaheshwari)")
    st.write("✉️ 247shivam@gmail.com")
    st.write("📱 +91-9468955596")
    st.markdown("---")
    unit_choice = st.radio("INR big values unit:", ["Crore", "Lakh"], index=0, horizontal=True)
    st.caption("Non-INR values show as K/M/B/T. All numbers display with 2 decimals.")

# ================= Helpers =================
def _safe_round(x, n=2):
    try:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return None
        return round(float(x), n)
    except Exception:
        return None

def _to_int(x):
    try:
        if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
            return None
        return int(x)
    except Exception:
        return None

def _pct(x, n=2):
    try:
        return _safe_round(100 * float(x), n) if x is not None else None
    except Exception:
        return None

def to_float(x):
    """Safely convert mixed/str values to float; returns None if not possible."""
    try:
        if x is None:
            return None
        if isinstance(x, (int, float, np.integer, np.floating)):
            val = float(x)
        elif isinstance(x, str):
            s = x.strip().replace(",", "").replace("%", "")
            if s in ("", "NA", "N/A", "-", "--", "—"):
                return None
            val = float(s)
        else:
            val = float(x)
        if np.isnan(val) or np.isinf(val):
            return None
        return val
    except Exception:
        return None

def _sanitize_ticker(t):
    t = (t or "").strip().upper()
    return re.sub(r"[^A-Z0-9\.\-]", "", t)

def indian_comma_format(number, decimals=2):
    try:
        neg = float(number) < 0
        number = abs(float(number))
        s = f"{number:.{decimals}f}"
        if "." in s:
            integer, frac = s.split(".")
        else:
            integer, frac = s, ""
        if len(integer) <= 3:
            grouped = integer
        else:
            grouped = integer[-3:]
            integer = integer[:-3]
            parts = []
            while len(integer) > 2:
                parts.append(integer[-2:])
                integer = integer[:-2]
            if integer:
                parts.append(integer)
            grouped = ",".join(reversed(parts)) + "," + grouped
        out = grouped + (("." + frac) if decimals > 0 else "")
        return f"-{out}" if neg else out
    except Exception:
        return str(number)

def format_inr_value(x, unit="Cr", decimals=2):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    factor = 1e7 if unit.lower().startswith("cr") else 1e5
    val = x / factor
    return f"{indian_comma_format(val, decimals)} {unit}"

def format_big_value(x, currency, unit_for_inr="Cr", decimals=2):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    if (currency or "").upper() == "INR":
        return format_inr_value(x, unit=unit_for_inr, decimals=decimals)
    ax = abs(float(x))
    if ax >= 1e12:
        val, suf = x / 1e12, "T"
    elif ax >= 1e9:
        val, suf = x / 1e9, "B"
    elif ax >= 1e6:
        val, suf = x / 1e6, "M"
    elif ax >= 1e3:
        val, suf = x / 1e3, "K"
    else:
        return f"{_safe_round(x, 2):.2f}"
    return f"{_safe_round(val, decimals):.2f}{suf}"

def style_2dec(df):
    return df.style.format(lambda v: f"{float(v):,.2f}" if isinstance(v, (int, float, np.floating)) else v).hide(axis="index")

def percent_str(x):
    v = _pct(x)
    return f"{v:.2f}%" if v is not None else None

# Query params helpers
def get_query_params():
    try:
        return dict(st.query_params)
    except Exception:
        return {k: v[0] if isinstance(v, list) and v else v for k, v in st.experimental_get_query_params().items()}

def set_query_params(**kwargs):
    try:
        st.query_params.clear()
        for k, v in kwargs.items():
            st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**kwargs)

# ================= Data: yfinance with .NS/.BO fallback =================
def _get_ticker_with_fallback(ticker, period="6mo", interval="1d"):
    t = _sanitize_ticker(ticker)
    tried = []
    suffixes = [""] if any(t.endswith(s) for s in [".NS", ".BO", ".NSE", ".BSE"]) else ["", ".NS", ".BO"]
    for suf in suffixes:
        sym = t if suf == "" else f"{t}{suf}"
        tried.append(sym)
        stock = yf.Ticker(sym)
        hist = stock.history(period=period, interval=interval, auto_adjust=False)
        if not hist.empty:
            return stock, hist, sym, tried
    return yf.Ticker(t), pd.DataFrame(), None, tried

def _get_info(stock):
    for getter in ("info", "get_info"):
        try:
            obj = getattr(stock, getter)
            data = obj() if callable(obj) else obj
            if isinstance(data, dict) and data:
                return data
        except Exception:
            continue
    return {}

# ================= Screener.in Fundamentals =================
@st.cache_data(show_spinner=False, ttl=60*60)
def screener_fundamentals(stock_code):
    try:
        url = f"https://www.screener.in/company/{stock_code}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        fundamentals = {}
        ratios_box = soup.find("div", class_="company-ratios")
        if ratios_box:
            rows = ratios_box.find_all("li")
            for row in rows:
                try:
                    key = row.find("span", class_="name").get_text(strip=True)
                    val = row.find("span", class_="value").get_text(strip=True)
                    fundamentals[key] = val
                except:
                    pass

        factoids = soup.find_all("li", class_="flex flex-space-between")
        for f in factoids:
            try:
                key = f.find("span", class_="name").get_text(strip=True)
                val = f.find("span", class_="value").get_text(strip=True)
                fundamentals[key] = val
            except:
                pass

        holding_section = soup.find("section", id="shareholding")
        if holding_section:
            rows = holding_section.find_all("tr")
            for row in rows:
                cols = [c.get_text(strip=True) for c in row.find_all("td")]
                if len(cols) >= 2:
                    fundamentals[cols[0]] = cols[1]
        return fundamentals
    except Exception:
        return {}

def screener_symbol_from_used(used_symbol: str) -> str:
    if not used_symbol:
        return ""
    return used_symbol.split(".")[0].upper()

# ================= Core: Technical + Fundamentals =================
@st.cache_data(show_spinner=False, ttl=900)
def super_technical_analysis(ticker: str, unit_inr="Cr"):
    stock, hist, used_ticker, tried = _get_ticker_with_fallback(ticker, period="6mo", interval="1d")
    if hist.empty:
        return None, None, used_ticker, tried, None

    hist = hist.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if hist.shape[0] < 30:
        return None, None, used_ticker, tried, None

    # Indicators
    hist["EMA10"] = hist["Close"].ewm(span=10).mean()
    hist["EMA20"] = hist["Close"].ewm(span=20).mean()
    hist["RSI"] = ta.momentum.RSIIndicator(close=hist["Close"], window=14).rsi()
    macd_ind = ta.trend.MACD(close=hist["Close"])
    hist["MACD"] = macd_ind.macd()
    hist["MACD_Signal"] = macd_ind.macd_signal()
    hist["ATR"] = ta.volatility.AverageTrueRange(
        high=hist["High"], low=hist["Low"], close=hist["Close"], window=14
    ).average_true_range()
    hist["ADX"] = ta.trend.ADXIndicator(
        high=hist["High"], low=hist["Low"], close=hist["Close"], window=14
    ).adx()
    bb = ta.volatility.BollingerBands(close=hist["Close"], window=20, window_dev=2)
    hist["BB_high"] = bb.bollinger_hband()
    hist["BB_low"] = bb.bollinger_lband()

    latest = hist.iloc[-1]
    prev = hist.iloc[-2]

    # Pivots
    P = (latest["High"] + latest["Low"] + latest["Close"]) / 3
    R1 = 2 * P - latest["Low"]
    S1 = 2 * P - latest["High"]
    R2 = P + (latest["High"] - latest["Low"])
    S2 = P - (latest["High"] - latest["Low"])
    R3 = latest["High"] + 2 * (P - latest["Low"])
    S3 = latest["Low"] - 2 * (latest["High"] - P)

    # Candle patterns
    candle_signal = "None"
    body = abs(latest["Open"] - latest["Close"])
    range_ = (latest["High"] - latest["Low"]) + 1e-9
    if (latest["Close"] > latest["Open"] and prev["Close"] < prev["Open"]
        and latest["Close"] > prev["Open"] and latest["Open"] < prev["Close"]):
        candle_signal = "Bullish Engulfing"
    elif (latest["Close"] < latest["Open"] and prev["Close"] > prev["Open"]
          and latest["Close"] < prev["Open"] and latest["Open"] > prev["Close"]):
        candle_signal = "Bearish Engulfing"
    elif (latest["High"] - latest["Low"]) > 3 * body and (latest["Close"] - latest["Low"]) / range_ > 0.6:
        candle_signal = "Hammer"
    elif (latest["High"] - latest["Low"]) > 3 * body and (latest["High"] - latest["Close"]) / range_ > 0.6:
        candle_signal = "Shooting Star"

    # Voting
    signals = []
    if latest["EMA10"] > latest["EMA20"]: signals.append("Buy")
    elif latest["EMA10"] < latest["EMA20"]: signals.append("Sell")
    if latest["RSI"] > 60: signals.append("Buy")
    elif latest["RSI"] < 40: signals.append("Sell")
    if hist["MACD"].iloc[-1] > hist["MACD_Signal"].iloc[-1]: signals.append("Buy")
    elif hist["MACD"].iloc[-1] < hist["MACD_Signal"].iloc[-1]: signals.append("Sell")
    if latest["ADX"] > 25 and latest["EMA10"] > latest["EMA20"]: signals.append("Buy")
    elif latest["ADX"] > 25 and latest["EMA10"] < latest["EMA20"]: signals.append("Sell")

    buy_votes, sell_votes = signals.count("Buy"), signals.count("Sell")
    total_votes = buy_votes + sell_votes
    if buy_votes > sell_votes: final_signal = "Buy"
    elif sell_votes > buy_votes: final_signal = "Sell"
    else: final_signal = "Hold"

    if total_votes == 0:
        strength = "Neutral"
    elif final_signal == "Buy":
        strength = f"Strong Buy ({buy_votes}/{total_votes})" if buy_votes >= 0.75 * total_votes else f"Weak Buy ({buy_votes}/{total_votes})"
    elif final_signal == "Sell":
        strength = f"Strong Sell ({sell_votes}/{total_votes})" if sell_votes >= 0.75 * total_votes else f"Weak Sell ({sell_votes}/{total_votes})"
    else:
        strength = "Neutral"

    # ATR Stoploss
    atr_val = latest["ATR"]
    stoploss = None
    if final_signal == "Buy":
        stoploss = _safe_round(latest["Close"] - 1.5 * atr_val, 2)
    elif final_signal == "Sell":
        stoploss = _safe_round(latest["Close"] + 1.5 * atr_val, 2)

    # Fibonacci (last 5 sessions)
    swing_high = hist["High"].iloc[-5:].max()
    swing_low = hist["Low"].iloc[-5:].min()
    diff = swing_high - swing_low
    fib_targets = {}
    if final_signal == "Buy":
        fib_targets["Target1 (0.618)"] = _safe_round(swing_high + 0.618 * diff, 2)
        fib_targets["Target2 (1.0)"] = _safe_round(swing_high + 1.0 * diff, 2)
    elif final_signal == "Sell":
        fib_targets["Target1 (0.618)"] = _safe_round(swing_low - 0.618 * diff, 2)
        fib_targets["Target2 (1.0)"] = _safe_round(swing_low - 1.0 * diff, 2)

    tech = {
        "Ticker": used_ticker,
        "Date": str(pd.to_datetime(hist.index[-1]).date()),
        "Open": _safe_round(latest["Open"], 2),
        "High": _safe_round(latest["High"], 2),
        "Low": _safe_round(latest["Low"], 2),
        "Close": _safe_round(latest["Close"], 2),
        "Volume": _to_int(latest["Volume"]),
        "EMA10": _safe_round(latest["EMA10"], 2),
        "EMA20": _safe_round(latest["EMA20"], 2),
        "RSI": _safe_round(latest["RSI"], 2),
        "MACD": _safe_round(latest["MACD"], 2),
        "MACD_Signal": _safe_round(latest["MACD_Signal"], 2),
        "ATR": _safe_round(atr_val, 2),
        "ADX": _safe_round(latest["ADX"], 2),
        "BB_High": _safe_round(hist["BB_high"].iloc[-1], 2),
        "BB_Low": _safe_round(hist["BB_low"].iloc[-1], 2),
        "CandlePattern": candle_signal,
        "Signal": final_signal,
        "Strength": strength,
        "Stoploss": stoploss,
        "Fibonacci_Targets": fib_targets,
        "Pivot": _safe_round(P, 2),
        "R1": _safe_round(R1, 2),
        "R2": _safe_round(R2, 2),
        "R3": _safe_round(R3, 2),
        "S1": _safe_round(S1, 2),
        "S2": _safe_round(S2, 2),
        "S3": _safe_round(S3, 2),
    }

    # Fundamentals (display trimmed as per your request)
    info = _get_info(stock)
    currency = info.get("currency")
    market_cap = info.get("marketCap")
    enterprise_val = info.get("enterpriseValue")
    free_cf = info.get("freeCashflow")
    total_debt = info.get("totalDebt")
    total_cash = info.get("totalCash")

    market_cap_n = to_float(market_cap)
    enterprise_val_n = to_float(enterprise_val)
    free_cf_n = to_float(free_cf)
    total_debt_n = to_float(total_debt)
    total_cash_n = to_float(total_cash)

    roe_raw = info.get("returnOnEquity")
    dte_raw = info.get("debtToEquity")
    pm_raw  = info.get("profitMargins")
    revg_raw = info.get("revenueGrowth")

    roe_n = to_float(roe_raw)
    dte_n = to_float(dte_raw)
    pm_n  = to_float(pm_raw)
    revg_n = to_float(revg_raw)
    fcf_yield_n = (free_cf_n / market_cap_n) if (free_cf_n is not None and market_cap_n and market_cap_n != 0) else None

    fundamentals = {
        "Company": info.get("longName") or info.get("shortName"),
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
        "Country": info.get("country"),
        "Currency": currency,

        "MarketCap": format_big_value(market_cap, currency, unit_for_inr=unit_inr),
        "EnterpriseValue": format_big_value(enterprise_val, currency, unit_for_inr=unit_inr),

        "PE_TTM": _safe_round(info.get("trailingPE"), 2),
        "Forward_PE": _safe_round(info.get("forwardPE"), 2),
        # REMOVED: PEG
        "PriceToBook": _safe_round(info.get("priceToBook"), 2),
        "EV_to_EBITDA": _safe_round(info.get("enterpriseToEbitda"), 2),

        "DividendRate": _safe_round(info.get("dividendRate") or info.get("trailingAnnualDividendRate"), 2),
        "DividendYield": percent_str(to_float(info.get("dividendYield"))),
        "PayoutRatio": percent_str(to_float(info.get("payoutRatio"))),

        "RevenueGrowth": percent_str(revg_n),
        "EarningsGrowth": percent_str(to_float(info.get("earningsGrowth"))),
        "ProfitMargin": percent_str(pm_n),
        "OperatingMargin": percent_str(to_float(info.get("operatingMargins"))),
        "GrossMargin": percent_str(to_float(info.get("grossMargins"))),

        # REMOVED from display: ROE, ROA, CurrentRatio, QuickRatio, FreeCashFlow, FCF_Yield
        "DebtToEquity": _safe_round(dte_n, 2),

        "TotalDebt": format_big_value(total_debt, currency, unit_for_inr=unit_inr),
        "TotalCash": format_big_value(total_cash, currency, unit_for_inr=unit_inr),

        "Beta": _safe_round(info.get("beta"), 2),
        "CurrentPrice": _safe_round(info.get("currentPrice") or latest["Close"], 2),
        "HighLow52W": f"{_safe_round(info.get('fiftyTwoWeekHigh'),2)} / {_safe_round(info.get('fiftyTwoWeekLow'),2)}" if info.get("fiftyTwoWeekHigh") and info.get("fiftyTwoWeekLow") else None,
        "BookValue": _safe_round(info.get("bookValue"), 2),
        "AsOf": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    # Scoring (kept; independent from display)
    flags = []
    score = 0
    max_score = 6
    pe_n = to_float(info.get("trailingPE"))
    if pe_n is not None and pe_n > 0 and pe_n <= 20: score += 1; flags.append("Reasonable P/E")
    if roe_n is not None and roe_n >= 0.15: score += 1; flags.append("High ROE (>=15%)")
    if dte_n is not None and dte_n <= 150: score += 1; flags.append("Moderate Leverage")
    if pm_n is not None and pm_n >= 0.10: score += 1; flags.append("Healthy Profit Margin")
    if revg_n is not None and revg_n >= 0.10: score += 1; flags.append("Strong Revenue Growth")
    if fcf_yield_n is not None and fcf_yield_n >= 0.04: score += 1; flags.append("Attractive FCF Yield")
    fundamentals["Score"] = f"{score}/{max_score} ({'Strong' if score>=4 else ('Moderate' if score>=2 else 'Weak')})"
    fundamentals["Flags"] = flags

    return tech, fundamentals, used_ticker, tried, hist

# ================= Support/Resistance (Pivot) Chart =================
def make_sr_chart(hist: pd.DataFrame, techs: dict, lookback: int = 120):
    if not PLOTLY_AVAILABLE:
        return None
    df = hist.tail(lookback).copy()
    df["Date"] = df.index
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="OHLC", increasing_line_color="#2ca02c", decreasing_line_color="#d62728", showlegend=False
    ))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA10"], name="EMA10", line=dict(color="#1f77b4", width=1.5)))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA20"], name="EMA20", line=dict(color="#ff7f0e", width=1.5)))

    levels = [("S3", "#2ca02c"), ("S2", "#2ca02c"), ("S1", "#2ca02c"),
              ("Pivot", "#7f7f7f"), ("R1", "#d62728"), ("R2", "#d62728"), ("R3", "#d62728")]
    shapes, annotations = [], []
    x0, x1 = df["Date"].iloc[0], df["Date"].iloc[-1]
    y_min = df["Low"].min()
    y_max = df["High"].max()

    for name, color in levels:
        y = techs.get(name)
        if y is None: continue
        shapes.append(dict(type="line", xref="x", yref="y", x0=x0, x1=x1, y0=y, y1=y,
                           line=dict(color=color, width=1, dash="dot")))
        annotations.append(dict(x=x1, y=y, xref="x", yref="y",
                                text=f"{name}: {y:.2f}", showarrow=False,
                                font=dict(size=10, color=color),
                                bgcolor="rgba(255,255,255,0.6)"))
        y_min = min(y_min, y)
        y_max = max(y_max, y)

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=30, b=10),
        height=450, xaxis_rangeslider_visible=False,
        shapes=shapes, annotations=annotations,
        legend=dict(orientation="h", y=1.02, x=0)
    )
    fig.update_yaxes(tickformat=".2f", range=[y_min * 0.98, y_max * 1.02])
    return fig

# ================= Data Source: NSE stock list (optional) =================
symbol_to_name = {}
all_stock_codes = []
try:
    symbols_df = pd.read_csv("nse_stock_list.csv")
    all_stock_codes = symbols_df["Symbol"].dropna().astype(str).tolist()
    symbol_to_name = dict(zip(symbols_df["Symbol"], symbols_df["NAME OF COMPANY"]))
except Exception:
    pass

# ================= Sidebar: Compare feature (up to 10) =================
with st.sidebar:
    st.markdown("---")
    st.markdown("#### 🔀 Compare (2–10 tickers)")
    unit_inr_sidebar = "Cr" if unit_choice == "Crore" else "L"

    if all_stock_codes:
        cmp_sel = st.multiselect("Select tickers", all_stock_codes, max_selections=10)
        cmp_input_text = st.text_input("Or type comma-separated (e.g., RELIANCE, TCS, INFY)", "")
        cmp_tickers = [t.strip().upper() for t in cmp_input_text.split(",") if t.strip()] if cmp_input_text.strip() else cmp_sel
    else:
        cmp_input_text = st.text_input("Enter tickers (comma-separated)", "RELIANCE, TCS")
        cmp_tickers = [t.strip().upper() for t in cmp_input_text.split(",") if t.strip()]

    cmp_tickers = [_sanitize_ticker(t) for t in cmp_tickers]
    cmp_tickers = [t for t in cmp_tickers if t]

    if st.button("Get Compare Link (New Tab)"):
        if len(cmp_tickers) < 2 or len(cmp_tickers) > 10:
            st.warning("Please select 2 to 10 tickers.")
        else:
            qs = f"?mode=compare&tickers={','.join(cmp_tickers)}&unit={unit_inr_sidebar}"
            st.markdown(f"<a href='{qs}' target='_blank'>Open Compare View ↗️</a>", unsafe_allow_html=True)

# ================= UI: Input section (aligned button) =================
try:
    col_in1, col_in2 = st.columns([2, 1], vertical_alignment="bottom")
except TypeError:
    col_in1, col_in2 = st.columns([2, 1])

with col_in1:
    if all_stock_codes:
        default_idx = all_stock_codes.index("RELIANCE") if "RELIANCE" in all_stock_codes else 0
        user_input = st.selectbox("🔍 Search or select stock symbol:", all_stock_codes, index=default_idx)
    else:
        user_input = st.text_input("Enter stock symbol (e.g., RELIANCE, TCS, INFY, AAPL):", value="RELIANCE")

with col_in2:
    run_btn = st.button("Analyze 🚀", use_container_width=True)

# ================= Compare View (via query params) =================
def render_compare_view():
    qp = get_query_params()
    mode = (qp.get("mode") or "").lower()
    if mode != "compare":
        return False
    unit_q = (qp.get("unit") or "Cr")
    tickers_q = (qp.get("tickers") or "")
    tickers_list = [_sanitize_ticker(t) for t in tickers_q.split(",") if t.strip()]
    st.markdown(f"### 🔀 Compare Stocks: {', '.join(tickers_list)}")
    if len(tickers_list) < 2 or len(tickers_list) > 10:
        st.warning("Please provide 2–10 tickers in the URL, e.g., ?mode=compare&tickers=RELIANCE,TCS,INFY&unit=Cr")
        return True

    tech_rows = []
    fund_rows = []

    for t in tickers_list:
        techs, funds, used, tried, hist = super_technical_analysis(t, unit_inr=unit_q)
        if not techs or hist is None:
            st.error(f"Data not found for {t}. Tried: {', '.join([x for x in (tried or []) if x])}")
            continue

        scr_symbol = screener_symbol_from_used(used or t)
        scr = screener_fundamentals(scr_symbol) if scr_symbol else {}

        # Technical row
        fib = techs.get("Fibonacci_Targets", {}) or {}
        fib_str = ""
        if fib:
            t1 = fib.get("Target1 (0.618)") or fib.get("Target1(0.618)")
            t2 = fib.get("Target2 (1.0)") or fib.get("Target2(1.0)")
            if t1 is not None: fib_str += f"T1: {float(t1):.2f}"
            if t2 is not None: fib_str += (", " if fib_str else "") + f"T2: {float(t2):.2f}"

        tech_rows.append({
            "Ticker": used or t,
            "Company": funds.get("Company"),
            "Sector": funds.get("Sector"),
            "Industry": funds.get("Industry"),
            "Signal": techs["Signal"],
            "Strength": techs["Strength"],
            "Last Close": techs["Close"],
            "RSI": techs["RSI"],
            "Stoploss": techs["Stoploss"],
            "Fibonacci Targets": fib_str if fib_str else "NA",
            "Volume": techs["Volume"],
        })

        # Fundamentals row (trimmed)
        row = {
            "Ticker": used or t,
            "Company": funds.get("Company"),
            "Sector": funds.get("Sector"),
            "Industry": funds.get("Industry"),
            "Market Cap": funds.get("MarketCap"),
            "Enterprise Value": funds.get("EnterpriseValue"),
            "PE (TTM)": funds.get("PE_TTM"),
            "Price to Book": funds.get("PriceToBook"),
            "EV/EBITDA": funds.get("EV_to_EBITDA"),
            "Stock P/E": scr.get("Stock P/E") or funds.get("PE_TTM"),
            "Dividends": funds.get("DividendRate"),
            "Dividend Yield": funds.get("DividendYield"),
            "Revenue Growth": funds.get("RevenueGrowth"),
            "Earnings Growth": funds.get("EarningsGrowth"),
            "Profit Margin": funds.get("ProfitMargin"),
            "Operating Margin": funds.get("OperatingMargin"),
            "Gross Margin": funds.get("GrossMargin"),
            "ROCE": scr.get("ROCE") or scr.get("ROCE 3Yr") or scr.get("Return on capital employed"),
            "Debt to Equity": funds.get("DebtToEquity"),
            "Total Debt": funds.get("TotalDebt"),
            "Total Cash": funds.get("TotalCash"),
            "Current Price": funds.get("CurrentPrice"),
            "High / Low": scr.get("High / Low") or funds.get("HighLow52W"),
            "Book Value": scr.get("Book Value") or funds.get("BookValue"),
        }
        fund_rows.append(row)

    # Technical Comparison table (AgGrid with pinned Ticker & Company)
    if tech_rows:
        st.subheader("📊 Technical Comparison")
        df_t = pd.DataFrame(tech_rows)

        if AGGRID_AVAILABLE:
            gb_t = GridOptionsBuilder.from_dataframe(df_t)
            gb_t.configure_default_column(resizable=True, filter=True, sortable=True, min_width=120)
            gb_t.configure_column("Ticker", pinned="left", width=110)
            gb_t.configure_column("Company", pinned="left", width=220)
            # Numeric formatting
            for col in ["Last Close","RSI","Stoploss"]:
                if col in df_t.columns:
                    gb_t.configure_column(
                        col, type=["numericColumn"],
                        valueFormatter="value == null ? '' : Number(value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                    )
            if "Volume" in df_t.columns:
                gb_t.configure_column(
                    "Volume", type=["numericColumn"],
                    valueFormatter="value == null ? '' : Number(value).toLocaleString()"
                )
            gb_t.configure_grid_options(domLayout="normal")
            grid_options_t = gb_t.build()
            AgGrid(
                df_t,
                gridOptions=grid_options_t,
                theme="balham",
                fit_columns_on_grid_load=False,
                allow_unsafe_jscode=True,
                update_mode=GridUpdateMode.NO_UPDATE,
                height=420
            )
        else:
            # Fallback static table with 2-dec formatting
            for col in ["Last Close","RSI","Stoploss"]:
                if col in df_t.columns:
                    df_t[col] = df_t[col].apply(lambda v: f"{float(v):,.2f}" if isinstance(v, (int,float,np.floating)) else v)
            if "Volume" in df_t.columns:
                df_t["Volume"] = df_t["Volume"].apply(lambda v: f"{int(v):,}" if v is not None else "NA")
            st.dataframe(df_t, use_container_width=True)

    # Fundamentals Comparison with pinned columns
    if fund_rows:
        st.subheader("🏦 Fundamentals Comparison")
        keep_cols = [
            "Ticker", "Company", "Sector", "Industry",
            "Market Cap", "Enterprise Value",
            "PE (TTM)", "Price to Book", "EV/EBITDA", "Stock P/E",
            "Dividends", "Dividend Yield",
            "Revenue Growth", "Earnings Growth", "Profit Margin", "Operating Margin", "Gross Margin", "ROCE",
            "Debt to Equity", "Total Debt", "Total Cash",
            "Current Price", "High / Low", "Book Value"
        ]
        df_f = pd.DataFrame(fund_rows)
        for c in keep_cols:
            if c not in df_f.columns:
                df_f[c] = None
        df_f = df_f[keep_cols]

        if AGGRID_AVAILABLE:
            gb = GridOptionsBuilder.from_dataframe(df_f)
            gb.configure_default_column(resizable=True, filter=True, sortable=True, min_width=120)
            gb.configure_column("Ticker", pinned="left", width=110)
            gb.configure_column("Company", pinned="left", width=220)
            num_cols = ["PE (TTM)", "Price to Book", "EV/EBITDA", "Dividends", "Debt to Equity", "Current Price", "Book Value"]
            for col in num_cols:
                if col in df_f.columns:
                    gb.configure_column(
                        col, type=["numericColumn"],
                        valueFormatter="value == null ? '' : Number(value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})"
                    )
            gb.configure_grid_options(domLayout="normal")
            grid_options = gb.build()
            AgGrid(
                df_f,
                gridOptions=grid_options,
                theme="balham",
                fit_columns_on_grid_load=False,
                allow_unsafe_jscode=True,
                update_mode=GridUpdateMode.NO_UPDATE,
                height=480
            )
        else:
            st.info("Install 'streamlit-aggrid' to enable pinned columns. Showing static table for now.")
            for col in ["PE (TTM)","Price to Book","EV/EBITDA","Dividends","Debt to Equity","Current Price","Book Value"]:
                if col in df_f.columns:
                    df_f[col] = df_f[col].apply(lambda v: f"{float(v):,.2f}" if isinstance(v, (int,float,np.floating)) else v)
            st.dataframe(df_f, use_container_width=True)

    # Normalized performance chart
    perf = {}
    for t in tickers_list:
        techs, funds, used, tried, hist = super_technical_analysis(t, unit_inr=unit_q)
        if hist is not None and not hist.empty:
            c = hist["Close"].astype(float).dropna()
            if len(c) > 0:
                perf[used or t] = (c / c.iloc[0]) * 100.0
    if perf:
        st.subheader("📈 Normalized Performance (Rebased to 100)")
        norm_df = pd.DataFrame(perf)
        st.line_chart(norm_df, height=350, use_container_width=True)

    return True

# If compare mode via URL, render and stop
if render_compare_view():
    st.stop()

# ================= Run Single Ticker Analysis =================
if run_btn:
    company_name = symbol_to_name.get(user_input, "")
    unit_inr = "Cr" if unit_choice == "Crore" else "L"

    techs, funds, used, tried, hist = super_technical_analysis(user_input, unit_inr=unit_inr)

    st.markdown(f"### 📈 Swing Trading Analysis - {company_name} ({user_input})")
    if used and used != user_input:
        st.caption(f"Used symbol: {used} (tried: {', '.join([t for t in tried if t])})")

    if techs and hist is not None:
        # Key Trade Highlights
        st.subheader("🔎 Key Trade Highlights")
        key_high_data = pd.DataFrame([{
            "Candle Pattern": techs["CandlePattern"],
            "Signal": techs["Signal"],
            "Strength": techs["Strength"],
            "Last Close": techs["Close"],
            "RSI": techs["RSI"],
            "ADX": techs["ADX"],
            "ATR": techs["ATR"],
            "Stoploss": techs["Stoploss"] if techs["Stoploss"] is not None else "NA",
        }])
        st.table(style_2dec(key_high_data))

        fib = techs.get("Fibonacci_Targets", {}) or {}
        fib_df = pd.DataFrame(list(fib.items()), columns=["Target", "Price"])
        if not fib_df.empty:
            st.markdown("#### 🎯 Fibonacci Targets")
            st.table(style_2dec(fib_df))

        # Detailed Technicals
        st.subheader("📊 Detailed Technicals")
        tech_df = pd.DataFrame([
            ["Open", techs["Open"]],
            ["High", techs["High"]],
            ["Low", techs["Low"]],
            ["Close", techs["Close"]],
            ["Volume", techs["Volume"]],
            ["EMA10", techs["EMA10"]],
            ["EMA20", techs["EMA20"]],
            ["RSI", techs["RSI"]],
            ["MACD", techs["MACD"]],
            ["MACD Signal", techs["MACD_Signal"]],
            ["ATR", techs["ATR"]],
            ["ADX", techs["ADX"]],
            ["BB High", techs["BB_High"]],
            ["BB Low", techs["BB_Low"]],
            ["Pivot", techs["Pivot"]],
            ["R1", techs["R1"]],
            ["R2", techs["R2"]],
            ["R3", techs["R3"]],
            ["S1", techs["S1"]],
            ["S2", techs["S2"]],
            ["S3", techs["S3"]],
        ], columns=["Metric","Value"])
        tech_df["Value"] = tech_df["Value"].apply(
            lambda v: f"{float(v):,.2f}" if isinstance(v, (int, float, np.floating)) else (f"{int(v):,}" if isinstance(v, (int, np.integer)) else v)
        )
        tech_df.index = range(1, len(tech_df)+1)
        st.dataframe(tech_df, use_container_width=True)

        # Simple Price Chart
        st.subheader("📉 Price Chart (6 months)")
        chart_df = hist[["Close","EMA10","EMA20"]].copy()
        chart_df.columns = ["Close","EMA10","EMA20"]
        st.line_chart(chart_df, height=300, use_container_width=True)

        # Support & Resistance Chart
        st.subheader("🧱 Support & Resistance (Pivot) Chart")
        fig = make_sr_chart(hist, techs, lookback=120)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("Plotly not installed. Install plotly to see the S/R candlestick chart.")

    else:
        st.error("❌ No technical data found. Tried: " + ", ".join([t for t in (tried or []) if t]))

    # Fundamentals (trimmed display)
    st.markdown(f"### 🏦 Fundamentals - {company_name} ({user_input})")
    if funds:
        f_score = funds.get("Score", "NA")
        flags = funds.get("Flags", [])
        st.write(f"Overall Score: {f_score}")
        if flags:
            st.write("Highlights: " + " • ".join(flags))

        exclude_keys = {"Score","Flags"}
        fund_items = [(k, v) for k, v in funds.items() if k not in exclude_keys]
        df_fund = pd.DataFrame(fund_items, columns=["Metric","Value"])
        def fmt_val(x):
            try:
                if isinstance(x, (int, float, np.floating)):
                    return f"{float(x):,.2f}"
                return x
            except:
                return x
        df_fund["Value"] = df_fund["Value"].apply(fmt_val)
        df_fund.index = range(1, len(df_fund)+1)
        st.dataframe(df_fund, use_container_width=True)
    else:
        st.warning("No yfinance fundamentals available for this ticker.")

    # Screener snapshot
    st.markdown(f"### 📄 Screener.in Snapshot - {company_name} ({user_input})")
    scr = screener_fundamentals(user_input)
    if scr:
        df_scr = pd.DataFrame(list(scr.items()), columns=["Metric","Value"])
        df_scr.index = range(1, len(df_scr)+1)
        st.dataframe(df_scr, use_container_width=True)
    else:
        st.info("Could not fetch Screener.in data (might not exist for this symbol or network blocked).")

else:
    st.info("Select a symbol and click Analyze 🚀")