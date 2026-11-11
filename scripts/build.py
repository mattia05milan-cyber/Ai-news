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

CSS = "body{font:18px/1.5 system-ui,sans-serif;max-width:40rem;margin:0 auto;padding:1rem;color:#222;background:#fff}" \
      "@media(prefers-color-scheme:dark){body{background:#111;color:#eee}a{color:#8ab4f8}}" \
      "h1{font-size:1.5rem}h2{font-size:1.2rem;margin-top:1.6rem;border-bottom:1px solid #8884}" \
      "li{margin:.6rem 0}small{opacity:.65}nav a{margin-right:.8rem}"

def page(titolo, corpo):
    return f'<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' \
           f'<title>{e(titolo)}</title><style>{CSS}</style></head><body><nav><a href="index.html">Indice</a></nav><h1>{e(titolo)}</h1>{corpo}</body></html>'

def voce(v, data=None):
    r = f'<li><a href="{e(v["link"])}">{e(v["titolo"])}</a>'
    if v.get("riassunto") and v["riassunto"] != v["titolo"]: r += f'<br>{e(v["riassunto"])}'
    sfx = f' · {bella(data)}' if data else ""
    return r + f'<br><small>{e(v.get("fonte",""))}{sfx}</small></li>'

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
        if vs: corpo += f"<h2>{e(SEZ[k])}</h2><ul>" + "".join(voce(v) for v in vs) + "</ul>"
    open(f"docs/{d}.html", "w").write(page(f"Notizie del {bella(d)}", corpo))

for k, nome in SEZ.items():
    corpo, n = "<ul>", 0
    for d in sorted(giorni, reverse=True):
        for v in giorni[d]:
            if v["sezione"] == k: corpo += voce(v, d); n += 1
    open(f"docs/sezione-{k}.html", "w").write(page(nome, corpo + "</ul>" if n else "<p>Ancora nessuna notizia.</p>"))

corpo = "<h2>Per sezione</h2><ul>" + "".join(f'<li><a href="sezione-{k}.html">{e(n)}</a></li>' for k, n in SEZ.items()) + "</ul><h2>Per data</h2><ul>"
corpo += "".join(f'<li><a href="{d}.html">{bella(d)}</a> <small>({len(giorni[d])} notizie)</small></li>' for d in sorted(giorni, reverse=True)) + "</ul>"
open("docs/index.html", "w").write(page("Archivio notizie AI", corpo))
print(f"{len(giorni)} giorni, pagine generate in docs/")
