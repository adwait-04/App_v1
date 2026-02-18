# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 11:08:13 2026

@author: Adwait
"""

import streamlit as st

st.set_page_config(
    page_title="Drone Health Analytics",
    page_icon="🚁",
    layout="wide"
)

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

    if st.button("Open FlightScore"):
        st.switch_page("pages/1_FlightScore.py")

# FlightDegrade
with col2:
    st.markdown("### 📉 FlightDegrade")
    st.write("Post-flight degradation and performance drift monitoring")

    if st.button("Open FlightDegrade"):
        st.switch_page("pages/FlightDegrade.py")

st.markdown("---")

# MissionFeas
st.markdown("### 🎯 MissionFeas")
st.write("Mission feasibility and payload recommendation")

st.button("Coming Soon", disabled=True, key="mission_soon")


st.divider()
st.caption("Drone Health Analytics")