# Project notes — VME Craftsmanship

I replicated the Asness–Moskowitz–Pedersen value/momentum correlation signature on Ken French data, then tested whether AQR-style integrate construction beats a simple mix after turnover costs.

**What I found:** value–momentum correlation stayed negative (~−0.19). Mix kept a higher net Sharpe than integrate at 10 bps, so the construction upgrade did not win in this public-data setup. Both series clear a high t-stat bar; I still treat any “new” construction edge cautiously under multiple-testing discipline.
