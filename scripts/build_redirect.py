#!/usr/bin/env python3
"""Genera dist-redirect/: rimando dal vecchio GitHub Pages al sito su Cloudflare.

Per ogni pagina HTML di dist/ scrive una pagina minima con meta refresh,
canonical e location.replace verso lo stesso percorso su
https://incentiviperte.pages.dev/. La 404 rimanda alla home nuova.
Aggiunge .nojekyll. Non pubblica nulla e non tocca il branch gh-pages.

Uso: python3 scripts/build_redirect.py
"""
import html
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUT = ROOT / "dist-redirect"
NEW = "https://incentiviperte.pages.dev/"


def destination(rel):
    if rel == "404.html":
        return NEW
    return NEW + rel


def redirect_html(url):
    safe = html.escape(url, quote=True)
    js = url.replace("\\", "\\\\").replace('"', '\\"')
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>IncentiviPerTe si è spostato</title>
<meta http-equiv="refresh" content="0; url={safe}">
<link rel="canonical" href="{safe}">
<script>location.replace("{js}");</script>
</head>
<body>
<p>IncentiviPerTe si è spostato. <a href="{safe}">Continua sul nuovo sito</a>.</p>
</body>
</html>
"""


def generate(dist=DIST, out=OUT):
    dist = pathlib.Path(dist)
    out = pathlib.Path(out)
    pages = sorted(p for p in dist.rglob("*.html") if p.is_file())
    if not pages:
        raise ValueError("dist/ non contiene pagine HTML: esegui prima scripts/build.py")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    (out / ".nojekyll").write_text("", encoding="utf-8")
    for src in pages:
        rel = src.relative_to(dist).as_posix()
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(redirect_html(destination(rel)), encoding="utf-8")
    return len(pages)


def main():
    try:
        n = generate()
    except ValueError as ex:
        print(f"ERRORE: {ex}", file=sys.stderr)
        return 1
    print(f"OK: {n} rimandi -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
