import random
import streamlit as st

def init_event_state():
    if "active_event" not in st.session_state:
        st.session_state.active_event = None

def check_for_daily_event():
    init_event_state()
    
    # If an event is already active, don't trigger another
    if st.session_state.active_event is not None:
        return

    # 35% chance to trigger an interactive event each day
    if random.random() < 0.35:
        event_pool = [
            {
                "id": "corpo_bribe",
                "title": "🤝 Corporate Backdoor Deal",
                "desc": "An anonymous fixer from OmniCorp reaches out. They offer $4,000 cash if you inject a tracking script into your server farm.",
                "choices": [
                    {"label": "Accept Offer (+$4,000, +20% Heat)", "action": "bribe_accept"},
                    {"label": "Refuse Deal (No Effect)", "action": "bribe_refuse"},
                    {"label": "Report to Authorities (+10% Heat, -$1,000 legal fee)", "action": "bribe_report"}
                ]
            },
            {
                "id": "hardware_meltdown",
                "title": "🔥 Server Rack Overheating",
                "desc": "Cooling unit failure in Subnet Alpha! Your Micro-Nodes are at risk of thermal destruction.",
                "choices": [
                    {"label": "Emergency Coolant Spray (-$800)", "action": "cool_buy"},
                    {"label": "Overclock Fans (+15% Heat, 50% chance of server damage)", "action": "cool_risk"},
                    {"label": "Let it Burn (Lose 1 Micro-Node)", "action": "cool_ignore"}
                ]
            },
            {
                "id": "rival_hack",
                "title": "⚡ Rival Netrunner Intrusion",
                "desc": "A hacker alias known as 'Phant0m' is trying to siphon funds from your active credit balances!",
                "choices": [
                    {"label": "Deploy Counter-Firewall (-$1,200)", "action": "hack_defend"},
                    {"label": "Counter-Hack Phant0m (+25% Heat, chance to steal $3,000)", "action": "hack_counter"},
                    {"label": "Disconnect System (Skip day earnings)", "action": "hack_flee"}
                ]
            }
        ]
        
        st.session_state.active_event = random.choice(event_pool)
        st.session_state.logs.append(f"⚠️ ENCOUNTER: {st.session_state.active_event['title']}")

def resolve_event_choice(action_code):
    event = st.session_state.active_event
    if not event:
        return

    # --- CORPO BRIBE RESOLUTION ---
    if action_code == "bribe_accept":
        st.session_state.credits += 4000
        st.session_state.heat += 20
        st.session_state.logs.append("🤝 Accepted bribe. +$4,000 added, but Heat increased by 20%.")
    elif action_code == "bribe_refuse":
        st.session_state.logs.append("🚫 Refused corporate bribe. Maintained system integrity.")
    elif action_code == "bribe_report":
        st.session_state.credits = max(0, st.session_state.credits - 1000)
        st.session_state.heat += 10
        st.session_state.logs.append("📜 Filed report with authorities. Paid $1,000 legal filing fees.")

    # --- HARDWARE MELTDOWN RESOLUTION ---
    elif action_code == "cool_buy":
        if st.session_state.credits >= 800:
            st.session_state.credits -= 800
            st.session_state.logs.append("❄️ Purchased emergency coolant. Servers stabilized.")
        else:
            st.session_state.logs.append("❌ Could not afford coolant! Server rack damaged.")
            if "Micro-Node" in st.session_state.servers and st.session_state.servers["Micro-Node"]["owned"] > 0:
                st.session_state.servers["Micro-Node"]["owned"] -= 1
    elif action_code == "cool_risk":
        st.session_state.heat += 15
        if random.random() < 0.5:
            st.session_state.logs.append("🌀 Overclocking worked! Heat spiked, but servers saved.")
        else:
            st.session_state.logs.append("💥 Overclocking failed! Lost 1 Micro-Node.")
            if "Micro-Node" in st.session_state.servers and st.session_state.servers["Micro-Node"]["owned"] > 0:
                st.session_state.servers["Micro-Node"]["owned"] -= 1
    elif action_code == "cool_ignore":
        st.session_state.logs.append("🔥 Subnet destroyed. Lost 1 Micro-Node.")
        if "Micro-Node" in st.session_state.servers and st.session_state.servers["Micro-Node"]["owned"] > 0:
            st.session_state.servers["Micro-Node"]["owned"] -= 1

    # --- RIVAL HACK RESOLUTION ---
    elif action_code == "hack_defend":
        if st.session_state.credits >= 1200:
            st.session_state.credits -= 1200
            st.session_state.logs.append("🛡️ Firewall deployed. Phant0m repelled successfully.")
        else:
            loss = min(st.session_state.credits, 2000)
            st.session_state.credits -= loss
            st.session_state.logs.append(f"❌ Failed to afford firewall. Phant0m stole ${loss}!")
    elif action_code == "hack_counter":
        st.session_state.heat += 25
        if random.random() < 0.6:
            st.session_state.credits += 3000
            st.session_state.logs.append("⚡ Counter-hack successful! Siphoned $3,000 from Phant0m.")
        else:
            st.session_state.logs.append("💀 Counter-hack backfired! Phant0m traced your origin.")
    elif action_code == "hack_flee":
        st.session_state.logs.append("🔌 Emergency shutdown executed. Safe from attack.")

    # Clear active event after choice
    st.session_state.active_event = None

def render_event_popup():
    init_event_state()
    
    if st.session_state.active_event is not None:
        ev = st.session_state.active_event
        
        st.warning(f"### {ev['title']}")
        st.write(ev['desc'])
        
        cols = st.columns(len(ev['choices']))
        for i, choice in enumerate(ev['choices']):
            with cols[i]:
                st.button(
                    choice['label'], 
                    key=f"ev_choice_{i}", 
                    use_container_width=True, 
                    on_click=resolve_event_choice, 
                    args=(choice['action'],)
                )
        st.divider()
