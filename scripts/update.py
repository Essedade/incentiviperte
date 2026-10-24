#!/usr/bin/env python3
"""Ricontrolla ogni bando sulla fonte ufficiale (pagina raggiungibile + testo atteso).

Se il controllo riesce aggiorna ultimo_controllo; altrimenti segnala il caso in report.txt
per una revisione umana. Non modifica le schede andate male e non pubblica il sito.
Il markup, badge compresi, lo produce solo build.py: il conto dei giorni non è scritto
nel HTML, quindi una nuova build prima della scadenza non cambia quel testo.
Uso: python3 scripts/update.py && python3 scripts/build.py
"""
import datetime
import json
import pathlib
import urllib.error
import urllib.request

R = pathlib.Path(__file__).resolve().parent.parent
P = R / "data" / "bandi.json"
REPORT = R / "report.txt"


def matches(body, expected):
    return isinstance(expected, str) and bool(expected.strip()) and expected in body


def atomic_write(path, text):
    path = pathlib.Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def fetch(url, timeout=30):
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("url non https")
    req = urllib.request.Request(url, headers={"User-Agent": "IncentiviPerTe-checker/0.2"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read().decode("utf-8", "ignore")


def main():
    raw = P.read_text(encoding="utf-8")
    bandi = json.loads(raw)
    if not isinstance(bandi, list):
        print("ERRORE: bandi.json non è una lista")
        return 1
    oggi = datetime.date.today().isoformat()
    problemi = []
    for b in bandi:
        bid = b.get("id", "?")
        try:
            testo = fetch(b.get("url", ""))
        except (urllib.error.URLError, TimeoutError, ValueError) as ex:
            problemi.append(f"{bid}: errore {ex}")
            continue
        if matches(testo, b.get("check", "")):
            b["ultimo_controllo"] = oggi
        else:
            atteso = b.get("check", "")
            problemi.append(f'{bid}: testo atteso "{atteso}" non trovato')
    nuovo = json.dumps(bandi, ensure_ascii=False, indent=1)
    if nuovo != raw:
        atomic_write(P, nuovo)
    atomic_write(REPORT, ("\n".join(problemi) or "Tutto ok") + "\n")
    print("\n".join(problemi) or "Tutto ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
