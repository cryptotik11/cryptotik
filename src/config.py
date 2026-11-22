"""إعدادات المشروع — AI Crypto TikTok
كل ما يمكن تعديله بدون لمس الكود موجود هنا.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
RENDERS = ROOT / "renders"
DATA = ROOT / "data"

# ---------- الهوية ----------
BRAND = {
    "handle": "@trade7717",              # حسابك على تيك توك
    "name_ar": "نبض الكريبتو",
    "name_en": "Crypto Pulse AI",
    "tagline_ar": "السوق باختصار… قبل الجميع",
    "tagline_en": "The market, before everyone else",
    "disclaimer_ar": "محتوى تعليمي وليس نصيحة مالية",
    "disclaimer_en": "Educational content, not financial advice",
    "accent": (34, 211, 238),      # سماوي
    "accent2": (168, 85, 247),     # بنفسجي
    "up": (34, 197, 94),
    "down": (239, 68, 68),
    "bg": (9, 12, 20),
    "bg2": (17, 24, 39),
    "text": (240, 246, 252),
    "muted": (148, 163, 184),
}

# ---------- العملات المتابعة ----------
COINS = [
    {"id": "bitcoin",     "symbol": "BTC", "binance": "BTCUSDT"},
    {"id": "ethereum",    "symbol": "ETH", "binance": "ETHUSDT"},
    {"id": "solana",      "symbol": "SOL", "binance": "SOLUSDT"},
    {"id": "binancecoin", "symbol": "BNB", "binance": "BNBUSDT"},
]

# ---------- مصادر الأخبار ----------
NEWS_FEEDS = [
    {"name": "CoinDesk",     "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "weight": 3},
    {"name": "Cointelegraph","url": "https://cointelegraph.com/rss",                    "weight": 2},
    {"name": "Decrypt",      "url": "https://decrypt.co/feed",                          "weight": 2},
    {"name": "The Block",    "url": "https://www.theblock.co/rss.xml",                  "weight": 3},
]

# بحث Google News عن الشخصيات المؤثرة
ENTITY_QUERIES = [
    {"entity": "CZ",    "query": 'CZ OR "Changpeng Zhao" binance crypto', "weight": 3},
    {"entity": "Musk",  "query": 'Elon Musk crypto OR dogecoin OR bitcoin', "weight": 3},
    {"entity": "Trump", "query": 'Trump crypto OR bitcoin OR "digital assets" OR tariff', "weight": 3},
]

GOOGLE_NEWS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

# كلمات ترفع أهمية الخبر
HOT_KEYWORDS = {
    "sec": 3, "etf": 3, "approval": 2, "approved": 2, "ban": 3, "hack": 4, "exploit": 4,
    "lawsuit": 3, "fed": 3, "rate cut": 4, "rate": 1, "tariff": 3, "reserve": 3,
    "whale": 2, "liquidation": 3, "all-time high": 3, "all time high": 3, "ath": 2,
    "crash": 3, "surge": 2, "plunge": 3, "rally": 2, "halving": 2, "stablecoin": 2,
    "blackrock": 3, "treasury": 3, "regulation": 2, "etf inflow": 4, "etf outflow": 4,
    "cz": 3, "musk": 3, "trump": 3, "tariffs": 3, "doge": 2, "dow": 1, "nasdaq": 2,
}

# ---------- أوقات النشر (بتوقيت اليمن UTC+3) ----------
SCHEDULE_YEMEN = {
    "asia_open":  "03:00",
    "europe_open": "11:00",
    "us_open":    "17:30",
    "daily_recap": "23:00",
}

# ---------- الفيديو ----------
VIDEO = {
    "w": 1080, "h": 1920, "fps": 30,
    "max_seconds": 55,
}

# ---------- الأصوات (edge-tts) ----------
VOICES = {
    "ar": "ar-SA-HamedNeural",     # بديل: ar-EG-ShakirNeural / ar-SA-ZariyahNeural (أنثى)
    "en": "en-US-ChristopherNeural",
    "ar_rate": "+14%",
    "en_rate": "+12%",
}

# ---------- الهاشتاجات والإفصاح ----------
# إفصاح إلزامي: تيك توك يطلب وسم المحتوى المولّد بالذكاء الاصطناعي
AI_DISCLOSURE_AR = "محتوى مولّد بالذكاء الاصطناعي · تعليمي وليس نصيحة مالية"
AI_DISCLOSURE_EN = "AI-generated content · Educational, not financial advice"

HASHTAGS_AR = "#كريبتو #بيتكوين #العملات_الرقمية #تحليل_السوق #تيك_توك_مالي #AI"
HASHTAGS_EN = "#crypto #bitcoin #btc #cryptonews #marketupdate #tiktokfinance #AI"
