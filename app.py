import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import re
from datetime import datetime

# ================= Streamlit Config =================
st.set_page_config(page_title="Swing Trading + Fundamentals Dashboard", page_icon="📊", layout="wide")
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
    st.caption("Note: Non-INR values will show as K/M/B/T")

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

def _sanitize_ticker(t):
    t = (t or "").strip().upper()
    return re.sub(r"[^A-Z0-9\.\-]", "", t)  # keep letters, digits, dot, dash

def indian_comma_format(number, decimals=2):
    try:
        neg = number < 0
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
    factor = 1e7 if unit.lower().startswith("cr") else 1e5  # Cr=1e7, L=1e5
    val = x / factor
    return f"{indian_comma_format(val, decimals)} {unit}"

def format_big_value(x, currency, unit_for_inr="Cr", decimals=2):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    if (currency or "").upper() == "INR":
        return format_inr_value(x, unit=unit_for_inr, decimals=decimals)
    # non-INR: humanize
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
        return _safe_round(x, 2)
    return f"{_safe_round(val, decimals)}{suf}"

# ================= Data: yfinance with .NS/.BO fallback =================
def _get_ticker_with_fallback(ticker, period="6mo", interval="1d"):
    t = _sanitize_ticker(ticker)
    tried = []
    # If suffix already provided, try only raw; else try raw + NSE + BSE
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
    # robust info fetch for different yfinance versions
    for getter in ("info", "get_info"):
        try:
            obj = getattr(stock, getter)
            data = obj() if callable(obj) else obj
            if isinstance(data, dict) and data:
                return data
        except Exception:
            continue
    return {}

# ================= Screener.in Fundamentals (from your reference) =================
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

# ================= Core: Technical + Fundamentals =================
def super_technical_analysis(ticker: str, unit_inr="Cr"):
    stock, hist, used_ticker, tried = _get_ticker_with_fallback(ticker, period="6mo", interval="1d")
    if hist.empty:
        return None, None, used_ticker, tried

    hist = hist.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if hist.shape[0] < 30:
        return None, None, used_ticker, tried

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
        "BB_High": _safe_round(latest["BB_high"], 2),
        "BB_Low": _safe_round(latest["BB_low"], 2),
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

    # Fundamentals (yfinance)
    info = _get_info(stock)
    currency = info.get("currency")
    market_cap = info.get("marketCap")
    enterprise_val = info.get("enterpriseValue")
    free_cf = info.get("freeCashflow")
    total_debt = info.get("totalDebt")
    total_cash = info.get("totalCash")

    fcf_yield = (free_cf / market_cap) if (free_cf and market_cap and market_cap != 0) else None
    roe = info.get("returnOnEquity")
    dte = info.get("debtToEquity")
    pm = info.get("profitMargins")
    revg = info.get("revenueGrowth")

    fundamentals = {
        "Company": info.get("longName") or info.get("shortName"),
        "Sector": info.get("sector"),
        "Industry": info.get("industry"),
        "Country": info.get("country"),
        "Currency": currency,
        "MarketCap": format_big_value(market_cap, currency, unit_for_inr=unit_inr),
        "EnterpriseValue": format_big_value(enterprise_val, currency, unit_for_inr=unit_inr),
        "PE_TTM": info.get("trailingPE"),
        "Forward_PE": info.get("forwardPE"),
        "PEG": info.get("pegRatio"),
        "PriceToBook": info.get("priceToBook"),
        "EV_to_EBITDA": info.get("enterpriseToEbitda"),
        "DividendYield_%": _pct(info.get("dividendYield")),
        "PayoutRatio_%": _pct(info.get("payoutRatio")),
        "RevenueGrowth_%": _pct(revg),
        "EarningsGrowth_%": _pct(info.get("earningsGrowth")),
        "ProfitMargin_%": _pct(pm),
        "OperatingMargin_%": _pct(info.get("operatingMargins")),
        "GrossMargin_%": _pct(info.get("grossMargins")),
        "ROE_%": _pct(roe),
        "ROA_%": _pct(info.get("returnOnAssets")),
        "DebtToEquity": dte,
        "CurrentRatio": info.get("currentRatio"),
        "QuickRatio": info.get("quickRatio"),
        "TotalDebt": format_big_value(total_debt, currency, unit_for_inr=unit_inr),
        "TotalCash": format_big_value(total_cash, currency, unit_for_inr=unit_inr),
        "FreeCashFlow": format_big_value(free_cf, currency, unit_for_inr=unit_inr),
        "FCF_Yield_%": _pct(fcf_yield),
        "Beta": info.get("beta"),
        "AsOf": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    # Fundamental Score/Flags
    flags = []
    score = 0
    max_score = 6
    pe = info.get("trailingPE")
    if pe is not None and pe > 0 and pe <= 20:
        score += 1; flags.append("Reasonable P/E")
    if roe is not None and roe >= 0.15:
        score += 1; flags.append("High ROE (>=15%)")
    if dte is not None and dte <= 150:
        score += 1; flags.append("Moderate Leverage")
    if pm is not None and pm >= 0.10:
        score += 1; flags.append("Healthy Profit Margin")
    if revg is not None and revg >= 0.10:
        score += 1; flags.append("Strong Revenue Growth")
    if fcf_yield is not None and fcf_yield >= 0.04:
        score += 1; flags.append("Attractive FCF Yield")
    fund_rating = "Strong" if score >= 4 else ("Moderate" if score >= 2 else "Weak")
    fundamentals["Score"] = f"{score}/{max_score} ({fund_rating})"
    fundamentals["Flags"] = flags

    return tech, fundamentals, used_ticker, tried, hist

# ================= Data Source: NSE stock list (optional) =================
symbol_to_name = {}
all_stock_codes = []
try:
    symbols_df = pd.read_csv("nse_stock_list.csv")  # must contain columns: Symbol, NAME OF COMPANY
    all_stock_codes = symbols_df["Symbol"].dropna().astype(str).tolist()
    symbol_to_name = dict(zip(symbols_df["Symbol"], symbols_df["NAME OF COMPANY"]))
except Exception:
    pass  # if not available, we’ll use text input

# ================= UI: Input section =================
col_in1, col_in2 = st.columns([2,1])
with col_in1:
    if all_stock_codes:
        user_input = st.selectbox("🔍 Search or select stock symbol:", all_stock_codes, index=all_stock_codes.index("RELIANCE") if "RELIANCE" in all_stock_codes else 0)
    else:
        user_input = st.text_input("Enter stock symbol (e.g., RELIANCE, TCS, INFY, AAPL):", value="RELIANCE")

with col_in2:
    run_btn = st.button("Analyze 🚀", use_container_width=True)

if run_btn:
    company_name = symbol_to_name.get(user_input, "")
    unit_inr = "Cr" if unit_choice == "Crore" else "L"

    techs, funds, used, tried, hist = super_technical_analysis(user_input, unit_inr=unit_inr)

    st.markdown(f"### 📈 Swing Trading Analysis - {company_name} ({user_input})")
    if used and used != user_input:
        st.caption(f"Used symbol: {used} (fallback from: {', '.join([t for t in tried if t])})")

    if techs and hist is not None:
        # -------- Key Trade Highlights + Fibonacci Targets --------
        st.subheader("🔎 Key Trade Highlights")
        c1, c2 = st.columns([1.4, 1.1])

        with c1:
            key_high_data = pd.DataFrame([{
                "Candle Pattern": techs["CandlePattern"],
                "Signal": techs["Signal"],
                "Strength": techs["Strength"],
                "Last Close": techs["Close"],
                "RSI": techs["RSI"],
                "ADX": techs["ADX"],
                "ATR": techs["ATR"],
                "Stoploss": techs["Stoploss"] if techs["Stoploss"] else "NA",
            }])
            st.table(key_high_data.style.hide(axis="index"))

        with c2:
            fib = techs.get("Fibonacci_Targets", {}) or {}
            fib_df = pd.DataFrame(list(fib.items()), columns=["Target", "Price"])
            if not fib_df.empty:
                st.markdown("#### 🎯 Fibonacci Targets")
                st.table(fib_df.style.hide(axis="index"))

        # -------- Detailed Technicals --------
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
        ], columns=["Metric","Value"])
        tech_df.index = range(1, len(tech_df)+1)
        st.dataframe(tech_df, use_container_width=True)

        # -------- Pivot Levels --------
        piv_df = pd.DataFrame({
            "Level":["Pivot","R1","R2","R3","S1","S2","S3"],
            "Value":[techs["Pivot"],techs["R1"],techs["R2"],techs["R3"],
                     techs["S1"],techs["S2"],techs["S3"]]
        })
        piv_df.index = range(1, len(piv_df)+1)
        st.subheader("🧭 Pivot Levels")
        st.dataframe(piv_df.style.background_gradient(cmap="Blues"), use_container_width=True)

        # -------- Price Chart --------
        st.subheader("📉 Price Chart (6 months)")
        chart_df = hist[["Close","EMA10","EMA20"]].copy()
        chart_df.columns = ["Close","EMA10","EMA20"]
        st.line_chart(chart_df, height=350, use_container_width=True)

    else:
        st.error("❌ No technical data found. Tried: " + ", ".join([t for t in (tried or []) if t]))

    # -------- Fundamentals (yfinance) --------
    st.markdown(f"### 🏦 Fundamentals - {company_name} ({user_input})")
    if funds:
        # Score and Flags first
        f_score = funds.get("Score", "NA")
        flags = funds.get("Flags", [])
        st.write(f"Overall Score: {f_score}")
        if flags:
            st.write("Highlights: " + " • ".join(flags))

        # Show fundamentals key-value
        exclude_keys = {"Score","Flags"}
        fund_items = [(k, v) for k, v in funds.items() if k not in exclude_keys]
        df_fund = pd.DataFrame(fund_items, columns=["Metric","Value"])
        df_fund.index = range(1, len(df_fund)+1)
        st.dataframe(df_fund.style.background_gradient(cmap="Oranges"), use_container_width=True)
    else:
        st.warning("No yfinance fundamentals available for this ticker.")

    # -------- Screener.in Fundamentals (optional) --------
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