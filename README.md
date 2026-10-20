# IncentiviPerTe

Sito statico gratuito con bandi e incentivi per startup e PMI, da Arezzo, per le imprese di tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali per avviare e far crescere l'impresa.

Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.

Il Check-up Bandi è un controllo personalizzato di quali bandi regionali e nazionali sono adatti all'impresa, consegnato come relazione scritta. Si richiede dai contatti già indicati sul sito.

- `python3 scripts/build.py` valida `data/bandi.json` e genera `dist/` (zero dipendenze, zero tracker).
- `python3 scripts/test_build.py` controlla etichette sponsor, prezzi, SEO, accessibilità di base e la rimozione delle pagine obsolete.
- `python3 scripts/update.py` ricontrolla le fonti ufficiali e scrive `report.txt`. Non pubblica il sito.
- `python3 scripts/build_redirect.py` genera `dist-redirect/`, il rimando dal vecchio indirizzo. Non pubblica il sito.
- Pagine generate: schede in `bando/`, aree (`nazionale.html`, `toscana.html`, `umbria.html`, `emilia-romagna.html`) e destinatari in `settore/`.
- Il sito è su Cloudflare Pages, alla radice di https://incentiviperte.pages.dev. Il workflow in `.github/workflows/` esegue solo i test.

## Pubblicazione

Dopo `python3 scripts/build.py`:

- Cloudflare Pages (il sito): `wrangler pages deploy dist --project-name=incentiviperte --branch=main`
- Branch `gh-pages` (solo il rimando, non il sito): `python3 scripts/build_redirect.py`, poi pubblica il contenuto di `dist-redirect/`. Ogni pagina rimanda allo stesso percorso su https://incentiviperte.pages.dev/; la 404 del rimando manda alla home nuova.

Niente cookie e niente script di terze parti. Ogni spazio a pagamento porta l'etichetta Sponsorizzato. FoglioPEF è un progetto dello stesso titolare, non un link affiliato.
