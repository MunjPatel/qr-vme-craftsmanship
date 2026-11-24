"""Ken French / AQR-style public factor & portfolio loaders."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache"


def _ensure():
    CACHE.mkdir(parents=True, exist_ok=True)


def _parse_ff_monthly_block(raw: str, n_cols: int) -> pd.DataFrame:
    lines = raw.splitlines()
    start = None
    for i, line in enumerate(lines):
        tok = line.strip().split(",")[0].strip()
        if tok.isdigit() and len(tok) == 6:
            start = i
            break
    if start is None:
        raise ValueError("Could not find YYYYMM start in Ken French file")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        tok = lines[i].strip().split(",")[0].strip()
        if not tok or not tok.isdigit():
            end = i
            break
    body = "\n".join(lines[start:end])
    df = pd.read_csv(io.StringIO(body), header=None)
    df = df.iloc[:, :n_cols]
    df[0] = df[0].astype(str)
    df["date"] = pd.to_datetime(df[0], format="%Y%m") + pd.offsets.MonthEnd(0)
    for c in range(1, n_cols):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _download_ff_zip(url: str) -> str:
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith((".csv", ".txt")))
        return zf.read(name).decode("utf-8", errors="ignore")


def load_ff5(force: bool = False) -> pd.DataFrame:
    _ensure()
    out = CACHE / "ff5.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"]).set_index("date")
    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip"
    raw = _download_ff_zip(url)
    df = _parse_ff_monthly_block(raw, 7)
    df.columns = ["yyyymm", "Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF", "date"]
    for c in ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]:
        df[c] = df[c] / 100.0
    df = df.set_index("date").sort_index()
    df.to_csv(out)
    return df


def load_mom(force: bool = False) -> pd.Series:
    _ensure()
    out = CACHE / "mom.csv"
    if out.exists() and not force:
        s = pd.read_csv(out, parse_dates=["date"]).set_index("date")["MOM"]
        return s
    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip"
    raw = _download_ff_zip(url)
    df = _parse_ff_monthly_block(raw, 2)
    df.columns = ["yyyymm", "MOM", "date"]
    df["MOM"] = df["MOM"] / 100.0
    s = df.set_index("date")["MOM"].sort_index()
    s.to_frame().to_csv(out)
    return s


def load_25_size_bm(force: bool = False) -> pd.DataFrame:
    """25 value-weighted portfolios formed on size and book-to-market."""
    _ensure()
    out = CACHE / "ff25_size_bm.csv"
    if out.exists() and not force:
        return pd.read_csv(out, parse_dates=["date"]).set_index("date")
    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/25_Portfolios_5x5_CSV.zip"
    raw = _download_ff_zip(url)
    # Average Value Weighted Returns -- Monthly first block
    lines = raw.splitlines()
    start = None
    for i, line in enumerate(lines):
        tok = line.strip().split(",")[0].strip()
        if tok.isdigit() and len(tok) == 6:
            start = i
            break
    end = len(lines)
    for i in range(start + 1, len(lines)):
        tok = lines[i].strip().split(",")[0].strip()
        if not tok or not tok.isdigit():
            end = i
            break
    body = "\n".join(lines[start:end])
    df = pd.read_csv(io.StringIO(body), header=None)
    # col0 = yyyymm, then 25 portfolios
    ncols = min(26, df.shape[1])
    df = df.iloc[:, :ncols]
    names = ["yyyymm"] + [f"S{s}BM{b}" for s in range(1, 6) for b in range(1, 6)]
    df.columns = names[:ncols]
    df["date"] = pd.to_datetime(df["yyyymm"].astype(str), format="%Y%m") + pd.offsets.MonthEnd(0)
    for c in df.columns:
        if c not in ("yyyymm", "date"):
            df[c] = pd.to_numeric(df[c], errors="coerce") / 100.0
    df = df.set_index("date").drop(columns=["yyyymm"]).sort_index()
    # Drop missing (-99.99 already coerced)
    df = df.replace(-0.9999, np.nan)
    df.to_csv(out)
    return df


def portfolio_style_scores() -> pd.DataFrame:
    """Static value score from BM quintile; size score from size quintile."""
    rows = []
    for s in range(1, 6):
        for b in range(1, 6):
            rows.append({"portfolio": f"S{s}BM{b}", "size_q": s, "value_q": b})
    return pd.DataFrame(rows).set_index("portfolio")
