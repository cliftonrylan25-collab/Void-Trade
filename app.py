import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import datetime
import time

# ==========================================
# PAGE CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="TERMINAL: LIQUIDITY RUN", layout="wide", initial_sidebar_state="expanded")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
html, body, [class*="css"], [class*="st-"] {
    font-family: 'Share Tech Mono', monospace !important;
}
.stApp {
    background-color: #0d1117;
    color: #c9d1d9;
}
h1, h2, h3 {
    color: #58a6ff !important;
    text-transform: uppercase;
    text-shadow: 0 0 5px rgba(88, 166, 255, 0.3);
}
div[data-testid="stMetricValue"] {
    color: #3fb950 !important;
    font-size: 1.5rem !important;
    text-shadow: 0 0 5px rgba(63, 185, 80, 0.4);
}
div[data-testid="stMetricDelta"] {
    font-size: 1rem !important;
}
.metric-container {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-left: 4px solid #58a6ff;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 10px;
}
.danger-metric {
    border-left: 4px solid #f85149 !important;
}
.danger-metric div[data-testid="stMetricValue"] {
    color: #f85149 !important;
    text-shadow: 0 0 5px rgba(248, 81, 73, 0.4);
}
.stButton>button {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 4px;
    width: 100%;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
    border-color: #8b949e;
    background-color: #30363d;
}
.buy-btn>button {
    background-color: #238636 !important;
    border-color: #2ea043 !important;
    color: white !important;
    font-weight: bold;
}
.sell-btn>button {
    background-color: #da3633 !important;
    border-color: #f85149 !important;
    color: white !important;
    font-weight: bold;
}
.news-ticker {
    background-color: #000;
    color: #ff7b72;
    padding: 10px;
    border: 1px dashed #ff7b72;
    font-size: 0.9rem;
    margin-bottom: 20px;
}
.log-box {
    background-color: #0d1117;
    border: 1px solid #30363d;
    padding: 10px;
    height: 200px;
    overflow-y: scroll;
    font-size: 0.8rem;
    color: #8b949e;
}
hr {
    border-color: #30363d;
}
.skill-card {
    background: #161b22;
    border: 1px solid #30363d;
    padding: 10px;
    margin-bottom: 10px;
    border-radius: 4px;
}
.skill-card h4 {
    margin-top: 0;
    color: #d2a8ff !important;
    font-size: 14px;
}
.skill-owned {
    border-color: #3fb950;
    box-shadow: 0 0 8px rgba(63,185,80,0.2);
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================
# TECHNICAL ANALYSIS ENGINE
# ==========================================
def calc_sma(series, window):
    return series.rolling(window=window, min_periods=1).mean()

def calc_ema(series, window):
    return series.ewm(span=window, adjust=False, min_periods=1).mean()

def calc_bollinger_bands(series, window=20, num_std=2):
    sma = calc_sma(series, window)
    rolling_std = series.rolling(window=window, min_periods=1).std()
    upper_band = sma + (rolling_std * num_std)
    lower_band = sma - (rolling_std * num_std)
    return upper_band, sma, lower_band

def calc_macd(series, fast=12, slow=26, signal=9):
    exp1 = calc_ema(series, fast)
    exp2 = calc_ema(series, slow)
    macd = exp1 - exp2
    macd_signal = calc_ema(macd, signal)
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def calc_rsi(series, window=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=window-1, adjust=False, min_periods=1).mean()
    ema_down = down.ewm(com=window-1, adjust=False, min_periods=1).mean()
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    rsi[:] = np.where(ema_down == 0, 100, rsi)
    return rsi

# ==========================================
# MARKET ASSET CLASS
# ==========================================
class MarketAsset:
    def __init__(self, symbol, name, initial_price, volatility, drift):
        self.symbol = symbol
        self.name = name
        self.initial_price = initial_price
        self.volatility = volatility
        self.base_drift = drift
        self.current_drift = drift
        self.history = self._generate_initial_data(100)
        self.current_price = self.history.iloc[-1]['close']
        self.trend_duration = 0
        self.active_event = None

    def _generate_initial_data(self, periods):
        dates = [datetime.datetime.now() - datetime.timedelta(minutes=i) for i in range(periods, 0, -1)]
        data = []
        price = self.initial_price
        for d in dates:
            open_p = price
            high_p = price * (1 + abs(np.random.normal(0, self.volatility)))
            low_p = price * (1 - abs(np.random.normal(0, self.volatility)))
            close_p = price * (1 + np.random.normal(self.base_drift, self.volatility))
            
            # Ensure proper candlestick logic
            high_p = max(high_p, open_p, close_p)
            low_p = min(low_p, open_p, close_p)
            
            vol = int(np.random.normal(10000, 2000))
            data.append([d, open_p, high_p, low_p, close_p, max(0, vol)])
            price = close_p
            
        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        return df

    def process_tick(self, master_volatility_mod):
        last_close = self.history.iloc[-1]['close']
        open_p = last_close
        
        # Trend persistence logic
        if self.trend_duration > 0:
            self.trend_duration -= 1
        else:
            self.current_drift = self.base_drift + np.random.normal(0, 0.002)
            self.active_event = None
            
        total_volatility = self.volatility * master_volatility_mod
        
        # Geometric Brownian Motion step
        shock = np.random.normal(self.current_drift, total_volatility)
        close_p = open_p * (1 + shock)
        
        # Intra-tick extremes
        high_p = max(open_p, close_p) * (1 + abs(np.random.normal(0, total_volatility/2)))
        low_p = min(open_p, close_p) * (1 - abs(np.random.normal(0, total_volatility/2)))
        
        vol = int(np.random.normal(15000, 5000))
        new_row = pd.DataFrame([[datetime.datetime.now(), open_p, high_p, low_p, close_p, max(0, vol)]], 
                               columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        self.history = pd.concat([self.history, new_row], ignore_index=True)
        self.history = self.history.iloc[1:] # Keep window size fixed
        self.current_price = close_p

    def apply_event(self, impact, duration, description):
        self.current_drift = impact
        self.trend_duration = duration
        self.active_event = description

# ==========================================
# NEWS & EVENT ENGINE
# ==========================================
class NewsEngine:
    def __init__(self):
        self.events = [
            {"msg": "Federal Reserve signals surprise interest rate hike.", "impact": -0.015, "dur": 8, "type": "bear"},
            {"msg": "Institutional whales accumulating massive positions.", "impact": 0.012, "dur": 6, "type": "bull"},
            {"msg": "Regulatory bodies announce strict compliance frameworks.", "impact": -0.008, "dur": 10, "type": "bear"},
            {"msg": "Quarterly earnings exceed expectations across sectors.", "impact": 0.015, "dur": 5, "type": "bull"},
            {"msg": "Flash crash initiated by high-frequency trading algorithms.", "impact": -0.03, "dur": 3, "type": "crash"},
            {"msg": "Geopolitical tensions threaten global supply chains.", "impact": -0.01, "dur": 12, "type": "bear"},
            {"msg": "Breakthrough in proprietary algorithmic trading logic.", "impact": 0.02, "dur": 4, "type": "bull"}
        ]
        self.current_news = "MARKET STABLE. AWAITING VOLATILITY TRIGGERS."
        self.global_vol_mod = 1.0

    def roll_event(self, assets):
        if random.random() < 0.15: # 15% chance per tick for an event
            event = random.choice(self.events)
            self.current_news = f"BREAKING: {event['msg']}"
            
            # Affect random asset or market wide
            target = random.choice(assets)
            target.apply_event(event['impact'], event['dur'], event['msg'])
            
            if event['type'] == 'crash':
                self.global_vol_mod = 3.0
            elif event['type'] == 'bull' or event['type'] == 'bear':
                self.global_vol_mod = 1.5
        else:
            # Decay global volatility back to normal
            self.global_vol_mod = max(1.0, self.global_vol_mod - 0.1)

# ==========================================
# PORTFOLIO & TRADER STATE
# ==========================================
class Portfolio:
    def __init__(self, starting_balance=10000.0):
        self.cash = starting_balance
        self.positions = [] # List of dicts
        self.peak_equity = starting_balance
        self.reputation = 0
        self.total_trades = 0
        self.win_streak = 0
        self.upgrades = {
            "apex": False,
            "loot": False,
            "sohc4v": False,
            "insider": False
        }
        self.action_log = ["SYSTEM INITIALIZED. PORTFOLIO AT $10,000."]

    def log(self, msg):
        self.action_log.insert(0, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
        if len(self.action_log) > 50:
            self.action_log.pop()

    def get_equity(self, current_prices):
        equity = self.cash
        for pos in self.positions:
            current_price = current_prices[pos['symbol']]
            if pos['type'] == 'LONG':
                pnl = (current_price - pos['entry']) * pos['qty']
            else: # SHORT
                pnl = (pos['entry'] - current_price) * pos['qty']
            equity += pnl
        
        if equity > self.peak_equity:
            self.peak_equity = equity
            
        return equity

    def get_margin_usage(self, current_prices):
        total_exposure = 0
        for pos in self.positions:
            total_exposure += (current_prices[pos['symbol']] * pos['qty'])
        
        equity = self.get_equity(current_prices)
        if equity <= 0:
            return 100.0
        return min(100.0, (total_exposure / (equity * 10)) * 100) # Assuming max 10x leverage allowed globally

    def execute_trade(self, symbol, current_price, trade_type, leverage, amount_pct):
        equity = self.get_equity({symbol: current_price}) # Approx, doesn't need all prices just for sizing
        
        if equity <= 0:
            return False, "Insufficient Equity"
            
        trade_capital = equity * (amount_pct / 100.0)
        notional_value = trade_capital * leverage
        
        # Calculate quantity based on current price
        qty = notional_value / current_price
        
        # Slippage simulation (reduced if SOHC4V upgrade is owned)
        slippage_pct = random.uniform(0.0005, 0.002)
        if self.upgrades['sohc4v']:
            slippage_pct *= 0.2 # 80% reduction in slippage
            
        entry_price = current_price * (1 + slippage_pct) if trade_type == 'LONG' else current_price * (1 - slippage_pct)
        
        self.positions.append({
            'symbol': symbol,
            'type': trade_type,
            'entry': entry_price,
            'qty': qty,
            'leverage': leverage,
            'initial_capital': trade_capital
        })
        
        self.cash -= trade_capital
        self.log(f"EXECUTED {trade_type} {symbol} | Lev: {leverage}x | Qty: {qty:.2f} @ ${entry_price:.2f}")
        return True, "Trade Executed"

    def close_position(self, index, current_prices):
        if index < 0 or index >= len(self.positions): return
        
        pos = self.positions.pop(index)
        current_price = current_prices[pos['symbol']]
        
        if pos['type'] == 'LONG':
            pnl = (current_price - pos['entry']) * pos['qty']
        else:
            pnl = (pos['entry'] - current_price) * pos['qty']
            
        gross_return = pos['initial_capital'] + pnl
        self.cash += gross_return
        self.total_trades += 1
        
        if pnl > 0:
            self.reputation += int(5 * pos['leverage'])
            self.win_streak += 1
            self.log(f"CLOSED {pos['type']} {pos['symbol']} | PROFIT: +${pnl:.2f} 🟢")
        else:
            self.reputation -= int(2 * pos['leverage'])
            self.win_streak = 0
            self.log(f"CLOSED {pos['type']} {pos['symbol']} | LOSS: -${abs(pnl):.2f} 🔴")

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
def init_game():
    if 'market_assets' not in st.session_state:
        st.session_state.market_assets = {
            "NDX": MarketAsset("NDX", "Tech Index", 15000.0, 0.005, 0.0001),
            "CRPT": MarketAsset("CRPT", "Crypto Core", 45000.0, 0.015, 0.0),
            "HVA": MarketAsset("HVA", "Heavy Vanguard Corp", 250.0, 0.008, 0.00005)
        }
    if 'news_engine' not in st.session_state:
        st.session_state.news_engine = NewsEngine()
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = Portfolio()
    if 'active_asset' not in st.session_state:
        st.session_state.active_asset = "NDX"
    if 'game_over' not in st.session_state:
        st.session_state.game_over = False

init_game()

# References to state
assets = st.session_state.market_assets
news = st.session_state.news_engine
port = st.session_state.portfolio
active_symbol = st.session_state.active_asset

current_prices = {sym: asset.current_price for sym, asset in assets.items()}
current_equity = port.get_equity(current_prices)

# ==========================================
# MARGIN CALL / GAME OVER LOGIC
# ==========================================
if current_equity <= 100.0 and not st.session_state.game_over:
    if port.upgrades['loot']:
        # The LOOT Net recovery mechanic
        st.session_state.portfolio.cash += 2500.0
        st.session_state.portfolio.positions = []
        st.session_state.portfolio.upgrades['loot'] = False # Consumed
        port.log("⚠️ FATAL: MARGIN CALL OVERRIDDEN BY LOOT NET. RECOVERED $2,500. POSITIONS WIPED.")
    else:
        st.session_state.game_over = True

if st.session_state.game_over:
    st.markdown("<h1 style='color:red !important; text-align:center; font-size:4rem;'>LIQUIDATED</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>ALL-TIME PEAK FLEX: ${port.peak_equity:,.2f}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center;'>FINAL REPUTATION SCORE: {port.reputation} TR</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("REBOOT CAREER (RESET)", key="reset_btn"):
            peak = port.peak_equity
            st.session_state.clear()
            init_game()
            st.session_state.portfolio.peak_equity = peak # Persist the ultimate flex across runs
            st.rerun()
    st.stop()

# ==========================================
# CORE GAME LOOP / TICKER ADVANCE
# ==========================================
def advance_market():
    news.roll_event(list(assets.values()))
    for asset in assets.values():
        asset.process_tick(news.global_vol_mod)

# ==========================================
# UI RENDERING: TOP BAR
# ==========================================
st.markdown("<h1>🌐 APEX TRADING TERMINAL v1.4</h1>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class='metric-container'>
        <div style='font-size:12px; color:#8b949e;'>NET LIQUIDITY</div>
        <div data-testid='stMetricValue'>${current_equity:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class='metric-container'>
        <div style='font-size:12px; color:#8b949e;'>AVAILABLE CASH</div>
        <div data-testid='stMetricValue' style='color:#c9d1d9 !important'>${port.cash:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    margin_usage = port.get_margin_usage(current_prices)
    danger_class = "danger-metric" if margin_usage > 75 else ""
    st.markdown(f"""
    <div class='metric-container {danger_class}'>
        <div style='font-size:12px; color:#8b949e;'>MARGIN UTILIZATION</div>
        <div data-testid='stMetricValue'>{margin_usage:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class='metric-container' style='border-left-color:#d2a8ff;'>
        <div style='font-size:12px; color:#8b949e;'>TRADER REPUTATION</div>
        <div data-testid='stMetricValue' style='color:#d2a8ff !important'>{port.reputation} TR</div>
    </div>
    """, unsafe_allow_html=True)

# Ticker Tape News
if news.current_news != "MARKET STABLE. AWAITING VOLATILITY TRIGGERS.":
    st.markdown(f"<div class='news-ticker'>⚠️ {news.current_news}</div>", unsafe_allow_html=True)

# ==========================================
# UI RENDERING: SIDEBAR (UPGRADES & SETTINGS)
# ==========================================
with st.sidebar:
    st.header("SYSTEM LINK")
    if st.button("⏩ FORCE NEXT TICK", key="force_tick", help="Advance the market 1 step"):
        advance_market()
        st.rerun()
        
    st.markdown("<hr>", unsafe_allow_html=True)
    st.header("MARKET SELECTOR")
    for sym, asset in assets.items():
        if st.button(f"📡 {asset.name} ({sym})", key=f"sel_{sym}"):
            st.session_state.active_asset = sym
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.header("INFRASTRUCTURE MATRIX")
    
    # UPGRADE 1: APEX
    apex_owned = port.upgrades['apex']
    st.markdown(f"<div class='skill-card {'skill-owned' if apex_owned else ''}'><h4>Advanced Predictive Executive Matrix (APEX)</h4><p style='font-size:11px; margin:0;'>Unlocks dynamic support/resistance overlay mapping.</p><b style='font-size:10px;'>COST: $50,000</b></div>", unsafe_allow_html=True)
    if not apex_owned:
        if st.button("BUY APEX", key="buy_apex"):
            if port.cash >= 50000:
                port.cash -= 50000
                port.upgrades['apex'] = True
                port.log("UPGRADE: APEX MATRIX integrated into mainframe.")
                st.rerun()
            else: st.error("Insufficient Funds")
            
    # UPGRADE 2: LOOT
    loot_owned = port.upgrades['loot']
    st.markdown(f"<div class='skill-card {'skill-owned' if loot_owned else ''}'><h4>LOOT Asset Recovery Net</h4><p style='font-size:11px; margin:0;'>Automated failsafe. Overrides one Margin Call and recovers $2,500.</p><b style='font-size:10px;'>COST: $25,000</b></div>", unsafe_allow_html=True)
    if not loot_owned:
        if st.button("BUY LOOT NET", key="buy_loot"):
            if port.cash >= 25000:
                port.cash -= 25000
                port.upgrades['loot'] = True
                port.log("UPGRADE: LOOT NET failsafe armed.")
                st.rerun()
            else: st.error("Insufficient Funds")
            
    # UPGRADE 3: SOHC-4V
    sohc_owned = port.upgrades['sohc4v']
    st.markdown(f"<div class='skill-card {'skill-owned' if sohc_owned else ''}'><h4>SOHC-4V Algorithmic Engine</h4><p style='font-size:11px; margin:0;'>High-rev frequency trading protocols. Reduces entry slippage by 80%.</p><b style='font-size:10px;'>COST: $75,000</b></div>", unsafe_allow_html=True)
    if not sohc_owned:
        if st.button("BUY SOHC-4V", key="buy_sohc"):
            if port.cash >= 75000:
                port.cash -= 75000
                port.upgrades['sohc4v'] = True
                port.log("UPGRADE: SOHC-4V Engine revving at maximum capacity.")
                st.rerun()
            else: st.error("Insufficient Funds")


# ==========================================
# UI RENDERING: MAIN CHART (PLOTLY)
# ==========================================
active_data = assets[active_symbol]
df = active_data.history.copy()

# Calculate Technicals
df['upper_bb'], df['sma'], df['lower_bb'] = calc_bollinger_bands(df['close'])
df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
df['rsi'] = calc_rsi(df['close'])

# Build Subplots
fig = make_subplots(
    rows=3, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.02,
    row_heights=[0.6, 0.2, 0.2],
    specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]]
)

# Row 1: Candlesticks & Bollinger Bands
fig.add_trace(go.Candlestick(
    x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
    name="Price", increasing_line_color='#3fb950', decreasing_line_color='#f85149'
), row=1, col=1)

fig.add_trace(go.Scatter(x=df['time'], y=df['upper_bb'], line=dict(color='rgba(88,166,255,0.4)', width=1, dash='dot'), name='Upper BB'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['time'], y=df['lower_bb'], line=dict(color='rgba(88,166,255,0.4)', width=1, dash='dot'), name='Lower BB', fill='tonexty', fillcolor='rgba(88,166,255,0.05)'), row=1, col=1)

# APEX Upgrade: Show 200 EMA support lines
if port.upgrades['apex']:
    df['ema_200'] = calc_ema(df['close'], 50) # Using 50 to fit the 100 period window better
    fig.add_trace(go.Scatter(x=df['time'], y=df['ema_200'], line=dict(color='#d2a8ff', width=2), name='APEX Support Vector'), row=1, col=1)

# Row 2: MACD
colors = ['#3fb950' if val >= 0 else '#f85149' for val in df['macd_hist']]
fig.add_trace(go.Bar(x=df['time'], y=df['macd_hist'], marker_color=colors, name='MACD Hist'), row=2, col=1)
fig.add_trace(go.Scatter(x=df['time'], y=df['macd'], line=dict(color='#58a6ff', width=1), name='MACD'), row=2, col=1)
fig.add_trace(go.Scatter(x=df['time'], y=df['macd_signal'], line=dict(color='#ff7b72', width=1), name='Signal'), row=2, col=1)

# Row 3: RSI
fig.add_trace(go.Scatter(x=df['time'], y=df['rsi'], line=dict(color='#d2a8ff', width=1), name='RSI'), row=3, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="rgba(248,81,73,0.5)", row=3, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="rgba(63,185,80,0.5)", row=3, col=1)

# Update Layout
fig.update_layout(
    height=600,
    margin=dict(l=10, r=10, t=30, b=10),
    plot_bgcolor='#0d1117',
    paper_bgcolor='#0d1117',
    font=dict(color='#8b949e', family='Share Tech Mono'),
    xaxis=dict(showgrid=True, gridcolor='#30363d', rangeslider=dict(visible=False)),
    xaxis2=dict(showgrid=True, gridcolor='#30363d'),
    xaxis3=dict(showgrid=True, gridcolor='#30363d'),
    yaxis=dict(showgrid=True, gridcolor='#30363d', side='right'),
    yaxis2=dict(showgrid=True, gridcolor='#30363d', side='right'),
    yaxis3=dict(showgrid=True, gridcolor='#30363d', side='right', range=[0, 100]),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ==========================================
# UI RENDERING: TRADING TERMINAL & LOGS
# ==========================================
col_trade, col_pos, col_log = st.columns([2, 3, 2])

# Panel 1: Order Execution
with col_trade:
    st.markdown("### 🛒 EXECUTION DECK")
    st.markdown(f"<div style='margin-bottom:10px; color:#58a6ff; font-size:20px;'><b>{active_data.name} ({active_data.symbol})</b> @ ${active_data.current_price:.2f}</div>", unsafe_allow_html=True)
    
    trade_size_pct = st.slider("Position Size (% of Equity)", 1, 100, 10)
    lev_allowed = 10 if active_symbol != "CRPT" else 25 # High leverage for crypto
    leverage = st.slider("Leverage (Multiplier)", 1, lev_allowed, 1)
    
    st.write(f"*Est. Notional Exposure: ${(current_equity * (trade_size_pct/100) * leverage):,.2f}*")
    
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("<div class='buy-btn'>", unsafe_allow_html=True)
        if st.button("📈 LONG / BUY"):
            success, msg = port.execute_trade(active_symbol, active_data.current_price, "LONG", leverage, trade_size_pct)
            if success:
                advance_market()
                st.rerun()
            else: st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with b2:
        st.markdown("<div class='sell-btn'>", unsafe_allow_html=True)
        if st.button("📉 SHORT / SELL"):
            success, msg = port.execute_trade(active_symbol, active_data.current_price, "SHORT", leverage, trade_size_pct)
            if success:
                advance_market()
                st.rerun()
            else: st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

# Panel 2: Open Positions
with col_pos:
    st.markdown("### 📋 ACTIVE POSITIONS")
    if not port.positions:
        st.info("NO OPEN POSITIONS. WAITING FOR ENTRY SIGNALS.")
    else:
        for idx, pos in enumerate(port.positions):
            c_price = current_prices[pos['symbol']]
            
            # Calculate PNL
            if pos['type'] == 'LONG': pnl = (c_price - pos['entry']) * pos['qty']
            else: pnl = (pos['entry'] - c_price) * pos['qty']
            
            roi_pct = (pnl / pos['initial_capital']) * 100
            
            pnl_color = "#3fb950" if pnl >= 0 else "#f85149"
            type_color = "#3fb950" if pos['type'] == 'LONG' else "#f85149"
            
            with st.container():
                st.markdown(f"""
                <div style='background-color:#161b22; border:1px solid #30363d; padding:10px; border-radius:4px; margin-bottom:5px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <b style='color:{type_color}'>{pos['type']} {pos['symbol']}</b> | {pos['leverage']}x Lev<br>
                            <span style='font-size:12px; color:#8b949e;'>Entry: ${pos['entry']:.2f} | Current: ${c_price:.2f}</span>
                        </div>
                        <div style='text-align:right;'>
                            <b style='color:{pnl_color}'>${pnl:,.2f} ({roi_pct:+.2f}%)</b>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"✖ CLOSE {pos['symbol']}", key=f"close_{idx}"):
                    port.close_position(idx, current_prices)
                    advance_market()
                    st.rerun()

# Panel 3: Action Log
with col_log:
    st.markdown("### 📝 TERMINAL LOG")
    log_content = "<br>".join(port.action_log)
    st.markdown(f"<div class='log-box'>{log_content}</div>", unsafe_allow_html=True)

# ==========================================
# FOOTER & FLEX STATS
# ==========================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align:center; color:#8b949e; font-size:12px;'>
    ALL-TIME PEAK EQUITY FLEX: <b style='color:#e3b341;'>${port.peak_equity:,.2f}</b> | 
    TOTAL TRADES EXECUTED: <b>{port.total_trades}</b> | 
    CURRENT WIN STREAK: <b>{port.win_streak}</b>
</div>
""", unsafe_allow_html=True)
