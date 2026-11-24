from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from construction import walk_forward_backtest  # noqa: E402
from data import load_25_size_bm, load_ff5, load_mom  # noqa: E402
from metrics import summarize, val_mom_diagnostics  # noqa: E402


def main():
    out = ROOT / "outputs"
    out.mkdir(parents=True, exist_ok=True)

    ff5 = load_ff5()
    mom = load_mom()
    ports = load_25_size_bm()

    # Align
    common = ff5.index.intersection(mom.index).intersection(ports.index)
    ff5, mom, ports = ff5.loc[common], mom.loc[common], ports.loc[common]

    diag = val_mom_diagnostics(ff5["HML"], mom)
    pd.Series(diag).to_csv(out / "vme_diagnostics.csv")

    # Ablations + main methods
    methods = ["value", "momentum", "mix", "integrate"]
    cost_grid = [0.0, 5.0, 10.0, 20.0]
    summaries = []
    curves = {}

    for method in methods:
        bt = walk_forward_backtest(ports, method=method, cost_bps=10.0)
        bt.to_csv(out / f"returns_{method}.csv")
        curves[method] = bt
        summaries.append(summarize(bt["net"], f"{method}_net_10bps"))
        summaries.append(summarize(bt["gross"], f"{method}_gross"))

    # Cost sensitivity for mix vs integrate
    cost_rows = []
    for c in cost_grid:
        for method in ("mix", "integrate"):
            bt = walk_forward_backtest(ports, method=method, cost_bps=c)
            cost_rows.append(
                {
                    "method": method,
                    "cost_bps": c,
                    "sharpe_net": summarize(bt["net"], method)["sharpe"],
                    "ann_mean_net": summarize(bt["net"], method)["ann_mean"],
                    "avg_turnover": float(bt["turnover"].mean()),
                    "t_stat": summarize(bt["net"], method)["t_stat"],
                }
            )
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(out / "cost_sensitivity.csv", index=False)

    # Failed / weak ablation: weekly-style faster mom (use lookback 6)
    bt_fast = walk_forward_backtest(ports, method="integrate", mom_lookback=6, cost_bps=10.0)
    summaries.append(summarize(bt_fast["net"], "integrate_mom6_net_10bps"))
    bt_fast.to_csv(out / "returns_integrate_mom6.csv")

    # Equal top_frac stress
    bt_wide = walk_forward_backtest(ports, method="integrate", top_frac=0.4, cost_bps=10.0)
    summaries.append(summarize(bt_wide["net"], "integrate_top40_net_10bps"))

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(out / "strategy_summary.csv", index=False)

    # Cumulative net wealth mix vs integrate
    cum = pd.DataFrame(
        {
            "mix": (1 + curves["mix"]["net"]).cumprod(),
            "integrate": (1 + curves["integrate"]["net"]).cumprod(),
        }
    )
    cum.to_csv(out / "cum_net_mix_vs_integrate.csv")

    # Lift table
    mix_s = summary_df.set_index("strategy").loc["mix_net_10bps"]
    int_s = summary_df.set_index("strategy").loc["integrate_net_10bps"]
    lift = {
        "integrate_minus_mix_sharpe": float(int_s["sharpe"] - mix_s["sharpe"]),
        "integrate_minus_mix_ann_mean": float(int_s["ann_mean"] - mix_s["ann_mean"]),
        "integrate_clears_hlz": bool(int_s["clears_hlz_t3"]),
        "mix_clears_hlz": bool(mix_s["clears_hlz_t3"]),
        "val_mom_corr": diag["val_mom_corr"],
    }

    memo = f"""# Research Memo — VME Craftsmanship (Mix vs Integrate)

## Hypothesis
Asness–Moskowitz–Pedersen (2013) document pervasive value and momentum premia that are negatively correlated. AQR (Fitzgibbons et al.) argue **integrate** construction should dominate **mix** by avoiding stocks/portfolios with offsetting style extremes.

## Data
Ken French 25 Size–BM value-weighted portfolios; FF5 HML; FF Momentum factor. Public data only.

## Design
Walk-forward monthly L/S: form weights at month t, earn t+1. Momentum = 12–1. Compare value-only, momentum-only, 50/50 **mix**, and z-score **integrate**. Net of one-way turnover × cost_bps.

## Key results
- HML–MOM correlation: **{diag['val_mom_corr']:.3f}**
- Mix net Sharpe (10 bps): **{mix_s['sharpe']:.3f}** (t={mix_s['t_stat']:.2f})
- Integrate net Sharpe (10 bps): **{int_s['sharpe']:.3f}** (t={int_s['t_stat']:.2f})
- Integrate − Mix Sharpe: **{lift['integrate_minus_mix_sharpe']:.3f}**
- Clears HLZ t>3? integrate={lift['integrate_clears_hlz']}, mix={lift['mix_clears_hlz']}

## What failed / weakened
- Shorter 6-1 momentum integrate variant and wider top-40% book are reported in `strategy_summary.csv` as ablations.
- HLZ (2016): a newly emphasized construction edge should be interpreted against a ~t>3 hurdle after data mining — treat borderline t-stats as provisional.

## Limitations
Portfolio-level proxy ≠ stock-level AQR integrate study. Costs are illustrative. No capacity/impact model.
"""
    (out / "RESEARCH_MEMO.md").write_text(memo, encoding="utf-8")

    meta = {
        "n_months": int(len(common)),
        "start": str(common.min().date()),
        "end": str(common.max().date()),
        "diagnostics": diag,
        "lift": lift,
        "sources": [
            "Asness, Moskowitz, Pedersen (2013), Value and Momentum Everywhere, JF",
            "Fitzgibbons et al. (2017), Portfolio Construction Matters, AQR",
            "Harvey, Liu, Zhu (2016), ... and the Cross-Section of Expected Returns, RFS",
        ],
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("QR P1 VME craftsmanship complete ->", out)
    print(pd.Series(lift))


if __name__ == "__main__":
    main()
