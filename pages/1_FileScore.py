import streamlit as st
import tempfile
from compute_flightscore import compute_flight_score, compute_flight_metrics

st.set_page_config(layout="wide")

# ---------------- STATE INIT ----------------
if "selected_log" not in st.session_state:
    st.session_state.selected_log = None


# =========================================================
# DETAILS VIEW
# =========================================================
# ---------- DETAILS PANEL ----------
if "selected_flight" in st.session_state:
    sel = st.session_state.selected_flight
    metrics = compute_flight_metrics(sel["path"])

    import os
    st.divider()
    st.subheader(f"Flight Details — {os.path.basename(sel['path'])}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Battery**")
        st.metric("Avg Voltage", f"{metrics['avg_voltage']:.2f}" if metrics["avg_voltage"] else "N/A")
        st.metric("Min Voltage", f"{metrics['min_voltage']:.2f}" if metrics["min_voltage"] else "N/A")
        st.metric("Health %", f"{metrics['battery_health']:.1f}" if metrics["battery_health"] else "N/A")

    with col2:
        st.markdown("**Vibration**")
        st.metric("Max", f"{metrics['max_vibe']:.2f}" if metrics["max_vibe"] else "N/A")
        st.metric("RMS", f"{metrics['rms_vibe']:.2f}" if metrics["rms_vibe"] else "N/A")
        st.metric("Severity", metrics["vibe_severity"])

    with col3:
        st.markdown("**Control & Stability**")
        st.metric("Roll Var", f"{metrics['roll_var']:.3f}" if metrics["roll_var"] else "N/A")
        st.metric("Pitch Var", f"{metrics['pitch_var']:.3f}" if metrics["pitch_var"] else "N/A")
        st.metric("Hover Thr", f"{metrics['hover_throttle']:.2f}" if metrics["hover_throttle"] else "N/A")

    st.divider()
    st.metric("Flight Score", f"{metrics['flight_score']:.1f}")

# =========================================================
# RANKING VIEW
# =========================================================

st.title("✈️ Flight Score Comparison")

uploaded = st.file_uploader(
    "Upload flight logs (.bin)",
    type=["bin"],
    accept_multiple_files=True
)

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

    if c3.button("Details", key=f"{f['name']}_{i}"):
        st.session_state.selected_log = f["path"]
        st.rerun()
