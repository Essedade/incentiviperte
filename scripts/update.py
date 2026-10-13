#!/usr/bin/env python3
"""Ricontrolla ogni bando sulla fonte ufficiale (pagina raggiungibile + testo atteso 'check').
Se ok aggiorna 'ultimo_controllo'; altrimenti lo segnala in report.txt per revisione umana.
Nessun LLM: costo zero. Uso: python scripts/update.py && python scripts/build.py"""
import json, pathlib, datetime, urllib.request
R = pathlib.Path(__file__).resolve().parent.parent
P = R / "data/bandi.json"; B = json.loads(P.read_text(encoding="utf-8"))
oggi = datetime.date.today().isoformat(); prob = []
for b in B:
    try:
        req = urllib.request.Request(b["url"], headers={"User-Agent": "IncentiviPerTe-checker/0.1"})
        t = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        if b.get("check", "") in t: b["ultimo_controllo"] = oggi
        else: prob.append(f'{b["id"]}: testo atteso "{b["check"]}" non trovato')
    except Exception as ex: prob.append(f'{b["id"]}: errore {ex}')
P.write_text(json.dumps(B, ensure_ascii=False, indent=1), encoding="utf-8")
(R / "report.txt").write_text("\n".join(prob) or "Tutto ok", encoding="utf-8")
print("\n".join(prob) or "Tutto ok")
