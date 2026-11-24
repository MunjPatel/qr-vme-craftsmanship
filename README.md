# VME Craftsmanship — Mix vs Integrate

**Role:** Quantitative Researcher  
**Sources:** Asness–Moskowitz–Pedersen (2013); AQR Portfolio Construction Matters (2017); Harvey–Liu–Zhu (2016)

## Reproduce

```bash
cd portfolio/projects
.venv\Scripts\activate
python 08_qr_vme_craftsmanship/scripts/run_mvp.py
streamlit run 08_qr_vme_craftsmanship/app/dashboard.py
```

Read `outputs/RESEARCH_MEMO.md` first.



1. Push this repo to GitHub (already done if you cloned from MunjPatel/qr-vme-craftsmanship).
2. Go to https://share.streamlit.io/ → **New app**
3. Select repo `MunjPatel/qr-vme-craftsmanship`, branch `main`
4. Main file path: `app/dashboard.py`
5. Python version 3.11+ recommended → Deploy

The app reads artifacts under `outputs/`. Re-run `scripts/run_mvp.py` locally if you need to refresh them before pushing.
