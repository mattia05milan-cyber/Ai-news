#!/usr/bin/env python3
"""Genera le pagine HTML in docs/ da data/AAAA-MM-GG.json (zero AI, solo libreria standard).
Formato di ogni file giornaliero: [{"sezione","titolo","riassunto","link","fonte"}, ...]"""
import glob, html, json, os
from datetime import date

SEZ = {"legale":"Legale e normative (UE e Italia)","modelli":"Nuovi modelli AI","claude":"Novità Claude",
       "github":"Progetti GitHub utili","strumenti":"Strumenti","finanza":"Finanza e banche",
       "marketing":"Marketing e social","lavoro":"Lavoro e aziende","creativita":"Creatività"}
MESI = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
e = html.escape
def bella(d): x = date.fromisoformat(d); return f"{x.day} {MESI[x.month-1]} {x.year}"

CSS = ":root{--bg:#f4f5f7;--card:#fff;--tx:#1c1e21;--mu:#6b7280;--ac:#2557d6;--bd:#e5e7eb}" \
      "@media(prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#181b21;--tx:#e8eaed;--mu:#9aa0a6;--ac:#8ab4f8;--bd:#2a2e36}}" \
      "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:17px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}" \
      "header{background:var(--ac);color:#fff;padding:1rem}header a{color:#fff;text-decoration:none;font-weight:700}" \
      "main{max-width:42rem;margin:0 auto;padding:1rem}h1{font-size:1.45rem;line-height:1.25;margin:.4rem 0 1rem}" \
      "section{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:.4rem 1rem 1rem;margin:0 0 1rem}" \
      "h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ac);margin:.9rem 0 .4rem}" \
      "ul{list-style:none;margin:0;padding:0}li{padding:.75rem 0;border-top:1px solid var(--bd)}li:first-child{border-top:0}" \
      "li a{color:var(--tx);font-weight:600;text-decoration:none}li a:hover{color:var(--ac)}" \
      "p{margin:.25rem 0}.fonte{color:var(--mu);font-size:.8rem}" \
      ".menu a{display:flex;justify-content:space-between;padding:.2rem 0;color:var(--tx);text-decoration:none;font-weight:600}.menu small{color:var(--mu);font-weight:400}"

def page(titolo, corpo):
    return f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' \
           f'<title>{e(titolo)}</title><style>{CSS}</style></head><body><header><a href="index.html">&larr; Archivio notizie AI</a></header><main><h1>{e(titolo)}</h1>{corpo}</main></body></html>'

def voce(v, data=None):
    r = f'<li><a href="{e(v["link"])}">{e(v["titolo"])}</a>'
    if v.get("riassunto") and v["riassunto"] != v["titolo"]: r += f'<p>{e(v["riassunto"])}</p>'
    sfx = f' &middot; {bella(data)}' if data else ""
    return r + f'<p class="fonte">{e(v.get("fonte",""))}{sfx}</p></li>'

giorni = {}
for f in sorted(glob.glob("data/20??-??-??.json")):
    d = os.path.basename(f)[:-5]
    v = json.load(open(f))
    if v: giorni[d] = v
os.makedirs("docs", exist_ok=True)

for d, voci in giorni.items():
    corpo = ""
    for k in SEZ:
        vs = [v for v in voci if v["sezione"] == k]
        if vs: corpo += f"<section><h2>{e(SEZ[k])}</h2><ul>" + "".join(voce(v) for v in vs) + "</ul></section>"
    open(f"docs/{d}.html", "w").write(page(f"Notizie del {bella(d)}", corpo))

for k, nome in SEZ.items():
    corpo, n = "<ul>", 0
    for d in sorted(giorni, reverse=True):
        for v in giorni[d]:
            if v["sezione"] == k: corpo += voce(v, d); n += 1
    open(f"docs/sezione-{k}.html", "w").write(page(nome, "<section>" + (corpo + "</ul>" if n else "<p>Ancora nessuna notizia.</p>") + "</section>"))

corpo = '<section><h2>Per sezione</h2><ul class="menu">' + "".join(f'<li><a href="sezione-{k}.html">{e(n)} <small>&rsaquo;</small></a></li>' for k, n in SEZ.items()) + "</ul></section>"
corpo += '<section><h2>Per data</h2><ul class="menu">' + "".join(f'<li><a href="{d}.html">{bella(d)} <small>{len(giorni[d])} notizie</small></a></li>' for d in sorted(giorni, reverse=True)) + "</ul></section>"
open("docs/index.html", "w").write(page("Archivio notizie AI", corpo))
print(f"{len(giorni)} giorni, pagine generate in docs/")
