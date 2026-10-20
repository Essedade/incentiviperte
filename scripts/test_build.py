#!/usr/bin/env python3
"""Controlli sul generatore: dati, etichette, SEO, pulizia dei file obsoleti."""
import datetime
import json
import pathlib
import re
import sys
import unittest
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
        for loc in (BASE, BASE + "nazionale.html", BASE + "toscana.html", BASE + "settore/startup.html", BASE + "settore/pmi.html", BASE + "sponsor.html"):
            self.assertIn(loc, locs)
        self.assertNotIn(BASE + "404.html", locs)
        for loc in locs:
            rel = "index.html" if loc == BASE else loc.removeprefix(BASE)
            self.assertTrue((DIST / rel).is_file(), rel)

    def test_home_filtri_conversione_e_link(self):
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn('lang="it"', home)
        self.assertIn('id="main"', home)
        self.assertEqual(home.count("<h1"), 1)
        self.assertIn('<button type="button" class="link" id="z">Azzera filtri</button>', home)
        self.assertIn('type="search"', home)
        self.assertIn(".after(sponsor)", home)
        self.assertIn("Sponsorizzato", home)
        self.assertIn("https://fogliopef.gumroad.com", home)
        self.assertIn("stesso titolare", home.lower())
        self.assertNotIn("link affiliato", home.lower())
        self.assertIn('href="settore/startup.html"', home)
        self.assertIn('href="nazionale.html"', home)
        self.assertIn("Domande frequenti", home)
        self.assertIn("MonetaryGrant", (DIST / "bando" / "smart-start-italia.html").read_text(encoding="utf-8"))
        self.assertNotIn("<script src=", home)
        for token in ("googletagmanager", "gtag(", "cookiebot", "facebook.net"):
            self.assertNotIn(token, home)

    def test_scheda_collegamenti_e_sponsor(self):
        page = (DIST / "bando" / "smart-start-italia.html").read_text(encoding="utf-8")
        self.assertIn("Bandi collegati", page)
        self.assertIn('href="../settore/startup.html"', page)
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
        self.assertIn(build.EMAIL, foglio)
        self.assertIn(build.FPEF_EMAIL, foglio)
        self.assertIn("Contatto per FoglioPEF:", foglio)
        self.assertIn(build.EMAIL, entrambi)
        self.assertIn(build.FPEF_EMAIL, entrambi)
        self.assertIn("Contatto per entrambi i siti:", entrambi)
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
        self.assertIn('href="/settore/startup.html"', page)
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
        self.assertIn('href="contatti.html">Richiedi il Check-up Bandi</a>', home)
        self.assertIn("incentivi nazionali per avviare e far crescere l'impresa", home)
        self.assertIn(
            "Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.",
            about,
        )
        toscana = (DIST / "toscana.html").read_text(encoding="utf-8")
        self.assertIn("Tutta la Toscana: bandi regionali e delle Camere di Commercio toscane", toscana)
        self.assertNotIn("Arezzo-Siena", toscana)
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
            for banned in ("Invitalia", "Sorbolini", "Frascadore", "Flavio", "Giuseppe", "Arezzo-Siena"):
                self.assertNotIn(banned, text, path.as_posix())
            visible = build.without_urls(text)
            self.assertIsNone(re.search(r"invitalia", visible, re.I), path.as_posix())

    def test_dominio_cloudflare_e_niente_vecchio_percorso(self):
        self.assertEqual(build.BASE, "https://incentiviperte.pages.dev/")
        self.assertIn("https://incentiviperte.pages.dev/", (DIST / "index.html").read_text(encoding="utf-8"))
        self.assertIn("Sitemap: https://incentiviperte.pages.dev/sitemap.xml", (DIST / "robots.txt").read_text(encoding="utf-8"))
        for path in DIST.rglob("*"):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            self.assertNotIn(b"essedade.github.io", raw, path.as_posix())
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
            if rel == "404.html":
                url = "https://incentiviperte.pages.dev/"
            else:
                url = "https://incentiviperte.pages.dev/" + rel
            self.assertIn(f'content="0; url={url}"', page, rel)
            self.assertIn(f'rel="canonical" href="{url}"', page, rel)
            self.assertIn(f'location.replace("{url}")', page, rel)


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
