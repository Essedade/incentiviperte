# IncentiviPerTe – MVP statico
- `python3 scripts/build.py` genera il sito in `dist/` (zero dipendenze esterne).
- `python3 scripts/update.py` ricontrolla le fonti ufficiali e scrive `report.txt`.
- `ci/update.yml` è pronto (va spostato in `.github/workflows/` per usarlo) ma non attivo (solo avvio manuale, schedule commentato).
- Pubblicazione: Cloudflare Pages (build `python3 scripts/build.py`, output `dist`) oppure GitHub Pages.
