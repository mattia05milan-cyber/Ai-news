#!/usr/bin/env python3
"""Invia la notifica delle 9:00 (ntfy + WhatsApp opzionale). Zero AI, solo libreria standard."""
import glob, json, os, sys, urllib.parse, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

env, rome = os.environ.get, datetime.now(ZoneInfo("Europe/Rome"))
if env("FORCE") != "1" and rome.hour != 9: sys.exit("Non sono le 9 a Roma: esco.")
files = sorted(glob.glob("data/20??-??-??.json"))
if not files: sys.exit("Nessun file giornaliero.")
day = os.path.basename(files[-1])[:-5]
if env("FORCE") != "1" and day != rome.date().isoformat(): sys.exit("Nessuna novita di oggi: niente messaggio.")
voci = json.load(open(files[-1]))
if not voci: sys.exit("Giornata vuota: niente messaggio.")

# 5 titoli: prima 2 legali, poi una per sezione
scelte = [v for v in voci if v["sezione"] == "legale"][:2]
for v in voci:
    if len(scelte) < 5 and v not in scelte and v["sezione"] not in [s["sezione"] for s in scelte]: scelte.append(v)
for v in voci:
    if len(scelte) < 5 and v not in scelte: scelte.append(v)
riga = lambda v: "• " + (v.get("riassunto") or v["titolo"])[:100]
corpo = "\n".join(riga(v) for v in scelte)
owner, repo = (env("GITHUB_REPOSITORY") or "utente/Ai-news").split("/")
link = f"https://{owner}.github.io/{repo}/{day}.html"
print(corpo, link, sep="\n")
if env("DRY_RUN") == "1": sys.exit()

def post(url, data=None, headers=None):
    urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers or {"User-Agent": "ai-news-bot"}), timeout=20).read()

if env("NTFY_TOPIC"):
    post("https://ntfy.sh/" + env("NTFY_TOPIC"), corpo.encode(), {"Title": "Notizie AI di oggi", "Click": link, "Tags": "newspaper", "User-Agent": "ai-news-bot"})
    print("ntfy inviato")
else: print("NTFY_TOPIC mancante: ntfy saltato")
if env("WHATSAPP_ENABLED") == "true" and env("CALLMEBOT_KEY") and env("WHATSAPP_PHONE"):
    q = urllib.parse.urlencode({"phone": env("WHATSAPP_PHONE"), "apikey": env("CALLMEBOT_KEY"), "text": f"Notizie AI di oggi\n{corpo}\n{link}"})
    post("https://api.callmebot.com/whatsapp.php?" + q)
    print("WhatsApp inviato")
