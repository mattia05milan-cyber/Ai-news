#!/usr/bin/env python3
"""Raccoglie novita da fonti fisse (zero AI). Scrive data/new.json e aggiorna data/seen.json."""
import json, os, re, sys, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

# GitHub puo ritardare i cron di ore: non guardiamo l'ora, ma facciamo UNA raccolta al giorno
# (data/last_run.txt). Run manuale: FORCE=1 ignora il controllo.
OGGI = datetime.now(ZoneInfo("Europe/Rome")).date().isoformat()
if os.environ.get("FORCE") != "1" and os.path.exists("data/last_run.txt") and open("data/last_run.txt").read().strip() == OGGI:
    print("Raccolta di oggi gia fatta: esco."); sys.exit(0)

NOW = datetime.now(timezone.utc)
MAX_AGE, MAX_TOTAL, MAX_SOURCE = timedelta(days=3), 15, 3
AI = re.compile(r"\b(AI|IA|A\.I\.|LLM|GPT|Claude|Gemini|intelligenza artificiale|artificial intelligence|machine learning|generativ\w*|chatbot|algoritm\w*)\b", re.I)
LEGAL = re.compile(r"(AI Act|copyright|diritto d'autore|GDPR|privacy|regolament\w*|regulation|direttiva|normativ\w*|legge|law|Garante|AGCOM|AgID|Commissione|Commission|Parlamento|Parliament)", re.I)
# (sezione, nome, tipo, url, filtro)  filtro: None | "ai" | "legal" (ai + legal)
S = [
 ("legale","EU Digital Strategy","rss","https://digital-strategy.ec.europa.eu/en/rss.xml","ai"),
 ("legale","EDPB","rss","https://www.edpb.europa.eu/feed/news_en","ai"),
 ("legale","AgID","rss","https://www.agid.gov.it/it/rss.xml","ai"),
 ("legale","Agenda Digitale","rss","https://www.agendadigitale.eu/feed/","legal"),
 ("legale","Altalex","rss","https://www.altalex.com/rss","legal"),
 ("legale","Google News UE","rss","https://news.google.com/rss/search?hl=it&gl=IT&ceid=IT:it&q=%22AI+Act%22+OR+%22Commissione+europea%22+intelligenza+artificiale+regole",None),
 ("legale","Google News Garante","rss","https://news.google.com/rss/search?hl=it&gl=IT&ceid=IT:it&q=Garante+privacy+intelligenza+artificiale",None),
 ("legale","Google News AGCOM","rss","https://news.google.com/rss/search?hl=it&gl=IT&ceid=IT:it&q=AGCOM+intelligenza+artificiale+OR+copyright",None),
 ("legale","Google News copyright","rss","https://news.google.com/rss/search?hl=it&gl=IT&ceid=IT:it&q=copyright+%22intelligenza+artificiale%22+diritto+d%27autore",None),
 ("marketing","Google News marketing","rss","https://news.google.com/rss/search?hl=it&gl=IT&ceid=IT:it&q=marketing+social+media+intelligenza+artificiale",None),
 ("lavoro","Il Post Tecnologia","rss","https://www.ilpost.it/tecnologia/feed/","ai"),
 ("lavoro","The Verge AI","rss","https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",None),
 ("strumenti","MarkTechPost","rss","https://www.marktechpost.com/feed/",None),
 ("creativita","Google News creativita","rss","https://news.google.com/rss/search?hl=it&gl=IT&ceid=IT:it&q=intelligenza+artificiale+immagini+OR+video+OR+musica+generativa",None),
 ("modelli","OpenAI","rss","https://openai.com/news/rss.xml",None),
 ("modelli","Google AI","rss","https://blog.google/technology/ai/rss/",None),
 ("modelli","DeepMind","rss","https://deepmind.google/blog/rss.xml",None),
 ("modelli","Hugging Face","rss","https://huggingface.co/blog/feed.xml",None),
 ("claude","Claude Code","rss","https://github.com/anthropics/claude-code/releases.atom",None),
 ("claude","Anthropic SDK","rss","https://github.com/anthropics/anthropic-sdk-python/releases.atom",None),
 ("claude","Anthropic News","rss","https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",None),
 ("github","GitHub nuovi repo","gh","https://api.github.com/search/repositories?q=topic:llm+stars:>50+created:>{d}&sort=stars&per_page=5",None),
 ("github","Show HN","hn","https://hn.algolia.com/api/v1/search?tags=show_hn&query=AI&numericFilters=points>40,created_at_i>{t}",None),
 ("strumenti","Simon Willison","rss","https://simonwillison.net/atom/everything/",None),
 ("strumenti","Product Hunt","rss","https://www.producthunt.com/feed","ai"),
 ("strumenti","Hacker News","hn","https://hn.algolia.com/api/v1/search?tags=story&query=AI%20tool&numericFilters=points>80,created_at_i>{t}",None),
 ("finanza","Il Sole 24 Ore","rss","https://www.ilsole24ore.com/rss/finanza.xml","ai"),
 ("finanza","Finextra","rss","https://www.finextra.com/rss/headlines.aspx","ai"),
 ("marketing","Social Media Today","rss","https://www.socialmediatoday.com/feeds/news/","ai"),
 ("lavoro","Wired Italia","rss","https://www.wired.it/feed/rss","ai"),
 ("lavoro","MIT Tech Review","rss","https://www.technologyreview.com/feed/","ai"),
 ("lavoro","Il Sole 24 Ore Lavoro","rss","https://www.ilsole24ore.com/rss/norme-e-tributi.xml","ai"),
 ("creativita","Creative Bloq","rss","https://www.creativebloq.com/feeds/all","ai"),
]
ORDER = ["legale","modelli","claude","github","strumenti","finanza","marketing","lavoro","creativita"]
CAP = {s: 3 if s == "legale" else 2 for s in ORDER}

def get(url):
    r = urllib.request.Request(url.format(d=(NOW-timedelta(days=7)).date(), t=int((NOW-MAX_AGE).timestamp())), headers={"User-Agent": "ai-news-bot"})
    return urllib.request.urlopen(r, timeout=20).read()

def when(s):
    try: return parsedate_to_datetime(s)
    except Exception:
        try: return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None

def parse(kind, raw):
    if kind == "rss":
        for el in ET.fromstring(raw).iter():
            if el.tag.split("}")[-1] in ("item", "entry"):
                f = {c.tag.split("}")[-1]: c for c in el}
                link = (f["link"].get("href") or f["link"].text or "").strip() if "link" in f else ""
                d = next((f[k].text for k in ("pubDate","published","updated") if k in f and f[k].text), "")
                yield (f["title"].text or "").strip() if "title" in f else "", link, when(d)
    elif kind == "hn":
        for h in json.loads(raw)["hits"]:
            yield h["title"], h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}", None
    else:
        for r in json.loads(raw)["items"]:
            yield f"{r['full_name']}: {r.get('description') or ''}"[:140], r["html_url"], None

def main():
    seen = json.load(open("data/seen.json")) if os.path.exists("data/seen.json") else {}
    out, errors = [], []
    for sec, name, kind, url, flt in S:
        try: items = list(parse(kind, get(url)))
        except Exception as e:
            errors.append(f"{name}: {e}"); continue
        n = 0
        for title, link, dt in items:
            if n >= MAX_SOURCE or not title or not link or link in seen: continue
            if dt and dt.tzinfo and NOW - dt > MAX_AGE: continue
            if flt and not AI.search(title): continue
            if flt == "legal" and not LEGAL.search(title): continue
            out.append({"sezione": sec, "fonte": name, "titolo": title, "link": link}); n += 1
    final, count = [], {}
    for e in sorted(out, key=lambda e: ORDER.index(e["sezione"])):
        if count.get(e["sezione"], 0) < CAP[e["sezione"]] and len(final) < MAX_TOTAL:
            final.append(e); count[e["sezione"]] = count.get(e["sezione"], 0) + 1
    for e in final: seen[e["link"]] = NOW.date().isoformat()
    cutoff = (NOW - timedelta(days=30)).date().isoformat()
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    open("data/last_run.txt", "w").write(OGGI)
    json.dump(final, open("data/new.json", "w"), ensure_ascii=False, indent=1)
    json.dump(seen, open("data/seen.json", "w"), ensure_ascii=False, indent=1)
    print(f"{len(final)} novita. Fonti con errore: {len(errors)}")
    for e in errors: print(" -", e)

main()
