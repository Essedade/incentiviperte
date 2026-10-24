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

    def test_home_filtri_conversione_e_link(self):
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn('lang="it"', home)
        self.assertIn('id="main"', home)
        self.assertEqual(home.count("<h1"), 1)
        self.assertIn('<button type="button" class="link" id="z">Azzera filtri</button>', home)
        self.assertIn('type="search"', home)
        self.assertIn(".after(sponsor)", home)
        self.assertIn("Sponsorizzato", home)
        self.assertIn("https://fogliopef.pages.dev", home)
        self.assertNotIn("fogliopef.gumroad.com", home)
        self.assertIn("https://www.linkedin.com/company/fogliopef", home)
        about = (DIST / "chi-siamo.html").read_text(encoding="utf-8")
        self.assertIn("https://fogliopef.pages.dev", about)
        self.assertIn("https://www.linkedin.com/company/fogliopef", about)
        sponsor = (DIST / "sponsor.html").read_text(encoding="utf-8")
        self.assertIn("https://fogliopef.pages.dev", sponsor)
        self.assertIn(">fogliopef.pages.dev<", sponsor)
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

    def test_bandi_20_ottobre_e_conto_alla_rovescia(self):
        home = (DIST / "index.html").read_text(encoding="utf-8")
        self.assertIn("Aggiornato il 24/10/2026", home)
        self.assertNotIn("Aggiornato il 20/10/2026", home)
        self.assertNotIn("Aggiornato il 15/10/2026", home)
        self.assertIn('getAttribute("data-scadenza")', home)
        self.assertIn('getAttribute("data-apre")', home)
        self.assertIn('data-scad="2026-10-23"', home)
        self.assertIn('data-scadenza="2026-10-23"', home)
        visible = re.sub(r"<script\b.*?</script>", "", home, flags=re.S)
        self.assertIn("Scade il 23/10/2026", visible)
        self.assertIn("Aperto fino al 23/10/2026", visible)
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
        self.assertTrue(all(row["ultimo_controllo"] == "2026-10-24" for row in data))
        oggi = datetime.date(2026, 10, 24)
        prepared = build.prepare(data, oggi)
        self.assertEqual(sum(1 for b in prepared if b["scaduto"]), 1)
        self.assertEqual(sum(1 for b in prepared if b["in_arrivo"]), 2)
        self.assertEqual(sum(1 for b in prepared if build.is_aperto(b)), 53)
        toscana = [b for b in prepared if b["regione"] == "Toscana"]
        emilia = [b for b in prepared if b["regione"] == "Emilia-Romagna"]
        self.assertEqual(len(toscana), 25)
        self.assertEqual(sum(1 for b in toscana if b["scaduto"]), 1)
        self.assertEqual(sum(1 for b in emilia if b["in_arrivo"]), 2)
        self.assertEqual(sum(1 for b in prepared if b["regione"] == "Umbria"), 6)
        self.assertEqual(sum(1 for b in prepared if b["regione"] == "Nazionale"), 8)
        self.assertEqual(sum(1 for b in emilia if build.is_aperto(b)), 15)
        self.assertEqual(sum(1 for b in toscana if build.is_aperto(b)), 24)
        eco = next(b for b in prepared if b["id"] == "economia-circolare-privati")
        self.assertTrue(eco["scaduto"])
        self.assertEqual(eco["scadenza"], "2026-10-23")
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
            return "".join(re.findall(r'<p class="note">(.*?)</p>', card, re.S))

        for slug in (
            "cciaa-maremma-tirreno-internazionalizzazione-2026",
            "cciaa-maremma-tirreno-agricoltura-green-2026",
            "cciaa-maremma-tirreno-imprese-vicinato-2026",
        ):
            text = note(slug)
            self.assertIn("senza garanzia di copertura", text, slug)
        self.assertIn("18.481,60", note("cciaa-maremma-tirreno-internazionalizzazione-2026"))
        self.assertIn("senza ulteriori risorse da assegnare", note("cciaa-maremma-tirreno-agricoltura-green-2026"))
        self.assertIn("0,00", note("cciaa-maremma-tirreno-imprese-vicinato-2026"))
        poli = note("umbria-poli-innovazione-2026")
        self.assertIn("30/10/2026", poli)
        self.assertIn("30/11/2026", poli)
        self.assertIn("termine da verificare", poli)
        turismo = note("cciaa-maremma-tirreno-turismo-sostenibile-2026")
        self.assertIn("40.000", turismo)
        self.assertIn("60.000", turismo)
        self.assertIn("50.000", turismo)

    def test_dominio_cloudflare_e_niente_vecchio_percorso(self):
        self.assertEqual(build.BASE, "https://incentiviperte.pages.dev/")
        self.assertIn("https://incentiviperte.pages.dev/", (DIST / "index.html").read_text(encoding="utf-8"))
        self.assertIn("Sitemap: https://incentiviperte.pages.dev/sitemap.xml", (DIST / "robots.txt").read_text(encoding="utf-8"))
        for path in DIST.rglob("*"):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            self.assertNotIn(b"essedade.github.io", raw, path.as_posix())
            self.assertNotIn(b"fogliopef.gumroad.com", raw, path.as_posix())
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
        for icon in ("favicon.svg", "favicon-16.png", "favicon-32.png", "apple-touch-icon.png", "favicon-512.png"):
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
        self.assertIn('data-scadenza="2026-10-23"', home)
        self.assertIn("Scade il 23/10/2026", home)
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
        self.assertIn('rel="canonical" href="https://incentiviperte.pages.dev/check-up"', page)
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
        self.assertEqual(services[0]["url"], "https://incentiviperte.pages.dev/check-up")
        privacy = (DIST / "privacy.html").read_text(encoding="utf-8")
        cookie = (DIST / "cookie.html").read_text(encoding="utf-8")
        for text in (privacy, cookie):
            self.assertIn("Cloudflare Pages (Cloudflare, Inc.)", text)
            self.assertIn("https://www.cloudflare.com/privacypolicy/", text)
            self.assertNotIn("GitHub", text)
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
            text = path.read_text(encoding="utf-8")
            title = re.search(r"<title>(.*?)</title>", text).group(1)
            desc = re.search(r'<meta name="description" content="([^"]*)"', text).group(1)
            self.assertNotRegex(title + " " + desc, r"\d+ bandi aperti")
            self.assertIsNone(re.search(r'''(?:href|src)="(?!https?:|mailto:)[^"]*\.html''', text), path.name)

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
        scheda = (DIST / "bando" / "economia-circolare-privati.html").read_text(encoding="utf-8")
        visible = re.sub(r"<script\b.*?</script>", "", scheda, flags=re.S)
        self.assertIn("Aperto fino al 23/10/2026", visible)
        self.assertIn(">Scade il 23/10/2026<", visible)
        self.assertNotIn(">Scaduto il 23/10/2026<", visible)
        self.assertIn('data-deadline="2026-10-23"', scheda)
        self.assertIn('data-scadenza="2026-10-23"', scheda)
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
