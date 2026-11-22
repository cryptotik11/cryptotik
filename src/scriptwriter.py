"""كاتب السكربت: يحوّل البيانات + أهم الأخبار إلى سكربت فيديو (عربي + إنجليزي)
قابل للتشغيل بدون أي API مدفوع. إن وُجد OPENAI_API_KEY يُستخدم لتحسين الصياغة (اختياري).
"""
from __future__ import annotations
import os, json, re
from .translate import title_pair
from . import config

# ---------- أدوات تنسيق ----------
def money(v) -> str:
    if v is None:
        return "—"
    a = abs(v)
    if a >= 1e12: return f"{v/1e12:.2f} تريليون"
    if a >= 1e9:  return f"{v/1e9:.1f} مليار"
    if a >= 1e6:  return f"{v/1e6:.0f} مليون"
    return f"{v:,.0f}"


def money_en(v) -> str:
    if v is None:
        return "—"
    a = abs(v)
    if a >= 1e12: return f"{v/1e12:.2f}T"
    if a >= 1e9:  return f"{v/1e9:.1f}B"
    if a >= 1e6:  return f"{v/1e6:.0f}M"
    return f"{v:,.0f}"


def price(v) -> str:
    if v is None: return "—"
    if v >= 1000: return f"{v:,.0f}"
    if v >= 10:   return f"{v:,.1f}"
    return f"{v:,.2f}"


def pct(v) -> str:
    if v is None: return "—"
    return f"{v:+.1f}%"


TERMS_AR = {
    "bitcoin":"البيتكوين","ethereum":"الإيثريوم","crypto":"الكريبتو","cryptocurrency":"العملات الرقمية",
    "hack":"اختراق","hacked":"تعرضت للاختراق","exploit":"استغلال ثغرة","surges":"يقفز","plunges":"يهوي",
    "plunge":"هبوط حاد","rally":"صعود","crash":"انهيار","etf":"صندوق ETF","sec":"هيئة الأوراق المالية",
    "trump":"ترامب","musk":"ماسك","cz":"تشانغبينغ تشاو","binance":"بينانس","tariffs":"الرسوم الجمركية",
    "tariff":"الرسوم الجمركية","lawsuit":"دعوى قضائية","whale":"حوت","liquidation":"تصفيات",
    "stablecoin":"عملة مستقرة","treasury":"الخزينة","approval":"موافقة","approve":"موافقة",
    "ban":"حظر","banned":"محظور","regulation":"تنظيم","fed":"الاحتياطي الفيدرالي","rate cut":"خفض الفائدة",
    "all-time high":"أعلى مستوى تاريخي","reserve":"احتياطي","investors":"المستثمرون","billion":"مليار",
    "million":"مليون","protocol":"بروتوكول","bridge":"جسر","tokenized":"مرمّز","dinner":"عشاء",
    "netflix":"نتفليكس","series":"مسلسل","provokes":"يثير","denies":"ينفي","bounty":"مكافأة",
    "halt":"إيقاف","suspected":"مشتبه","security":"أمن","quantum":"كمي","hearings":"جلسات استماع",
    "oversight":"رقابة","declining":"متراجعة","reward":"يكافئ","owners":"المالكين","token":"عملة",
}

def quick_ar_title(title: str, limit: int = 90) -> str:
    """ترجمة سريعة بدون API: تُبقي العنوان الأصلي مع أشهر المصطلحات مترجمة.
    عند توفر OPENAI_API_KEY في scriptwriter.polish_with_llm يتم تحسين الترجمة كاملة."""
    return title  # العناوين تبقى كما هي في الفيديو (قابلة للتحسين عبر LLM) — انظر build_title_pair


def trend_ar(v) -> str:
    if v is None: return "غير واضحة"
    if v >= 3:  return "قوية صاعدة"
    if v >= 0.5: return "إيجابية"
    if v > -0.5: return "مستقرة"
    if v > -3:  return "ضعيفة"
    return "سلبية حادة"


def trend_en(v) -> str:
    if v is None: return "unclear"
    if v >= 3:  return "strongly bullish"
    if v >= 0.5: return "bullish"
    if v > -0.5: return "flat"
    if v > -3: return "bearish"
    return "sharply bearish"


SCENES_AR = {
    "asia_open":   ("افتتاح آسيا — هذه بداية اليوم", "ASIA OPEN"),
    "europe_open": ("افتتاح أوروبا — السيولة تدخل", "EUROPE OPEN"),
    "us_open":     ("افتتاح أمريكا — الساعة الأهم", "US OPEN"),
    "daily_recap": ("ملخص اليوم — أين انتهى السوق؟", "DAILY RECAP"),
    "breaking":    ("خبر عاجل الآن", "BREAKING"),
    "token":       ("اليوم لا نراقب الأرقام فقط", "MARKET RADAR"),
}


def build(snap: dict, news: list[dict], kind: str = "us_open") -> dict:
    """يبني سكربت مقسّم لمشاهد. kind: asia_open | europe_open | us_open | daily_recap | breaking"""
    q = {x["symbol"]: x for x in snap["quotes"]}
    btc = q.get("BTC", {})
    g = snap.get("global", {})
    fng = snap.get("fng", {})
    defi = snap.get("defi", {})
    top_news = news[:3]

    hook_ar, label = SCENES_AR.get(kind, SCENES_AR["us_open"])
    btc_p, btc_c = price(btc.get("price")), btc.get("change24")

    # ---- النص العربي ----
    ar = []
    chg_ar = "مرتفع" if (btc_c or 0) >= 0 else "منخفض"
    chg_val = f"{abs(btc_c or 0):.1f} بالمئة"
    ar.append(f"{hook_ar}. البيتكوين عند {btc_p} دولار، {chg_ar} {chg_val} في ٢٤ ساعة.")
    if fng.get("value") is not None:
        ar.append(f"الخوف والجشع عند {fng['value']}، {fng['label_ar']}. "
                  f"السوق الكلية {trend_ar(g.get('mcap_change24'))} عند {money(g.get('mcap_usd'))} دولار.")
    top_news_ar = []
    for n in top_news:
        ar_t, en_t = title_pair(n["title"])
        top_news_ar.append(ar_t)
    if top_news:
        ar.append(f"الخبر الأهم: {top_news_ar[0]}")
    if defi.get("tvl_total"):
        line = f"سيولة الديفاي {money(defi['tvl_total'])} دولار."
        if defi.get("mover"):
            m = defi["mover"]
            line += f" وأكبر تحرك عند {m['name']}."
        ar.append(line)
    # ماذا يعني للسوق — يقرأ اتجاه BTC + معنويات الخوف/الجشع + اتجاه السوق الكلي
    fv = fng.get("value")
    mc = g.get("mcap_change24")
    if btc_c is None:
        reading = "الصورة غير مكتملة بعد، راقب السيولة قبل أي قرار."
    elif btc_c > 2 and (fv is None or fv >= 45):
        reading = "الزخم مع المشترين. ولكن راقب الفوليوم: صعود بلا سيولة = فخ محتمل."
    elif btc_c > 0 and fv is not None and fv < 25:
        reading = ("البيتكوين أخضر بلا حماس: الأسعار ترتفع والمشاعر خوف شديد. "
                   "هذا يعني أن هناك من يشتري في الخفاء، لكن هل تصمد السيولة؟")
    elif btc_c > -2 and (fv is None or fv >= 25):
        reading = "السوق متماسك. لا شيء يحسم الاتجاه بعد، والسيولة هي الحكم."
    elif btc_c > -2:
        reading = (f"ضغط بيعي خفيف مع خوف في السوق ({fng.get('label_ar')}). "
                   "راقب هل يتحول الهبوط إلى فرص شراء أم يستمر.")
    else:
        reading = ("الضغط البيعي قوي" + (f" والسوق في حالة {fng.get('label_ar')}" if fv is not None else "")
                   + ". لا تحاول التقاط السكين، السعر والسيولة هما الحكم.")
    if mc is not None and mc < -2 and btc_c > 0:
        reading += " والأهم: معظم السوق ينزف رغم ثبات البيتكوين — الألتكوينات هي الأكثر عرضة للخطر."
    ar.append(f"القراءة: {reading}")
    ar.append(f"تابع {config.BRAND['name_ar']} قبل كل افتتاح سوق. محتوى تعليمي وليس نصيحة مالية.")

    # ---- النص الإنجليزي ----
    en = []
    en.append(f"{label}: Bitcoin {price(btc.get('price'))} USD, {pct(btc_c)} in 24h.")
    if fng.get("value") is not None:
        en.append(f"Fear & Greed at {fng['value']} ({fng.get('label')}). "
                  f"Total market cap {money_en(g.get('mcap_usd'))}, {pct(g.get('mcap_change24'))}, "
                  f"trend {trend_en(g.get('mcap_change24'))}.")
    if top_news:
        en.append(f"Top story: {top_news[0]['title']}")
    if defi.get("tvl_total"):
        en.append(f"DeFi TVL {money_en(defi['tvl_total'])} USD ({pct(defi.get('tvl_change_pct'))} today).")
    # reading_en — نسخة إنجليزية من "ماذا يعني"
    if btc_c is None:
        reading_en = "The picture is incomplete. Watch liquidity before any decision."
    elif btc_c > 2 and (fv is None or fv >= 45):
        reading_en = "Momentum is with the buyers. But watch volume: a rally without liquidity is a possible trap."
    elif btc_c > 0 and fv is not None and fv < 25:
        reading_en = ("Bitcoin is green with no enthusiasm: prices rise while sentiment sits in extreme fear. "
                      "Someone is buying quietly. The question is whether liquidity holds.")
    elif btc_c > -2 and (fv is None or fv >= 25):
        reading_en = "The market holds. Nothing has decided direction yet, and liquidity is the judge."
    elif btc_c > -2:
        reading_en = ("Light selling pressure with fear in the market. Watch whether the dip turns into "
                      "an opportunity or keeps going.")
    else:
        reading_en = ("Selling pressure is strong. Do not try to catch a falling knife: price and liquidity decide.")
    en.append(f"The read: {reading_en}")
    en.append("Watch volume and liquidity — price alone is never the full story.")
    en.append("Educational content. Not financial advice.")

    # ---- المشاهد (30-55 ثانية) — حقول كاملة جاهزة للرسم ----
    price_txt = price(btc.get("price"))
    quotes_rich = []
    names_ar = {"BTC": "بيتكوين", "ETH": "إيثريوم", "SOL": "سولانا", "BNB": "بي إن بي"}
    names_en = {"BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "BNB": "BNB"}
    for x in snap["quotes"]:
        quotes_rich.append({"s": x["symbol"], "name_ar": names_ar.get(x["symbol"], ""),
                            "name_en": names_en.get(x["symbol"], x["symbol"]),
                            "p": price(x["price"]), "c": x["change24"], "spark": (x.get("spark") or [])[-24:]})
    mcap_txt = money(g.get("mcap_usd"))
    top_news = news[:3]

    import datetime as _dt
    _now = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=3)))
    _months = ["يناير","فبراير","مارس","أبريل","مايو","يونيو","يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]
    stamp = f"{_now.day} {_months[_now.month-1]} · {_now.strftime('%H:%M')}"
    fv_ = fng.get("value")
    mcap_lbl = "قيمة السوق"
    fng_lbl = "الخوف والجشع"
    hook_stats = [
        {"label": "قيمة السوق", "label_en": "Market cap",
         "value": f"${money_en(g.get('mcap_usd')).replace('T','T')}",
         "sub": f"{pct(g.get('mcap_change24'))} · 24h",
         "sub_color": config.BRAND["down"] if (g.get('mcap_change24') or 0) < 0 else config.BRAND["up"]},
    ]
    if fv_ is not None:
        fc = config.BRAND["down"] if fv_ < 30 else (config.BRAND["up"] if fv_ > 60 else config.BRAND["accent"])
        hook_stats.append({"label": "الخوف والجشع", "label_en": "Fear & Greed",
                           "value": str(fv_), "sub": fng.get("label_ar", ""),
                           "sub_en": fng.get("label", ""),
                           "color": fc, "sub_color": fc})

    scenes = [
        {"type": "hook", "label": label, "headline_ar": hook_ar, "headline_en": label,
         "narration_ar": ar[0], "narration_en": en[0], "stamp": stamp,
         "stamp_en": _now.strftime("%b %d · %H:%M"),
         "price_txt": price_txt, "btc_change": btc_c, "stats": hook_stats},
        {"type": "prices", "label": "PRICES · الأرقام",
         "narration_ar": (ar[1] if len(ar) > 1 else ""), "narration_en": (en[1] if len(en) > 1 else ""),
         "quotes_rich": quotes_rich, "mcap_txt": mcap_txt, "mcap_chg": g.get("mcap_change24"), "fng": fng},
        {"type": "news", "label": "TOP STORY · الخبر الأهم",
         "headline_ar": (top_news_ar[0] if top_news else "لا أخبار جوهرية الآن"),
         "headline_en": (top_news[0]["title"] if top_news else "No major news right now"),
         "narration_ar": (ar[2] if len(ar) > 2 else ""), "narration_en": (en[2] if len(en) > 2 else ""),
         "source": (top_news[0]["source"] if top_news else ""),
         "image_query": (top_news[0]["title"] if top_news else ""),
         "news": [{"t": t_ar, "t_en": n["title"], "src": n["source"]}
                  for t_ar, n in zip(top_news_ar[1:], top_news[1:])]},
    ]
    if defi.get("tvl_total"):
        scenes.append({"type": "defi", "label": "DEFI · LIQUIDITY",
                       "narration_ar": (ar[3] if len(ar) > 3 else ""), "narration_en": (en[3] if len(en) > 3 else ""),
                       "tvl_txt": money(defi["tvl_total"]), "mover": defi.get("mover"), "defi": defi})
    scenes.append({"type": "reading", "label": "THE READ · ماذا يعني؟",
                   "narration_ar": ar[-2], "narration_en": en[-2],
                   "read_ar": reading, "read_en": reading_en})
    scenes.append({"type": "outro", "label": "FOLLOW · تابعنا",
                   "narration_ar": ar[-1], "narration_en": en[-1]})

    script = {
        "kind": kind, "scenes": scenes,
        "narration_ar": "\n".join(ar), "narration_en": "\n".join(en),
        "sources": [{"title": n["title"], "link": n["link"], "source": n["source"], "score": n["score"]} for n in top_news],
        "data_snapshot": {"btc": btc.get("price"), "btc_change24": btc_c, "fng": fng.get("value"),
                          "mcap": g.get("mcap_usd"), "defi_tvl": defi.get("tvl_total")},
    }
    script = polish_with_llm(script) if os.getenv("OPENAI_API_KEY") else script
    return script


def polish_with_llm(script: dict) -> dict:
    """اختياري: تحسين الصياغة عبر OpenAI إن وُجد مفتاح. لا يفشل النظام إذا غاب."""
    try:
        import requests
        facts = json.dumps(script["data_snapshot"], ensure_ascii=False)
        headlines = "\n".join(f"- {s['title']}" for s in script["sources"])
        prompt = (
            "أنت محرر محتوى كريبتو لتيك توك. أعد صياغة السرد العربي التالي ليكون طبيعيًا ومختصرًا ومثيرًا، "
            "بدون مبالغة أو وعود. حافظ على كل الأرقام كما هي. أعد السرد فقط كسطر واحد لكل مشهد، بصيغة JSON: "
            '{"ar": ["...","..."], "en": ["...","..."]}\n\n'
            f"الأرقام: {facts}\nعناوين الأخبار:\n{headlines}\n\nالسرد الحالي (عربي):\n{script['narration_ar']}\n\n(إنجليزي):\n{script['narration_en']}"
        )
        r = requests.post("https://api.openai.com/v1/chat/completions",
                          headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                          json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.6}, timeout=60)
        txt = r.json()["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            data = json.loads(m.group(0))
            # توزيع السرد المحسّن على المشاهد
            for i, s in enumerate(script["scenes"]):
                if i < len(data.get("ar", [])):
                    s["narration_ar"] = data["ar"][i]
                if i < len(data.get("en", [])):
                    s["narration_en"] = data["en"][i]
            script["polished"] = True
    except Exception:
        script["polished"] = False
    return script


if __name__ == "__main__":
    from . import datafeed, newsradar
    snap = datafeed.snapshot()
    news = newsradar.collect(10)
    sc = build(snap, news, "us_open")
    print(sc["narration_ar"])
    print("----")
    print(sc["narration_en"])
