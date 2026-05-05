import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import time
import json
import os
from datetime import datetime

# --- 1. DATA PERSISTENCE (USER DB) ---
USER_DB = "users.json"

def load_users():
    if not os.path.exists(USER_DB):
        return {"admin": "admin123"} # Default dev account
    with open(USER_DB, "r") as f:
        return json.load(f)

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DB, "w") as f:
        json.dump(users, f)

# --- 2. PAGE CONFIG & ENHANCED UI ---
st.set_page_config(page_title="ZiG Agile BI Monitor", page_icon="🇿🇼", layout="wide")

# Enhanced CSS for Glassmorphism UI
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stMetric { 
        background-color: #161b22; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .news-card { 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 12px; 
        border-left: 4px solid #00d4ff;
        background-color: #1c2128;
    }
    .auth-container {
        padding: 30px;
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.title("🇿🇼 ZiG BI Portal")
        auth_mode = st.tabs(["Login", "Create Account"])
        
        # --- LOGIN TAB ---
        with auth_mode[0]:
            login_user = st.text_input("Username", key="l_user")
            login_pass = st.text_input("Password", type="password", key="l_pass")
            if st.button("Access Dashboard"):
                users = load_users()
                if login_user in users and users[login_user] == login_pass:
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        # --- SIGN UP TAB ---
        with auth_mode[1]:
            new_user = st.text_input("Choose Username", key="s_user")
            new_pass = st.text_input("Choose Password", type="password", key="s_pass")
            conf_pass = st.text_input("Confirm Password", type="password")
            if st.button("Register"):
                users = load_users()
                if new_user in users:
                    st.warning("User already exists!")
                elif new_pass != conf_pass:
                    st.error("Passwords do not match")
                elif len(new_pass) < 6:
                    st.error("Password too short (min 6 chars)")
                else:
                    save_user(new_user, new_pass)
                    st.success("Account created! Please Login.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 4. DATA LOGIC ---
def get_live_market_data():
    try:
        ticker = yf.Ticker("ZAR=X")
        df = ticker.history(period="1d", interval="1m").tail(35)
        df['ZiG_Price'] = df['Close'] * 1.55 
        df['SMA_5'] = df['ZiG_Price'].rolling(window=5).mean()
        return df.dropna()
    except:
        return pd.DataFrame()

def get_zim_news():
    rss_urls = ["https://herald.co.zw"]
    all_headlines = []
    for url in rss_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                all_headlines.append({"title": entry.title, "link": entry.link})
        except: continue
    return all_headlines

# --- 5. DASHBOARD UI (LOGGED IN) ---
st.sidebar.title(f"Welcome, {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

refresh_sec = st.sidebar.slider("Refresh (sec)", 30, 120, 60)
st.sidebar.divider()
st.sidebar.markdown("### 📊 Portfolio Status")
st.sidebar.info("Account Type: Data Scientist (Admin)")

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
            
            # KPI Cards with enhanced visual style
            m1, m2, m3 = st.columns(3)
            m1.metric("USD/ZWG Rate", f"{curr:.4f}", f"{change:.3%}")
            m2.metric("SMA Trend", f"{sma:.4f}")
            
            if curr > sma:
                m3.error("🚨 STRATEGY: DEFENSIVE")
            else:
                m3.success("✅ STRATEGY: EXPANSION")

            # High-Contrast Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['ZiG_Price'], name="Price", line=dict(color='#00d4ff', width=4)))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_5'], name="SMA Trend", line=dict(color='#ffffff', width=2, dash='dot')))
            
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=20, b=0), hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            # Intelligence & News
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("📰 Market Intelligence")
                for item in news_items:
                    st.markdown(f"""<div class="news-card"><a href="{item['link']}" style="color:#58a6ff; text-decoration:none;">{item['title']}</a></div>""", unsafe_allow_html=True)

            with c2:
                st.subheader("📋 Decision Log")
                st.dataframe(df[['ZiG_Price', 'SMA_5']].tail(5), use_container_width=True)

    time.sleep(refresh_sec)
