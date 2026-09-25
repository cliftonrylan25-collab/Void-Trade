import random
import streamlit as st
import pandas as pd

def init_market_state():
    if "market_initialized" not in st.session_state:
        st.session_state.market_initialized = True
        st.session_state.portfolio = {"APEX": 0, "LOOT": 0, "VOID": 0, "CYBR": 0}
        st.session_state.short_positions = {"APEX": 0, "LOOT": 0, "VOID": 0, "CYBR": 0}
        st.session_state.short_entry_prices = {"APEX": 0, "LOOT": 0, "VOID": 0, "CYBR": 0}
        st.session_state.prices = {"APEX": 150, "LOOT": 75, "VOID": 30, "CYBR": 220}
        st.session_state.history = {
            "APEX": [150], "LOOT": [75], "VOID": [30], "CYBR": [220]
        }
        st.session_state.volatility = {"APEX": 0.15, "LOOT": 0.25, "VOID": 0.35, "CYBR": 0.10}
        st.session_state.insider_tip = "No active rumors on the dark web."

def update_market_prices():
    init_market_state()
    
    # 5% chance of a market-wide crash or boom
    macro_event = random.random()
    multiplier_override = None
    if macro_event < 0.03:
        multiplier_override = 0.65  # Crash (-35%)
        st.session_state.logs.append("💥 MARKET CRASH: Global financial panic! Stocks plummeting.")
    elif macro_event > 0.97:
        multiplier_override = 1.40  # Bull Run (+40%)
        st.session_state.logs.append("🚀 BULL RUN: Tech sector skyrocketing!")

    for asset in st.session_state.prices:
        vol = st.session_state.volatility[asset]
        if multiplier_override:
            change_pct = multiplier_override - 1.0 + random.uniform(-0.05, 0.05)
        else:
            change_pct = random.uniform(-vol, vol + 0.02) # Slightly biased upward

        new_price = max(5, int(st.session_state.prices[asset] * (1 + change_pct)))
        st.session_state.prices[asset] = new_price
        st.session_state.history[asset].append(new_price)

    # Generate new insider tip for tomorrow
    generate_insider_tip()

def generate_insider_tip():
    target = random.choice(list(st.session_state.prices.keys()))
    direction = random.choice(["surge", "plummet"])
    st.session_state.insider_tip = f"⚡ DARKNET LEAK: Whispers suggest {target} will {direction} tomorrow."

def buy_stock(asset, qty=1):
    cost = st.session_state.prices[asset] * qty
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.session_state.portfolio[asset] += qty
        st.session_state.logs.append(f"🟢 BOUGHT {qty}x {asset} @ ${st.session_state.prices[asset]}")
    else:
        st.session_state.logs.append(f"❌ Insufficient funds to buy {qty}x {asset}.")

def sell_stock(asset, qty=1):
    if st.session_state.portfolio[asset] >= qty:
        earned = st.session_state.prices[asset] * qty
        st.session_state.credits += earned
        st.session_state.portfolio[asset] -= qty
        st.session_state.logs.append(f"🔴 SOLD {qty}x {asset} @ ${st.session_state.prices[asset]}")
    else:
        st.session_state.logs.append(f"❌ Insufficient shares of {asset} owned.")

def short_stock(asset, qty=1):
    # Short selling: Bet that price drops
    if st.session_state.short_positions[asset] > 0:
        st.session_state.logs.append(f"⚠️ Existing short position already open on {asset}.")
        return
    
    collateral = st.session_state.prices[asset] * qty
    if st.session_state.credits >= collateral:
        st.session_state.credits -= collateral
        st.session_state.short_positions[asset] = qty
        st.session_state.short_entry_prices[asset] = st.session_state.prices[asset]
        st.session_state.logs.append(f"📉 SHORTED {qty}x {asset} @ ${st.session_state.prices[asset]}")
    else:
        st.session_state.logs.append(f"❌ Need ${collateral} collateral to short {asset}.")

def close_short(asset):
    qty = st.session_state.short_positions[asset]
    if qty <= 0:
        return
    
    entry_p = st.session_state.short_entry_prices[asset]
    current_p = st.session_state.prices[asset]
    
    # Profit = difference between entry price and current lower price
    profit_per_share = entry_p - current_p
    total_returned = (entry_p * qty) + (profit_per_share * qty)
    
    st.session_state.credits += max(0, total_returned)
    st.session_state.short_positions[asset] = 0
    st.session_state.short_entry_prices[asset] = 0
    
    pnl_str = f"+${profit_per_share * qty}" if profit_per_share >= 0 else f"-${abs(profit_per_share * qty)}"
    st.session_state.logs.append(f"📊 CLOSED SHORT on {asset}. PnL: {pnl_str}")

def render_market_ui():
    init_market_state()
    
    st.subheader("Global Stock Exchange")
    
    # Insider Tip Banner
    st.info(st.session_state.insider_tip)
    
    # Chart
    df = pd.DataFrame(st.session_state.history)
    st.line_chart(df)
    
    st.subheader("Live Trading Desk")
    for asset in st.session_state.prices:
        cur_price = st.session_state.prices[asset]
        owned = st.session_state.portfolio[asset]
        shorted = st.session_state.short_positions[asset]
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
        
        with c1:
            st.write(f"**{asset}**")
            st.caption(f"Owned: {owned} | Shorted: {shorted}")
        with c2:
            st.write(f"**${cur_price}**")
            vol_str = f"High Volatility" if st.session_state.volatility[asset] > 0.20 else "Stable"
            st.caption(vol_str)
        with c3:
            st.button("BUY 1", key=f"buy_{asset}", use_container_width=True, on_click=buy_stock, args=(asset, 1))
        with c4:
            st.button("SELL 1", key=f"sell_{asset}", use_container_width=True, on_click=sell_stock, args=(asset, 1))
        with c5:
            if shorted == 0:
                st.button("SHORT 1", key=f"short_{asset}", use_container_width=True, on_click=short_stock, args=(asset, 1))
            else:
                st.button("CLOSE SHORT", key=f"cshort_{asset}", type="primary", use_container_width=True, on_click=close_short, args=(asset,))
