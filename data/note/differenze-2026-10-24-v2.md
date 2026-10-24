# Bandi IncentiviPerTe – differenze tra v1 e v2 (controllo del 24/10/2026)

Partenza: `bandi-2026-10-24.json` (45 bandi). Risultato: `bandi-2026-10-24-v2.json` (56 bandi).
Validazione su copia locale: `build.py` OK (56 bandi, 78 pagine). `test_build.py`: 20 test superati su 21; fallisce solo il test fissato su "Aggiornato il 20/10/2026", come atteso. Il repository remoto non è stato toccato e non è stato pubblicato o inviato nulla.

## Aggiunti (11)

| id | Area | Scadenza | Nota | Fonte |
|---|---|---|---|---|
| cciaa-maremma-tirreno-certificazioni-qualita-2026 | Toscana | 10/11/2026 | 60%, fino a 2.000 € + 300 €; dotazione 30.000 €; 1.510,92 € residui (scheda del 19/10/2026) | https://www.lg.camcom.it/bandi/bando-certificazioni-qualita-2026 |
| cciaa-maremma-tirreno-societa-benefit-2026 | Toscana | 10/11/2026 | 60%, fino a 4.000 € + 300 €; 20.000 €; nessuna domanda al 21/10/2026 | https://www.lg.camcom.it/bandi/bando-sostegno-della-creazione-societa-benefit-anno-2026 |
| cciaa-maremma-tirreno-internazionalizzazione-2026 | Toscana | 10/11/2026 | **Risorse esaurite**: −18.481,60 € (scheda del 02/09/2026). Inserito con nota | https://www.lg.camcom.it/bandi/bando-sostegno-internazionalizzazione-delle-imprese-2026 |
| cciaa-maremma-tirreno-agricoltura-green-2026 | Toscana | 10/11/2026 | **Risorse impegnate**: 430.000 € tra liquidate e in corso (scheda del 01/09/2026). Inserito con nota | https://www.lg.camcom.it/bandi/bando-agricoltura-green-2026 |
| cciaa-maremma-tirreno-imprese-vicinato-2026 | Toscana | 10/11/2026 | **0,00 € disponibili** (scheda del 20/10/2026). Inserito con nota: il bando è formalmente aperto e accetta domande, finanziabili solo con economie o rifinanziamenti, come Doppia Transizione | https://www.lg.camcom.it/bandi/bando-sostegno-imprese-vicinato-2026 |
| cciaa-maremma-tirreno-frihub-2026 | Toscana | 06/11/2026 (prorogata, DD 384 del 16/10/2026) | voucher 100%, fino a 6.900 €; 82.800 €; province di GR, LI, LU, MS, PI | https://www.lg.camcom.it/bandi/bando-voucher-la-partecipazione-di-mpmi-al-progetto-frihub |
| cciaa-tno-competenze-trasversali-2026 | Toscana | 31/10/2026, ore 18:00 | PCTO, fino a 5.000 € per impresa; 100.000 €; tutte le imprese di LU, MS e PI | https://tno.camcom.it/bandi/2026/bando-la-realizzazione-di-percorsi-le-competenze-trasversali-lorientamento-e-la |
| cciaa-arezzo-siena-export-2026-arezzo | Toscana | 15/12/2026 | 50%, fino a 1.500 €; fondo 140.000 €; solo fiere all'estero | https://www.as.camcom.it/bando-export-2026-arezzo |
| cciaa-arezzo-siena-export-2026-siena | Toscana | 15/12/2026 | 50%, fino a 1.500 €; fondo 114.500 €; fiere internazionali anche in Italia | https://www.as.camcom.it/bando-export-2026-siena |
| umbria-feampa-indennizzo-pesca-acquacoltura-2026 | Umbria | 27/10/2026 | indennizzo 100% (pesca acque interne e acquacoltura); 18.958 €, aumentabile a 60.000 € | widget Regione Umbria, codBando 2026-002-11091 |
| umbria-poli-innovazione-2026 | Umbria | 30/10/2026 (termine da verificare, vedi sotto) | 50%; spesa da 0,5 a 2 milioni €; 4 milioni €, aumentabili a 6 milioni € | widget Regione Umbria, codBando 2026-002-8261 |

Tutti i check sono stati verificati sul testo delle pagine indicate in `url`.

## Modificati (2 bandi, più `ultimo_controllo` = 2026-10-24 su tutti)

| id | Campo | Valore vecchio | Valore nuovo | Fonte |
|---|---|---|---|---|
| cciaa-maremma-tirreno-turismo-sostenibile-2026 | sintesi (dotazione) | "Dotazione: da verificare (40.000 € nel bando, poi rifinanziato)." | "Dotazione: il bando indica 40.000 €; la scheda di avanzamento della Camera del 07/10/2026 riporta uno stanziamento di 60.000 € più un rifinanziamento di 50.000 €, con 48.677,68 € ancora da assegnare (dato a solo titolo informativo)." | Pagina del bando (modificata il 07/10) e PDF "AVANZAMENTO SITO TS26 07O" (creato il 07/10/2026): stanziamento 60.000 €, rifinanziamento 50.000 €, assegnate e liquidate 61.322,32 €, in corso 0,00 €, disponibili 48.677,68 € |
| toscana-disabilita-assunzioni-2026-2027 | sintesi | Esempi presi dal solo avviso di Arezzo e Siena; "importi e dotazione del proprio settore da verificare" | Importi uguali nei 5 avvisi (15.000 €; +2.000 € per ogni caratteristica, fino a 10.000 €; 5.000 €; 10.000 €; telelavoro e tutoraggio). Dotazione 3.199.999,99 €: Firenze e Prato 893.387,53 €; Lucca e Pistoia 625.629,68 €; Arezzo e Siena 626.091,28 €; Pisa e Massa Carrara 591.574,67 €; Grosseto e Livorno 463.316,83 € | Allegato A dei decreti ARTI n. 1168 del 06/10, n. 1161 del 05/10, n. 1163 del 05/10, n. 1164 del 06/10 e n. 1166 del 06/10/2026 |

## Rimossi
Nessuno. Economia Circolare (scaduta il 23/10) resta nel file perché il self_check di build.py lo richiede; è già segnata come scaduta.

## Conteggi per area

| Area | v1 | v2 |
|---|---|---|
| Toscana | 16 | 25 |
| Emilia-Romagna | 17 | 17 |
| Umbria | 4 | 6 |
| Nazionale | 8 | 8 |
| **Totale** | **45** | **56** |

## Elenchi dei bandi aperti: stato della lettura

| Elenco | Letto? | URL | Esito |
|---|---|---|---|
| Camera Toscana Nord-Ovest | Sì. Con il fetch semplice risponde 403; letta con intestazioni da browser | https://tno.camcom.it/bandi/bandi-aperti | 3 voci: Doppia Transizione II (già presente), Premio Eco-innovazione (chiuso il 20/10, escluso), PCTO 2026 (aggiunto) |
| Camera di Arezzo e Siena | In parte. L'elenco https://www.as.camcom.it/bandi-contributi-2 è vuoto; i bandi sono stati letti dalla sitemap | https://www.as.camcom.it/sitemap | Aggiunti Export 2026 Arezzo e Siena. Doppia Transizione 2026 è chiusa (Arezzo dal 20/07, Siena dal 05/08). Certificazioni è già presente |
| Camera di Pistoia-Prato | Sì | https://www.ptpo.camcom.it/servizi/contributi/index | Solo FSL 2026, già presente (scade il 12/11) |
| Camera dell'Umbria | Sì. La pagina carica l'elenco in JavaScript, che è stato letto tramite l'API del sito | https://www.umbria.camcom.it/promuovere-limpresa-e-il-territorio/bandi-e-contributi | Nessun bando di contributo aperto (Doppia Transizione chiusa il 14/09) |
| Sviluppumbria | Sì | https://www.sviluppumbria.it/imprese | Tutti chiusi (ICC il 05/10, Umbria Sorprendente il 23/09, Fiere il 31/07, autoimpiego il 30/06); STEP è già presente |
| Regione Umbria | Sì, tutte e due le pagine (22 risultati). La pagina contiene un iframe: è stato letto il widget | https://www.regione.umbria.it/la-regione/bandi → https://applicazioni.regione.umbria.it/widget/web/servizi/bandi1/-/bandi_WAR_bandiportlet | Aggiunti FEAMPA 222507 e Poli di Innovazione. Esclusi: SRD06 Azione 2 (le domande si aprono solo dopo il riconoscimento regionale della singola calamità); SRD07, SRH01, FESR 4.6.1, SOMS e FSE (destinati a enti, consulenti o cittadini); contributo caminetti (cittadini). In pagina 2 ci sono l'accreditamento degli ITS Academy e i tutori volontari per minori stranieri: nessuno dei due è per le imprese |

## Misure del punto 5
- **FRIHUB**: aperto, vale per 5 province toscane: **aggiunto**.
- **Scoperta Imprenditoriale II**: **non aggiunta**. Lo sportello è sospeso dall'08/10/2026 per esaurimento delle risorse (decreto direttoriale dell'08/10/2026, GURI n. 238 del 13/10/2026). La misura vale inoltre solo per Basilicata, Calabria, Campania, Molise, Puglia, Sardegna e Sicilia. Fonte: https://www.mimit.gov.it/it/incentivi/scoperta-imprenditoriale-2026

## Ancora da verificare
1. **Turismo sostenibile (Maremma e Tirreno)**: la delibera di rifinanziamento da 50.000 € non è stata trovata né nell'albo camerale né in Amministrazione trasparente. C'è anche un'incoerenza: lo stanziamento iniziale è di 40.000 € nel bando e di 60.000 € nella scheda. La scheda dichiara di avere "valenza esclusivamente informativa".
2. **Poli di Innovazione (Umbria)**: la scheda del portale indica domande dal 21/10 al 30/10/2026, mentre l'avviso aggiornato dopo la proroga ("prorogato_09.10.26", DD n. 10238/2026) indica invio via PEC dalle 12:00 del 10/09 alle 12:00 del 30/11/2026. Nel file ho messo il termine più prudente, 30/10, con la nota.
3. **Internazionalizzazione e Agricoltura green**: le ultime schede di avanzamento sono dell'inizio di settembre; i dati potrebbero essere cambiati.
4. **Fondo disabilità ARTI**: le voci D.3 e D.4 (fino a 3.000 € e 2.000 €) non sono descritte una per una nella sintesi.
