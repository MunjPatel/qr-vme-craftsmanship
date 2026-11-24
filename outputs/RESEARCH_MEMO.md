# Research Memo — VME Craftsmanship (Mix vs Integrate)

## Hypothesis
Asness–Moskowitz–Pedersen (2013) document pervasive value and momentum premia that are negatively correlated. AQR (Fitzgibbons et al.) argue **integrate** construction should dominate **mix** by avoiding stocks/portfolios with offsetting style extremes.

## Data
Ken French 25 Size–BM value-weighted portfolios; FF5 HML; FF Momentum factor. Public data only.

## Design
Walk-forward monthly L/S: form weights at month t, earn t+1. Momentum = 12–1. Compare value-only, momentum-only, 50/50 **mix**, and z-score **integrate**. Net of one-way turnover × cost_bps.

## Key results
- HML–MOM correlation: **-0.191**
- Mix net Sharpe (10 bps): **0.517** (t=4.01)
- Integrate net Sharpe (10 bps): **0.423** (t=3.28)
- Integrate − Mix Sharpe: **-0.094**
- Clears HLZ t>3? integrate=True, mix=True

## What failed / weakened
- Shorter 6-1 momentum integrate variant and wider top-40% book are reported in `strategy_summary.csv` as ablations.
- HLZ (2016): a newly emphasized construction edge should be interpreted against a ~t>3 hurdle after data mining — treat borderline t-stats as provisional.

## Limitations
Portfolio-level proxy ≠ stock-level AQR integrate study. Costs are illustrative. No capacity/impact model.
