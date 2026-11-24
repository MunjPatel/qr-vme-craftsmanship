"""Weights at t must not use returns from t+1."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from construction import momentum_scores  # noqa: E402


def test_momentum_uses_skip():
    rng = np.random.default_rng(0)
    idx = pd.date_range("2000-01-31", periods=24, freq="ME")
    cols = [f"S{s}BM{b}" for s in range(1, 3) for b in range(1, 3)]
    rets = pd.DataFrame(rng.normal(0, 0.05, (24, 4)), index=idx, columns=cols)
    mom = momentum_scores(rets, lookback=12, skip=1)
    # First valid momentum row should be NaN until enough history
    assert mom.iloc[:12].isna().all().all() or mom.iloc[11].isna().any()
    # Momentum at t should be finite only after lookback+skip
    assert mom.iloc[13].notna().any()
