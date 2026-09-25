import random
import streamlit as st

def init_hack_state():
    if "breach_active" not in st.session_state:
        st.session_state.breach_active = False
        st.session_state.target_name = ""
        st.session_state.nodes_cleared = 0
        st.session_state.total_nodes = 0
        st.session_state.bandwidth = 0
        st.session_state.trace_level = 0

def start_breach(target_name, nodes, bandwidth):
    st.session_state.breach_active = True
    st.session_state.target_name = target_name
    st.session_state.nodes_cleared = 0
    st.session_state.total_nodes = nodes
    st.session_state.bandwidth = bandwidth
    st.session_state.trace_level = 0
    st.session_state.logs.append(f"⚡ INITIATED BREACH ON: {target_name}")

def execute_node_command(action):
    if not st.session_state.breach_active:
        return

    # Action: Brute Force (High success, high trace cost, uses 1 bandwidth)
    if action == "brute":
        st.session_state.bandwidth -= 1
        st.session_state.trace_level += random.randint(15, 30)
        if random.random() > 0.1:
            st.session_state.nodes_cleared += 1
            
    # Action: Stealth Inject (Low trace cost, low success chance, uses 1 bandwidth)
    elif action == "stealth":
        st.session_state.bandwidth -= 1
        st.session_state.trace_level += random.randint(0, 10)
        if random.random() > 0.4:
            st.session_state.nodes_cleared += 1

    # Check Win/Loss conditions
    if st.session_state.nodes_cleared >= st.session_state.total_nodes:
        reward = st.session_state.total_nodes * random.randint(1000, 2500)
        st.session_state.credits += reward
        st.session_state.logs.append(f"🟢 BREACH SUCCESS: Extracted ${reward}!")
        st.session_state.breach_active = False
    elif st.session_state.bandwidth <= 0:
        st.session_state.logs.append("❌ BREACH FAILED: Ran out of bandwidth. Disconnected.")
        st.session_state.breach_active = False
    elif st.session_state.trace_level >= 100:
        st.session_state.heat += 25
        st.session_state.logs.append("🚨 CRITICAL FAILURE: Trace completed! System heat spiked by 25%.")
        st.session_state.breach_active = False

def render_hacking_ui():
    init_hack_state()
    
    if not st.session_state.breach_active:
        st.subheader("Available Targets")
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            st.write("**Local Credit Union**")
            st.caption("Nodes: 3 | Bandwidth: 5")
            st.button("Breach Local", use_container_width=True, on_click=start_breach, args=("Local Credit Union", 3, 5))
        with c2:
            st.write("**OmniCorp Logistics**")
            st.caption("Nodes: 5 | Bandwidth: 7")
            st.button("Breach OmniCorp", use_container_width=True, on_click=start_breach, args=("OmniCorp Logistics", 5, 7))
        with c3:
            st.write("**Global Reserve**")
            st.caption("Nodes: 8 | Bandwidth: 10")
            st.button("Breach Global Reserve", type="primary", use_container_width=True, on_click=start_breach, args=("Global Reserve", 8, 10))
    else:
        st.error(f"⚠️ ACTIVE BREACH: {st.session_state.target_name}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Nodes Cleared", f"{st.session_state.nodes_cleared} / {st.session_state.total_nodes}")
        m2.metric("Bandwidth Remaining", f"{st.session_state.bandwidth} TB/s")
        m3.metric("Active Trace", f"{st.session_state.trace_level}%")
        
        st.progress(min(1.0, st.session_state.trace_level / 100.0))
        
        st.write("Select tactical approach for the next security node:")
        a1, a2, a3 = st.columns(3)
        with a1:
            st.button("🔨 Brute Force (High Trace, 90% Success)", use_container_width=True, on_click=execute_node_command, args=("brute",))
        with a2:
            st.button("🥷 Stealth Inject (Low Trace, 60% Success)", use_container_width=True, on_click=execute_node_command, args=("stealth",))
        with a3:
            st.button("🛑 Abort Connection", use_container_width=True, on_click=lambda: st.session_state.update(breach_active=False, logs=st.session_state.logs + ["🛑 Breach manually aborted."]))
