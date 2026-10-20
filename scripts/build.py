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
BASE = "https://incentiviperte.pages.dev/"
SITE = "IncentiviPerTe"
LINKEDIN = "https://www.linkedin.com/company/incentiviperte/"
EMAIL = "incentiviperte.team@gmail.com"
FPEF_EMAIL = "foglioPEF.team@gmail.com"
FPEF = "https://fogliopef.gumroad.com"
FPEF_LI = "https://www.linkedin.com/company/fogliopef"
REG = ["Nazionale", "Toscana", "Umbria", "Emilia-Romagna"]
REQUIRED = (
    "id", "titolo", "ente", "regione", "destinatari", "scadenza", "nota_scadenza",
    "sintesi", "url", "check", "ultimo_controllo", "importo",
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
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
    "Umbria": "Bandi della Regione Umbria gestiti da Gepafin. Per un'impresa umbra restano rilevanti anche gli incentivi nazionali per avviare e far crescere l'impresa, tra cui Autoimpiego Centro-Nord.",
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
     "È un controllo personalizzato di quali bandi regionali e nazionali sono adatti alla tua impresa: tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), Umbria, Emilia-Romagna e incentivi nazionali per avviare e far crescere l'impresa. Ricevi una relazione scritta. Per richiederlo usa la pagina Contatti."),
)
NAV = (
    ("index.html", "Bandi"),
    ("nazionale.html", "Nazionali"),
    ("toscana.html", "Toscana"),
    ("umbria.html", "Umbria"),
    ("emilia-romagna.html", "Emilia-Romagna"),
    ("chi-siamo.html", "Chi siamo"),
    ("sponsor.html", "Sponsor"),
    ("contatti.html", "Contatti"),
)
KEEP = {"style.css", "favicon.svg", "og.svg", "og.png", "robots.txt", "sitemap.xml", ".nojekyll"}
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
        parse_date(b["ultimo_controllo"], "ultimo_controllo", bid)
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
        out.append(b)
    out.sort(key=lambda b: b["scadenza"] or "9999-12-31")
    return out


def deadline_text(b):
    if b["scaduto"]:
        return "Scaduto il " + it_date(b["scadenza"])
    if b["scadenza"]:
        return f"Aperto fino al {it_date(b['scadenza'])}"
    return "Senza scadenza indicata: verifica sul sito ufficiale"


def days_left(b, today):
    if not b["scadenza"]:
        return None
    return (datetime.date.fromisoformat(b["scadenza"]) - today).days


def badge(b, today):
    if b["scaduto"]:
        return '<span class="badge exp">Scaduto</span>'
    if not b["scadenza"]:
        return '<span class="badge open">Sportello aperto</span>'
    g = days_left(b, today)
    if g <= 0:
        label, cls = ("Scade oggi", " soon")
    elif g == 1:
        label, cls = ("Manca 1 giorno", " soon")
    elif g <= 14:
        label, cls = (f"Mancano {g} giorni", " soon")
    else:
        label, cls = (f"Mancano {g} giorni", "")
    return f'<span class="badge{cls}">{label}</span>'


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
            lis.append(f'<li><a href="{pre}{href}">{e(label)}</a></li>')
    return f'<nav class="crumb" aria-label="Percorso"><ol>{"".join(lis)}</ol></nav>'


def breadcrumb_ld(items):
    elements = []
    for i, (href, label) in enumerate(items, start=1):
        item = {"@type": "ListItem", "position": i, "name": label}
        if href is not None:
            item["item"] = BASE if href == "" else BASE + href
        elements.append(item)
    return {"@type": "BreadcrumbList", "itemListElement": elements}


def org_ld():
    return {
        "@type": "Organization",
        "name": SITE,
        "url": BASE,
        "sameAs": [LINKEDIN],
        "logo": BASE + "favicon.svg",
    }


def card(b, pre, today):
    tags = f'<a class="tag area" href="{pre}{region_path(b["regione"])}">{e(b["regione"])}</a>'
    tags += "".join(
        f'<a class="tag" href="{pre}{sector_path(d)}">{e(d)}</a>' for d in b["destinatari"]
    )
    search = " ".join(" ".join([
        b["titolo"], b["sintesi"], b["ente"], b["regione"], " ".join(b["destinatari"]),
    ]).split())
    hidden = " hidden" if b["scaduto"] else ""
    href = f'{pre}bando/{b["id"]}.html'
    return (
        f'<article class="card" data-reg="{e(b["regione"])}" '
        f'data-dest="{e("|".join(b["destinatari"]))}" data-scad="{b["scadenza"] or "9999-12-31"}" '
        f'data-scaduto="{1 if b["scaduto"] else 0}" data-search="{e(search)}"{hidden}>'
        f'{badge(b, today)}<h3><a href="{href}">{e(b["titolo"])}</a></h3>'
        f'<p class="amt">{e(b["importo"])}</p><div class="tags">{tags}</div>'
        f'<p class="sum">{e(b["sintesi"])}</p><div class="meta"><span class="dl">{e(deadline_text(b))}</span>'
        f'<span class="ente">{e(b["ente"])}</span>'
        f'<a class="more" href="{href}">Vedi la scheda</a></div></article>'
    )


def sponsor_card(pre):
    return (
        '<aside class="card spc" aria-label="Spazio sponsor"><span class="lab">Sponsorizzato</span>'
        '<p class="spt">Il tuo studio qui, tra chi cerca un finanziamento</p>'
        '<p class="spp">Da 49 € al mese · prezzo di lancio</p>'
        f'<a class="btn" href="{pre}sponsor.html">Diventa sponsor</a></aside>'
    )


def grid(items, pre, today):
    blocks = [card(b, pre, today) for b in items]
    active = [i for i, b in enumerate(items) if not b["scaduto"]]
    pos = active[2] + 1 if len(active) >= 3 else len(blocks)
    blocks.insert(pos, sponsor_card(pre))
    return '<div class="grid" id="elenco">' + "".join(blocks) + "</div>"


def official_bando_link(url):
    host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
    if "invitalia" in host.lower():
        label = "Vai al bando ufficiale"
    else:
        label = f"Vai al bando ufficiale su {e(host)}"
    return ext(url, label, "btn")


def checkup_section(pre):
    return (
        '<section class="checkup" aria-labelledby="checkup-title"><div class="box">'
        "<h2 id=\"checkup-title\">Check-up Bandi</h2>"
        "<p>Controllo personalizzato di quali bandi regionali e nazionali sono adatti alla tua impresa: "
        "tutta la Toscana (bandi regionali e delle Camere di Commercio toscane), Umbria, Emilia-Romagna e incentivi nazionali "
        "per avviare e far crescere l'impresa, tra cui finanziamenti a tasso zero e contributi a fondo perduto "
        "per nuove imprese, startup innovative e investimenti. Il risultato è una relazione scritta.</p>"
        f'<p><a class="btn" href="{pre}contatti.html">Richiedi il Check-up Bandi</a></p>'
        "</div></section>"
    )


def fpef_box():
    return (
        '<aside class="fpef" aria-label="FoglioPEF, progetto dello stesso titolare">'
        '<p class="lab">Progetto dello stesso titolare</p>'
        '<h2>Numeri in ordine per un investimento immobiliare</h2>'
        '<p>FoglioPEF è un foglio Excel per ricavi, costi e cassa. Serve a preparare un piano economico-finanziario immobiliare: non presenta la domanda e non sostituisce il bando.</p>'
        '<p class="row">'
        f'{ext(FPEF, "Apri FoglioPEF", "btn")}'
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
        visible[Math.min(2, visible.length - 1)].after(sponsor);
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
        out.append((pre + region_path(reg), "Nazionali" if reg == "Nazionale" else reg, n))
    return out


def dest_links(bandi, pre, current=None):
    names = sort_dest({d for b in bandi for d in b["destinatari"]})
    out = []
    for name in names:
        if name == current:
            continue
        n = sum(1 for b in bandi if name in b["destinatari"] and not b["scaduto"])
        out.append((pre + sector_path(name), name, n))
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


def page(path, title, desc, body, hero="", ld=None, robots=None):
    pre = prefix(path)
    url = BASE if path == "index.html" else BASE + path
    full = title if path == "index.html" else f"{title} – {SITE}"
    nav = "".join(
        f'<li><a href="{pre}{href}"{" aria-current=\"page\"" if href == path else ""}>{label}</a></li>'
        for href, label in NAV
    )
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
{robots_html}{canon}{alt}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE}">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="{full_e}">
<meta property="og:description" content="{desc_e}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{BASE}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="IncentiviPerTe – Bandi e incentivi per startup e PMI">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{full_e}">
<meta name="twitter:description" content="{desc_e}">
<meta name="twitter:image" content="{BASE}og.png">
<meta name="theme-color" content="#0b5cad">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{pre}style.css">
{ld_html}
</head>
<body>
<a class="skip" href="#main">Vai al contenuto</a>
<header class="top"><div class="wrap bar">
<a class="brand" href="{pre}index.html">{LOGO}<span>Incentivi<span class="per">PerTe</span></span></a>
<nav class="dnav" aria-label="Principale"><ul>{nav}</ul></nav>
<details class="menu"><summary><span class="when-closed">Menu</span><span class="when-open">Chiudi</span></summary>
<nav aria-label="Menu"><ul>{nav}</ul></nav></details>
</div></header>
<main id="main" tabindex="-1">{hero}<div class="wrap">{body}</div></main>
{footer(pre)}
</body>
</html>
"""


LOGO = '<svg viewBox="0 0 32 32" width="32" height="32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#0b5cad"/><path d="M9 22V10m5 12V14m5 8v-5m5 5V8" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>'


def footer(pre):
    # I link di area e destinatario sono aggiunti dopo, quando i bandi sono noti.
    info = (
        ("chi-siamo.html", "Chi siamo"),
        ("contatti.html", "Contatti"),
        ("sponsor.html", "Sponsor e pubblicità"),
        ("disclaimer.html", "Disclaimer"),
        ("privacy.html", "Privacy"),
        ("cookie.html", "Cookie policy"),
        ("note-legali.html", "Note legali"),
    )
    links = "".join(f'<li><a href="{pre}{href}">{label}</a></li>' for href, label in info)
    return f"""<footer><div class="wrap">
<p><strong>{SITE}</strong> · raccolta gratuita e indipendente di bandi per startup e PMI, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali. Le schede sono sintesi: fa fede solo il bando ufficiale.</p>
<nav aria-label="Aree"><p><strong>Aree</strong></p><ul id="foot-aree"></ul></nav>
<nav aria-label="Destinatari"><p><strong>Destinatari</strong></p><ul id="foot-dest"></ul></nav>
<nav aria-label="Informazioni"><ul>{links}</ul></nav>
<p>Strumento dello stesso titolare: {ext(FPEF, "FoglioPEF")}, modelli Excel per il piano economico-finanziario immobiliare ({ext(FPEF_LI, "LinkedIn")}). Contatti: {ext(LINKEDIN, "messaggi della Pagina LinkedIn IncentiviPerTe")} o {mail_link()}. Nessun cookie, nessun tracker.</p>
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


CSS = """:root{--b:#0b5cad;--bd:#083f78;--t:#18202e;--m:#3d4a5c;--bg:#f4f6fa;--l:#dde3ec;--ok:#0b5a2d}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--t);background:var(--bg)}
h1,h2,h3,p,li,dd{overflow-wrap:break-word}
h1{font-size:clamp(1.6rem,3vw,2rem);line-height:1.2;margin:0 0 12px}
h2{font-size:1.3rem;line-height:1.3;margin:28px 0 10px}
a{color:var(--b);text-underline-offset:2px}
a:hover{color:var(--bd)}
:focus-visible{outline:3px solid #fff;outline-offset:2px;box-shadow:0 0 0 6px #083f78}
.skip{position:absolute;left:8px;top:8px;transform:translateY(-160%);background:#fff;color:var(--t);padding:10px 12px;z-index:20;border-radius:8px;font-weight:700}
.skip:focus{transform:none}
.vh{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.wrap{max-width:1040px;margin:auto;padding:0 max(16px,env(safe-area-inset-right)) 0 max(16px,env(safe-area-inset-left))}
header .wrap{max-width:1180px}
header.top{background:#fff;border-bottom:1px solid var(--l);position:sticky;top:0;z-index:5}
.bar{display:flex;align-items:center;justify-content:space-between;min-height:64px;gap:12px;position:relative}
.brand{display:flex;align-items:center;gap:8px;min-height:44px;font-weight:800;font-size:1.15rem;color:var(--t);text-decoration:none}
.brand .per{color:var(--b)}
nav ul{list-style:none;margin:0;padding:0;display:flex;gap:2px;flex-wrap:wrap}
nav a{display:flex;align-items:center;min-height:44px;padding:8px;border-radius:8px;text-decoration:none;color:var(--t);font-weight:700;font-size:15px}
.dnav ul{flex-wrap:nowrap}
nav a:hover,nav a[aria-current="page"]{background:#e8f0fb;color:var(--b)}
.dnav{display:none}
details.menu summary{list-style:none;cursor:pointer;min-height:44px;min-width:44px;display:flex;align-items:center;padding:8px 12px;border:1px solid #5c6b82;border-radius:8px;font-weight:800;background:#fff}
details.menu summary::-webkit-details-marker{display:none}
details.menu .when-open{display:none}
details.menu[open] .when-closed{display:none}
details.menu[open] .when-open{display:inline}
details.menu[open] summary{border-color:var(--b);color:var(--b)}
details.menu nav{position:absolute;z-index:6;left:0;right:0;top:100%;background:#fff;border:1px solid var(--l);border-radius:12px;padding:8px;box-shadow:0 8px 24px #0002;max-height:min(70vh,520px);overflow:auto}
details.menu nav ul{flex-direction:column}
@media(min-width:1000px){.dnav{display:block}details.menu{display:none}}
.hero{background:linear-gradient(135deg,#083f78,#0b5cad);color:#fff;padding:36px 0 32px}
.hero h1{font-size:clamp(1.7rem,4.5vw,2.5rem);line-height:1.15;margin:0 0 10px;color:#fff}
.hero p{margin:0;color:#fff;max-width:42rem}
.hero .upd{margin-top:8px;font-weight:700}
.hero-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}
main{padding:0 0 40px}
main:focus{outline:none}
main>.wrap{padding-top:20px}
.note{background:#fff8e6;border:1px solid #c4922a;border-radius:10px;padding:12px 14px;margin:16px 0}
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
.grid{display:grid;gap:14px;grid-template-columns:1fr}
@media(min-width:700px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1000px){.grid{grid-template-columns:repeat(3,1fr)}}
.card{background:#fff;border:1px solid var(--l);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column}
.card[hidden]{display:none !important}
.card h3{font-size:1.15rem;margin:8px 0;line-height:1.3}
.card h3 a{text-decoration:underline;text-underline-offset:3px}
.amt{font-weight:800;margin:0 0 8px}
.sum{margin:0 0 10px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card .meta{margin-top:auto;display:flex;flex-direction:column;gap:4px;border-top:1px solid var(--l);padding-top:10px;font-size:14px;color:var(--m)}
.ente{color:var(--m)}
.dl{font-weight:800;color:var(--t)}
.more{font-weight:800;margin-top:4px}
.badge{align-self:flex-start;font-size:13px;font-weight:800;border-radius:999px;padding:4px 10px;background:#e7f6ec;color:var(--ok)}
.badge.soon{background:#fde8e7;color:#9b1c1c}
.badge.exp{background:#eceff3;color:#243044}
.badge.open{background:#e8f0fb;color:var(--bd)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px}
.tag{display:inline-flex;align-items:center;min-height:32px;background:#fff;color:var(--bd);border:1px solid var(--b);border-radius:999px;padding:2px 10px;font-size:13px;font-weight:800;text-decoration:none}
a.tag:hover{background:#e8f0fb}
.tag.area{background:var(--b);color:#fff;border-color:var(--b)}
a.tag.area:hover{background:var(--bd);color:#fff}
.spc{border:2px dashed #5c6b82;background:#f8fafc}
.spt{font-size:1.05rem;font-weight:800;margin:8px 0}
.spp{font-weight:800;color:var(--b);margin:0 0 8px}
.lab{display:inline-block;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;background:#e8edf3;color:#243044;border-radius:6px;padding:3px 8px}
.checkup{margin:22px 0}
.checkup h2{margin-top:0}
.fpef{background:#f5f9ff;border:2px solid var(--b);border-radius:14px;padding:16px 18px;margin:22px 0}
.fpef h2,.offer h3{margin-top:0}
.fpef .row,.hero-actions{align-items:center}
.fpef .row{display:flex;flex-wrap:wrap;gap:12px 16px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;background:var(--b);color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:800}
.btn:hover{background:var(--bd);color:#fff}
.hero .btn{background:#fff;color:var(--bd)}
.hero .btn:hover{background:#e8f0fb;color:var(--bd)}
.btn.ghost,.hero .btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
.btn.ghost:hover,.hero .btn.ghost:hover{background:#fff;color:var(--bd)}
.pills{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:8px 0 0}
.pills a{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:8px 12px;background:#fff;border:1px solid #5c6b82;border-radius:999px;text-decoration:none;font-weight:800;color:var(--t)}
.pills a:hover{border-color:var(--b);color:var(--b)}
.num{background:#e8f0fb;color:var(--bd);border-radius:999px;min-width:1.6rem;text-align:center;padding:0 8px;font-size:13px}
.faq details{background:#fff;border:1px solid var(--l);border-radius:12px;padding:4px 14px;margin:8px 0}
.faq summary{cursor:pointer;font-weight:800;min-height:44px;display:flex;align-items:center}
.box{background:#fff;border:1px solid var(--l);border-radius:14px;padding:18px}
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
.offer{border:2px solid #5c6b82;border-radius:14px;padding:16px;background:#fff;display:flex;flex-direction:column;gap:8px}
.offer.featured{border-color:var(--b);background:#f5f9ff}
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
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def static_pages(today):
    li = ext(LINKEDIN, "Pagina LinkedIn IncentiviPerTe")
    li_btn = ext(LINKEDIN, "Contattaci su LinkedIn", "btn")
    mail = mail_link()
    fpef_mail = mail_link(FPEF_EMAIL)
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
            "Chi siamo",
            "IncentiviPerTe, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna e per gli incentivi nazionali: metodo, team e Check-up Bandi.",
            "<h1>Chi siamo</h1><div class='box'>"
            "<p>IncentiviPerTe è una raccolta gratuita e indipendente di bandi e incentivi per startup e PMI, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali. In Toscana la copertura è tutta la regione: bandi regionali e delle Camere di Commercio toscane.</p>"
            "<p>Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale.</p>"
            "<h2>Metodo</h2><p>Ogni scheda è redatta partendo dalla fonte ufficiale (ministeri, Regioni, Sviluppo Toscana, Camere di Commercio toscane, Gepafin e altri enti) e riporta il link al bando e la data dell'ultimo controllo. Le pagine ufficiali vengono ricontrollate periodicamente e ogni anomalia è verificata a mano. I bandi scaduti vengono rimossi.</p>"
            "<h2>Indipendenza</h2><p>Non siamo un ente pubblico né siamo affiliati agli enti citati. Le schede gratuite sono sintesi informative e non sostituiscono il testo del bando. Il sito si sostiene con spazi sponsor sempre etichettati come <em>Sponsorizzato</em>, che non influenzano la selezione dei bandi.</p>"
            "<p>Per gli spazi pubblicitari vedi <a href='sponsor.html'>Sponsor e pubblicità</a>. Per segnalare un bando, una correzione o per il Check-up Bandi, <a href='contatti.html'>Contatti</a>.</p></div>"
            + checkup_section(""),
            True,
        ),
        "contatti.html": (
            "Contatti",
            "Come contattare IncentiviPerTe: segnalazioni di bandi, Check-up Bandi e richieste sponsor.",
            f"<h1>Contatti</h1><div class='box'><p>Per segnalare un bando, una correzione, per richiedere il Check-up Bandi o per informazioni sugli spazi sponsor scrivici tramite i messaggi della Pagina LinkedIn IncentiviPerTe oppure all'indirizzo email:</p>{contacts}<p>Le schede pubblicate restano sintesi: requisiti e domanda si verificano sull'ente che gestisce la misura. Il Check-up Bandi è il controllo personalizzato, consegnato come relazione scritta, e si richiede da questi stessi contatti. Gli spazi pubblicitari sono descritti nella pagina <a href='sponsor.html'>Sponsor</a>.</p></div>",
            False,
        ),
        "sponsor.html": (
            "Sponsor e pubblicità",
            "Spazi sponsor su IncentiviPerTe da 49 € al mese, su FoglioPEF da 39 € e su entrambi i siti a 69 €.",
            f"""<h1>Sponsor e pubblicità</h1><div class="box">
<p>IncentiviPerTe è letto da imprenditori, startup e PMI che cercano finanziamenti. Gli spazi sono per <strong>commercialisti, consulenti di finanza agevolata, banche e software</strong> per le imprese.</p>
{sponsor_contacts}
<h2>Cosa include lo spazio su IncentiviPerTe</h2>
<ul><li>Un posto in <strong>home page</strong></li><li>Un posto nelle <strong>pagine regionali</strong> (Toscana, Umbria, Emilia-Romagna) e nei bandi nazionali</li><li>Un posto nelle <strong>schede dei bandi</strong></li><li>Etichetta <strong>Sponsorizzato</strong> sempre visibile</li></ul>
<h2 id="prezzi">Prezzi</h2>
<p>I prezzi qui sotto sono per uno spazio pubblicitario etichettato Sponsorizzato. Non sono il prezzo dei modelli Excel.</p>
<div class="offers">
<div class="offer featured"><h3>IncentiviPerTe</h3><p class="price"><strong>49 €</strong> al mese</p><p class="launch">Prezzo di lancio: 3 posti, poi 79 €</p><p class="fine">Il prezzo sale man mano che si vendono gli spazi: 49 € per i primi 3 sponsor, poi 79 €, poi 99 € al mese. Nessun pagamento online: ti rispondiamo con i dettagli.</p><div class="contact-links">{li_btn}{mail}</div></div>
<div class="offer"><h3>FoglioPEF</h3><p class="price"><strong>39 €</strong> al mese</p><p class="launch">Spazio su FoglioPEF</p><p class="fine">Modelli Excel per immobili e cassa: {ext(FPEF, "fogliopef.gumroad.com")}. Stessa etichetta <strong>Sponsorizzato</strong>.</p><div class="contact-links">{li_btn}{mail}{fpef_space}</div></div>
<div class="offer"><h3>Entrambi i siti</h3><p class="price"><strong>69 €</strong> al mese</p><p class="launch">Pacchetto entrambi i siti: IncentiviPerTe + FoglioPEF</p><p class="fine">Uno spazio su IncentiviPerTe e uno su FoglioPEF, entrambi etichettati <strong>Sponsorizzato</strong>. Nessun pagamento online: ti rispondiamo con i dettagli.</p><div class="contact-links">{li_btn}{mail}{fpef_pack}</div></div>
</div>
<h2>Regole</h2>
<ul><li>Ogni contenuto a pagamento è etichettato <strong>Sponsorizzato</strong>.</li><li>Gli sponsor non influenzano quali bandi pubblichiamo né come li descriviamo.</li><li>Nessun tracciamento degli utenti: niente pixel, cookie o script di terze parti.</li></ul>
<p>Domande? Scrivi a messaggi della {li} o all'indirizzo {mail}. Per le sponsorizzazioni FoglioPEF (39 € al mese) e per il pacchetto entrambi i siti (69 € al mese): {fpef_mail}.</p>
</div>""",
            False,
        ),
        "cookie.html": (
            "Cookie policy",
            "IncentiviPerTe non usa cookie né strumenti di tracciamento.",
            "<h1>Cookie policy</h1><div class='box'><p>Questo sito <strong>non installa cookie</strong>, né tecnici né di profilazione, e non utilizza strumenti di analisi, pixel pubblicitari, font o script di terze parti. Per questo non è mostrato alcun banner cookie.</p><p>Il sito è ospitato da GitHub Pages (GitHub, Inc.), che può trattare dati tecnici di navigazione come l'indirizzo IP nei propri log per finalità di sicurezza e funzionamento: vedi la <a href='https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement' rel='noopener noreferrer'>informativa di GitHub</a>.</p><p>Se in futuro introducessimo cookie non tecnici, chiederemo prima il consenso e aggiorneremo questa pagina.</p></div>",
            False,
        ),
        "note-legali.html": (
            "Note legali",
            "Note legali di IncentiviPerTe: titolarità, contenuti, marchi e link esterni.",
            f"<h1>Note legali</h1><div class='box'><h2>Titolare del sito</h2><p>{owner}</p><h2>Contenuti</h2><p>Le schede sono sintesi originali redatte a scopo informativo da fonti pubbliche ufficiali, citate e linkate. I testi dei bandi restano dei rispettivi enti. Nomi e marchi citati appartengono ai legittimi titolari.</p><h2>Link esterni</h2><p>I link a siti di terzi sono forniti per comodità; non siamo responsabili dei loro contenuti.</p><h2>Responsabilità</h2><p>Vedi il <a href='disclaimer.html'>Disclaimer</a>. Per segnalazioni o richieste di rimozione scrivi all'indirizzo sopra.</p></div>",
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
            f"<h1>Informativa privacy</h1><div class='box'><p>Ai sensi degli artt. 13-14 del Regolamento UE 2016/679 (GDPR).</p><h2>Titolare del trattamento</h2><p>{owner}</p><h2>Dati trattati</h2><ul><li><strong>Navigazione</strong>: il sito non usa cookie, analytics o tracker. L'hosting (GitHub Pages, GitHub Inc.) può registrare dati tecnici come l'indirizzo IP nei log di server per sicurezza e funzionamento, secondo la propria informativa; base giuridica: legittimo interesse (art. 6.1.f).</li><li><strong>Email</strong>: se ci scrivi trattiamo indirizzo e contenuto del messaggio solo per rispondere; base giuridica: misure su richiesta dell'interessato / legittimo interesse. Conservazione: il tempo necessario a gestire la richiesta e comunque non oltre 24 mesi.</li></ul><h2>Trasferimenti</h2><p>GitHub Inc. ha sede negli USA; i trasferimenti avvengono secondo le garanzie previste dal GDPR (es. EU-US Data Privacy Framework o clausole contrattuali standard) indicate dal fornitore.</p><h2>Diritti</h2><p>Puoi chiedere accesso, rettifica, cancellazione, limitazione, opposizione e portabilità (artt. 15-22) scrivendo al titolare tramite i messaggi della {li} o all'indirizzo {mail}, e proporre reclamo al Garante per la protezione dei dati personali (garanteprivacy.it).</p><p>Nessuna newsletter è attiva: se verrà introdotta, sarà con consenso esplicito e informativa dedicata.</p><p><small>Ultimo aggiornamento: {it_date(today.isoformat())}.</small></p></div>",
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
                "url": f"{BASE}bando/{b['id']}.html",
                "name": b["titolo"],
            }
            for i, b in enumerate((b for b in items if not b["scaduto"]), start=1)
        ],
    }


def write_assets():
    (D / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#0b5cad"/><path d="M9 22V10m5 12V14m5 8v-5m5 5V8" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>',
        encoding="utf-8",
    )
    (D / "og.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><rect width="1200" height="630" fill="#0b5cad"/><text x="80" y="300" font-family="sans-serif" font-size="96" font-weight="700" fill="#fff">IncentiviPerTe</text><text x="80" y="390" font-family="sans-serif" font-size="44" fill="#dbe8fb">Bandi e incentivi per startup e PMI</text></svg>',
        encoding="utf-8",
    )
    (D / "style.css").write_text(CSS, encoding="utf-8")
    (D / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy(R / "assets" / "og.png", D / "og.png")


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
        for banned in ("Invitalia", "Sorbolini", "Frascadore", "Flavio", "Giuseppe"):
            if banned in text:
                raise ValueError(f"{name}: testo non pubblicabile ({banned})")
        if re.search(r"invitalia", without_urls(text), re.I):
            raise ValueError(f"{name}: la parola Invitalia compare fuori dai link ufficiali")
        if "essedade.github.io" in text:
            raise ValueError(f"{name}: vecchio indirizzo GitHub Pages")
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
    about = (D / "chi-siamo.html").read_text(encoding="utf-8")
    if "Dietro IncentiviPerTe c'è un team di esperti professionisti con esperienza pluriennale." not in about:
        raise ValueError("chi siamo: manca la descrizione del team")
    if "Check-up Bandi" not in about or "tutta la Toscana" not in about or "Camere di Commercio toscane" not in about:
        raise ValueError("chi siamo: copertura o Check-up Bandi mancanti")
    if "Arezzo-Siena" in about:
        raise ValueError("chi siamo: Arezzo-Siena resta come limite di copertura")
    home = (D / "index.html").read_text(encoding="utf-8")
    if "Check-up Bandi" not in home or 'href="contatti.html">Richiedi il Check-up Bandi</a>' not in home:
        raise ValueError("home: manca la sezione Check-up Bandi")
    if 'value="Umbria"' not in home or 'value="Emilia-Romagna"' not in home or 'value="Toscana"' not in home:
        raise ValueError("home: filtri di area incompleti")
    if "focus iniziale" in home or "focus iniziale" in about:
        raise ValueError("testo che restringe la copertura ancora presente")
    if FPEF not in home or "stesso titolare" not in home.lower():
        raise ValueError("home: manca il rimando a FoglioPEF con la disclosure")
    if "link affiliato" in home.lower():
        raise ValueError("home: FoglioPEF non va etichettato come link affiliato")
    robots = (D / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {BASE}sitemap.xml" not in robots or "Disallow: /" in robots:
        raise ValueError("robots.txt non valido")
    sitemap = (D / "sitemap.xml").read_text(encoding="utf-8")
    if "<loc>" not in sitemap or "404.html" in sitemap:
        raise ValueError("sitemap non valida")
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
        f"<p>Raccolta gratuita, da Arezzo, per le imprese di tutta la Toscana, dell'Umbria e dell'Emilia-Romagna, più gli incentivi nazionali: {len(att)} bandi aperti, con scadenza e link alla fonte ufficiale.</p>"
        f'<p class="upd">Aggiornato il {it_date(agg)} · fonti ufficiali · senza cookie</p>'
        '<p class="hero-actions"><a class="btn" href="#filtri">Trova il tuo bando</a>'
        '<a class="btn ghost" href="sponsor.html">Spazi per professionisti</a></p>'
        "</div></section>"
    )
    home_desc = clip(
        f"{len(att)} bandi aperti per startup e PMI, da Arezzo: tutta la Toscana, Umbria, Emilia-Romagna e incentivi nazionali, con scadenze e link ufficiali."
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
        desc = clip(f"{title}: {len(rows)} misure aperte, con scadenze, destinatari e link alle fonti ufficiali.")
        others = pills(area_links(bandi, "", reg))
        sectors_here = sort_dest({d for b in rows for d in b["destinatari"]})
        sector_pills = pills([
            (sector_path(name), name, sum(1 for b in rows if name in b["destinatari"]))
            for name in sectors_here
        ]) if sectors_here else ""
        listing = grid(rows, "", today) if rows else '<p class="note">Nessun bando aperto in questa area. Guarda le altre aree qui sotto.</p>'
        h1_fix = "Bandi nazionali aperti" if reg == "Nazionale" else f"Bandi aperti in {reg}"
        body = (
            crumbs([("index.html", "Bandi"), ("", label)], "")
            + f"<h1>{e(h1_fix)}</h1><p>{e(INTRO_REG[reg])} In elenco: {len(rows)} bandi aperti.</p>"
            + f'<p><a href="index.html?{urllib.parse.urlencode({"area": reg})}#filtri">Apri gli stessi bandi nel filtro della home</a></p>'
            + listing
            + (f'<section aria-labelledby="dest-qui"><h2 id="dest-qui">Destinatari</h2>{sector_pills}</section>' if sector_pills else "")
            + f'<section aria-labelledby="altre-aree"><h2 id="altre-aree">Altre aree</h2>{others}</section>'
            + fpef_box()
        )
        ld = {
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "CollectionPage", "name": title, "url": BASE + path, "inLanguage": "it-IT", "isPartOf": BASE},
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
        desc = clip(f"{title}: {len(rows)} bandi aperti ({where}), con scadenze e link ufficiali.")
        listing = grid(rows, "../", today) if rows else '<p class="note">Nessun bando aperto per questo destinatario. Guarda gli altri destinatari qui sotto.</p>'
        body = (
            crumbs([("index.html", "Bandi"), ("", name)], "../")
            + f"<h1>Bandi aperti per {e(name)}</h1>"
            + f"<p>{e(intro)} In elenco: {len(rows)} bandi aperti, aree {e(where)}.</p>"
            + f'<p><a href="../index.html?{urllib.parse.urlencode({"dest": name})}#filtri">Apri gli stessi bandi nel filtro della home</a></p>'
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
                {"@type": "CollectionPage", "name": title, "url": BASE + path, "inLanguage": "it-IT", "about": name},
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
            f'<a href="../{sector_path(d)}">{e(d)}</a>' for d in b["destinatari"]
        )
        sibs = related(b, bandi)
        related_html = ""
        if sibs:
            lis = "".join(
                f'<li><a href="{o["id"]}.html">{e(o["titolo"])}<span>{e(o["regione"])} · {e(deadline_text(o))}</span></a></li>'
                for o in sibs
            )
            related_html = f'<section class="related" aria-labelledby="collegati"><h2 id="collegati">Bandi collegati</h2><ul>{lis}</ul></section>'
        tags = f'<a class="tag area" href="../{area_href}">{e(b["regione"])}</a>' + "".join(
            f'<a class="tag" href="../{sector_path(d)}">{e(d)}</a>' for d in b["destinatari"]
        )
        body = (
            crumbs([("index.html", "Bandi"), (area_href, area_label), ("", b["titolo"])], "../")
            + f'<article class="box"><div class="tags">{tags}</div><h1>{e(b["titolo"])}</h1>'
            + "<dl class=\"kv\">"
            + f"<dt>Ente</dt><dd>{e(b['ente'])}</dd>"
            + f'<dt>Area</dt><dd><a href="../{area_href}">{e(b["regione"])}</a></dd>'
            + f"<dt>Destinatari</dt><dd>{dest_html}</dd>"
            + f"<dt>Importo</dt><dd>{e(b['importo'])}</dd>"
            + f"<dt>Scadenza</dt><dd><strong>{e(deadline_text(b))}</strong><br><small>{e(b['nota_scadenza'])}</small></dd>"
            + f"<dt>Ultimo controllo</dt><dd>{it_date(b['ultimo_controllo'])}</dd>"
            + "</dl>"
            + f"<p>{e(b['sintesi'])}</p>"
            + f"<p>{official_bando_link(b['url'])}</p>"
            + '<p class="note">Sintesi indicativa. Fa fede esclusivamente il testo ufficiale pubblicato dall&#39;ente. <a href="../disclaimer.html">Disclaimer</a></p></article>'
            + related_html
            + '<aside class="sp" aria-label="Spazio sponsor"><span class="lab">Sponsorizzato</span>'
            + '<p class="spt">Spazio disponibile per commercialisti, consulenti, banche e software</p>'
            + '<p class="spp">Da 49 € al mese · prezzo di lancio</p>'
            + '<p><a class="btn" href="../sponsor.html">Scopri gli spazi</a></p></aside>'
            + fpef_box()
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
                    "url": BASE + path,
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
            "url": BASE + path,
            "inLanguage": "it-IT",
            "publisher": org_ld(),
        }
        freq = "monthly" if path == "sponsor.html" else "yearly"
        priority = "0.8" if path == "sponsor.html" else "0.3"
        emit(path, page(path, title, desc, body, ld=ld), agg, freq, priority)

    # La 404 può essere servita da qualsiasi percorso: i link partono dalla radice.
    # Gli schemi (mailto:, https:) restano intatti.
    not_found = fill_footer(page(
        "404.html",
        "Pagina non trovata",
        "La pagina richiesta non esiste.",
        '<div class="box"><h1>Pagina non trovata</h1><p>La pagina che cerchi non esiste o è stata spostata. Il bando potrebbe essere scaduto e non essere più in elenco.</p><p><a class="btn" href="/index.html">Torna ai bandi</a></p></div>',
        robots="noindex",
    ), bandi, "/")
    not_found = re.sub(
        r'\b(href|src)="(?![a-z][a-z0-9+.-]*:|/|#)([^"]*)"',
        r'\1="/\2"',
        not_found,
        flags=re.I,
    )
    (D / "404.html").write_text(not_found, encoding="utf-8")
    written.add("404.html")

    urlset = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod, freq, priority in urls:
        loc = BASE if path == "index.html" else BASE + path
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
