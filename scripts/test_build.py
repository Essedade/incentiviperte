#!/usr/bin/env python3
"""Controlli sul generatore: dati, etichette, SEO, pulizia dei file obsoleti."""
import datetime
import json
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build
import update

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
TODAY = datetime.date(2026, 10, 13)
BASE = "https://essedade.github.io/incentiviperte/"


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
        for rel in ("privacy.html", "note-legali.html"):
            text = (DIST / rel).read_text(encoding="utf-8")
            self.assertIn("Davide Davoglio, Arezzo (Italia)", text)
        for path in DIST.rglob("*.html"):
            if path.name in ("privacy.html", "note-legali.html"):
                continue
            self.assertNotIn("Davoglio", path.read_text(encoding="utf-8"))

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
        self.assertIn('href="/incentiviperte/style.css"', page)
        self.assertIn('href="/incentiviperte/settore/startup.html"', page)

    def test_jsonld(self):
        for path in DIST.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            for chunk in text.split('<script type="application/ld+json">')[1:]:
                json.loads(chunk.split("</script>", 1)[0])


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
