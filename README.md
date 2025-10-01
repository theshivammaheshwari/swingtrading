# 📊 Swing Trading + Fundamentals Dashboard  

A powerful **Streamlit web app** for analyzing stocks with **technical indicators + fundamental data**.  
The app integrates **Yahoo Finance**, **Screener.in**, and custom logic to provide:  
- Swing trading signals  
- Candle pattern detection  
- Pivot levels & Fibonacci targets  
- Fundamentals & financial ratios  
- Multi-stock comparison  

🌐 **Live App**: [Trading247 Dashboard](https://trading247.streamlit.app/)  

---

## 🚀 Features  

✅ **Technical Analysis**  
- EMA (10/20) crossover  
- RSI, MACD, ATR, ADX  
- Bollinger Bands  
- Support/Resistance pivots  
- Fibonacci targets  
- Candle patterns (Hammer, Engulfing, Shooting Star)  

✅ **Fundamental Analysis**  
- Market Cap, Enterprise Value, P/E, P/B, EV/EBITDA  
- Dividend yield, payout ratio  
- Revenue & earnings growth  
- Margins (Profit, Operating, Gross)  
- Debt-to-equity, Total Debt, Total Cash  
- Scoring model with **flags** (Strong/Moderate/Weak fundamentals)  

✅ **Comparison Dashboard**  
- Compare **2–10 stocks** side-by-side  
- Technical signals & fundamentals  
- Normalized performance chart  

✅ **UI Enhancements**  
- Clean Streamlit design (wide layout)  
- Interactive AgGrid tables with pinned columns  
- Sidebar options for unit formatting (Crore / Lakh)  
- Shareable **Compare View Links**  

---

## 📦 Installation  

Clone the repo:  
```bash
git clone https://github.com/<your-username>/trading247.git
cd trading247
```

Create a virtual environment & install dependencies:  
```bash
pip install -r requirements.txt
```

Run the app locally:  
```bash
streamlit run app.py
```

---

## ⚙️ Dependencies  

- streamlit  
- yfinance  
- ta (technical indicators)  
- pandas, numpy  
- beautifulsoup4, requests  
- plotly *(optional, for charts)*  
- streamlit-aggrid *(optional, for interactive tables)*  

---

## 📸 Screenshots  

🔍 **Single Stock Analysis**  
- Key trade highlights with signals, stoploss, Fibonacci targets  
- Technical charts with support/resistance  
- Fundamentals overview  

📊 **Multi-Stock Comparison**  
- Compare up to 10 stocks  
- Technical + fundamental comparison tables  
- Normalized performance line chart  

---

## ⚠️ Disclaimer  

This project is for **educational & portfolio purposes only**.  
It does **NOT** constitute financial, trading, or investment advice.  
Always consult a **SEBI-registered financial advisor** before making investment decisions.  

---

## 👨‍💻 Developer Info  

**Shivam Maheshwari**  

- 🔗 [LinkedIn](https://www.linkedin.com/in/theshivammaheshwari)  
- 📸 [Instagram](https://www.instagram.com/theshivammaheshwari)  
- 📘 [Facebook](https://www.facebook.com/theshivammaheshwari)  
- ✉️ 247shivam@gmail.com  
- 📱 +91-9468955596  
