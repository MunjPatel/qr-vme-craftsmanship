from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # local shared/ for standalone + Streamlit Cloud
from shared.plot_theme import COLORS, apply_plotly_theme  # noqa: E402

st.set_page_config(page_title="VME Craftsmanship", layout="wide")
st.markdown(
    f"<style>.stApp {{ background-color: {COLORS['bg']}; color: {COLORS['text']}; }}</style>",
    unsafe_allow_html=True,
)
st.title("VME Craftsmanship — Mix vs Integrate")
out = ROOT / "outputs"
if not (out / "meta.json").exists():
    st.warning("Run `python 08_qr_vme_craftsmanship/scripts/run_mvp.py` first.")
    st.stop()

meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
summary = pd.read_csv(out / "strategy_summary.csv")
cost = pd.read_csv(out / "cost_sensitivity.csv")
cum = pd.read_csv(out / "cum_net_mix_vs_integrate.csv", parse_dates=["date"])

c1, c2, c3 = st.columns(3)
c1.metric("Val–Mom corr", f"{meta['diagnostics']['val_mom_corr']:.3f}")
c2.metric("Integrate − Mix Sharpe", f"{meta['lift']['integrate_minus_mix_sharpe']:.3f}")
c3.metric("Integrate clears HLZ t>3", str(meta["lift"]["integrate_clears_hlz"]))

tab1, tab2, tab3 = st.tabs(["Wealth", "Cost sensitivity", "Memo"])
with tab1:
    m = cum.melt("date", var_name="method", value_name="wealth")
    fig = px.line(m, x="date", y="wealth", color="method", title="Cumulative net wealth (10 bps)")
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(summary, use_container_width=True)
with tab2:
    fig = px.line(cost, x="cost_bps", y="sharpe_net", color="method", markers=True)
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
with tab3:
    st.markdown((out / "RESEARCH_MEMO.md").read_text(encoding="utf-8"))
