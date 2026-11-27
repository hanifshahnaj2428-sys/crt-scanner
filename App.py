
import streamlit as st
import yfinance as yf
import pandas as pd

# মোবাইল স্ক্রিনের জন্য পেজ সেটআপ
st.set_page_config(page_title="CRT Pro Mobile Scanner", page_icon="📱", layout="centered")

st.title("📱 CRT + MSS + FVG Pro স্ক্যানার")
st.caption("অটোমেটিক SL, TP এবং মাল্টি-টাইমফ্রেম অ্যানালাইসিস")

# স্ক্যান করার জন্য ফরেক্স পেয়ার লিস্ট
pairs = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "GOLD (XAU/USD)": "GC=F"
}

# ৪টি CRT টাইমফ্রেম অপশন
crt_tf = st.selectbox("CRT ক্যান্ডেল টাইমফ্রেম বেছে নিন:", ["5m", "15m", "1h", "4h"], index=2)

# CRT টাইমফ্রেম অনুযায়ী সঠিক লোয়ার টাইমফ্রেম (LTF) নির্ধারণ
ltf_map = {
    "4h": ("15m", "5d"),
    "1h": ("15m", "3d"),
    "15m": ("5m", "2d"),
    "5m": ("1m", "1d")
}

def get_clean_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def analyze_crt(ticker, crt_timeframe):
    try:
        # ১. উচ্চতর টাইমফ্রেমের (CRT) ডেটা সংগ্রহ
        if crt_timeframe == "4h":
            htf_data = get_clean_data(ticker, period="10d", interval="1h")
            if not htf_data.empty:
                htf_data = htf_data.resample("4h").agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
                }).dropna()
        elif crt_timeframe == "1h":
            htf_data = get_clean_data(ticker, period="5d", interval="1h")
        elif crt_timeframe == "15m":
            htf_data = get_clean_data(ticker, period="2d", interval="15m")
        else: # 5m
            htf_data = get_clean_data(ticker, period="1d", interval="5m")
            
        if htf_data.empty or len(htf_data) < 4:
            return "ডেটা পাওয়া যায়নি", "neutral", "-"
        
        # আগের ক্লোজ হওয়া CRT ক্যান্ডেলের High ও Low
        prev_crt_high = float(htf_data['High'].iloc[-2])
        prev_crt_low = float(htf_data['Low'].iloc[-2])
        
        # ২. লোয়ার টাইমফ্রেম (LTF) ডেটা সংগ্রহ
        ltf_interval, ltf_period = ltf_map[crt_timeframe]
        ltf_data = get_clean_data(ticker, period=ltf_period, interval=ltf_interval)
        
        if ltf_data.empty or len(ltf_data) < 10:
            return "LTF ডেটা অপর্যাপ্ত", "neutral", "-"
            
        recent_high = float(ltf_data['High'].iloc[-5:].max())
        recent_low = float(ltf_data['Low'].iloc[-5:].min())
        current_close = float(ltf_data['Close'].iloc[-1])
        
        # FVG চেক (শেষ ৩টি ক্যান্ডেলের মধ্যে)
        c1_high = float(ltf_data['High'].iloc[-3])
        c1_low = float(ltf_data['Low'].iloc[-3])
        c3_high = float(ltf_data['High'].iloc[-1])
        c3_low = float(ltf_data['Low'].iloc[-1])
        
        bullish_fvg = c3_low > c1_high
        bearish_fvg = c3_high < c1_low
        
        # সুইং হাই/লো (MSS-এর জন্য)
        swing_high = float(ltf_data['High'].iloc[-8:-2].max())
        swing_low = float(ltf_data['Low'].iloc[-8:-2].min())
        
        # সুইপ যাচাই
        swept_high = recent_high > prev_crt_high
        swept_low = recent_low < prev_crt_low
        
        decimals = 2 if ("GC=F" in ticker or "JPY" in ticker) else 5
        
        # ৩. সিগন্যাল এবং অটোমেটিক SL ও TP হিসাব
        if swept_high and current_close < swing_low and bearish_fvg:
            entry_price = round((c3_high + c1_low) / 2, decimals)
            sl_price = round(recent_high, decimals)
            risk = abs(sl_price - entry_price)
            tp1_crt = round(prev_crt_low, decimals)
            tp2_rr = round(entry_price - (risk * 2), decimals)
            
            details = (
                f"📌 **LTF:** {ltf_interval} | **Entry Zone:** {round(c3_high, decimals)} - {round(c1_low, decimals)}\n\n"
                f"🛑 **Stop Loss (SL):** {sl_price}\n\n"
                f"🎯 **TP 1 (CRT Low):** {tp1_crt}\n\n"
                f"🏆 **TP 2 (1:2 R:R):** {tp2_rr}"
            )
            return "🔴 SELL (CRT + MSS + FVG)", "sell", details
            
        elif swept_low and current_close > swing_high and bullish_fvg:
            entry_price = round((c1_high + c3_low) / 2, decimals)
            sl_price = round(recent_low, decimals)
            risk = abs(entry_price - sl_price)
            tp1_crt = round(prev_crt_high, decimals)
            tp2_rr = round(entry_price + (risk * 2), decimals)
            
            details = (
                f"📌 **LTF:** {ltf_interval} | **Entry Zone:** {round(c1_high, decimals)} - {round(c3_low, decimals)}\n\n"
                f"🛑 **Stop Loss (SL):** {sl_price}\n\n"
                f"🎯 **TP 1 (CRT High):** {tp1_crt}\n\n"
                f"🏆 **TP 2 (1:2 R:R):** {tp2_rr}"
            )
            return "🟢 BUY (CRT + MSS + FVG)", "buy", details
            
        elif swept_high:
            return f"⚠️ CRT High সুইপ হয়েছে ({ltf_interval}-এ MSS/FVG অপেক্ষায়)", "wait", f"CRT High: {round(prev_crt_high, decimals)} | Sweep High: {round(recent_high, decimals)}"
        elif swept_low:
            return f"⚠️ CRT Low সুইপ হয়েছে ({ltf_interval}-এ MSS/FVG অপেক্ষায়)", "wait", f"CRT Low: {round(prev_crt_low, decimals)} | Sweep Low: {round(recent_low, decimals)}"
        else:
            return "⚪ কোনো সেটআপ নেই", "neutral", f"CRT Range: {round(prev_crt_low, decimals)} - {round(prev_crt_high, decimals)}"
            
    except Exception as e:
        return f"এরর: {str(e)}", "neutral", "-"

# স্ক্যান বাটন
if st.button("🔍 মার্কেট স্ক্যান করুন", use_container_width=True, type="primary"):
    with st.spinner(f"{crt_tf} CRT এবং {ltf_map[crt_tf][0]} এন্ট্রি স্ক্যান করা হচ্ছে..."):
        for name, symbol in pairs.items():
            status, signal_type, details = analyze_crt(symbol, crt_tf)
            
            with st.container(border=True):
                st.subheader(name)
                if signal_type == "buy":
                    st.success(f"**{status}**\n\n{details}")
                elif signal_type == "sell":
                    st.error(f"**{status}**\n\n{details}")
                elif signal_type == "wait":
                    st.warning(f"**{status}**\n\n{details}")
                else:
                    st.info(f"{status} | {details}")
