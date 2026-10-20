# IncentiviPerTe

Sito statico gratuito con bandi e incentivi per startup e PMI, da Arezzo, per le imprese di Toscana (compresa la Camera di Commercio di Arezzo-Siena), Umbria ed Emilia-Romagna, più gli incentivi nazionali per avviare e far crescere l'impresa.

Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.

Il Check-up Bandi è un controllo personalizzato di quali bandi regionali e nazionali sono adatti all'impresa, consegnato come relazione scritta. Si richiede dai contatti già indicati sul sito.

- `python3 scripts/build.py` valida `data/bandi.json` e genera `dist/` (zero dipendenze, zero tracker).
- `python3 scripts/test_build.py` controlla etichette sponsor, prezzi, SEO, accessibilità di base e la rimozione delle pagine obsolete.
- `python3 scripts/update.py` ricontrolla le fonti ufficiali e scrive `report.txt`. Non pubblica il sito.
- Pagine generate: schede in `bando/`, aree (`nazionale.html`, `toscana.html`, `umbria.html`, `emilia-romagna.html`) e destinatari in `settore/`.
- La pubblicazione prevista è il branch `gh-pages` oppure Cloudflare Pages (output `dist`). Il workflow in `.github/workflows/` esegue solo i test.

Niente cookie e niente script di terze parti. Ogni spazio a pagamento porta l'etichetta Sponsorizzato. FoglioPEF è un progetto dello stesso titolare, non un link affiliato.
