"""Performance and Harvey–Liu–Zhu-style inference helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def sharpe(rets: pd.Series, periods: int = 12) -> float:
    s = rets.dropna()
    if s.std() == 0 or len(s) < 3:
        return float("nan")
    return float(np.sqrt(periods) * s.mean() / s.std())


def tstat_mean(rets: pd.Series) -> float:
    s = rets.dropna()
    if len(s) < 3 or s.std() == 0:
        return float("nan")
    return float(s.mean() / (s.std() / np.sqrt(len(s))))


def max_drawdown(rets: pd.Series) -> float:
    wealth = (1 + rets.fillna(0)).cumprod()
    return float((wealth / wealth.cummax() - 1).min())


def summarize(rets: pd.Series, label: str, hlz_hurdle: float = 3.0) -> dict:
    t = tstat_mean(rets)
    return {
        "strategy": label,
        "ann_mean": float(rets.mean() * 12),
        "ann_vol": float(rets.std() * np.sqrt(12)),
        "sharpe": sharpe(rets),
        "t_stat": t,
        "hlz_hurdle": hlz_hurdle,
        "clears_hlz_t3": bool(t == t and abs(t) >= hlz_hurdle),
        "max_dd": max_drawdown(rets),
        "n_months": int(rets.dropna().shape[0]),
    }


def val_mom_diagnostics(hml: pd.Series, mom: pd.Series) -> dict:
    df = pd.concat([hml.rename("HML"), mom.rename("MOM")], axis=1).dropna()
    corr = float(df["HML"].corr(df["MOM"]))
    return {
        "val_mom_corr": corr,
        "hml_sharpe": sharpe(df["HML"]),
        "mom_sharpe": sharpe(df["MOM"]),
        "n_months": int(len(df)),
        "note": "Negative val–mom correlation is the Asness–Moskowitz–Pedersen (2013) signature.",
    }
