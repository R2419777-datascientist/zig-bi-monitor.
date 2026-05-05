import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import time
from datetime import datetime

# --- 1. PAGE CONFIG & CLEAN THEME ---
st.set_page_config(
    page_title="ZiG Agile BI Monitor",
    page_icon="🇿🇼",
    layout="wide"
)

# Clean CSS: Removed gold backgrounds, focused on high-contrast text
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    .news-card { 
        padding: 12px; 
        border-radius: 5px; 
        margin-bottom: 10px; 
        border: 1px solid #333;
        background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & NEWS LOGIC ---
def get_live_market_data():
    try:
        ticker = yf.Ticker("ZAR=X")
        df = ticker.history(period="1d", interval="1m").tail(35)
        # 1 ZAR = ~1.55 ZWG (Simulated Live Feed)
        df['ZiG_Price'] = df['Close'] * 1.55 
        df['SMA_5'] = df['ZiG_Price'].rolling(window=5).mean()
        return df.dropna()
    except:
        return pd.DataFrame()

def get_zim_news():
    rss_urls = [
        "https://herald.co.zw",
        "https://newsday.co.zw"
    ]
    all_headlines = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:
                all_headlines.append({"title": entry.title, "link": entry.link})
        except:
            continue
    return all_headlines

# --- 3. SIDEBAR ---
st.sidebar.title("BI Controls")
refresh_sec = st.sidebar.slider("Update Frequency (sec)", 30, 120, 60)
st.sidebar.divider()
st.sidebar.write("**Project Goal:** Real-time prescriptive analytics for volatile markets.")

# --- 4. MAIN DASHBOARD LOOP ---
placeholder = st.empty()

while True:
    df = get_live_market_data()
    news_items = get_zim_news()
    
    if not df.empty:
        curr = df['ZiG_Price'].iloc[-1]
        prev = df['ZiG_Price'].iloc[-2]
        change = (curr - prev) / prev
        sma = df['SMA_5'].iloc[-1]
        
        with placeholder.container():
            st.title("🇿🇼 ZiG Real-Time Decision Support")
            
            # --- ROW 1: KPI METRICS ---
            m1, m2, m3 = st.columns(3)
            m1.metric("Current USD/ZWG", f"{curr:.4f}", f"{change:.3%}")
            m2.metric("Trend Baseline (SMA)", f"{sma:.4f}")
            
            # Agile Prescriptive Logic
            if curr > sma:
                m3.error("🚨 STRATEGY: DEFENSIVE\n(Price above trend)")
            else:
                m3.success("✅ STRATEGY: EXPANSION\n(Price below trend)")

            # --- ROW 2: HIGH-CONTRAST CHART ---
            fig = go.Figure()
            
            # Primary Price Line - Clean Blue/Cyan
            fig.add_trace(go.Scatter(
                x=df.index, y=df['ZiG_Price'], 
                name="Live Price", 
                line=dict(color='#00d4ff', width=4)
            ))
            
            # Trend Line - High Visibility White Dash
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_5'], 
                name="5-Min Trend", 
                line=dict(color='#ffffff', width=2, dash='dot')
            ))
            
            fig.update_layout(
                template="plotly_dark",
                height=450,
                xaxis_title="Time",
                yaxis_title="Rate",
                margin=dict(l=0, r=0, t=20, b=0),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- ROW 3: INTELLIGENCE & LOGS ---
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("📰 Market Headlines")
                if news_items:
                    for item in news_items:
                        st.markdown(f"""<div class="news-card"><a href="{item['link']}" style="color:#58a6ff; text-decoration:none;">{item['title']}</a></div>""", unsafe_allow_html=True)
                else:
                    st.info("Awaiting new headlines...")

            with c2:
                st.subheader("📋 Decision Log")
                st.dataframe(df[['ZiG_Price', 'SMA_5']].tail(5), use_container_width=True)

    time.sleep(refresh_sec)
