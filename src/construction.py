"""Mix vs integrate style portfolio construction (AQR craftsmanship)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data import portfolio_style_scores


def momentum_scores(returns: pd.DataFrame, lookback: int = 12, skip: int = 1) -> pd.DataFrame:
    """12-1 month momentum for each portfolio column."""
    # product of (1+r) over months t-lookback ... t-skip, minus 1
    rolled = (1 + returns).rolling(lookback).apply(lambda x: np.prod(x) - 1, raw=True)
    # skip most recent month: shift by skip
    return rolled.shift(skip)


def zscore_cross_section(row: pd.Series) -> pd.Series:
    mu, sig = row.mean(), row.std()
    if sig == 0 or np.isnan(sig):
        return row * 0.0
    return (row - mu) / sig


def integrate_scores(value_q: pd.Series, mom: pd.Series) -> pd.Series:
    """Average of cross-sectional z-scores of value quintile and momentum."""
    # value_q constant across time for each name — broadcast
    v = value_q.reindex(mom.index)
    # For a single date cross-section, mom is a Series over portfolios
    z_v = zscore_cross_section(v.astype(float))
    z_m = zscore_cross_section(mom.astype(float))
    return 0.5 * z_v + 0.5 * z_m


def long_short_from_scores(scores: pd.Series, top_frac: float = 0.2) -> pd.Series:
    """Equal-weight long top_frac / short bottom_frac. Weights sum to ~0, gross 1."""
    s = scores.dropna()
    n = len(s)
    k = max(int(np.floor(top_frac * n)), 1)
    order = s.sort_values()
    shorts = order.index[:k]
    longs = order.index[-k:]
    w = pd.Series(0.0, index=scores.index)
    w.loc[longs] = 1.0 / k
    w.loc[shorts] = -1.0 / k
    return w


def mix_weights(value_q: pd.Series, mom: pd.Series, top_frac: float = 0.2) -> pd.Series:
    """50/50 mix of value L/S and momentum L/S portfolios."""
    w_v = long_short_from_scores(value_q.astype(float), top_frac=top_frac)
    w_m = long_short_from_scores(mom.astype(float), top_frac=top_frac)
    return 0.5 * w_v.fillna(0) + 0.5 * w_m.fillna(0)


def integrate_weights(value_q: pd.Series, mom: pd.Series, top_frac: float = 0.2) -> pd.Series:
    scores = integrate_scores(value_q, mom)
    return long_short_from_scores(scores, top_frac=top_frac)


def walk_forward_backtest(
    returns: pd.DataFrame,
    method: str = "integrate",
    top_frac: float = 0.2,
    mom_lookback: int = 12,
    mom_skip: int = 1,
    min_hist: int = 36,
    cost_bps: float = 10.0,
) -> pd.DataFrame:
    """
    Expanding-window monthly backtest.
    Weights formed at t using info through t; earn returns at t+1.
    """
    scores_meta = portfolio_style_scores()
    value_q = scores_meta["value_q"]
    mom_panel = momentum_scores(returns, lookback=mom_lookback, skip=mom_skip)

    dates = returns.index
    rows = []
    prev_w = None
    for i in range(min_hist, len(dates) - 1):
        dt = dates[i]
        nxt = dates[i + 1]
        mom = mom_panel.loc[dt]
        if mom.dropna().shape[0] < 10:
            continue
        vq = value_q.reindex(mom.index)
        if method == "mix":
            w = mix_weights(vq, mom, top_frac=top_frac)
        elif method == "value":
            w = long_short_from_scores(vq.astype(float), top_frac=top_frac)
        elif method == "momentum":
            w = long_short_from_scores(mom.astype(float), top_frac=top_frac)
        else:
            w = integrate_weights(vq, mom, top_frac=top_frac)

        w = w.reindex(returns.columns).fillna(0.0)
        r_next = returns.loc[nxt].fillna(0.0)
        gross = float((w * r_next).sum())

        # one-way turnover * cost
        if prev_w is None:
            turnover = float(w.abs().sum())  # initial build
        else:
            turnover = float((w - prev_w.reindex(w.index).fillna(0)).abs().sum())
        cost = turnover * (cost_bps / 1e4)
        net = gross - cost
        rows.append(
            {
                "date": nxt,
                "gross": gross,
                "net": net,
                "turnover": turnover,
                "method": method,
            }
        )
        prev_w = w
    return pd.DataFrame(rows).set_index("date")
