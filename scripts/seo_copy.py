"""Testi SEO del 25/10/2026 e titoli/meta delle schede.

I title delle schede sono quelli della tabella 6.R (e delle schede 6.15-6.20).
La meta si genera da importo, destinatari e scadenza, al massimo 155 caratteri,
senza puntini di sospensione. Dove il documento fissa la frase, si usa quella,
accorciata solo se supera il limite o se contiene la stringa vietata «Arezzo-Siena».
"""
import re
import warnings

TITOLO_SCHEDA = {
    "bando-132-bei-2026": "Bando 1.3.2 BEI Toscana 2026: aiuti su interessi e garanzia",
    "minibond-toscana-2026": "Minibond Toscana 2026: contributi per PMI che emettono",
    "igp-artigianato-toscana-2026": "Bando IGP artigianato Toscana 2026: contributo 50%",
    "toscana-disabilita-assunzioni-2026-2027": "Contributi assunzione disabili Toscana 2026-2027",
    "economia-circolare-privati": "Bando Economia Circolare Toscana (chiuso il 23/10/2026)",
    "premio-innovazione-toscana-2026": "Premio Innovazione Toscana 2026: premi per PMI e startup",
    "cciaa-firenze-nuove-imprese-2026": "Contributi nuove imprese Firenze 2026: fino a 5.000 €",
    "cciaa-firenze-sicurezza-sedi-2026": "Contributi sicurezza sedi aziendali Firenze 2026",
    "cciaa-firenze-turismo-sostenibile-2026": "Turismo sostenibile Firenze 2026: contributi alle MPMI",
    "cciaa-arezzo-siena-certificazioni-2026": "Voucher parità di genere Arezzo e Siena 2026",
    "cciaa-arezzo-siena-export-2026-siena": "Contributi fiere internazionali 2026 Siena: Bando Export",
    "cciaa-maremma-tirreno-creazione-impresa-2026": "Bando creazione d'impresa Livorno e Grosseto 2026",
    "cciaa-maremma-tirreno-agricoltura-green-2026": "Agricoltura green Livorno e Grosseto 2026",
    "cciaa-maremma-tirreno-certificazioni-qualita-2026": "Certificazioni di qualità Livorno e Grosseto 2026",
    "cciaa-maremma-tirreno-doppia-transizione-2026": "Doppia transizione Livorno e Grosseto 2026: voucher",
    "cciaa-maremma-tirreno-frihub-2026": "Voucher FRIHUB 2026 Livorno e Grosseto",
    "cciaa-maremma-tirreno-imprese-vicinato-2026": "Bando imprese di vicinato Livorno e Grosseto 2026",
    "cciaa-maremma-tirreno-internazionalizzazione-2026": "Internazionalizzazione Livorno e Grosseto 2026",
    "cciaa-maremma-tirreno-societa-benefit-2026": "Contributi società benefit Livorno e Grosseto 2026",
    "cciaa-maremma-tirreno-turismo-sostenibile-2026": "Turismo sostenibile Livorno e Grosseto 2026",
    "cciaa-tno-competenze-trasversali-2026": "Contributi PCTO 2026 Lucca, Massa-Carrara, Pisa",
    "cciaa-tno-doppia-transizione-2-2026": "Voucher doppia transizione Lucca, Massa, Pisa 2026",
    "cciaa-pistoia-prato-formazione-lavoro-2026": "Contributi formazione scuola-lavoro Pistoia-Prato 2026",
    "step-2026-sovvenzione-umbria": "Avviso STEP Umbria 2026: linea a fondo perduto",
    "step-2026-umbria": "Avviso STEP Umbria 2026: finanziamento all'1%",
    "efficienza-energetica-2026-umbria": "Bando efficienza energetica Umbria 2026 per imprese",
    "fonti-rinnovabili-2026-umbria": "Bando fonti rinnovabili Umbria 2026 per imprese",
    "umbria-poli-innovazione-2026": "Avviso Poli di Innovazione Umbria 2026",
    "umbria-feampa-indennizzo-pesca-acquacoltura-2026": "Indennizzo FEAMPA pesca e acquacoltura Umbria 2026",
    "fondo-starter-er-2026": "StartER Emilia-Romagna 2026: finanziamenti a tasso zero",
    "fondo-greener-er-2026": "GreenER Emilia-Romagna 2026: finanziamenti per l'energia",
    "trasferimento-tecnologico-er-2026": "Trasferimento tecnologico Emilia-Romagna 2026",
    "fotovoltaico-pensiline-er-2026": "Fotovoltaico su pensiline Emilia-Romagna 2026",
    "assunzioni-montagna-er-2026": "Contributi assunzioni in montagna Emilia-Romagna 2026",
    "eureca-er-tutti-settori-2026": "EuReCa Emilia-Romagna: contributo sugli interessi",
    "cciaa-bologna-finanza-innovativa-2026": "Finanza innovativa Bologna 2026: contributi alle MPMI",
    "cciaa-emilia-credito-confidi-2026": "Contributi Confidi Parma, Piacenza, Reggio Emilia 2026",
    "cciaa-ferrara-ravenna-credito-confidi-2026": "Contributi Confidi Ferrara e Ravenna 2026",
    "cciaa-ferrara-ravenna-creazione-imprese-giovanili-2026": "Imprese giovanili Ferrara e Ravenna 2026: avvio",
    "cciaa-ferrara-ravenna-competitivita-imprese-giovanili-2026": "Imprese giovanili Ferrara e Ravenna 2026: crescita",
    "ferrara-locali-sfitti-centro-storico": "Locali sfitti centro storico Ferrara: contributo affitto",
    "cciaa-modena-fondo-sicurezza-2026": "Fondo sicurezza Modena 2026: contributi alle imprese",
    "cciaa-modena-occupazione-giovanile-2026": "Occupazione giovanile Modena 2026: contributi",
    "cciaa-romagna-antirapina-2026": "Contributi antirapina Forlì-Cesena e Rimini 2026",
    "cciaa-romagna-credito-confidi-2026": "Contributi Confidi Forlì-Cesena e Rimini 2026",
    "cciaa-romagna-fondo-energia-2026": "Fondo Energia Imprese Romagna 2026",
    "nuova-sabatini": "Nuova Sabatini 2026: come funziona e chi può chiederla",
    "fondo-garanzia-pmi": "Fondo di garanzia PMI: come funziona e come si chiede",
    "italia-economia-sociale": "Italia Economia Sociale: agevolazioni imprese sociali",
    "detrazione-investimenti-startup-innovative": "Detrazione 65% per chi investe in startup innovative",
    "autoimpiego-centro-nord": "Autoimpiego Centro-Nord 2026: requisiti e importi",
    "resto-al-sud-2": "Resto al Sud 2.0: vale al Centro-Nord? Le alternative",
    "on-nuove-imprese-tasso-zero": "ON Nuove imprese a tasso zero 2026: requisiti",
    "smart-start-italia": "Smart&Start Italia 2026: requisiti e tasso zero",
    "bando-132-50k-2026": "Bando 1.3.2 Toscana 2026: finanziamenti fino a 50.000 €",
    "cciaa-arezzo-siena-export-2026-arezzo": "Contributi fiere internazionali 2026 Arezzo: Bando Export",
    "bando-neve-funzionamento-toscana-2026": "Bando Neve Toscana 2026: fondo perduto fino all'80%",
}

# H1 più lungo del title, solo dove il documento lo distingue.
H1_SCHEDA = {
    "autoimpiego-centro-nord": "Autoimpiego Centro-Nord: requisiti, importi e come funziona",
    "resto-al-sud-2": "Resto al Sud 2.0: chi può accedere e cosa c'è al Centro-Nord",
    "on-nuove-imprese-tasso-zero": "ON – Oltre Nuove imprese a tasso zero: requisiti e novità 2026",
    "smart-start-italia": "Smart&Start Italia: requisiti e finanziamento a tasso zero",
    "bando-132-50k-2026": "Bando 1.3.2 Toscana – Sostegno alle PMI fino a 50.000 € (2026)",
    "cciaa-arezzo-siena-export-2026-arezzo": "Bando Export 2026 Arezzo: contributi per le fiere internazionali",
    "cciaa-arezzo-siena-export-2026-siena": "Bando Export 2026 Siena: contributi per le fiere internazionali",
    "bando-neve-funzionamento-toscana-2026": (
        "Bando Neve Toscana 2026: fondo perduto fino all'80% per gli impianti di risalita"
    ),
}

# Meta fissate dal documento. Nuova Sabatini e Resto al Sud sono accorciate di poche
# lettere rispetto alla frase del documento, per restare entro 155 caratteri.
# L'export di Arezzo non usa «Arezzo-Siena»: quella stringa è vietata nel sito.
META_FISSA = {
    "nuova-sabatini": (
        "MIMIT: contributo pari agli interessi al 2,75% o 3,575% su finanziamenti "
        "da 20.000 a 4 mln € per beni strumentali delle PMI. A sportello. Requisiti e link."
    ),
    "cciaa-maremma-tirreno-imprese-vicinato-2026": (
        "Camera di Commercio Maremma e Tirreno: fondo perduto 60% fino a 2.500 € "
        "per negozi di vicinato. Risorse esaurite: lista d'attesa fino al 10/11/2026."
    ),
    "fondo-starter-er-2026": (
        "Emilia-Romagna: finanziamento da 20.000 a 500.000 €, 75% a tasso zero "
        "(80% imprese femminili), per imprese nate da max 5 anni. Domande fino al 30/11/2026."
    ),
    "autoimpiego-centro-nord": (
        "Per under 35 inattivi, inoccupati o disoccupati che avviano un'attività al Centro-Nord: "
        "voucher fino a 30.000 € o fondo perduto 65% fino a 120.000 €."
    ),
    "resto-al-sud-2": (
        "Resto al Sud 2.0 vale solo in 8 regioni del Mezzogiorno, non in Toscana, Umbria "
        "ed Emilia-Romagna. Al Centro-Nord c'è Autoimpiego Centro-Nord: ecco come."
    ),
    "on-nuove-imprese-tasso-zero": (
        "Per micro e piccole imprese di giovani o donne fino a 60 mesi. Dal 1° luglio 2026 "
        "solo finanziamento a tasso zero, senza fondo perduto. Requisiti e link."
    ),
    "smart-start-italia": (
        "Smart&Start Italia: tasso zero sull'80-90% delle spese per startup innovative "
        "fino a 60 mesi. In Toscana niente fondo perduto. Requisiti e link ufficiale."
    ),
    "bando-132-50k-2026": (
        "Regione Toscana: fondo perduto su interessi e garanzia per finanziamenti fino a "
        "50.000 € a PMI e professionisti. A sportello fino a esaurimento risorse."
    ),
    "cciaa-arezzo-siena-export-2026-arezzo": (
        "Camera di Commercio di Arezzo e Siena: 50% delle spese per fiere internazionali "
        "all'estero, fino a 1.500 €. Domande entro il 15/12/2026."
    ),
    "cciaa-arezzo-siena-export-2026-siena": (
        "Camera di Commercio di Arezzo e Siena: 50% delle spese per fiere internazionali, "
        "anche in Italia, fino a 1.500 €. Domande entro il 15/12/2026."
    ),
}

LEAD_SCHEDA = {
    "autoimpiego-centro-nord": (
        "Autoimpiego Centro-Nord è l'incentivo del Ministero del Lavoro per i giovani tra 18 e 35 anni "
        "non compiuti, inattivi, inoccupati o disoccupati, che avviano un'attività in 12 regioni del "
        "Centro-Nord, tra cui Toscana, Umbria ed Emilia-Romagna. Dà un voucher a fondo perduto fino a "
        "30.000 € (elevabile a 40.000 €) oppure un contributo a fondo perduto del 65% per programmi fino "
        "a 120.000 € e del 60% fino a 200.000 €. È a sportello dal 15/10/2025, fino a esaurimento risorse."
    ),
    "resto-al-sud-2": (
        "Resto al Sud 2.0 vale solo per chi avvia un'attività in Abruzzo, Basilicata, Calabria, Campania, "
        "Molise, Puglia, Sardegna o Sicilia: non si può usare in Toscana, Umbria ed Emilia-Romagna. "
        "Per i giovani under 35 del Centro-Nord la misura con le stesse regole di base è Autoimpiego "
        "Centro-Nord, con importi più bassi."
    ),
    "on-nuove-imprese-tasso-zero": (
        "ON – Oltre Nuove imprese a tasso zero è la misura del MIMIT per micro e piccole imprese "
        "costituite da non più di 60 mesi, o da costituire, con soci in maggioranza giovani tra 18 e 35 anni "
        "o donne. Per le domande presentate dal 1° luglio 2026 il fondo perduto è esaurito: l'agevolazione "
        "è solo un finanziamento a tasso zero da rimborsare in 10 anni, per progetti fino a 1,5 milioni € "
        "(3 milioni € per le imprese tra 36 e 60 mesi)."
    ),
    "smart-start-italia": (
        "Smart&Start Italia finanzia le startup innovative di piccola dimensione, costituite da non più di "
        "60 mesi e iscritte nella sezione speciale del Registro delle imprese, con un finanziamento a tasso "
        "zero dell'80% delle spese ammissibili (90% se la compagine è tutta di donne e/o under 36). "
        "In Toscana, Umbria ed Emilia-Romagna non c'è la quota a fondo perduto, prevista solo nel Mezzogiorno. "
        "Domande a sportello, esaminate entro 60 giorni."
    ),
    "bando-132-50k-2026": (
        "Il Bando 1.3.2 della Regione Toscana, gestito da Sviluppo Toscana, copre con un contributo a fondo "
        "perduto gli interessi e il costo della garanzia su finanziamenti bancari fino a 50.000 € per "
        "investimenti di PMI e professionisti toscani. Ha tre linee: A1 per nuove imprese giovanili, "
        "femminili o di persone in ammortizzatori sociali; A2 per chi rileva uno stabilimento chiuso; "
        "B per le PMI già attive. È a sportello dall'11/05/2026, fino a esaurimento risorse."
    ),
    "cciaa-arezzo-siena-export-2026-arezzo": (
        "Il Bando Export 2026 della Camera di Commercio di Arezzo e Siena rimborsa alle micro, piccole e "
        "medie imprese della provincia di Arezzo il 50% delle spese per partecipare in presenza a fiere "
        "internazionali all'estero (affitto e allestimento dello stand, spedizione del campionario), fino a "
        "1.500 € per domanda. Domande via PEC fino al 15/12/2026, in ordine di arrivo."
    ),
    "cciaa-arezzo-siena-export-2026-siena": (
        "Il Bando Export 2026 della Camera di Commercio di Arezzo e Siena rimborsa alle micro, piccole e "
        "medie imprese della provincia di Siena il 50% delle spese per partecipare in presenza a fiere "
        "internazionali, anche in Italia, fino a 1.500 € per domanda. Domande via PEC fino al 15/12/2026, "
        "in ordine di arrivo."
    ),
}

# Domande già coperte dal testo della scheda. Le risposte restano generali.
FAQ_SCHEDA = {
    "autoimpiego-centro-nord": (
        (
            "Chi può fare domanda?",
            "Giovani tra 18 anni compiuti e 35 non compiuti, inattivi, inoccupati o disoccupati, "
            "anche disoccupati GOL e working poor.",
        ),
        (
            "Quali attività sono escluse?",
            "Agricoltura, pesca e acquacoltura.",
        ),
        (
            "L'attività deve essere già aperta?",
            "Sì: l'impresa o la partita IVA vanno avviate nel mese della domanda o in quello precedente "
            "e non devono essere ancora operative.",
        ),
        (
            "Come funziona l'esame delle domande?",
            "A sportello, in ordine cronologico, entro 90 giorni e nei limiti delle risorse.",
        ),
        (
            "Vale anche al Sud?",
            "No: al Sud c'è Resto al Sud 2.0.",
        ),
    ),
    "on-nuove-imprese-tasso-zero": (
        (
            "ON dà ancora il fondo perduto?",
            "No, per le domande dal 1° luglio 2026 resta solo il finanziamento a tasso zero.",
        ),
    ),
}

META_MAX = 155
TITOLO_MAX = 60
CODA_META = "Requisiti e link ufficiale."


def _it_date(iso):
    y, m, g = iso.split("-")
    return f"{g}/{m}/{y}"


def _senza_vietate(testo):
    """Toglie dal ripiego le stringhe che la build non può pubblicare."""
    testo = str(testo or "")
    testo = testo.replace("Arezzo-Siena", "Arezzo e Siena")
    testo = re.sub(r"invitalia", "", testo, flags=re.I)
    testo = re.sub(r"\+\s*iva", "", testo, flags=re.I)
    testo = testo.replace("…", " ").replace("...", " ")
    return " ".join(testo.split())


def _titolo_ripiego(bando):
    """Title di ripiego dal nome del bando, entro 60 caratteri, senza promesse."""
    nome = _senza_vietate(bando.get("titolo"))
    regione = _senza_vietate(bando.get("regione"))
    if nome and regione and regione.lower() not in nome.lower():
        con_regione = f"{nome} ({regione})"
        candidato = con_regione if len(con_regione) <= TITOLO_MAX else nome
    else:
        candidato = nome or regione
    if not candidato:
        candidato = _senza_vietate(str(bando.get("id") or "bando").replace("-", " "))
    titolo = _accorcia(candidato, TITOLO_MAX)
    if not titolo or "Arezzo-Siena" in titolo or "…" in titolo or "..." in titolo:
        titolo = _accorcia(
            _senza_vietate(str(bando.get("id") or "bando").replace("-", " ")) or "Bando",
            TITOLO_MAX,
        )
    return titolo or "Bando"


def titolo_scheda(bando):
    """Title della scheda. Se manca in TITOLO_SCHEDA, un ripiego: la build non si ferma."""
    titolo = TITOLO_SCHEDA.get(bando["id"])
    generato = False
    if not titolo:
        titolo = _titolo_ripiego(bando)
        generato = True
    if len(titolo) > TITOLO_MAX:
        raise ValueError(f"{bando['id']}: title SEO di {len(titolo)} caratteri")
    if "Arezzo-Siena" in titolo or "…" in titolo:
        raise ValueError(f"{bando['id']}: title SEO non pubblicabile")
    if generato:
        TITOLO_SCHEDA[bando["id"]] = titolo
        warnings.warn(
            f"{bando['id']}: manca il title SEO in TITOLO_SCHEDA; "
            f"la build usa il ripiego «{titolo}» ({len(titolo)} caratteri). "
            f"Aggiungi un title dedicato, al massimo {TITOLO_MAX} caratteri.",
            UserWarning,
            stacklevel=2,
        )
    return titolo


def h1_scheda(bando):
    return H1_SCHEDA.get(bando["id"]) or titolo_scheda(bando)


def titolo_in_elenco(bando):
    """Il nome in elenco. Il premio toscano non pubblica il nome di persona nel titolo ufficiale."""
    if bando["id"] == "premio-innovazione-toscana-2026":
        return titolo_scheda(bando)
    return bando["titolo"]


def _ente_breve(ente):
    if ente.startswith("Comune di Ferrara"):
        return "Comune di Ferrara"
    testo = ente
    for src, dst in (
        ("Camera di Commercio della ", "Camera di Commercio "),
        ("Camera di Commercio di ", "Camera di Commercio "),
        ("Camera di Commercio dell'", "Camera di Commercio "),
    ):
        testo = testo.replace(src, dst)
    if testo.startswith("Regione "):
        testo = testo[len("Regione "):]
    if " (" in testo:
        testo = testo.split(" (", 1)[0]
    if " / " in testo:
        testo = testo.split(" / ", 1)[0]
    if " – " in testo:
        testo = testo.split(" – ", 1)[0]
    return testo.strip()


def _importo_breve(importo):
    testo = importo.split("·")[0].strip().rstrip(".")
    testo = testo.replace("–", "-").replace("—", "-")
    testo = " ".join(testo.split())
    # Prima clausola, senza spezzare una parentesi («investimenti, start-up»).
    profondita = 0
    for i, ch in enumerate(testo):
        if ch == "(":
            profondita += 1
        elif ch == ")":
            profondita = max(0, profondita - 1)
        elif ch == "," and profondita == 0:
            prima = testo[:i].strip()
            if len(prima) >= 12:
                return prima
            break
    return testo


def _destinatari_brevi(nomi):
    return ", ".join(nomi)


def _stato_meta(bando):
    nota = (bando.get("nota_scadenza") or "").lower()
    if bando.get("stato") == "lista_attesa":
        if bando.get("scadenza"):
            return f"Risorse esaurite: lista d'attesa fino al {_it_date(bando['scadenza'])}."
        return "Risorse esaurite: lista d'attesa."
    if bando.get("scaduto") and bando.get("scadenza"):
        return f"Chiuso il {_it_date(bando['scadenza'])}."
    if not bando.get("scadenza"):
        if "esaurimento" in nota:
            return "A sportello fino a esaurimento risorse."
        return "A sportello."
    if "esaurimento" in nota:
        return f"A sportello fino al {_it_date(bando['scadenza'])}."
    return f"Scade il {_it_date(bando['scadenza'])}."


_PAROLE_APPESE = {
    "per", "di", "e", "ed", "a", "al", "allo", "alla", "ai", "alle",
    "del", "dello", "della", "dei", "delle", "con", "su", "sul", "sulla",
    "tra", "fra", "fino", "da", "in", "nel", "nella", "nei", "o",
}


def _accorcia(testo, n):
    """Accorcia su uno spazio, senza puntini e senza una preposizione finale."""
    testo = " ".join(testo.split())
    if len(testo) <= n:
        return testo.rstrip(".,;: ")
    taglio = testo[: n + 1].rsplit(" ", 1)[0].rstrip(".,;: ")
    while taglio and taglio.split()[-1].lower() in _PAROLE_APPESE:
        taglio = taglio.rsplit(" ", 1)[0].rstrip(".,;: ")
    if len(taglio) < 8:
        taglio = testo[:n].rstrip(".,;: ")
    return taglio


def _componi_meta(ente, importo, destinatari, stato, con_coda):
    coda = f" {CODA_META}" if con_coda else ""
    if destinatari:
        return f"{ente}: {importo}. Per {destinatari}. {stato}{coda}"
    return f"{ente}: {importo}. {stato}{coda}"


def meta_scheda(bando):
    """Meta da importo, destinatari e scadenza. Mai oltre 155 caratteri, mai con «…»."""
    if bando["id"] in META_FISSA:
        testo = " ".join(META_FISSA[bando["id"]].split())
    else:
        ente = _ente_breve(bando["ente"])
        importo = _importo_breve(bando["importo"])
        destinatari = _destinatari_brevi(bando["destinatari"])
        stato = _stato_meta(bando)
        testo = _componi_meta(ente, importo, destinatari, stato, True)
        if len(testo) > META_MAX:
            testo = _componi_meta(ente, importo, "", stato, True)
        if len(testo) > META_MAX:
            budget = META_MAX - (len(testo) - len(importo))
            importo = _accorcia(importo, max(budget, 16))
            testo = _componi_meta(ente, importo, "", stato, True)
        if len(testo) > META_MAX:
            testo = _componi_meta(ente, importo, "", stato, False)
        if len(testo) > META_MAX:
            importo = _accorcia(importo, max(12, len(importo) - (len(testo) - META_MAX)))
            testo = _componi_meta(ente, importo, "", stato, False)
    testo = " ".join(testo.split())
    if len(testo) > META_MAX:
        raise ValueError(f"{bando['id']}: meta di {len(testo)} caratteri")
    if "…" in testo or "..." in testo:
        raise ValueError(f"{bando['id']}: meta con puntini di sospensione")
    if "Arezzo-Siena" in testo:
        raise ValueError(f"{bando['id']}: meta con Arezzo-Siena")
    return testo


def lead_scheda(bando, quando):
    """Frase «cos'è, a chi serve, quanto dà, fino a quando», poi resta la sintesi della scheda."""
    if bando["id"] in LEAD_SCHEDA:
        return LEAD_SCHEDA[bando["id"]]
    nome = bando["titolo"]
    if bando["id"] == "premio-innovazione-toscana-2026":
        nome = titolo_scheda(bando)
    quanto = _importo_breve(bando["importo"])
    chi = _destinatari_brevi(bando["destinatari"])
    return f"{nome}: {quanto}. Per {chi}. {quando}."


def faq_scheda(bando):
    return FAQ_SCHEDA.get(bando["id"], ())
