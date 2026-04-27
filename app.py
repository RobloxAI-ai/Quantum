import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
import datetime
import time
import json
import os
import json
from supabase import create_client
# --- INITIALIZE SESSION STATE ---
# Create a dictionary to hold shares for each ticker separately
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {} 
from datetime import datetime, timedelta
# Adds 3 hours to the server time to match KSA
st.sidebar.write(f"{(datetime.utcnow() + timedelta(hours=3)).strftime('%H:%M:%S')}")
# Ensure cash and debt are ready
if 'balance' not in st.session_state:
    st.session_state.balance = 10000.0
if 'debt' not in st.session_state:
    st.session_state.debt = 0.0
def auto_sync():
    """Automatically pushes session data to Supabase with safety checks"""
    try:
        # We use .get(key, default) to prevent the "AttributeError"
        payload = {
            "username": st.session_state.get("current_agent", "Unknown_Agent"),
            "balance": float(st.session_state.get("balance", 10000.0)),
            "portfolio": int(st.session_state.get("portfolio", 0)),
            "debt": float(st.session_state.get("debt", 0.0))
        }
        
        # Only sync if we have a real username
        if payload["username"] != "Unknown_Agent":
            supabase.table("profiles").upsert(payload).execute()
    except Exception as e:
        # This will show you if there's a database problem without crashing the whole app
        print(f"Sync error (silent): {e}")
# Get these from your Supabase Project Settings API
url = "https://dnbjjudvjlocelfzihjl.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRuYmpqdWR2amxvY2VsZnppaGpsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMjE3NTgsImV4cCI6MjA5MjY5Nzc1OH0.0oKwthTuSxkghYI2173HDHxDukwkJ1yI187_GVhSoho"
supabase = create_client(url, key)
def login_screen():
    st.title("QUANTUM")
def sync_to_supabase():
    """Pushes your current balance and assets to the cloud"""
    if 'current_agent' in st.session_state:
        data = {
            "balance": float(st.session_state.user_data["balance"]),
            "portfolio": int(st.session_state.user_data["portfolio"]),
            "debt": float(st.session_state.user_data["debt"])
        }
        # This updates the row in Supabase that matches your username
        supabase.table("profiles").update(data).eq("username", st.session_state.current_agent).execute()   
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        u_name = st.text_input("Username", key="login_u")
        p_word = st.text_input("Password", type="password", key="login_p")
        if st.button("Access Terminal"):
            # Check Supabase for the user
            user = supabase.table("profiles").select("*").eq("username", u_name).eq("password", p_word).execute()
            if user.data:
                st.session_state.user_data = user.data[0]
                st.session_state.current_agent = u_name
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Agent Credentials.")

    with tab2:
        new_u = st.text_input("Choose Username", key="reg_u")
        new_p = st.text_input("Choose Password", type="password", key="reg_p")
        if st.button("Register New Agent"):
            # Save new user to Supabase
            data = {"username": new_u, "password": new_p, "balance": 10000.0, "portfolio": 0, "debt": 0.0}
            try:
                supabase.table("profiles").insert(data).execute()
                st.success("Registration Successful! Now Login.")
            except:
                st.error("Username already taken.")

# --- APP FLOW ---
if 'logged_in' not in st.session_state:
    login_screen()
else:
    # Your whole game code goes here!
    st.sidebar.write(f"Logged in as: **{st.session_state.current_agent}**")
    if st.sidebar.button("Logout"):
        del st.session_state.logged_in
        st.rerun()
def load_all_users():
    try:
        with open("user_database.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
DB_FILE = "user_database.json"
# --- EMERGENCY LOAN NOTIFICATION ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}
def save_user_data(user_id, data):
    db = load_db()
    db[user_id] = data
    with open(DB_FILE, "w") as f:
        json.dump(db, f)
    # --- ADD THIS AT LINE 21 ---
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = ""
# --- TOP OF FILE ---
def detect_pattern(df):
    try:
        # Check if we have enough data to compare
        if len(df) < 2:
            return "Gathering Data..."
            
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        if last['Close'] > prev['Open'] and prev['Close'] < prev['Open']:
            return "Bullish Engulfing"
        elif last['Close'] < prev['Open'] and prev['Close'] > prev['Open']:
            return "❄️ Bearish Engulfing"
        return "⚖️ Consolidation"
    except Exception:
        return "Analyzing..."
# --- CONFIG ---
st.set_page_config(page_title="QUANTUM-EYE Terminal", layout="wide", page_icon="📈")

# --- SESSION STATE (Money & Portfolio) ---
if 'trade_log' not in st.session_state:
    st.session_state.trade_log = []
if 'balance' not in st.session_state:
    st.session_state.balance = 10000.0
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = 0

# --- FRAGMENT 1: THE SMOOTH CLOCK ---
@st.fragment(run_every="1s")
def render_clock():
    now = datetime.datetime.now()
    st.markdown(f"""
        <div style="background-color: #161B22; border: 1px solid #30363D; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;">
            <span style="color: #00FFC8; font-size: 1.5em; font-family: monospace; font-weight: bold;">{now.strftime("%H:%M:%S")}</span>
            <span style="color: #8B949E; margin-left: 15px;">| {now.strftime("%b %d, %Y")}</span>
        </div>
    """, unsafe_allow_html=True)

render_clock()
# --- TICKER TAPE ---
@st.cache_data(ttl=600)
def get_tape_data():
    assets = {
        "BTC-USD": "Bitcoin", 
        "ETH-USD": "Ethereum", 
        "GC=F": "Gold", 
        "CL=F": "Oil", 
        "^GSPC": "S&P 500"
    }
    
    try:
        # 1. Download 5 days to cover the weekend gap
        raw_data = yf.download(list(assets.keys()), period="5d", interval="1d")['Close']
        
        # 2. Fix the "MultiIndex" issue (flattens the table)
        if isinstance(raw_data, pd.DataFrame):
            # Fill missing values and take the most recent row
            latest_prices = raw_data.ffill().iloc[-1]
        else:
            latest_prices = raw_data

        tape_items = []
        for ticker, name in assets.items():
            # 3. Extract the price safely
            price = latest_prices[ticker]
            if pd.notna(price):
                tape_items.append(f"{name}: ${price:,.2f}")
            else:
                tape_items.append(f"{name}: Closed")
        
        return "  |  ".join(tape_items)

    except Exception:
        # Fallback if the internet or API glitches
        return "Market Data Syncing... | Bitcoin: Live | Gold: Friday Close"

# --- RENDER TAPE ---
tape_str = get_tape_data()
st.markdown(f"""
    <marquee style="color: #00FFC8; font-family: monospace; font-size: 1.2em; background: #161B22; padding: 5px; border-radius: 5px;">
        {tape_str}
    </marquee>
""", unsafe_allow_html=True)
# --- REPLACE LINES 105-125 WITH THIS ---
with st.sidebar:
    st.header("Terminal Access")
    u_id = st.text_input("Agent ID", key="uid").strip()
    u_pwd = st.text_input("Access Key", type="password", key="pwd").strip()
    
    if st.button("AUTHENTICATE", use_container_width=True):
        users = load_db()
        if u_id in users and users[u_id]["key"] == u_pwd:
            st.session_state.user_data = users[u_id]
            st.session_state.current_agent = u_id
            st.success("Authorized")
            st.rerun()
        elif u_id not in users and u_id != "":
            # 1. NEW: Check if this Access Key (password) is already being used by someone else
            password_exists = any(user_info.get('key') == u_pwd for user_info in users.values())

            if u_id.strip().lower() == u_pwd.strip().lower():
                st.sidebar.error("SECURITY ERROR: Access Key cannot match Agent ID.")
            
            elif password_exists:
                st.sidebar.error("ERROR: Access Key already used. Choose a different password.")
            
            else:
                # 2. Proceed with registration if unique
                new_profile = {
                    "key": u_pwd, 
                    "balance": 10000.0, 
                    "portfolio": {}, 
                    "debt": 0.0,
                    "history": []
                }
                save_user_data(u_id, new_profile)
                st.session_state.user_data = new_profile
                st.session_state.current_agent = u_id
                st.sidebar.success("New Agent Registered")
                st.rerun()
        else:
            st.error("Invalid Credentials")

    if not st.session_state.get("user_data"):
        st.stop()

    # Define ticker and days only if authorized
    ticker = st.selectbox("Select Asset", ["2222.SR", "1120.SR", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "NFLX", "LLY", "META", "TSM", "BTC-USD", "GC=F", "CL=F"], key="tk")
    days = st.slider("Forecast Days", 7, 90, 30, key="ds")
    
    # THE ASSET GUIDE (Legend)
with st.expander("VIEW ASSET LEGEND"):
        # We create a simple dictionary for the legend
        legend_data = {
            "Market": [
                "Saudi Aramco", "Al Rajhi Bank", "Nvidia Corp", "Apple Inc", 
                "Microsoft", "Amazon", "Alphabet", "Tesla Motors", 
                "Netflix", "Eli Lilly", "Meta Platforms", "TSMC Chips", 
                "Bitcoin", "Gold Futures", "Oil"
            ],
            "Symbol": [
                "2222.SR", "1120.SR", "NVDA", "AAPL", 
                "MSFT", "AMZN", "GOOGL", "TSLA", 
                "NFLX", "LLY", "META", "TSM", 
                "BTC-USD", "GC=F", "CL=F"
            ]
        }
        
        # Display as a clean, static table
        st.table(legend_data)
        
        st.caption("Use these symbols in the Search Bar for manual lookup.")
    # --- UPDATED DATA ENGINE ---
@st.cache_data(ttl=300)
def get_terminal_data(symbol):
    t = yf.Ticker(symbol)
    df = t.history(period="2y")
    
    # Flatten columns if multi-indexed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # 1. SMAs
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    
    # 2. RSI CALCULATION (This fixes the KeyError)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Handle any empty news/info
    info = t.info if t.info else {}
    news = t.news if t.news else []
    
    return df, info, news

data, info, news = get_terminal_data(ticker)
current_price = float(data['Close'].iloc[-1])
# --- DEFINE ALL USER VARIABLES ---
# This pulls the data from your save file into the script
current_balance = st.session_state.user_data.get("balance", 0.0)
current_shares = st.session_state.user_data.get("portfolio", 0)
current_debt = st.session_state.user_data.get("debt", 0.0)

# Create a shorthand variable to fix the yellow underlines
balance = current_balance
# --- TRADING SIMULATOR SECTION ---
st.markdown("---")
# 1. Get the dictionary of all assets
portfolio_dict = st.session_state.user_data.get("portfolio", {})

# 2. Calculate the total sum
if isinstance(portfolio_dict, dict):
    total_shares_sum = sum(portfolio_dict.values())
else:
    total_shares_sum = int(portfolio_dict)

# 3. Layout for the far right margin
left_spacer, right_margin = st.columns([4, 1])

with right_margin:
    # Show the Total Shares Header
    st.markdown(
        f"<p style='text-align: right; color: #8B949E; font-size: 0.9em; margin-bottom: 0px;'>"
        f"TOTAL SHARES: <b style='color: #00FFC8;'>{total_shares_sum}</b></p>", 
        unsafe_allow_html=True
    )
    
    # 4. If shares exist, show the breakdown
    if total_shares_sum > 0 and isinstance(portfolio_dict, dict):
        for ticker_name, share_count in portfolio_dict.items():
            if share_count > 0:
                # Display each market and its shares in a smaller, clean text
                st.markdown(
                    f"<p style='text-align: right; color: #8B949E; font-size: 0.8em; margin: 0px;'>"
                    f"{ticker_name}: <b style='color: #ffffff;'>{share_count}</b></p>", 
                    unsafe_allow_html=True
                )
# --- RE-CALCULATE EVERYTHING TO CLEAR YELLOW LINES ---
# 1. Get the latest price from your data fetch
# 1. Fetch current price
current_price = float(data['Close'].iloc[-1])
# --- LOCK SYSTEM ---
# This checks if the user's debt is dangerously high
is_locked = current_debt > 45000  # You can change 5000 to whatever limit you want

if is_locked:
    st.error("**BUYING LOCKED**: Debt is too high. Pay back at least $1000 to attempt to unlock.")
# 2. Pull user data
current_balance = st.session_state.user_data.get("balance", 0.0)
current_shares = st.session_state.user_data.get("portfolio", 0)
current_debt = st.session_state.user_data.get("debt", 0.0)

# 3. THIS LINE REMOVES THE YELLOW UNDERLINE:
# 1. Get the dictionary of all stocks
all_assets = st.session_state.user_data.get("portfolio", {})

# 2. Extract ONLY the shares for the current market (e.g., NVDA)
# If 'all_assets' is still a number from your old code, we treat it as 0 to avoid the error
if isinstance(all_assets, dict):
    current_market_shares = all_assets.get(ticker, 0) if isinstance(all_assets, dict) else 0
    st.metric(label=f"Your {ticker} Shares", value=current_market_shares)
else:
    current_market_shares = 0

# 3. Calculate the value correctly
total_value = current_balance + (current_market_shares * current_price)

# 4. Final Net Worth and P/L
net_worth = total_value - current_debt
raw_delta = round(float(net_worth - 10000.0), 2)

# 3. Create the layout
col_bal, col_buy, col_sell = st.columns([2, 1, 1])

# 1. Pull the values from the dictionary
user_info = st.session_state.user_data
current_balance = user_info["balance"]
current_shares = user_info["portfolio"]

# --- CLEAN FINANCIAL DISPLAY ---
# Use the .get() method to prevent crashes on old accounts
current_debt = st.session_state.user_data.get("debt", 0.0)
current_balance = st.session_state.user_data.get("balance", 0.0)

# Calculate net worth correctly (Assets - Liabilities)
net_worth = total_value - current_debt
raw_delta = round(float(net_worth - 10000.0), 2)

with col_bal:
    st.metric("Total Net Worth", f"${total_value:,.2f}", delta=raw_delta)
    # This single line below handles the Cash and Red Debt text
    # Simple alternative if the red color syntax fails:
    # Create a small sub-layout for the text labels
c1, c2, c3 = st.columns(3)
with c1:
    st.write(f"Cash: **${current_balance:,.2f}**")
with c2:
    # This uses a simple "if" to color the debt only if you owe money
    if current_debt > 0:
        st.error(f"Debt: ${current_debt:,.2f}")
    else:
        st.write(f"Debt: $0.00")
# 1. Look into the portfolio dictionary for ONLY this ticker
# We check user_data since that is what saves to your JSON
portfolio_dict = st.session_state.user_data.get("portfolio", {})

if isinstance(portfolio_dict, dict):
    current_shares = portfolio_dict.get(ticker, 0)
else:
    current_shares = 0  # Fallback if it's a new account
with c3:
    st.write(f"Shares: **{current_shares}**")

# 3. Define the order quantity
order_qty = st.number_input("Order Quantity", min_value=1, value=1, step=1)

# 2. Now you can use it in your buttons
col_buy, col_sell, col_all = st.columns(3)

with col_buy:
    if st.button(f"BUY {order_qty}", use_container_width=True, disabled=is_locked):
        cost = order_qty * current_price
        
        # 1. CHECK MONEY FIRST
        if current_balance >= cost:
            # 2. DEDUCT CASH
            st.session_state.user_data["balance"] -= cost
            
            # 3. FIX THE SHARE PROBLEM: Use the ticker as a key inside user_data
            # Initialize the portfolio dictionary if it doesn't exist
            if "portfolio" not in st.session_state.user_data or isinstance(st.session_state.user_data["portfolio"], (int, float)):
                st.session_state.user_data["portfolio"] = {}

            # Add shares to the specific ticker pocket
            if ticker not in st.session_state.user_data["portfolio"]:
                st.session_state.user_data["portfolio"][ticker] = 0
            
            st.session_state.user_data["portfolio"][ticker] += order_qty

            # 4. SAVE AND REFRESH
            save_user_data(st.session_state.current_agent, st.session_state.user_data)
            st.success(f"Bought {order_qty} {ticker}!")
            st.rerun()
        else:
            st.error("Not enough cash!")
with col_sell:
    # Use the variable we just defined above
    can_sell = current_market_shares >= order_qty if order_qty > 0 else False
    
    if st.button(f"SELL {order_qty}", use_container_width=True, disabled=not can_sell):
        gain = order_qty * current_price
        
        # 1. Update Cash
        st.session_state.user_data["balance"] += gain
        
        # 2. Subtract Shares from the specific pocket
        st.session_state.user_data["portfolio"][ticker] -= order_qty
        
        # 3. Save to JSON
        save_user_data(st.session_state.current_agent, st.session_state.user_data)
        st.success(f"Sold {order_qty} {ticker} for ${gain:,.2f}!")
        st.rerun()
    elif order_qty > 0 and not can_sell:
        st.error(f"You don't have {order_qty} shares of {ticker} to sell!")
if st.button("SELL ALL SHARES", use_container_width=True):
    if current_shares > 0:
        # Calculate total payout
        sale_proceeds = current_shares * current_price
        
        # Update Session State
        st.session_state.user_data["balance"] += sale_proceeds
        st.session_state.user_data["portfolio"] = 0
        
        # Log the transaction
        st.session_state.user_data["history"].append(f"Sold All: {current_shares} shares @ ${current_price:,.2f}")
        
        # Save to database and refresh
        save_user_data(st.session_state.current_agent, st.session_state.user_data)
        st.success(f"Liquidated portfolio for ${sale_proceeds:,.2f}")
        st.rerun()
    else:
        st.error("You have no shares to sell!")
# Inside your BUY button logic
st.session_state.trade_log.append({
    "Time": datetime.datetime.now().strftime("%H:%M:%S"),
    "Type": "BUY",
    "Asset": ticker,
    "Price": f"${current_price:.2f}"
})

# Inside your SELL button logic
st.session_state.trade_log.append({
    "Time": datetime.datetime.now().strftime("%H:%M:%S"),
    "Type": "SELL",
    "Asset": ticker,
    "Price": f"${current_price:.2f}"
})
# Run this once after you buy/sell to push your local $14k to the cloud
def sync_to_cloud():
    data = {
        "username": st.session_state.current_agent,
        "balance": float(st.session_state.balance),
        "portfolio": int(st.session_state.portfolio),
        "debt": float(st.session_state.debt)
    }
    # This sends your data to Supabase
    supabase.table("profiles").upsert(data).execute()
    st.success("Synced to Global Cloud!")

# --- RISK ANALYTICS ---
st.markdown("---")
risk_col, vol_col, trend_col = st.columns(3)

# Calculate RSI Status
last_rsi = data['RSI'].iloc[-1]
if last_rsi > 70:
    status, color = "OVERBOUGHT (Risk High)", "#FF4B4B"
elif last_rsi < 30:
    status, color = "OVERSOLD (Bargain)", "#00FFC8"
else:
    status, color = "NEUTRAL", "#8B949E"

risk_col.metric("Market Sentiment", "Greed" if last_rsi > 50 else "Fear")
vol_col.metric("RSI (14D)", f"{last_rsi:.2f}")
trend_col.markdown(f"**Signal:** <span style='color:{color};'>{status}</span>", unsafe_allow_html=True)

# --- MAIN CHARTS ---
st.subheader("Market Dynamics")
fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Price")])
fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], line=dict(color='#FFD700', width=1.5), name='SMA 20'))
fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=400, margin=dict(t=0, b=0))
st.plotly_chart(fig, use_container_width=True)
st.subheader("Market Correlation (vs. S&P 500)")

# --- FIXED COMPARISON ENGINE ---
@st.cache_data(ttl=600)
def get_comparison_data(symbol):
    # Fetch data for S&P 500 and the Asset
    spy = yf.download("^GSPC", period="1mo")['Close']
    asset = yf.download(symbol, period="1mo")['Close']
    
    # Fix for MultiIndex (removes the extra headers if they exist)
    if isinstance(spy, pd.DataFrame): spy = spy.iloc[:, 0]
    if isinstance(asset, pd.DataFrame): asset = asset.iloc[:, 0]
    
    # Normalize to % starting from 100 for a fair comparison
    spy_norm = (spy / spy.iloc[0]) * 100
    asset_norm = (asset / asset.iloc[0]) * 100
    return spy_norm, asset_norm

# --- RENDER COMPARISON CHART ---
st.subheader(f"⚖️ {ticker} vs. S&P 500 (1 Month Performance)")
try:
    spy_p, asset_p = get_comparison_data(ticker)
    
    comp_fig = go.Figure()
    # Broad Market Line
    comp_fig.add_trace(go.Scatter(
        x=spy_p.index, y=spy_p, 
        name="S&P 500 (Market)", 
        line=dict(color="#8B949E", width=1, dash='dot')
    ))
    # Your Selected Asset Line
    comp_fig.add_trace(go.Scatter(
        x=asset_p.index, y=asset_p, 
        name=ticker, 
        line=dict(color="#00FFC8", width=3)
    ))
    
    comp_fig.update_layout(
        template="plotly_dark", 
        height=300, 
        margin=dict(t=20, b=20, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(comp_fig, use_container_width=True)
except Exception as e:
    st.error(f"Correlation Data Sync Error: {e}")

# --- 7. COMPANY INTEL & NEWS ---
st.markdown("---")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Company Profile & Intelligence")
    
    # Create a nice dark container for the stats
    with st.container(border=True):
        # Professional Stats
        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        st.write(f"**Market Cap:** ${info.get('marketCap', 0):,}")
        
        # --- THE AI SIGNAL ---
        # This uses the function we moved to the top of the file
        signal = detect_pattern(data)
        st.markdown(f"**Technical Signal:** {signal}")
        
        # Small Divider
        st.markdown("---")
        
        # Summary Expander so it doesn't take up too much space
        with st.expander("View Business Summary"):
            st.write(info.get('longBusinessSummary', 'No company summary available.'))

with c2:
    st.subheader("Live Market News")
    # Loop through the news and create professional link buttons
    if news:
        for n in news[:3]:
            # Guard against None values in the news title
            raw_title = n.get('title') or "Market Update"
            clean_title = raw_title[:60] + "..."
            
            # Using link_button makes it look like a real terminal
            st.link_button(
                f"{n.get('publisher', 'Finance')}: {clean_title}", 
                n.get('link', 'https://finance.yahoo.com'),
                use_container_width=True
            )
    else:
        st.info("Searching for recent news updates...")
# --- AI PREDICTION (Fragment 2: Heavy but Isolated) ---
st.markdown("---")
st.subheader("AI Prophet Prediction")

@st.cache_data(ttl=3600) # Only calculate AI once per hour per stock
def run_ai_logic(df, p_days):
    df_p = df.reset_index()[['Date', 'Close']]
    df_p.columns = ['ds', 'y']
    df_p['ds'] = df_p['ds'].dt.tz_localize(None)
    m = Prophet(interval_width=0.95)
    m.fit(df_p)
    fut = m.make_future_dataframe(periods=p_days)
    fcst = m.predict(fut)
    return fcst

forecast = run_ai_logic(data, days)
fig_ai = go.Figure()
fig_ai.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name='AI Forecast', line=dict(color='#00FFC8')))
fig_ai.update_layout(template="plotly_dark", height=350)
st.plotly_chart(fig_ai, use_container_width=True)
with st.expander("View Session Trade History"):
    if st.session_state.trade_log:
        df_log = pd.DataFrame(st.session_state.trade_log)
        st.table(df_log.iloc[::-1]) # Shows newest trades first
    else:
        st.write("No trades executed in this session.")
# --- LOAN SYSTEM ---
if current_balance < 500:
    # A big red alert that only shows when you are broke
    st.error("**LIQUIDITY ALERT**: Your funds are critically low ($" + str(round(current_balance, 2)) + ")")
    
    if st.button("🏛️ VISIT BANK FOR LOAN", type="primary", use_container_width=True):
        st.session_state.page = "bank"
        st.rerun()

if st.session_state.get("page") == "bank":
    st.title("Global Lending Terminal")
    
    col1, col2 = st.columns(2)
    with col1:
        country = st.selectbox("Select Jurisdiction", ["Saudi Arabia", "USA", "UK", "Switzerland"])
        bank = st.selectbox("Select Institution", ["Arabia Bank", "NB", "J.J. Morgan", "CSBH"])
    
    with col2:
        name = st.text_input("Confirm Legal Name")
        amount = st.number_input("Loan Amount ($)", min_value=1000, max_value=50000)

    interest_rate = 0.05 if country == "Saudi Arabia" else 0.08 # Real-world rates vary
    
    if st.button("SIGN LOAN AGREEMENT"):
        # update balance and debt
        st.session_state.user_data["balance"] += amount
        st.session_state.user_data["debt"] += amount * (1 + interest_rate)
        save_user_data(st.session_state.current_agent, st.session_state.user_data)
        st.session_state.page = "main" # Go back
        st.success(f"Funds Wired. Total Debt: ${st.session_state.user_data['debt']:,.2f}")
        st.rerun()
    # --- DEBT ENFORCEMENT ---
if current_debt> 0 and current_balance <= 0 and current_shares > 0:
    st.error("**ASSET SEIZURE**: The bank has sold your shares to cover your debt!")
    
    # Sell 1 share automatically to pay the bank
    st.session_state.user_data["portfolio"] -= 1
    st.session_state.user_data["debt"] -= current_price
    
    save_user_data(st.session_state.current_agent, st.session_state.user_data)
    st.rerun()
# Add this near your other math
if current_debt > 0:
    # Every 'action' adds a tiny bit of interest
    st.session_state.user_data["debt"] *= 1.001
if current_debt > 0:
    st.markdown("### Repayment Terminal")
    
    # Simple button to pay exactly $100
    if st.button("PAY $100 TOWARDS DEBT", use_container_width=True):
        if current_balance >= 1000:
            st.session_state.user_data["balance"] -= 1000
            st.session_state.user_data["debt"] -= 1000
            
            save_user_data(st.session_state.current_agent, st.session_state.user_data)
            st.success("Payment received! Debt reduced.")
            st.rerun()
        else:
            st.error("You don't even have $1000 in cash!")
# --- FULL DEBT REPAYMENT LOGIC ---
if current_debt > 0:
    st.markdown("---")
    st.subheader("🏛️ Debt Settlement")
    
    # Show exactly what is owed
    st.warning(f"Total Outstanding: **${current_debt:,.2f}**")
    
    if st.button("PAY OFF ALL DEBT", use_container_width=True, type="primary"):
        if current_balance >= current_debt:
            # The Math: Subtract debt from cash and set debt to zero
            st.session_state.user_data["balance"] -= current_debt
            st.session_state.user_data["debt"] = 0.0
            
            # Save the new state
            save_user_data(st.session_state.current_agent, st.session_state.user_data)
            
            st.success("Debt cleared! Your credit score is safe.")
            st.rerun()
        else:
            # If they can't afford the whole thing, show how much they're short
            shortfall = current_debt - current_balance
            st.error(f"Insufficient Cash! You need ${shortfall:,.2f} more to clear this debt.")

def quantum_leaderboard():
    st.markdown("---")
    st.header("Global Wealth Leaderboard")

    file_path = "user_database.json"

    try:
        # 1. Fetch data from the local JSON file
        if not os.path.exists(file_path):
            st.info("The market is empty. Start trading to create the database!")
            return

        with open(file_path, "r") as f:
            players_dict = json.load(f)

        if not players_dict:
            st.info("No agents found in the database.")
            return

        # 2. Get the current stock price for live valuation
        live_price = st.session_state.get('current_price', 1.0)

        # 3. Process every player's Net Worth from the JSON structure
        processed_list = []
        for username, stats in players_dict.items():
            # Handle the portfolio correctly (summing up all shares across markets)
            portfolio_data = stats.get('portfolio', 0)
            
            # If portfolio is a dictionary (X: 9, Y: 0), sum the values
            if isinstance(portfolio_data, dict):
                total_shares = sum(portfolio_data.values())
            else:
                total_shares = int(portfolio_data)

            # Formula: Cash + (Total Shares * Live Price) - Debt
            net_worth = (
                float(stats.get('balance', 0)) + 
                (total_shares * live_price) - 
                float(stats.get('debt', 0))
            )
            
            processed_list.append({
                "Agent": username,
                "Value": net_worth,
                "Debt": float(stats.get('debt', 0))
            })

        # 4. Sort by Value (Richest at the top)
        processed_list.sort(key=lambda x: x["Value"], reverse=True)

        # 5. Format the table for the UI
        ui_table = []
        for i, entry in enumerate(processed_list):
            ui_table.append({
                "Rank": i + 1,
                "Agent Name": entry["Agent"],
                "Net Worth": f"${entry['Value']:,.2f}",
                "Status": "In Debt" if entry["Debt"] > 0 else "Clean"
            })

        # 6. Render the Table
        st.table(ui_table)

    except Exception as e:
        st.error(f"Leaderboard Error: {e}")

# --- RUN IT ---
quantum_leaderboard()
# --- LEGAL DISCLAIMER ---
st.sidebar.markdown("---")
st.sidebar.warning("""
**DISCLAIMER** This is a **TRADING SIMULATOR**.  
No real money is involved. All balances, debts, and profits are purely digital for educational and entertainment purposes.
""")
