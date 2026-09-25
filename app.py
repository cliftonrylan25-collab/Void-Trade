import random
import streamlit as st

# Page Config
st.set_page_config(
    page_title="Neon Market 2099",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Initialize Game State
if "day" not in st.session_state:
    st.session_state.day = 1
    st.session_state.credits = 500
    st.session_state.heat = 0
    st.session_state.portfolio = {"CYBR": 0, "NEO": 0, "BYTE": 0}
    st.session_state.prices = {"CYBR": 100, "NEO": 50, "BYTE": 25}
    st.session_state.history = {"CYBR": [100], "NEO": [50], "BYTE": [25]}
    st.session_state.logs = ["Welcome to the terminal, Operator. Make your fortune."]

def advance_day():
    st.session_state.day += 1
    # Decay heat slightly each day
    if st.session_state.heat > 0:
        st.session_state.heat = max(0, st.session_state.heat - 5)

    # Fluctuating market prices
    for item in st.session_state.prices:
        change_pct = random.uniform(-0.25, 0.30)
        new_price = max(5, int(st.session_state.prices[item] * (1 + change_pct)))
        st.session_state.prices[item] = new_price
        st.session_state.history[item].append(new_price)

    st.session_state.logs.append(f"📅 Day {st.session_state.day}: Market prices updated.")

def buy_asset(asset, amount=1):
    cost = st.session_state.prices[asset] * amount
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.session_state.portfolio[asset] += amount
        st.session_state.logs.append(f"🟢 Bought {amount} {asset} @ ${st.session_state.prices[asset]}")
    else:
        st.session_state.logs.append(f"❌ Insufficient funds for {asset}!")

def sell_asset(asset, amount=1):
    if st.session_state.portfolio[asset] >= amount:
        earned = st.session_state.prices[asset] * amount
        st.session_state.credits += earned
        st.session_state.portfolio[asset] -= amount
        st.session_state.logs.append(f"🔴 Sold {amount} {asset} @ ${st.session_state.prices[asset]}")
    else:
        st.session_state.logs.append(f"❌ No {asset} available to sell!")

def hack_node():
    if st.session_state.heat >= 80:
        st.session_state.logs.append("⚠️ System lock! Heat level too high to breach.")
        return

    st.session_state.heat += random.randint(15, 30)
    outcome = random.choice(["pump", "dump", "bounty"])

    if outcome == "pump":
        target = random.choice(list(st.session_state.prices.keys()))
        st.session_state.prices[target] = int(st.session_state.prices[target] * 1.6)
        st.session_state.logs.append(f"⚡ HACK SUCCESS: Artificially pumped {target} market value!")
    elif outcome == "dump":
        target = random.choice(list(st.session_state.prices.keys()))
        st.session_state.prices[target] = max(5, int(st.session_state.prices[target] * 0.5))
        st.session_state.logs.append(f"⚡ HACK SUCCESS: Crashed {target} market value!")
    else:
        stolen = random.randint(200, 500)
        st.session_state.credits += stolen
        st.session_state.logs.append(f"⚡ HACK SUCCESS: Exfiltrated ${stolen} from corporate accounts!")

# App Layout
st.title("📈 NEON MARKET 2099")

# Top Metrics Bar
m1, m2, m3 = st.columns(3)
m1.metric("Credits", f"${st.session_state.credits}")
m2.metric("Heat Level", f"{st.session_state.heat}%")
m3.metric("Current Day", f"#{st.session_state.day}")

st.progress(min(1.0, st.session_state.heat / 100.0))

if st.session_state.heat >= 100:
    st.error("🚨 CORPO FIREWALL DETECTED YOUR TRACE! GAME OVER.")
    if st.button("Reset Terminal"):
        st.session_state.clear()
else:
    st.divider()

    # Market Trends Chart
    st.subheader("Market Trends")
    st.line_chart(st.session_state.history)

    # Trading Controls
    st.subheader("Asset Exchange")
    for asset in st.session_state.prices:
        col_name, col_price, col_owned, col_buy, col_sell = st.columns([2, 2, 2, 2, 2])
        col_name.write(f"**{asset}**")
        col_price.write(f"${st.session_state.prices[asset]}")
        col_owned.write(f"Owned: {st.session_state.portfolio[asset]}")

        with col_buy:
            st.button(f"Buy", key=f"buy_{asset}", use_container_width=True, on_click=buy_asset, args=(asset,))
        with col_sell:
            st.button(f"Sell", key=f"sell_{asset}", use_container_width=True, on_click=sell_asset, args=(asset,))

    st.divider()

    # Action Buttons
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        st.button("⏩ Advance Day", use_container_width=True, type="primary", on_click=advance_day)
    with action_col2:
        st.button("💻 Breach Node (+Heat)", use_container_width=True, on_click=hack_node)

# Activity Log
st.divider()
st.subheader("Terminal Logs")
for log in reversed(st.session_state.logs[-6:]):
    st.write(log)
