#!/usr/bin/env python3
"""Genera il sito statico in dist/ da data/bandi.json. Nessuna dipendenza, nessun tracker."""
import json, html, pathlib, datetime
R = pathlib.Path(__file__).resolve().parent.parent
D = R / "dist"; D.mkdir(exist_ok=True); (D / "bando").mkdir(exist_ok=True)
B = json.loads((R / "data/bandi.json").read_text(encoding="utf-8"))
oggi = datetime.date.today().isoformat()
for b in B: b["scaduto"] = bool(b["scadenza"] and b["scadenza"] < oggi)
B.sort(key=lambda b: b["scadenza"] or "9999")
e = html.escape
BASE = "https://essedade.github.io/incentiviperte/"
SITE = "IncentiviPerTe"
MAIL = "davoglio@mail.grokbot.com"
FPEF = "https://fogliopef.gumroad.com"
AGG = max(b["ultimo_controllo"] for b in B)
ATT = [b for b in B if not b["scaduto"]]
def dl(b): return ("Scaduto il " + it(b["scadenza"])) if b["scaduto"] else (f"Aperto fino al {it(b['scadenza'])}" if b["scadenza"] else "Senza scadenza indicata: verifica sul sito ufficiale")
REG = ["Nazionale", "Toscana", "Umbria", "Emilia-Romagna"]
def it(d): y, m, g = d.split("-"); return f"{g}/{m}/{y}"
LOGO = '<svg viewBox="0 0 32 32" width="32" height="32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#0b5cad"/><path d="M9 22V10m5 12V14m5 8v-5m5 5V8" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>'
(D / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#0b5cad"/><path d="M9 22V10m5 12V14m5 8v-5m5 5V8" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>', encoding="utf-8")
(D / "og.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><rect width="1200" height="630" fill="#0b5cad"/><text x="80" y="300" font-family="sans-serif" font-size="96" font-weight="700" fill="#fff">IncentiviPerTe</text><text x="80" y="390" font-family="sans-serif" font-size="44" fill="#dbe8fb">Bandi e incentivi per startup e PMI</text></svg>', encoding="utf-8")
CSS = """:root{--b:#0b5cad;--bd:#083f78;--t:#18202e;--m:#4a5568;--bg:#f4f6fa;--c:#fff;--l:#dde3ec;--ok:#0f7a3d;--w:#9a5b00}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}body{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--t);background:var(--bg)}
a{color:var(--b)}a:hover{color:var(--bd)}:focus-visible{outline:3px solid #f5a623;outline-offset:2px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
.wrap{max-width:1040px;margin:auto;padding:0 16px}
header.top{background:var(--c);border-bottom:1px solid var(--l);position:sticky;top:0;z-index:5}
.bar{display:flex;align-items:center;justify-content:space-between;min-height:60px;gap:12px}
.brand{display:flex;align-items:center;gap:8px;font-weight:800;font-size:19px;color:var(--t);text-decoration:none}
nav ul{list-style:none;margin:0;padding:0;display:flex;gap:4px;flex-wrap:wrap}nav a{display:block;padding:8px 10px;border-radius:8px;text-decoration:none;color:var(--t);font-size:15px}nav a:hover,nav a[aria-current]{background:#e8f0fb;color:var(--b)}
details.menu summary{list-style:none;cursor:pointer;padding:8px 12px;border:1px solid var(--l);border-radius:8px;font-weight:600}details.menu summary::-webkit-details-marker{display:none}
details.menu nav{position:absolute;right:16px;left:16px;top:60px;background:#fff;border:1px solid var(--l);border-radius:12px;padding:8px;box-shadow:0 8px 24px #0002}details.menu nav ul{flex-direction:column}
.dnav{display:none}@media(min-width:900px){.dnav{display:block}details.menu{display:none}}
.hero{background:linear-gradient(135deg,var(--b),#1b7bd6);color:#fff;padding:36px 0 30px}.hero h1{font-size:clamp(26px,5vw,40px);line-height:1.15;margin:0 0 10px}.hero p{margin:0;color:#e3eefc;max-width:640px}
main{padding:20px 0 32px}h1{line-height:1.2}h2{font-size:21px;margin:26px 0 10px}
.note{background:#fff8e6;border:1px solid #f1d9a0;border-radius:10px;padding:10px 14px;font-size:14px;margin:16px 0}
.filters{display:grid;gap:10px;grid-template-columns:1fr;background:var(--c);border:1px solid var(--l);border-radius:12px;padding:14px;margin:16px 0}
@media(min-width:700px){.filters{grid-template-columns:repeat(3,1fr)}}.filters .fbar label{display:flex;margin:0;font-weight:400;color:var(--t)}
.filters label{font-size:13px;font-weight:600;color:var(--m);display:block;margin-bottom:4px}.filters select{width:100%;padding:10px;border:1px solid #b8c2d0;border-radius:8px;font-size:15px;background:#fff}
.count{font-size:14px;color:var(--m);margin:4px 0 8px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}@media(max-width:360px){.grid{grid-template-columns:1fr}}
.card{background:var(--c);border:1px solid var(--l);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column}
.card[hidden]{display:none}.badge{align-self:flex-start;font-size:12.5px;font-weight:700;border-radius:999px;padding:3px 10px;background:#e7f5ec;color:var(--ok)}.badge.soon{background:#fde8e7;color:#b42318}.badge.exp{background:#eee;color:#555}.badge.open{background:#e8f0fb;color:var(--bd)}.amt{font-weight:700;color:var(--t)!important;font-size:14.5px!important;margin:0 0 8px!important}.sum{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.tag.area{background:var(--b);color:#fff}.tag:not(.area){background:#fff;border:1px solid #9fb6d6}.tags{margin-bottom:8px}.meta{display:flex;flex-direction:column;gap:2px;border-top:1px solid var(--l);padding-top:10px}.ente{font-size:13px;color:#5b6575}.more{font-weight:700;font-size:14px;text-decoration:none;margin-top:4px}.spc{border:2px dashed #9aa7ba;background:#fbfcfe;align-items:flex-start;justify-content:center;gap:10px}.spt{font-size:17px!important;font-weight:700;color:var(--t)!important}.upd{font-size:14px;margin-top:8px!important}.hbtn{background:#fff;color:var(--b);margin-top:14px}.hbtn:hover{background:#e8f0fb;color:var(--bd)}.fbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px 18px;grid-column:1/-1}.fbar .count{margin:0;font-weight:600}.chk{font-size:14px;display:flex;gap:6px;align-items:center}#filtri{scroll-margin-top:70px}@media(min-width:900px){.filters{position:sticky;top:61px;z-index:4;box-shadow:0 4px 12px #0001}}.card h3{font-size:18px;margin:6px 0 6px;line-height:1.3}.card h3 a{text-decoration:none}.card h3 a:hover{text-decoration:underline}
.card p{margin:0 0 10px;color:#2d3748;font-size:15px}.meta{margin-top:auto;font-size:14px;color:var(--m)}
.tags{display:flex;flex-wrap:wrap;gap:6px}.tag{background:#e8f0fb;color:var(--bd);border-radius:999px;padding:2px 10px;font-size:12.5px;font-weight:600}
.dl{font-weight:700;color:var(--t)}.soon{color:#b42318}
.sp{border:2px dashed #aab4c3;border-radius:14px;padding:16px;text-align:center;background:#fbfcfe;margin:18px 0;color:var(--m)}
.lab{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:#eef0f3;color:#4a5568;border-radius:6px;padding:2px 8px;margin-bottom:6px}
.tool{background:var(--c);border:1px solid var(--l);border-radius:14px;padding:14px 18px;font-size:15px;margin:18px 0}
.box{background:var(--c);border:1px solid var(--l);border-radius:14px;padding:18px 22px}
.btn{display:inline-block;background:var(--b);color:#fff;padding:11px 18px;border-radius:10px;text-decoration:none;font-weight:700}.btn:hover{background:var(--bd);color:#fff}
dl.kv{display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;margin:12px 0}dl.kv dt{font-weight:700;color:var(--m)}dl.kv dd{margin:0}
.crumb{font-size:14px;margin-bottom:8px}
footer{background:#111827;color:#cbd5e1;font-size:14px;padding:26px 0}footer a{color:#e2e8f0}footer ul{list-style:none;padding:0;margin:8px 0;display:flex;flex-wrap:wrap;gap:6px 16px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}"""
(D / "style.css").write_text(CSS, encoding="utf-8")
NAV = [("index.html","Bandi"),("toscana.html","Toscana"),("umbria.html","Umbria"),("emilia-romagna.html","Emilia-Romagna"),("chi-siamo.html","Chi siamo"),("sponsor.html","Sponsor"),("contatti.html","Contatti")]
def page(path, title, desc, body, hero="", ld=None, pre=""):
    url = BASE + ("" if path == "index.html" else path)
    nav = "".join(f'<li><a href="{pre}{h}"{" aria-current=\"page\"" if h==path else ""}>{t}</a></li>' for h,t in NAV)
    ldj = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    full = title if path == "index.html" else f"{title} – {SITE}"
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE}"><meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}og.svg"><meta property="og:locale" content="it_IT"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b5cad"><link rel="icon" href="{pre}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{pre}style.css">{ldj}</head>
<body><a class="skip" href="#main">Vai al contenuto</a>
<header class="top"><div class="wrap bar"><a class="brand" href="{pre}index.html" aria-label="{SITE}, home">{LOGO}<span>Incentivi<span style="color:var(--b)">PerTe</span></span></a>
<nav class="dnav" aria-label="Principale"><ul>{nav}</ul></nav><details class="menu"><summary aria-label="Apri il menu">Menu</summary><nav aria-label="Principale (mobile)"><ul>{nav}</ul></nav></details></div></header>
{hero}<main id="main"><div class="wrap">{body}</div></main>
<footer><div class="wrap"><p><strong>{SITE}</strong> · raccolta gratuita e indipendente di bandi per startup e PMI. Informazioni indicative: fa fede solo il bando ufficiale.</p>
<ul><li><a href="{pre}chi-siamo.html">Chi siamo</a></li><li><a href="{pre}contatti.html">Contatti</a></li><li><a href="{pre}sponsor.html">Sponsor e pubblicità</a></li><li><a href="{pre}disclaimer.html">Disclaimer</a></li><li><a href="{pre}privacy.html">Privacy</a></li><li><a href="{pre}cookie.html">Cookie policy</a></li><li><a href="{pre}note-legali.html">Note legali</a></li></ul>
<p>Strumenti consigliati: <a href="{FPEF}" rel="noopener" target="_blank">FoglioPEF</a>, modelli finanziari Excel per l'immobiliare (progetto dello stesso titolare; <a href="https://www.linkedin.com/company/fogliopef" rel="noopener" target="_blank">LinkedIn</a>). · Contatti: <a href="mailto:{MAIL}">{MAIL}</a> · Nessun cookie, nessun tracker.</p></div></footer></body></html>"""
SP = '<aside class="sp" aria-label="Spazio sponsor"><span class="lab">Sponsorizzato</span><br><strong>Spazio disponibile</strong><br><span style="font-size:14px">Commercialisti, consulenti, banche e software: <a href="{pre}sponsor.html">scopri come comparire qui</a>.</span></aside>'
def sp(pre=""): return SP.replace("{pre}", pre)
TOOL = f'<aside class="tool" aria-label="Strumenti consigliati"><strong>Strumenti consigliati</strong><br><a href="{FPEF}" rel="noopener" target="_blank">FoglioPEF</a>: modelli finanziari Excel per l&#39;immobiliare. · <a href="https://www.linkedin.com/company/fogliopef" rel="noopener" target="_blank">FoglioPEF su LinkedIn</a> <small>(Progetto dello stesso titolare del sito.)</small></aside>'
def card(b, pre=""):
    t = f'<span class="tag area">{e(b["regione"])}</span>' + "".join(f'<span class="tag">{e(x)}</span>' for x in b["destinatari"])
    if b["scaduto"]: badge = '<span class="badge exp">Scaduto</span>'
    elif b["scadenza"]:
        g = (datetime.date.fromisoformat(b["scadenza"]) - datetime.date.today()).days
        badge = f'<span class="badge{" soon" if g <= 14 else ""}">{"Scade oggi" if g == 0 else ("Manca 1 giorno" if g == 1 else f"Mancano {g} giorni")}</span>'
    else: badge = '<span class="badge open">Sportello aperto</span>'
    return f'''<article class="card" data-reg="{e(b["regione"])}" data-dest="{e("|".join(b["destinatari"]))}" data-scad="{b["scadenza"] or "9999-12-31"}" data-scaduto="{1 if b["scaduto"] else 0}"{" hidden" if b["scaduto"] else ""}>{badge}<h3><a href="{pre}bando/{b["id"]}.html">{e(b["titolo"])}</a></h3><p class="amt">{e(b["importo"])}</p><div class="tags">{t}</div><p class="sum">{e(b["sintesi"])}</p><div class="meta"><span class="dl">{e(dl(b))}</span><span class="ente">{e(b["ente"])}</span><a class="more" href="{pre}bando/{b["id"]}.html">Vedi la scheda →</a></div></article>'''
def grid(L, pre=""):
    out = [card(b, pre) for b in L]
    sp_card = f'<aside class="card spc" aria-label="Spazio sponsor"><span class="lab">Sponsorizzato</span><p class="spt">Il tuo studio qui: raggiungi PMI che cercano finanziamenti</p><a class="btn" href="{pre}sponsor.html">Diventa sponsor</a></aside>'
    att = [i for i, b in enumerate(L) if not b["scaduto"]]
    pos = att[2] + 1 if len(att) >= 3 else len(out)
    out.insert(pos, sp_card)
    return '<div class="grid" id="bandi">' + "".join(out) + "</div>"
dest = sorted({d for b in B for d in b["destinatari"]})
FILT = f"""<form class="filters" role="search" aria-label="Filtra i bandi" onsubmit="return false">
<div><label for="r">Area</label><select id="r"><option value="">Tutte le aree</option>{"".join(f"<option>{x}</option>" for x in REG)}</select></div>
<div><label for="d">Destinatari</label><select id="d"><option value="">Tutti i destinatari</option>{"".join(f"<option>{e(x)}</option>" for x in dest)}</select></div>
<div><label for="s">Scadenza</label><select id="s"><option value="">Qualsiasi scadenza</option><option value="30">Entro 30 giorni</option><option value="90">Entro 90 giorni</option><option value="none">Senza scadenza fissa</option></select></div>
<div class="fbar"><p class="count" id="n" aria-live="polite">{len(ATT)} bandi trovati</p><label class="chk"><input type="checkbox" id="x"> Mostra scaduti</label><a href="#" id="z">Azzera filtri</a></div></form>"""
JS = """<script>(function(){const $=i=>document.getElementById(i),R=$('r'),Dd=$('d'),S=$('s'),X=$('x'),N=$('n'),C=[...document.querySelectorAll('.grid .card:not(.spc)')];
function f(){const r=R.value,d=Dd.value,s=S.value,now=new Date();let k=0;C.forEach(c=>{let ok=(X.checked||c.dataset.scaduto!=='1')&&(!r||c.dataset.reg==r)&&(!d||c.dataset.dest.split('|').includes(d));const sc=c.dataset.scad;if(s=='none')ok=ok&&sc.startsWith('9999');else if(s)ok=ok&&!sc.startsWith('9999')&&(new Date(sc)-now)/864e5<=+s;c.hidden=!ok;if(ok)k++});N.textContent=k===0?'Nessun bando con questi filtri, prova a modificarli':k===1?'1 bando trovato':k+' bandi trovati'}
[R,Dd,S,X].forEach(x=>x.addEventListener('change',f));$('z').addEventListener('click',ev=>{ev.preventDefault();R.value=Dd.value=S.value='';X.checked=false;f()});f()})()</script>"""
ORG = {"@type": "Organization", "name": SITE, "url": BASE, "email": MAIL, "logo": BASE + "favicon.svg"}
pages = []
def W(path, html_): (D / path).write_text(html_, encoding="utf-8"); pages.append(path)
hero = f'<section class="hero"><div class="wrap"><h1>Bandi e incentivi per startup e PMI</h1><p>Raccolta gratuita dei bandi aperti nazionali e regionali, con focus su Toscana, Umbria ed Emilia-Romagna: {len(ATT)} bandi aperti.</p><p class="upd">Aggiornato il {it(AGG)} · fonti ufficiali · gratis</p><p><a class="btn hbtn" href="#filtri">Trova il tuo bando</a></p></div></section>'
W("index.html", page("index.html", "IncentiviPerTe – Bandi e incentivi per startup e PMI", f"{len(ATT)} bandi e incentivi aperti per startup e PMI: nazionali, Toscana, Umbria ed Emilia-Romagna, con scadenze e link ufficiali.",
  f'<p class="note">Queste sono sintesi. Prima di fare domanda, controlla requisiti e scadenze sul sito dell&#39;ente.</p><div id="filtri">{FILT}</div>{grid(B)}{JS}{TOOL}', hero,
  {"@context": "https://schema.org", "@graph": [{"@type": "WebSite", "name": SITE, "url": BASE, "inLanguage": "it"}, ORG,
   {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f'{BASE}bando/{b["id"]}.html', "name": b["titolo"]} for i, b in enumerate(ATT)]}]}))
for reg in REG[1:]:
    L = [b for b in ATT if b["regione"] == reg]; slug = reg.lower() + ".html"
    W(slug, page(slug, f"Bandi {reg}", f"Bandi e incentivi aperti per imprese in {reg}: scadenze, destinatari e link alle fonti ufficiali.",
      f'<p class="crumb"><a href="index.html">Bandi</a> › {reg}</p><h1>Bandi aperti in {reg}</h1><p>{len(L)} bandi regionali. Per le imprese di {reg} sono rilevanti anche gli <a href="index.html">incentivi nazionali</a> (per esempio Autoimpiego Centro-Nord e Smart&amp;Start Italia).</p>{grid(L)}{TOOL}',
      ld={"@context": "https://schema.org", "@type": "CollectionPage", "name": f"Bandi {reg}", "url": BASE + slug, "inLanguage": "it"}))
for b in B:
    p = f'bando/{b["id"]}.html'
    body = f'''<p class="crumb"><a href="../index.html">Bandi</a> › <a href="../{b["regione"].lower() + ".html" if b["regione"] != "Nazionale" else "index.html"}">{e(b["regione"])}</a></p>
<article class="box"><div class="tags">{"".join(f'<span class="tag">{e(x)}</span>' for x in [b["regione"]]+b["destinatari"])}</div><h1>{e(b["titolo"])}</h1>
<dl class="kv"><dt>Ente</dt><dd>{e(b["ente"])}</dd><dt>Area</dt><dd>{e(b["regione"])}</dd><dt>Destinatari</dt><dd>{e(", ".join(b["destinatari"]))}</dd><dt>Importo</dt><dd>{e(b["importo"])}</dd><dt>Scadenza</dt><dd><strong>{e(dl(b))}</strong><br><small>{e(b["nota_scadenza"])}</small></dd><dt>Ultimo controllo</dt><dd>{it(b["ultimo_controllo"])}</dd></dl>
<p>{e(b["sintesi"])}</p><p><a class="btn" href="{e(b["url"])}" rel="noopener" target="_blank">Vai al bando ufficiale<span class="skip"> (si apre in una nuova scheda)</span></a></p>
<p class="note">Sintesi indicativa. Fa fede esclusivamente il testo ufficiale pubblicato dall&#39;ente. <a href="../disclaimer.html">Disclaimer</a></p></article>{sp("../")}'''
    W(p, page(p, b["titolo"], f'{b["titolo"]} ({b["ente"]}): {b["sintesi"][:120]}', body, pre="../",
      ld={"@context": "https://schema.org", "@type": "WebPage", "name": b["titolo"], "url": BASE + p, "inLanguage": "it", "dateModified": b["ultimo_controllo"], "isBasedOn": b["url"], "publisher": ORG}))
STAT = {
"chi-siamo.html": ("Chi siamo", "Chi c'è dietro IncentiviPerTe, il metodo di raccolta dei bandi e come si sostiene il sito.",
 f"<h1>Chi siamo</h1><div class='box'><p>IncentiviPerTe è una raccolta gratuita e indipendente di bandi e incentivi per startup e PMI italiane, nata ad Arezzo, con focus iniziale su Toscana, Umbria ed Emilia-Romagna.</p><h2>Metodo</h2><p>Ogni scheda è redatta partendo dalla fonte ufficiale (Invitalia, Regioni, Sviluppo Toscana, Gepafin e altri enti) e riporta il link al bando e la data dell'ultimo controllo. Le pagine ufficiali vengono ricontrollate periodicamente e ogni anomalia è verificata a mano. I bandi scaduti vengono rimossi.</p><h2>Indipendenza</h2><p>Non siamo un ente pubblico né siamo affiliati agli enti citati. Non offriamo consulenza. Il sito si sostiene con spazi sponsor sempre etichettati come <em>Sponsorizzato</em>, che non influenzano la selezione dei bandi.</p></div>"),
"contatti.html": ("Contatti", "Come contattare IncentiviPerTe: segnalazioni di bandi, correzioni e richieste sponsor.",
 f"<h1>Contatti</h1><div class='box'><p>Per segnalare un bando, una correzione o per informazioni sugli spazi sponsor scrivi a:</p><p><a class='btn' href='mailto:{MAIL}'>{MAIL}</a></p><p>Non forniamo consulenza sui singoli bandi: per domande su requisiti e domanda rivolgiti all'ente che gestisce la misura o a un professionista.</p></div>"),
"sponsor.html": ("Sponsor e pubblicità", "Spazi sponsor su IncentiviPerTe per commercialisti, consulenti di finanza agevolata, banche e software.",
 f"<h1>Sponsor e pubblicità</h1><div class='box'><p>IncentiviPerTe è letto da imprenditori, startup e PMI che cercano finanziamenti. Offriamo spazi per <strong>commercialisti, consulenti di finanza agevolata, banche e software</strong> per le imprese.</p><h2>Formati</h2><ul><li>Spazio in home page</li><li>Spazio nelle pagine regionali (Toscana, Umbria, Emilia-Romagna)</li><li>Spazio nelle schede dei bandi</li></ul><h2>Regole</h2><ul><li>Ogni contenuto a pagamento è etichettato <strong>Sponsorizzato</strong>.</li><li>Gli sponsor non influenzano quali bandi pubblichiamo né come li descriviamo.</li><li>Nessun tracciamento degli utenti: niente pixel, cookie o script di terze parti.</li></ul><p>Condizioni e disponibilità su richiesta: <a href='mailto:{MAIL}?subject=Spazio%20sponsor'>{MAIL}</a>.</p></div>"),
"cookie.html": ("Cookie policy", "IncentiviPerTe non usa cookie né strumenti di tracciamento.",
 "<h1>Cookie policy</h1><div class='box'><p>Questo sito <strong>non installa cookie</strong>, né tecnici né di profilazione, e non utilizza strumenti di analisi, pixel pubblicitari, font o script di terze parti. Per questo non è mostrato alcun banner cookie.</p><p>Il sito è ospitato da GitHub Pages (GitHub, Inc.), che può trattare dati tecnici di navigazione come l'indirizzo IP nei propri log per finalità di sicurezza e funzionamento: vedi la <a href='https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement' rel='noopener'>informativa di GitHub</a>.</p><p>Se in futuro introducessimo cookie non tecnici, chiederemo prima il consenso e aggiorneremo questa pagina.</p></div>"),
"note-legali.html": ("Note legali", "Note legali di IncentiviPerTe: titolarità, contenuti, marchi e link esterni.",
 f"<h1>Note legali</h1><div class='box'><h2>Titolare del sito</h2><p>Davide Davoglio, Arezzo (Italia) – <a href='mailto:{MAIL}'>{MAIL}</a>.</p><h2>Contenuti</h2><p>Le schede sono sintesi originali redatte a scopo informativo da fonti pubbliche ufficiali, citate e linkate. I testi dei bandi restano dei rispettivi enti. Nomi e marchi citati appartengono ai legittimi titolari.</p><h2>Link esterni</h2><p>I link a siti di terzi sono forniti per comodità; non siamo responsabili dei loro contenuti.</p><h2>Responsabilità</h2><p>Vedi il <a href='disclaimer.html'>Disclaimer</a>. Per segnalazioni o richieste di rimozione scrivi all'indirizzo sopra.</p></div>"),
"disclaimer.html": ("Disclaimer", "Avvertenze sull'uso delle informazioni pubblicate da IncentiviPerTe.",
 "<h1>Disclaimer</h1><div class='box'><ul><li>IncentiviPerTe è un servizio informativo <strong>gratuito e indipendente</strong>, non affiliato ad alcun ente pubblico o gestore delle misure.</li><li>Le schede sono <strong>sintesi indicative</strong>: possono contenere errori, omissioni o non essere aggiornate. Requisiti, scadenze e dotazioni possono cambiare o esaurirsi in qualsiasi momento.</li><li><strong>Fa fede esclusivamente</strong> il testo del bando e degli atti pubblicati dall'ente competente. Prima di presentare una domanda verifica sempre la fonte ufficiale.</li><li>Le informazioni <strong>non costituiscono consulenza</strong> fiscale, legale o finanziaria. Per valutare il tuo caso rivolgiti a un professionista.</li><li>Nei limiti consentiti dalla legge, il titolare non risponde di danni derivanti dall'uso delle informazioni del sito.</li><li>I contenuti a pagamento sono sempre etichettati <strong>Sponsorizzato</strong>; il link a FoglioPEF riguarda un progetto dello stesso titolare.</li></ul></div>"),
"privacy.html": ("Informativa privacy", "Informativa privacy di IncentiviPerTe ai sensi del Regolamento UE 2016/679 (GDPR).",
 f"<h1>Informativa privacy</h1><div class='box'><p>Ai sensi degli artt. 13-14 del Regolamento UE 2016/679 (GDPR).</p><h2>Titolare del trattamento</h2><p>Davide Davoglio, Arezzo (Italia) – <a href='mailto:{MAIL}'>{MAIL}</a>.</p><h2>Dati trattati</h2><ul><li><strong>Navigazione</strong>: il sito non usa cookie, analytics o tracker. L'hosting (GitHub Pages, GitHub Inc.) può registrare dati tecnici come l'indirizzo IP nei log di server per sicurezza e funzionamento, secondo la propria informativa; base giuridica: legittimo interesse (art. 6.1.f).</li><li><strong>Email</strong>: se ci scrivi trattiamo indirizzo e contenuto del messaggio solo per rispondere; base giuridica: misure su richiesta dell'interessato / legittimo interesse. Conservazione: il tempo necessario a gestire la richiesta e comunque non oltre 24 mesi.</li></ul><h2>Trasferimenti</h2><p>GitHub Inc. ha sede negli USA; i trasferimenti avvengono secondo le garanzie previste dal GDPR (es. EU-US Data Privacy Framework o clausole contrattuali standard) indicate dal fornitore.</p><h2>Diritti</h2><p>Puoi chiedere accesso, rettifica, cancellazione, limitazione, opposizione e portabilità (artt. 15-22) scrivendo al titolare, e proporre reclamo al Garante per la protezione dei dati personali (garanteprivacy.it).</p><p>Nessuna newsletter è attiva: se verrà introdotta, sarà con consenso esplicito e informativa dedicata.</p><p><small>Ultimo aggiornamento: {it(oggi)}.</small></p></div>"),
}
for pth, (t, d, body) in STAT.items():
    W(pth, page(pth, t, d, body + (TOOL if pth == "chi-siamo.html" else ""), ld={"@context": "https://schema.org", "@type": "WebPage", "name": t, "url": BASE + pth, "inLanguage": "it", "publisher": ORG}))
(D / "404.html").write_text(page("404.html", "Pagina non trovata", "La pagina richiesta non esiste.", '<div class="box" style="text-align:center"><h1>Pagina non trovata (404)</h1><p>La pagina che cerchi non esiste o è stata spostata. Il bando potrebbe essere scaduto e archiviato.</p><p><a class="btn" href="/incentiviperte/index.html">Torna ai bandi</a></p></div>', pre="/incentiviperte/").replace('<link rel="canonical" href="https://essedade.github.io/incentiviperte/404.html">', '<meta name="robots" content="noindex">'), encoding="utf-8")
(D / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{BASE}{'' if p == 'index.html' else p}</loc><lastmod>{AGG}</lastmod></url>" for p in pages) + "</urlset>", encoding="utf-8")
(D / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
(D / ".nojekyll").write_text("")
print(f"OK: {len(B)} bandi, {len(pages)+1} pagine -> {D}")
