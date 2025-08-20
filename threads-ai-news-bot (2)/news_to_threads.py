# news_to_threads.py
import os, textwrap, datetime as dt
import feedparser
from urllib.parse import urlparse, urlsplit, urlunsplit, parse_qsl, urlencode

MSK = dt.timezone(dt.timedelta(hours=3))

FEEDS = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/news/rss.xml",
    "https://ai.googleblog.com/feeds/posts/default",
    "https://ai.meta.com/blog/rss/",
    "https://blogs.microsoft.com/ai/feed/",
    "https://techcrunch.com/tag/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://huggingface.co/blog/feed.xml",
]

MAX_POINT_LEN = 650
POINTS_MIN, POINTS_MAX = 6, 8

def _now_msk():
    return dt.datetime.now(MSK)

def _cutoff_utc(hours=24):
    return dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)

def _add_utm(link: str) -> str:
    try:
        parts = urlsplit(link)
        q = dict(parse_qsl(parts.query, keep_blank_values=True))
        q.setdefault("utm_source", "threads")
        q.setdefault("utm_medium", "social")
        q.setdefault("utm_campaign", "ai-daily")
        new_query = urlencode(q, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
    except Exception:
        return link

def pick_items():
    cutoff = _cutoff_utc(24)
    items = []
    for url in FEEDS:
        d = feedparser.parse(url)
        for e in d.entries[:10]:
            t = None
            for key in ("published_parsed","updated_parsed","created_parsed"):
                if getattr(e, key, None):
                    t = dt.datetime(*getattr(e,key)[:6], tzinfo=dt.timezone.utc)
                    break
            if not t or t < cutoff:
                continue
            title = (getattr(e, "title", "") or "").strip()
            link = (getattr(e, "link", "") or "").strip()
            if not title or not link:
                continue
            items.append({
                "title": title,
                "link": _add_utm(link),
                "source": urlparse(url).netloc.replace("www.",""),
                "time": t,
            })
    items.sort(key=lambda x: (-x["time"].timestamp(), x["source"], x["title"]))
    seen = set(); uniq = []
    for it in items:
        key = (it["title"].lower(), it["link"])
        if key in seen: continue
        seen.add(key); uniq.append(it)
    return uniq[:12]

def format_point(it):
    text = f"{it['title']} | Источник: {it['source']} | Ссылка: {it['link']}"
    if len(text) > MAX_POINT_LEN:
        text = text[:MAX_POINT_LEN-1] + "…"
    return text

def build_thread():
    now_msk = _now_msk()
    header = f"Обновлено: {now_msk:%H:%M} МСК, {now_msk:%d.%m.%Y}"
    items = pick_items()
    points = [format_point(it) for it in items][:POINTS_MAX]
    if len(points) < POINTS_MIN:
        points += ["Сегодня мало новостей с бизнес-углом."]
        points = points[:POINTS_MIN]
    body = [f"{i+1}. {p}" for i, p in enumerate(points)]
    footer = "Итог: следим за релизами и внедрениями. #AI #бизнес #операции #генеративныйИИ #LLM"
    return [header] + body + [footer]

if __name__ == "__main__":
    parts = build_thread()
    for part in parts:
        print(part)
        print("---")
