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
if st.session_state.selected_log:

    st.title("✈️ Flight Health Details")

    if st.button("⬅ Back to Ranking"):
        st.session_state.selected_log = None
        st.rerun()

    metrics = compute_flight_metrics(st.session_state.selected_log)

    score = metrics["flight_score"]
    st.metric("Flight Score", f"{score:.1f}/100")

    st.subheader("Battery")
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg V", f"{metrics['avg_voltage']:.2f}" if metrics["avg_voltage"] else "N/A")
    c2.metric("Min V", f"{metrics['min_voltage']:.2f}" if metrics["min_voltage"] else "N/A")
    c3.metric("Health %", f"{metrics['battery_health']:.1f}" if metrics["battery_health"] else "N/A")

    st.subheader("Vibration")
    c1, c2, c3 = st.columns(3)
    c1.metric("Max", f"{metrics['max_vibe']:.2f}" if metrics["max_vibe"] else "N/A")
    c2.metric("RMS", f"{metrics['rms_vibe']:.2f}" if metrics["rms_vibe"] else "N/A")
    c3.metric("Severity", metrics["vibe_severity"])

    st.subheader("Stability")
    c1, c2 = st.columns(2)
    c1.metric("Roll Var", f"{metrics['roll_var']:.3f}" if metrics["roll_var"] else "N/A")
    c2.metric("Pitch Var", f"{metrics['pitch_var']:.3f}" if metrics["pitch_var"] else "N/A")

    st.subheader("Control")
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Thr", f"{metrics['avg_throttle']:.2f}" if metrics["avg_throttle"] else "N/A")
    c2.metric("Peak Thr", f"{metrics['peak_throttle']:.2f}" if metrics["peak_throttle"] else "N/A")
    c3.metric("Sat %", f"{metrics['motor_sat_pct']:.1f}" if metrics["motor_sat_pct"] else "N/A")

    st.subheader("Electrical")
    st.metric("Vcc Std", f"{metrics['vcc_std']:.3f}" if metrics["vcc_std"] else "N/A")

    st.subheader("Energy")
    st.metric("Volt Drop", f"{metrics['volt_drop']:.2f}" if metrics["volt_drop"] else "N/A")

    st.stop()


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
