#!/usr/bin/env python3
"""Controlli sul generatore: dati, etichette, SEO, pulizia dei file obsoleti."""
import datetime
import html
import json
import pathlib
import re
import sys
import unittest
import urllib.parse
import warnings
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build
import update

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
TODAY = datetime.date(2026, 10, 13)
BASE = build.BASE


def sample(**over):
    row = {
        "id": "esempio-bando",
        "titolo": "Bando di esempio",
        "ente": "Ente",
        "regione": "Toscana",
        "destinatari": ["PMI"],
        "scadenza": "2026-12-01",
        "nota_scadenza": "1/12/2026",
        "sintesi": "Sintesi abbastanza lunga da descrivere la misura senza copiare il bando.",
        "url": "https://example.com/bando",
        "check": "Aperto",
        "ultimo_controllo": "2026-10-13",
        "importo": "10.000 €",
    }
    row.update(over)
    return row


class Validazione(unittest.TestCase):
    def test_rifiuta_id_duplicato_data_e_url(self):
        with self.assertRaises(ValueError):
            build.validate([sample(id="ID Maiuscolo")])
        with self.assertRaises(ValueError):
            build.validate([sample(), sample()])
        with self.assertRaises(ValueError):
            build.validate([sample(scadenza="13/10/2026")])
        with self.assertRaises(ValueError):
            build.validate([sample(url="http://example.com")])
        with self.assertRaises(ValueError):
            build.validate([sample(regione="Lazio")])
        with self.assertRaises(ValueError):
            build.validate([sample(destinatari=[])])
        with self.assertRaises(ValueError):
            build.validate([sample(sintesi="Scrivi a ufficio@example.com per info sul bando lungo")])
        with self.assertRaises(ValueError):
            build.validate([sample(ente="Invitalia")])
        with self.assertRaises(ValueError):
            build.validate([sample(sintesi="Misura curata da Sorbolini per le imprese.")])

    def test_scaduto_e_ordinamento(self):
        rows = build.prepare(
            [sample(id="tardi", scadenza="2026-12-01"), sample(id="vecchio", scadenza="2020-01-01"), sample(id="aperto", scadenza=None)],
            TODAY,
        )
        self.assertEqual([b["id"] for b in rows], ["vecchio", "tardi", "aperto"])
        self.assertTrue(rows[0]["scaduto"])
        self.assertFalse(rows[1]["scaduto"])
        self.assertIn("Scaduto il 01/01/2020", build.deadline_text(rows[0]))
        self.assertIn("Sportello aperto", build.badge(rows[2], TODAY))
        futuro = build.prepare([sample(scadenza="2026-12-01")], TODAY)[0]
        prima = build.badge(futuro, datetime.date(2026, 10, 13))
        dopo = build.badge(futuro, datetime.date(2026, 10, 20))
        self.assertEqual(prima, dopo)
        self.assertIn('data-scadenza="2026-12-01"', prima)
        self.assertIn("Scade il 01/12/2026", prima)
        self.assertNotIn("Mancano", prima)
        self.assertIn(">Scaduto<", build.badge(rows[0], TODAY))
        self.assertEqual(build.qty(1, "bando aperto", "bandi aperti"), "1 bando aperto")
        self.assertEqual(build.qty(0, "bando", "bandi"), "0 bandi")

    def test_apertura_facoltativa(self):
        build.validate([sample(apertura="2026-11-02")])
        with self.assertRaises(ValueError):
            build.validate([sample(apertura="02/12/2026")])
        with self.assertRaises(ValueError):
            build.validate([sample(apertura="2026-12-02", scadenza="2026-12-01")])
        futuro = build.prepare(
            [sample(id="in-arrivo", apertura="2026-12-02", scadenza="2027-03-31", nota_scadenza="Dal 02/12/2026")],
            TODAY,
        )[0]
        self.assertTrue(futuro["in_arrivo"])
        self.assertFalse(futuro["scaduto"])
        self.assertEqual(build.deadline_text(futuro), "Apre il 02/12/2026")
        self.assertIn("Apre il 02/12/2026", build.badge(futuro, TODAY))
        self.assertIn('data-apre="2026-12-02"', build.badge(futuro, TODAY))
        self.assertIn('data-scadenza="2027-03-31"', build.badge(futuro, TODAY))
        self.assertNotIn("Aperto fino al", build.deadline_text(futuro))
        gia = build.prepare(
            [sample(id="gia-aperto", apertura="2026-10-01", scadenza="2026-12-01")],
            TODAY,
        )[0]
        self.assertFalse(gia["in_arrivo"])
        self.assertIn("Aperto fino al 01/12/2026", build.deadline_text(gia))

    def test_apertura_facoltativa(self):
        build.validate([sample(apertura="2026-11-02")])
        with self.assertRaises(ValueError):
            build.validate([sample(apertura="02/12/2026")])
        with self.assertRaises(ValueError):
            build.validate([sample(apertura="2026-12-02", scadenza="2026-12-01")])
        futuro = build.prepare(
            [sample(id="in-arrivo", apertura="2026-12-02", scadenza="2027-03-31", nota_scadenza="Dal 02/12/2026")],
            TODAY,
        )[0]
        self.assertTrue(futuro["in_arrivo"])
        self.assertFalse(futuro["scaduto"])
        self.assertEqual(build.deadline_text(futuro), "Apre il 02/12/2026")
        self.assertIn("Apre il 02/12/2026", build.badge(futuro, TODAY))
        self.assertNotIn("Aperto fino al", build.deadline_text(futuro))
        gia = build.prepare(
            [sample(id="gia-aperto", apertura="2026-10-01", scadenza="2026-12-01")],
            TODAY,
        )[0]
        self.assertFalse(gia["in_arrivo"])
        self.assertIn("Aperto fino al 01/12/2026", build.deadline_text(gia))

    def test_stato_lista_attesa_resta_aperto(self):
        with self.assertRaises(ValueError):
            build.validate([sample(stato="chiuso")])
        with self.assertRaises(ValueError):
            build.validate([sample(stato="lista_attesa", fonte="http://example.com/scheda")])
        build.validate([sample(stato="lista_attesa", fonte="https://example.com/scheda.pdf")])
        row = build.prepare(
            [sample(stato="lista_attesa", scadenza="2026-12-01", fonte="https://example.com/scheda.pdf")],
            TODAY,
        )[0]
        self.assertEqual(row["stato"], "lista_attesa")
        self.assertFalse(row["scaduto"])
        self.assertTrue(build.is_aperto(row))
        self.assertNotIn(">Scaduto<", build.badge(row, TODAY))
        avviso = build.avviso_fondi(row, con_link=True)
        self.assertIn("Risorse esaurite: nuove domande solo in lista d&#x27;attesa.", avviso)
        self.assertIn("Verificato il 13/10/2026", avviso)
        self.assertIn("https://example.com/scheda.pdf", avviso)
        self.assertIn("Fonte ufficiale", avviso)
        self.assertEqual(build.avviso_fondi(build.prepare([sample()], TODAY)[0]), "")

    def test_conto_aperti_esclude_in_arrivo(self):
        rows = build.prepare(
            [
                sample(id="aperto", scadenza="2026-12-01"),
                sample(id="scaduto", scadenza="2020-01-01"),
                sample(id="arrivo", apertura="2026-12-02", scadenza="2027-03-31", nota_scadenza="Dal 02/12/2026"),
                sample(id="sportello", scadenza=None),
                sample(id="apre-oggi", apertura=TODAY.isoformat(), scadenza="2026-12-01"),
            ],
            TODAY,
        )
        self.assertTrue(next(b for b in rows if b["id"] == "arrivo")["in_arrivo"])
        self.assertFalse(build.is_aperto(next(b for b in rows if b["id"] == "arrivo")))
        self.assertTrue(build.is_aperto(next(b for b in rows if b["id"] == "apre-oggi")))
        self.assertEqual(build.conto_aperti(rows), 3)
        self.assertEqual(
            {b["id"] for b in rows if build.is_aperto(b)},
            {"aperto", "sportello", "apre-oggi"},
        )

    def test_title_seo_mancante_non_blocca_la_build(self):
        copia = build.seo_copy
        bid = "esempio-senza-title-seo"
        self.assertNotIn(bid, copia.TITOLO_SCHEDA)
        bando = sample(
            id=bid,
            titolo="Contributo Invitalia + IVA per le fiere di Arezzo-Siena",
            regione="Toscana",
        )
        troppo = "esempio-title-troppo-lungo"
        try:
            with self.assertWarns(UserWarning) as ctx:
                titolo = copia.titolo_scheda(bando)
            self.assertEqual(titolo, "Contributo per le fiere di Arezzo e Siena (Toscana)")
            self.assertLessEqual(len(titolo), 60)
            self.assertNotIn("Invitalia", titolo)
            self.assertNotIn("invitalia", titolo.lower())
            self.assertNotIn("+ IVA", titolo)
            self.assertNotIn("+IVA", titolo)
            self.assertNotIn("Arezzo-Siena", titolo)
            self.assertNotIn("…", titolo)
            self.assertEqual(copia.TITOLO_SCHEDA[bid], titolo)
            messaggio = str(ctx.warning)
            self.assertIn(bid, messaggio)
            self.assertIn("manca il title SEO", messaggio)
            self.assertIn(titolo, messaggio)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                self.assertEqual(copia.titolo_scheda(bando), titolo)
                self.assertEqual(copia.h1_scheda(bando), titolo)
            self.assertEqual(caught, [])
            curato = {"id": "nuova-sabatini", "titolo": "altro", "regione": "Nazionale"}
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                self.assertEqual(
                    copia.titolo_scheda(curato),
                    copia.TITOLO_SCHEDA["nuova-sabatini"],
                )
            self.assertEqual(caught, [])
            copia.TITOLO_SCHEDA[troppo] = "x" * 61
            with self.assertRaises(ValueError):
                copia.titolo_scheda({"id": troppo, "titolo": "Bando", "regione": "Toscana"})
        finally:
            copia.TITOLO_SCHEDA.pop(bid, None)
            copia.TITOLO_SCHEDA.pop(troppo, None)


class Sito(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (DIST / "bando").mkdir(parents=True, exist_ok=True)
        (DIST / "settore").mkdir(parents=True, exist_ok=True)
        (DIST / "bando" / "non-esiste.html").write_text("vecchio", encoding="utf-8")
        (DIST / "settore" / "vecchio.html").write_text("vecchio", encoding="utf-8")
        (DIST / "pagina-vecchia.html").write_text("vecchio", encoding="utf-8")
        cls.written = build.build(TODAY)

    def test_pulizia_e_idempotenza(self):
        self.assertFalse((DIST / "bando" / "non-esiste.html").exists())
        self.assertFalse((DIST / "settore" / "vecchio.html").exists())
        self.assertFalse((DIST / "pagina-vecchia.html").exists())
        prima = (DIST / "index.html").read_bytes()
        build.build(TODAY)
        self.assertEqual(prima, (DIST / "index.html").read_bytes())

    def test_seo_sitemap_robots(self):
        robots = (DIST / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Sitemap: {BASE}sitemap.xml", robots)
        self.assertNotIn("Disallow: /", robots)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [el.text for el in ET.parse(DIST / "sitemap.xml").findall("s:url/s:loc", ns)]
        for loc in (BASE, BASE + "nazionale", BASE + "toscana", BASE + "settore/startup", BASE + "settore/pmi", BASE + "sponsor", BASE + "check-up"):
            self.assertIn(loc, locs)
        self.assertNotIn(".html", "\n".join(locs))
        for loc in locs:
            rel = loc.removeprefix(BASE)
            file_rel = "index.html" if rel == "" else rel + ".html"
            self.assertTrue((DIST / file_rel).is_file(), file_rel)

    def test_verifica_search_console(self):
        path = DIST / build.GSC_FILE
        self.assertTrue(path.is_file())
        self.assertEqual(path.parent, DIST)
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "google-site-verification: googlec8d66ea588cfa987.html",
        )
        meta = (
            '<meta name="google-site-verification" '
            'content="jCzN7Fx7XoDrf8U8F0zh3SqX4j2mogdrXKI-ygMN8m4" />'
        )
        pages = [p for p in DIST.rglob("*.html") if p.name != build.GSC_FILE]
        self.assertGreater(len(pages), 10)
        for page in pages:
            head = page.read_text(encoding="utf-8").split("</head>", 1)[0]
            self.assertIn(meta, head, page.relative_to(DIST).as_posix())
        sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn("googlec8d66ea588cfa987", sitemap)
        self.assertNotIn(build.GSC_TOKEN, sitemap)
        robots = (DIST / "robots.txt").read_text(encoding="utf-8")
        self.assertEqual(robots, f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")

    def test_home_filtri_conversione_e_link(self):
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn('lang="it"', home)
        self.assertIn('id="main"', home)
        self.assertEqual(home.count("<h1"), 1)
        self.assertIn('<button type="button" class="link" id="z">Azzera filtri</button>', home)
        self.assertIn('type="search"', home)
        self.assertIn(".after(sponsor)", home)
        self.assertIn("Sponsorizzato", home)
        self.assertIn("https://fogliopef.github.io", home)
        self.assertNotIn("fogliopef.pages.dev", home)
        self.assertNotIn("fogliopef.gumroad.com", home)
        self.assertIn("https://www.linkedin.com/company/fogliopef", home)
        about = (DIST / "chi-siamo.html").read_text(encoding="utf-8")
        self.assertIn("https://fogliopef.github.io", about)
        self.assertNotIn("fogliopef.pages.dev", about)
        self.assertIn("https://www.linkedin.com/company/fogliopef", about)
        sponsor = (DIST / "sponsor.html").read_text(encoding="utf-8")
        self.assertIn("https://fogliopef.github.io", sponsor)
        self.assertIn(">fogliopef.github.io<", sponsor)
        self.assertNotIn("fogliopef.pages.dev", sponsor)
        self.assertIn("stesso titolare", home.lower())
        self.assertNotIn("link affiliato", home.lower())
        self.assertIn('href="/settore/startup"', home)
        self.assertIn('href="/nazionale"', home)
        self.assertIn("Domande frequenti", home)
        self.assertIn("MonetaryGrant", (DIST / "bando" / "smart-start-italia.html").read_text(encoding="utf-8"))
        self.assertNotIn("<script src=", home)
        for token in ("googletagmanager", "gtag(", "cookiebot", "facebook.net"):
            self.assertNotIn(token, home)

    def test_scheda_collegamenti_e_sponsor(self):
        page = (DIST / "bando" / "smart-start-italia.html").read_text(encoding="utf-8")
        self.assertIn("Bandi collegati", page)
        self.assertIn('href="/settore/startup"', page)
        self.assertIn(">Sponsorizzato<", page)
        self.assertIn('rel="noopener noreferrer"', page)
        self.assertIn("si apre in una nuova scheda", page)
        self.assertIn("Progetto dello stesso titolare", page)

    def test_prezzi_e_titolare(self):
        sponsor = (DIST / "sponsor.html").read_text(encoding="utf-8")
        for price in ("49 €", "39 €", "69 €", "79 €", "99 €"):
            self.assertIn(price, sponsor)
        self.assertIn("Prezzo di lancio: 3 posti, poi 79 €", sponsor)
        self.assertIn(f'href="mailto:{build.FPEF_EMAIL}"', sponsor)
        self.assertIn(
            "Per le sponsorizzazioni FoglioPEF (39 € al mese) e per il pacchetto entrambi i siti (69 € al mese)",
            sponsor,
        )
        foglio = sponsor.split("<h3>FoglioPEF</h3>", 1)[1].split("<h3>", 1)[0]
        entrambi = sponsor.split("<h3>Entrambi i siti</h3>", 1)[1].split("<h2>", 1)[0]
        ipt = sponsor.split("<h3>IncentiviPerTe</h3>", 1)[1].split("<h3>", 1)[0]
        self.assertNotIn(build.EMAIL, foglio)
        self.assertNotIn(build.LINKEDIN, foglio)
        self.assertNotIn("Contattaci su LinkedIn", foglio)
        self.assertIn(build.FPEF_EMAIL, foglio)
        self.assertIn(
            f'Contatto per FoglioPEF: <a class="mail" href="mailto:{build.FPEF_EMAIL}">{build.FPEF_EMAIL}</a>',
            foglio,
        )
        self.assertNotIn(build.EMAIL, entrambi)
        self.assertNotIn(build.LINKEDIN, entrambi)
        self.assertNotIn("Contattaci su LinkedIn", entrambi)
        self.assertIn(build.FPEF_EMAIL, entrambi)
        self.assertIn(
            f'Contatto per entrambi i siti: <a class="mail" href="mailto:{build.FPEF_EMAIL}">{build.FPEF_EMAIL}</a>',
            entrambi,
        )
        self.assertIn(build.EMAIL, ipt)
        self.assertNotIn(build.FPEF_EMAIL, ipt)
        self.assertNotIn(build.FPEF_EMAIL, sponsor.split("<footer>", 1)[1])
        for rel in ("privacy.html", "note-legali.html"):
            text = (DIST / rel).read_text(encoding="utf-8")
            self.assertIn("Davide Davoglio, Arezzo (Italia)", text)
        for path in DIST.rglob("*.html"):
            if path.name in ("privacy.html", "note-legali.html"):
                continue
            self.assertNotIn("Davoglio", path.read_text(encoding="utf-8"))

    def test_email_brand_consentita_e_vietata_nelle_schede(self):
        mailto = f'href="mailto:{build.EMAIL}"'
        linkedin = build.LINKEDIN
        with self.assertRaises(ValueError) as altro:
            build.validate([sample(sintesi="Scrivi a ufficio@example.com per info sul bando lungo")])
        self.assertIn("contiene un indirizzo email", str(altro.exception))
        with self.assertRaises(ValueError):
            build.validate([sample(importo=f"10.000 €, {build.EMAIL}")])
        with self.assertRaises(ValueError):
            build.reject_emails_in_cards(
                f'<article class="card"><a href="mailto:{build.EMAIL}">{build.EMAIL}</a></article>',
                "index.html",
            )
        build.reject_emails_in_cards(
            '<article class="card"><p>Scheda senza contatti</p></article>'
            f'<footer><a href="mailto:{build.EMAIL}">{build.EMAIL}</a></footer>',
            "index.html",
        )

        privacy = (DIST / "privacy.html").read_text(encoding="utf-8")
        titolare = privacy.split("<h2>Titolare del trattamento</h2>", 1)[1].split("<h2>", 1)[0]
        diritti = privacy.split("<h2>Diritti</h2>", 1)[1].split("</p>", 1)[0]
        self.assertIn("artt. 15-22", diritti)
        for fragment in (titolare, diritti):
            self.assertIn(mailto, fragment)
            self.assertIn(linkedin, fragment)
        self.assertIn("Davide Davoglio, Arezzo (Italia)", titolare)
        self.assertNotIn("Davide", diritti)

        note = (DIST / "note-legali.html").read_text(encoding="utf-8")
        titolare_note = note.split("<h2>Titolare del sito</h2>", 1)[1].split("<h2>", 1)[0]
        self.assertIn(mailto, titolare_note)
        self.assertIn(linkedin, titolare_note)
        self.assertIn("Davide Davoglio, Arezzo (Italia)", titolare_note)

        for rel in ("contatti.html", "sponsor.html"):
            text = (DIST / rel).read_text(encoding="utf-8")
            main = text.split("<footer>", 1)[0]
            self.assertIn(mailto, main)
            self.assertIn(linkedin, main)
            self.assertIn("Contattaci su LinkedIn", main)
            self.assertNotIn("Davide", main)
            self.assertNotIn("Davoglio", main)
        sponsor_main = (DIST / "sponsor.html").read_text(encoding="utf-8").split("<footer>", 1)[0]
        contatti_main = (DIST / "contatti.html").read_text(encoding="utf-8").split("<footer>", 1)[0]
        self.assertIn(f'href="mailto:{build.FPEF_EMAIL}"', sponsor_main)
        self.assertLess(sponsor_main.find(build.EMAIL), sponsor_main.find(build.FPEF_EMAIL))
        self.assertNotIn(build.FPEF_EMAIL, contatti_main)
        self.assertFalse(build.foreign_email(sponsor_main))
        self.assertTrue(build.foreign_email(sponsor_main + " segreteria@example.com"))

        home = (DIST / "index.html").read_text(encoding="utf-8")
        footer = home.split("<footer>", 1)[1]
        self.assertIn(mailto, footer)
        self.assertIn("messaggi della Pagina LinkedIn IncentiviPerTe", footer)
        self.assertNotIn("Davide", home)
        self.assertNotIn("Davoglio", home)
        cards = re.findall(r'<article class="card\b.*?</article>', home, re.S)
        self.assertGreaterEqual(len(cards), 1)
        for card in cards:
            self.assertNotIn("mailto:", card.lower())
            self.assertIsNone(build.EMAIL_RE.search(card))
        self.assertFalse(build.foreign_email(home))
        self.assertFalse(build.foreign_email(privacy))
        self.assertNotIn(build.FPEF_EMAIL, home)
        self.assertNotIn(build.FPEF_EMAIL, privacy)
        self.assertTrue(build.foreign_email(home + " segreteria@example.com"))
        self.assertFalse(build.foreign_email("Contatto " + build.FPEF_EMAIL))

        scheda = (DIST / "bando" / "smart-start-italia.html").read_text(encoding="utf-8")
        self.assertNotIn("mailto:", scheda.split("<footer>", 1)[0].lower())
        self.assertIn(mailto, scheda.split("<footer>", 1)[1])
        self.assertIn("49 €", (DIST / "sponsor.html").read_text(encoding="utf-8"))

    def test_accessibilita_e_prestazioni(self):
        css = (DIST / "style.css").read_text(encoding="utf-8")
        self.assertIn("min-height:44px", css)
        self.assertNotIn("content-visibility", css)
        self.assertNotIn("@import", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(".card[hidden]{display:none !important}", css)
        page = (DIST / "404.html").read_text(encoding="utf-8")
        self.assertIn("noindex", page)
        self.assertNotIn('rel="canonical"', page)
        self.assertIn('href="/style.css"', page)
        self.assertIn('href="/settore/startup"', page)
        self.assertIn('href="/"', page)
        self.assertNotIn(".html", page)
        self.assertIn('href="mailto:incentiviperte.team@gmail.com"', page)
        self.assertNotIn("/mailto:", page)
        self.assertIsNone(re.search(r'''\b(?:href|src)\s*=\s*["']/incentiviperte/''', page))

    def test_jsonld(self):
        for path in DIST.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            for chunk in text.split('<script type="application/ld+json">')[1:]:
                json.loads(chunk.split("</script>", 1)[0])

    def test_team_checkup_filtri_e_niente_nomi(self):
        home = (DIST / "index.html").read_text(encoding="utf-8")
        about = (DIST / "chi-siamo.html").read_text(encoding="utf-8")
        self.assertIn('value="Umbria"', home)
        self.assertIn('value="Emilia-Romagna"', home)
        self.assertIn('value="Toscana"', home)
        self.assertIn("Check-up Bandi", home)
        self.assertIn('href="/check-up">Richiedi il Check-up</a>', home)
        self.assertIn("incentivi nazionali per avviare e far crescere l'impresa", home)
        self.assertIn(
            "Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.",
            about,
        )
        toscana = (DIST / "toscana.html").read_text(encoding="utf-8")
        self.assertIn("Tutta la Toscana: bandi regionali e delle Camere di Commercio toscane", toscana)
        self.assertNotIn("Arezzo-Siena", toscana)
        umbria = (DIST / "umbria.html").read_text(encoding="utf-8")
        self.assertIn("gestiti da Gepafin e Sviluppumbria", umbria)
        self.assertIn("da Arezzo", home)
        self.assertIn("Check-up Bandi", (DIST / "contatti.html").read_text(encoding="utf-8"))
        self.assertNotIn("focus iniziale", about)
        enti = {
            "smart-start-italia.html": "MIMIT",
            "on-nuove-imprese-tasso-zero.html": "MIMIT",
            "autoimpiego-centro-nord.html": "Ministero del Lavoro",
            "resto-al-sud-2.html": "Ministero del Lavoro",
            "italia-economia-sociale.html": "MIMIT",
        }
        for name, ente in enti.items():
            page = (DIST / "bando" / name).read_text(encoding="utf-8")
            self.assertIn(f"<dd>{ente}</dd>", page)
            self.assertIn("https://www.invitalia.it/", page)
            self.assertIn(">Vai al bando ufficiale<", page)
        for path in DIST.rglob("*"):
            if not path.is_file() or path.suffix not in {".html", ".css", ".svg", ".txt", ".xml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for banned in ("Invitalia", "Sorbolini", "Frascadore", "Flavio", "Giuseppe", "Arezzo-Siena", "Myself Plus"):
                self.assertNotIn(banned, text, path.as_posix())
            visible = build.visible_text(text)
            self.assertIsNone(re.search(r"invitalia", visible, re.I), path.as_posix())

    def test_hero_uguale_alla_ricerca_predefinita(self):
        """Hero e «bandi trovati» contano solo i bandi già aperti e non scaduti."""
        home = (DIST / "index.html").read_text(encoding="utf-8")
        hero = re.search(
            r'<section class="hero">.*?<span data-aperti>(\d+) band(?:o aperto|i aperti)</span>',
            home,
            re.S,
        )
        found = re.search(
            r'<p class="count" id="n"[^>]*>(\d+) band(?:o trovato|i trovati)</p>',
            home,
        )
        self.assertIsNotNone(hero)
        self.assertIsNotNone(found)
        cards = re.findall(r'<article class="card\b.*?</article>', home, re.S)
        upcoming = []
        open_cards = []
        for card in cards:
            if 'data-scaduto="1"' in card:
                continue
            opening = re.search(r'data-apre="(\d{4}-\d{2}-\d{2})"', card)
            if opening and opening.group(1) > TODAY.isoformat():
                upcoming.append(card)
            else:
                open_cards.append(card)
        data = json.loads((ROOT / "data" / "bandi.json").read_text(encoding="utf-8"))
        prepared = build.prepare(data, TODAY)
        self.assertGreaterEqual(len(upcoming), 1)
        self.assertEqual(int(hero.group(1)), len(open_cards))
        self.assertEqual(int(found.group(1)), len(open_cards))
        self.assertEqual(len(open_cards), build.conto_aperti(prepared))
        self.assertEqual(len(open_cards), sum(1 for b in prepared if build.is_aperto(b)))
        for card in upcoming:
            self.assertIn('data-scaduto="0"', card)
            self.assertNotRegex(card[:card.find(">") + 1], r"\shidden(?:\s|>|$)")
            self.assertIn("Apre il ", card)
        for bid in ("cciaa-modena-occupazione-giovanile-2026", "eureca-er-tutti-settori-2026"):
            self.assertTrue(any(f"/bando/{bid}" in card for card in upcoming), bid)
        script = re.search(
            r"<script>\s*(\(function \(\) \{\s*var form = document\.getElementById\(\"filtri-form\"\);.*?\}\)\(\);)\s*</script>",
            home,
            re.S,
        )
        self.assertIsNotNone(script)
        self.assertIn("syncHero();", script.group(1))
        self.assertIn('getAttribute("data-apre")', script.group(1))
        runner = r"""
const fs = require("fs");
const script = fs.readFileSync(process.argv[2], "utf8");
const RealDate = Date;
function mockDate(iso) {
  const fixed = new RealDate(iso + "T12:00:00");
  function D(...args) {
    if (args.length === 0) return new RealDate(fixed.getTime());
    return new RealDate(...args);
  }
  D.prototype = RealDate.prototype;
  D.now = function () { return fixed.getTime(); };
  D.parse = RealDate.parse;
  D.UTC = RealDate.UTC;
  return D;
}
function el(attrs) {
  const node = {
    attrs: Object.assign({}, attrs),
    hidden: false,
    value: attrs.value || "",
    checked: false,
    _text: attrs.text || "",
    options: attrs.options || [],
    listeners: {}
  };
  node.getAttribute = function (name) {
    return Object.prototype.hasOwnProperty.call(node.attrs, name) ? node.attrs[name] : null;
  };
  node.addEventListener = function (type, fn) {
    (node.listeners[type] = node.listeners[type] || []).push(fn);
  };
  node.dispatch = function (type) {
    (node.listeners[type] || []).forEach(function (fn) { fn(); });
  };
  Object.defineProperty(node, "textContent", {
    get: function () { return node._text; },
    set: function (value) { node._text = String(value); }
  });
  return node;
}
function card(id, extra) {
  return el(Object.assign({
    class: "card",
    id: id,
    "data-scaduto": "0",
    "data-reg": "Toscana",
    "data-dest": "PMI",
    "data-scad": "2026-12-01",
    "data-apre": "",
    "data-search": id
  }, extra));
}
function run(iso) {
  if (iso) Date = mockDate(iso);
  else Date = RealDate;
  const area = el({ id: "r", options: [{ value: "" }, { value: "Toscana" }, { value: "Emilia-Romagna" }, { value: "Nazionale" }] });
  const dest = el({ id: "d", options: [{ value: "" }, { value: "PMI" }] });
  const scad = el({ id: "s", options: [{ value: "" }, { value: "30" }, { value: "90" }, { value: "none" }] });
  const q = el({ id: "q" });
  const expired = el({ id: "x" });
  const count = el({ id: "n", text: "0 bandi trovati" });
  const reset = el({ id: "z" });
  const form = el({ id: "filtri-form" });
  const hero = el({ "data-aperti": "", text: "0 bandi aperti" });
  const cards = [
    card("aperto"),
    card("arrivo", { "data-apre": "2026-12-02", "data-reg": "Emilia-Romagna", "data-scad": "2027-03-31" }),
    card("modena", { "data-apre": "2026-11-02", "data-reg": "Emilia-Romagna", "data-scad": "2026-11-30" }),
    card("scaduto", { "data-scaduto": "1", "data-scad": "2020-01-01" }),
    card("sportello", { "data-scad": "9999-12-31", "data-reg": "Nazionale" })
  ];
  const byId = { r: area, d: dest, s: scad, q: q, x: expired, n: count, z: reset, "filtri-form": form };
  const document = {
    getElementById: function (id) { return byId[id] || null; },
    querySelectorAll: function (sel) {
      if (sel === "#elenco .card:not(.spc)") return cards.slice();
      if (sel === ".hero [data-aperti]") return [hero];
      return [];
    },
    querySelector: function () { return null; }
  };
  const location = { search: "", pathname: "/", hash: "" };
  const history = { replaceState: function () {} };
  eval(script);
  const initial = {
    hero: hero.textContent,
    count: count.textContent,
    hidden: cards.map(function (item) { return item.hidden; })
  };
  area.value = "Emilia-Romagna";
  area.dispatch("change");
  const filtered = {
    hero: hero.textContent,
    count: count.textContent,
    hidden: cards.map(function (item) { return item.hidden; })
  };
  Date = RealDate;
  return { initial: initial, filtered: filtered };
}
const today = run("2026-10-25");
const opening = run("2026-11-02");
process.stdout.write(JSON.stringify({ today: today, opening: opening }));
"""
        script_path = DIST / "_ricerca.js"
        runner_path = DIST / "_ricerca_runner.js"
        script_path.write_text(script.group(1), encoding="utf-8")
        runner_path.write_text(runner, encoding="utf-8")
        try:
            import subprocess
            out = subprocess.run(
                ["node", str(runner_path), str(script_path)],
                check=True, capture_output=True, text=True,
            )
        finally:
            script_path.unlink(missing_ok=True)
            runner_path.unlink(missing_ok=True)
        runtime = json.loads(out.stdout)
        today = runtime["today"]
        self.assertEqual(today["initial"]["hero"], "2 bandi aperti")
        self.assertEqual(today["initial"]["count"], "2 bandi trovati")
        self.assertEqual(today["initial"]["hidden"], [False, False, False, True, False])
        self.assertEqual(today["filtered"]["hero"], "2 bandi aperti")
        self.assertEqual(today["filtered"]["count"], "0 bandi trovati")
        self.assertEqual(today["filtered"]["hidden"], [True, False, False, True, True])
        opened = runtime["opening"]
        self.assertEqual(opened["initial"]["hero"], "3 bandi aperti")
        self.assertEqual(opened["initial"]["count"], "3 bandi trovati")
        self.assertEqual(opened["filtered"]["hero"], "3 bandi aperti")
        self.assertEqual(opened["filtered"]["count"], "1 bando trovato")

    def test_bandi_20_ottobre_e_conto_alla_rovescia(self):
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn("Aggiornato il 26/10/2026", home)
        self.assertNotIn("Aggiornato il 24/10/2026", home)
        self.assertNotIn("Aggiornato il 20/10/2026", home)
        self.assertNotIn("Aggiornato il 15/10/2026", home)
        self.assertIn('getAttribute("data-scadenza")', home)
        self.assertIn('getAttribute("data-apre")', home)
        self.assertIn('data-scad="2026-10-26"', home)
        self.assertIn('data-scadenza="2026-10-26"', home)
        visible = re.sub(r"<script\b.*?</script>", "", home, flags=re.S)
        self.assertIn("Scade il 26/10/2026", visible)
        self.assertIn("Aperto fino al 26/10/2026", visible)
        self.assertNotIn("Mancano 10 giorni", visible)
        self.assertNotIn("Mancano 3 giorni", visible)
        self.assertIn('"Mancano " + left + " giorni"', home)
        self.assertNotIn("Myself Plus", home)
        smart = (DIST / "bando" / "smart-start-italia.html").read_text(encoding="utf-8")
        self.assertIn("non è previsto in Toscana, Umbria ed Emilia-Romagna", smart)
        self.assertIn("fondo perduto solo nel Mezzogiorno", smart)
        on_page = (DIST / "bando" / "on-nuove-imprese-tasso-zero.html").read_text(encoding="utf-8")
        self.assertIn("Solo finanziamento a tasso zero dal 01/07/2026", on_page)
        self.assertIn("solo un finanziamento a tasso zero", on_page)
        arezzo = (DIST / "bando" / "cciaa-arezzo-siena-certificazioni-2026.html").read_text(encoding="utf-8")
        self.assertIn("Camera di Commercio di Arezzo e Siena", arezzo)
        self.assertNotIn("Arezzo-Siena", arezzo)
        data = json.loads((ROOT / "data" / "bandi.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data), 56)
        aree = {}
        for row in data:
            aree[row["regione"]] = aree.get(row["regione"], 0) + 1
        self.assertEqual(aree, {"Nazionale": 8, "Toscana": 25, "Umbria": 6, "Emilia-Romagna": 17})
        self.assertEqual(max(row["ultimo_controllo"] for row in data), "2026-10-26")
        self.assertEqual(
            sorted(row["id"] for row in data if row["ultimo_controllo"] != "2026-10-26"),
            [
                "cciaa-arezzo-siena-export-2026-arezzo",
                "cciaa-arezzo-siena-export-2026-siena",
                "cciaa-maremma-tirreno-creazione-impresa-2026",
            ],
        )
        oggi = datetime.date(2026, 10, 24)
        prepared = build.prepare(data, oggi)
        self.assertEqual(sum(1 for b in prepared if b["scaduto"]), 0)
        self.assertEqual(sum(1 for b in prepared if b["in_arrivo"]), 2)
        self.assertEqual(sum(1 for b in prepared if build.is_aperto(b)), 54)
        toscana = [b for b in prepared if b["regione"] == "Toscana"]
        emilia = [b for b in prepared if b["regione"] == "Emilia-Romagna"]
        self.assertEqual(len(toscana), 25)
        self.assertEqual(sum(1 for b in toscana if b["scaduto"]), 0)
        self.assertEqual(sum(1 for b in emilia if b["in_arrivo"]), 2)
        self.assertEqual(sum(1 for b in prepared if b["regione"] == "Umbria"), 6)
        self.assertEqual(sum(1 for b in prepared if b["regione"] == "Nazionale"), 8)
        self.assertEqual(sum(1 for b in emilia if build.is_aperto(b)), 15)
        self.assertEqual(sum(1 for b in toscana if build.is_aperto(b)), 25)
        neve = next(b for b in prepared if b["id"] == "bando-neve-funzionamento-toscana-2026")
        self.assertFalse(neve["scaduto"])
        self.assertEqual(neve["scadenza"], "2026-11-16")
        for bid, when in (
            ("cciaa-modena-occupazione-giovanile-2026", "Apre il 02/11/2026"),
            ("eureca-er-tutti-settori-2026", "Apre il 02/12/2026"),
        ):
            page = (DIST / "bando" / f"{bid}.html").read_text(encoding="utf-8")
            self.assertIn(when, page)
            self.assertTrue(next(b for b in prepared if b["id"] == bid)["in_arrivo"])

    def test_note_fondi_data_e_importi_sulla_card(self):
        home = (DIST / "index.html").read_text(encoding="utf-8")
        cards = {}
        for card in re.findall(r'<article class="card\b.*?</article>', home, re.S):
            link = re.search(r'href="(/bando/[^"]+)"', card)
            self.assertIsNotNone(link)
            cards[link.group(1)] = card

        def note(slug):
            card = cards["/bando/" + slug]
            summary = card.split('<p class="sum">', 1)[1].split("</p>", 1)[0]
            self.assertNotIn('class="note"', summary)
            return "".join(re.findall(r'<p class="note"[^>]*>(.*?)</p>', card, re.S))

        self.assertIn("senza garanzia di copertura", note("cciaa-maremma-tirreno-agricoltura-green-2026"))
        self.assertIn("senza ulteriori risorse da assegnare", note("cciaa-maremma-tirreno-agricoltura-green-2026"))
        for slug, quando in (
            ("cciaa-maremma-tirreno-internazionalizzazione-2026", "26/10/2026"),
            ("cciaa-maremma-tirreno-imprese-vicinato-2026", "26/10/2026"),
            ("cciaa-maremma-tirreno-creazione-impresa-2026", "24/10/2026"),
            ("cciaa-maremma-tirreno-doppia-transizione-2026", "26/10/2026"),
        ):
            text = note(slug)
            self.assertIn("Risorse esaurite: nuove domande solo in lista d&#x27;attesa.", text, slug)
            self.assertIn(f"Verificato il {quando}", text, slug)
            self.assertNotIn("senza garanzia di copertura", text, slug)
        self.assertIn("18.481,60", note("cciaa-maremma-tirreno-internazionalizzazione-2026"))
        self.assertIn("0,00", note("cciaa-maremma-tirreno-imprese-vicinato-2026"))
        self.assertIn("0,00", note("cciaa-maremma-tirreno-creazione-impresa-2026"))
        poli = note("umbria-poli-innovazione-2026")
        self.assertIn("30/10/2026", poli)
        self.assertIn("30/11/2026", poli)
        self.assertIn("termine da verificare", poli)
        turismo = note("cciaa-maremma-tirreno-turismo-sostenibile-2026")
        self.assertIn("40.000", turismo)
        self.assertIn("60.000", turismo)
        self.assertIn("50.000", turismo)
        self.assertIn("48.677,68", turismo)
        self.assertNotIn("lista d&#x27;attesa", turismo)

    def test_avviso_fondi_esauriti_sulle_schede(self):
        lista = (
            "cciaa-maremma-tirreno-creazione-impresa-2026",
            "cciaa-maremma-tirreno-doppia-transizione-2026",
            "cciaa-maremma-tirreno-imprese-vicinato-2026",
            "cciaa-maremma-tirreno-internazionalizzazione-2026",
        )
        data = json.loads((ROOT / "data" / "bandi.json").read_text(encoding="utf-8"))
        prepared = build.prepare(data, datetime.date(2026, 10, 24))
        by_id = {b["id"]: b for b in prepared}
        frase = "Risorse esaurite: nuove domande solo in lista d&#x27;attesa."
        for slug in lista:
            row = by_id[slug]
            self.assertEqual(row["stato"], "lista_attesa", slug)
            self.assertFalse(row["scaduto"], slug)
            self.assertTrue(build.is_aperto(row), slug)
            page = (DIST / "bando" / f"{slug}.html").read_text(encoding="utf-8")
            scheda = page.split("<article", 1)[1].split('class="related"', 1)[0]
            self.assertIn(frase, scheda, slug)
            quando = "24/10/2026" if slug == "cciaa-maremma-tirreno-creazione-impresa-2026" else "26/10/2026"
            self.assertIn(f"Verificato il {quando}", scheda, slug)
            self.assertIn(">Fonte ufficiale<", scheda, slug)
            self.assertIn(row["fonte"], scheda, slug)
            self.assertIn('class="badge"', scheda, slug)
            self.assertNotIn('class="badge exp"', scheda, slug)
            self.assertNotIn(">Scaduto<", scheda, slug)
            self.assertIn('data-avviso="fondi"', scheda, slug)
        doppia = (DIST / "bando" / "cciaa-maremma-tirreno-doppia-transizione-2026.html").read_text(encoding="utf-8")
        self.assertIn("12:00 dell&#x27;08/07/2026", doppia)
        self.assertIn("0,00", doppia)
        vicinato = (DIST / "bando" / "cciaa-maremma-tirreno-imprese-vicinato-2026.html").read_text(encoding="utf-8")
        self.assertIn("21/10/2026", vicinato)
        self.assertNotIn("20/10/2026", vicinato)
        creazione = (DIST / "bando" / "cciaa-maremma-tirreno-creazione-impresa-2026.html").read_text(encoding="utf-8")
        self.assertIn("137.094,15", creazione)
        self.assertIn("0,00", creazione)
        internaz = (DIST / "bando" / "cciaa-maremma-tirreno-internazionalizzazione-2026.html").read_text(encoding="utf-8")
        self.assertIn("−18.481,60", internaz)
        self.assertIn("02/09/2026", internaz)
        firenze = (DIST / "bando" / "cciaa-firenze-nuove-imprese-2026.html").read_text(encoding="utf-8")
        self.assertIn("150.000", firenze)
        self.assertIn("90.000", firenze)
        self.assertIn("15:00 del 14/09/2026", firenze)
        self.assertIn("16:00 del 31/12/2026", firenze)
        self.assertIn("26/10/2026", firenze)
        self.assertIn("https://www.fi.camcom.gov.it/", firenze)
        self.assertNotIn("lista d&#x27;attesa", firenze)
        self.assertNotIn('data-avviso="fondi"', firenze)
        turismo_page = (DIST / "bando" / "cciaa-maremma-tirreno-turismo-sostenibile-2026.html").read_text(encoding="utf-8")
        self.assertIn("48.677,68", turismo_page)
        self.assertIn("60.000", turismo_page)
        self.assertIn("50.000", turismo_page)
        self.assertIn("23:59 del 10/11/2026", turismo_page)
        self.assertIn("Verificato il 26/10/2026", turismo_page)
        self.assertIn(">Fonte ufficiale<", turismo_page)
        self.assertNotIn("lista d&#x27;attesa", turismo_page)
        self.assertNotIn('data-avviso="fondi"', turismo_page)
        agri = (DIST / "bando" / "cciaa-maremma-tirreno-agricoltura-green-2026.html").read_text(encoding="utf-8")
        self.assertNotIn('data-avviso="fondi"', agri)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        for slug in lista:
            card = next(
                block for block in re.findall(r'<article class="card\b.*?</article>', home, re.S)
                if f'href="/bando/{slug}"' in block
            )
            self.assertIn('data-scaduto="0"', card, slug)
            self.assertNotIn('data-scaduto="1"', card, slug)
            self.assertIn('data-avviso="fondi"', card, slug)
            self.assertNotIn(">Scaduto<", card, slug)

    def test_dominio_pubblico_e_niente_vecchio_percorso(self):
        self.assertEqual(build.BASE, "https://incentiviperte.github.io/")
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn("https://incentiviperte.github.io/", home)
        self.assertNotIn("incentiviperte.pages.dev", home)
        self.assertIn("Sitemap: https://incentiviperte.github.io/sitemap.xml", (DIST / "robots.txt").read_text(encoding="utf-8"))
        self.assertNotIn("pages.dev", (DIST / "robots.txt").read_text(encoding="utf-8"))
        self.assertNotIn("pages.dev", (DIST / "sitemap.xml").read_text(encoding="utf-8"))
        for path in DIST.rglob("*"):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            self.assertNotIn(b"essedade.github.io", raw, path.as_posix())
            if b"fogliopef.gumroad.com" in raw:
                self.assertEqual(path.name, "check-up.html", path.as_posix())
                leftover = raw
                for url in (build.GUMROAD_CHECKUP_BASE_URL, build.GUMROAD_CHECKUP_COMPLETO_URL):
                    self.assertIn(url.encode(), raw, path.as_posix())
                    leftover = leftover.replace(url.encode(), b"")
                self.assertNotIn(b"gumroad.com", leftover.lower(), path.as_posix())
            if path.suffix.lower() not in {".html", ".css", ".svg", ".txt", ".xml"}:
                continue
            text = raw.decode("utf-8")
            self.assertIsNone(
                re.search(r'''\b(?:href|src)\s*=\s*["']/incentiviperte/''', text),
                path.as_posix(),
            )

    def test_rimando_gh_pages(self):
        import build_redirect

        n = build_redirect.generate()
        out = ROOT / "dist-redirect"
        htmls = list(DIST.rglob("*.html"))
        self.assertEqual(n, len(htmls))
        self.assertTrue((out / ".nojekyll").is_file())
        self.assertEqual((out / ".nojekyll").read_text(encoding="utf-8"), "")
        for src in htmls:
            rel = src.relative_to(DIST).as_posix()
            page = (out / rel).read_text(encoding="utf-8")
            self.assertNotIn("essedade.github.io", page, rel)
            self.assertIn('http-equiv="refresh"', page, rel)
            self.assertIn('rel="canonical"', page, rel)
            self.assertIn("location.replace(", page, rel)
            if rel == "404.html" or rel == "index.html":
                url = "https://incentiviperte.pages.dev/"
            elif rel.endswith(".html"):
                url = "https://incentiviperte.pages.dev/" + rel[: -len(".html")]
            else:
                url = "https://incentiviperte.pages.dev/" + rel
            self.assertIn(f'content="0; url={url}"', page, rel)
            self.assertIn(f'rel="canonical" href="{url}"', page, rel)
            self.assertIn(f'location.replace("{url}")', page, rel)


    def test_checkup_loghi_verde_e_url(self):
        css = (DIST / "style.css").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"#0b5cad", css, re.I))
        for color in ("#0F7A5C", "#0A5A44", "#E7F4EE", "#F4FAF7"):
            self.assertIn(color, css)
        self.assertIn("-webkit-line-clamp:2", css)
        self.assertIn("border:2px dashed #8b95a5", css)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn('alt="IncentiviPerTe"', home)
        self.assertIn("logo-header.svg", home)
        self.assertIn('height="40"', home)
        for icon in (
            "favicon.svg", "favicon-16.png", "favicon-32.png", "favicon-48.png",
            "apple-touch-icon.png", "favicon-512.png", "logo-header-80.png", "logo-header-160.png",
        ):
            self.assertIn(icon, home)
            self.assertTrue((DIST / icon).is_file(), icon)
        self.assertIn('content="#0F7A5C"', home)
        self.assertIn('class="cta" href="/check-up">Check-up</a>', home)
        self.assertNotIn("Spazi per professionisti", home)
        self.assertIn('href="/check-up">Richiedi il Check-up</a>', home)
        self.assertIn(">Sponsor</a>", home.split("<footer>", 1)[1])
        self.assertNotIn("Sponsor e pubblicità", home.split("<footer>", 1)[1])
        self.assertIn("modelli Excel per business plan, immobiliare e finanza d'impresa", home)
        self.assertIn('content="IncentiviPerTe – Bandi e incentivi per la tua impresa"', home)
        og = (DIST / "og.png").read_bytes()
        self.assertEqual(og[16:24], (1200).to_bytes(4, "big") + (630).to_bytes(4, "big"))
        visible = re.sub(r"<script\b.*?</script>", "", home, flags=re.S)
        self.assertNotIn("Mancano", visible)
        self.assertIn('data-scadenza="2026-10-26"', home)
        self.assertIn("Scade il 26/10/2026", home)
        self.assertIn("data-scadenza", home)
        self.assertIn("Mancano ", home)
        cards = re.findall(r'<article class="card\b.*?</article>', home, re.S)
        self.assertGreaterEqual(len(cards), 6)
        for card in cards:
            self.assertIn('class="cardlink"', card)
            self.assertIsNone(re.search(r'<a[^>]*class="tag"', card))
        blocks = re.findall(r'<article class="card\b.*?</article>|<aside class="card spc\b.*?</aside>', home, re.S)
        sponsor_at = next(i for i, block in enumerate(blocks) if block.startswith("<aside"))
        aperti = sum(1 for block in blocks[:sponsor_at] if 'data-scaduto="0"' in block)
        self.assertEqual(aperti, 6)
        self.assertNotIn("1 bandi", visible)
        page = (DIST / "check-up.html").read_text(encoding="utf-8")
        self.assertIn(f'rel="canonical" href="{BASE}check-up"', page)
        self.assertIn("una relazione scritta sui bandi adatti", page)
        self.assertIn(
            "Base</strong>, 49 €: report di circa 3-4 pagine, entro 5 giorni lavorativi dalla ricezione dei dati completi.",
            page,
        )
        self.assertIn("Completo</strong>, 79 €: report di 6-10 pagine, entro 7-10 giorni lavorativi", page)
        self.assertIn("Livelli del servizio", page)
        for item in build.CHECKUP_EXTRA:
            self.assertIn(item, page)
        self.assertIn('id="checkup-fallback"', page)
        self.assertIn('id="checkup-text"', page)
        self.assertIn('id="checkup-copy">Copia<', page)
        self.assertIn("Se non si apre un'app di posta", page)
        self.assertIn("team di esperti professionisti con esperienza pluriennale", page)
        self.assertIn(">Invia richiesta<", page)
        self.assertIn("Regione (comprende la provincia)", page)
        self.assertIn("Tipo di impresa", page)
        self.assertIn(">Stadio<", page)
        self.assertIn("Importo indicativo", page)
        self.assertIn('name="livello" value="Base"', page)
        self.assertIn('name="livello" value="Completo"', page)
        self.assertIn("mailto:incentiviperte.team@gmail.com", page)
        self.assertNotIn('href="/contatti">Richiedi il Check-up', page)
        raw = page.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
        data = json.loads(raw)
        services = [node for node in data["@graph"] if node["@type"] == "Service"]
        self.assertEqual(len(services), 1)
        offers = {item["name"]: item for item in services[0]["offers"]}
        self.assertEqual(offers["Base"]["price"], "49")
        self.assertEqual(offers["Completo"]["price"], "79")
        self.assertIn("entro 5 giorni lavorativi", offers["Base"]["description"])
        self.assertIn("3-4 pagine", offers["Base"]["description"])
        self.assertIn(build.CHECKUP_BASE, offers["Base"]["description"])
        self.assertIn("entro 7-10 giorni lavorativi", offers["Completo"]["description"])
        self.assertIn("6-10 pagine", offers["Completo"]["description"])
        self.assertIn(build.CHECKUP_COMPLETO, offers["Completo"]["description"])
        for item in build.CHECKUP_EXTRA:
            self.assertIn(item, offers["Completo"]["description"])
        self.assertEqual(services[0]["url"], BASE + "check-up")
        privacy = (DIST / "privacy.html").read_text(encoding="utf-8")
        cookie = (DIST / "cookie.html").read_text(encoding="utf-8")
        for text in (privacy, cookie):
            self.assertIn("Cloudflare Pages (Cloudflare, Inc.)", text)
            self.assertIn("https://www.cloudflare.com/privacypolicy/", text)
        self.assertNotIn("GitHub", cookie)
        sponsor = (DIST / "sponsor.html").read_text(encoding="utf-8")
        self.assertIn("fogliopef.team@gmail.com", sponsor)
        self.assertNotIn("foglioPEF.team", sponsor)
        self.assertIn("Domande? Scrivici a", sponsor)
        self.assertIn("o in un messaggio alla", sponsor)
        self.assertIn("nostra pagina LinkedIn", sponsor)
        self.assertNotIn("Scrivi a messaggi della", sponsor)
        donne = (DIST / "settore" / "donne.html").read_text(encoding="utf-8")
        self.assertIn("6 bandi aperti", donne)
        self.assertNotIn("1 bandi", donne)
        for path in DIST.rglob("*.html"):
            if path.name == build.GSC_FILE:
                continue
            text = path.read_text(encoding="utf-8")
            title = re.search(r"<title>(.*?)</title>", text).group(1)
            desc = re.search(r'<meta name="description" content="([^"]*)"', text).group(1)
            self.assertNotRegex(title + " " + desc, r"\d+ bandi aperti")
            self.assertIsNone(re.search(r'''(?:href|src)="(?!https?:|mailto:)[^"]*\.html''', text), path.name)

    def test_checkup_codice_lancio_e_rimando(self):
        page = (DIST / "check-up.html").read_text(encoding="utf-8")
        self.assertIn("49 €", page)
        self.assertIn("79 €", page)
        self.assertIn("LANCIO15", page)
        self.assertIn(build.CHECKUP_LANCIO, page)
        self.assertIn("30/10/2026", page)
        self.assertNotIn("15% di sconto", page)
        self.assertNotIn("Invitalia", page)
        self.assertIsNone(re.search(r"invitalia", build.visible_text(page), re.I))
        self.assertIn('rel="canonical" href="https://incentiviperte.github.io/check-up"', page)
        self.assertIn('property="og:url" content="https://incentiviperte.github.io/check-up"', page)
        self.assertIn(
            'mailto:incentiviperte.team@gmail.com?subject=" + encodeURIComponent("Richiesta Check-up Bandi")',
            page,
        )
        alias = (DIST / "check-up-bandi.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="refresh" content="0; url=/check-up"', alias)
        self.assertIn('href="/check-up">Vai al Check-up</a>', alias)
        self.assertIn('rel="canonical" href="https://incentiviperte.github.io/check-up"', alias)
        self.assertIn('property="og:url" content="https://incentiviperte.github.io/check-up"', alias)
        self.assertNotIn("Invitalia", alias)
        self.assertNotIn("LANCIO15", alias)
        sitemap = (DIST / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("<loc>https://incentiviperte.github.io/check-up</loc>", sitemap)
        self.assertNotIn("check-up-bandi", sitemap)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("/check-up-bandi", home)
        self.assertIn('href="/check-up">Richiedi il Check-up</a>', home)
        nav = home.split('<nav class="dnav"', 1)[1].split("</nav>", 1)[0]
        self.assertIn('href="/check-up">Check-up</a>', nav)
        self.assertNotIn("check-up-bandi", nav)
        self.assertEqual(nav.count('href="/check-up"'), 1)
        footer = home.split("<footer>", 1)[1]
        self.assertNotIn("check-up-bandi", footer)
        self.assertNotIn('href="/check-up"', footer)

    def test_pagamento_checkup_e_riquadro_bando(self):
        page = (DIST / "check-up.html").read_text(encoding="utf-8")
        self.assertIn('rel="canonical" href="https://incentiviperte.github.io/check-up"', page)
        self.assertIn('property="og:url" content="https://incentiviperte.github.io/check-up"', page)
        self.assertNotIn("pages.dev", page)
        self.assertNotIn("essedade.github.io", page)
        self.assertIn("Il Check-up è una verifica di ammissibilità e non garantisce l'ottenimento del contributo.", page)
        self.assertIn("l'IBAN non è pubblicato sul sito", page)
        self.assertIn("Dopo la richiesta lo inviamo per email da", page)
        self.assertIn("incentiviperte.team@gmail.com", page)
        self.assertIsNone(re.search(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", page))
        self.assertIsNone(re.search(r"\b[A-Z]{2}\d{2}(?:\s[A-Z0-9]{4}){3,8}\b", page))
        self.assertIn('<p class="code">LANCIO15</p>', page)
        self.assertIn(build.CHECKUP_LANCIO, page)
        self.assertIn(">Invia richiesta<", page)
        self.assertEqual(build.GUMROAD_CHECKUP_BASE_URL, "https://fogliopef.gumroad.com/l/checkup-bandi-base")
        self.assertEqual(build.GUMROAD_CHECKUP_COMPLETO_URL, "https://fogliopef.gumroad.com/l/checkup-bandi-completo")
        self.assertEqual(build.CHECKUP_PRODUCT_BASE, "IncentiviPerTe – Check-up Bandi Base")
        self.assertEqual(build.CHECKUP_PRODUCT_COMPLETO, "IncentiviPerTe – Check-up Bandi Completo")
        paga = page.split('id="paga-ora"', 1)[1].split("</section>", 1)[0]
        self.assertIn("Paga ora", paga)
        self.assertIn("IncentiviPerTe – Check-up Bandi Base", paga)
        self.assertIn("IncentiviPerTe – Check-up Bandi Completo", paga)
        base = paga.split("IncentiviPerTe – Check-up Bandi Base", 1)[1].split("IncentiviPerTe – Check-up Bandi Completo", 1)[0]
        completo = paga.split("IncentiviPerTe – Check-up Bandi Completo", 1)[1]
        self.assertIn("49 €", base)
        self.assertIn("79 €", completo)
        self.assertIn('href="https://fogliopef.gumroad.com/l/checkup-bandi-base"', base)
        self.assertIn('href="https://fogliopef.gumroad.com/l/checkup-bandi-completo"', completo)
        self.assertEqual(paga.count("Pagamento sicuro con carta tramite Gumroad"), 2)
        self.assertEqual(paga.count(">Bonifico istantaneo<"), 2)
        for subject in (
            "Richiesta Check-up Base – pagamento con bonifico istantaneo",
            "Richiesta Check-up Completo – pagamento con bonifico istantaneo",
        ):
            self.assertIn(urllib.parse.quote(subject), page)
        self.assertIn(
            'mailto:incentiviperte.team@gmail.com?subject=" + encodeURIComponent("Richiesta Check-up Bandi")',
            page,
        )
        for banned in ("Sorbolini", "Frascadore", "Invitalia"):
            self.assertNotIn(banned, page)
        bandi = sorted((DIST / "bando").glob("*.html"))
        self.assertGreaterEqual(len(bandi), 56)
        phrase = "Documenti da preparare, calendario ed errori da evitare per questo bando"
        for path in bandi:
            text = path.read_text(encoding="utf-8")
            self.assertIn('class="bando-checkup"', text, path.name)
            box = text.split('class="bando-checkup"', 1)[1].split("</aside>", 1)[0]
            self.assertIn(phrase, box, path.name)
            self.assertIn("(da 49 €)", box, path.name)
            self.assertIn(build.CHECKUP_IVA_NOTE, box, path.name)
            self.assertIn("Verifica di ammissibilità, non garantisce il contributo.", box, path.name)
            self.assertIn('href="/check-up"', box, path.name)
            self.assertIn(f'rel="canonical" href="https://incentiviperte.github.io/bando/{path.stem}"', text, path.name)
            self.assertNotIn("pages.dev", text, path.name)
            self.assertNotIn("essedade.github.io", text, path.name)
            self.assertIsNone(re.search(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", text), path.name)
        self.assertNotIn('class="bando-checkup"', (DIST / "index.html").read_text(encoding="utf-8"))

    def test_prezzi_finali_senza_piu_iva(self):
        """I prezzi indicati sono finali: niente «+ IVA» su Check-up e sponsor."""
        page = (DIST / "check-up.html").read_text(encoding="utf-8")
        main = page.split('<main id="main"', 1)[1].split("</main>", 1)[0]
        self.assertEqual(main.count(build.CHECKUP_IVA_NOTE), 2)
        livelli = main.split("<h2>Livelli del servizio</h2>", 1)[1].split('<aside class="promo"', 1)[0]
        self.assertIn(build.CHECKUP_IVA_NOTE, livelli)
        self.assertIn("Base</strong>, 49 €:", livelli)
        self.assertIn("Completo</strong>, 79 €:", livelli)
        self.assertIn("Base · 49 €", main)
        self.assertIn("Completo · 79 €", main)
        paga = main.split('id="paga-ora"', 1)[1].split("</section>", 1)[0]
        self.assertIn(build.CHECKUP_IVA_NOTE, paga)
        self.assertIn(build.CHECKUP_LANCIO, main.split('id="paga-ora"', 1)[0])
        self.assertIn("41,65 €", main)
        self.assertIn("67,15 €", main)
        self.assertNotIn("+ IVA", main)
        choices = re.findall(r'<div class="pay-choice">(.*?)</div>', paga, re.S)
        self.assertEqual(len(choices), 4)
        card_amounts = []
        wire_amounts = []
        for chunk in choices:
            amount = re.search(r'class="pay-amt">(.*?)</span>', chunk).group(1)
            if "gumroad.com" in chunk:
                card_amounts.append(amount)
                self.assertIn(amount, ("49 €", "79 €"))
            else:
                wire_amounts.append(amount)
                self.assertIn(">Bonifico istantaneo<", chunk)
                self.assertTrue(amount.endswith("(prezzo finale, nessuna IVA aggiunta)"), amount)
        self.assertEqual(card_amounts, ["49 €", "79 €"])
        self.assertEqual(
            wire_amounts,
            [
                "49 € (prezzo finale, nessuna IVA aggiunta)",
                "79 € (prezzo finale, nessuna IVA aggiunta)",
            ],
        )
        hrefs = []
        for chunk in choices:
            if "gumroad.com" in chunk:
                continue
            hrefs.extend(re.findall(r'href="(mailto:[^"]+)"', chunk))
        self.assertEqual(len(hrefs), 2)
        for href in hrefs:
            parsed = urllib.parse.urlparse(html.unescape(href))
            query = urllib.parse.parse_qs(parsed.query)
            subject = query["subject"][0]
            body = query["body"][0]
            self.assertNotIn("+ IVA", subject)
            self.assertNotIn("+ IVA", body)
            self.assertNotIn("prestazione occasionale", subject + body)
            self.assertNotIn("forfettario", subject + body)
            self.assertRegex(body, r"Importo: (?:49|79) €\n")
        desc = re.search(r'<meta name="description" content="([^"]*)"', page).group(1)
        self.assertIn(build.CHECKUP_IVA_NOTE, html.unescape(desc))
        self.assertNotIn("+ IVA", html.unescape(desc))
        raw = page.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
        data = json.loads(raw)
        service = next(node for node in data["@graph"] if node["@type"] == "Service")
        self.assertIn(build.CHECKUP_IVA_NOTE, service["description"])
        self.assertNotIn("+ IVA", service["description"])
        for offer in service["offers"]:
            self.assertIn(build.CHECKUP_IVA_NOTE, offer["description"])
            self.assertNotIn("+ IVA", offer["description"])
            self.assertNotIn("+", offer["price"])
        for path in (DIST / "bando").glob("*.html"):
            box = path.read_text(encoding="utf-8").split('class="bando-checkup"', 1)[1].split("</aside>", 1)[0]
            self.assertIn("da 49 €", box, path.name)
            self.assertNotIn("+ IVA", box, path.name)
            self.assertIn(build.CHECKUP_IVA_NOTE, box, path.name)
        sponsor = re.sub(r"<[^>]+>", "", (DIST / "sponsor.html").read_text(encoding="utf-8"))
        for price in ("49 € al mese", "39 € al mese", "69 € al mese", "79 € al mese", "99 € al mese"):
            self.assertIn(price, sponsor)
        self.assertNotIn("+ IVA", sponsor)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn("da 49 € al mese", home)
        self.assertNotIn("+ IVA", home)
        for path in DIST.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            if 'class="spp"' in text:
                self.assertIn(build.SPONSOR_DA, text, path.as_posix())
        self.assertNotIn("24 €", page)
        self.assertNotIn("24 €", sponsor)

    def test_niente_piu_iva_prestazione_o_forfettario(self):
        banned = ("+ IVA", "prestazione occasionale", "forfettario")
        seen = 0
        for path in DIST.rglob("*"):
            if path.suffix.lower() not in {".html", ".css", ".xml", ".txt", ".svg"}:
                continue
            text = path.read_text(encoding="utf-8")
            seen += 1
            for phrase in banned:
                self.assertNotIn(phrase, text, path.as_posix())
        self.assertGreater(seen, 10)
        source = (ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
        for phrase in banned:
            self.assertNotIn(phrase, source)

    def test_privacy_cita_github(self):
        privacy = (DIST / "privacy.html").read_text(encoding="utf-8")
        self.assertIn("GitHub", privacy)

    def test_marchio_proposta_a(self):
        """Header e favicon di ogni pagina usano i file del marchio A."""
        import hashlib
        import struct

        icons = (
            '<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">',
            '<link rel="icon" href="{pre}favicon-48.png" type="image/png" sizes="48x48">',
            '<link rel="icon" href="{pre}favicon-32.png" type="image/png" sizes="32x32">',
            '<link rel="icon" href="{pre}favicon-16.png" type="image/png" sizes="16x16">',
            '<link rel="apple-touch-icon" href="{pre}apple-touch-icon.png" sizes="180x180">',
            '<link rel="icon" href="{pre}favicon-512.png" type="image/png" sizes="512x512">',
        )
        brand = (
            '<source srcset="{pre}logo-header.svg" type="image/svg+xml">'
            '<img src="{pre}logo-header-80.png" '
            'srcset="{pre}logo-header-80.png 1x, {pre}logo-header-160.png 2x" '
            'alt="IncentiviPerTe" width="222" height="40">'
        )
        expected = {
            "logo-header.svg": "03b6e4bd4d7e735e879336b4f07a37184aea5d44aaf82b512f8537237d88d6ab",
            "logo-header-80.png": "42948c7882d290a3771e3363fef57701604ff210dafca67566913a439161399c",
            "logo-header-160.png": "8b03bc1a8819f7a35d3d720f86da14210f05962a43552755c3a686c551e8f552",
            "favicon.svg": "d37b06dcfbea1e81dc4a8eaa6969a838b84fdf84cd56ae0b3df3fe95d3b400ec",
            "favicon-16.png": "1837cf049ee26e751edf483a1e7af468c5075c3ef45880050d927074d5a5aa97",
            "favicon-32.png": "127cc7557248100729280db89fa8ccfb7d2d673b6810010ed7f769c0c5e3c443",
            "favicon-48.png": "a051afe7f8777ddd263284fd476e365612a39e886d758e3d545cd3a37ea7177f",
            "apple-touch-icon.png": "61990e384527a791c0ba0972a9cd0686d90d29f78c7de986ba42801dbb23a70b",
            "favicon-512.png": "ee6ae2045cd043586d72c742cb4f3a1af9827a08924fb9e4d9a402c262dd429c",
            "og.png": "2f5f77e70348259d0a5413d07755fc1aff0bf925588bbd7d69044575331b783e",
        }
        sizes = {
            "favicon-16.png": (16, 16),
            "favicon-32.png": (32, 32),
            "favicon-48.png": (48, 48),
            "apple-touch-icon.png": (180, 180),
            "favicon-512.png": (512, 512),
            "logo-header-80.png": (445, 80),
            "logo-header-160.png": (889, 160),
            "og.png": (1200, 630),
        }
        for name, digest in expected.items():
            data = (DIST / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest, name)
            self.assertEqual((ROOT / "assets" / name).read_bytes(), data, name)
            if name in sizes:
                self.assertEqual(struct.unpack(">II", data[16:24]), sizes[name], name)
        header = (DIST / "logo-header.svg").read_text(encoding="utf-8")
        self.assertIn("#0F7A5C", header)
        self.assertIn("#14213D", header)
        pages = [p for p in DIST.rglob("*.html") if p.name != build.GSC_FILE]
        self.assertGreater(len(pages), 10)
        for path in pages:
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(DIST).as_posix()
            # La 404 è servita da qualunque percorso: gli asset partono dalla radice.
            pre = "/" if rel == "404.html" else "../" * rel.count("/")
            for icon in icons:
                self.assertIn(icon.format(pre=pre), text, rel)
            self.assertIn(brand.format(pre=pre), text, rel)
            self.assertIn(f'property="og:image" content="{BASE}og.png"', text, rel)
            self.assertIn(f'name="twitter:image" content="{BASE}og.png"', text, rel)
            self.assertNotIn("pages.dev", text, rel)

    def test_descrizione_fogliopef_e_mailto_sponsor(self):
        old = "FoglioPEF è un foglio Excel"
        boxed = 0
        for path in DIST.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(old, text, path.as_posix())
            self.assertNotIn("Numeri in ordine per un investimento immobiliare", text, path.as_posix())
            if 'class="fpef"' in text:
                boxed += 1
                box = text.split('class="fpef"', 1)[1].split("</aside>", 1)[0]
                self.assertIn("<h2>FoglioPEF</h2>", box, path.as_posix())
                self.assertNotIn("Numeri in ordine per un investimento immobiliare", box, path.as_posix())
                self.assertIn(build.FPEF_DESC, box, path.as_posix())
                footer = text.split("<footer>", 1)[1]
                self.assertIn(build.FPEF_DESC.split(": ", 1)[1], footer, path.as_posix())
        self.assertGreaterEqual(boxed, 1)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        about = (DIST / "chi-siamo.html").read_text(encoding="utf-8")
        self.assertIn('class="fpef"', home)
        self.assertIn('class="fpef"', about)
        for name in ("nazionale.html", "toscana.html", "umbria.html", "emilia-romagna.html"):
            self.assertIn('class="fpef"', (DIST / name).read_text(encoding="utf-8"))
        sponsor = (DIST / "sponsor.html").read_text(encoding="utf-8")
        for title, end in (("FoglioPEF", "<h3>"), ("Entrambi i siti", "<h2>")):
            chunk = sponsor.split(f"<h3>{title}</h3>", 1)[1].split(end, 1)[0]
            self.assertIn(f'<a class="btn" href="mailto:{build.FPEF_EMAIL}">Scrivi a FoglioPEF</a>', chunk)
            self.assertNotIn(f'<a class="btn" href="mailto:{build.EMAIL}">', chunk)
            self.assertNotIn(build.EMAIL, chunk)
            self.assertNotIn("Contattaci su LinkedIn", chunk)
            self.assertNotIn(build.LINKEDIN, chunk)
        ipt = sponsor.split("<h3>IncentiviPerTe</h3>", 1)[1].split("<h3>", 1)[0]
        self.assertIn(f'<a class="btn" href="mailto:{build.EMAIL}">Scrivi a IncentiviPerTe</a>', ipt)
        self.assertNotIn(f'<a class="btn" href="mailto:{build.FPEF_EMAIL}">', ipt)

    def test_scaduti_fra_un_build_e_laltro(self):
        pages = [
            DIST / "index.html",
            DIST / "toscana.html",
            DIST / "settore" / "pmi.html",
        ]
        for path in pages:
            text = path.read_text(encoding="utf-8")
            self.assertIn("<span data-aperti>", text, path.name)
            self.assertIn('open === 1 ? "1 bando aperto"', text, path.name)
            self.assertIn('open + " bandi aperti"', text, path.name)
            self.assertIn("list.appendChild", text, path.name)
            self.assertIn('node.textContent = "Scaduto il "', text, path.name)
        scheda = (DIST / "bando" / "cciaa-tno-doppia-transizione-2-2026.html").read_text(encoding="utf-8")
        visible = re.sub(r"<script\b.*?</script>", "", scheda, flags=re.S)
        self.assertIn("Aperto fino al 26/10/2026", visible)
        self.assertIn(">Scade il 26/10/2026<", visible)
        self.assertNotIn(">Scaduto il 26/10/2026<", visible)
        self.assertIn('data-deadline="2026-10-26"', scheda)
        self.assertIn('data-scadenza="2026-10-26"', scheda)
        script = re.search(r"<script>\s*(\(function \(\) \{.*?startOfToday.*?\}\)\(\);)\s*</script>", scheda, re.S)
        self.assertIsNotNone(script)
        runner = r"""
const fs = require("fs");
const script = fs.readFileSync(process.argv[2], "utf8");
function has(node, cls) {
  return (" " + ((node.attrs && node.attrs.class) || "") + " ").indexOf(" " + cls + " ") >= 0;
}
function match(node, sel) {
  if (!node || !node.attrs) return false;
  if (sel === ".badge[data-scadenza]") return has(node, "badge") && node.getAttribute("data-scadenza");
  if (sel === "[data-deadline]") return !!node.getAttribute("data-deadline");
  if (sel === "[data-aperti]") return node.getAttribute("data-aperti") !== null;
  if (sel === "article.card") return node.tag === "article" && has(node, "card");
  if (sel === "article") return node.tag === "article";
  return false;
}
function walk(node, fn) {
  fn(node);
  (node.children || []).forEach(function (child) { walk(child, fn); });
}
function h(tag, attrs, text) {
  const node = { tag: tag, attrs: Object.assign({}, attrs), children: [], parent: null, _text: text || "" };
  node.getAttribute = function (name) {
    return Object.prototype.hasOwnProperty.call(node.attrs, name) ? node.attrs[name] : null;
  };
  node.setAttribute = function (name, value) { node.attrs[name] = String(value); };
  node.classList = {
    add: function () {
      const set = (node.attrs.class || "").split(/\s+/).filter(Boolean);
      for (let i = 0; i < arguments.length; i++) if (set.indexOf(arguments[i]) < 0) set.push(arguments[i]);
      node.attrs.class = set.join(" ");
    },
    remove: function () {
      const drop = Array.prototype.slice.call(arguments);
      node.attrs.class = (node.attrs.class || "").split(/\s+/).filter(function (c) {
        return c && drop.indexOf(c) < 0;
      }).join(" ");
    }
  };
  Object.defineProperty(node, "textContent", {
    get: function () { return node._text; },
    set: function (value) { node._text = String(value); }
  });
  node.appendChild = function (child) {
    if (child.parent) {
      const i = child.parent.children.indexOf(child);
      if (i >= 0) child.parent.children.splice(i, 1);
    }
    child.parent = node;
    node.children.push(child);
  };
  node.querySelectorAll = function (sel) {
    const parts = sel.split(",");
    const out = [];
    walk(node, function (n) {
      if (n === node) return;
      for (let i = 0; i < parts.length; i++) if (match(n, parts[i].trim())) { out.push(n); return; }
    });
    return out;
  };
  node.closest = function (sel) {
    let cur = node;
    while (cur) {
      if (match(cur, sel)) return cur;
      cur = cur.parent;
    }
    return null;
  };
  return node;
}
function mount(children) {
  const document = h("document", {}, "");
  children.forEach(function (child) { document.appendChild(child); });
  document.getElementById = function (id) {
    let found = null;
    walk(document, function (n) { if (n.attrs && n.attrs.id === id) found = n; });
    return found;
  };
  var window = { INCENTIVI_OGGI: "2026-10-20T12:00:00" };
  eval(script);
  return document;
}
function card(id, iso, openText) {
  const article = h("article", { class: "card", id: id, "data-scaduto": "0" }, "");
  article.appendChild(h("span", { class: "badge", "data-scadenza": iso }, openText));
  article.appendChild(h("span", { class: "dl", "data-deadline": iso }, "Aperto fino al " + iso));
  return article;
}
function run(cards) {
  const count = h("span", { "data-aperti": "" }, "99 bandi aperti");
  const list = h("div", { id: "elenco" }, "");
  cards.forEach(function (item) { list.appendChild(item); });
  list.appendChild(h("aside", { class: "card spc", id: "sponsor" }, ""));
  const document = mount([count, list]);
  return {
    label: count.textContent,
    order: list.children.map(function (child) { return child.attrs.id; }),
    cards: cards.map(function (item) {
      return {
        id: item.attrs.id,
        scaduto: item.getAttribute("data-scaduto"),
        badge: item.children[0].textContent,
        cls: item.children[0].attrs.class,
        dl: item.children[1].textContent
      };
    })
  };
}
const one = run([card("vecchio", "2020-01-01", "Scade il 01/01/2020"), card("aperto", "2026-12-01", "Scade il 01/12/2026")]);
const two = run([card("a", "2026-12-01", "Scade il 01/12/2026"), card("b", "2026-12-15", "Scade il 15/12/2026")]);
const zero = run([card("a", "2020-01-01", "Scade il 01/01/2020"), card("b", "2020-02-01", "Scade il 01/02/2020")]);
const detailBadge = h("span", { class: "badge", "data-scadenza": "2020-01-01" }, "Scade il 01/01/2020");
const detailWhen = h("strong", { "data-deadline": "2020-01-01" }, "Aperto fino al 01/01/2020");
const article = h("article", { class: "box" }, "");
article.appendChild(detailBadge);
article.appendChild(detailWhen);
mount([article]);
process.stdout.write(JSON.stringify({
  one: one,
  two: two.label,
  zero: zero.label,
  detail: { badge: detailBadge.textContent, cls: detailBadge.attrs.class, when: detailWhen.textContent }
}));
"""
        script_path = DIST / "_scadenze.js"
        runner_path = DIST / "_scadenze_runner.js"
        script_path.write_text(script.group(1), encoding="utf-8")
        runner_path.write_text(runner, encoding="utf-8")
        try:
            import subprocess
            out = subprocess.run(
                ["node", str(runner_path), str(script_path)],
                check=True, capture_output=True, text=True,
            )
        finally:
            script_path.unlink(missing_ok=True)
            runner_path.unlink(missing_ok=True)
        data = json.loads(out.stdout)
        self.assertEqual(data["one"]["label"], "1 bando aperto")
        self.assertEqual(data["one"]["order"], ["aperto", "sponsor", "vecchio"])
        vecchio = data["one"]["cards"][0]
        aperto = data["one"]["cards"][1]
        self.assertEqual(vecchio["badge"], "Scaduto")
        self.assertEqual(vecchio["scaduto"], "1")
        self.assertIn("exp", vecchio["cls"].split())
        self.assertEqual(vecchio["dl"], "Scaduto il 01/01/2020")
        self.assertEqual(aperto["badge"], "Mancano 42 giorni")
        self.assertEqual(aperto["scaduto"], "0")
        self.assertEqual(aperto["dl"], "Aperto fino al 2026-12-01")
        self.assertEqual(data["two"], "2 bandi aperti")
        self.assertEqual(data["zero"], "0 bandi aperti")
        self.assertEqual(data["detail"]["badge"], "Scaduto")
        self.assertIn("exp", data["detail"]["cls"].split())
        self.assertEqual(data["detail"]["when"], "Scaduto il 01/01/2020")

    def test_importo_non_allarga_la_griglia(self):
        css = (DIST / "style.css").read_text(encoding="utf-8")
        amt = css.split(".amt{", 1)[1].split("}", 1)[0]
        card = css.split(".card{", 1)[1].split("}", 1)[0]
        grids = re.findall(r"\.grid\{([^}]*)\}", css)
        contained = "min-width:0" in card and all("minmax(0,1fr)" in rule for rule in grids)
        if "nowrap" in amt and not contained:
            self.fail(".amt ha white-space:nowrap senza contenimento della griglia")
        self.assertNotIn("nowrap", amt)
        self.assertNotIn("text-overflow", amt)
        self.assertIn("overflow-wrap:anywhere", amt)
        self.assertIn("min-width:0", card)
        self.assertGreaterEqual(len(grids), 3)
        for rule in grids:
            self.assertIn("minmax(0,1fr)", rule)
            self.assertNotIn("grid-template-columns:1fr", rule)
            self.assertNotRegex(rule, r"repeat\(\d+,1fr\)")

    def test_revisione_ux_pulsanti(self):
        css = (DIST / "style.css").read_text(encoding="utf-8")
        self.assertIn(
            "@media(min-width:1180px){.dnav{display:flex;flex:1;min-width:0}details.menu{display:none}a.btn.head-cta{display:none}}",
            css,
        )
        btn = css.split(".btn{", 1)[1].split("}", 1)[0]
        self.assertIn("font:inherit", btn)
        self.assertIn("border:0", btn)
        self.assertIn("cursor:pointer", btn)
        self.assertIn(".btn.outline{background:transparent;color:var(--b);border:2px solid var(--b)}", css)
        self.assertIn(".card .tag{background:#E7F4EE;border:0;color:var(--bd)}", css)
        self.assertIn("white-space:nowrap", css)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        aside = re.search(r'<aside class="card spc".*?</aside>', home, re.S).group(0)
        self.assertIn(">Scopri gli spazi sponsor<", aside)
        self.assertIn('class="btn outline"', aside)
        self.assertNotIn('class="btn"', aside.replace('class="btn outline"', ""))
        self.assertRegex(home, r'class="btn outline"[^>]*>Apri FoglioPEF')
        sponsor = (DIST / "sponsor.html").read_text(encoding="utf-8")
        self.assertRegex(sponsor, r'class="btn outline"[^>]*>Contattaci su LinkedIn')
        scheda = (DIST / "bando" / "smart-start-italia.html").read_text(encoding="utf-8")
        self.assertRegex(scheda, r'class="btn"[^>]*>Vai al bando ufficiale<span')
        self.assertIn('class="host">', scheda)
        self.assertNotIn("Vai al bando ufficiale su ", scheda)
        self.assertLess(scheda.find("Vai al bando ufficiale"), scheda.find('class="checkup-ask"'))
        self.assertIn('class="checkup-ask"', scheda)
        self.assertIn('href="/check-up"', scheda.split('class="checkup-ask"', 1)[1].split("</aside>", 1)[0])
        self.assertIn(">Scopri gli spazi sponsor<", scheda)
        for path in (DIST / "bando").glob("*.html"):
            text = path.read_text(encoding="utf-8")
            self.assertIn(">Vai al bando ufficiale<", text, path.name)
            self.assertNotIn("Vai al bando ufficiale su ", text, path.name)
            self.assertIn('class="host">', text, path.name)
            self.assertIn('class="checkup-ask"', text, path.name)

    def test_invitalia_assente_dal_testo_visibile(self):
        nazionali = (
            "smart-start-italia.html",
            "on-nuove-imprese-tasso-zero.html",
            "autoimpiego-centro-nord.html",
            "resto-al-sud-2.html",
            "italia-economia-sociale.html",
        )
        for name in nazionali:
            page = (DIST / "bando" / name).read_text(encoding="utf-8")
            self.assertIn("https://www.invitalia.it/", page, name)
            self.assertIn("sito ufficiale dell'ente gestore", page, name)
            self.assertIsNone(re.search(r"invitalia", build.visible_text(page), re.I), name)
        for path in DIST.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            visible = build.visible_text(text)
            self.assertIsNone(
                re.search(r"invitalia", visible, re.I),
                path.as_posix(),
            )
        sample = (
            '<a href="https://www.invitalia.it/bando">Vai al bando ufficiale</a>'
            '<small class="host">invitalia.it</small>'
            '<script type="application/ld+json">{"url":"https://www.invitalia.it/bando"}</script>'
        )
        self.assertIsNotNone(re.search(r"invitalia", build.visible_text(sample), re.I))


    def test_illustrazioni(self):
        """Ogni img ha alt non vuoto e dimensioni; gli hero non sono lazy."""
        img_re = re.compile(r"<img\b[^>]*>", re.I)
        pages = [p for p in DIST.rglob("*.html") if p.name != build.GSC_FILE]
        seen = 0
        for path in pages:
            text = path.read_text(encoding="utf-8")
            for tag in img_re.findall(text):
                seen += 1
                alt = re.search(r'\balt="([^"]*)"', tag)
                self.assertIsNotNone(alt, (path.name, tag))
                self.assertTrue(html.unescape(alt.group(1)).strip(), (path.name, tag))
                self.assertRegex(tag, r'\bwidth="[1-9]\d*"', tag)
                self.assertRegex(tag, r'\bheight="[1-9]\d*"', tag)
        self.assertGreater(seen, len(pages))
        css = (DIST / "style.css").read_text(encoding="utf-8")
        self.assertIn(".hero-img,.sec-img{display:block;max-width:100%;height:auto}", css)
        self.assertIn(".sec-img{border-radius:14px;margin:12px 0}", css)
        for name in build.ILLUSTRAZIONI:
            src = ROOT / "assets" / "img" / name
            dst = DIST / "assets" / "img" / name
            self.assertTrue(src.is_file(), name)
            self.assertEqual(src.read_bytes(), dst.read_bytes(), name)

        def hero_of(rel):
            text = (DIST / rel).read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"<h1[\s>]", text)), 1, rel)
            block = text.split('<section class="hero">', 1)[1].split("</section>", 1)[0]
            return text, block

        def lazy(page, name, alt_key, width, height):
            tag = re.search(rf'<img\b[^>]*{re.escape(name)}[^>]*>', page)
            self.assertIsNotNone(tag, name)
            tag = tag.group(0)
            self.assertIn('loading="lazy"', tag)
            self.assertIn('decoding="async"', tag)
            self.assertIn(f'width="{width}"', tag)
            self.assertIn(f'height="{height}"', tag)
            self.assertIn('class="sec-img"', tag)
            self.assertNotIn("fetchpriority", tag)
            self.assertIn(build.ALT[alt_key], html.unescape(tag))

        home, hero = hero_of("index.html")
        self.assertEqual(home.count('rel="preload"'), 1)
        self.assertIn('rel="preload" as="image" href="/assets/img/hero-home.webp"', home)
        self.assertIn("/assets/img/hero-home-800.webp 800w", hero)
        self.assertIn('media="(max-width: 640px)"', hero)
        self.assertIn("/assets/img/hero-home-mobile.webp", hero)
        self.assertIn('fetchpriority="high"', hero)
        self.assertIn('loading="eager"', hero)
        self.assertNotIn('loading="lazy"', hero)
        self.assertIn('width="1280"', hero)
        self.assertIn('height="720"', hero)
        self.assertIn(build.ALT["hero-home"], html.unescape(hero))
        for rel, stem in (("check-up.html", "hero-check-up"), ("sponsor.html", "hero-sponsor")):
            text, block = hero_of(rel)
            self.assertNotIn('rel="preload"', text.split("</head>", 1)[0])
            self.assertIn(f"/assets/img/{stem}-800.webp 800w", block)
            self.assertIn(f"/assets/img/{stem}-mobile.webp", block)
            self.assertIn('fetchpriority="high"', block)
            self.assertIn('loading="eager"', block)
            self.assertNotIn('loading="lazy"', block)
            self.assertIn(build.ALT[stem], html.unescape(block))
        lazy(home, "bandi-per-area.webp", "bandi-per-area", 800, 308)
        lazy(home, "bandi-per-destinatario.webp", "bandi-per-destinatario", 800, 600)
        lazy(home, "verifica-ammissibilita.webp", "verifica-ammissibilita", 800, 600)
        checkup = (DIST / "check-up.html").read_text(encoding="utf-8")
        lazy(checkup, "relazione-scritta.webp", "relazione-scritta", 800, 600)
        paga = checkup.split('id="paga-ora"', 1)[1].split("</section>", 1)[0]
        lazy(paga, "verifica-ammissibilita.webp", "verifica-ammissibilita", 800, 600)
        livelli = checkup.split("<h2>Livelli del servizio</h2>", 1)[1].split('<aside class="promo"', 1)[0]
        self.assertIn("relazione-scritta.webp", livelli)
        about = (DIST / "chi-siamo.html").read_text(encoding="utf-8")
        lazy(about, "metodo-fonti-ufficiali.webp", "metodo-fonti-ufficiali", 800, 600)
        contatti = (DIST / "contatti.html").read_text(encoding="utf-8")
        lazy(contatti, "contatti.webp", "contatti", 800, 600)
        for name in ("toscana.html", "umbria.html", "emilia-romagna.html", "nazionale.html"):
            page = (DIST / name).read_text(encoding="utf-8")
            section = page.split('id="altre-aree"', 1)[1].split("</section>", 1)[0]
            lazy(section, "bandi-per-area.webp", "bandi-per-area", 800, 308)
        settori = list((DIST / "settore").glob("*.html"))
        self.assertGreaterEqual(len(settori), 8)
        for path in settori:
            page = path.read_text(encoding="utf-8")
            section = page.split('id="altri-dest"', 1)[1].split("</section>", 1)[0]
            lazy(section, "bandi-per-destinatario.webp", "bandi-per-destinatario", 800, 600)
        preloads = [p.name for p in pages if 'rel="preload"' in p.read_text(encoding="utf-8")]
        self.assertEqual(preloads, ["index.html"])
        og = home.split('property="og:image"', 1)[1].split(">", 1)[0]
        self.assertIn("og.png", og)
        self.assertNotIn("hero-", og)

    def test_seo_titoli_meta_e_pagine_nuove(self):
        """Title delle schede entro 60 caratteri, meta entro 155, senza puntini."""
        for path in (DIST / "bando").glob("*.html"):
            text = path.read_text(encoding="utf-8")
            title = html.unescape(re.search(r"<title>(.*?)</title>", text).group(1))
            desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', text).group(1))
            self.assertLessEqual(len(title), 60, path.name)
            self.assertLessEqual(len(desc), 155, path.name)
            self.assertNotIn("…", desc, path.name)
            self.assertNotIn("...", desc, path.name)
            self.assertNotIn("Arezzo-Siena", title + desc, path.name)
            self.assertEqual(title, build.seo_copy.TITOLO_SCHEDA[path.stem], path.name)
            if path.stem in build.seo_copy.META_FISSA:
                self.assertEqual(desc, " ".join(build.seo_copy.META_FISSA[path.stem].split()), path.name)
        premio = (DIST / "bando" / "premio-innovazione-toscana-2026.html").read_text(encoding="utf-8")
        self.assertNotIn("Amerigo", premio)
        self.assertNotIn("Vespucci", premio)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("Amerigo", home)
        self.assertNotIn("Vespucci", home)
        neve = (DIST / "bando" / "bando-neve-funzionamento-toscana-2026.html").read_text(encoding="utf-8")
        neve_title = html.unescape(re.search(r"<title>(.*?)</title>", neve).group(1))
        neve_h1 = html.unescape(re.search(r"<h1>(.*?)</h1>", neve).group(1))
        self.assertEqual(neve_title, "Bando Neve Toscana 2026: fondo perduto fino all'80%")
        self.assertLessEqual(len(neve_title), 60)
        self.assertEqual(
            neve_h1,
            "Bando Neve Toscana 2026: fondo perduto fino all'80% per gli impianti di risalita",
        )
        self.assertIn("16/11/2026", neve)
        self.assertIn("80%", neve)
        self.assertNotIn("Invitalia", neve)
        self.assertNotIn("+ IVA", neve)
        self.assertNotIn("ottieni il contributo", neve.lower())

        page = (DIST / "check-up.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Check-up Bandi: quali bandi sono adatti alla tua impresa</h1>", page)
        self.assertIn('"@type": "FAQPage"', page)
        self.assertIn('"@type": "BreadcrumbList"', page)
        self.assertIn("Check-up Bandi", page)
        self.assertNotIn("presenta anche la domanda", page.lower())
        self.assertNotIn("presentazione della domanda", page.lower())
        for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
            chunk = page.split(attr, 1)[1].split(">", 1)[0]
            self.assertIn(build.CHECKUP_IVA_NOTE, html.unescape(chunk))
        self.assertIn('aria-label="Guide"', home)
        self.assertIn('href="/guida/bando-a-sportello"', home)
        self.assertIn('href="/guida/de-minimis"', home)
        self.assertIn('href="/guida/fondo-perduto-o-finanziamento-agevolato"', home)
        self.assertIn("Cosa significa bando a sportello?", home)
        self.assertIn("Scopri il Check-up Bandi", home)

        toscana = (DIST / "toscana.html").read_text(encoding="utf-8")
        self.assertIn("data-aperti-n", toscana)
        self.assertIn('querySelectorAll("[data-aperti-n]")', toscana)
        self.assertIn('href="/aprire-attivita-toscana"', toscana)
        self.assertIn('href="/bandi-camere-di-commercio-toscana"', toscana)
        umbria = (DIST / "umbria.html").read_text(encoding="utf-8")
        self.assertIn("<h2>Bandi Gepafin</h2>", umbria)
        self.assertIn("<h2>Bandi Sviluppumbria</h2>", umbria)

        hub = (DIST / "bandi-camere-di-commercio-toscana.html").read_text(encoding="utf-8")
        for titolo in (
            "Camera di Commercio di Firenze",
            "Camera di Commercio di Arezzo e Siena",
            "Camera di Commercio della Maremma e del Tirreno",
            "Camera di Commercio della Toscana Nord-Ovest",
            "Camera di Commercio di Pistoia-Prato",
        ):
            self.assertIn(f"<h2>{titolo}</h2>", hub)
        self.assertNotIn('id="elenco"', hub)
        self.assertIn('"@type": "BreadcrumbList"', hub)
        self.assertIn('"@type": "FAQPage"', hub)
        scheda = (DIST / "bando" / "cciaa-arezzo-siena-export-2026-arezzo.html").read_text(encoding="utf-8")
        self.assertIn('href="/bandi-camere-di-commercio-toscana#arezzo-siena"', scheda)
        self.assertIn("Altri bandi della Camera di Commercio di Arezzo e Siena", scheda)

        er = (DIST / "bandi-camere-di-commercio-emilia-romagna.html").read_text(encoding="utf-8")
        self.assertIn("Cosa sono i contributi tramite Confidi?", er)
        self.assertIn('href="/bandi-camere-di-commercio-emilia-romagna"', (DIST / "emilia-romagna.html").read_text(encoding="utf-8"))

        aprire = (DIST / "aprire-attivita-toscana.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Contributi per aprire un'attività in Toscana</h1>", html.unescape(aprire))
        self.assertIn("Regolamento UE 2023/2831", aprire)
        self.assertIn("eur-lex.europa.eu", aprire)
        self.assertIn('href="/guida/de-minimis"', aprire)
        self.assertIn('href="/aprire-attivita-toscana"', (DIST / "settore" / "nuove-imprese.html").read_text(encoding="utf-8"))
        self.assertIn('href="/aprire-attivita-toscana"', (DIST / "settore" / "under-35.html").read_text(encoding="utf-8"))

        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = ET.parse(DIST / "sitemap.xml").findall("s:url", ns)

        def field(node, name):
            return node.find(f"s:{name}", ns).text

        locs = [field(node, "loc") for node in urls]
        nuovi = [
            BASE + "bandi-camere-di-commercio-toscana",
            BASE + "bandi-camere-di-commercio-emilia-romagna",
            BASE + "aprire-attivita-toscana",
            BASE + "guida/bando-a-sportello",
            BASE + "guida/de-minimis",
            BASE + "guida/fondo-perduto-o-finanziamento-agevolato",
        ]
        self.assertEqual(locs[-6:], nuovi)
        data = json.loads((ROOT / "data" / "bandi.json").read_text(encoding="utf-8"))
        bandi = sorted(data, key=lambda b: b["scadenza"] or "9999-12-31")
        attesi = [
            BASE,
            BASE + "nazionale",
            BASE + "toscana",
            BASE + "umbria",
            BASE + "emilia-romagna",
        ]
        for name in (
            "startup", "pmi", "nuove-imprese", "under-35", "donne",
            "investitori", "professionisti", "grandi-imprese",
        ):
            attesi.append(BASE + "settore/" + name)
        for bando in bandi:
            attesi.append(BASE + "bando/" + bando["id"])
        for slug in ("chi-siamo", "contatti", "sponsor", "check-up", "cookie", "note-legali", "disclaimer", "privacy"):
            attesi.append(BASE + slug)
        self.assertEqual(locs[:-6], attesi)
        by = {field(node, "loc"): node for node in urls}
        for slug in ("cookie", "note-legali", "disclaimer", "privacy"):
            self.assertEqual(field(by[BASE + slug], "lastmod"), "2026-10-26", slug)
            self.assertEqual(field(by[BASE + slug], "changefreq"), "yearly", slug)
            self.assertEqual(field(by[BASE + slug], "priority"), "0.3", slug)
        self.assertEqual(field(by[BASE], "changefreq"), "weekly")
        self.assertEqual(field(by[BASE], "priority"), "1.0")
        self.assertEqual(field(by[BASE], "lastmod"), "2026-10-26")
        self.assertEqual(field(by[BASE + "check-up"], "lastmod"), "2026-10-26")
        self.assertEqual(field(by[BASE + "check-up"], "changefreq"), "monthly")
        self.assertEqual(field(by[BASE + "bando/nuova-sabatini"], "lastmod"), "2026-10-26")
        self.assertEqual(field(by[BASE + "bando/nuova-sabatini"], "changefreq"), "weekly")
        self.assertEqual(field(by[BASE + "bando/nuova-sabatini"], "priority"), "0.7")
        for loc in nuovi[:3]:
            self.assertEqual(field(by[loc], "lastmod"), "2026-10-25")
            self.assertEqual(field(by[loc], "changefreq"), "weekly")
            self.assertEqual(field(by[loc], "priority"), "0.8")
        for loc in nuovi[3:]:
            self.assertEqual(field(by[loc], "lastmod"), "2026-10-25")
            self.assertEqual(field(by[loc], "changefreq"), "monthly")
            self.assertEqual(field(by[loc], "priority"), "0.6")
        fondo = (DIST / "guida" / "fondo-perduto-o-finanziamento-agevolato.html").read_text(encoding="utf-8")
        self.assertNotIn("Il contributo a fondo perduto si tassa", fondo)
        self.assertNotIn("commercialista", fondo.lower())
        self.assertIn('"@type": "FAQPage"', fondo)
        self.assertIn('"@type": "BreadcrumbList"', fondo)
        de_minimis = (DIST / "guida" / "de-minimis.html").read_text(encoding="utf-8")
        self.assertIn("eur-lex.europa.eu", de_minimis)
        self.assertIn("rna.gov.it", de_minimis)
        self.assertIn("non un parere sul caso della singola impresa", de_minimis)
        sportello = (DIST / "guida" / "bando-a-sportello.html").read_text(encoding="utf-8")
        self.assertIn('href="/bando/nuova-sabatini"', sportello)
        self.assertIn('href="/bando/bando-132-50k-2026"', sportello)
        self.assertIn("lista d'attesa", html.unescape(sportello).lower())

    def test_lancio_e_scheda_scaduta_dopo_il_23_ottobre(self):
        fino = build.checkup_body(datetime.date(2026, 10, 30))
        dopo = build.checkup_body(datetime.date(2026, 10, 31))
        codice = urllib.parse.quote("Codice di lancio: LANCIO15")
        self.assertIn('<aside class="promo"', fino)
        self.assertIn(build.CHECKUP_LANCIO, fino)
        self.assertIn(codice, fino)
        self.assertNotIn('<aside class="promo"', dopo)
        self.assertNotIn(build.CHECKUP_LANCIO, dopo)
        self.assertNotIn(codice, dopo)
        self.assertIn("LANCIO15", dopo)
        data = json.loads((ROOT / "data" / "bandi.json").read_text(encoding="utf-8"))
        slug = "cciaa-tno-doppia-transizione-2-2026"
        righe = build.prepare(data, datetime.date(2026, 10, 27))
        chiuso = next(b for b in righe if b["id"] == slug)
        self.assertTrue(chiuso["scaduto"])
        card = build.card(chiuso, "", datetime.date(2026, 10, 27))
        self.assertIn(" hidden>", card)
        self.assertIn(">Scaduto<", card)
        urls = [item["url"] for item in build.item_list(righe)["itemListElement"]]
        self.assertNotIn(build.public_url(f"bando/{slug}.html"), urls)
        home = (DIST / "index.html").read_text(encoding="utf-8")
        visibile = next(
            block for block in re.findall(r'<article class="card\b.*?</article>', home, re.S)
            if f"/bando/{slug}" in block
        )
        self.assertNotIn(" hidden>", visibile)


class Update(unittest.TestCase):
    def test_match_e_scrittura_atomica(self):
        self.assertTrue(update.matches("<p>Attivo</p>", "Attivo"))
        self.assertFalse(update.matches("<p>Attivo</p>", ""))
        self.assertFalse(update.matches("<p>Attivo</p>", "Chiuso"))
        path = DIST / "atomico-test.txt"
        update.atomic_write(path, "ok")
        self.assertEqual(path.read_text(encoding="utf-8"), "ok")
        self.assertFalse(path.with_name(path.name + ".tmp").exists())
        path.unlink()


if __name__ == "__main__":
    raise SystemExit(unittest.main())
