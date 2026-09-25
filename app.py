import streamlit as st
import random
import hacking # Imports your new custom module

st.set_page_config(page_title="Neon Terminal OS", layout="wide", initial_sidebar_state="collapsed")

# 1. MASSIVE STATE INITIALIZATION
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.day = 1
    st.session_state.credits = 2500
    st.session_state.heat = 0
    st.session_state.logs = ["SYSTEM BOOT COMPLETE."]
    
    # Advanced Tycoon Server Logic (Condition-based)
    st.session_state.servers = {
        "Micro-Node": {"owned": 1, "cost": 500, "income": 50, "condition": 100},
        "Data Rack": {"owned": 0, "cost": 2500, "income": 300, "condition": 100},
    }
    
    hacking.init_hack_state()

def trigger_random_event():
    # 20% chance for a dynamic event each day
    if random.random() < 0.20:
        events = [
            {"msg": "⚠️ RIVAL AI ATTACK: A corporate netrunner damaged your servers. Maintenance required.", "effect": "damage"},
            {"msg": "📈 CRYPTO BOOM: Unmarked wallet found in deaddrop.", "effect": "cash_injection"},
            {"msg": "🚨 SWEEP INITIATED: Law enforcement is scanning local subnets. Heat +15.", "effect": "heat_spike"}
        ]
        event = random.choice(events)
        st.session_state.logs.append(event["msg"])
        
        if event["effect"] == "damage":
            st.session_state.servers["Micro-Node"]["condition"] = max(0, st.session_state.servers["Micro-Node"]["condition"] - 25)
        elif event["effect"] == "cash_injection":
            st.session_state.credits += random.randint(1000, 3000)
        elif event["effect"] == "heat_spike":
            st.session_state.heat += 15

def advance_day():
    if st.session_state.breach_active:
        st.session_state.logs.append("❌ CANNOT ADVANCE DAY WHILE BREACH IS ACTIVE.")
        return

    st.session_state.day += 1
    
    # Calculate Income based on Server Condition
    daily_income = 0
    for s_name, s_data in st.session_state.servers.items():
        efficiency = s_data["condition"] / 100.0
        daily_income += int((s_data["owned"] * s_data["income"]) * efficiency)
    
    st.session_state.credits += daily_income
    st.session_state.heat = max(0, st.session_state.heat - 5)
    
    trigger_random_event()
    st.session_state.logs.append(f"📅 Day {st.session_state.day} ended. Income: +${daily_income}.")

# 2. UI RENDERING
st.title("💻 Neon OS // Build 3.1.4")

h1, h2, h3, h4 = st.columns(4)
h1.metric("Credits", f"${st.session_state.credits}")
h2.metric("Heat Level", f"{st.session_state.heat}%")
h3.metric("Current Day", f"#{st.session_state.day}")
with h4:
    st.button("⏩ ADVANCE DAY", type="primary", use_container_width=True, on_click=advance_day)

if st.session_state.heat >= 100:
    st.error("🚨 TERMINAL LOCKED. YOU HAVE BEEN TRACED.")
    st.stop()

st.divider()

# Core Navigation
tab_sys, tab_hack, tab_market = st.tabs(["🖥️ System & Servers", "⚡ Cyber Warfare", "📈 Market Exchange"])

with tab_sys:
    st.subheader("Hardware Racks")
    for s_name, s_data in st.session_state.servers.items():
        c1, c2, c3 = st.columns([3, 2, 2])
        c1.write(f"**{s_name}** (Owned: {s_data['owned']})")
        c2.progress(s_data['condition'] / 100.0, text=f"Condition: {s_data['condition']}%")
        if s_data['condition'] < 100:
            c3.button(f"Repair ($500)", key=f"rep_{s_name}", use_container_width=True, on_click=lambda sn=s_name: st.session_state.servers[sn].update({"condition": 100}) if st.session_state.credits >= 500 else None)

with tab_hack:
    # Router to your new module
    hacking.render_hacking_ui()

with tab_market:
    st.write("*(Build out your `market.py` module and hook it up here!)*")

st.divider()
st.subheader("Terminal Logs")
log_output = "\n".join([f"> {log}" for log in reversed(st.session_state.logs[-8:])])
st.text_area("Live Feed", value=log_output, height=200, disabled=True, label_visibility="collapsed")
