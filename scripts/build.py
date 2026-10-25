#!/usr/bin/env python3
"""Genera il sito statico in dist/ da data/bandi.json.

Nessuna dipendenza, nessun tracker, nessun cookie.
Uso: python3 scripts/build.py
"""
import datetime
import html
import json
import pathlib
import re
import shutil
import sys
import urllib.parse

import seo_copy

R = pathlib.Path(__file__).resolve().parent.parent
D = R / "dist"
DATA = R / "data" / "bandi.json"
BASE = "https://incentiviperte.github.io/"
SITE = "IncentiviPerTe"
LINKEDIN = "https://www.linkedin.com/company/incentiviperte/"
EMAIL = "incentiviperte.team@gmail.com"
FPEF_EMAIL = "fogliopef.team@gmail.com"
FPEF = "https://fogliopef.github.io"
FPEF_LI = "https://www.linkedin.com/company/fogliopef"
FPEF_DESC = "FoglioPEF: modelli Excel per business plan, immobiliare e finanza d'impresa."
# Pagine prodotto sul negozio Gumroad fogliopef. Sono bozze non pubblicate:
# unire solo dopo che entrambe sono pubbliche. Unico punto di configurazione.
# IncentiviPerTe – Check-up Bandi Base (49 €)
GUMROAD_CHECKUP_BASE_URL = "https://fogliopef.gumroad.com/l/checkup-bandi-base"
# IncentiviPerTe – Check-up Bandi Completo (79 €)
GUMROAD_CHECKUP_COMPLETO_URL = "https://fogliopef.gumroad.com/l/checkup-bandi-completo"
CHECKUP_PRODUCT_BASE = "IncentiviPerTe – Check-up Bandi Base"
CHECKUP_PRODUCT_COMPLETO = "IncentiviPerTe – Check-up Bandi Completo"
CARD_PAY_LABEL = "Pagamento sicuro con carta tramite Gumroad"
CHECKUP_BASE = "report di circa 3-4 pagine, entro 5 giorni lavorativi dalla ricezione dei dati completi"
CHECKUP_EXTRA = (
    "requisiti punto per punto",
    "cumulo e de minimis",
    "documenti da preparare",
    "priorità motivata",
    "stima indicativa dell'agevolazione (non garantita)",
    "scadenzario",
    "call di 30 minuti",
)
CHECKUP_COMPLETO = (
    "report di 6-10 pagine, entro 7-10 giorni lavorativi dalla ricezione dei dati completi, "
    "con tutto il Base più " + ", ".join(CHECKUP_EXTRA[:-1]) + " e " + CHECKUP_EXTRA[-1]
)
CHECKUP_IVA_NOTE = (
    "Con carta su Gumroad, ai clienti privati dell'UE Gumroad può aggiungere l'IVA del loro paese al pagamento."
)
CHECKUP_LANCIO = (
    "Con LANCIO15 fino al 30/10/2026: Base 41,65 €, Completo 67,15 €."
)
# Il codice resta in pagina fino al 30/10/2026 compreso. Dal 31/10 sparisce in generazione
# e, se la pagina è già stata pubblicata, anche nello script del browser.
LANCIO_FINO = datetime.date(2026, 10, 30)
# Giorno del ritocco SEO. lastmod delle pagine toccate; le pagine legali restano alla data dei dati.
SEO_LASTMOD = "2026-10-25"
PAGINE_LASTMOD_DATI = {"cookie.html", "note-legali.html", "disclaimer.html", "privacy.html"}
# Link del gruppo «Guide» nel footer. L'ordine è quello del documento.
GUIDE = (
    ("guida/bando-a-sportello.html", "Bando a sportello"),
    ("guida/de-minimis.html", "Regime de minimis"),
    ("guida/fondo-perduto-o-finanziamento-agevolato.html", "Fondo perduto o finanziamento"),
)
RNA_AIUTI = "https://www.rna.gov.it/"
EURLEX_DE_MINIMIS = "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX%3A32023R2831"
SPONSOR_DA = "Da 49 € al mese · prezzo di lancio"
REG = ["Nazionale", "Toscana", "Umbria", "Emilia-Romagna"]
REQUIRED = (
    "id", "titolo", "ente", "regione", "destinatari", "scadenza", "nota_scadenza",
    "sintesi", "url", "check", "ultimo_controllo", "importo",
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Stato facoltativo, riutilizzabile. «lista_attesa» non chiude il bando:
# lo sportello resta aperto e la scheda mostra l'avviso sui fondi.
STATI = {
    "aperto": "",
    "lista_attesa": "Risorse esaurite: nuove domande solo in lista d'attesa.",
}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
TRACKERS = (
    "googletagmanager", "google-analytics", "gtag(", "facebook.net", "connect.facebook",
    "hotjar", "doubleclick", "plausible.io", "segment.com", "mixpanel", "clarity.ms",
    "cookiebot", "googlesyndication", "mc.yandex",
)
AFFILIATE_HINTS = ("affiliate", "awin.", "shareasale", "tradedoubler", "tradetracker")
DEST_ORDER = ["Startup", "PMI", "Nuove imprese", "Under 35", "Donne", "Investitori", "Professionisti", "Grandi imprese"]
INTRO_REG = {
    "Nazionale": "Incentivi nazionali per avviare e far crescere l'impresa: finanziamenti a tasso zero e contributi a fondo perduto per nuove imprese, startup innovative e investimenti, insieme alle misure di MIMIT e del Ministero del Lavoro. Molte valgono anche per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna; altre, come Resto al Sud 2.0, riguardano solo il Mezzogiorno.",
    "Toscana": "Tutta la Toscana: bandi regionali e delle Camere di Commercio toscane, in tutte le province. Per un'impresa toscana restano rilevanti anche gli incentivi nazionali per avviare e far crescere l'impresa, tra cui Autoimpiego Centro-Nord e Smart&Start Italia.",
    "Umbria": "Bandi della Regione Umbria gestiti da Gepafin e Sviluppumbria. Per un'impresa umbra restano rilevanti anche gli incentivi nazionali per avviare e far crescere l'impresa, tra cui Autoimpiego Centro-Nord.",
    "Emilia-Romagna": "Bandi della Regione Emilia-Romagna, comprese le finestre del Fondo Multiscopo. Per un'impresa emiliano-romagnola restano rilevanti anche gli incentivi nazionali per avviare e far crescere l'impresa, tra cui Autoimpiego Centro-Nord.",
}
INTRO_DEST = {
    "Startup": "Misure per startup e imprese innovative: finanziamenti a tasso zero, premi e agevolazioni collegate all'investimento nel capitale.",
    "PMI": "Misure per piccole e medie imprese: fondo perduto, finanziamenti agevolati e contributi su interessi e garanzie.",
    "Nuove imprese": "Misure per chi avvia un'attività, in particolare voucher e contributi per nuove imprese.",
    "Under 35": "Misure in cui il requisito è l'età, fino a 35 anni, per avviare o sviluppare un'impresa.",
    "Donne": "Misure in cui la compagine femminile è un requisito oppure aumenta l'intensità dell'aiuto.",
    "Investitori": "Agevolazioni per le persone fisiche che investono nel capitale di startup innovative.",
    "Professionisti": "Misure il cui bando include anche i professionisti tra i destinatari.",
    "Grandi imprese": "Misure che ammettono le grandi imprese insieme alle PMI.",
}
FAQ = (
    ("IncentiviPerTe è gratuito?",
     "Sì. Consultare i bandi non costa nulla e non richiede un account. Il sito si sostiene con spazi sponsor, sempre etichettati Sponsorizzato."),
    ("La scheda basta per presentare domanda?",
     "No. Ogni scheda è una sintesi. Requisiti, scadenze e importi vanno verificati sul testo dell'ente: il link è nella scheda."),
    ("Come segnalo un bando o un errore?",
     "Dalla pagina Contatti, con un messaggio alla Pagina LinkedIn IncentiviPerTe o all'indirizzo incentiviperte.team@gmail.com."),
    ("Posso comparire sul sito con il mio studio?",
     "Sì. Uno spazio su IncentiviPerTe parte da 49 € al mese, prezzo di lancio. Importi, regole ed etichetta Sponsorizzato sono sulla pagina Sponsor."),
    ("Che cos'è il Check-up Bandi?",
     "È un controllo personalizzato di quali bandi regionali e nazionali sono adatti alla tua impresa: tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), Umbria, Emilia-Romagna e incentivi nazionali per avviare e far crescere l'impresa. Ricevi una relazione scritta. Per richiederlo usa la pagina Check-up."),
)
NAV = (
    ("index.html", "Bandi", ""),
    ("nazionale.html", "Nazionali", ""),
    ("toscana.html", "Toscana", ""),
    ("umbria.html", "Umbria", ""),
    ("emilia-romagna.html", "Emilia-Romagna", ""),
    ("chi-siamo.html", "Chi siamo", ""),
    ("sponsor.html", "Sponsor", ""),
    ("contatti.html", "Contatti", ""),
    ("check-up.html", "Check-up", "cta"),
)
KEEP = {
    "style.css", "favicon.svg", "favicon-16.png", "favicon-32.png", "favicon-48.png",
    "favicon-512.png", "apple-touch-icon.png", "logo-header.svg", "logo-header-80.png",
    "logo-header-160.png", "og.png", "robots.txt", "sitemap.xml", ".nojekyll",
}
# Verifica Search Console. Non è una pagina: resta fuori da sitemap e dai controlli sulle schede.
GSC_FILE = "googlec8d66ea588cfa987.html"
GSC_CONTENT = "google-site-verification: googlec8d66ea588cfa987.html"
GSC_TOKEN = "jCzN7Fx7XoDrf8U8F0zh3SqX4j2mogdrXKI-ygMN8m4"
STATIC_ASSETS = (
    "favicon.svg", "favicon-16.png", "favicon-32.png", "favicon-48.png", "favicon-512.png",
    "apple-touch-icon.png", "logo-header.svg", "logo-header-80.png", "logo-header-160.png",
    "og.png",
)
# Illustrazioni in assets/img/, copiate in dist/assets/img/ (URL /assets/img/…).
IMG = "/assets/img"
ILLUSTRAZIONI = (
    "hero-home.webp", "hero-home-800.webp", "hero-home-mobile.webp",
    "hero-check-up.webp", "hero-check-up-800.webp", "hero-check-up-mobile.webp",
    "hero-sponsor.webp", "hero-sponsor-800.webp", "hero-sponsor-mobile.webp",
    "bandi-per-area.webp", "bandi-per-destinatario.webp", "verifica-ammissibilita.webp",
    "relazione-scritta.webp", "metodo-fonti-ufficiali.webp", "contatti.webp",
)
ALT = {
    "hero-home": (
        "Illustrazione di un piccolo borgo produttivo tra colline toscane con cipressi: "
        "officina, negozio, ufficio e capannone con pannelli solari, sovrastati da un documento "
        "con spunta che diventa freccia verso l'alto"
    ),
    "hero-check-up": (
        "Illustrazione di una lista di controllo su un portablocchi con spunte verdi, una lente "
        "d'ingrandimento, una relazione rilegata, un calendario e uno scudo con spunta, tra rametti d'ulivo"
    ),
    "hero-sponsor": (
        "Illustrazione di un portatile e di uno smartphone con pagine web stilizzate in cui uno "
        "spazio è evidenziato, con un megafono, una freccia di crescita e una stretta di mano"
    ),
    "bandi-per-area": (
        "Tre paesaggi stilizzati con segnaposto: colline toscane con cipressi e vigneti, colline "
        "umbre con un borgo medievale e ulivi, pianura emiliana con filari di pioppi e un casolare"
    ),
    "bandi-per-destinatario": (
        "Illustrazione isometrica di edifici d'impresa collegati da un sentiero: un garage di "
        "startup con una piantina a forma di razzo, una bottega artigiana, un negozio, un ufficio "
        "moderno e un piccolo stabilimento"
    ),
    "verifica-ammissibilita": (
        "Illustrazione di una verifica di ammissibilità: un documento con lista di requisiti "
        "spuntati, una lente d'ingrandimento e un imbuto che seleziona una sola scheda tra molte"
    ),
    "relazione-scritta": (
        "Illustrazione di una relazione scritta rilegata con grafici stilizzati, una busta che la "
        "contiene, un calendario e un orologio"
    ),
    "metodo-fonti-ufficiali": (
        "Illustrazione di un edificio pubblico con colonne e un cipresso, collegato da una linea "
        "tratteggiata a una scheda verificata con spunta e a un calendario con frecce di aggiornamento"
    ),
    "contatti": (
        "Illustrazione di una busta aperta, due fumetti di conversazione, un aeroplanino di carta "
        "e una scheda con segnaposto per segnalare un bando o un errore"
    ),
}
e = html.escape


def region_path(regione):
    return regione.lower() + ".html"


def slugify(name):
    s = name.lower().strip()
    for src, dst in (("à", "a"), ("è", "e"), ("é", "e"), ("ì", "i"), ("ò", "o"), ("ù", "u")):
        s = s.replace(src, dst)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if not s or not ID_RE.match(s):
        raise ValueError(f"slug non valido per «{name}»")
    return s


def sector_path(name):
    return f"settore/{slugify(name)}.html"


def prefix(path):
    return "../" * path.count("/")


def public_path(file_path):
    """Percorso pubblico senza .html. I file restano nome.html: il server li rimanda."""
    if not file_path or file_path in ("index.html", "index"):
        return ""
    if file_path.endswith(".html"):
        return file_path[: -len(".html")]
    return file_path


def public_url(file_path):
    rel = public_path(file_path)
    return BASE if not rel else BASE + rel


def site_href(file_path, query="", fragment=""):
    rel = public_path(file_path)
    url = "/" + rel if rel else "/"
    if query:
        url += "?" + query
    if fragment:
        url += "#" + fragment.lstrip("#")
    return url


def is_aperto(b):
    """Un bando in arrivo ha il badge «Apre il …» e non entra nel conto degli aperti."""
    return not b.get("scaduto") and not b.get("in_arrivo")


def lancio_attivo(today):
    """True fino al 30/10/2026 compreso."""
    return today <= LANCIO_FINO


def lastmod_pagina(path, data_lastmod):
    """Le pagine il cui testo non cambia tengono la data dei dati. Le altre avanzano al ritocco.

    Con le guide nel footer ogni pagina, anche quelle legali, cambia: il lastmod avanza.
    """
    if path in PAGINE_LASTMOD_DATI and not GUIDE:
        return data_lastmod
    return max(data_lastmod, SEO_LASTMOD)


def checkup_meta():
    """La nota Gumroad resta parola per parola. Il resto è accorciato: insieme starebbero a 260 caratteri."""
    return (
        "Verifica scritta dei bandi adatti alla tua impresa. 49 € o 79 €. "
        + CHECKUP_IVA_NOTE
    )


def conto_aperti(bandi):
    """Già aperti e non scaduti: apertura assente oppure non successiva a oggi.

    È il numero del hero e dell'etichetta «bandi trovati» con i filtri azzerati.
    I bandi con apertura futura restano in elenco, ma non entrano nel conto.
    """
    return sum(1 for b in bandi if is_aperto(b))


def qty(n, one, many):
    return f"{n} {one if n == 1 else many}"


def it_date(iso):
    y, m, g = iso.split("-")
    return f"{g}/{m}/{y}"


def join_it(items):
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    conj = "ed" if items[-1][:1].lower() in "aeiouàèéìòù" else "e"
    return ", ".join(items[:-1]) + f" {conj} " + items[-1]


def clip(text, n=155):
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    cut = text[: n - 1].rsplit(" ", 1)[0].rstrip(".,;:–- ")
    if len(cut) < 40:
        cut = text[: n - 1].rstrip()
    return cut + "…"


def sort_dest(names):
    return sorted(names, key=lambda n: (DEST_ORDER.index(n) if n in DEST_ORDER else 50, n))


def parse_date(value, field, bid):
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise ValueError(f"{bid}: {field} non è una data YYYY-MM-DD")
    try:
        datetime.date.fromisoformat(value)
    except ValueError as ex:
        raise ValueError(f"{bid}: {field} non valida") from ex


def validate(bandi):
    if not isinstance(bandi, list) or not bandi:
        raise ValueError("bandi.json deve essere una lista non vuota")
    seen = set()
    slugs = {}
    for i, b in enumerate(bandi):
        if not isinstance(b, dict):
            raise ValueError(f"elemento {i}: atteso un oggetto")
        missing = [k for k in REQUIRED if k not in b]
        if missing:
            raise ValueError(f"elemento {i}: campi mancanti {', '.join(missing)}")
        bid = b["id"]
        if not isinstance(bid, str) or not ID_RE.match(bid):
            raise ValueError(f"elemento {i}: id non valido (solo minuscole, numeri e trattini)")
        if bid in seen:
            raise ValueError(f"{bid}: id duplicato")
        seen.add(bid)
        if b["regione"] not in REG:
            raise ValueError(f"{bid}: regione «{b['regione']}» non prevista. Aree ammesse: {', '.join(REG)}")
        dest = b["destinatari"]
        if not isinstance(dest, list) or not dest:
            raise ValueError(f"{bid}: destinatari deve essere una lista non vuota")
        for d in dest:
            if not isinstance(d, str) or not d.strip():
                raise ValueError(f"{bid}: destinatario vuoto")
            if "|" in d or any(ch in d for ch in "<>\n\r"):
                raise ValueError(f"{bid}: destinatario non ammesso «{d}»")
            slug = slugify(d)
            prev = slugs.get(slug)
            if prev and prev != d:
                raise ValueError(f"slug settore in conflitto tra «{prev}» e «{d}»")
            slugs[slug] = d
        if b["scadenza"] is not None:
            parse_date(b["scadenza"], "scadenza", bid)
        if "apertura" in b and b["apertura"] is not None:
            parse_date(b["apertura"], "apertura", bid)
            if b["scadenza"] is not None and b["apertura"] > b["scadenza"]:
                raise ValueError(f"{bid}: apertura successiva alla scadenza")
        parse_date(b["ultimo_controllo"], "ultimo_controllo", bid)
        stato = b.get("stato")
        if stato is not None and stato not in STATI:
            raise ValueError(
                f"{bid}: stato «{stato}» non previsto. Valori ammessi: {', '.join(STATI)}"
            )
        fonte = b.get("fonte")
        if fonte is not None:
            fonte_parts = urllib.parse.urlparse(fonte) if isinstance(fonte, str) else None
            if not fonte_parts or fonte_parts.scheme != "https" or not fonte_parts.netloc or " " in fonte:
                raise ValueError(f"{bid}: fonte deve essere un URL https")
        for field in ("titolo", "ente", "sintesi", "importo", "nota_scadenza", "check"):
            val = b[field]
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"{bid}: {field} vuoto")
            if EMAIL_RE.search(val) or "mailto:" in val.lower():
                raise ValueError(f"{bid}: {field} contiene un indirizzo email")
            if re.search(r"invitalia", val, re.I):
                raise ValueError(f"{bid}: {field} cita Invitalia; indica il ministero o «Incentivo nazionale»")
            for banned in ("Sorbolini", "Frascadore", "Flavio", "Giuseppe"):
                if banned in val:
                    raise ValueError(f"{bid}: {field} contiene un nome non pubblicabile")
        url = b["url"]
        parts = urllib.parse.urlparse(url) if isinstance(url, str) else None
        if not parts or parts.scheme != "https" or not parts.netloc or " " in url:
            raise ValueError(f"{bid}: url deve essere https")
    return bandi


def prepare(bandi, today):
    validate(bandi)
    out = []
    iso = today.isoformat()
    for src in bandi:
        b = dict(src)
        b["destinatari"] = list(src["destinatari"])
        b["scaduto"] = bool(b["scadenza"] and b["scadenza"] < iso)
        # apertura è facoltativa: se è nel futuro la scheda non è ancora aperta.
        b["in_arrivo"] = bool(b.get("apertura") and b["apertura"] > iso)
        if b["in_arrivo"]:
            b["scaduto"] = False
        out.append(b)
    out.sort(key=lambda b: b["scadenza"] or "9999-12-31")
    return out


def deadline_text(b):
    if b.get("scaduto"):
        return "Scaduto il " + it_date(b["scadenza"])
    if b.get("in_arrivo") and b.get("apertura"):
        return "Apre il " + it_date(b["apertura"])
    if b["scadenza"]:
        return f"Aperto fino al {it_date(b['scadenza'])}"
    return "Senza scadenza indicata: verifica sul sito ufficiale"


def days_left(b, today):
    if not b["scadenza"]:
        return None
    return (datetime.date.fromisoformat(b["scadenza"]) - today).days


def badge(b, today):
    """Testo stabile, uguale a ogni build finché la scadenza non passa.

    Il conto dei giorni lo calcola il browser da data-scadenza. Senza JavaScript
    resta la data; un bando già scaduto in generazione mostra Scaduto.
    """
    del today
    apre = f' data-apre="{b["apertura"]}"' if b.get("apertura") else ""
    if b.get("in_arrivo") and b.get("apertura"):
        scad = f' data-scadenza="{b["scadenza"]}"' if b.get("scadenza") else ""
        return f'<span class="badge open"{apre}{scad}>Apre il {it_date(b["apertura"])}</span>'
    if not b["scadenza"]:
        return f'<span class="badge open"{apre}>Sportello aperto</span>'
    iso = b["scadenza"]
    if b.get("scaduto"):
        return f'<span class="badge exp" data-scadenza="{iso}"{apre}>Scaduto</span>'
    return f'<span class="badge" data-scadenza="{iso}"{apre}>Scade il {it_date(iso)}</span>'


BADGE_JS = r"""<script>
(function () {
  function startOfToday() {
    var now = window.INCENTIVI_OGGI ? new Date(window.INCENTIVI_OGGI) : new Date();
    return new Date(now.getFullYear(), now.getMonth(), now.getDate());
  }
  function parts(iso) {
    var p = (iso || "").split("-");
    if (p.length !== 3 || p[0].length !== 4) return null;
    if (isNaN(+p[0]) || isNaN(+p[1]) || isNaN(+p[2])) return null;
    return p;
  }
  function daysLeft(iso, start) {
    var p = parts(iso);
    if (!p) return null;
    var target = new Date(+p[0], +p[1] - 1, +p[2]);
    return Math.round((target - start) / 864e5);
  }
  function itDate(p) {
    var d = p[2].length < 2 ? "0" + p[2] : p[2];
    var m = p[1].length < 2 ? "0" + p[1] : p[1];
    return d + "/" + m + "/" + p[0];
  }
  var start = startOfToday();
  var nodes = document.querySelectorAll(".badge[data-scadenza], .badge[data-apre]");
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    var card = el.closest("article");
    var apre = el.getAttribute("data-apre") || (card && card.getAttribute("data-apre")) || "";
    var pOpen = parts(apre);
    el.classList.remove("soon", "exp", "open");
    if (pOpen && daysLeft(apre, start) > 0) {
      el.textContent = "Apre il " + itDate(pOpen);
      el.classList.add("open");
      if (card) card.setAttribute("data-scaduto", "0");
      continue;
    }
    var iso = el.getAttribute("data-scadenza") || "";
    var p = parts(iso);
    if (!p) {
      el.textContent = "Sportello aperto";
      el.classList.add("open");
      if (card) card.setAttribute("data-scaduto", "0");
      continue;
    }
    var left = daysLeft(iso, start);
    if (left < 0) {
      el.textContent = "Scaduto";
      el.classList.add("exp");
      if (card) card.setAttribute("data-scaduto", "1");
    } else if (left === 0) {
      el.textContent = "Scade oggi";
      el.classList.add("soon");
    } else if (left === 1) {
      el.textContent = "Manca 1 giorno";
      el.classList.add("soon");
    } else {
      el.textContent = "Mancano " + left + " giorni";
      if (left <= 14) el.classList.add("soon");
    }
  }
  var deadlines = document.querySelectorAll("[data-deadline]");
  for (var j = 0; j < deadlines.length; j++) {
    var node = deadlines[j];
    var apreD = node.getAttribute("data-apre") || "";
    var pOpenD = parts(apreD);
    var isoD = node.getAttribute("data-deadline") || "";
    var pD = parts(isoD);
    if (pOpenD && daysLeft(apreD, start) > 0) {
      node.textContent = "Apre il " + itDate(pOpenD);
      continue;
    }
    if (!pD) continue;
    if (daysLeft(isoD, start) < 0) node.textContent = "Scaduto il " + itDate(pD);
    else if (pOpenD) node.textContent = "Aperto fino al " + itDate(pD);
  }
  var list = document.getElementById("elenco");
  if (!list) return;
  var cards = list.querySelectorAll("article.card");
  var expired = [];
  var open = 0;
  for (var k = 0; k < cards.length; k++) {
    var card = cards[k];
    if (card.getAttribute("data-scaduto") === "1") {
      expired.push(card);
      continue;
    }
    var apreCard = card.getAttribute("data-apre") || "";
    if (apreCard && daysLeft(apreCard, start) > 0) continue;
    open++;
  }
  for (var n = 0; n < expired.length; n++) list.appendChild(expired[n]);
  var label = open === 1 ? "1 bando aperto" : open + " bandi aperti";
  var counts = document.querySelectorAll("[data-aperti]");
  for (var c = 0; c < counts.length; c++) counts[c].textContent = label;
  var numeri = document.querySelectorAll("[data-aperti-n]");
  for (var u = 0; u < numeri.length; u++) numeri[u].textContent = String(open);
})();
</script>"""


def ext(url, label, klass=""):
    cls = f' class="{klass}"' if klass else ""
    return (
        f'<a{cls} href="{e(url)}" rel="noopener noreferrer" target="_blank">{label}'
        f'<span class="vh"> (si apre in una nuova scheda)</span></a>'
    )


def mail_link(address=None):
    address = EMAIL if address is None else address
    return f'<a class="mail" href="mailto:{address}">{e(address)}</a>'


def crumbs(items, pre):
    lis = []
    for i, (href, label) in enumerate(items):
        if i == len(items) - 1 or not href:
            lis.append(f'<li aria-current="page">{e(label)}</li>')
        else:
            lis.append(f'<li><a href="{site_href(href)}">{e(label)}</a></li>')
    return f'<nav class="crumb" aria-label="Percorso"><ol>{"".join(lis)}</ol></nav>'


def breadcrumb_ld(items):
    elements = []
    for i, (href, label) in enumerate(items, start=1):
        item = {"@type": "ListItem", "position": i, "name": label}
        if href is not None:
            item["item"] = public_url(href)
        elements.append(item)
    return {"@type": "BreadcrumbList", "itemListElement": elements}


def org_ld():
    return {
        "@type": "Organization",
        "name": SITE,
        "url": BASE,
        "sameAs": [LINKEDIN],
        "logo": BASE + "favicon-512.png",
    }


_CARD_WARNING = re.compile(
    r"senza garanzia di copertura|risorse esaurite|risorse impegnate|"
    r"risorse disponibili(?: sono)? (?:0,00|esaurite)|"
    r"senza ulteriori risorse|disponibilità\s*[−\-]",
    re.I,
)


def _sentences(text):
    return [part.strip() for part in re.split(r"(?<=\.)\s+", text.strip()) if part.strip()]


def stato_bando(b):
    return b.get("stato") or "aperto"


def avviso_fondi(b, con_link=False):
    """Avviso sui fondi esauriti. Il bando resta aperto: non diventa «scaduto»."""
    frase = STATI.get(stato_bando(b)) or ""
    if not frase:
        return ""
    link = ""
    if con_link:
        link = " " + ext(b.get("fonte") or b["url"], "Fonte ufficiale")
    return (
        f'<p class="note" data-avviso="fondi" role="status">'
        f"<strong>{e(frase)}</strong> Verificato il {e(it_date(b['ultimo_controllo']))}.{link}"
        f"</p>"
    )


def fonte_fuori_avviso(b):
    """Link alla fonte del dato, quando non è già dentro l'avviso di lista d'attesa."""
    fonte = b.get("fonte")
    if not fonte or STATI.get(stato_bando(b)):
        return ""
    return (
        f'<p class="fonte">Verificato il {e(it_date(b["ultimo_controllo"]))}. '
        f'{ext(fonte, "Fonte ufficiale")}</p>'
    )


def card_note(b):
    """Frasi dei dati che la sintesi a due righe non mostra sulla card.

    Stesso riquadro delle altre note (classe note): la card non cambia impianto.
    """
    sintesi = " ".join((b.get("sintesi") or "").split())
    nota = " ".join((b.get("nota_scadenza") or "").split())
    importo = b.get("importo") or ""
    visible = f"{importo} {sintesi[:160]}"
    chosen = []

    def add(text):
        text = " ".join(text.split())
        if not text or text in visible:
            return
        if any(text in prev or prev in text for prev in chosen):
            return
        chosen.append(text)

    for sentence in _sentences(sintesi):
        if _CARD_WARNING.search(sentence):
            add(sentence)
        if (
            re.search(r"(?<!\d)40\.000", sentence)
            and re.search(r"(?<!\d)60\.000", sentence)
            and "40.000" not in importo
            and "60.000" not in importo
        ):
            add(sentence)
    # La nota sulla data (30/10 contro 30/11) sta in nota_scadenza, non nella sintesi.
    if "30/10" in nota and "30/11" in nota and "30/11" not in visible:
        add(nota)
    if not chosen:
        return ""
    return f'<p class="note">{e(" ".join(chosen))}</p>'


def card(b, pre, today, mostra_scaduto=False):
    tags = f'<span class="tag area">{e(b["regione"])}</span>'
    tags += "".join(f'<span class="tag">{e(d)}</span>' for d in b["destinatari"])
    note = card_note(b)
    avviso = avviso_fondi(b)
    search_bits = [seo_copy.titolo_in_elenco(b), b["sintesi"], b["ente"], b["regione"], " ".join(b["destinatari"])]
    frase_stato = STATI.get(stato_bando(b)) or ""
    if note or frase_stato:
        search_bits.append(b.get("nota_scadenza") or "")
    if frase_stato:
        search_bits.append(frase_stato)
    search = " ".join(" ".join(search_bits).split())
    # Negli elenchi predefiniti lo scaduto resta nel DOM ma nascosto (c'è «Mostra scaduti»).
    # Sulle pagine delle Camere resta visibile, in fondo alla sezione.
    hidden = "" if mostra_scaduto or not b["scaduto"] else " hidden"
    href = site_href(f'bando/{b["id"]}.html')
    when = f' data-deadline="{b["scadenza"]}"' if b["scadenza"] else ""
    if b.get("apertura"):
        when += f' data-apre="{b["apertura"]}"'
    return (
        f'<article class="card" data-reg="{e(b["regione"])}" '
        f'data-dest="{e("|".join(b["destinatari"]))}" data-scad="{b["scadenza"] or "9999-12-31"}" '
        f'data-apre="{e(b.get("apertura") or "")}" '
        f'data-scaduto="{1 if b["scaduto"] else 0}" data-search="{e(search)}"{hidden}>'
        f'{badge(b, today)}{avviso}<h3><a class="cardlink" href="{href}">{e(seo_copy.titolo_in_elenco(b))}</a></h3>'
        f'<p class="amt">{e(b["importo"])}</p><div class="tags">{tags}</div>'
        f'<p class="sum">{e(b["sintesi"])}</p>{note}<div class="meta"><span class="dl"{when}>{e(deadline_text(b))}</span>'
        f'<span class="ente">{e(b["ente"])}</span></div></article>'
    )


def sponsor_card(pre):
    return (
        '<aside class="card spc" aria-label="Spazio sponsor"><span class="lab">Sponsorizzato</span>'
        '<p class="spt">Il tuo studio qui, tra chi cerca un finanziamento</p>'
        f'<p class="spp">{SPONSOR_DA}</p>'
        f'<a class="btn outline" href="{site_href("sponsor.html")}">Scopri gli spazi sponsor</a></aside>'
    )


def grid(items, pre, today):
    blocks = [card(b, pre, today) for b in items]
    active = [i for i, b in enumerate(items) if not b["scaduto"]]
    pos = active[5] + 1 if len(active) >= 6 else len(blocks)
    blocks.insert(pos, sponsor_card(pre))
    return '<div class="grid" id="elenco">' + "".join(blocks) + "</div>" + BADGE_JS


def official_bando_link(url):
    host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
    if "invitalia" in host.lower():
        host = "sito ufficiale dell'ente gestore"
    return (
        '<div class="official">'
        + ext(url, "Vai al bando ufficiale", "btn")
        + f'<small class="host">{html.escape(host, quote=False)}</small></div>'
    )


def checkup_ask():
    return (
        '<aside class="checkup-ask" aria-labelledby="checkup-scheda">'
        '<h2 id="checkup-scheda">Richiedi il Check-up</h2>'
        "<p>Relazione scritta sui bandi regionali e nazionali adatti alla tua impresa: "
        "Base, circa 3-4 pagine; Completo, 6-10 pagine.</p>"
        f'<p><a class="btn outline" href="{site_href("check-up.html")}">Richiedi il Check-up</a></p>'
        "</aside>"
    )


def bando_checkup_box():
    return (
        '<aside class="bando-checkup" aria-label="Check-up per questo bando">'
        "<p>Documenti da preparare, calendario ed errori da evitare per questo bando: "
        "li verifichiamo per la tua impresa con il "
        f'<a href="{site_href("check-up.html")}">Check-up Bandi</a> '
        "(da 49 €). Verifica di ammissibilità, non garantisce il contributo.</p>"
        f"<p>{CHECKUP_IVA_NOTE}</p>"
        "</aside>"
    )


def checkup_section(pre, con_immagine=False, variante="standard"):
    if variante == "home":
        testo = (
            "<h2 id=\"checkup-title\">Check-up Bandi</h2>"
            "<p>Vuoi sapere quali di questi bandi sono adatti alla tua impresa? "
            "Con il Check-up Bandi ricevi una relazione scritta: Base 49 €, Completo 79 € (prezzi finali).</p>"
            f'<p><a class="btn" href="{site_href("check-up.html")}">Scopri il Check-up Bandi</a></p>'
        )
    else:
        testo = (
            "<h2 id=\"checkup-title\">Check-up Bandi</h2>"
            "<p>Controllo personalizzato di quali bandi regionali e nazionali sono adatti alla tua impresa: "
            "tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), Umbria, Emilia-Romagna e incentivi nazionali "
            "per avviare e far crescere l'impresa, tra cui finanziamenti a tasso zero e contributi a fondo perduto "
            "per nuove imprese, startup innovative e investimenti. Il risultato è una relazione scritta.</p>"
            f'<p><a class="btn" href="{site_href("check-up.html")}">Richiedi il Check-up</a></p>'
        )
    if con_immagine:
        inner = f'<div class="box with-illu"><div>{testo}</div>{sec_img("verifica-ammissibilita", 800, 600)}</div>'
    else:
        inner = f'<div class="box">{testo}</div>'
    return f'<section class="checkup" aria-labelledby="checkup-title">{inner}</section>'


def fpef_box():
    return (
        '<aside class="fpef" aria-label="FoglioPEF, progetto dello stesso titolare">'
        '<p class="lab">Progetto dello stesso titolare</p>'
        '<h2>FoglioPEF</h2>'
        f"<p>{FPEF_DESC}</p>"
        '<p class="row">'
        f'{ext(FPEF, "Apri FoglioPEF", "btn outline")}'
        f'{ext(FPEF_LI, "FoglioPEF su LinkedIn")}'
        '</p></aside>'
    )


def related(b, bandi, n=3):
    scored = []
    for other in bandi:
        if other["id"] == b["id"] or other["scaduto"]:
            continue
        score = (2 if other["regione"] == b["regione"] else 0) + len(set(other["destinatari"]) & set(b["destinatari"]))
        if score:
            scored.append((-score, other["scadenza"] or "9999-12-31", other["id"], other))
    scored.sort()
    return [row[-1] for row in scored[:n]]


def filter_form(bandi):
    dests = sort_dest({d for b in bandi for d in b["destinatari"]})
    areas = "".join(
        f'<option value="{e(x)}">{e("Nazionali" if x == "Nazionale" else x)}</option>' for x in REG
    )
    dest_opts = "".join(f'<option value="{e(x)}">{e(x)}</option>' for x in dests)
    att = conto_aperti(bandi)
    label = "1 bando trovato" if att == 1 else f"{att} bandi trovati"
    return f'''<form id="filtri-form" class="filters" role="search" aria-label="Cerca e filtra i bandi" autocomplete="off">
<div><label for="q">Cerca</label><input id="q" name="q" type="search" placeholder="Titolo, ente o parola chiave" enterkeyhint="search"></div>
<div><label for="r">Area</label><select id="r" name="area"><option value="">Tutte le aree</option>{areas}</select></div>
<div><label for="d">Destinatari</label><select id="d" name="dest"><option value="">Tutti i destinatari</option>{dest_opts}</select></div>
<div><label for="s">Scadenza</label><select id="s" name="scadenza"><option value="">Qualsiasi scadenza</option><option value="30">Entro 30 giorni</option><option value="90">Entro 90 giorni</option><option value="none">Senza scadenza fissa</option></select></div>
<div class="fbar"><p class="count" id="n" aria-live="polite" aria-atomic="true">{label}</p><label class="chk"><input type="checkbox" id="x" name="scaduti"> Mostra scaduti</label><button type="button" class="link" id="z">Azzera filtri</button></div>
</form>'''


JS = r"""<script>
(function () {
  var form = document.getElementById("filtri-form");
  if (!form) return;
  var area = document.getElementById("r");
  var dest = document.getElementById("d");
  var scad = document.getElementById("s");
  var q = document.getElementById("q");
  var expired = document.getElementById("x");
  var count = document.getElementById("n");
  var reset = document.getElementById("z");
  var cards = Array.prototype.slice.call(document.querySelectorAll("#elenco .card:not(.spc)"));
  function hasOption(sel, value) {
    if (!value) return false;
    for (var i = 0; i < sel.options.length; i++) if (sel.options[i].value === value) return true;
    return false;
  }
  function daysUntil(iso) {
    var p = iso.split("-");
    if (p.length !== 3 || iso.indexOf("9999") === 0) return 99999;
    var target = new Date(+p[0], +p[1] - 1, +p[2]);
    var now = new Date();
    var start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return Math.round((target - start) / 864e5);
  }
  function shownByDefault(card) {
    return card.getAttribute("data-scaduto") !== "1";
  }
  function isOpen(card) {
    if (!shownByDefault(card)) return false;
    var apre = card.getAttribute("data-apre") || "";
    if (apre && daysUntil(apre) > 0) return false;
    return true;
  }
  function syncHero() {
    var n = 0;
    for (var i = 0; i < cards.length; i++) if (isOpen(cards[i])) n++;
    var label = n === 1 ? "1 bando aperto" : n + " bandi aperti";
    var nodes = document.querySelectorAll(".hero [data-aperti]");
    for (var c = 0; c < nodes.length; c++) nodes[c].textContent = label;
  }
  function readUrl() {
    var params = new URLSearchParams(location.search);
    if (hasOption(area, params.get("area") || "")) area.value = params.get("area");
    if (hasOption(dest, params.get("dest") || "")) dest.value = params.get("dest");
    if (hasOption(scad, params.get("scadenza") || "")) scad.value = params.get("scadenza");
    if (params.get("q")) q.value = params.get("q");
    if (params.get("scaduti") === "1") expired.checked = true;
  }
  function writeUrl() {
    var params = new URLSearchParams();
    if (area.value) params.set("area", area.value);
    if (dest.value) params.set("dest", dest.value);
    if (scad.value) params.set("scadenza", scad.value);
    if (q.value.trim()) params.set("q", q.value.trim());
    if (expired.checked) params.set("scaduti", "1");
    var qs = params.toString();
    try { history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash); } catch (err) {}
  }
  function apply() {
    var text = q.value.trim().toLowerCase();
    var visible = [];
    cards.forEach(function (card) {
      var ok = expired.checked || shownByDefault(card);
      if (area.value && card.getAttribute("data-reg") !== area.value) ok = false;
      if (dest.value && (card.getAttribute("data-dest") || "").split("|").indexOf(dest.value) === -1) ok = false;
      var iso = card.getAttribute("data-scad") || "";
      if (scad.value === "none") ok = ok && iso.indexOf("9999") === 0;
      else if (scad.value) {
        var left = daysUntil(iso);
        ok = ok && iso.indexOf("9999") !== 0 && left >= 0 && left <= +scad.value;
      }
      if (text && (card.getAttribute("data-search") || "").toLowerCase().indexOf(text) === -1) ok = false;
      card.hidden = !ok;
      if (ok) visible.push(card);
    });
    var sponsor = document.querySelector("#elenco .spc");
    if (sponsor) {
      if (!visible.length) sponsor.hidden = true;
      else {
        sponsor.hidden = false;
        visible[Math.min(5, visible.length - 1)].after(sponsor);
      }
    }
    var n = 0;
    for (var v = 0; v < visible.length; v++) if (isOpen(visible[v])) n++;
    var label = visible.length === 0 ? "Nessun bando con questi filtri. Modifica la ricerca o mostra gli scaduti." : (n === 1 ? "1 bando trovato" : n + " bandi trovati");
    if (count.textContent !== label) count.textContent = label;
  }
  readUrl();
  apply();
  syncHero();
  [area, dest, scad, expired].forEach(function (el) {
    el.addEventListener("change", function () { apply(); writeUrl(); });
  });
  q.addEventListener("input", function () { apply(); writeUrl(); });
  form.addEventListener("submit", function (ev) { ev.preventDefault(); apply(); writeUrl(); });
  reset.addEventListener("click", function () {
    area.value = ""; dest.value = ""; scad.value = ""; q.value = ""; expired.checked = false;
    apply(); writeUrl();
  });
})();
</script>"""


def pills(links):
    lis = []
    for href, label, num in links:
        count = f'<span class="num">{num}</span>' if num is not None else ""
        lis.append(f'<li><a href="{href}">{e(label)}{count}</a></li>')
    return f'<ul class="pills">{"".join(lis)}</ul>'


def area_links(bandi, pre, current=None):
    out = []
    for reg in REG:
        if reg == current:
            continue
        n = sum(1 for b in bandi if b["regione"] == reg and not b["scaduto"])
        out.append((site_href(region_path(reg)), "Nazionali" if reg == "Nazionale" else reg, n))
    return out


def dest_links(bandi, pre, current=None):
    names = sort_dest({d for b in bandi for d in b["destinatari"]})
    out = []
    for name in names:
        if name == current:
            continue
        n = sum(1 for b in bandi if name in b["destinatari"] and not b["scaduto"])
        out.append((site_href(sector_path(name)), name, n))
    return out


def hubs(bandi, pre):
    return (
        '<section aria-labelledby="aree-title"><h2 id="aree-title">Bandi per area</h2>'
        + sec_img("bandi-per-area", 800, 308)
        + pills(area_links(bandi, pre))
        + '</section><section aria-labelledby="dest-title"><h2 id="dest-title">Bandi per destinatario</h2>'
        + '<div class="with-illu"><div>'
        + pills(dest_links(bandi, pre))
        + "</div>"
        + sec_img("bandi-per-destinatario", 800, 600)
        + "</div></section>"
    )


def faq_html(pairs=None, raw=False):
    """pairs: (domanda, risposta). Con raw=False la risposta è testo e viene escapata."""
    if pairs is None:
        pairs = FAQ
        raw = False
    blocks = []
    for q, a in pairs:
        answer = a if raw else e(a)
        blocks.append(f"<details><summary>{e(q)}</summary><p>{answer}</p></details>")
    return '<section class="faq" aria-labelledby="faq-title"><h2 id="faq-title">Domande frequenti</h2>' + "".join(blocks) + "</section>"


def faq_ld(pairs):
    """pairs con risposta già in testo semplice, senza markup."""
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in pairs
        ],
    }


def link_verifica():
    return f'<a href="{site_href("check-up.html")}">verifica scritta dei bandi adatti alla tua impresa</a>'


def head_icons(pre):
    """Favicon del marchio A: SVG, PNG 16/32/48/512 e apple-touch da 180."""
    icons = (
        ("icon", "favicon.svg", ' type="image/svg+xml"'),
        ("icon", "favicon-48.png", ' type="image/png" sizes="48x48"'),
        ("icon", "favicon-32.png", ' type="image/png" sizes="32x32"'),
        ("icon", "favicon-16.png", ' type="image/png" sizes="16x16"'),
        ("apple-touch-icon", "apple-touch-icon.png", ' sizes="180x180"'),
        ("icon", "favicon-512.png", ' type="image/png" sizes="512x512"'),
    )
    return "\n".join(
        f'<link rel="{rel}" href="{pre}{name}"{extra}>' for rel, name, extra in icons
    )


def hero_picture(stem):
    """Hero above-the-fold: niente lazy, srcset 800w e ritaglio 4:3 sotto i 640 px."""
    alt = e(ALT[stem])
    return (
        "<picture>"
        f'<source media="(max-width: 640px)" srcset="{IMG}/{stem}-mobile.webp" width="800" height="600">'
        f'<img src="{IMG}/{stem}.webp" '
        f'srcset="{IMG}/{stem}-800.webp 800w, {IMG}/{stem}.webp 1280w" '
        f'sizes="(min-width: 900px) 560px, 100vw" '
        f'width="1280" height="720" alt="{alt}" '
        'fetchpriority="high" loading="eager" decoding="async" class="hero-img">'
        "</picture>"
    )


def hero_block(stem, copy):
    return (
        '<section class="hero"><div class="wrap">'
        f'<div class="hero-copy">{copy}</div>{hero_picture(stem)}</div></section>'
    )


def hero_home_preload():
    return (
        f'<link rel="preload" as="image" href="{IMG}/hero-home.webp" '
        f'imagesrcset="{IMG}/hero-home-800.webp 800w, {IMG}/hero-home.webp 1280w" '
        'imagesizes="(min-width: 900px) 560px, 100vw" fetchpriority="high">\n'
    )


def sec_img(name, width, height):
    """Illustrazione sotto la piega: lazy, dimensioni esplicite, niente shift."""
    return (
        f'<img src="{IMG}/{name}.webp" width="{width}" height="{height}" '
        f'alt="{e(ALT[name])}" loading="lazy" decoding="async" class="sec-img">'
    )


def brand_link(pre):
    """Wordmark di testata: SVG del marchio A, PNG 80/160 come fallback."""
    return (
        f'<a class="brand" href="{site_href("index.html")}">'
        f"<picture>"
        f'<source srcset="{pre}logo-header.svg" type="image/svg+xml">'
        f'<img src="{pre}logo-header-80.png" '
        f'srcset="{pre}logo-header-80.png 1x, {pre}logo-header-160.png 2x" '
        f'alt="IncentiviPerTe" width="222" height="40">'
        f"</picture></a>"
    )


def page(path, title, desc, body, hero="", ld=None, robots=None, extra_head="", title_as_is=False):
    pre = prefix(path)
    # /check-up-bandi è solo un rimando: canonical e social puntano alla pagina vera.
    url = public_url("check-up.html") if path == "check-up-bandi.html" else public_url(path)
    # title_as_is: il documento fissa già il title intero (schede entro 60 caratteri, senza il marchio).
    full = title if path == "index.html" or title_as_is else f"{title} – {SITE}"
    nav_items = []
    for href, label, kind in NAV:
        cls = f' class="{kind}"' if kind else ""
        current = ' aria-current="page"' if href == path or (path == "check-up-bandi.html" and href == "check-up.html") else ""
        nav_items.append(f'<li{cls}><a{cls} href="{site_href(href)}"{current}>{label}</a></li>')
    nav = "".join(nav_items)
    cta_current = ' aria-current="page"' if path in ("check-up.html", "check-up-bandi.html") else ""
    refresh = '<meta http-equiv="refresh" content="0; url=/check-up">' if path == "check-up-bandi.html" else ""
    ld_html = ""
    if ld:
        raw = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
        ld_html = f'<script type="application/ld+json">{raw}</script>'
    robots_html = f'<meta name="robots" content="{e(robots)}">' if robots else ""
    canon = "" if robots and "noindex" in robots else f'<link rel="canonical" href="{e(url)}">'
    alt = "" if robots and "noindex" in robots else (
        f'<link rel="alternate" hreflang="it" href="{e(url)}">'
        f'<link rel="alternate" hreflang="x-default" href="{e(url)}">'
    )
    desc_e, full_e = e(desc), e(full)
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{full_e}</title>
<meta name="description" content="{desc_e}">
<meta name="google-site-verification" content="{GSC_TOKEN}" />
{refresh}{robots_html}{canon}{alt}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE}">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="{full_e}">
<meta property="og:description" content="{desc_e}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{BASE}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="IncentiviPerTe – Bandi e incentivi per la tua impresa">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{full_e}">
<meta name="twitter:description" content="{desc_e}">
<meta name="twitter:image" content="{BASE}og.png">
<meta name="theme-color" content="#0F7A5C">
{head_icons(pre)}
<link rel="stylesheet" href="{pre}style.css">
{extra_head}{ld_html}
</head>
<body>
<a class="skip" href="#main">Vai al contenuto</a>
<header class="top"><div class="wrap bar">
{brand_link(pre)}
<nav class="dnav" aria-label="Principale"><ul>{nav}</ul></nav>
<a class="btn head-cta" href="{site_href("check-up.html")}"{cta_current}>Check-up</a>
<details class="menu"><summary><span class="when-closed">Menu</span><span class="when-open">Chiudi</span></summary>
<nav aria-label="Menu"><ul>{nav}</ul></nav></details>
</div></header>
<main id="main" tabindex="-1">{hero}<div class="wrap">{body}</div></main>
{footer(pre)}
</body>
</html>
"""


def footer(pre):
    # I link di area e destinatario sono aggiunti dopo, quando i bandi sono noti.
    info = (
        ("chi-siamo.html", "Chi siamo"),
        ("contatti.html", "Contatti"),
        ("sponsor.html", "Sponsor"),
        ("disclaimer.html", "Disclaimer"),
        ("privacy.html", "Privacy"),
        ("cookie.html", "Cookie policy"),
        ("note-legali.html", "Note legali"),
    )
    links = "".join(f'<li><a href="{site_href(href)}">{label}</a></li>' for href, label in info)
    guide = ""
    if GUIDE:
        voci = "".join(f'<li><a href="{site_href(href)}">{e(label)}</a></li>' for href, label in GUIDE)
        guide = f'<nav aria-label="Guide"><p><strong>Guide</strong></p><ul>{voci}</ul></nav>\n'
    return f"""<footer><div class="wrap">
<p><strong>{SITE}</strong> · raccolta gratuita e indipendente di bandi per startup e PMI, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali. Le schede sono sintesi: fa fede solo il bando ufficiale.</p>
<nav aria-label="Aree"><p><strong>Aree</strong></p><ul id="foot-aree"></ul></nav>
<nav aria-label="Destinatari"><p><strong>Destinatari</strong></p><ul id="foot-dest"></ul></nav>
{guide}<nav aria-label="Informazioni"><ul>{links}</ul></nav>
<p>Strumento dello stesso titolare: {FPEF_DESC.replace("FoglioPEF", ext(FPEF, "FoglioPEF"), 1)} ({ext(FPEF_LI, "LinkedIn")}). Contatti: {ext(LINKEDIN, "messaggi della Pagina LinkedIn IncentiviPerTe")} o {mail_link()}. Nessun cookie, nessun tracker.</p>
</div></footer>"""


def fill_footer(html_text, bandi, pre):
    aree = "".join(
        f'<li><a href="{href}">{e(label)}</a></li>' for href, label, _n in area_links(bandi, pre)
    )
    dest = "".join(
        f'<li><a href="{href}">{e(label)}</a></li>' for href, label, _n in dest_links(bandi, pre)
    )
    return html_text.replace('<ul id="foot-aree"></ul>', f"<ul>{aree}</ul>", 1).replace(
        '<ul id="foot-dest"></ul>', f"<ul>{dest}</ul>", 1
    )


CSS = """:root{--b:#0F7A5C;--bd:#0A5A44;--t:#14213D;--m:#3d4a5c;--bg:#f4f6fa;--l:#dde3ec;--ok:#0b5a2d}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--t);background:var(--bg)}
h1,h2,h3,p,li,dd{overflow-wrap:break-word}
h1{font-size:clamp(1.6rem,3vw,2rem);line-height:1.2;margin:0 0 12px}
h2{font-size:1.3rem;line-height:1.3;margin:28px 0 10px}
a{color:var(--b);text-underline-offset:2px}
a:hover{color:var(--bd)}
:focus-visible{outline:3px solid #fff;outline-offset:2px;box-shadow:0 0 0 6px #0A5A44}
.skip{position:absolute;left:8px;top:8px;transform:translateY(-160%);background:#fff;color:var(--t);padding:10px 12px;z-index:20;border-radius:8px;font-weight:700}
.skip:focus{transform:none}
.vh{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.wrap{max-width:1040px;margin:auto;padding:0 max(16px,env(safe-area-inset-right)) 0 max(16px,env(safe-area-inset-left))}
header .wrap{max-width:1180px}
header.top{background:#fff;border-bottom:1px solid var(--l);position:sticky;top:0;z-index:5}
.bar{display:flex;align-items:center;justify-content:space-between;min-height:64px;gap:12px;position:relative}
.brand{display:flex;align-items:center;min-height:44px;min-width:0;color:var(--t);text-decoration:none}
.brand picture{display:block;min-width:0;max-width:100%}
.brand img{display:block;height:auto;max-height:40px;width:auto;max-width:min(222px,100%)}
@media(max-width:1179px){.brand{flex:1 1 auto}}
nav ul{list-style:none;margin:0;padding:0;display:flex;gap:2px;flex-wrap:wrap}
nav a{display:flex;align-items:center;min-height:44px;padding:8px;border-radius:8px;text-decoration:none;color:var(--t);font-weight:700;font-size:15px}
.dnav ul{flex-wrap:nowrap;width:100%;align-items:center}
.dnav li.cta{margin-left:auto}
nav a.cta,a.head-cta{background:var(--b);color:#fff;border-radius:10px}
nav a.cta:hover,nav a.cta[aria-current="page"],a.head-cta:hover,a.head-cta[aria-current="page"]{background:var(--bd);color:#fff}
.head-cta{margin-left:auto;flex:0 0 auto}
nav a:hover,nav a[aria-current="page"]{background:#E7F4EE;color:var(--b)}
.dnav{display:none}
details.menu summary{list-style:none;cursor:pointer;min-height:44px;min-width:44px;display:flex;align-items:center;padding:8px 12px;border:1px solid #5c6b82;border-radius:8px;font-weight:800;background:#fff}
details.menu summary::-webkit-details-marker{display:none}
details.menu .when-open{display:none}
details.menu[open] .when-closed{display:none}
details.menu[open] .when-open{display:inline}
details.menu[open] summary{border-color:var(--b);color:var(--b)}
details.menu nav{position:absolute;z-index:6;left:0;right:0;top:100%;background:#fff;border:1px solid var(--l);border-radius:12px;padding:8px;box-shadow:0 8px 24px #0002;max-height:min(70vh,520px);overflow:auto}
details.menu nav ul{flex-direction:column}
@media(min-width:1180px){.dnav{display:flex;flex:1;min-width:0}details.menu{display:none}a.btn.head-cta{display:none}}
.hero{background:linear-gradient(135deg,#0A5A44,#0F7A5C);color:#fff;padding:36px 0 32px}
.hero h1{font-size:clamp(1.7rem,4.5vw,2.5rem);line-height:1.15;margin:0 0 10px;color:#fff}
.hero p{margin:0;color:#fff;max-width:42rem}
.hero .upd{margin-top:8px;font-weight:700}
.hero-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}
.hero .wrap{display:grid;gap:18px 28px;align-items:center}
.hero-copy{min-width:0}
.hero picture{display:block;min-width:0;max-width:100%}
.hero-img,.sec-img{display:block;max-width:100%;height:auto}
.hero-img{width:100%;aspect-ratio:16/9}
@media(max-width:640px){.hero-img{aspect-ratio:4/3}}
@media(min-width:900px){.hero .wrap{grid-template-columns:minmax(0,1.05fr) minmax(220px,560px);max-width:1180px}}
.sec-img{border-radius:14px;margin:12px 0}
.with-illu{display:grid;gap:12px 20px;align-items:center}
.with-illu>.sec-img{margin:0}
@media(min-width:800px){.with-illu{grid-template-columns:minmax(0,1fr) minmax(180px,360px)}.with-illu>.sec-img{max-width:360px;justify-self:end}}
.paga .with-illu{grid-template-columns:minmax(0,1fr)}
.paga .with-illu>.sec-img{max-width:min(100%,360px);justify-self:start}
main{padding:0 0 40px}
main:focus{outline:none}
main>.wrap{padding-top:20px}
.note{background:#fff8e6;border:1px solid #c4922a;border-radius:10px;padding:12px 14px;margin:16px 0}
.note[data-avviso]{border-width:2px}
.card .note[data-avviso]{margin:8px 0 12px}
.fonte{margin:8px 0 16px}
.filters{display:grid;gap:12px;grid-template-columns:1fr;background:#fff;border:1px solid var(--l);border-radius:12px;padding:14px;margin:16px 0}
.filters label{font-size:13px;font-weight:800;color:var(--m);display:block;margin:0 0 4px}
.filters select,.filters input[type="search"]{width:100%;min-height:44px;padding:8px 10px;border:1px solid #5c6b82;border-radius:8px;font:inherit;font-size:16px;background:#fff;color:var(--t)}
.fbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;grid-column:1/-1}
.fbar .count{margin:0;font-weight:800}
.chk{font-size:16px;font-weight:700;color:var(--t);display:flex;gap:8px;align-items:center;min-height:44px;margin:0}
.chk input{width:1.15rem;height:1.15rem}
button.link{background:none;border:0;padding:8px 0;min-height:44px;font:inherit;font-weight:800;color:var(--b);text-decoration:underline;cursor:pointer}
@media(min-width:700px){.filters{grid-template-columns:1fr 1fr}}
@media(min-width:1000px){.filters{grid-template-columns:1.3fr 1fr 1fr 1fr;position:sticky;top:72px;z-index:4;box-shadow:0 4px 16px #0001}}
#filtri{scroll-margin-top:88px}
.grid{display:grid;gap:14px;grid-template-columns:minmax(0,1fr)}
@media(min-width:700px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:1000px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
.card{background:#fff;border:1px solid var(--l);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column;position:relative;min-width:0}
.card[hidden]{display:none !important}
.card h3{font-size:1.15rem;margin:8px 0;line-height:1.3}
.card h3 a{display:inline-flex;align-items:center;min-height:44px;text-decoration:underline;text-underline-offset:3px}
.card h3 a::after{content:"";position:absolute;inset:0}
.amt{font-weight:800;margin:0 0 8px;min-width:0;overflow-wrap:anywhere}
.sum{margin:0 0 10px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{margin-top:auto;display:flex;flex-direction:column;gap:4px;border-top:1px solid var(--l);padding-top:10px;font-size:14px;color:var(--m)}
.ente{color:var(--m)}
.dl{font-weight:800;color:var(--t)}
.more{font-weight:800;margin-top:4px}
.badge{align-self:flex-start;font-size:13px;font-weight:800;border-radius:999px;padding:4px 10px;background:#e7f6ec;color:var(--ok)}
.badge.soon{background:#fde8e7;color:#9b1c1c}
.badge.exp{background:#eceff3;color:#243044}
.badge.open{background:#E7F4EE;color:var(--bd)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px}
.tag{display:inline-flex;align-items:center;min-height:32px;background:#fff;color:var(--bd);border:1px solid var(--b);border-radius:999px;padding:2px 10px;font-size:13px;font-weight:800;text-decoration:none}
a.tag:hover{background:#E7F4EE}
.tag.area{background:var(--b);color:#fff;border-color:var(--b)}
a.tag.area:hover{background:var(--bd);color:#fff}
.card .tag{background:#E7F4EE;border:0;color:var(--bd)}
.spc{border:2px dashed #8b95a5;background:#f8fafc}
.spt{font-size:1.05rem;font-weight:800;margin:8px 0}
.spp{font-weight:800;color:var(--b);margin:0 0 8px}
.lab{display:inline-block;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:#e8edf3;color:#243044;border-radius:6px;padding:3px 8px}
.checkup{margin:22px 0}
.checkup h2{margin-top:0}
.fpef{background:#F4FAF7;border:2px solid var(--b);border-radius:14px;padding:16px 18px;margin:22px 0}
.fpef h2,.offer h3{margin-top:0}
.fpef .row,.hero-actions{align-items:center}
.fpef .row{display:flex;flex-wrap:wrap;gap:12px 16px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;background:var(--b);color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font:inherit;font-weight:800;border:0;cursor:pointer}
.btn:hover{background:var(--bd);color:#fff}
.btn.outline{background:transparent;color:var(--b);border:2px solid var(--b)}
.btn.outline:hover{background:#E7F4EE;color:var(--bd)}
.hero .btn{background:#fff;color:var(--bd)}
.hero .btn:hover{background:#E7F4EE;color:var(--bd)}
.btn.ghost,.hero .btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
.btn.ghost:hover,.hero .btn.ghost:hover{background:#fff;color:var(--bd)}
.pills{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:8px 0 0}
.pills a{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:8px 12px;background:#fff;border:1px solid #5c6b82;border-radius:999px;text-decoration:none;font-weight:800;color:var(--t)}
.pills a:hover{border-color:var(--b);color:var(--b)}
.num{background:#E7F4EE;color:var(--bd);border-radius:999px;min-width:1.6rem;text-align:center;padding:0 8px;font-size:13px}
.faq details{background:#fff;border:1px solid var(--l);border-radius:12px;padding:4px 14px;margin:8px 0}
.faq summary{cursor:pointer;font-weight:800;min-height:44px;display:flex;align-items:center}
.box{background:#fff;border:1px solid var(--l);border-radius:14px;padding:18px}
.official{display:flex;flex-direction:column;align-items:flex-start;gap:2px;margin:12px 0}
.official small{color:var(--m);font-size:13px;line-height:1.3}
.checkup-ask{background:#F4FAF7;border:1px solid var(--b);border-radius:14px;padding:16px 18px;margin:18px 0}
.checkup-ask h2{margin-top:0}
.bando-checkup{background:#F4FAF7;border:1px solid var(--b);border-radius:14px;padding:12px 14px;margin:12px 0}
.bando-checkup p{margin:0}
.bando-checkup p+p{margin-top:8px}
dl.kv{display:grid;grid-template-columns:minmax(8rem,max-content) 1fr;gap:8px 16px;margin:12px 0}
dl.kv dt{font-weight:800;color:var(--m)}
dl.kv dd{margin:0}
@media(max-width:560px){dl.kv{grid-template-columns:1fr;gap:2px}dl.kv dt{margin-top:10px}dl.kv dt:first-child{margin-top:0}}
nav.crumb{font-size:15px;margin:0 0 12px}
nav.crumb ol{display:flex;flex-wrap:wrap;gap:4px 0;list-style:none;padding:0;margin:0}
nav.crumb li{display:inline-flex;align-items:center;min-height:44px}
nav.crumb li+li::before{content:"›";color:var(--m);margin:0 6px}
.related ul{list-style:none;padding:0;margin:0;display:grid;gap:8px}
.related a{display:block;padding:12px 14px;background:#fff;border:1px solid var(--l);border-radius:12px;text-decoration:none;min-height:44px}
.related a:hover{border-color:var(--b)}
.related span{display:block;font-weight:400;color:var(--m);font-size:14px}
.offers{display:grid;gap:12px;margin:12px 0}
@media(min-width:800px){.offers{grid-template-columns:repeat(3,1fr);align-items:stretch}}
.promo{border:2px dashed var(--b);border-radius:14px;padding:16px 18px;background:#F4FAF7;margin:18px 0}
.promo p{margin:8px 0 0}
.promo p:first-child{margin-top:0}
.promo .code{font-size:1.25rem;font-weight:800;letter-spacing:.04em;color:var(--bd)}
.offer{border:2px solid #5c6b82;border-radius:14px;padding:16px;background:#fff;display:flex;flex-direction:column;gap:8px}
.offer.featured{border-color:var(--b);background:#F4FAF7}
.price{font-size:18px;margin:0}
.price strong{font-size:34px;color:var(--b);line-height:1.1}
.launch{font-weight:800;color:#9b1c1c;margin:0}
.offer .fine{color:var(--m);font-size:15px;margin:0}
.offer .btn{margin-top:auto}
.contact-links{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center}
.contact-links a.mail{display:inline-flex;align-items:center;min-height:44px;font-weight:800;overflow-wrap:anywhere}
.contact-links .for{display:inline-flex;flex-wrap:wrap;align-items:center;gap:4px 6px;min-height:44px}
.offer .contact-links{margin-top:auto;flex-direction:column;align-items:flex-start;gap:8px}
.offer .contact-links .btn{margin-top:0}
.sp{border:2px dashed #5c6b82;border-radius:14px;padding:16px;background:#f8fafc;margin:18px 0}
footer{background:#111827;color:#e5e7eb;font-size:15px;padding:28px 0}
footer a{color:#fff}
footer ul{list-style:none;padding:0;margin:4px 0 0;display:flex;flex-wrap:wrap;gap:0 14px}
footer li a{min-height:44px;display:inline-flex;align-items:center}
footer p{margin:10px 0}
footer nav{margin-top:8px}
@media(max-width:600px){
  .hero{padding:28px 0 24px}
  .hero-actions{flex-direction:column;align-items:stretch}
  .hero-actions .btn,.spc .btn,.offer .btn{width:100%}
  footer ul{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}
}
.checkup-form{display:grid;gap:12px;margin-top:16px}
.checkup-form label,.checkup-form legend{font-weight:800}
.checkup-form label{display:block;margin:0 0 4px}
.checkup-form input[type="text"],.checkup-form input:not([type]),.checkup-form select,.checkup-form textarea{width:100%;min-height:44px;padding:8px 10px;border:1px solid #5c6b82;border-radius:8px;font:inherit;font-size:16px;background:#fff;color:var(--t)}
.checkup-form textarea{min-height:8rem}
#checkup-fallback{display:grid;gap:8px;margin-top:12px}
#checkup-fallback[hidden]{display:none}
.checkup-form fieldset{border:1px solid var(--l);border-radius:12px;margin:0;padding:8px 12px 12px}
.checkup-form legend{padding:0 4px}
.livelli{display:flex;flex-wrap:wrap;gap:8px 16px}
.livelli label{display:flex;align-items:center;gap:8px;min-height:44px;margin:0;font-weight:700}
.checkup-split{display:grid;gap:18px;align-items:start}
@media(min-width:900px){.checkup-split{grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr)}}
.paga{background:#F4FAF7;border:1px solid var(--b);border-radius:14px;padding:16px 18px}
.paga h2{margin-top:0}
.pay-level{background:#fff;border:1px solid var(--l);border-radius:12px;padding:12px 14px;margin:12px 0}
.pay-level h3{margin:0 0 4px;font-size:1.05rem}
.pay-amt{font-weight:800;color:var(--b);margin:0}
.pay-actions{display:flex;flex-wrap:wrap;gap:12px 20px}
.pay-choice{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.pay-actions .btn{text-align:center}
@media(max-width:600px){.pay-actions{flex-direction:column;align-items:stretch}.pay-choice{align-items:stretch}.pay-actions .btn{width:100%}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def checkup_service():
    return {
        "@type": "Service",
        "name": "Check-up Bandi",
        "serviceType": "Relazione scritta sui bandi adatti all'impresa",
        "description": (
            "Relazione scritta sui bandi adatti all'impresa. "
            f"Base, 49 €: {CHECKUP_BASE}. Completo, 79 €: {CHECKUP_COMPLETO}. "
            f"{CHECKUP_IVA_NOTE}"
        ),
        "url": public_url("check-up.html"),
        "provider": org_ld(),
        "offers": [
            {
                "@type": "Offer",
                "name": "Base",
                "price": "49",
                "priceCurrency": "EUR",
                "description": f"Base, 49 €: {CHECKUP_BASE}. {CHECKUP_IVA_NOTE}",
            },
            {
                "@type": "Offer",
                "name": "Completo",
                "price": "79",
                "priceCurrency": "EUR",
                "description": f"Completo, 79 €: {CHECKUP_COMPLETO}. {CHECKUP_IVA_NOTE}",
            },
        ],
    }


def unexpected_gumroad(text, allow_products):
    """Vero se resta un rimando Gumroad oltre i due prodotti del Check-up."""
    cleaned = text
    if allow_products:
        for url in (GUMROAD_CHECKUP_BASE_URL, GUMROAD_CHECKUP_COMPLETO_URL):
            cleaned = cleaned.replace(url, "")
    return "gumroad.com" in cleaned.lower()


def mailto_href(subject, body):
    query = urllib.parse.urlencode(
        {"subject": subject, "body": body},
        quote_via=urllib.parse.quote,
    )
    return f"mailto:{EMAIL}?{query}"


def bonifico_link(level, product, price, today):
    subject = f"Richiesta Check-up {level} – pagamento con bonifico istantaneo"
    body = (
        f"Livello: {level}\n"
        f"Prodotto: {product}\n"
        f"Importo: {price}\n"
    )
    if lancio_attivo(today):
        body += "Codice di lancio: LANCIO15\n"
    return f'<a class="btn" href="{e(mailto_href(subject, body))}">Bonifico istantaneo</a>'


def card_pay_link(url):
    """Link al prodotto Gumroad. URL vuoto: nessun pulsante, così non si apre una pagina rotta."""
    url = (url or "").strip()
    prefix = "https://fogliopef.gumroad.com/l/"
    if not url:
        return ""
    if not url.startswith(prefix) or len(url) <= len(prefix):
        raise ValueError("URL prodotto Gumroad del Check-up non valido")
    return ext(url, CARD_PAY_LABEL, "btn outline")


def pay_choice(link_html, amount):
    return (
        '<div class="pay-choice">'
        f"{link_html}"
        f'<span class="pay-amt">{e(amount)}</span>'
        "</div>"
    )


def pay_level(product, price, level, url, today):
    final = f"{price} (prezzo finale, nessuna IVA aggiunta)"
    return (
        '<div class="pay-level">'
        f"<h3>{e(product)}</h3>"
        '<div class="pay-actions">'
        f"{pay_choice(bonifico_link(level, product, price, today), final)}"
        f"{pay_choice(card_pay_link(url), price)}"
        "</div></div>"
    )


def checkup_pay_section(today):
    return (
        '<section class="paga" aria-labelledby="paga-ora">'
        '<h2 id="paga-ora">Paga ora</h2>'
        '<div class="with-illu"><div>'
        "<p>Il Check-up è una verifica di ammissibilità e non garantisce l'ottenimento del contributo.</p>"
        f"<p>{CHECKUP_IVA_NOTE}</p>"
        "</div>"
        + sec_img("verifica-ammissibilita", 800, 600)
        + "</div>"
        + pay_level(CHECKUP_PRODUCT_BASE, "49 €", "Base", GUMROAD_CHECKUP_BASE_URL, today)
        + pay_level(CHECKUP_PRODUCT_COMPLETO, "79 €", "Completo", GUMROAD_CHECKUP_COMPLETO_URL, today)
        + "<p>Bonifico istantaneo: l'IBAN non è pubblicato sul sito. "
        + f"Dopo la richiesta lo inviamo per email da {mail_link()}.</p>"
        + "</section>"
    )


def checkup_faq():
    """Solo ciò che la pagina Check-up dice già. Niente presentazione della domanda."""
    extra = ", ".join(CHECKUP_EXTRA[:-1]) + " e " + CHECKUP_EXTRA[-1]
    return (
        (
            "Che cos'è il Check-up Bandi?",
            "Una relazione scritta che indica quali bandi regionali, camerali e nazionali aperti sono adatti alla tua impresa.",
        ),
        (
            "Quanto costa?",
            "Base 49 €, Completo 79 €. Sono prezzi finali.",
        ),
        (
            "Cosa cambia tra Base e Completo?",
            "Il Completo aggiunge " + extra + ".",
        ),
        (
            "Quali territori copre?",
            "Tutta la Toscana (Regione e Camere di Commercio toscane), Umbria, Emilia-Romagna e gli incentivi nazionali.",
        ),
        (
            "In quanto tempo ricevo la relazione?",
            "Base entro 5 giorni lavorativi, Completo entro 7-10 giorni lavorativi, dalla ricezione dei dati completi.",
        ),
        (
            "Come si paga?",
            "Con carta su Gumroad oppure con bonifico istantaneo; l'IBAN viene inviato per email dopo la richiesta.",
        ),
    )


LANCIO_JS = r"""<script>
(function () {
  var ultimo = new Date(2026, 9, 30);
  var now = window.INCENTIVI_OGGI ? new Date(window.INCENTIVI_OGGI) : new Date();
  var start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  if (start <= ultimo) return;
  var promo = document.querySelector("aside.promo");
  if (promo && promo.parentNode) promo.parentNode.removeChild(promo);
  var links = document.querySelectorAll("a[href]");
  for (var i = 0; i < links.length; i++) {
    var href = links[i].getAttribute("href") || "";
    if (href.indexOf("LANCIO15") === -1) continue;
    var q = href.split("?");
    if (q.length < 2) continue;
    var params = q[1].split("&");
    var out = [];
    for (var p = 0; p < params.length; p++) {
      var kv = params[p].split("=");
      var key = decodeURIComponent((kv[0] || "").replace(/\+/g, " "));
      var val = decodeURIComponent((kv.slice(1).join("=") || "").replace(/\+/g, " "));
      if (key === "body") {
        val = val.split("\n").filter(function (line) {
          return line.indexOf("LANCIO15") === -1;
        }).join("\n");
      }
      out.push(encodeURIComponent(key) + "=" + encodeURIComponent(val));
    }
    links[i].setAttribute("href", q[0] + "?" + out.join("&"));
  }
})();
</script>"""


def checkup_body(today):
    tipi = (
        "Startup", "PMI", "Nuove imprese", "Under 35", "Donne",
        "Professionisti", "Grandi imprese", "Altro",
    )
    stadi = ("Da costituire", "Appena costituita", "In attività", "In crescita")
    tipo_opts = "".join(f'<option value="{e(x)}">{e(x)}</option>' for x in tipi)
    stadio_opts = "".join(f'<option value="{e(x)}">{e(x)}</option>' for x in stadi)
    extra = "".join(f"<li>{e(item)}</li>" for item in CHECKUP_EXTRA)
    if lancio_attivo(today):
        promo = (
            '<aside class="promo" aria-label="Codice di lancio">'
            '<p class="lab">Codice di lancio</p>'
            '<p class="code">LANCIO15</p>'
            f"<p>{CHECKUP_LANCIO}</p></aside>\n"
        )
    else:
        promo = ""
    percorso = crumbs([("index.html", "Home"), ("", "Check-up Bandi")], "")
    domande = faq_html(checkup_faq())
    return f"""{percorso}<div class="box">
<p>Il Check-up Bandi è una verifica scritta dei bandi adatti alla tua impresa: bandi della Regione Toscana e delle Camere di Commercio toscane, dell'Umbria, dell'Emilia-Romagna e incentivi nazionali. Ci mandi i dati dell'impresa e ricevi una relazione scritta sui bandi adatti e cosa serve per partecipare. Base 49 €, relazione di circa 3-4 pagine entro 5 giorni lavorativi. Completo 79 €, 6-10 pagine entro 7-10 giorni lavorativi, con call di 30 minuti. Prezzi finali.</p>
<p>Il Check-up è una verifica di ammissibilità e non garantisce l'ottenimento del contributo.</p>
<h2>Livelli del servizio</h2>
<div class="with-illu"><div>
<ul>
<li><strong>Base</strong>, 49 €: {e(CHECKUP_BASE)}.</li>
<li><strong>Completo</strong>, 79 €: report di 6-10 pagine, entro 7-10 giorni lavorativi dalla ricezione dei dati completi. Include tutto il Base, più:<ul>{extra}</ul></li>
</ul>
<p>{CHECKUP_IVA_NOTE}</p>
</div>
{sec_img("relazione-scritta", 800, 600)}
</div>
{promo}<h2>Chi lo prepara</h2>
<p>Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.</p>
<div class="checkup-split">
<div>
<form id="checkup-form" class="checkup-form">
<div><label for="cu-regione">Regione (comprende la provincia)</label><input id="cu-regione" name="regione" type="text" required autocomplete="address-level1"></div>
<div><label for="cu-tipo">Tipo di impresa</label><select id="cu-tipo" name="tipo" required><option value="">Scegli</option>{tipo_opts}</select></div>
<div><label for="cu-stadio">Stadio</label><select id="cu-stadio" name="stadio" required><option value="">Scegli</option>{stadio_opts}</select></div>
<div><label for="cu-importo">Importo indicativo</label><input id="cu-importo" name="importo" type="text" required inputmode="decimal" placeholder="es. 50.000 €"></div>
<fieldset><legend>Livello</legend><div class="livelli">
<label><input type="radio" name="livello" value="Base" required> Base · 49 €</label>
<label><input type="radio" name="livello" value="Completo"> Completo · 79 €</label>
</div></fieldset>
<button type="submit" class="btn">Invia richiesta</button>
</form>
<p>Il pulsante apre il programma di posta con oggetto e testo già compilati.</p>
<div id="checkup-fallback" hidden>
<p>Se non si apre un'app di posta, copia il testo e invialo a {mail_link()}.</p>
<label for="checkup-text">Testo della richiesta</label>
<textarea id="checkup-text" readonly></textarea>
<button type="button" class="btn outline" id="checkup-copy">Copia</button>
<p id="checkup-copied" role="status" hidden>Testo copiato.</p>
</div>
</div>
{checkup_pay_section(today)}
</div>
</div>
{domande}
{LANCIO_JS}
<script>
(function () {{
  var form = document.getElementById("checkup-form");
  var fallback = document.getElementById("checkup-fallback");
  var area = document.getElementById("checkup-text");
  var copy = document.getElementById("checkup-copy");
  var status = document.getElementById("checkup-copied");
  if (!form || !fallback || !area || !copy) return;
  form.addEventListener("submit", function (ev) {{
    ev.preventDefault();
    var data = new FormData(form);
    var body = [
      "Regione (comprende la provincia): " + (data.get("regione") || ""),
      "Tipo di impresa: " + (data.get("tipo") || ""),
      "Stadio: " + (data.get("stadio") || ""),
      "Importo indicativo: " + (data.get("importo") || ""),
      "Livello: " + (data.get("livello") || "")
    ].join("\\n");
    area.value = body;
    fallback.hidden = false;
    location.href = "mailto:{EMAIL}?subject=" + encodeURIComponent("Richiesta Check-up Bandi") + "&body=" + encodeURIComponent(body);
  }});
  copy.addEventListener("click", function () {{
    var text = area.value;
    var done = function () {{ if (status) status.hidden = false; }};
    var manual = function () {{
      area.focus();
      area.select();
      try {{ document.execCommand("copy"); }} catch (err) {{}}
      done();
    }};
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, manual);
    else manual();
  }});
}})();
</script>"""


def static_pages(today):
    li = ext(LINKEDIN, "Pagina LinkedIn IncentiviPerTe")
    li_btn = ext(LINKEDIN, "Contattaci su LinkedIn", "btn outline")
    mail = mail_link()
    fpef_mail = mail_link(FPEF_EMAIL)
    ipt_btn = f'<a class="btn" href="mailto:{EMAIL}">Scrivi a IncentiviPerTe</a>'
    fpef_btn = f'<a class="btn" href="mailto:{FPEF_EMAIL}">Scrivi a FoglioPEF</a>'
    contacts = f'<p class="contact-links">{li_btn}{mail}</p>'
    sponsor_contacts = (
        f'<p class="contact-links">{li_btn}{mail}{fpef_mail}</p>'
        f"<p>Per le sponsorizzazioni FoglioPEF (39 € al mese) e per il pacchetto entrambi i siti "
        f"(69 € al mese) scrivi a {fpef_mail}.</p>"
    )
    fpef_space = f'<span class="for">Contatto per FoglioPEF: {fpef_mail}</span>'
    fpef_pack = f'<span class="for">Contatto per entrambi i siti: {fpef_mail}</span>'
    owner = f"Davide Davoglio, Arezzo (Italia) – contattabile tramite i messaggi della {li} o all'indirizzo {mail}."
    return {
        "chi-siamo.html": (
            "Chi siamo: metodo e fonti di IncentiviPerTe",
            "Raccolta gratuita e indipendente di bandi, da Arezzo: come scegliamo e controlliamo le schede, quali fonti ufficiali usiamo e cos'è il Check-up Bandi.",
            "<h1>Chi siamo e come controlliamo i bandi</h1><div class='box'>"
            "<p>IncentiviPerTe è una raccolta gratuita e indipendente di bandi per startup e PMI, nata ad Arezzo. Ogni scheda riassume un bando ufficiale, indica la data dell'ultimo controllo e rimanda al testo dell'ente: fa fede sempre il bando ufficiale.</p>"
            "<p>La copertura è tutta la Toscana: bandi regionali e delle Camere di Commercio toscane, più l'Umbria, l'Emilia-Romagna e gli incentivi nazionali.</p>"
            "<p>Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.</p>"
            "<h2>Metodo</h2><div class=\"with-illu\"><p>Ogni scheda è redatta partendo dalla fonte ufficiale (ministeri, Regioni, Sviluppo Toscana, Camere di Commercio toscane, Gepafin e altri enti) e riporta il link al bando e la data dell'ultimo controllo. Le pagine ufficiali vengono ricontrollate periodicamente e ogni anomalia è verificata a mano. I bandi scaduti vengono rimossi.</p>"
            + sec_img("metodo-fonti-ufficiali", 800, 600)
            + "</div>"
            "<h2>Indipendenza</h2><p>Non siamo un ente pubblico né siamo affiliati agli enti citati. Le schede gratuite sono sintesi informative e non sostituiscono il testo del bando. Il sito si sostiene con spazi sponsor sempre etichettati come <em>Sponsorizzato</em>, che non influenzano la selezione dei bandi.</p>"
            "<p>Per gli spazi pubblicitari vedi <a href='/sponsor'>Sponsor</a>. Per segnalare un bando o una correzione, <a href='/contatti'>Contatti</a>. Per il Check-up, <a href='/check-up'>Richiedi il Check-up</a>.</p></div>"
            + checkup_section(""),
            True,
        ),
        "contatti.html": (
            "Contatti – IncentiviPerTe",
            "Scrivici per segnalare un bando o un errore, chiedere il Check-up Bandi o uno spazio sponsor: email e messaggi alla Pagina LinkedIn.",
            f"<h1>Contatti</h1><div class='box'><div class='with-illu'><div><p>Per segnalare un bando, una correzione o per informazioni sugli spazi sponsor scrivici tramite i messaggi della Pagina LinkedIn IncentiviPerTe oppure all'indirizzo email:</p>{contacts}<p>Le schede pubblicate restano sintesi: requisiti e domanda si verificano sull'ente che gestisce la misura. Il Check-up Bandi è la relazione scritta sui bandi adatti: <a href='/check-up'>Richiedi il Check-up</a>. Gli spazi pubblicitari sono descritti nella pagina <a href='/sponsor'>Sponsor</a>.</p></div>{sec_img('contatti', 800, 600)}</div></div>",
            False,
        ),
        "sponsor.html": (
            "Pubblicità per studi e consulenti – IncentiviPerTe",
            "Spazi sponsor per studi, consulenti e banche davanti a chi cerca bandi: da 49 € al mese su IncentiviPerTe, 39 € su FoglioPEF, 69 € su entrambi i siti.",
            f"""<div class="box">
<p>IncentiviPerTe è letto da imprenditori, startup e PMI che cercano finanziamenti. Gli spazi sono per <strong>commercialisti, consulenti di finanza agevolata, banche e software</strong> per le imprese.</p>
{sponsor_contacts}
<h2>Cosa include lo spazio su IncentiviPerTe</h2>
<ul><li>Un posto in <strong>home page</strong></li><li>Un posto nelle <strong>pagine regionali</strong> (Toscana, Umbria, Emilia-Romagna) e nei bandi nazionali</li><li>Un posto nelle <strong>schede dei bandi</strong></li><li>Etichetta <strong>Sponsorizzato</strong> sempre visibile</li></ul>
<h2 id="prezzi">Prezzi</h2>
<p>I prezzi qui sotto sono per uno spazio pubblicitario etichettato Sponsorizzato. Non sono il prezzo dei modelli Excel.</p>
<div class="offers">
<div class="offer featured"><h3>IncentiviPerTe</h3><p class="price"><strong>49 €</strong> al mese</p><p class="launch">Prezzo di lancio: 3 posti, poi 79 € al mese</p><p class="fine">Il prezzo sale man mano che si vendono gli spazi: 49 € al mese per i primi 3 sponsor, poi 79 € al mese, poi 99 € al mese. Nessun pagamento online: ti rispondiamo con i dettagli.</p><div class="contact-links">{ipt_btn}{li_btn}{mail}</div></div>
<div class="offer"><h3>FoglioPEF</h3><p class="price"><strong>39 €</strong> al mese</p><p class="launch">Spazio su FoglioPEF</p><p class="fine">Modelli Excel per immobili e cassa: {ext(FPEF, "fogliopef.github.io")}. Stessa etichetta <strong>Sponsorizzato</strong>.</p><div class="contact-links">{fpef_btn}{fpef_space}</div></div>
<div class="offer"><h3>Entrambi i siti</h3><p class="price"><strong>69 €</strong> al mese</p><p class="launch">Pacchetto entrambi i siti: IncentiviPerTe + FoglioPEF</p><p class="fine">Uno spazio su IncentiviPerTe e uno su FoglioPEF, entrambi etichettati <strong>Sponsorizzato</strong>. Nessun pagamento online: ti rispondiamo con i dettagli.</p><div class="contact-links">{fpef_btn}{fpef_pack}</div></div>
</div>
<h2>Regole</h2>
<ul><li>Ogni contenuto a pagamento è etichettato <strong>Sponsorizzato</strong>.</li><li>Gli sponsor non influenzano quali bandi pubblichiamo né come li descriviamo.</li><li>Nessun tracciamento degli utenti: niente pixel, cookie o script di terze parti.</li></ul>
<p>Domande? Scrivici a {mail} o in un messaggio alla {ext(LINKEDIN, "nostra pagina LinkedIn")}. Per le sponsorizzazioni FoglioPEF (39 € al mese) e per il pacchetto entrambi i siti (69 € al mese): {fpef_mail}.</p>
</div>""",
            False,
        ),
        "check-up.html": (
            "Check-up Bandi per imprese: verifica scritta da 49 €",
            checkup_meta(),
            checkup_body(today),
            False,
        ),
        "cookie.html": (
            "Cookie policy",
            "IncentiviPerTe non usa cookie né strumenti di tracciamento.",
            "<h1>Cookie policy</h1><div class='box'><p>Questo sito <strong>non installa cookie</strong>, né tecnici né di profilazione, e non utilizza strumenti di analisi, pixel pubblicitari, font o script di terze parti. Per questo non è mostrato alcun banner cookie.</p><p>Il sito è ospitato da Cloudflare Pages (Cloudflare, Inc.), che può trattare dati tecnici di navigazione come l'indirizzo IP nei propri log per finalità di sicurezza e funzionamento: vedi la <a href='https://www.cloudflare.com/privacypolicy/' rel='noopener noreferrer'>privacy policy di Cloudflare</a>.</p><p>Se in futuro introducessimo cookie non tecnici, chiederemo prima il consenso e aggiorneremo questa pagina.</p></div>",
            False,
        ),
        "note-legali.html": (
            "Note legali",
            "Note legali di IncentiviPerTe: titolarità, contenuti, marchi e link esterni.",
            f"<h1>Note legali</h1><div class='box'><h2>Titolare del sito</h2><p>{owner}</p><h2>Contenuti</h2><p>Le schede sono sintesi originali redatte a scopo informativo da fonti pubbliche ufficiali, citate e linkate. I testi dei bandi restano dei rispettivi enti. Nomi e marchi citati appartengono ai legittimi titolari.</p><h2>Link esterni</h2><p>I link a siti di terzi sono forniti per comodità; non siamo responsabili dei loro contenuti.</p><h2>Responsabilità</h2><p>Vedi il <a href='/disclaimer'>Disclaimer</a>. Per segnalazioni o richieste di rimozione scrivi all'indirizzo sopra.</p></div>",
            False,
        ),
        "disclaimer.html": (
            "Disclaimer",
            "Avvertenze sull'uso delle informazioni pubblicate da IncentiviPerTe.",
            "<h1>Disclaimer</h1><div class='box'><ul><li>IncentiviPerTe è un servizio informativo <strong>gratuito e indipendente</strong>, non affiliato ad alcun ente pubblico o gestore delle misure. Copre tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), l'Umbria, l'Emilia-Romagna e gli incentivi nazionali.</li><li>Le schede sono <strong>sintesi indicative</strong>: possono contenere errori, omissioni o non essere aggiornate. Requisiti, scadenze e dotazioni possono cambiare o esaurirsi in qualsiasi momento.</li><li><strong>Fa fede esclusivamente</strong> il testo del bando e degli atti pubblicati dall'ente competente. Prima di presentare una domanda verifica sempre la fonte ufficiale.</li><li>Le schede pubblicate <strong>non costituiscono consulenza</strong> fiscale, legale o finanziaria.</li><li>Il <strong>Check-up Bandi</strong> è un servizio distinto: una relazione scritta su quali bandi regionali e nazionali sono adatti all'impresa. Non sostituisce il testo ufficiale del bando.</li><li>Nei limiti consentiti dalla legge, il titolare non risponde di danni derivanti dall'uso delle informazioni del sito.</li><li>I contenuti a pagamento sono sempre etichettati <strong>Sponsorizzato</strong>; il link a FoglioPEF riguarda un progetto dello stesso titolare.</li></ul></div>",
            False,
        ),
        "privacy.html": (
            "Informativa privacy",
            "Informativa privacy di IncentiviPerTe ai sensi del Regolamento UE 2016/679 (GDPR).",
            f"<h1>Informativa privacy</h1><div class='box'><p>Ai sensi degli artt. 13-14 del Regolamento UE 2016/679 (GDPR).</p><h2>Titolare del trattamento</h2><p>{owner}</p><h2>Dati trattati</h2><ul><li><strong>Navigazione</strong>: il sito non usa cookie, analytics o tracker. Il sito è ospitato da GitHub Pages (GitHub, Inc., USA, società controllata da Microsoft), con una copia su Cloudflare Pages (Cloudflare, Inc.). GitHub può registrare dati tecnici come l'indirizzo IP nei log per sicurezza, secondo la propria <a href='https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement' rel='noopener noreferrer'>informativa sulla privacy</a>, e Cloudflare può registrare dati tecnici come l'indirizzo IP nei log di server per sicurezza e funzionamento, secondo la propria <a href='https://www.cloudflare.com/privacypolicy/' rel='noopener noreferrer'>privacy policy</a>; base giuridica: legittimo interesse (art. 6.1.f).</li><li><strong>Email</strong>: se ci scrivi trattiamo indirizzo e contenuto del messaggio solo per rispondere; base giuridica: misure su richiesta dell'interessato / legittimo interesse. Conservazione: il tempo necessario a gestire la richiesta e comunque non oltre 24 mesi.</li></ul><h2>Trasferimenti</h2><p>GitHub, Inc. e Cloudflare, Inc. hanno sede negli USA; i trasferimenti al di fuori dell'UE avvengono secondo le garanzie previste dal GDPR (es. EU-US Data Privacy Framework e/o clausole contrattuali standard) indicate dai fornitori.</p><h2>Diritti</h2><p>Puoi chiedere accesso, rettifica, cancellazione, limitazione, opposizione e portabilità (artt. 15-22) scrivendo al titolare tramite i messaggi della {li} o all'indirizzo {mail}, e proporre reclamo al Garante per la protezione dei dati personali (garanteprivacy.it).</p><p>Nessuna newsletter è attiva: se verrà introdotta, sarà con consenso esplicito e informativa dedicata.</p><p><small>Ultimo aggiornamento: {it_date(today.isoformat())}.</small></p></div>",
            False,
        ),
    }


def item_list(items):
    return {
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": public_url(f"bando/{b['id']}.html"),
                "name": seo_copy.titolo_in_elenco(b),
            }
            for i, b in enumerate((b for b in items if not b["scaduto"]), start=1)
        ],
    }


def write_search_console():
    """File di verifica in radice di dist/. Va scritto dopo cleanup: quello elimina gli html non in «written»."""
    (D / GSC_FILE).write_text(GSC_CONTENT, encoding="utf-8")


def write_assets():
    for name in STATIC_ASSETS:
        shutil.copy(R / "assets" / name, D / name)
    img_src = R / "assets" / "img"
    img_dst = D / "assets" / "img"
    if img_dst.exists():
        shutil.rmtree(img_dst)
    img_dst.mkdir(parents=True)
    missing = [name for name in ILLUSTRAZIONI if not (img_src / name).is_file()]
    if missing:
        raise ValueError("immagini mancanti: " + ", ".join(missing))
    for name in ILLUSTRAZIONI:
        shutil.copy(img_src / name, img_dst / name)
    old_og = D / "og.svg"
    if old_og.exists():
        old_og.unlink()
    (D / "style.css").write_text(CSS, encoding="utf-8")
    (D / ".nojekyll").write_text("", encoding="utf-8")


def cleanup(written):
    for path in D.rglob("*.html"):
        rel = path.relative_to(D).as_posix()
        if rel not in written:
            path.unlink()


def reject_emails_in_cards(html_text, name):
    """Le schede bando non pubblicano indirizzi email, neanche quello del brand."""
    for fragment in re.findall(r'<article class="card\b.*?</article>', html_text, re.S):
        if "mailto:" in fragment.lower() or EMAIL_RE.search(fragment):
            raise ValueError(f"{name}: indirizzo email nella scheda bando")


def foreign_email(text):
    """Vero se resta un indirizzo diverso da quelli consentiti del brand."""
    cleaned = text
    for address in (EMAIL, FPEF_EMAIL):
        cleaned = cleaned.replace(f"mailto:{address}", "").replace(address, "")
    return "mailto:" in cleaned.lower() or EMAIL_RE.search(cleaned) is not None


def without_urls(text):
    text = re.sub(r'href="[^"]*"', "", text, flags=re.I)
    return re.sub(r'"https?://[^"]*"', "", text, flags=re.I)


def visible_text(text):
    """Testo visibile: via gli href e il JSON-LD, resta il dominio sotto il pulsante."""
    text = re.sub(
        r'<script type="application/ld\+json">.*?</script>',
        "",
        text,
        flags=re.I | re.S,
    )
    return re.sub(r'\bhref="[^"]*"', "", text, flags=re.I)


def self_check(written):
    htmls = [p for p in written if p.endswith(".html")]
    for rel in htmls:
        text = (D / rel).read_text(encoding="utf-8")
        name = rel
        if '<html lang="it">' not in text:
            raise ValueError(f"{name}: manca lang=it")
        if len(re.findall(r"<h1[\s>]", text)) != 1:
            raise ValueError(f"{name}: atteso un solo h1")
        if "<script src=" in text or "<script src='" in text:
            raise ValueError(f"{name}: script esterno")
        low = text.lower()
        for token in TRACKERS:
            if token in low:
                raise ValueError(f"{name}: riferimento a tracker ({token})")
        reject_emails_in_cards(text, name)
        # L'email del brand è nel footer e nelle pagine di contatto.
        # foglioPEF.team@gmail.com sta solo sulla pagina sponsor. Ogni altro indirizzo resta vietato.
        if foreign_email(text):
            raise ValueError(f"{name}: indirizzo email")
        if rel != "sponsor.html" and FPEF_EMAIL.lower() in low:
            raise ValueError(f"{name}: email FoglioPEF fuori dalla pagina sponsor")
        for match in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            json.loads(match.group(1))
            if re.search(r'https://incentiviperte\.pages\.dev/[^"\s]*\.html', match.group(1)):
                raise ValueError(f"{name}: URL canonico con .html nei dati strutturati")
        if re.search(r'''(?:href|src)="(?!https?:|mailto:)[^"]*\.html''', text):
            raise ValueError(f"{name}: link interno con .html")
        if re.search(r"\b1 bandi\b|\b1 misure\b", text):
            raise ValueError(f"{name}: plurale sbagliato")
        if name == "404.html":
            if "noindex" not in text or 'rel="canonical"' in text:
                raise ValueError("404: atteso noindex senza canonical")
        elif 'rel="canonical"' not in text:
            raise ValueError(f"{name}: manca canonical")
        for tag in re.findall(r"<a\b[^>]*>", text):
            if 'target="_blank"' in tag and "noopener" not in tag:
                raise ValueError(f"{name}: link esterno senza noopener")
            href_m = re.search(r'href="([^"]+)"', tag)
            href = href_m.group(1).lower() if href_m else ""
            if any(hint in href for hint in AFFILIATE_HINTS) and "link affiliato" not in text[text.find(tag):text.find(tag) + 240].lower():
                raise ValueError(f"{name}: link affiliato senza etichetta")
        if 'aria-label="Spazio sponsor"' in text and "Sponsorizzato" not in text:
            raise ValueError(f"{name}: spazio sponsor senza etichetta Sponsorizzato")
        personal = "Davide" in text or "Davoglio" in text
        if personal and rel not in ("privacy.html", "note-legali.html"):
            raise ValueError(f"{name}: nome personale fuori dalle pagine legali")
        if rel in ("privacy.html", "note-legali.html") and "Davide Davoglio, Arezzo (Italia)" not in text:
            raise ValueError(f"{name}: dati del titolare mancanti")
        for banned in ("Invitalia", "Sorbolini", "Frascadore", "Flavio", "Giuseppe", "Myself Plus"):
            if banned in text:
                raise ValueError(f"{name}: testo non pubblicabile ({banned})")
        if re.search(r"invitalia", visible_text(text), re.I):
            raise ValueError(f"{name}: la parola Invitalia compare nel testo visibile")
        if "essedade.github.io" in text:
            raise ValueError(f"{name}: vecchio indirizzo GitHub Pages")
        if unexpected_gumroad(text, rel == "check-up.html"):
            raise ValueError(f"{name}: rimando Gumroad non previsto")
        if rel.startswith("bando/") and 'class="bando-checkup"' not in text:
            raise ValueError(f"{name}: manca il riquadro Check-up sul bando")
        if re.search(r'''\b(?:href|src)\s*=\s*["']/incentiviperte/''', text):
            raise ValueError(f"{name}: link assoluto del vecchio percorso GitHub Pages")
        for match in re.finditer("Arezzo-Siena", text):
            window = text[max(0, match.start() - 80):match.start()]
            if "<dt>Ente</dt><dd>" not in window:
                raise ValueError(f"{name}: Arezzo-Siena compare come limite di copertura")
    sponsor = (D / "sponsor.html").read_text(encoding="utf-8")
    for price in ("49 €", "39 €", "69 €", "79 €", "99 €"):
        if price not in sponsor:
            raise ValueError(f"prezzo mancante sulla pagina sponsor: {price}")
    if f"mailto:{FPEF_EMAIL}" not in sponsor:
        raise ValueError("pagina sponsor: manca il contatto FoglioPEF")
    for title, end in (("FoglioPEF", "<h3>"), ("Entrambi i siti", "<h2>")):
        chunk = sponsor.split(f"<h3>{title}</h3>", 1)[1].split(end, 1)[0]
        if f'<a class="btn" href="mailto:{FPEF_EMAIL}">' not in chunk:
            raise ValueError(f"pagina sponsor: il pulsante di {title} non apre {FPEF_EMAIL}")
        if f'<a class="btn" href="mailto:{EMAIL}">' in chunk:
            raise ValueError(f"pagina sponsor: il pulsante pieno di {title} apre l'email di IncentiviPerTe")
        if "Contattaci su LinkedIn" in chunk or LINKEDIN in chunk:
            raise ValueError(f"pagina sponsor: {title} rimanda al LinkedIn di IncentiviPerTe")
        if EMAIL in chunk:
            raise ValueError(f"pagina sponsor: {title} usa l'email di IncentiviPerTe")
        if f'href="mailto:{FPEF_EMAIL}"' not in chunk:
            raise ValueError(f"pagina sponsor: {title} non ha il mailto di FoglioPEF")
    about = (D / "chi-siamo.html").read_text(encoding="utf-8")
    if "Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale." not in about:
        raise ValueError("chi siamo: manca la descrizione del team")
    if "Check-up Bandi" not in about or "tutta la Toscana" not in about or "Camere di Commercio toscane" not in about:
        raise ValueError("chi siamo: copertura o Check-up Bandi mancanti")
    if "Arezzo-Siena" in about:
        raise ValueError("chi siamo: Arezzo-Siena resta come limite di copertura")
    home = (D / "index.html").read_text(encoding="utf-8")
    if "Check-up Bandi" not in home or 'href="/check-up">Richiedi il Check-up</a>' not in home:
        raise ValueError("home: manca la sezione Check-up Bandi")
    if 'getAttribute("data-scadenza")' not in home or 'getAttribute("data-apre")' not in home:
        raise ValueError("home: il conto alla rovescia non viene dalle date dei bandi")
    if 'data-scad="2026-10-23"' not in home:
        raise ValueError("home: manca la scadenza letta dai dati")
    if 'value="Umbria"' not in home or 'value="Emilia-Romagna"' not in home or 'value="Toscana"' not in home:
        raise ValueError("home: filtri di area incompleti")
    if "focus iniziale" in home or "focus iniziale" in about:
        raise ValueError("testo che restringe la copertura ancora presente")
    if FPEF not in home or "stesso titolare" not in home.lower():
        raise ValueError("home: manca il rimando a FoglioPEF con la disclosure")
    if "fogliopef.gumroad.com" in home or "fogliopef.gumroad.com" in about:
        raise ValueError("rimando FoglioPEF ancora su Gumroad")
    checkup = (D / "check-up.html").read_text(encoding="utf-8")
    if "verifica di ammissibilità" not in checkup or "non garantisce l'ottenimento del contributo" not in checkup:
        raise ValueError("check-up: manca l'avvertenza sulla verifica di ammissibilità")
    if re.search(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", checkup):
        raise ValueError("check-up: compare un IBAN")
    if 'rel="canonical" href="https://incentiviperte.github.io/check-up"' not in checkup:
        raise ValueError("check-up: il canonical non è su github.io")
    for url in (GUMROAD_CHECKUP_BASE_URL, GUMROAD_CHECKUP_COMPLETO_URL):
        if f'href="{url}"' not in checkup:
            raise ValueError("check-up: manca il link al prodotto Gumroad")
    for path in (p for p in htmls if p.startswith("bando/")):
        scheda = (D / path).read_text(encoding="utf-8")
        box = scheda.split('class="bando-checkup"', 1)[-1].split("</aside>", 1)[0]
        if "Check-up Bandi" not in box or 'href="/check-up"' not in box:
            raise ValueError(f"{path}: il riquadro Check-up non rimanda a /check-up")
        if f'rel="canonical" href="{BASE}bando/' not in scheda:
            raise ValueError(f"{path}: canonical fuori da github.io")
    if FPEF_LI not in home:
        raise ValueError("home: manca il link LinkedIn di FoglioPEF")
    if "link affiliato" in home.lower():
        raise ValueError("home: FoglioPEF non va etichettato come link affiliato")
    robots = (D / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {BASE}sitemap.xml" not in robots or "Disallow: /" in robots:
        raise ValueError("robots.txt non valido")
    sitemap = (D / "sitemap.xml").read_text(encoding="utf-8")
    if "<loc>" not in sitemap or ".html" in sitemap or "/404<" in sitemap:
        raise ValueError("sitemap non valida")
    css = (D / "style.css").read_text(encoding="utf-8")
    if re.search(r"#0b5cad", css, re.I):
        raise ValueError("css: resta #0B5CAD")
    if "a.btn.head-cta{display:none}" not in css:
        raise ValueError("css: il Check-up in header non si nasconde sopra i 1180px")
    if ".btn.outline{background:transparent;color:var(--b);border:2px solid var(--b)}" not in css:
        raise ValueError("css: manca il pulsante outline")
    if ".card .tag{background:#E7F4EE;border:0;color:var(--bd)}" not in css:
        raise ValueError("css: le chip delle card sembrano ancora cliccabili")
    for rel in htmls:
        text = (D / rel).read_text(encoding="utf-8")
        if "FoglioPEF è un foglio Excel" in text:
            raise ValueError(f"{rel}: descrizione vecchia di FoglioPEF")
        if 'class="fpef"' in text and FPEF_DESC not in text:
            raise ValueError(f"{rel}: il riquadro FoglioPEF non usa la descrizione unica")
    for rel in ("robots.txt", "sitemap.xml"):
        blob = (D / rel).read_text(encoding="utf-8")
        if "essedade.github.io" in blob:
            raise ValueError(f"{rel}: vecchio indirizzo GitHub Pages")
    if (D / GSC_FILE).read_text(encoding="utf-8") != GSC_CONTENT:
        raise ValueError("file di verifica Search Console mancante o alterato")
    if GSC_FILE in sitemap or GSC_TOKEN in sitemap:
        raise ValueError("il file di verifica non va nella sitemap")
    for rel in htmls:
        if f'name="google-site-verification" content="{GSC_TOKEN}"' not in (D / rel).read_text(encoding="utf-8"):
            raise ValueError(f"{rel}: manca il meta di verifica Search Console")


def span_n(n):
    return f'<span data-aperti-n>{n}</span>'


def riga_aperti(n):
    return f'In elenco: <span data-aperti>{qty(n, "bando aperto", "bandi aperti")}</span>'


def link_bando(b):
    return f'<a href="{site_href(f"bando/{b["id"]}.html")}">{e(seo_copy.titolo_in_elenco(b))}</a>'


def lista_bandi(rows):
    if not rows:
        return "<p>Nessuna scheda in questo elenco.</p>"
    voci = "".join(f"<li>{link_bando(b)} — {e(deadline_text(b))}</li>" for b in rows)
    return f"<ul>{voci}</ul>"


def chiave_camera(bando):
    ente = bando["ente"].lower()
    if bando["regione"] == "Toscana" and "camera di commercio" in ente:
        if "firenze" in ente:
            return "firenze"
        if "arezzo" in ente:
            return "arezzo-siena"
        if "maremma" in ente:
            return "maremma"
        if "nord-ovest" in ente:
            return "tno"
        if "pistoia" in ente:
            return "pistoia"
    if bando["regione"] == "Emilia-Romagna" and ("camera di commercio" in ente or "ferrara" in ente):
        if "bologna" in ente:
            return "bologna"
        if "dell'emilia" in ente:
            return "emilia"
        if "ferrara" in ente:
            return "ferrara"
        if "modena" in ente:
            return "modena"
        if "romagna" in ente:
            return "romagna"
    return ""


CAMERE_TOSCANA = (
    ("firenze", "Camera di Commercio di Firenze", "Altri bandi della Camera di Commercio di Firenze"),
    ("arezzo-siena", "Camera di Commercio di Arezzo e Siena", "Altri bandi della Camera di Commercio di Arezzo e Siena"),
    ("maremma", "Camera di Commercio della Maremma e del Tirreno", "Altri bandi della Camera di Commercio della Maremma e del Tirreno"),
    ("tno", "Camera di Commercio della Toscana Nord-Ovest", "Altri bandi della Camera di Commercio della Toscana Nord-Ovest"),
    ("pistoia", "Camera di Commercio di Pistoia-Prato", "Altri bandi della Camera di Commercio di Pistoia-Prato"),
)
CAMERE_ER = (
    ("bologna", "Camera di Commercio di Bologna", "Altri bandi della Camera di Commercio di Bologna"),
    ("emilia", "Camera di Commercio dell'Emilia", "Altri bandi della Camera di Commercio dell'Emilia"),
    ("ferrara", "Camera di Commercio di Ferrara e Ravenna", "Altri bandi della Camera di Commercio di Ferrara e Ravenna"),
    ("modena", "Camera di Commercio di Modena", "Altri bandi della Camera di Commercio di Modena"),
    ("romagna", "Camera di Commercio della Romagna", "Altri bandi della Camera di Commercio della Romagna"),
)
HUB_TOSCANA = "bandi-camere-di-commercio-toscana.html"
HUB_ER = "bandi-camere-di-commercio-emilia-romagna.html"
PAGINA_APRIRE = "aprire-attivita-toscana.html"


def rimando_camera(bando):
    chiave = chiave_camera(bando)
    if not chiave:
        return ""
    tabella = CAMERE_TOSCANA if bando["regione"] == "Toscana" else CAMERE_ER
    pagina = HUB_TOSCANA if bando["regione"] == "Toscana" else HUB_ER
    for cid, _h2, etichetta in tabella:
        if cid == chiave:
            return f'<p><a href="{site_href(pagina, fragment=cid)}">{e(etichetta)}</a></p>'
    return ""


def faq_scheda_html(bando):
    plain, html_pairs = [], []
    for domanda, risposta in seo_copy.faq_scheda(bando):
        if bando["id"] == "autoimpiego-centro-nord" and domanda.startswith("Vale anche"):
            href = site_href("bando/resto-al-sud-2.html")
            testo = "No: al Sud c'è Resto al Sud 2.0."
            marcato = f'No: al Sud c\'è <a href="{href}">Resto al Sud 2.0</a>.'
        else:
            testo, marcato = risposta, e(risposta)
        plain.append((domanda, testo))
        html_pairs.append((domanda, marcato))
    return plain, html_pairs


def home_faq():
    sportello = (
        "Cosa significa bando a sportello?",
        "Le domande vengono esaminate in ordine di arrivo finché ci sono risorse: il bando può chiudere prima della scadenza. "
        "La guida è Bando a sportello.",
    )
    resto = (
        "Resto al Sud 2.0 vale in Toscana?",
        "No, vale solo nelle otto regioni del Mezzogiorno. Al Centro-Nord la misura per gli under 35 è Autoimpiego Centro-Nord.",
    )
    plain = list(FAQ) + [sportello, resto]
    resto_html = (
        "No, vale solo nelle otto regioni del Mezzogiorno. Al Centro-Nord la misura per gli under 35 è "
        f'<a href="{site_href("bando/autoimpiego-centro-nord.html")}">Autoimpiego Centro-Nord</a>.'
    )
    sportello_html = (
        "Le domande vengono esaminate in ordine di arrivo finché ci sono risorse: il bando può chiudere prima della scadenza. "
        f'<a href="{site_href("guida/bando-a-sportello.html")}">Che cos\'è un bando a sportello</a>.'
    )
    marcate = [(q, e(a)) for q, a in FAQ] + [(sportello[0], sportello_html), (resto[0], resto_html)]
    return plain, marcate


def _schede(bandi, ids):
    ordine = {bid: i for i, bid in enumerate(ids)}
    return sorted((b for b in bandi if b["id"] in ordine), key=lambda b: ordine[b["id"]])


def sezioni_toscana(rows):
    doppia = _schede(rows, (
        "cciaa-maremma-tirreno-doppia-transizione-2026",
        "cciaa-tno-doppia-transizione-2-2026",
    ))
    doppia_html = " e ".join(link_bando(b) for b in doppia)
    aperti_perduto = [
        b for b in rows
        if is_aperto(b) and "fondo perduto" in f'{b["importo"]} {b["sintesi"]}'.lower()
    ]
    if aperti_perduto:
        nomi = ", ".join(seo_copy.titolo_in_elenco(b) for b in aperti_perduto)
        links = ", ".join(link_bando(b) for b in aperti_perduto)
    else:
        nomi = "In questo momento non ci sono schede toscane aperte con contributo a fondo perduto."
        links = e(nomi)
    faq_plain = (
        ("Quali bandi a fondo perduto sono aperti in Toscana?", nomi),
        (
            "Dove si presenta la domanda per i bandi della Regione Toscana?",
            "Per i bandi gestiti da Sviluppo Toscana sul Sistema Fondi Toscana (sft.sviluppo.toscana.it), "
            "con identità digitale e imposta di bollo; per i bandi camerali di solito su ReStart.",
        ),
        (
            "Ci sono bandi per l'imprenditoria femminile in Toscana?",
            "Sì: per esempio la linea A1 del Bando 1.3.2 è dedicata anche alla creazione di imprese femminili. "
            "L'elenco completo è nella pagina Bandi per l'imprenditoria femminile.",
        ),
    )
    donne = site_href("settore/donne.html")
    faq_html_pairs = [
        (faq_plain[0][0], links),
        (faq_plain[1][0], e(faq_plain[1][1])),
        (
            faq_plain[2][0],
            "Sì: per esempio la linea A1 del Bando 1.3.2 è dedicata anche alla creazione di imprese femminili. "
            f'L\'elenco completo è nella pagina <a href="{donne}">Bandi per l\'imprenditoria femminile</a>.',
        ),
    ]
    blocchi = (
        '<section><h2>Bandi della Regione Toscana e di Sviluppo Toscana</h2>'
        "<p>Nell'elenco qui sotto ci sono le misure della Regione gestite da Sviluppo Toscana, come il Bando 1.3.2, "
        "e i contributi di ARTI per le assunzioni.</p></section>"
        '<section><h2>Bandi delle Camere di Commercio toscane</h2>'
        "<p>Tutta la Toscana: bandi regionali e delle Camere di Commercio toscane. "
        f'La raccolta per Camera è nella pagina <a href="{site_href(HUB_TOSCANA)}">Bandi delle Camere di Commercio in Toscana</a>.</p></section>'
        '<section><h2>Digitalizzazione e transizione</h2>'
        f"<p>Schede sulla doppia transizione: {doppia_html}.</p></section>"
        '<section><h2>Per chi apre un\'impresa in Toscana</h2>'
        f'<p><a href="{site_href(PAGINA_APRIRE)}">Contributi per aprire un\'attività in Toscana</a>.</p></section>'
    )
    return blocchi, faq_plain, faq_html_pairs


def sezioni_umbria(rows):
    def gruppo(pred):
        return [b for b in rows if pred(b) and is_aperto(b)]
    gepafin = gruppo(lambda b: "Gepafin" in b["ente"])
    svilupp = gruppo(lambda b: "Sviluppumbria" in b["ente"])
    altri = gruppo(lambda b: "Gepafin" not in b["ente"] and "Sviluppumbria" not in b["ente"])
    faq = (
        (
            "Cosa vuol dire finanziamento con remissione?",
            "È un prestito agevolato di cui una parte, a certe condizioni, non va restituita: "
            "per esempio l'Avviso STEP prevede una remissione fino al 50%.",
        ),
        (
            "Dove trovo i bandi non scaduti della Regione Umbria?",
            "In questa pagina sono elencati solo i bandi con scadenza futura o a sportello aperto, "
            "con la data dell'ultimo controllo.",
        ),
    )
    # Il secondo punto del documento vale per l'elenco predefinito: gli scaduti restano raggiungibili
    # con «Mostra scaduti» in home e con la propria scheda. Qui si dice come è fatta questa pagina.
    blocchi = (
        "<section><h2>Bandi Gepafin</h2>" + lista_bandi(gepafin) + "</section>"
        "<section><h2>Bandi Sviluppumbria</h2>" + lista_bandi(svilupp) + "</section>"
        "<section><h2>Altri bandi della Regione Umbria</h2>" + lista_bandi(altri) + "</section>"
    )
    return blocchi, faq


def sezioni_emilia():
    return (
        (
            "Cos'è il Fondo Multiscopo dell'Emilia-Romagna?",
            "Un fondo regionale di finanza agevolata: il 75% del finanziamento è a tasso zero e il 25% è bancario "
            "a tasso convenzionato. Ha sezioni diverse, come StartER per le imprese giovani e GreenER per energia "
            "ed economia circolare.",
        ),
        (
            "Dove si presenta la domanda per i bandi FESR?",
            "Di solito sulla piattaforma regionale Sfinge 2020, indicata nel bando.",
        ),
    )


SETTORE_SEO = {
    "PMI": (
        "Bandi per PMI 2026: Toscana, Umbria, Emilia-Romagna",
        "Bandi aperti per PMI: contributi a fondo perduto e finanziamenti agevolati regionali, camerali e nazionali, con scadenze e link al bando ufficiale.",
        "Bandi aperti per PMI in Toscana, Umbria ed Emilia-Romagna",
        "Qui trovi i bandi aperti per le piccole e medie imprese di Toscana, Umbria ed Emilia-Romagna e quelli nazionali: contributi a fondo perduto, aiuti su interessi e garanzie, finanziamenti agevolati.",
    ),
    "Startup": (
        "Bandi per startup 2026: incentivi regionali e nazionali",
        "Bandi e incentivi per startup e startup innovative: Smart&Start Italia, StartER in Emilia-Romagna e bandi toscani. Requisiti, scadenze e link ufficiali.",
        "Bandi aperti per startup e startup innovative",
        "Qui trovi i bandi aperti per le startup in Toscana, Umbria, Emilia-Romagna e a livello nazionale: finanziamenti a tasso zero come Smart&Start Italia, finanza agevolata come StartER e i bandi per chi investe in startup innovative.",
    ),
    "Donne": (
        "Imprenditoria femminile 2026: bandi a fondo perduto",
        "Bandi per imprese femminili e donne che aprono un'attività in Toscana, Emilia-Romagna e in Italia: fondo perduto e tasso zero, requisiti e link ufficiali.",
        "Bandi per l'imprenditoria femminile",
        "Qui trovi i bandi aperti per le imprese femminili e per le donne che avviano un'attività in Toscana, Emilia-Romagna e a livello nazionale: per esempio la linea A1 del Bando 1.3.2 in Toscana, la quota a tasso zero più alta per le imprese femminili in StartER (Emilia-Romagna) e ON Nuove imprese a tasso zero.",
    ),
    "Nuove imprese": (
        "Bandi per nuove imprese 2026: contributi aperti",
        "Contributi a fondo perduto e finanziamenti a tasso zero per chi apre una nuova impresa: bandi camerali, regionali e nazionali, requisiti e link ufficiali.",
        "Bandi aperti per nuove imprese",
        "Qui trovi i contributi aperti per chi ha appena aperto o sta per aprire un'impresa: voucher delle Camere di Commercio, aiuti regionali e misure nazionali come Autoimpiego Centro-Nord e ON tasso zero.",
    ),
    "Under 35": (
        "Bandi per under 35 che aprono un'impresa nel 2026",
        "Incentivi per giovani under 35 che avviano un'attività: Autoimpiego Centro-Nord, ON tasso zero e bandi camerali per imprese giovanili, requisiti e link.",
        "Bandi per giovani under 35",
        "Qui trovi i bandi aperti per i giovani under 35 in Toscana, Umbria, Emilia-Romagna e a livello nazionale, con importo, scadenza e link al bando ufficiale.",
    ),
    "Professionisti": (
        "Bandi per liberi professionisti 2026",
        "Bandi aperti anche ai liberi professionisti in Toscana, Umbria, Emilia-Romagna e Italia: contributi e aiuti sui finanziamenti, scadenze e link ufficiali.",
        "Bandi aperti per liberi professionisti",
        "Qui trovi i bandi aperti per i liberi professionisti in Toscana, Umbria, Emilia-Romagna e a livello nazionale, con importo, scadenza e link al bando ufficiale.",
    ),
    "Grandi imprese": (
        "Bandi per grandi imprese 2026: misure aperte",
        "Bandi aperti anche alle grandi imprese in Toscana, Umbria ed Emilia-Romagna: cosa finanziano, importi, scadenze e link al bando ufficiale.",
        "Bandi aperti per grandi imprese",
        "Qui trovi i bandi aperti per le grandi imprese in Toscana, Umbria, Emilia-Romagna e a livello nazionale, con importo, scadenza e link al bando ufficiale.",
    ),
    "Investitori": (
        "Agevolazioni per chi investe in startup innovative",
        "Detrazione IRPEF del 65% per chi investe in startup innovative, fino a 100.000 € l'anno: requisiti, limiti de minimis e link alla norma ufficiale.",
        "Agevolazioni per chi investe in startup",
        "Qui trovi i bandi aperti per chi investe in startup innovative in Toscana, Umbria, Emilia-Romagna e a livello nazionale, con importo, scadenza e link al bando ufficiale.",
    ),
}

FAQ_DONNE = (
    (
        "Cosa si intende per impresa femminile?",
        "Dipende dal bando: di solito un'impresa in cui le donne hanno la maggioranza delle quote e degli organi di amministrazione. La definizione esatta è nel testo di ogni bando.",
    ),
)

FAQ_CAMERE = (
    (
        "Chi può partecipare ai bandi della Camera di Commercio?",
        "Le micro, piccole e medie imprese con sede o unità locale nella provincia della Camera, iscritte al Registro delle imprese. Ogni bando ha requisiti propri.",
    ),
    (
        "Serve essere in regola con il diritto annuale?",
        "Quasi sempre sì, insieme al DURC regolare. Alcuni bandi permettono di regolarizzare il diritto annuale entro pochi giorni.",
    ),
    (
        "Come si presenta la domanda?",
        "Di solito online sulla piattaforma ReStart, con firma digitale, oppure via PEC: il bando indica quale.",
    ),
    (
        'Cosa vuol dire "risorse esaurite, lista d\'attesa"?',
        "Che i fondi sono finiti: le nuove domande vengono finanziate solo se si liberano risorse o se la Camera rifinanzia il bando.",
    ),
    (
        "Quando escono i nuovi bandi?",
        "Molte Camere pubblicano i bandi in primavera; la data varia da Camera a Camera.",
    ),
)
FAQ_CONFIDI = (
    "Cosa sono i contributi tramite Confidi?",
    "Contributi della Camera che riducono il costo della garanzia o degli interessi su un finanziamento con la garanzia di un Confidi; di solito la domanda la presenta il Confidi.",
)


def griglia_camera(gruppo, today):
    aperti = [b for b in gruppo if not b["scaduto"]]
    chiusi = [b for b in gruppo if b["scaduto"]]
    blocchi = "".join(card(b, "", today, mostra_scaduto=True) for b in aperti + chiusi)
    if not blocchi:
        return "<p>Nessuna scheda in questa sezione.</p>"
    return f'<div class="grid">{blocchi}</div>'


def corpo_camere(titolo_h1, paragrafo, voci, bandi, today, faq):
    sezioni = []
    for cid, h2, _etichetta in voci:
        gruppo = [b for b in bandi if chiave_camera(b) == cid]
        sezioni.append(f'<section id="{cid}"><h2>{e(h2)}</h2>{griglia_camera(gruppo, today)}</section>')
    return (
        crumbs([("index.html", "Home"), ("", titolo_h1)], "")
        + f"<h1>{e(titolo_h1)}</h1><p>{e(paragrafo)}</p>"
        + "".join(sezioni)
        + "<section><h2>Come si presenta la domanda</h2>"
        + "<p>Di solito online sulla piattaforma ReStart, con firma digitale, oppure via PEC: il bando indica quale. "
        + f"Per orientarti prima, puoi chiedere una {link_verifica()}.</p></section>"
        + faq_html(faq)
        + BADGE_JS
    )


def ld_raccolta(path, title, crumb_label, items, faq=()):
    graph = [
        {"@type": "CollectionPage", "name": title, "url": public_url(path), "inLanguage": "it-IT", "isPartOf": BASE},
        breadcrumb_ld([("", "Home"), (path, crumb_label)]),
        item_list([b for b in items if not b["scaduto"]]),
    ]
    if faq:
        graph.append(faq_ld(faq))
    return {"@context": "https://schema.org", "@graph": graph}


AREA_SEO = {
    "Nazionale": (
        "Incentivi nazionali 2026 per nuove imprese e PMI",
        "Incentivi nazionali aperti nel 2026: Autoimpiego Centro-Nord, ON tasso zero, Smart&Start Italia, Nuova Sabatini, Fondo di garanzia. Requisiti e link.",
        "Incentivi nazionali aperti per nuove imprese e PMI",
    ),
    "Toscana": (
        "Bandi Toscana 2026 per imprese: fondo perduto e scadenze",
        "Bandi aperti in Toscana per PMI e startup: Regione, Sviluppo Toscana, ARTI e Camere di Commercio. Contributi a fondo perduto e finanziamenti, con scadenze.",
        "Bandi aperti in Toscana per imprese e startup",
    ),
    "Umbria": (
        "Contributi a fondo perduto Umbria 2026: bandi aperti",
        "Bandi aperti in Umbria per imprese: Regione, Gepafin e Sviluppumbria. Fondo perduto e finanziamenti agevolati con remissione, scadenze e link ufficiali.",
        "Bandi aperti in Umbria per imprese",
    ),
    "Emilia-Romagna": (
        "Bandi Emilia-Romagna 2026 per imprese e startup",
        "Bandi aperti in Emilia-Romagna per PMI e startup: PR FESR, Fondo Multiscopo (StartER, GreenER) e Camere di Commercio, con scadenze e link ufficiali.",
        "Bandi aperti in Emilia-Romagna per imprese e startup",
    ),
}

HUB_TITOLO_TOSCANA = "Bandi delle Camere di Commercio in Toscana"
HUB_TITOLO_ER = "Bandi delle Camere di Commercio in Emilia-Romagna"
APRIRE_TITOLO = "Contributi per aprire un'attività in Toscana"
APRIRE_TITLE = "Contributi per aprire un'attività in Toscana nel 2026"


def apertura_area(reg, n, data):
    """Paragrafi di apertura. Il numero è quello dei bandi già aperti, non scaduti."""
    num = span_n(n)
    quando = e(it_date(data))
    if reg == "Nazionale":
        testo = (
            "Qui trovi gli incentivi nazionali aperti che valgono anche in Toscana, Umbria ed Emilia-Romagna: "
            "per chi apre un'impresa (Autoimpiego Centro-Nord, ON Nuove imprese a tasso zero), per le startup "
            "innovative (Smart&amp;Start Italia) e per gli investimenti delle PMI (Nuova Sabatini, Fondo di garanzia). "
            f"Per ogni misura: importo, requisiti e link al bando ufficiale. Aggiornato al {quando}."
        )
    elif reg == "Toscana":
        testo = (
            f"Al {quando} in Toscana sono aperti {num} bandi per imprese: misure della Regione Toscana gestite da "
            "Sviluppo Toscana (come il Bando 1.3.2 per le PMI), contributi di ARTI per le assunzioni e voucher "
            "delle Camere di Commercio toscane. La maggior parte sono contributi a fondo perduto o aiuti sul costo "
            "dei finanziamenti. Per ogni bando trovi importo, destinatari, scadenza e link al bando ufficiale."
        )
    elif reg == "Umbria":
        testo = (
            f"Al {quando} in Umbria sono aperti {num} bandi per imprese della Regione Umbria, "
            "gestiti da Gepafin e Sviluppumbria: soprattutto finanziamenti agevolati con remissione parziale "
            "del debito (Avviso STEP, efficienza energetica, fonti rinnovabili) e contributi a fondo perduto. "
            "Per ogni bando: importo, destinatari, scadenza e link al bando ufficiale."
        )
    else:
        testo = (
            f"Al {quando} in Emilia-Romagna sono aperti {num} bandi per imprese: misure regionali del PR FESR "
            "2021-2027, il Fondo Multiscopo con le sezioni StartER (nuove imprese) e GreenER (energia), e i bandi "
            f"delle Camere di Commercio. Per ogni bando: importo, destinatari, scadenza e link al bando ufficiale."
        )
    return f"<p>{testo}</p><p>{riga_aperti(n)}. Puoi chiedere una {link_verifica()}.</p>"


def _faq_aprire():
    resto = "No. Al Centro-Nord la misura equivalente per gli under 35 è Autoimpiego Centro-Nord."
    piano = "Molti bandi chiedono un piano degli investimenti e delle spese; per costruirlo in Excel c'è FoglioPEF."
    cumulo = (
        "A volte sì, se riguardano spese diverse e se il bando lo permette, nel limite del regime de minimis. "
        "Le regole generali sono nella guida Regime de minimis. Il testo del regolamento è il Regolamento UE 2023/2831."
    )
    plain = (
        (
            "Ci sono contributi a fondo perduto per aprire un'attività in Toscana?",
            "Sì, soprattutto dalle Camere di Commercio e per gli under 35 con Autoimpiego Centro-Nord. "
            "Gli importi e i requisiti cambiano da bando a bando.",
        ),
        ("Resto al Sud 2.0 vale in Toscana?", resto),
        (
            "Posso chiedere il contributo prima di aprire la partita IVA?",
            "Dipende dal bando: Autoimpiego Centro-Nord, per esempio, richiede che l'attività sia già avviata "
            "nel mese della domanda o in quello precedente; altri bandi accettano imprese da costituire.",
        ),
        ("Serve un business plan?", piano + " È su fogliopef.github.io."),
        ("Posso cumulare più contributi?", cumulo),
    )
    resto_html = (
        'No. Al Centro-Nord la misura equivalente per gli under 35 è '
        f'<a href="{site_href("bando/autoimpiego-centro-nord.html")}">Autoimpiego Centro-Nord</a>.'
    )
    piano_html = (
        "Molti bandi chiedono un piano degli investimenti e delle spese; per costruirlo in Excel c'è "
        f"{ext(FPEF, 'FoglioPEF')}."
    )
    cumulo_html = (
        "A volte sì, se riguardano spese diverse e se il bando lo permette, nel limite del regime de minimis. "
        f'Le regole generali sono nella guida <a href="{site_href("guida/de-minimis.html")}">Regime de minimis</a>. '
        f"Il testo del regolamento è il {ext(EURLEX_DE_MINIMIS, 'Regolamento UE 2023/2831')}."
    )
    html_pairs = [
        (plain[0][0], e(plain[0][1])),
        (plain[1][0], resto_html),
        (plain[2][0], e(plain[2][1])),
        (plain[3][0], piano_html),
        (plain[4][0], cumulo_html),
    ]
    return plain, html_pairs


def corpo_aprire(bandi, data):
    """Pagina per chi apre un'attività in Toscana. Solo bandi già in archivio."""
    def prendi(*ids):
        return _schede(bandi, ids)

    camere = prendi(
        "cciaa-firenze-nuove-imprese-2026",
        "cciaa-maremma-tirreno-creazione-impresa-2026",
        "cciaa-maremma-tirreno-societa-benefit-2026",
    )
    regione = prendi("bando-132-50k-2026")
    nazionali = prendi("autoimpiego-centro-nord", "on-nuove-imprese-tasso-zero")
    plain, html_pairs = _faq_aprire()
    apertura = (
        "Per aprire un'attività in Toscana nel 2026 ci sono tre tipi di aiuto: i contributi a fondo perduto "
        "delle Camere di Commercio per le nuove imprese (per esempio Firenze: 50% delle spese di avvio, fino a "
        "5.000 €), gli aiuti della Regione sul costo dei finanziamenti (Bando 1.3.2, linea A1) e le misure "
        "nazionali per gli under 35 e le nuove imprese (Autoimpiego Centro-Nord, ON tasso zero). Qui li trovi "
        f"divisi per tipo, con requisiti e link ufficiali. Aggiornato al {it_date(data)}."
    )
    corpo = (
        crumbs([("index.html", "Home"), ("", APRIRE_TITOLO)], "")
        + f"<h1>{e(APRIRE_TITOLO)}</h1><p>{e(apertura)}</p>"
        + "<section><h2>Risposta breve: quali aiuti ci sono oggi</h2>"
        + "<p>Oggi gli aiuti per aprire un'attività in Toscana sono di tre tipi: contributi delle Camere di "
        + "Commercio per le nuove imprese, aiuti della Regione sul costo dei finanziamenti (Bando 1.3.2, linea A1) "
        + "e misure nazionali per gli under 35 e le nuove imprese (Autoimpiego Centro-Nord, ON tasso zero). "
        + f"Per la tua impresa puoi chiedere una {link_verifica()}.</p></section>"
        + '<section><h2>Contributi delle Camere di Commercio per le nuove imprese</h2>'
        + f'<p>L\'elenco completo per Camera è nella pagina <a href="{site_href(HUB_TOSCANA)}">{e(HUB_TITOLO_TOSCANA)}</a>.</p>'
        + lista_bandi(camere)
        + "</section>"
        + "<section><h2>Aiuti della Regione Toscana</h2>"
        + "<p>Il Bando 1.3.2, linea A1, riguarda le nuove imprese giovanili, femminili o di persone in ammortizzatori sociali.</p>"
        + lista_bandi(regione)
        + "</section>"
        + "<section><h2>Misure nazionali valide anche in Toscana</h2>"
        + lista_bandi(nazionali)
        + "</section>"
        + '<section><h2>Under 35 e imprese femminili</h2>'
        + f'<p>Pagine dedicate: <a href="{site_href("settore/under-35.html")}">bandi per giovani under 35</a> e '
        + f'<a href="{site_href("settore/donne.html")}">bandi per l\'imprenditoria femminile</a>.</p>'
        + lista_bandi(nazionali)
        + "</section>"
        + "<section><h2>Documenti che servono di solito</h2>"
        + "<p>Quasi sempre servono il DURC regolare e il diritto annuale in regola, insieme all'iscrizione al "
        + "Registro delle imprese. La domanda si presenta di solito online sulla piattaforma ReStart, con firma "
        + "digitale, oppure via PEC: il bando indica quale.</p></section>"
        + faq_html(html_pairs, raw=True)
    )
    return corpo, plain, camere + regione + nazionali


def ld_guida(path, title, crumb, faq):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "name": title, "url": public_url(path), "inLanguage": "it-IT", "isPartOf": BASE},
            breadcrumb_ld([("", "Home"), (path, crumb)]),
            faq_ld(faq),
        ],
    }


def _esempi(bandi, ids):
    return lista_bandi(_schede(bandi, ids))


def corpo_guide(bandi):
    """Tre guide brevi. Nessun parere fiscale sul caso singolo."""
    sportello_plain = (
        (
            "Un bando a sportello può chiudere prima della scadenza?",
            "Sì, quando le risorse finiscono. L'ente lo comunica sul proprio sito.",
        ),
        (
            'Cosa vuol dire "fino a esaurimento risorse"?',
            "Che non c'è una data fissa di chiusura: il bando resta aperto finché ci sono fondi.",
        ),
        (
            "Cos'è la lista d'attesa?",
            "Quando i fondi sono finiti, alcune Camere di Commercio accettano ancora domande, "
            "che vengono finanziate solo se si liberano risorse.",
        ),
        (
            'Cosa vuol dire "click day"?',
            "È uno sportello che apre a un'ora precisa: le risorse possono finire in pochi minuti.",
        ),
    )
    deminimis_plain = (
        (
            "Qual è il limite de minimis?",
            "300.000 € per impresa unica in tre anni, per il regolamento generale; agricoltura e pesca hanno limiti propri. "
            "Il testo è il Regolamento UE 2023/2831.",
        ),
        (
            "Cosa si intende per impresa unica?",
            "L'insieme delle imprese collegate tra loro, per esempio una società e quelle che controlla: gli aiuti si sommano. "
            "La definizione è nel regolamento.",
        ),
        (
            "Come si calcolano i tre anni?",
            "Si guarda il periodo di tre anni che termina con la data della nuova concessione, "
            "sommando gli aiuti de minimis ricevuti in quel periodo, come indica il regolamento.",
        ),
        (
            "Dove verifico gli aiuti ricevuti?",
            "Nel Registro nazionale degli aiuti di Stato (RNA), con la visura per codice fiscale.",
        ),
        (
            "Cos'è la dichiarazione de minimis?",
            "La dichiarazione, richiesta da molti bandi, con cui l'impresa indica gli aiuti de minimis già ricevuti.",
        ),
    )
    # «Il contributo a fondo perduto si tassa?» è un parere da commercialista: non è in pagina.
    fondo_plain = (
        (
            "Che differenza c'è tra contributo a fondo perduto e finanziamento agevolato?",
            "Il primo non si restituisce, il secondo sì ma a condizioni migliori di un prestito normale.",
        ),
        (
            "Cos'è il contributo in conto interessi?",
            "Un contributo che paga in tutto o in parte gli interessi di un finanziamento bancario.",
        ),
        (
            "Cos'è la remissione del debito?",
            "La parte di un finanziamento agevolato che, a certe condizioni, non va restituita.",
        ),
        (
            "Cos'è un voucher?",
            "Un contributo di importo fisso o in percentuale per comprare un servizio o un bene preciso, "
            "per esempio consulenza o digitale.",
        ),
    )
    verifica = f"<p>Per la tua impresa puoi chiedere una {link_verifica()}.</p>"
    sportello = (
        "guida/bando-a-sportello.html",
        "Bando a sportello: cosa significa e come funziona",
        "Cos'è un bando a sportello, come si differenzia da un bando a graduatoria e perché può chiudere prima della scadenza. Con esempi di bandi aperti.",
        "Bando a sportello: cosa significa",
        (
            crumbs([("index.html", "Home"), ("", "Bando a sportello")], "")
            + "<h1>Bando a sportello: cosa significa</h1>"
            + "<p>Un bando a sportello esamina le domande in ordine di arrivo e le finanzia finché ci sono risorse. "
            + "Per questo può chiudere prima della data di scadenza scritta, e conta presentare presto una domanda completa. "
            + "Nel bando a graduatoria, invece, tutte le domande arrivate entro la scadenza vengono valutate insieme "
            + "e finanziate in ordine di punteggio.</p>"
            + "<section><h2>Esempi di bandi aperti</h2>"
            + "<p>Tra le schede a sportello ci sono il Bando 1.3.2 della Regione Toscana e Nuova Sabatini. "
            + "Alcuni bandi della Maremma e del Tirreno, a risorse esaurite, tengono una lista d'attesa.</p>"
            + _esempi(bandi, (
                "bando-132-50k-2026",
                "nuova-sabatini",
                "cciaa-maremma-tirreno-imprese-vicinato-2026",
            ))
            + "</section>"
            + verifica
            + faq_html(sportello_plain)
        ),
        sportello_plain,
    )
    deminimis = (
        "guida/de-minimis.html",
        "Regime de minimis: cos'è, limite e come si calcola",
        "Il de minimis in parole semplici: limite di 300.000 € in tre anni per impresa unica, come si calcola, dove si verifica e cosa chiedono i bandi.",
        "Regime de minimis: cos'è e come funziona",
        (
            crumbs([("index.html", "Home"), ("", "Regime de minimis")], "")
            + "<h1>Regime de minimis: cos'è e come funziona</h1>"
            + "<p>Il regime de minimis permette di dare alle imprese aiuti pubblici di piccolo importo senza notificarli "
            + "alla Commissione europea. Ogni impresa unica può ricevere al massimo 300.000 € di aiuti de minimis "
            + "nell'arco di tre anni (Regolamento UE 2023/2831). Prima di chiedere un contributo conviene controllare "
            + "quanto si è già ricevuto nel Registro nazionale degli aiuti di Stato (RNA). "
            + "Quanto segue è un riassunto del regolamento, non un parere sul caso della singola impresa.</p>"
            + "<p>Fonti: "
            + ext(EURLEX_DE_MINIMIS, "Regolamento UE 2023/2831 su EUR-Lex")
            + " e "
            + ext(RNA_AIUTI, "Registro nazionale degli aiuti di Stato")
            + ".</p>"
            + verifica
            + faq_html(deminimis_plain)
        ),
        deminimis_plain,
    )
    fondo = (
        "guida/fondo-perduto-o-finanziamento-agevolato.html",
        "Fondo perduto o finanziamento agevolato: differenze",
        "Fondo perduto, tasso zero, finanziamento con remissione, contributo in conto interessi e voucher: cosa sono e come leggerli in un bando.",
        "Fondo perduto o finanziamento agevolato: le differenze",
        (
            crumbs([("index.html", "Home"), ("", "Fondo perduto o finanziamento agevolato")], "")
            + "<h1>Fondo perduto o finanziamento agevolato: le differenze</h1>"
            + "<p>Il contributo a fondo perduto non si restituisce; il finanziamento agevolato sì, ma a tasso zero "
            + "o a un tasso più basso di quello di mercato. Molti bandi mescolano le due cose: per esempio "
            + f'{link_bando(next(b for b in bandi if b["id"] == "step-2026-umbria"))} in Umbria è un finanziamento all\'1% '
            + "con una parte che non va restituita, e "
            + f'{link_bando(next(b for b in bandi if b["id"] == "bando-132-50k-2026"))} in Toscana è un contributo a fondo perduto '
            + "che paga gli interessi di un prestito bancario.</p>"
            + verifica
            + faq_html(fondo_plain)
        ),
        fondo_plain,
    )
    return (sportello, deminimis, fondo)


def build(today=None):
    today = today or datetime.date.today()
    bandi = prepare(json.loads(DATA.read_text(encoding="utf-8")), today)
    att = [b for b in bandi if not b["scaduto"]]
    agg = max(b["ultimo_controllo"] for b in bandi)
    D.mkdir(exist_ok=True)
    (D / "bando").mkdir(exist_ok=True)
    (D / "settore").mkdir(exist_ok=True)
    written = set()

    def emit(path, html_text, lastmod, freq, priority):
        pre = prefix(path)
        (D / path).parent.mkdir(parents=True, exist_ok=True)
        (D / path).write_text(fill_footer(html_text, bandi, pre), encoding="utf-8")
        written.add(path)
        urls.append((path, lastmod, freq, priority))

    urls = []
    aperti_home = qty(conto_aperti(bandi), "bando aperto", "bandi aperti")
    hero = hero_block(
        "hero-home",
        "<h1>Bandi aperti per startup e PMI in Toscana, Umbria ed Emilia-Romagna</h1>"
        "<p>IncentiviPerTe raccoglie gratis i bandi aperti per startup e PMI di Toscana, Umbria ed Emilia-Romagna "
        "e gli incentivi nazionali: contributi a fondo perduto, finanziamenti agevolati e voucher delle Camere di "
        "Commercio. Ogni scheda indica importo, destinatari, scadenza, data dell'ultimo controllo e link al bando "
        f"ufficiale. Aggiornato al {it_date(agg)}.</p>"
        f"<p><span data-aperti>{aperti_home}</span>, con scadenza e link alla fonte ufficiale.</p>"
        f'<p class="upd">Aggiornato il {it_date(agg)} · fonti ufficiali · senza cookie</p>'
        '<p class="hero-actions"><a class="btn" href="#filtri">Trova il tuo bando</a>'
        '<a class="btn ghost" href="/check-up">Richiedi il Check-up</a></p>',
    )
    home_title = "Bandi per imprese in Toscana, Umbria ed Emilia-Romagna"
    home_desc = (
        "Bandi e contributi aperti per startup e PMI in Toscana, Umbria, Emilia-Romagna e incentivi nazionali: "
        "fondo perduto, scadenze e link ai bandi ufficiali."
    )
    home_plain, home_marcate = home_faq()
    home_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": SITE, "url": BASE, "inLanguage": "it-IT", "publisher": org_ld()},
            org_ld(),
            item_list(att),
            faq_ld(home_plain),
        ],
    }
    raccolte = (
        "<p>Raccolte: "
        f'<a href="{site_href(HUB_TOSCANA)}">{e(HUB_TITOLO_TOSCANA)}</a>, '
        f'<a href="{site_href(HUB_ER)}">{e(HUB_TITOLO_ER)}</a>, '
        f'<a href="{site_href(PAGINA_APRIRE)}">{e(APRIRE_TITOLO).replace("Contributi", "contributi", 1)}</a>.</p>'
    )
    home_body = (
        f'<p class="note">Queste sono sintesi. Prima di fare domanda, controlla requisiti e scadenze sul sito dell&#39;ente.</p>'
        f"{raccolte}"
        f'<div id="filtri">{filter_form(bandi)}</div>'
        '<noscript><p class="note">Senza JavaScript restano visibili tutti i bandi aperti. I filtri girano solo sul tuo dispositivo e non inviano dati.</p></noscript>'
        f"{grid(bandi, '', today)}{JS}{hubs(bandi, '')}{checkup_section('', con_immagine=True, variante='home')}{faq_html(home_marcate, raw=True)}{fpef_box()}"
    )
    emit(
        "index.html",
        page(
            "index.html", home_title, home_desc, home_body,
            hero, home_ld, extra_head=hero_home_preload(),
        ),
        lastmod_pagina("index.html", agg), "weekly", "1.0",
    )
    for reg in REG:
        rows = [b for b in att if b["regione"] == reg]
        path = region_path(reg)
        label = "Nazionali" if reg == "Nazionale" else reg
        title, desc, h1_fix = AREA_SEO[reg]
        n_area = sum(1 for b in rows if is_aperto(b))
        others = pills(area_links(bandi, "", reg))
        sectors_here = sort_dest({d for b in rows for d in b["destinatari"]})
        sector_pills = pills([
            (site_href(sector_path(name)), name, sum(1 for b in rows if name in b["destinatari"]))
            for name in sectors_here
        ]) if sectors_here else ""
        listing = grid(rows, "", today) if rows else '<p class="note">Nessun bando aperto in questa area. Guarda le altre aree qui sotto.</p>'
        sezioni = ""
        faq_plain = ()
        faq_block = ""
        if reg == "Toscana":
            sezioni, faq_plain, faq_html_pairs = sezioni_toscana(rows)
            faq_block = faq_html(faq_html_pairs, raw=True)
        elif reg == "Umbria":
            sezioni, faq_plain = sezioni_umbria(rows)
            faq_block = faq_html(faq_plain)
        elif reg == "Emilia-Romagna":
            faq_plain = sezioni_emilia()
            faq_block = faq_html(faq_plain)
        extra_link = ""
        if reg == "Emilia-Romagna":
            extra_link = (
                f'<p>I bandi camerali, Camera per Camera: '
                f'<a href="{site_href(HUB_ER)}">{e(HUB_TITOLO_ER)}</a>.</p>'
            )
        body = (
            crumbs([("index.html", "Bandi"), ("", label)], "")
            + f"<h1>{e(h1_fix)}</h1>"
            + apertura_area(reg, n_area, agg)
            + extra_link
            + f'<p><a href="{site_href("index.html", urllib.parse.urlencode({"area": reg}), "filtri")}">Trova il tuo bando</a></p>'
            + sezioni
            + listing
            + (f'<section aria-labelledby="dest-qui"><h2 id="dest-qui">Destinatari</h2>{sector_pills}</section>' if sector_pills else "")
            + f'<section aria-labelledby="altre-aree"><h2 id="altre-aree">Altre aree</h2>{sec_img("bandi-per-area", 800, 308)}{others}</section>'
            + fpef_box()
            + faq_block
        )
        graph = [
            {"@type": "CollectionPage", "name": title, "url": public_url(path), "inLanguage": "it-IT", "isPartOf": BASE},
            breadcrumb_ld([("", "Bandi"), (path, label)]),
            item_list(rows),
        ]
        if faq_plain:
            graph.append(faq_ld(faq_plain))
        ld = {"@context": "https://schema.org", "@graph": graph}
        emit(path, page(path, title, desc, body, ld=ld, title_as_is=True), lastmod_pagina(path, agg), "weekly", "0.8")

    names = sort_dest({d for b in bandi for d in b["destinatari"]})
    for name in names:
        rows = [b for b in att if name in b["destinatari"]]
        path = sector_path(name)
        regs = [reg for reg in REG if any(b["regione"] == reg for b in rows)]
        where = join_it(["nazionali" if r == "Nazionale" else r for r in regs]) or "nessuna area"
        title, desc, h1_fix, paragrafo = SETTORE_SEO[name]
        n_settore = sum(1 for b in rows if is_aperto(b))
        extra = ""
        if name == "Nuove imprese":
            extra = (
                " Per la Toscana c'è anche la pagina "
                f'<a href="{site_href(PAGINA_APRIRE)}">{e(APRIRE_TITOLO)}</a>.'
            )
        elif name == "Under 35":
            extra = (
                " In Toscana: "
                f'<a href="{site_href(PAGINA_APRIRE)}">{e(APRIRE_TITOLO).replace("Contributi", "contributi", 1)}</a>.'
            )
        listing = grid(rows, "../", today) if rows else '<p class="note">Nessun bando aperto per questo destinatario. Guarda gli altri destinatari qui sotto.</p>'
        faq_block = faq_html(FAQ_DONNE) if name == "Donne" else ""
        body = (
            crumbs([("index.html", "Bandi"), ("", name)], "../")
            + f"<h1>{e(h1_fix)}</h1>"
            + f"<p>{e(paragrafo)}{extra} Aggiornato al {e(it_date(agg))}.</p>"
            + f"<p>{riga_aperti(n_settore)}, aree {e(where)}.</p>"
            + f'<p><a href="{site_href("index.html", urllib.parse.urlencode({"dest": name}), "filtri")}">Trova il tuo bando</a></p>'
            + listing
            + '<section aria-labelledby="altre-aree"><h2 id="altre-aree">Aree</h2>'
            + pills(area_links(bandi, "../"))
            + '</section><section aria-labelledby="altri-dest"><h2 id="altri-dest">Altri destinatari</h2>'
            + '<div class="with-illu"><div>'
            + pills(dest_links(bandi, "../", name))
            + "</div>"
            + sec_img("bandi-per-destinatario", 800, 600)
            + "</div></section>"
            + fpef_box()
            + faq_block
        )
        graph = [
            {"@type": "CollectionPage", "name": title, "url": public_url(path), "inLanguage": "it-IT", "about": name},
            breadcrumb_ld([("", "Bandi"), (path, name)]),
            item_list(rows),
        ]
        if name == "Donne":
            graph.append(faq_ld(FAQ_DONNE))
        ld = {"@context": "https://schema.org", "@graph": graph}
        emit(path, page(path, title, desc, body, ld=ld, title_as_is=True), lastmod_pagina(path, agg), "weekly", "0.8")

    for b in bandi:
        path = f'bando/{b["id"]}.html'
        area_href = region_path(b["regione"])
        area_label = "Nazionali" if b["regione"] == "Nazionale" else b["regione"]
        nome = seo_copy.h1_scheda(b)
        dest_html = ", ".join(
            f'<a href="{site_href(sector_path(d))}">{e(d)}</a>' for d in b["destinatari"]
        )
        sibs = related(b, bandi)
        related_html = ""
        if sibs:
            lis = "".join(
                f'<li><a href="{site_href(f"bando/{o["id"]}.html")}">{e(seo_copy.titolo_in_elenco(o))}<span>{e(o["regione"])} · {e(deadline_text(o))}</span></a></li>'
                for o in sibs
            )
            related_html = f'<section class="related" aria-labelledby="collegati"><h2 id="collegati">Bandi collegati</h2><ul>{lis}</ul></section>'
        tags = f'<a class="tag area" href="{site_href(area_href)}">{e(b["regione"])}</a>' + "".join(
            f'<a class="tag" href="{site_href(sector_path(d))}">{e(d)}</a>' for d in b["destinatari"]
        )
        when = f' data-deadline="{b["scadenza"]}"' if b["scadenza"] else ""
        if b.get("apertura"):
            when += f' data-apre="{b["apertura"]}"'
        lead = seo_copy.lead_scheda(b, deadline_text(b))
        if b["id"] == "resto-al-sud-2":
            lead_html = e(lead).replace(
                "Autoimpiego Centro-Nord",
                f'<a href="{site_href("bando/autoimpiego-centro-nord.html")}">Autoimpiego Centro-Nord</a>',
                1,
            )
        else:
            lead_html = e(lead)
        chiuso = ""
        if b["scaduto"]:
            chiuso = "<p>Questo bando è chiuso. Più sotto, i bandi collegati sono misure aperte simili.</p>"
        faq_plain, faq_html_pairs = faq_scheda_html(b)
        faq_block = faq_html(faq_html_pairs, raw=True) if faq_html_pairs else ""
        body = (
            crumbs([("index.html", "Bandi"), (area_href, area_label), ("", nome)], "../")
            + f'<article class="box">{badge(b, today)}<div class="tags">{tags}</div><h1>{e(nome)}</h1>'
            + chiuso
            + avviso_fondi(b, con_link=True)
            + "<dl class=\"kv\">"
            + f"<dt>Ente</dt><dd>{e(b['ente'])}</dd>"
            + f'<dt>Area</dt><dd><a href="{site_href(area_href)}">{e(b["regione"])}</a></dd>'
            + f"<dt>Destinatari</dt><dd>{dest_html}</dd>"
            + f"<dt>Importo</dt><dd>{e(b['importo'])}</dd>"
            + f"<dt>Scadenza</dt><dd><strong{when}>{e(deadline_text(b))}</strong><br><small>{e(b['nota_scadenza'])}</small></dd>"
            + f"<dt>Ultimo controllo</dt><dd>{it_date(b['ultimo_controllo'])}</dd>"
            + "</dl>"
            + f"<p>{lead_html}</p>"
            + f"<p>{e(b['sintesi'])}</p>"
            + official_bando_link(b["url"])
            + fonte_fuori_avviso(b)
            + rimando_camera(b)
            + bando_checkup_box()
            + checkup_ask()
            + '<p class="note">Sintesi indicativa. Fa fede esclusivamente il testo ufficiale pubblicato dall&#39;ente. <a href="/disclaimer">Disclaimer</a></p></article>'
            + faq_block
            + related_html
            + '<aside class="sp" aria-label="Spazio sponsor"><span class="lab">Sponsorizzato</span>'
            + '<p class="spt">Spazio disponibile per commercialisti, consulenti, banche e software</p>'
            + f'<p class="spp">{SPONSOR_DA}</p>'
            + '<p><a class="btn outline" href="/sponsor">Scopri gli spazi sponsor</a></p></aside>'
            + fpef_box()
            + BADGE_JS
        )
        desc = seo_copy.meta_scheda(b)
        modificato = lastmod_pagina(path, b["ultimo_controllo"])
        grant = {
            "@type": "MonetaryGrant",
            "name": nome,
            "description": b["sintesi"],
            "url": b["url"],
            "funder": {"@type": "Organization", "name": b["ente"]},
            "areaServed": "Italia" if b["regione"] == "Nazionale" else b["regione"],
        }
        graph = [
            {
                "@type": "WebPage",
                "name": nome,
                "url": public_url(path),
                "inLanguage": "it-IT",
                "dateModified": modificato,
                "isBasedOn": b["url"],
                "publisher": org_ld(),
                "about": grant,
            },
            breadcrumb_ld([("", "Bandi"), (area_href, area_label), (path, nome)]),
            grant,
        ]
        if faq_plain:
            graph.append(faq_ld(faq_plain))
        ld = {"@context": "https://schema.org", "@graph": graph}
        emit(
            path,
            page(path, seo_copy.titolo_scheda(b), desc, body, ld=ld, title_as_is=True),
            modificato,
            "weekly",
            "0.7",
        )

    for path, (title, desc, body, with_tool) in static_pages(today).items():
        if with_tool:
            body += fpef_box()
        ld = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "url": public_url(path),
            "inLanguage": "it-IT",
            "publisher": org_ld(),
        }
        if path == "check-up.html":
            webpage = {k: v for k, v in ld.items() if k != "@context"}
            ld = {
                "@context": "https://schema.org",
                "@graph": [
                    webpage,
                    checkup_service(),
                    faq_ld(checkup_faq()),
                    breadcrumb_ld([("", "Home"), ("check-up.html", "Check-up Bandi")]),
                ],
            }
        freq = "monthly" if path in ("sponsor.html", "check-up.html") else "yearly"
        priority = "0.8" if path in ("sponsor.html", "check-up.html") else "0.3"
        hero = ""
        if path == "check-up.html":
            hero = hero_block(
                "hero-check-up",
                "<h1>Check-up Bandi: quali bandi sono adatti alla tua impresa</h1>",
            )
        elif path == "sponsor.html":
            hero = hero_block("hero-sponsor", "<h1>Sponsor e pubblicità</h1>")
        as_is = path in ("chi-siamo.html", "contatti.html", "sponsor.html", "check-up.html")
        emit(
            path,
            page(path, title, desc, body, hero, ld=ld, title_as_is=as_is),
            lastmod_pagina(path, agg),
            freq,
            priority,
        )

    # Pagine nuove, in coda alla sitemap: le URL già pubblicate restano davanti, nello stesso ordine.
    para_t = (
        "Le Camere di Commercio toscane finanziano ogni anno le imprese della propria provincia con voucher "
        "e contributi a fondo perduto, di solito tra 1.500 € e 5.000 € per impresa, per avvio d'impresa, "
        "digitale, sostenibilità, fiere e sicurezza. Qui trovi i bandi aperti, Camera per Camera, con scadenza "
        f"e link al bando ufficiale. Aggiornato al {it_date(agg)}."
    )
    meta_t = (
        "Voucher e contributi a fondo perduto delle Camere di Commercio toscane: Firenze, Arezzo e Siena, "
        "Livorno-Grosseto, Pisa-Lucca-Massa, Pistoia-Prato."
    )
    title_t = "Bandi Camere di Commercio Toscana 2026: voucher aperti"
    toscane = [b for b in bandi if b["regione"] == "Toscana" and chiave_camera(b)]
    emit(
        HUB_TOSCANA,
        page(
            HUB_TOSCANA, title_t, meta_t,
            corpo_camere(HUB_TITOLO_TOSCANA, para_t, CAMERE_TOSCANA, bandi, today, FAQ_CAMERE),
            ld=ld_raccolta(HUB_TOSCANA, title_t, HUB_TITOLO_TOSCANA, toscane, FAQ_CAMERE),
            title_as_is=True,
        ),
        SEO_LASTMOD, "weekly", "0.8",
    )
    para_er = (
        "Le Camere di Commercio dell'Emilia-Romagna sostengono le imprese del territorio con contributi a fondo "
        "perduto e con aiuti sul costo del credito tramite i Confidi. Qui trovi i bandi aperti di Bologna, "
        "dell'Emilia (Parma, Piacenza, Reggio Emilia), di Ferrara e Ravenna, di Modena e della Romagna "
        f"(Forlì-Cesena e Rimini), con scadenza e link ufficiale. Aggiornato al {it_date(agg)}."
    )
    meta_er = (
        "Contributi e voucher delle Camere di Commercio di Bologna, Emilia, Ferrara-Ravenna, Modena e Romagna: "
        "bandi aperti, importi, scadenze e link ufficiali."
    )
    title_er = "Bandi Camere di Commercio Emilia-Romagna 2026"
    faq_er = FAQ_CAMERE + (FAQ_CONFIDI,)
    emiliane = [b for b in bandi if b["regione"] == "Emilia-Romagna" and chiave_camera(b)]
    emit(
        HUB_ER,
        page(
            HUB_ER, title_er, meta_er,
            corpo_camere(HUB_TITOLO_ER, para_er, CAMERE_ER, bandi, today, faq_er),
            ld=ld_raccolta(HUB_ER, title_er, HUB_TITOLO_ER, emiliane, faq_er),
            title_as_is=True,
        ),
        SEO_LASTMOD, "weekly", "0.8",
    )
    corpo_a, faq_a, voci_a = corpo_aprire(bandi, agg)
    meta_a = (
        "Fondo perduto, tasso zero e voucher per chi apre un'impresa in Toscana: bandi delle Camere di Commercio, "
        "della Regione e nazionali. Requisiti e scadenze."
    )
    emit(
        PAGINA_APRIRE,
        page(
            PAGINA_APRIRE, APRIRE_TITLE, meta_a, corpo_a,
            ld=ld_raccolta(PAGINA_APRIRE, APRIRE_TITLE, APRIRE_TITOLO, voci_a, faq_a),
            title_as_is=True,
        ),
        SEO_LASTMOD, "weekly", "0.8",
    )
    for path, title, desc, h1, body, faq in corpo_guide(bandi):
        emit(
            path,
            page(path, title, desc, body, ld=ld_guida(path, title, h1, faq), title_as_is=True),
            SEO_LASTMOD, "monthly", "0.6",
        )

    # Il vecchio indirizzo resta raggiungibile, ma non è una seconda pagina: rimanda a /check-up
    # e non entra nella sitemap.
    alias = page(
        "check-up-bandi.html",
        "Check-up Bandi",
        "Il Check-up Bandi è sulla pagina Check-up.",
        "<h1>Check-up Bandi</h1><div class='box'>"
        "<p>Il Check-up Bandi è su un'unica pagina.</p>"
        f'<p><a class="btn" href="{site_href("check-up.html")}">Vai al Check-up</a></p></div>',
    )
    (D / "check-up-bandi.html").write_text(fill_footer(alias, bandi, prefix("check-up-bandi.html")), encoding="utf-8")
    written.add("check-up-bandi.html")

    # La 404 può essere servita da qualsiasi percorso: i link partono dalla radice.
    # Gli schemi (mailto:, https:) restano intatti.
    not_found = fill_footer(page(
        "404.html",
        "Pagina non trovata",
        "La pagina richiesta non esiste.",
        '<div class="box"><h1>Pagina non trovata</h1><p>La pagina che cerchi non esiste o è stata spostata. Il bando potrebbe essere scaduto e non essere più in elenco.</p><p><a class="btn" href="/">Torna ai bandi</a></p></div>',
        robots="noindex",
    ), bandi, "/")
    not_found = re.sub(
        r'\b(href|src)="(?![a-z][a-z0-9+.-]*:|/|#)([^"]*)"',
        r'\1="/\2"',
        not_found,
        flags=re.I,
    )

    def root_srcset(match):
        parts = []
        for item in match.group(1).split(","):
            bits = item.split()
            if not bits:
                continue
            url, rest = bits[0], bits[1:]
            if not re.match(r"(?:[a-z][a-z0-9+.-]*:|/|#)", url, re.I):
                url = "/" + url
            parts.append(" ".join([url, *rest]))
        return 'srcset="' + ", ".join(parts) + '"'

    not_found = re.sub(r'\bsrcset="([^"]*)"', root_srcset, not_found, flags=re.I)
    (D / "404.html").write_text(not_found, encoding="utf-8")
    written.add("404.html")

    urlset = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod, freq, priority in urls:
        loc = public_url(path)
        urlset.append(
            f"<url><loc>{loc}</loc><lastmod>{lastmod}</lastmod><changefreq>{freq}</changefreq><priority>{priority}</priority></url>"
        )
    urlset.append("</urlset>")
    (D / "sitemap.xml").write_text("\n".join(urlset) + "\n", encoding="utf-8")
    (D / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    write_assets()
    cleanup(written)
    # Dopo cleanup: gli html non generati come pagine vengono eliminati, e questo file non è una pagina.
    write_search_console()
    self_check(written)
    print(f"OK: {len(bandi)} bandi, {len(written)} pagine -> {D}")
    return written


def main():
    try:
        build()
    except ValueError as ex:
        print(f"ERRORE: {ex}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
