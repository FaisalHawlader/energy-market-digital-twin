from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Energy Market Digital Twin", layout="wide")
st.markdown(
    """
    <style>
      .stApp {background: linear-gradient(180deg, #08111f 0%, #0b1526 100%); color: #eef4ff;}
      .block-container {padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1400px;}
      .hero {padding: 1.1rem 1.3rem; border: 1px solid rgba(148,163,184,.18); border-radius: 18px; background: rgba(15,23,42,.55); backdrop-filter: blur(8px); margin-bottom: 1rem;}
      .hero h1 {font-size: 2rem; margin: 0 0 .25rem 0; color: #f8fafc;}
      .hero p {margin: 0; color: #cbd5e1;}
      .metric-card {padding: 1rem 1.1rem; border-radius: 18px; background: rgba(15,23,42,.75); border: 1px solid rgba(148,163,184,.14); box-shadow: 0 6px 24px rgba(2,8,23,.18);}
      .metric-title {font-size: .82rem; color: #94a3b8; margin-bottom: .35rem; text-transform: uppercase; letter-spacing: .04em;}
      .metric-value {font-size: 1.65rem; font-weight: 700; color: #f8fafc;}
      .metric-sub {font-size: .82rem; color: #cbd5e1; margin-top: .35rem;}
      .section-title {font-size: 1.1rem; font-weight: 700; color: #f8fafc; margin: .5rem 0 .75rem 0;}
      .alert-box {padding: .8rem 1rem; border-radius: 14px; background: rgba(30,41,59,.78); border-left: 4px solid #f59e0b; margin-bottom: .6rem;}
      .critical {border-left-color: #ef4444;}
      .info {border-left-color: #38bdf8;}
    </style>
    """,
    unsafe_allow_html=True,
)

def fetch_json(endpoint: str, params: dict | None = None):
    response = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=5)
    response.raise_for_status()
    return response.json()

st.markdown(
    """
    <div class="hero">
      <h1>⚡ Industrial Energy Market Digital Twin</h1>
      <p>Kafka-driven digital twin for grid state, pricing, carbon intensity, reserve margin, and battery operation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Control Panel")
    auto_refresh = st.slider("Refresh interval (seconds)", 1, 10, 2)
    history_points = st.slider("History window", 30, 300, 120, 10)
    forecast_horizon = st.slider("Forecast horizon (minutes)", 5, 60, 20, 5)
    st.caption(f"API base: {API_BASE}")

st_autorefresh(interval=auto_refresh * 1000, key="dashboard-refresh")

try:
    latest = fetch_json("/api/state")
    history = fetch_json("/api/history", {"points": history_points})
    forecast = fetch_json("/api/forecast", {"horizon": forecast_horizon})
    alerts = fetch_json("/api/alerts", {"limit": 8})
except requests.RequestException as exc:
    st.error(f"Backend not reachable at {API_BASE}: {exc}")
    st.stop()

history_df = pd.DataFrame(history)
forecast_df = pd.DataFrame(forecast["points"])
for frame in (history_df, forecast_df):
    if not frame.empty and "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])

def metric_card(title: str, value: str, subtitle: str = "") -> str:
    return f'<div class="metric-card"><div class="metric-title">{title}</div><div class="metric-value">{value}</div><div class="metric-sub">{subtitle}</div></div>'

row1 = st.columns(4)
row1[0].markdown(metric_card("Demand", f"{latest['demand_mw']:.1f} MW", "Current total load"), unsafe_allow_html=True)
row1[1].markdown(metric_card("Market Price", f"€{latest['market_price_eur_mwh']:.2f}", "Per MWh"), unsafe_allow_html=True)
row1[2].markdown(metric_card("Renewable Share", f"{latest['renewable_share_pct']:.1f}%", "Solar + wind contribution"), unsafe_allow_html=True)
row1[3].markdown(metric_card("Grid Status", latest['grid_status'], f"Imbalance {latest['imbalance_mw']:.1f} MW"), unsafe_allow_html=True)

row2 = st.columns(4)
row2[0].markdown(metric_card("Battery SOC", f"{latest['battery_level_pct']:.1f}%", latest['battery_mode'].title()), unsafe_allow_html=True)
row2[1].markdown(metric_card("Reserve Margin", f"{latest['reserve_margin_mw']:.1f} MW", "Post-dispatch reserve"), unsafe_allow_html=True)
row2[2].markdown(metric_card("Carbon Intensity", f"{latest['carbon_intensity_gco2_kwh']:.0f} gCO₂/kWh", "Estimated operational mix"), unsafe_allow_html=True)
row2[3].markdown(metric_card("Interconnector", f"{latest['interconnector_import_mw']:.1f} MW", "Imported balancing energy"), unsafe_allow_html=True)

left, right = st.columns([2, 1])
with left:
    st.markdown('<div class="section-title">Live Supply-Demand Envelope</div>', unsafe_allow_html=True)
    supply_fig = px.line(history_df, x="timestamp", y=["demand_mw", "solar_mw", "wind_mw", "conventional_mw"], template="plotly_dark")
    supply_fig.update_layout(height=360, margin=dict(l=15, r=15, t=10, b=10), legend_title_text="")
    st.plotly_chart(supply_fig, use_container_width=True)

    st.markdown('<div class="section-title">Price and Carbon Pressure</div>', unsafe_allow_html=True)
    pressure_fig = px.line(history_df, x="timestamp", y=["market_price_eur_mwh", "carbon_intensity_gco2_kwh"], template="plotly_dark")
    pressure_fig.update_layout(height=320, margin=dict(l=15, r=15, t=10, b=10), legend_title_text="")
    st.plotly_chart(pressure_fig, use_container_width=True)

with right:
    st.markdown('<div class="section-title">Operational Recommendation</div>', unsafe_allow_html=True)
    st.info(f"**{forecast['recommendation']}**\n\n{forecast['reasoning']}")

    st.markdown('<div class="section-title">Recent Alerts</div>', unsafe_allow_html=True)
    if alerts:
        for item in alerts:
            level = item["severity"]
            css = "critical" if level == "critical" else ("info" if level == "info" else "")
            st.markdown(
                f'<div class="alert-box {css}"><strong>{item["title"]}</strong><br>{item["message"]}<br><small>{item["timestamp"]}</small></div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("No active alert events in the recent window.")

    st.markdown('<div class="section-title">Asset Mix Snapshot</div>', unsafe_allow_html=True)
    mix_df = pd.DataFrame({"asset": ["Solar", "Wind", "Conventional", "Import"], "mw": [latest["solar_mw"], latest["wind_mw"], latest["conventional_mw"], latest["interconnector_import_mw"]]})
    mix_fig = px.pie(mix_df, values="mw", names="asset", hole=0.55, template="plotly_dark")
    mix_fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), legend_title_text="")
    st.plotly_chart(mix_fig, use_container_width=True)

bottom_left, bottom_right = st.columns(2)
with bottom_left:
    st.markdown('<div class="section-title">Short-Horizon Forecast</div>', unsafe_allow_html=True)
    ffig = px.line(forecast_df, x="timestamp", y=["predicted_demand_mw", "predicted_price_eur_mwh", "predicted_renewable_share_pct"], template="plotly_dark")
    ffig.update_layout(height=340, margin=dict(l=15, r=15, t=10, b=10), legend_title_text="")
    st.plotly_chart(ffig, use_container_width=True)

with bottom_right:
    st.markdown('<div class="section-title">Recent Telemetry Table</div>', unsafe_allow_html=True)
    st.dataframe(
        history_df[["timestamp", "demand_mw", "solar_mw", "wind_mw", "conventional_mw", "battery_level_pct", "market_price_eur_mwh", "carbon_intensity_gco2_kwh", "grid_status"]].sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True,
        height=340,
    )
