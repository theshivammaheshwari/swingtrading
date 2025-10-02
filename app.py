import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import re
from datetime import datetime
import streamlit.components.v1 as components

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

# ========== CHECK FOR SUPPORT MODE ==========
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# ========== TOP RIGHT BUTTON ==========
if st.session_state.page == 'home':
    col_title, col_support = st.columns([5, 1])
    
    with col_title:
        st.title("📊 Swing Trading + Fundamentals Dashboard")
    
    with col_support:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("☕ Support", use_container_width=True, type="primary", key="support_btn_top"):
            st.session_state.page = 'support'
            st.rerun()
# ========== END BUTTON ==========

# ========== SUPPORT PAGE CONTENT ==========
if st.session_state.page == 'support':
    # Custom CSS for support page
    st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div style='text-align: center; padding: 40px 20px; color: white;'>
            <h1>☕ Support the Developer</h1>
            <p style='font-size: 18px; margin-top: 20px;'>
                Thank you for considering support!<br>
                Your contribution helps keep this project running and ad-free.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for payment
    if 'selected_amount' not in st.session_state:
        st.session_state.selected_amount = None
    if 'show_payment' not in st.session_state:
        st.session_state.show_payment = False
    
    # Main container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        st.markdown("### 💰 Choose Amount")
        
        # Preset amounts
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("☕ ₹100", use_container_width=True, type="secondary", key="amt100"):
                st.session_state.selected_amount = 10000
                st.session_state.show_payment = False
            
            if st.button("☕☕☕ ₹500", use_container_width=True, type="secondary", key="amt500"):
                st.session_state.selected_amount = 50000
                st.session_state.show_payment = False
        
        with col_b:
            if st.button("☕☕ ₹250", use_container_width=True, type="secondary", key="amt250"):
                st.session_state.selected_amount = 25000
                st.session_state.show_payment = False
            
            if st.button("🎁 ₹1000", use_container_width=True, type="secondary", key="amt1000"):
                st.session_state.selected_amount = 100000
                st.session_state.show_payment = False
        
        st.markdown("---")
        
        # Custom amount
        st.markdown("### ✏️ Or Enter Custom Amount")
        custom_amount = st.number_input(
            "Amount in ₹",
            min_value=50,
            max_value=100000,
            value=100,
            step=50,
            key="custom_amt"
        )
        
        if st.button("Set Custom Amount", use_container_width=True, type="secondary", key="set_custom"):
            st.session_state.selected_amount = custom_amount * 100
            st.session_state.show_payment = False
        
        st.markdown("---")
        
        # Show selected amount
        if st.session_state.selected_amount:
            amount_in_rupees = st.session_state.selected_amount / 100
            st.success(f"✅ Selected Amount: ₹{amount_in_rupees:.0f}")
            
            # Proceed button
            if st.button("💳 Proceed to Payment", use_container_width=True, type="primary", key="proceed_pay"):
                st.session_state.show_payment = True
                st.rerun()
        else:
            st.info("👆 Please select or enter an amount above")
        
        # Show payment modal (FULL SCREEN)
        if st.session_state.show_payment and st.session_state.selected_amount:
            # Clear everything and show only payment
            st.markdown("---")
            
            # Full screen payment container
            payment_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .payment-container {{
                        background: white;
                        padding: 60px 40px;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        text-align: center;
                        max-width: 500px;
                        width: 90%;
                    }}
                    .loader {{
                        border: 6px solid #f3f3f3;
                        border-top: 6px solid #FFDD00;
                        border-radius: 50%;
                        width: 60px;
                        height: 60px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 30px;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                    h2 {{
                        color: #333;
                        margin-bottom: 15px;
                        font-size: 28px;
                    }}
                    p {{
                        color: #666;
                        font-size: 16px;
                        line-height: 1.6;
                    }}
                    .amount {{
                        background: #fff8e1;
                        padding: 20px;
                        border-radius: 12px;
                        margin: 20px 0;
                        border: 2px solid #FFDD00;
                    }}
                    .amount-value {{
                        font-size: 36px;
                        font-weight: bold;
                        color: #000;
                    }}
                    .success-icon {{
                        font-size: 80px;
                        margin-bottom: 20px;
                    }}
                    .error-icon {{
                        font-size: 80px;
                        margin-bottom: 20px;
                    }}
                    .payment-id {{
                        background: #f5f5f5;
                        padding: 15px;
                        border-radius: 8px;
                        margin-top: 20px;
                        font-family: 'Courier New', monospace;
                        font-size: 14px;
                        color: #666;
                        word-break: break-all;
                    }}
                    .status-message {{
                        margin-top: 20px;
                        font-size: 14px;
                        color: #999;
                    }}
                </style>
            </head>
            <body>
                <div class="payment-container" id="payment-status">
                    <div class="loader"></div>
                    <h2>Processing Payment</h2>
                    <div class="amount">
                        <p style="margin-bottom: 8px; color: #999; font-size: 14px;">Amount to Pay</p>
                        <div class="amount-value">₹{st.session_state.selected_amount / 100:.0f}</div>
                    </div>
                    <p>Opening secure Razorpay payment window...</p>
                    <p class="status-message">Please complete the payment in the popup window</p>
                </div>
                
                <script>
                    console.log('Initializing Razorpay payment...');
                    
                    var options = {{
                        "key": "rzp_live_WbMdjDSTBNEsE3",
                        "amount": {st.session_state.selected_amount},
                        "currency": "INR",
                        "name": "Swing Trading Dashboard",
                        "description": "Support the developer ☕",
                        "image": "https://cdn-icons-png.flaticon.com/512/3565/3565418.png",
                        "handler": function (response) {{
                            console.log('Payment successful:', response);
                            document.getElementById('payment-status').innerHTML = 
                                '<div class="success-icon">🎉</div>' +
                                '<h2 style="color: #2e7d32;">Payment Successful!</h2>' +
                                '<p style="font-size: 18px; margin: 20px 0;">Thank you so much for your support!</p>' +
                                '<div class="amount">' +
                                    '<p style="margin-bottom: 8px; color: #999; font-size: 14px;">Amount Paid</p>' +
                                    '<div class="amount-value">₹{st.session_state.selected_amount / 100:.0f}</div>' +
                                '</div>' +
                                '<div class="payment-id">' +
                                    '<strong>Payment ID:</strong><br>' + response.razorpay_payment_id +
                                '</div>' +
                                '<p style="margin-top: 30px; color: #666;">Your contribution helps keep this project running and ad-free.</p>';
                        }},
                        "prefill": {{
                            "email": "247shivam@gmail.com",
                            "contact": "+919468955596"
                        }},
                        "notes": {{
                            "amount": "₹{st.session_state.selected_amount / 100}",
                            "purpose": "Developer Support"
                        }},
                        "theme": {{
                            "color": "#FFDD00"
                        }},
                        "modal": {{
                            "ondismiss": function() {{
                                console.log('Payment cancelled by user');
                                document.getElementById('payment-status').innerHTML = 
                                    '<div class="error-icon">⚠️</div>' +
                                    '<h2 style="color: #f57c00;">Payment Cancelled</h2>' +
                                    '<p style="margin: 20px 0;">You cancelled the payment process</p>' +
                                    '<div class="amount">' +
                                        '<p style="margin-bottom: 8px; color: #999; font-size: 14px;">Amount</p>' +
                                        '<div class="amount-value">₹{st.session_state.selected_amount / 100:.0f}</div>' +
                                    '</div>' +
                                    '<p style="color: #999; margin-top: 20px;">You can close this window and try again</p>';
                            }},
                            "escape": true,
                            "backdropclose": true
                        }}
                    }};
                    
                    try {{
                        var rzp = new Razorpay(options);
                        
                        rzp.on('payment.failed', function (response) {{
                            console.error('Payment failed:', response.error);
                            document.getElementById('payment-status').innerHTML = 
                                '<div class="error-icon">❌</div>' +
                                '<h2 style="color: #d32f2f;">Payment Failed</h2>' +
                                '<p style="margin: 20px 0; color: #666;">' + response.error.description + '</p>' +
                                '<div class="amount">' +
                                    '<p style="margin-bottom: 8px; color: #999; font-size: 14px;">Amount</p>' +
                                    '<div class="amount-value">₹{st.session_state.selected_amount / 100:.0f}</div>' +
                                '</div>' +
                                '<div style="background: #ffebee; padding: 15px; border-radius: 8px; margin-top: 20px;">' +
                                    '<p style="color: #d32f2f; font-size: 14px; margin: 0;"><strong>Reason:</strong> ' + response.error.reason + '</p>' +
                                '</div>' +
                                '<p style="color: #999; margin-top: 20px;">Please try again or contact support</p>';
                        }});
                        
                        // Open Razorpay modal after a short delay
                        setTimeout(function() {{
                            console.log('Opening Razorpay modal...');
                            rzp.open();
                        }}, 800);
                        
                    }} catch(error) {{
                        console.error('Razorpay initialization error:', error);
                        document.getElementById('payment-status').innerHTML = 
                            '<div class="error-icon">⚠️</div>' +
                            '<h2 style="color: #d32f2f;">Unable to Load Payment</h2>' +
                            '<p style="margin: 20px 0;">Error: ' + error.message + '</p>' +
                            '<p style="color: #999; font-size: 14px;">Please check your internet connection and try again</p>';
                    }}
                </script>
            </body>
            </html>
            """
            
            # Render full screen payment (large height for full page effect)
            components.html(payment_html, height=700, scrolling=False)
            
            # Back button below payment
            st.markdown("<br><br>", unsafe_allow_html=True)
            col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
            with col_b2:
                if st.button("⬅️ Go Back", key="back_from_payment", use_container_width=True):
                    st.session_state.show_payment = False
                    st.session_state.selected_amount = None
                    st.rerun()
            
            st.stop()  # Stop rendering anything else

# ========== MAIN APP CONTENT (Only shows if page == 'home') ==========
# Your rest of the app code here...
st.markdown("## Your Main Dashboard Content")
st.markdown("""
    <style>
    div.stButton > button { width: 100%; margin-top: 0.55rem; }
    th, td { white-space: nowrap; }
    </style>
""", unsafe_allow_html=True)

# ========== SIMPLE BANNER ==========
def simple_banner():
    """Simple text banner"""
    banner_html = """
    <div style="background: #f0f7ff; border-left: 4px solid #1e40af; padding: 15px 20px; margin-bottom: 20px; border-radius: 8px;">
        <p style="margin: 0; color: #1e40af; font-size: 15px;">
            💳 <strong>SBI Simply Click Credit Card</strong> - 5X Reward Points on online shopping. 
            <a href="https://bitli.in/rRDvT8n" target="_blank" style="color: #1e40af; font-weight: bold; text-decoration: underline;">Apply Now →</a>
        </p>
    </div>
    """
    components.html(banner_html, height=70)

simple_banner()
# ========== END ==========

st.title("📊 Swing Trading + Fundamentals Dashboard")

# ================= Disclaimer (bilingual) =================
DISCLAIMER_MD = """
---
### ⚠️ Disclaimer / अस्वीकरण
This project is developed for educational and portfolio purposes only.  
It does not constitute investment, trading, or financial advice.  
Please consult a SEBI-registered financial adviser before making any investment decisions.  

यह प्रोजेक्ट केवल शैक्षिक और पोर्टफोलियो उद्देश्यों के लिए बनाया गया है।  
यह निवेश, ट्रेडिंग या वित्तीय सलाह नहीं है।  
किसी भी निवेश का निर्णय लेने से पहले कृपया SEBI-रजिस्टर्ड वित्तीय सलाहकार से परामर्श करें।  
---
"""

# ---------------- Sidebar: Developer + Settings + Disclaimer ----------------
with st.sidebar:
    st.markdown("### 👨‍💻 Developer Info")
    st.markdown("**Mr. Shivam Maheshwari**")
    st.write("🔗 [LinkedIn](https://www.linkedin.com/in/theshivammaheshwari)")
    st.write("📸 [Instagram](https://www.instagram.com/theshivammaheshwari)")
    st.write("📘 [Facebook](https://www.facebook.com/theshivammaheshwari)")
    st.write("✉️ 247shivam@gmail.com")
    st.write("📱 +91-9468955596")
    st.markdown("---")
    
    menu_option = st.radio(
        "📑 Navigation",
        ["Home - Stock Analysis", "🔥 Top Gainers & Losers", "🔀 Compare Stocks"],
        index=0
    )
    
    st.markdown("---")
    unit_choice = st.radio("INR big values unit:", ["Crore", "Lakh"], index=0, horizontal=True)
    st.caption("Non-INR values show as K/M/B/T. All numbers display with 2 decimals.")
    
    # ========== INDICES WITH METRICS ==========
    st.markdown("---")
    st.markdown("### 📊 Market Indices")
    
    @st.cache_data(ttl=120, show_spinner=False)
    def fetch_idx():
        r = []
        for s, n in [("^NSEI", "NIFTY 50"), ("^NSEBANK", "BANK NIFTY"), ("^BSESN", "SENSEX")]:
            try:
                t = yf.Ticker(s)
                h = t.history(period="5d")
                if len(h) >= 2:
                    c, p = float(h['Close'].iloc[-1]), float(h['Close'].iloc[-2])
                    chg, chgp = c-p, ((c-p)/p)*100
                    r.append({'name': n, 'price': c, 'change': chg, 'pct': chgp})
            except:
                pass
        return r
    
    try:
        data = fetch_idx()
        if data:
            for idx in data:
                st.metric(
                    label=idx['name'],
                    value=f"₹{idx['price']:,.0f}",
                    delta=f"{idx['change']:+.0f} ({idx['pct']:+.2f}%)"
                )
            
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_indices"):
                st.cache_data.clear()
                st.rerun()
            
            st.caption("🕐 Auto: 2 min")
        else:
            st.info("Loading...")
    except:
        st.warning("Unavailable")
    # ========== END ==========
    
    st.markdown(DISCLAIMER_MD)

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

# ================= NEW: Top Gainers/Losers Fetcher =================
@st.cache_data(show_spinner=False, ttl=300)
def fetch_top_movers():
    """
    Fetch top 10 gainers and losers from Nifty 50 using Yahoo Finance
    No extra dependencies needed!
    """
    try:
        # Nifty 50 stocks
        nifty50_symbols = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
            "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS",
            "ITC.NS", "ASIANPAINT.NS", "AXISBANK.NS", "LT.NS", "DMART.NS",
            "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "WIPRO.NS",
            "MARUTI.NS", "HCLTECH.NS", "TATAMOTORS.NS", "M&M.NS", "NTPC.NS",
            "BAJAJFINSV.NS", "TECHM.NS", "POWERGRID.NS", "ONGC.NS", "ADANIPORTS.NS",
            "TATASTEEL.NS", "HDFCLIFE.NS", "COALINDIA.NS", "JSWSTEEL.NS", "GRASIM.NS",
            "HINDALCO.NS", "INDUSINDBK.NS", "BRITANNIA.NS", "SHREECEM.NS", "DIVISLAB.NS",
            "DRREDDY.NS", "EICHERMOT.NS", "APOLLOHOSP.NS", "CIPLA.NS", "UPL.NS",
            "SBILIFE.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "TATACONSUM.NS", "BPCL.NS"
        ]
        
        data_list = []
        failed_count = 0
        
        # Use columns for better progress display
        prog_col1, prog_col2 = st.columns([3, 1])
        with prog_col1:
            progress_bar = st.progress(0)
        with prog_col2:
            progress_text = st.empty()
        
        for idx, symbol in enumerate(nifty50_symbols):
            try:
                progress_text.text(f"{idx+1}/{len(nifty50_symbols)}")
                progress_bar.progress((idx + 1) / len(nifty50_symbols))
                
                ticker = yf.Ticker(symbol)
                
                # Get last 2 days data
                hist = ticker.history(period="5d")
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                    
                    # Get company name
                    info = ticker.info
                    company_name = info.get('longName', info.get('shortName', symbol.replace('.NS', '')))
                    
                    data_list.append({
                        'Symbol': symbol.replace('.NS', ''),
                        'Company': company_name,
                        'Current Price (₹)': _safe_round(current_price, 2),
                        'Change (₹)': _safe_round(change, 2),
                        'Change (%)': _safe_round(change_pct, 2)
                    })
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                continue
        
        progress_bar.empty()
        progress_text.empty()
        
        if not data_list:
            st.error("❌ Could not fetch any stock data. Please check your internet connection.")
            return pd.DataFrame(), pd.DataFrame()
        
        if failed_count > 0:
            st.warning(f"⚠️ Could not fetch data for {failed_count} stocks")
        
        # Create DataFrame
        df = pd.DataFrame(data_list)
        
        # Sort by change percentage
        df_sorted = df.sort_values('Change (%)', ascending=False)
        
        # Top 10 gainers
        gainers_df = df_sorted.head(10).reset_index(drop=True)
        gainers_df.index = range(1, len(gainers_df) + 1)
        
        # Top 10 losers
        losers_df = df_sorted.tail(10).reset_index(drop=True)
        losers_df = losers_df.sort_values('Change (%)').reset_index(drop=True)
        losers_df.index = range(1, len(losers_df) + 1)
        
        return gainers_df, losers_df
        
    except Exception as e:
        st.error(f"❌ Error fetching top movers: {str(e)}")
        st.info("💡 Tip: Try refreshing the page or check your internet connection")
        return pd.DataFrame(), pd.DataFrame()


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

    # Fundamentals (trimmed for display; numeric-safe casting)
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

        "DebtToEquity": _safe_round(dte_n, 2),

        "TotalDebt": format_big_value(total_debt, currency, unit_for_inr=unit_inr),
        "TotalCash": format_big_value(total_cash, currency, unit_for_inr=unit_inr),

        "Beta": _safe_round(info.get("beta"), 2),
        "CurrentPrice": _safe_round(info.get("currentPrice") or latest["Close"], 2),
        "HighLow52W": f"{_safe_round(info.get('fiftyTwoWeekHigh'),2)} / {_safe_round(info.get('fiftyTwoWeekLow'),2)}" if info.get("fiftyTwoWeekHigh") and info.get("fiftyTwoWeekLow") else None,
        "BookValue": _safe_round(info.get("bookValue"), 2),
        "AsOf": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    # Scoring (kept for info)
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

# ================= Compare View (via query params or sidebar) =================
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
        st.markdown(DISCLAIMER_MD)
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

    # Technical Comparison (AgGrid pinned)
    if tech_rows:
        st.subheader("📊 Technical Comparison")
        df_t = pd.DataFrame(tech_rows)
        if AGGRID_AVAILABLE:
            gb_t = GridOptionsBuilder.from_dataframe(df_t)
            gb_t.configure_default_column(resizable=True, filter=True, sortable=True, min_width=120)
            gb_t.configure_column("Ticker", pinned="left", width=110)
            gb_t.configure_column("Company", pinned="left", width=220)
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
                df_t, gridOptions=grid_options_t, theme="balham",
                fit_columns_on_grid_load=False, allow_unsafe_jscode=True,
                update_mode=GridUpdateMode.NO_UPDATE, height=420
            )
        else:
            for col in ["Last Close","RSI","Stoploss"]:
                if col in df_t.columns:
                    df_t[col] = df_t[col].apply(lambda v: f"{float(v):,.2f}" if isinstance(v, (int,float,np.floating)) else v)
            if "Volume" in df_t.columns:
                df_t["Volume"] = df_t["Volume"].apply(lambda v: f"{int(v):,}" if v is not None else "NA")
            st.dataframe(df_t, use_container_width=True)

    # Fundamentals Comparison (AgGrid pinned)
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
                df_f, gridOptions=grid_options, theme="balham",
                fit_columns_on_grid_load=False, allow_unsafe_jscode=True,
                update_mode=GridUpdateMode.NO_UPDATE, height=480
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

    st.markdown(DISCLAIMER_MD)
    return True

# ================= MAIN APP LOGIC =================

# Check if compare mode via URL
if render_compare_view():
    st.stop()

# ================= Menu-based Navigation =================
unit_inr = "Cr" if unit_choice == "Crore" else "L"

# ---------- PAGE 1: TOP GAINERS & LOSERS (ENHANCED) ----------
if menu_option == "🔥 Top Gainers & Losers":
    
    # Header section
    st.markdown("""
        <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='color: white; text-align: center; margin: 0;'>
                🔥 Top 10 Gainers & Losers (NIFTY 50)
            </h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Control section
    col_refresh, col_time, col_info = st.columns([1, 2, 2])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_time:
        st.markdown(f"**📅 Updated:** {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")
    with col_info:
        st.markdown("**📊 Source:** Yahoo Finance (5-min cache)")
    
    # Fetch data
    with st.spinner("Fetching live market data..."):
        gainers_df, losers_df = fetch_top_movers()
    
    # ========== TOP 10 GAINERS ==========
    st.markdown("---")
    st.markdown("### 📈 Top 10 Gainers")
    
    if not gainers_df.empty:
        # Add rank column
        gainers_display = gainers_df.copy()
        gainers_display.insert(0, 'Rank', ['🥇', '🥈', '🥉'] + list(range(4, 11)))
        
        # Apply styling
        def highlight_gainers(row):
            styles = [''] * len(row)
            if row.name < 3:  # Top 3
                styles = ['background-color: #fff9c4'] * len(row)
            return styles
        
        styled_gainers = gainers_display.style.apply(highlight_gainers, axis=1).format({
            'Current Price (₹)': '₹{:.2f}',
            'Change (₹)': lambda x: f'+₹{x:.2f}' if x > 0 else f'₹{x:.2f}',
            'Change (%)': lambda x: f'+{x:.2f}%' if x > 0 else f'{x:.2f}%'
        })
        
        # Display table
        st.dataframe(styled_gainers, use_container_width=True, height=420)
        
        # Stats row
        col_stat1, col_stat2, col_stat3, col_download1 = st.columns([1, 1, 1, 1])
        with col_stat1:
            st.success(f"**Highest Gain:** {gainers_df['Change (%)'].max():.2f}%")
        with col_stat2:
            st.info(f"**Avg Gain:** {gainers_df['Change (%)'].mean():.2f}%")
        with col_stat3:
            st.warning(f"**Total Stocks:** {len(gainers_df)}")
        with col_download1:
            csv_gainers = gainers_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 CSV",
                data=csv_gainers,
                file_name=f"gainers_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.error("❌ Unable to fetch gainers data")
    
    # ========== TOP 10 LOSERS ==========
    st.markdown("---")
    st.markdown("### 📉 Top 10 Losers")
    
    if not losers_df.empty:
        # Add rank column
        losers_display = losers_df.copy()
        losers_display.insert(0, 'Rank', list(range(1, 11)))
        
        # Apply styling
        def highlight_losers(row):
            styles = [''] * len(row)
            if row.name < 3:  # Top 3
                styles = ['background-color: #ffcdd2'] * len(row)
            return styles
        
        styled_losers = losers_display.style.apply(highlight_losers, axis=1).format({
            'Current Price (₹)': '₹{:.2f}',
            'Change (₹)': lambda x: f'{x:.2f}' if x < 0 else f'+{x:.2f}',
            'Change (%)': lambda x: f'{x:.2f}%' if x < 0 else f'+{x:.2f}%'
        })
        
        # Display table
        st.dataframe(styled_losers, use_container_width=True, height=420)
        
        # Stats row
        col_stat1, col_stat2, col_stat3, col_download2 = st.columns([1, 1, 1, 1])
        with col_stat1:
            st.error(f"**Highest Loss:** {losers_df['Change (%)'].min():.2f}%")
        with col_stat2:
            st.info(f"**Avg Loss:** {losers_df['Change (%)'].mean():.2f}%")
        with col_stat3:
            st.warning(f"**Total Stocks:** {len(losers_df)}")
        with col_download2:
            csv_losers = losers_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 CSV",
                data=csv_losers,
                file_name=f"losers_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.error("❌ Unable to fetch losers data")
    
    # ========== MARKET OVERVIEW ==========
    if not gainers_df.empty and not losers_df.empty:
        st.markdown("---")
        st.markdown("### 📊 Market Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            top_gainer = gainers_df.iloc[0]
            st.metric(
                label="🏆 Best Performer",
                value=top_gainer['Symbol'],
                delta=f"{top_gainer['Change (%)']}%",
                delta_color="normal"
            )
        
        with col2:
            top_loser = losers_df.iloc[0]
            st.metric(
                label="⚠️ Worst Performer",
                value=top_loser['Symbol'],
                delta=f"{top_loser['Change (%)']}%",
                delta_color="inverse"
            )
        
        with col3:
            total_volume_gain = gainers_df['Change (%)'].sum()
            st.metric(
                label="📈 Total Gains",
                value=f"{total_volume_gain:.2f}%",
                delta="Combined"
            )
        
        with col4:
            total_volume_loss = losers_df['Change (%)'].sum()
            st.metric(
                label="📉 Total Losses",
                value=f"{total_volume_loss:.2f}%",
                delta="Combined"
            )
    
    st.markdown(DISCLAIMER_MD)
# ---------- PAGE 2: COMPARE STOCKS ----------
elif menu_option == "🔀 Compare Stocks":
    st.markdown("## 🔀 Compare Stocks (2-10 tickers)")
    
    if all_stock_codes:
        cmp_sel = st.multiselect("Select tickers to compare:", all_stock_codes, max_selections=10)
        cmp_input_text = st.text_input("Or type comma-separated (e.g., RELIANCE, TCS, INFY)", "")
        cmp_tickers = [t.strip().upper() for t in cmp_input_text.split(",") if t.strip()] if cmp_input_text.strip() else cmp_sel
    else:
        cmp_input_text = st.text_input("Enter tickers (comma-separated)", "RELIANCE, TCS, INFY")
        cmp_tickers = [t.strip().upper() for t in cmp_input_text.split(",") if t.strip()]

    cmp_tickers = [_sanitize_ticker(t) for t in cmp_tickers]
    cmp_tickers = [t for t in cmp_tickers if t]

    if st.button("🚀 Compare Now", use_container_width=True):
        if len(cmp_tickers) < 2 or len(cmp_tickers) > 10:
            st.warning("Please select 2 to 10 tickers for comparison.")
        else:
            tech_rows = []
            fund_rows = []

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, t in enumerate(cmp_tickers):
                status_text.text(f"Analyzing {t}... ({idx+1}/{len(cmp_tickers)})")
                progress_bar.progress((idx + 1) / len(cmp_tickers))
                
                techs, funds, used, tried, hist = super_technical_analysis(t, unit_inr=unit_inr)
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

                # Fundamentals row
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

            progress_bar.empty()
            status_text.empty()

            # Technical Comparison
            if tech_rows:
                st.subheader("📊 Technical Comparison")
                df_t = pd.DataFrame(tech_rows)
                if AGGRID_AVAILABLE:
                    gb_t = GridOptionsBuilder.from_dataframe(df_t)
                    gb_t.configure_default_column(resizable=True, filter=True, sortable=True, min_width=120)
                    gb_t.configure_column("Ticker", pinned="left", width=110)
                    gb_t.configure_column("Company", pinned="left", width=220)
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
                        df_t, gridOptions=grid_options_t, theme="balham",
                        fit_columns_on_grid_load=False, allow_unsafe_jscode=True,
                        update_mode=GridUpdateMode.NO_UPDATE, height=420
                    )
                else:
                    for col in ["Last Close","RSI","Stoploss"]:
                        if col in df_t.columns:
                            df_t[col] = df_t[col].apply(lambda v: f"{float(v):,.2f}" if isinstance(v, (int,float,np.floating)) else v)
                    if "Volume" in df_t.columns:
                        df_t["Volume"] = df_t["Volume"].apply(lambda v: f"{int(v):,}" if v is not None else "NA")
                    st.dataframe(df_t, use_container_width=True)

            # Fundamentals Comparison
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
                        df_f, gridOptions=grid_options, theme="balham",
                        fit_columns_on_grid_load=False, allow_unsafe_jscode=True,
                        update_mode=GridUpdateMode.NO_UPDATE, height=480
                    )
                else:
                    for col in ["PE (TTM)","Price to Book","EV/EBITDA","Dividends","Debt to Equity","Current Price","Book Value"]:
                        if col in df_f.columns:
                            df_f[col] = df_f[col].apply(lambda v: f"{float(v):,.2f}" if isinstance(v, (int,float,np.floating)) else v)
                    st.dataframe(df_f, use_container_width=True)

            # Normalized performance chart
            st.subheader("📈 Normalized Performance (Rebased to 100)")
            perf = {}
            for t in cmp_tickers:
                techs, funds, used, tried, hist = super_technical_analysis(t, unit_inr=unit_inr)
                if hist is not None and not hist.empty:
                    c = hist["Close"].astype(float).dropna()
                    if len(c) > 0:
                        perf[used or t] = (c / c.iloc[0]) * 100.0
            if perf:
                norm_df = pd.DataFrame(perf)
                st.line_chart(norm_df, height=350, use_container_width=True)

    st.markdown(DISCLAIMER_MD)

# ---------- PAGE 3: HOME - STOCK ANALYSIS (DEFAULT) ----------
else:  # "Home - Stock Analysis"
    
    # Check if stock was selected from Gainers/Losers page
    if 'selected_stock' in st.session_state:
        default_stock = st.session_state['selected_stock']
        del st.session_state['selected_stock']
    else:
        default_stock = "RELIANCE"
    
    # UI: Input section
    try:
        col_in1, col_in2 = st.columns([2, 1], vertical_alignment="bottom")
    except TypeError:
        col_in1, col_in2 = st.columns([2, 1])

    with col_in1:
        if all_stock_codes:
            try:
                default_idx = all_stock_codes.index(default_stock)
            except ValueError:
                default_idx = all_stock_codes.index("RELIANCE") if "RELIANCE" in all_stock_codes else 0
            user_input = st.selectbox("🔍 Search or select stock symbol:", all_stock_codes, index=default_idx)
        else:
            user_input = st.text_input("Enter stock symbol (e.g., RELIANCE, TCS, INFY, AAPL):", value=default_stock)

    with col_in2:
        run_btn = st.button("Analyze 🚀", use_container_width=True)

    # Run Analysis
    if run_btn:
        company_name = symbol_to_name.get(user_input, "")

        with st.spinner(f"Analyzing {user_input}..."):
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
            st.write(f"**Overall Score:** {f_score}")
            if flags:
                st.write("**Highlights:** " + " • ".join(flags))

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

        

        st.markdown(DISCLAIMER_MD)

    else:
        st.info("Select a symbol and click **Analyze 🚀** to get started")
        
        # Show quick links to popular stocks
        st.markdown("### 🔥 Popular Stocks")
        st.caption("Click to analyze quickly")
        
        popular_stocks = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "TATAMOTORS", "WIPRO", "LT", "AXISBANK"]
        
        cols = st.columns(5)
        for idx, stock in enumerate(popular_stocks):
            with cols[idx % 5]:
                if st.button(f"📊 {stock}", key=f"quick_{stock}"):
                    st.session_state['selected_stock'] = stock
                    st.rerun()
        
        st.markdown(DISCLAIMER_MD)

# ================= END OF CODE =================