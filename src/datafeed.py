"""جالب بيانات السوق — ثلاث طبقات احتياطية حتى لا يتعطل النشر أبدًا:
1) CoinMarketCap (الواجهة العامة — نفس مصدر خطتك)
2) Binance vision (أسعار لحظية)
3) CoinGecko (احتياطي أخير)
+ DefiLlama لبيانات السيولة، + مؤشر الخوف والجشع.
"""
from __future__ import annotations
import json, time
import requests
from . import config

UA = {"User-Agent": "Mozilla/5.0 (compatible; CryptoPulseAI/1.0)"}
TIMEOUT = 20
CMC_LIST = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing"
CMC_GLOBAL = "https://api.coinmarketcap.com/data-api/v3/global-metrics/quotes/latest"


def _get_json(url, params=None, retries=2):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 418):
                time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


# ---------- المصدر 1: CoinMarketCap ----------
def _cmc_coins() -> dict[str, dict]:
    """{SYMBOL: {price, change24, mcap, dominance}} لأول 200 عملة."""
    # جلب صفحات متعددة لضمان وجود عملاتنا
    out: dict[str, dict] = {}
    for start in (1, 101):
        j = _get_json(CMC_LIST, {"start": start, "limit": 100, "sortBy": "market_cap",
                                 "sortType": "desc", "convert": "USD"})
        if not j:
            continue
        for c in (j.get("data") or {}).get("cryptoCurrencyList") or []:
            q = (c.get("quotes") or [{}])[0]
            out[c.get("symbol", "")] = {
                "price": q.get("price"), "change24": q.get("percentChange24h"),
                "mcap": q.get("marketCap"), "dominance": q.get("dominance"),
                "name": c.get("name"),
            }
    return out


def _cmc_global() -> dict:
    j = _get_json(CMC_GLOBAL)
    if not j:
        return {}
    d = (j.get("data") or {})
    qs = d.get("quotes") or []
    q = qs[0] if isinstance(qs, list) and qs else (qs if isinstance(qs, dict) else {})
    tmc = q.get("totalMarketCap")
    tmc_y = q.get("totalMarketCapYesterday")
    chg = None
    if tmc and tmc_y:
        chg = (tmc - tmc_y) / tmc_y * 100
    return {
        "mcap_usd": tmc, "mcap_change24": chg,
        "btc_dominance": d.get("btcDominance"), "eth_dominance": d.get("ethDominance"),
        "volume_usd": q.get("totalVolume24H"),
        "defi_mcap": q.get("defiMarketCap"), "defi_chg": q.get("defi24HPercentageChange"),
        "stablecoin_mcap": q.get("stablecoinMarketCap"),
    }


# ---------- المصدر 2: Binance ----------
def _binance_ticker(symbol: str) -> dict | None:
    t = _get_json(f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={symbol}")
    if isinstance(t, dict) and "lastPrice" in t:
        try:
            return {"price": float(t["lastPrice"]), "change24": float(t["priceChangePercent"])}
        except Exception:
            return None
    return None


def _binance_klines(symbol: str, limit=24) -> list[float]:
    k = _get_json(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=1h&limit={limit}")
    if isinstance(k, list):
        try:
            return [float(row[4]) for row in k]
        except Exception:
            return []
    return []


# ---------- المصدر 3: CoinGecko ----------
def _cg_simple() -> dict:
    j = _get_json("https://api.coingecko.com/api/v3/simple/price",
                  {"ids": ",".join(c["id"] for c in config.COINS), "vs_currencies": "usd",
                   "include_24hr_change": "true"})
    return j if isinstance(j, dict) else {}


# ---------- الواجهة العامة ----------
def quotes() -> list[dict]:
    cmc = _cmc_coins()
    cg = _cg_simple() if not cmc else {}
    out = []
    for c in config.COINS:
        q = {"symbol": c["symbol"], "name": c.get("name", c["symbol"]), "price": None,
             "change24": None, "spark": []}
        m = cmc.get(c["symbol"])
        if m and m.get("price"):
            q["price"], q["change24"] = m["price"], m["change24"]
        else:
            b = _binance_ticker(c["binance"])
            if b:
                q["price"], q["change24"] = b["price"], b["change24"]
            elif c["id"] in cg:
                q["price"] = cg[c["id"]].get("usd")
                q["change24"] = cg[c["id"]].get("usd_24h_change")
        q["spark"] = _binance_klines(c["binance"])
        out.append(q)
    return out


def global_market() -> dict:
    g = _cmc_global()
    if not g.get("mcap_usd"):
        cgj = _get_json("https://api.coingecko.com/api/v3/global") or {}
        d = cgj.get("data", {})
        g = {
            "mcap_usd": d.get("total_market_cap", {}).get("usd"),
            "mcap_change24": d.get("market_cap_change_percentage_24h_usd"),
            "btc_dominance": d.get("market_cap_percentage", {}).get("btc"),
            "eth_dominance": d.get("market_cap_percentage", {}).get("eth"),
            "volume_usd": d.get("total_volume", {}).get("usd"),
        }
    return g


def fear_greed() -> dict:
    f = _get_json("https://api.alternative.me/fng/?limit=2") or {}
    data = f.get("data", [])
    if not data:
        return {"value": None, "label": None, "label_ar": None, "prev": None}
    cur = data[0]
    prev = data[1]["value"] if len(data) > 1 else None
    labels_ar = {"Extreme Fear": "خوف شديد", "Fear": "خوف", "Neutral": "محايد",
                 "Greed": "جشع", "Extreme Greed": "جشع شديد"}
    return {"value": int(cur["value"]), "label": cur["value_classification"],
            "label_ar": labels_ar.get(cur["value_classification"], cur["value_classification"]),
            "prev": int(prev) if prev else None}


def defi() -> dict:
    """DefiLlama — TVL + أكبر البروتوكولات + أكبر تحرك."""
    res = {"tvl_total": None, "tvl_change_pct": None, "top": [], "mover": None}
    total = _get_json("https://api.llama.fi/charts")
    if isinstance(total, list) and len(total) > 1:
        try:
            key = "totalLiquidityUSD" if "totalLiquidityUSD" in total[-1] else "tvl"
            cur, prev = float(total[-1][key]), float(total[-2][key])
            res["tvl_total"] = cur
            res["tvl_change_pct"] = (cur - prev) / prev * 100 if prev else None
        except Exception:
            pass
    p = _get_json("https://api.llama.fi/protocols")
    if isinstance(p, list):
        rows = [x for x in p if x.get("category") != "CEX" and (x.get("tvl") or 0) > 0]
        rows.sort(key=lambda x: x["tvl"], reverse=True)
        for x in rows[:5]:
            res["top"].append({"name": x.get("name"), "tvl": x.get("tvl"),
                               "change24": x.get("change_1d")})
        movers = [x for x in rows[:40] if x.get("change_1d") is not None]
        movers.sort(key=lambda x: abs(x["change_1d"]), reverse=True)
        if movers:
            m = movers[0]
            res["mover"] = {"name": m["name"], "change24": m["change_1d"], "tvl": m.get("tvl")}
    return res


def snapshot() -> dict:
    return {"quotes": quotes(), "global": global_market(), "fng": fear_greed(), "defi": defi(),
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=2, ensure_ascii=False)[:4000])
