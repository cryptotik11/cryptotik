"""ترجمة عناوين الأخبار إلى العربية — مجاني بدون مفتاح (MyMemory) مع ذاكرة تخزين محلية
وقاموس مصطلحات كريبتو ثابت لرفع الجودة. يفشل بهدوء ويُبقي النص الأصلي.
"""
from __future__ import annotations
import json, re, time, urllib.parse
from pathlib import Path
import requests

CACHE_FILE = Path(__file__).parent.parent / "data" / "translation_cache.json"
_cache: dict[str, str] | None = None

# مصطلحات تُحمى من الترجمة ثم تعاد كما هي
KEEP = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ETF", "SEC", "DeFi", "TVL", "AI",
        "CZ", "Binance", "FTX", "Trump", "Musk", "Bitcoin", "Ethereum", "Solana", "Fed",
        "IPO", "NFT", "USDT", "USDC", "BlackRock", "Coinbase", "Uniswap", "Aave", "Lido"]

GLOSSARY = {
    "bitcoin": "البيتكوين", "ethereum": "الإيثريوم", "crypto": "الكريبتو",
    "tariffs": "الرسوم الجمركية", "tariff": "الرسوم الجمركية", "hack": "اختراق",
    "exploit": "استغلال ثغرة", "rate cut": "خفض الفائدة", "all-time high": "أعلى مستوى تاريخي",
}


def _load():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _cache = {}
    return _cache


def _save():
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def translate_to_ar(text: str, timeout: int = 12) -> str:
    """يترجم نصًا إنجليزيًا قصيرًا إلى العربية. عند الفشل يعيد الأصل."""
    text = (text or "").strip()
    if not text or re.search(r"[\u0600-\u06FF]", text):
        return text
    cache = _load()
    if text in cache:
        return cache[text]
    # حماية الرموز
    protected = {}
    for i, k in enumerate(KEEP):
        if re.search(rf"\b{re.escape(k)}\b", text):
            ph = f"XZ{i}Q"
            protected[ph] = k
            text = re.sub(rf"\b{re.escape(k)}\b", ph, text)
    try:
        url = "https://api.mymemory.translated.net/get"
        r = requests.get(url, params={"q": text[:450], "langpair": "en|ar"}, timeout=timeout)
        j = r.json()
        out = (j.get("responseData") or {}).get("translatedText") or ""
        out = out.strip()
        if not out or "MYMEMORY WARNING" in out.upper() or out.count("?") > 3:
            return _fallback(text)
        for ph, k in protected.items():
            out = out.replace(ph, k)
        # تنظيف بسيط
        out = re.sub(r"\s+([،.!؟])", r"\1", out)
        cache[text] = out
        _save()
        return out
    except Exception:
        return _fallback(text)


def _fallback(text: str) -> str:
    """ترجمة تقريبية بمطابقة مصطلحات — أفضل من لا شيء."""
    if re.search(r"[\u0600-\u06FF]", text):
        return text
    t = text
    for en, ar in GLOSSARY.items():
        t = re.sub(rf"\b{re.escape(en)}\b", ar, t, flags=re.I)
    # نُبقي بقية النص إنجليزيًا بدل مخرجات مشوّهة
    return t


def title_pair(title: str, max_len: int = 110) -> tuple[str, str]:
    """(عربي، إنجليزي) مع تقصير معقول."""
    en = re.sub(r"\s+", " ", title).strip()
    ar = translate_to_ar(en)
    if len(ar) > max_len:
        ar = ar[:max_len].rsplit(" ", 1)[0] + "…"
    return ar, en


if __name__ == "__main__":
    for t in ["The Netflix Crypto Series on FTX Provokes CZ and Vitalik Buterin",
              "Trump Rewards Top Owners of His Declining Coin With Exclusive Dinner",
              "Chainflip's losses climb to $12 million after protocol discloses 122.9 BTC theft"]:
        print(t, "\n  ↳", translate_to_ar(t), "\n")
