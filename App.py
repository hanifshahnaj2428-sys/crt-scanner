import streamlit as st
import yfinance as yf
import pandas as pd

# মোবাইল স্ক্রিনের জন্য পেজ সেটআপ
st.set_page_config(page_title="CRT Mobile Scanner", page_icon="📱", layout="centered")

st.title("📱 CRT + MSS + FVG স্ক্যানার")
st.caption("মোবাইল ফরেক্স মার্কেট অ্যানালাইসিস টুল")

# স্ক্যান করার জন্য ফরেক্স পেয়ার লিস্ট
pairs = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "GOLD (XAU/USD)": "GC=F"
}

crt_tf = st.selectbox("CRT টাইমফ্রেম বেছে নিন:", ["1h", "4h"], index=0)

def analyze_crt(ticker, crt_timeframe):
    try:
        # ১. উচ্চতর টাইমফ্রেম থেকে আগের CRT ক্যান্ডেলের High ও Low নেওয়া
        htf_data = yf.download(ticker, period="5d", interval=crt_timeframe, progress=False)
        if len(htf_data) < 3:
            return "ডেটা পাওয়া যায়নি", "neutral", "-"
        
        # আগের ক্লোজ হওয়া ক্যান্ডেল
        prev_crt_high = float(htf_data['High'].iloc[-2])
        prev_crt_low = float(htf_data['Low'].iloc[-2])
        
        # ২. লোয়ার টাইমফ্রেম (15m) থেকে সুইপ, MSS এবং FVG চেক করা
        ltf_data = yf.download(ticker, period="2d", interval="15m", progress=False)
        if len(ltf_data) < 10:
            return "ডেটা অপর্যাপ্ত", "neutral", "-"
            
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
        
        # লজিক যাচাই
        swept_high = recent_high > prev_crt_high
        swept_low = recent_low < prev_crt_low
        
        if swept_high and current_close < swing_low and bearish_fvg:
            return "🔴 SELL (CRT + MSS + FVG)", "sell", f"Entry Zone: {round(c3_high, 4)} - {round(c1_low, 4)}"
        elif swept_low and current_close > swing_high and bullish_fvg:
            return "🟢 BUY (CRT + MSS + FVG)", "buy", f"Entry Zone: {round(c1_high, 4)} - {round(c3_low, 4)}"
        elif swept_high:
            return "⚠️ CRT High সুইপ হয়েছে (MSS/FVG অপেক্ষায়)", "wait", f"CRT High: {round(prev_crt_high, 4)}"
        elif swept_low:
            return "⚠️ CRT Low সুইপ হয়েছে (MSS/FVG অপেক্ষায়)", "wait", f"CRT Low: {round(prev_crt_low, 4)}"
        else:
            return "⚪ কোনো সেটআপ নেই", "neutral", f"Range: {round(prev_crt_low, 4)} - {round(prev_crt_high, 4)}"
            
    except Exception as e:
        return "এরর হয়েছে", "neutral", "-"

# স্ক্যান বাটন
if st.button("🔍 মার্কেট স্ক্যান করুন", use_container_width=True, type="primary"):
    with st.spinner("সবগুলো পেয়ার অ্যানালাইসিস করা হচ্ছে..."):
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
