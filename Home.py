import streamlit as st

st.set_page_config(layout="wide")

# ---------- STATE ----------
if "module" not in st.session_state:
    st.session_state.module = None

# =========================================================
# FLIGHT SCORE MODULE
# =========================================================
if st.session_state.module == "flightscore":
    from compute_flightscore import compute_flight_score, compute_flight_metrics
    import tempfile

    st.title("✈️ FlightScore")

    if st.button("⬅ Back"):
        st.session_state.module = None
        st.rerun()

    uploaded = st.file_uploader("Upload flight logs (.bin)", type=["bin"], accept_multiple_files=True)

    if not uploaded:
        st.stop()

    flights = []

    for f in uploaded:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        tmp.write(f.read())

        score = compute_flight_score(tmp.name)

        flights.append({
            "name": f.name,
            "path": tmp.name,
            "score": score
        })

    flights.sort(key=lambda x: x["score"], reverse=True)

    st.subheader("Ranking")

    for i, f in enumerate(flights, 1):
        c1, c2, c3 = st.columns([4,1,1])

        c1.write(f"**{i}. {f['name']}**")
        c2.metric("Score", f"{f['score']:.1f}")

    st.stop()

# =========================================================
# FLIGHT DEGRADE MODULE
# =========================================================
if st.session_state.module == "degrade":
    from compute_logic1 import compute_degradation  # adjust if needed

    st.title("📉 FlightDegrade")

    if st.button("⬅ Back"):
        st.session_state.module = None
        st.rerun()

    st.write("Upload flights to analyze degradation.")

    uploaded = st.file_uploader("Upload logs", type=["bin"], accept_multiple_files=True)

    if uploaded:
        st.success("Logs loaded (placeholder)")

    st.stop()

# =========================================================
# HOME
# =========================================================
st.title("Drone Health Analytics Platform")
st.caption("Flight Performance • Degradation • Mission Feasibility")

st.divider()
st.subheader("Select Analysis Module")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 FlightScore")
    st.write("Drone flight performance scoring and optimal flight identification")
    if st.button("Open FlightScore"):
        st.session_state.module = "flightscore"
        st.rerun()

with col2:
    st.markdown("### 📉 FlightDegrade")
    st.write("Post-flight degradation and performance drift monitoring")
    if st.button("Open FlightDegrade"):
        st.session_state.module = "degrade"
        st.rerun()

st.divider()
st.caption("Drone Health Analytics")
