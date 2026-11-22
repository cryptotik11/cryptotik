"""رادار الأخبار: RSS + Google News (CZ / Musk / Trump) + تقييم أهمية الخبر 1-10."""
from __future__ import annotations
import html, re, time
from datetime import datetime, timezone, timedelta
import feedparser
from . import config

UA_HEADERS = {"User-Agent": "Mozilla/5.0 (cryptotik/1.0)"}


def _clean(txt: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", txt or "")
    txt = html.unescape(txt)
    return re.sub(r"\s+", " ", txt).strip()


def _age_hours(entry) -> float:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            dt = datetime(*t[:6], tzinfo=timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600)
    return 6.0


def _strip_source(title: str) -> str:
    # Google News يضيف " - اسم المصدر" في نهاية العنوان
    return re.sub(r"\s+-\s+[^-]{2,40}$", "", title or "").strip()


def score(title: str, source_weight: int, feed_weight: int, age_h: float, entity: str | None) -> float:
    """محرك التقييم: كلمات ساخنة + حداثة + وزن المصدر + شخصية مؤثرة."""
    t = (title or "").lower()
    pts = 0.0
    hits = []
    for kw, w in config.HOT_KEYWORDS.items():
        if kw in t:
            pts += w
            hits.append(kw)
    pts += source_weight + feed_weight
    # الحداثة: خبر عمره ساعة = +4، عمره 6 ساعات = 0
    pts += max(0.0, 4 - age_h * 0.7)
    if entity:
        pts += 1.5
    # عناوين قصيرة/غامضة تخسر نقطة
    if len(t) < 25:
        pts -= 1
    # عقوبة قِدَم صارمة — لا نعطي خبرًا عمره أيام أهمية عاجلة
    if age_h > 24:
        pts *= 0.55
    if age_h > 72:
        pts *= 0.45
    if age_h > 168:
        pts *= 0.4
    return round(min(10.0, pts * 0.75), 1), hits


def collect(max_items: int = 40) -> list[dict]:
    items: list[dict] = []
    # استبعاد الأخبار الأقدم من 48 ساعة — الرادار للحظي فقط
    MAX_AGE = 48.0
    for feed in config.NEWS_FEEDS:
        try:
            d = feedparser.parse(feed["url"], request_headers=UA_HEADERS)
            for e in d.entries[:15]:
                title = _clean(e.get("title", ""))
                if not title:
                    continue
                age = _age_hours(e)
                if age > MAX_AGE:
                    continue
                s, hits = score(title, feed["weight"], 0, age, None)
                items.append({
                    "title": title, "link": e.get("link", ""), "source": feed["name"],
                    "age_h": round(age, 1), "score": s, "keywords": hits,
                    "entity": None, "summary": _clean(e.get("summary", ""))[:500],
                })
        except Exception:
            continue
    for eq in config.ENTITY_QUERIES:
        try:
            url = config.GOOGLE_NEWS.format(q=eq["query"].replace(" ", "+"))
            d = feedparser.parse(url, request_headers=UA_HEADERS)
            for e in d.entries[:8]:
                title = _strip_source(_clean(e.get("title", "")))
                if not title:
                    continue
                age = _age_hours(e)
                if age > MAX_AGE:
                    continue
                s, hits = score(title, 2, eq["weight"], age, eq["entity"])
                items.append({
                    "title": title, "link": e.get("link", ""),
                    "source": f"Google News · {eq['entity']}",
                    "age_h": round(age, 1), "score": s, "keywords": hits,
                    "entity": eq["entity"], "summary": _clean(e.get("summary", ""))[:500],
                })
        except Exception:
            continue
    # إزالة التكرار بكلمات العنوان
    seen, uniq = set(), []
    for it in sorted(items, key=lambda x: x["score"], reverse=True):
        key = " ".join(sorted(set(re.findall(r"\w{4,}", it["title"].lower())))[:8])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    return uniq[:max_items]


if __name__ == "__main__":
    news = collect(15)
    for n in news[:15]:
        print(f"[{n['score']:>4}] {n['entity'] or n['source']:<18} {n['age_h']:>4}h  {n['title'][:110]}")


# ---------- اختيار صورة المشهد ----------
MEDIA_KEYWORDS = {
    "bitcoin": ["bitcoin", "btc"], "ethereum": ["ethereum", "eth", "vitalik"],
    "donald trump": ["trump", "tariff"], "elon musk": ["musk", "tesla", "dogecoin"],
    "defi" : ["defi", "uniswap", "aave", "liquidity", "tvl"],
    "hacker" : ["hack", "exploit", "security breach"],
    "courthouse" : ["sec", "regulation", "lawsuit", "court", "hearing"],
    "stock market" : ["market", "trading", "nasdaq", "s&p"],
}

COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def news_image(title: str, entity: str | None, out_dir) -> str | None:
    """يبحث عن صورة حرة (Wikimedia Commons) مناسبة للخبر ويحفظها محليًا.
    يعيد المسار أو None عند الفشل (الفيديو يُكمل بدون صورة)."""
    import requests
    from pathlib import Path
    t = ((title or "") + " " + (entity or "")).lower()
    topic = "bitcoin"
    for k, kws in MEDIA_KEYWORDS.items():
        if any(w in t for w in kws):
            topic = k
            break
    try:
        j = requests.get(COMMONS_API, params={
            "action": "query", "generator": "search", "gsrsearch": f"{topic} filetype:bitmap",
            "gsrlimit": 6, "gsrnamespace": 6, "prop": "imageinfo",
            "iiprop": "url|mime|extmetadata", "iiurlwidth": 1200, "format": "json",
        }, headers=UA_HEADERS, timeout=20).json()
        pages = (j.get("query") or {}).get("pages") or {}
        pages = sorted(pages.values(), key=lambda x: x.get("index", 99))
        out = Path(out_dir) / f"news_{topic.replace(' ', '_')}.jpg"
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]
            url = ii.get("thumburl") or ii.get("url")
            mime = ii.get("mime", "")
            if not url or "image" not in mime:
                continue
            r = requests.get(url, headers=UA_HEADERS, timeout=25)
            if r.status_code == 200 and len(r.content) > 25000:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(r.content)
                return str(out)
    except Exception:
        return None
    return None
