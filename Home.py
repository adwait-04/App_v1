import streamlit as st

# ---------- HEADER ----------
col_logo, col_title = st.columns([1, 4])

with col_logo:
    st.write("")  # logo placeholder

with col_title:
    st.title("Drone Health Analytics Platform")
    st.caption("Flight Performance • Degradation • Mission Feasibility")

st.divider()

# ---------- MODULES ----------
st.subheader("Select Analysis Module")

col1, col2 = st.columns(2)

# FlightScore
with col1:
    st.markdown("### 📊 FlightScore")
    st.write("Drone flight performance scoring and optimal flight identification")

    st.page_link(
        "pages/1_FlightScore.py",
        label="Open FlightScore",
        icon="✈️"
    )

# FlightDegrade
with col2:
    st.markdown("### 📉 FlightDegrade")
    st.write("Post-flight degradation and performance drift monitoring")

    st.page_link(
        "pages/FlightDegrade.py",
        label="Open FlightDegrade",
        icon="📉"
    )

st.markdown("---")

# MissionFeas
st.markdown("### 🎯 MissionFeas")
st.write("Mission feasibility and payload recommendation")

st.button("Coming Soon", disabled=True)

st.divider()
st.caption("Drone Health Analytics")


