# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 11:25:30 2026

@author: Adwait
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import tempfile
import sys
import os

# ensure pages folder is in path
sys.path.append(os.path.dirname(__file__))

from compute_logic1 import analyze_log, assess_subsystems, overall_bottleneck


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="FlightDegrade",
    layout="wide"
)

# Optional margin tightening
st.markdown("""
<style>
.block-container {
    padding-left: 3rem;
    padding-right: 3rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------- TITLE ----------------
st.title("📉 FlightDegrade")
st.caption("Post-Flight Degradation & Subsystem Health Analysis")


# ---------------- FILE UPLOAD ----------------
st.markdown("### Upload Flight Log (.BIN)")
uploaded_file = st.file_uploader("Upload ArduPilot BIN file", type=["bin"])

log_path = None

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp.write(uploaded_file.getbuffer())
        log_path = tmp.name


# ---------------- ANALYSIS ----------------
metrics = None
series = None
subs = None
bottleneck = None
solution = None

if log_path:
    metrics, series = analyze_log(log_path)
    subs = assess_subsystems(metrics)
    bottleneck, solution = overall_bottleneck(subs)


# ---------------- CARD FUNCTION ----------------
def subsystem_card(title, fig, data):
    st.subheader(title)

    col1, col2 = st.columns([3, 2])

    # LEFT: Graph
    with col1:
        st.plotly_chart(fig, use_container_width=True, height=340)

    # RIGHT: Text
    with col2:
        st.markdown("**Issues Detected**")
        if data["issues"]:
            for i in data["issues"]:
                st.write("•", i)
        else:
            st.write("None")

        st.markdown("**Interpretation**")
        st.write(data["interp"])

        st.markdown("**Recommendation**")
        st.write(data["rec"])

    st.markdown(f"**Health Metric:** {data['health']:.2f}")
    st.markdown("---")


# ---------------- SUBSYSTEM SECTION ----------------
if subs is not None:

    st.header("Subsystem Health")

    # ---------- THRUST ----------
    if len(series["thrust"]) > 0:
        thrust = np.array(series["thrust"])

        fig_thrust = go.Figure()
        fig_thrust.add_hrect(y0=0.95, y1=1.0, fillcolor="red", opacity=0.15, line_width=0)

        fig_thrust.add_trace(go.Scatter(
            y=thrust,
            mode="lines",
            name="Thrust",
            line=dict(color="#1f77b4", width=2)
        ))

        fig_thrust.add_hline(y=0.95, line_dash="dash", line_color="red")

        sat_pct = np.mean(thrust >= 0.95) * 100
        fig_thrust.add_annotation(
            x=0.98,
            y=0.98,
            xref="paper",
            yref="paper",
            text=f"Saturation: {sat_pct:.1f}%",
            showarrow=False,
            font=dict(size=12)
        )

        fig_thrust.update_yaxes(range=[0, 1], title="Thrust Fraction")
        fig_thrust.update_xaxes(title="Time")
        fig_thrust.update_layout(margin=dict(l=20, r=20, t=30, b=20))

        subsystem_card("Thrust Margin", fig_thrust, subs["thrust"])

    # ---------- BATTERY ----------
    if len(series["battery"]) > 0:
        batt = np.array(series["battery"])

        fig_batt = go.Figure()
        fig_batt.add_hrect(y0=22, y1=25, fillcolor="green", opacity=0.08, line_width=0)

        fig_batt.add_trace(go.Scatter(
            y=batt,
            mode="lines",
            line=dict(color="#1f77b4", width=2),
            name="Voltage"
        ))

        fig_batt.add_hline(y=21, line_dash="dash", line_color="red")

        vmin = np.min(batt)
        fig_batt.add_annotation(
            x=0.98,
            y=0.02,
            xref="paper",
            yref="paper",
            text=f"Min: {vmin:.2f} V",
            showarrow=False,
            font=dict(size=12)
        )

        fig_batt.update_yaxes(range=[18, 25], title="Voltage (V)")
        fig_batt.update_xaxes(title="Time")
        fig_batt.update_layout(margin=dict(l=20, r=20, t=30, b=20))

        subsystem_card("Battery", fig_batt, subs["battery"])

    # ---------- FC POWER ----------
    if len(series["vcc"]) > 0:
        vcc = np.array(series["vcc"])

        fig_vcc = go.Figure()
        fig_vcc.add_hrect(y0=5.0, y1=5.3, fillcolor="green", opacity=0.10, line_width=0)

        fig_vcc.add_trace(go.Scatter(
            y=vcc,
            mode="lines",
            line=dict(color="#1f77b4", width=2),
            name="Vcc"
        ))

        fig_vcc.add_hline(y=4.8, line_dash="dash", line_color="red")

        vcc_min = np.min(vcc)
        fig_vcc.add_annotation(
            x=0.98,
            y=0.02,
            xref="paper",
            yref="paper",
            text=f"Min: {vcc_min:.2f} V",
            showarrow=False,
            font=dict(size=12)
        )

        fig_vcc.update_yaxes(range=[4.7, 5.4], title="FC Voltage (V)")
        fig_vcc.update_xaxes(title="Time")
        fig_vcc.update_layout(margin=dict(l=20, r=20, t=30, b=20))

        subsystem_card("FC Power", fig_vcc, subs["fc"])

    # ---------- PROPULSION ----------
    if len(series["vibration"]) > 0:
        vib = np.array(series["vibration"])

        fig_vib = go.Figure()
        fig_vib.add_vrect(x0=0, x1=0.3, fillcolor="green", opacity=0.08, line_width=0)
        fig_vib.add_vrect(x0=0.3, x1=0.6, fillcolor="yellow", opacity=0.08, line_width=0)
        fig_vib.add_vrect(x0=0.6, x1=0.8, fillcolor="red", opacity=0.08, line_width=0)

        fig_vib.add_trace(go.Histogram(
            x=vib,
            nbinsx=40,
            marker_color="#1f77b4",
            opacity=0.85
        ))

        rms = np.sqrt(np.mean(vib**2))
        fig_vib.add_vline(x=rms, line_dash="dash", line_color="black")

        fig_vib.add_annotation(
            x=rms,
            y=0.95,
            xref="x",
            yref="paper",
            text=f"RMS: {rms:.2f}",
            showarrow=False,
            font=dict(size=12)
        )

        fig_vib.update_xaxes(range=[0, 0.8], title="Gyro Vibration Magnitude")
        fig_vib.update_yaxes(title="Count")
        fig_vib.update_layout(margin=dict(l=20, r=20, t=30, b=20))

        subsystem_card("Propulsion", fig_vib, subs["propulsion"])

    # ---------- MOTOR BALANCE ----------
    if len(series["motors"]) > 0:
        motors = np.array(series["motors"])
        mean_vals = np.mean(motors, axis=0)

        fig_motor = go.Figure()
        labels = ["M1", "M2", "M3", "M4"]

        fig_motor.add_trace(go.Bar(
            x=labels,
            y=mean_vals,
            marker_color="#1f77b4"
        ))

        mean_all = np.mean(mean_vals)
        fig_motor.add_hline(y=mean_all, line_dash="dash", line_color="black")

        imbalance = np.std(mean_vals)
        fig_motor.add_annotation(
            x=0.5,
            y=0.95,
            xref="paper",
            yref="paper",
            text=f"Imbalance: {imbalance:.1f}",
            showarrow=False,
            font=dict(size=12)
        )

        fig_motor.update_yaxes(title="Motor Output (PWM)")
        fig_motor.update_xaxes(title="Motor")
        fig_motor.update_layout(margin=dict(l=20, r=20, t=30, b=20))

        subsystem_card("Motor Balance", fig_motor, subs["motor"])

    # ---------- OVERALL ----------
    st.header("Overall System Diagnosis")
    st.write(f"**Primary Bottleneck:** {bottleneck}")
    st.write(f"**Recommended Action:** {solution}")


# ---------------- BACK ----------------
st.divider()
if st.button("⬅ Back to Home"):
    st.switch_page("Home.py")