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
    "Prezzi + IVA. Con carta su Gumroad l'IVA del tuo Paese è calcolata e versata da Gumroad."
)
CHECKUP_LANCIO = (
    "Con LANCIO15 fino al 30/10/2026: Base 41,65 € + IVA, Completo 67,15 € + IVA."
)
SPONSOR_DA = "Da 49 € + IVA al mese · prezzo di lancio"
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
     "Sì. Uno spazio su IncentiviPerTe parte da 49 € + IVA al mese, prezzo di lancio. Importi, regole ed etichetta Sponsorizzato sono sulla pagina Sponsor."),
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
STATIC_ASSETS = (
    "favicon.svg", "favicon-16.png", "favicon-32.png", "favicon-48.png", "favicon-512.png",
    "apple-touch-icon.png", "logo-header.svg", "logo-header-80.png", "logo-header-160.png",
    "og.png",
)
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


def card(b, pre, today):
    tags = f'<span class="tag area">{e(b["regione"])}</span>'
    tags += "".join(f'<span class="tag">{e(d)}</span>' for d in b["destinatari"])
    note = card_note(b)
    avviso = avviso_fondi(b)
    search_bits = [b["titolo"], b["sintesi"], b["ente"], b["regione"], " ".join(b["destinatari"])]
    frase_stato = STATI.get(stato_bando(b)) or ""
    if note or frase_stato:
        search_bits.append(b.get("nota_scadenza") or "")
    if frase_stato:
        search_bits.append(frase_stato)
    search = " ".join(" ".join(search_bits).split())
    hidden = " hidden" if b["scaduto"] else ""
    href = site_href(f'bando/{b["id"]}.html')
    when = f' data-deadline="{b["scadenza"]}"' if b["scadenza"] else ""
    if b.get("apertura"):
        when += f' data-apre="{b["apertura"]}"'
    return (
        f'<article class="card" data-reg="{e(b["regione"])}" '
        f'data-dest="{e("|".join(b["destinatari"]))}" data-scad="{b["scadenza"] or "9999-12-31"}" '
        f'data-apre="{e(b.get("apertura") or "")}" '
        f'data-scaduto="{1 if b["scaduto"] else 0}" data-search="{e(search)}"{hidden}>'
        f'{badge(b, today)}{avviso}<h3><a class="cardlink" href="{href}">{e(b["titolo"])}</a></h3>'
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
        "(da 49 € + IVA). Verifica di ammissibilità, non garantisce il contributo.</p>"
        f"<p>{CHECKUP_IVA_NOTE}</p>"
        "</aside>"
    )


def checkup_section(pre):
    return (
        '<section class="checkup" aria-labelledby="checkup-title"><div class="box">'
        "<h2 id=\"checkup-title\">Check-up Bandi</h2>"
        "<p>Controllo personalizzato di quali bandi regionali e nazionali sono adatti alla tua impresa: "
        "tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), Umbria, Emilia-Romagna e incentivi nazionali "
        "per avviare e far crescere l'impresa, tra cui finanziamenti a tasso zero e contributi a fondo perduto "
        "per nuove imprese, startup innovative e investimenti. Il risultato è una relazione scritta.</p>"
        f'<p><a class="btn" href="{site_href("check-up.html")}">Richiedi il Check-up</a></p>'
        "</div></section>"
    )


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
    att = sum(1 for b in bandi if not b["scaduto"])
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
      var ok = expired.checked || card.getAttribute("data-scaduto") !== "1";
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
    var n = visible.length;
    var label = n === 0 ? "Nessun bando con questi filtri. Modifica la ricerca o mostra gli scaduti." : (n === 1 ? "1 bando trovato" : n + " bandi trovati");
    if (count.textContent !== label) count.textContent = label;
  }
  readUrl();
  apply();
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
        + pills(area_links(bandi, pre))
        + '</section><section aria-labelledby="dest-title"><h2 id="dest-title">Bandi per destinatario</h2>'
        + pills(dest_links(bandi, pre))
        + "</section>"
    )


def faq_html():
    blocks = []
    for q, a in FAQ:
        blocks.append(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>")
    return '<section class="faq" aria-labelledby="faq-title"><h2 id="faq-title">Domande frequenti</h2>' + "".join(blocks) + "</section>"


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


def page(path, title, desc, body, hero="", ld=None, robots=None):
    pre = prefix(path)
    # /check-up-bandi è solo un rimando: canonical e social puntano alla pagina vera.
    url = public_url("check-up.html") if path == "check-up-bandi.html" else public_url(path)
    full = title if path == "index.html" else f"{title} – {SITE}"
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
{ld_html}
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
    return f"""<footer><div class="wrap">
<p><strong>{SITE}</strong> · raccolta gratuita e indipendente di bandi per startup e PMI, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali. Le schede sono sintesi: fa fede solo il bando ufficiale.</p>
<nav aria-label="Aree"><p><strong>Aree</strong></p><ul id="foot-aree"></ul></nav>
<nav aria-label="Destinatari"><p><strong>Destinatari</strong></p><ul id="foot-dest"></ul></nav>
<nav aria-label="Informazioni"><ul>{links}</ul></nav>
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
            f"Base, 49 € + IVA: {CHECKUP_BASE}. Completo, 79 € + IVA: {CHECKUP_COMPLETO}. "
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
                "description": f"Base, 49 € + IVA: {CHECKUP_BASE}. {CHECKUP_IVA_NOTE}",
            },
            {
                "@type": "Offer",
                "name": "Completo",
                "price": "79",
                "priceCurrency": "EUR",
                "description": f"Completo, 79 € + IVA: {CHECKUP_COMPLETO}. {CHECKUP_IVA_NOTE}",
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


def bonifico_link(level, product, price):
    subject = f"Richiesta Check-up {level} – pagamento con bonifico istantaneo"
    body = (
        f"Livello: {level}\n"
        f"Prodotto: {product}\n"
        f"Importo: {price}\n"
        "Codice di lancio: LANCIO15\n"
    )
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


def pay_level(product, price, level, url):
    amount = price + " + IVA"
    return (
        '<div class="pay-level">'
        f"<h3>{e(product)}</h3>"
        '<div class="pay-actions">'
        f"{pay_choice(bonifico_link(level, product, amount), amount)}"
        f"{pay_choice(card_pay_link(url), amount)}"
        "</div></div>"
    )


def checkup_pay_section():
    return (
        '<section class="paga" aria-labelledby="paga-ora">'
        '<h2 id="paga-ora">Paga ora</h2>'
        "<p>Il Check-up è una verifica di ammissibilità e non garantisce l'ottenimento del contributo.</p>"
        f"<p>{CHECKUP_IVA_NOTE}</p>"
        + pay_level(CHECKUP_PRODUCT_BASE, "49 €", "Base", GUMROAD_CHECKUP_BASE_URL)
        + pay_level(CHECKUP_PRODUCT_COMPLETO, "79 €", "Completo", GUMROAD_CHECKUP_COMPLETO_URL)
        + "<p>Bonifico istantaneo: l'IBAN non è pubblicato sul sito. "
        + f"Dopo la richiesta lo inviamo per email da {mail_link()}.</p>"
        + "</section>"
    )


def checkup_body():
    tipi = (
        "Startup", "PMI", "Nuove imprese", "Under 35", "Donne",
        "Professionisti", "Grandi imprese", "Altro",
    )
    stadi = ("Da costituire", "Appena costituita", "In attività", "In crescita")
    tipo_opts = "".join(f'<option value="{e(x)}">{e(x)}</option>' for x in tipi)
    stadio_opts = "".join(f'<option value="{e(x)}">{e(x)}</option>' for x in stadi)
    extra = "".join(f"<li>{e(item)}</li>" for item in CHECKUP_EXTRA)
    return f"""<h1>Check-up Bandi</h1><div class="box">
<p>Ricevi una relazione scritta sui bandi adatti alla tua impresa: tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), Umbria, Emilia-Romagna e incentivi nazionali per avviare e far crescere l'impresa.</p>
<h2>Livelli del servizio</h2>
<ul>
<li><strong>Base</strong>, 49 € + IVA: {e(CHECKUP_BASE)}.</li>
<li><strong>Completo</strong>, 79 € + IVA: report di 6-10 pagine, entro 7-10 giorni lavorativi dalla ricezione dei dati completi. Include tutto il Base, più:<ul>{extra}</ul></li>
</ul>
<p>{CHECKUP_IVA_NOTE}</p>
<aside class="promo" aria-label="Codice di lancio">
<p class="lab">Codice di lancio</p>
<p class="code">LANCIO15</p>
<p>{CHECKUP_LANCIO}</p>
</aside>
<h2>Chi lo prepara</h2>
<p>Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.</p>
<div class="checkup-split">
<div>
<form id="checkup-form" class="checkup-form">
<div><label for="cu-regione">Regione (comprende la provincia)</label><input id="cu-regione" name="regione" type="text" required autocomplete="address-level1"></div>
<div><label for="cu-tipo">Tipo di impresa</label><select id="cu-tipo" name="tipo" required><option value="">Scegli</option>{tipo_opts}</select></div>
<div><label for="cu-stadio">Stadio</label><select id="cu-stadio" name="stadio" required><option value="">Scegli</option>{stadio_opts}</select></div>
<div><label for="cu-importo">Importo indicativo</label><input id="cu-importo" name="importo" type="text" required inputmode="decimal" placeholder="es. 50.000 €"></div>
<fieldset><legend>Livello</legend><div class="livelli">
<label><input type="radio" name="livello" value="Base" required> Base · 49 € + IVA</label>
<label><input type="radio" name="livello" value="Completo"> Completo · 79 € + IVA</label>
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
{checkup_pay_section()}
</div>
</div>
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
        f"<p>Per le sponsorizzazioni FoglioPEF (39 € + IVA al mese) e per il pacchetto entrambi i siti "
        f"(69 € + IVA al mese) scrivi a {fpef_mail}.</p>"
    )
    fpef_space = f'<span class="for">Contatto per FoglioPEF: {fpef_mail}</span>'
    fpef_pack = f'<span class="for">Contatto per entrambi i siti: {fpef_mail}</span>'
    owner = f"Davide Davoglio, Arezzo (Italia) – contattabile tramite i messaggi della {li} o all'indirizzo {mail}."
    return {
        "chi-siamo.html": (
            "Chi siamo",
            "IncentiviPerTe, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna e per gli incentivi nazionali: metodo, team e Check-up Bandi.",
            "<h1>Chi siamo</h1><div class='box'>"
            "<p>IncentiviPerTe è una raccolta gratuita e indipendente di bandi e incentivi per startup e PMI, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali. In Toscana la copertura è tutta la regione: bandi regionali e delle Camere di Commercio toscane.</p>"
            "<p>Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.</p>"
            "<h2>Metodo</h2><p>Ogni scheda è redatta partendo dalla fonte ufficiale (ministeri, Regioni, Sviluppo Toscana, Camere di Commercio toscane, Gepafin e altri enti) e riporta il link al bando e la data dell'ultimo controllo. Le pagine ufficiali vengono ricontrollate periodicamente e ogni anomalia è verificata a mano. I bandi scaduti vengono rimossi.</p>"
            "<h2>Indipendenza</h2><p>Non siamo un ente pubblico né siamo affiliati agli enti citati. Le schede gratuite sono sintesi informative e non sostituiscono il testo del bando. Il sito si sostiene con spazi sponsor sempre etichettati come <em>Sponsorizzato</em>, che non influenzano la selezione dei bandi.</p>"
            "<p>Per gli spazi pubblicitari vedi <a href='/sponsor'>Sponsor</a>. Per segnalare un bando o una correzione, <a href='/contatti'>Contatti</a>. Per il Check-up, <a href='/check-up'>Richiedi il Check-up</a>.</p></div>"
            + checkup_section(""),
            True,
        ),
        "contatti.html": (
            "Contatti",
            "Come contattare IncentiviPerTe: segnalazioni di bandi, Check-up Bandi e richieste sponsor.",
            f"<h1>Contatti</h1><div class='box'><p>Per segnalare un bando, una correzione o per informazioni sugli spazi sponsor scrivici tramite i messaggi della Pagina LinkedIn IncentiviPerTe oppure all'indirizzo email:</p>{contacts}<p>Le schede pubblicate restano sintesi: requisiti e domanda si verificano sull'ente che gestisce la misura. Il Check-up Bandi è la relazione scritta sui bandi adatti: <a href='/check-up'>Richiedi il Check-up</a>. Gli spazi pubblicitari sono descritti nella pagina <a href='/sponsor'>Sponsor</a>.</p></div>",
            False,
        ),
        "sponsor.html": (
            "Sponsor e pubblicità",
            "Spazi sponsor su IncentiviPerTe da 49 € + IVA al mese, su FoglioPEF da 39 € + IVA al mese e su entrambi i siti a 69 € + IVA al mese.",
            f"""<h1>Sponsor e pubblicità</h1><div class="box">
<p>IncentiviPerTe è letto da imprenditori, startup e PMI che cercano finanziamenti. Gli spazi sono per <strong>commercialisti, consulenti di finanza agevolata, banche e software</strong> per le imprese.</p>
{sponsor_contacts}
<h2>Cosa include lo spazio su IncentiviPerTe</h2>
<ul><li>Un posto in <strong>home page</strong></li><li>Un posto nelle <strong>pagine regionali</strong> (Toscana, Umbria, Emilia-Romagna) e nei bandi nazionali</li><li>Un posto nelle <strong>schede dei bandi</strong></li><li>Etichetta <strong>Sponsorizzato</strong> sempre visibile</li></ul>
<h2 id="prezzi">Prezzi</h2>
<p>I prezzi qui sotto sono per uno spazio pubblicitario etichettato Sponsorizzato. Non sono il prezzo dei modelli Excel.</p>
<div class="offers">
<div class="offer featured"><h3>IncentiviPerTe</h3><p class="price"><strong>49 € + IVA</strong> al mese</p><p class="launch">Prezzo di lancio: 3 posti, poi 79 € + IVA al mese</p><p class="fine">Il prezzo sale man mano che si vendono gli spazi: 49 € + IVA al mese per i primi 3 sponsor, poi 79 € + IVA al mese, poi 99 € + IVA al mese. Nessun pagamento online: ti rispondiamo con i dettagli.</p><div class="contact-links">{ipt_btn}{li_btn}{mail}</div></div>
<div class="offer"><h3>FoglioPEF</h3><p class="price"><strong>39 € + IVA</strong> al mese</p><p class="launch">Spazio su FoglioPEF</p><p class="fine">Modelli Excel per immobili e cassa: {ext(FPEF, "fogliopef.github.io")}. Stessa etichetta <strong>Sponsorizzato</strong>.</p><div class="contact-links">{fpef_btn}{fpef_space}</div></div>
<div class="offer"><h3>Entrambi i siti</h3><p class="price"><strong>69 € + IVA</strong> al mese</p><p class="launch">Pacchetto entrambi i siti: IncentiviPerTe + FoglioPEF</p><p class="fine">Uno spazio su IncentiviPerTe e uno su FoglioPEF, entrambi etichettati <strong>Sponsorizzato</strong>. Nessun pagamento online: ti rispondiamo con i dettagli.</p><div class="contact-links">{fpef_btn}{fpef_pack}</div></div>
</div>
<h2>Regole</h2>
<ul><li>Ogni contenuto a pagamento è etichettato <strong>Sponsorizzato</strong>.</li><li>Gli sponsor non influenzano quali bandi pubblichiamo né come li descriviamo.</li><li>Nessun tracciamento degli utenti: niente pixel, cookie o script di terze parti.</li></ul>
<p>Domande? Scrivici a {mail} o in un messaggio alla {ext(LINKEDIN, "nostra pagina LinkedIn")}. Per le sponsorizzazioni FoglioPEF (39 € + IVA al mese) e per il pacchetto entrambi i siti (69 € + IVA al mese): {fpef_mail}.</p>
</div>""",
            False,
        ),
        "check-up.html": (
            "Check-up Bandi",
            "Check-up Bandi: relazione scritta sui bandi adatti. Base entro 5 giorni lavorativi, Completo entro 7-10 giorni lavorativi. "
            + CHECKUP_IVA_NOTE,
            checkup_body(),
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
                "name": b["titolo"],
            }
            for i, b in enumerate((b for b in items if not b["scaduto"]), start=1)
        ],
    }


def write_assets():
    for name in STATIC_ASSETS:
        shutil.copy(R / "assets" / name, D / name)
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
    hero = (
        '<section class="hero"><div class="wrap">'
        "<h1>Bandi e incentivi per startup e PMI</h1>"
        f"<p>Raccolta gratuita, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali: <span data-aperti>{qty(sum(1 for b in att if is_aperto(b)), 'bando aperto', 'bandi aperti')}</span>, con scadenza e link alla fonte ufficiale.</p>"
        f'<p class="upd">Aggiornato il {it_date(agg)} · fonti ufficiali · senza cookie</p>'
        '<p class="hero-actions"><a class="btn" href="#filtri">Trova il tuo bando</a>'
        '<a class="btn ghost" href="/check-up">Richiedi il Check-up</a></p>'
        "</div></section>"
    )
    home_desc = clip(
        "Bandi aperti per startup e PMI, da Arezzo: tutta la Toscana, Umbria, Emilia-Romagna e incentivi nazionali, con scadenze e link ufficiali."
    )
    home_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": SITE, "url": BASE, "inLanguage": "it-IT", "publisher": org_ld()},
            org_ld(),
            item_list(att),
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in FAQ
                ],
            },
        ],
    }
    home_body = (
        f'<p class="note">Queste sono sintesi. Prima di fare domanda, controlla requisiti e scadenze sul sito dell&#39;ente.</p>'
        f'<div id="filtri">{filter_form(bandi)}</div>'
        '<noscript><p class="note">Senza JavaScript restano visibili tutti i bandi aperti. I filtri girano solo sul tuo dispositivo e non inviano dati.</p></noscript>'
        f"{grid(bandi, '', today)}{JS}{hubs(bandi, '')}{checkup_section('')}{faq_html()}{fpef_box()}"
    )
    emit(
        "index.html",
        page("index.html", f"{SITE} – Bandi e incentivi per startup e PMI", home_desc, home_body, hero, home_ld),
        agg, "weekly", "1.0",
    )
    for reg in REG:
        rows = [b for b in att if b["regione"] == reg]
        path = region_path(reg)
        label = "Nazionali" if reg == "Nazionale" else reg
        title = "Bandi e incentivi nazionali" if reg == "Nazionale" else f"Bandi e incentivi in {reg}"
        desc = clip(f"{title}: misure aperte, con scadenze, destinatari e link alle fonti ufficiali.")
        others = pills(area_links(bandi, "", reg))
        sectors_here = sort_dest({d for b in rows for d in b["destinatari"]})
        sector_pills = pills([
            (site_href(sector_path(name)), name, sum(1 for b in rows if name in b["destinatari"]))
            for name in sectors_here
        ]) if sectors_here else ""
        listing = grid(rows, "", today) if rows else '<p class="note">Nessun bando aperto in questa area. Guarda le altre aree qui sotto.</p>'
        h1_fix = "Bandi nazionali aperti" if reg == "Nazionale" else f"Bandi aperti in {reg}"
        body = (
            crumbs([("index.html", "Bandi"), ("", label)], "")
            + f"<h1>{e(h1_fix)}</h1><p>{e(INTRO_REG[reg])} In elenco: <span data-aperti>{qty(sum(1 for b in rows if is_aperto(b)), 'bando aperto', 'bandi aperti')}</span>.</p>"
            + f'<p><a href="{site_href("index.html", urllib.parse.urlencode({"area": reg}), "filtri")}">Trova il tuo bando</a></p>'
            + listing
            + (f'<section aria-labelledby="dest-qui"><h2 id="dest-qui">Destinatari</h2>{sector_pills}</section>' if sector_pills else "")
            + f'<section aria-labelledby="altre-aree"><h2 id="altre-aree">Altre aree</h2>{others}</section>'
            + fpef_box()
        )
        ld = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "CollectionPage", "name": title, "url": public_url(path), "inLanguage": "it-IT", "isPartOf": BASE},
                breadcrumb_ld([("", "Bandi"), (path, label)]),
                item_list(rows),
            ],
        }
        emit(path, page(path, title, desc, body, ld=ld), agg, "weekly", "0.8")

    names = sort_dest({d for b in bandi for d in b["destinatari"]})
    for name in names:
        rows = [b for b in att if name in b["destinatari"]]
        path = sector_path(name)
        regs = [reg for reg in REG if any(b["regione"] == reg for b in rows)]
        where = join_it(["nazionali" if r == "Nazionale" else r for r in regs]) or "nessuna area"
        intro = INTRO_DEST.get(name, f"Misure che indicano {name} tra i destinatari.")
        title = f"Bandi per {name}"
        desc = clip(f"{title}: bandi aperti ({where}), con scadenze e link ufficiali.")
        listing = grid(rows, "../", today) if rows else '<p class="note">Nessun bando aperto per questo destinatario. Guarda gli altri destinatari qui sotto.</p>'
        body = (
            crumbs([("index.html", "Bandi"), ("", name)], "../")
            + f"<h1>Bandi aperti per {e(name)}</h1>"
            + f"<p>{e(intro)} In elenco: <span data-aperti>{qty(sum(1 for b in rows if is_aperto(b)), 'bando aperto', 'bandi aperti')}</span>, aree {e(where)}.</p>"
            + f'<p><a href="{site_href("index.html", urllib.parse.urlencode({"dest": name}), "filtri")}">Trova il tuo bando</a></p>'
            + listing
            + '<section aria-labelledby="altre-aree"><h2 id="altre-aree">Aree</h2>'
            + pills(area_links(bandi, "../"))
            + '</section><section aria-labelledby="altri-dest"><h2 id="altri-dest">Altri destinatari</h2>'
            + pills(dest_links(bandi, "../", name))
            + "</section>"
            + fpef_box()
        )
        ld = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "CollectionPage", "name": title, "url": public_url(path), "inLanguage": "it-IT", "about": name},
                breadcrumb_ld([("", "Bandi"), (path, name)]),
                item_list(rows),
            ],
        }
        emit(path, page(path, title, desc, body, ld=ld), agg, "weekly", "0.8")

    for b in bandi:
        path = f'bando/{b["id"]}.html'
        area_href = region_path(b["regione"])
        area_label = "Nazionali" if b["regione"] == "Nazionale" else b["regione"]
        dest_html = ", ".join(
            f'<a href="{site_href(sector_path(d))}">{e(d)}</a>' for d in b["destinatari"]
        )
        sibs = related(b, bandi)
        related_html = ""
        if sibs:
            lis = "".join(
                f'<li><a href="{site_href(f"bando/{o["id"]}.html")}">{e(o["titolo"])}<span>{e(o["regione"])} · {e(deadline_text(o))}</span></a></li>'
                for o in sibs
            )
            related_html = f'<section class="related" aria-labelledby="collegati"><h2 id="collegati">Bandi collegati</h2><ul>{lis}</ul></section>'
        tags = f'<a class="tag area" href="{site_href(area_href)}">{e(b["regione"])}</a>' + "".join(
            f'<a class="tag" href="{site_href(sector_path(d))}">{e(d)}</a>' for d in b["destinatari"]
        )
        when = f' data-deadline="{b["scadenza"]}"' if b["scadenza"] else ""
        if b.get("apertura"):
            when += f' data-apre="{b["apertura"]}"'
        body = (
            crumbs([("index.html", "Bandi"), (area_href, area_label), ("", b["titolo"])], "../")
            + f'<article class="box">{badge(b, today)}<div class="tags">{tags}</div><h1>{e(b["titolo"])}</h1>'
            + avviso_fondi(b, con_link=True)
            + "<dl class=\"kv\">"
            + f"<dt>Ente</dt><dd>{e(b['ente'])}</dd>"
            + f'<dt>Area</dt><dd><a href="{site_href(area_href)}">{e(b["regione"])}</a></dd>'
            + f"<dt>Destinatari</dt><dd>{dest_html}</dd>"
            + f"<dt>Importo</dt><dd>{e(b['importo'])}</dd>"
            + f"<dt>Scadenza</dt><dd><strong{when}>{e(deadline_text(b))}</strong><br><small>{e(b['nota_scadenza'])}</small></dd>"
            + f"<dt>Ultimo controllo</dt><dd>{it_date(b['ultimo_controllo'])}</dd>"
            + "</dl>"
            + f"<p>{e(b['sintesi'])}</p>"
            + official_bando_link(b["url"])
            + fonte_fuori_avviso(b)
            + bando_checkup_box()
            + checkup_ask()
            + '<p class="note">Sintesi indicativa. Fa fede esclusivamente il testo ufficiale pubblicato dall&#39;ente. <a href="/disclaimer">Disclaimer</a></p></article>'
            + related_html
            + '<aside class="sp" aria-label="Spazio sponsor"><span class="lab">Sponsorizzato</span>'
            + '<p class="spt">Spazio disponibile per commercialisti, consulenti, banche e software</p>'
            + f'<p class="spp">{SPONSOR_DA}</p>'
            + '<p><a class="btn outline" href="/sponsor">Scopri gli spazi sponsor</a></p></aside>'
            + fpef_box()
            + BADGE_JS
        )
        desc = clip(f"{b['titolo']} ({b['ente']}): {b['sintesi']}")
        grant = {
            "@type": "MonetaryGrant",
            "name": b["titolo"],
            "description": b["sintesi"],
            "url": b["url"],
            "funder": {"@type": "Organization", "name": b["ente"]},
            "areaServed": "Italia" if b["regione"] == "Nazionale" else b["regione"],
        }
        ld = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebPage",
                    "name": b["titolo"],
                    "url": public_url(path),
                    "inLanguage": "it-IT",
                    "dateModified": b["ultimo_controllo"],
                    "isBasedOn": b["url"],
                    "publisher": org_ld(),
                    "about": grant,
                },
                breadcrumb_ld([("", "Bandi"), (area_href, area_label), (path, b["titolo"])]),
                grant,
            ],
        }
        emit(path, page(path, b["titolo"], desc, body, ld=ld), b["ultimo_controllo"], "weekly", "0.7")

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
            ld = {"@context": "https://schema.org", "@graph": [webpage, checkup_service()]}
        freq = "monthly" if path in ("sponsor.html", "check-up.html") else "yearly"
        priority = "0.8" if path in ("sponsor.html", "check-up.html") else "0.3"
        emit(path, page(path, title, desc, body, ld=ld), agg, freq, priority)

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
