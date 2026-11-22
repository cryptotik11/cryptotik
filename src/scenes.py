"""مولّد مشاهد الفيديو 9:16 — نسخة نهائية.
Pillow + raqm (تشكيل عربي أصلي) + محرك توزيع مرن (flex) يملأ الشاشة الرأسية بلا فراغات.
"""
from __future__ import annotations
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from . import config

W, H = config.VIDEO["w"], config.VIDEO["h"]
B = config.BRAND
SAFE_R = 84
TOP = 208
BOTTOM = 1700

# ---------------- اللغة (لغة واجهة المشاهد) ----------------
LANG = "ar"          # يبدّلها videobuild.render حسب اللغة
TXT = {}             # نصوص مخصّصة من السكربت (تُمرر اختياريًا)


def set_lang(lang: str, extra: dict | None = None):
    global LANG, TXT
    LANG = "en" if str(lang).startswith("en") else "ar"
    TXT = extra or {}


def is_en() -> bool:
    return LANG == "en"


def t_(ar: str, en: str) -> str:
    return en if is_en() else ar


def _align() -> str:
    return "left" if is_en() else "right"


_UNITS_EN = [("تريليون", "T"), ("مليار", "B"), ("مليون", "M")]


def _en_amount(txt: str) -> str:
    """يحوّل مبلغًا عربيًا منسّقًا (2.07 تريليون) إلى الصيغة الإنجليزية (2.07T)."""
    t = str(txt)
    for ar, en in _UNITS_EN:
        if ar in t:
            return t.replace(ar, "").strip().replace(",", "") + en
    return t

_FONTS: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
FONT_FILES = {
    "black": config.FONTS / "Cairo-ExtraBold.ttf",
    "bold":  config.FONTS / "Tajawal-Bold.ttf",
    "reg":   config.FONTS / "Tajawal-Regular.ttf",
    "naskh": config.FONTS / "NotoNaskhArabic-Bold.ttf",
}


# ---------------- أساسيات ----------------
def font(style: str, size: int) -> ImageFont.FreeTypeFont:
    key = (style, size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(str(FONT_FILES.get(style, FONT_FILES["bold"])), size)
    return _FONTS[key]


def has_arabic(t: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" for ch in str(t))


def kw(text: str) -> dict:
    return {"direction": "rtl", "language": "ar"} if has_arabic(text) else {}


def tlen(d, t, f) -> float:
    return d.textlength(str(t), font=f, **kw(t))


def draw_number(d, right_x: float, y: float, text: str, f, fill, raise_frac: float = 0.16):
    """يرسم رقمًا مع رفع الفواصل , و. (خط Cairo يضعها منخفضة جدًا). محاذاة يمين."""
    chars = list(str(text))
    # قياس العرض الكلي
    total = d.textlength("".join(chars), font=f)
    x = right_x - total
    for ch in chars:
        if ch == ",":
            d.text((x, y - f.size * raise_frac), ch, font=f, fill=fill)
        else:
            d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f)
    return total


NO_LINE_START = set("،؛؟!.,:%)]»…")


def wrap(d, text, f, max_w) -> list[str]:
    lines = []
    for para in str(text).split("\n"):
        words, cur = para.split(), ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if tlen(d, trial, f) <= max_w or not cur:
                cur = trial
            else:
                if w_ and w_[0] in NO_LINE_START:
                    cur = (cur + " " + w_).strip()
                else:
                    lines.append(cur); cur = w_
        if cur:
            lines.append(cur)
    return lines or [""]


def block_height(d, text, max_w, f, gap=14) -> int:
    return len(wrap(d, text, f, max_w)) * (f.size + gap)


def draw_block(d, text, xy, max_w, f, fill=B["text"], gap=14, align="right") -> int:
    x, y = xy
    total = 0
    for line in wrap(d, text, f, max_w):
        w = tlen(d, line, f)
        px = x + (max_w - w) if align == "right" else (x + (max_w - w) / 2 if align == "center" else x)
        d.text((px, y + total), line, font=f, fill=fill, **kw(line))
        total += f.size + gap
    return total


# ---------------- خلفية ----------------
def _gradient(w=W, h=H, top=(8, 11, 18), bottom=(26, 35, 52)) -> Image.Image:
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        img.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img.resize((w, h))


def _orb(base, center, radius, color, alpha=60):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius // 3))
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def background(seed: int = 0) -> Image.Image:
    rnd = random.Random(seed)
    img = _gradient()
    img = _orb(img, (rnd.randint(80, 1000), rnd.randint(120, 520)), rnd.randint(230, 350), B["accent"], 46)
    img = _orb(img, (rnd.randint(80, 1000), rnd.randint(1350, 1850)), rnd.randint(260, 420), B["accent2"], 40)
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W, 90):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 5), width=1)
    for y in range(0, H, 90):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 5), width=1)
    return img


# ---------------- إطار وترويسة ----------------
def header(img, label: str):
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([48, 54, W-48, 158], radius=26, fill=(255, 255, 255, 12),
                        outline=B["accent"] + (120,), width=3)
    d.ellipse([84, 94, 110, 120], fill=B["down"])
    _lab = config.BRAND["name_en"] if is_en() else label
    d.text((134, 106), _lab, font=font("bold", 40), fill=B["text"], anchor="lm", **kw(_lab))
    d.text((W-84, 106), config.BRAND["name_ar"] if is_en() else config.BRAND["name_en"],
           font=font("bold", 30), fill=B["muted"], anchor="rm", **kw(config.BRAND["name_ar"]))


def footer(img, page: int, total: int):
    d = ImageDraw.Draw(img, "RGBA")
    y = H - 78
    bar_w = W - 240
    d.rounded_rectangle([120, y, 120 + bar_w, y + 8], radius=4, fill=(255, 255, 255, 26))
    d.rounded_rectangle([120, y, 120 + int(bar_w * max(0.04, page / max(1, total))), y + 8],
                        radius=4, fill=B["accent"] + (255,))
    t = (config.BRAND["name_en"] if is_en() else config.BRAND["name_ar"]) + "  ·  " + config.BRAND["handle"]
    d.text((W//2, y + 46), t, font=font("reg", 25), fill=B["muted"], anchor="mm", **kw(t))


# ---------------- محرك التوزيع ----------------
def new_layer() -> Image.Image:
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _block(fn) -> Image.Image:
    L = new_layer()
    fn(ImageDraw.Draw(L, "RGBA"))
    return L


def flex_compose(img, layers, top=TOP, bottom=BOTTOM, base_gap=28, max_gap=120):
    items = []
    for L in layers:
        bb = L.getbbox()
        if not bb:
            continue
        crop = L.crop(bb)
        crop._x = bb[0]
        items.append(crop)
    if not items:
        return img
    n = len(items)
    total = sum(im.height for im in items)
    gap = base_gap
    if n > 1:
        gap = max(base_gap, min(max_gap, (bottom - top - total) / (n - 1)))
    used = total + gap * (n - 1)
    y = top + max(0, (bottom - top - used) // 2)
    out = img.convert("RGBA")
    for im in items:
        out.alpha_composite(im, (getattr(im, "_x", 0), int(y)))
        y += im.height + gap
    return out.convert("RGB")


# ---------------- عناصر ----------------
def pill_right(d, right_x, y, text, f, fg, bg, outline=None, px=24, py=12):
    w = tlen(d, text, f) + px * 2
    h = f.size + py * 2
    d.rounded_rectangle([right_x - w, y, right_x, y + h], radius=h // 2, fill=bg, outline=outline, width=2)
    d.text((right_x - w/2, y + h/2 + 1), text, font=f, fill=fg, anchor="mm", **kw(text))
    return w, h


def tri(d, cx, cy, size, up: bool, color):
    s = size
    pts = ([(cx, cy - s), (cx - s*0.85, cy + s*0.7), (cx + s*0.85, cy + s*0.7)] if up
           else [(cx, cy + s), (cx - s*0.85, cy - s*0.7), (cx + s*0.85, cy - s*0.7)])
    d.polygon(pts, fill=color)


def change_row(d, right_x, y, value, f, suffix=""):
    col = B["muted"] if value is None else (B["up"] if value >= 0 else B["down"])
    txt = f"{abs(value or 0):.2f}%{suffix}"
    w = tlen(d, txt, f)
    d.text((right_x, y), txt, font=f, fill=col, anchor="ra")
    if value is not None:
        tri(d, right_x - w - 24, y + f.size * 0.55, f.size * 0.3, value >= 0, col)


def spark(d, box, prices, color):
    if len(prices) < 2:
        return
    x0, y0, x1, y1 = box
    lo, hi = min(prices), max(prices)
    rng = (hi - lo) or 1
    pts = [(x0 + (x1 - x0) * i / (len(prices) - 1), y1 - (y1 - y0) * (p - lo) / rng)
           for i, p in enumerate(prices)]
    d.line(pts, fill=color, width=5, joint="curve")
    d.ellipse([pts[-1][0]-8, pts[-1][1]-8, pts[-1][0]+8, pts[-1][1]+8], fill=color)


def draw_amount_ar(d, right_x, y, number: str, unit: str = "", f_num=None, f_unit=None,
                   fill=B["text"], unit_fill=None):
    """يرسم رقمًا لاتينيًا ثم وحدة عربية على يمينه (تجنّب خلط الاتجاه).
    المحاذاة لليمين عند right_x. مثال: right_x=956 ← [٢.٠٧ تريليون][$]"""
    f_num = f_num or font("black", 60)
    f_unit = f_unit or font("bold", 34)
    unit_fill = unit_fill or fill
    x = right_x
    # الوحدة العربية أولًا (أقصى اليمين)
    if unit:
        d.text((x, y + f_num.size - f_unit.size - 6), unit, font=f_unit, fill=unit_fill, anchor="ra",
               **kw(unit))
        x -= tlen(d, unit, f_unit) + 14
    draw_number(d, x, y, number, f_num, fill)


def section_title(d, text, y=0, size=62) -> int:
    d.text((W - SAFE_R, y), text, font=font("black", size), fill=B["text"], anchor="ra", **kw(text))
    return y + size + 40


# ---------------- 1) الهوك ----------------
def scene_hook(info, kicker, price_txt, change, sub=None, stats=None, stamp=None):
    img = background(1)
    header(img, info.get("label", "MARKET UPDATE"))
    layers = []

    stamp = stamp if stamp is not None else info.get("stamp", "")
    if stamp:
        layers.append(_block(lambda d: pill_right(
            d, W - SAFE_R, 6, stamp, font("bold", 32), B["accent"], (255, 255, 255, 16),
            outline=B["accent"] + (110,))))

    def draw_kicker(d):
        f_kick = font("black", 88)
        while block_height(d, kicker, W - SAFE_R*2, f_kick, 26) > 400 and f_kick.size > 62:
            f_kick = font("black", f_kick.size - 4)
        y = draw_block(d, kicker, (SAFE_R, 0), W - SAFE_R*2, f_kick, B["text"], 26, _align())
        if sub:
            y += 22
            draw_block(d, sub, (SAFE_R, y), W - SAFE_R*2, font("reg", 40), B["muted"], 10, "right")
    layers.append(_block(draw_kicker))

    def draw_price(d):
        hgt = 300
        d.rounded_rectangle([SAFE_R, 0, W-SAFE_R, hgt], radius=38, fill=(255, 255, 255, 16),
                            outline=B["accent"] + (150,), width=3)
        d.text((W-124, 34), "BTC / USD", font=font("bold", 32), fill=B["muted"], anchor="ra")
        draw_number(d, W - 124, 82, f"${price_txt}", font("black", 108), B["text"])
        d.rounded_rectangle([124, hgt-80, W-124, hgt-26], radius=14, fill=(255, 255, 255, 12))
        change_row(d, W - 152, hgt - 76, change, font("black", 36), " · 24h")
    layers.append(_block(draw_price))

    if stats:
        def draw_stats(d):
            gap = 24
            cw = (W - SAFE_R*2 - gap) // 2
            for i, st in enumerate(stats[:2]):
                cx0 = SAFE_R + i * (cw + gap)
                d.rounded_rectangle([cx0, 0, cx0 + cw, 200], radius=26, fill=(255, 255, 255, 12))
                _sl = st.get("label_en", st["label"]) if is_en() else st["label"]
                d.text((cx0 + cw//2, 28), _sl, font=font("bold", 27), fill=B["muted"],
                       anchor="ma", **kw(_sl))
                _vc = st.get("color") or B["text"]
                _vc = tuple(_vc) if isinstance(_vc, (list, tuple)) else _vc
                d.text((cx0 + cw//2, 76), st["value"], font=font("black", 44),
                       fill=_vc, anchor="ma", **kw(st["value"]))
                _ss = (st.get("sub_en") or st.get("sub")) if is_en() else st.get("sub")
                _sc = st.get("sub_color") or st.get("color") or B["muted"]
                _sc = tuple(_sc) if isinstance(_sc, (list, tuple)) else _sc
                if _ss:
                    d.text((cx0 + cw//2, 140), _ss, font=font("bold", 25),
                           fill=_sc, anchor="ma", **kw(_ss))
        layers.append(_block(draw_stats))

    img = flex_compose(img, layers, base_gap=36, max_gap=110)
    footer(img, 1, info.get("total", 6))
    return img


# ---------------- 2) الأرقام ----------------
def scene_market(info, quotes, mcap_txt, mcap_chg, fng):
    img = background(2)
    header(img, info.get("label", "PRICES"))
    _st = t_("أين الأرقام الآن؟", "Where prices stand now")
    layers = [_block(lambda d: section_title(d, _st, 0, 62))]

    for q in quotes[:4]:
        def draw_row(d, q=q):
            row_h = 156
            d.rounded_rectangle([SAFE_R, 0, W-SAFE_R, row_h], radius=26, fill=(255, 255, 255, 12))
            d.text((W-124, 22), q["s"], font=font("black", 50), fill=B["text"], anchor="ra")
            nm = q.get("name_en", "") if is_en() else q.get("name_ar", "")
            d.text((W-124, 92), nm, font=font("reg", 28), fill=B["muted"], anchor="ra", **kw(nm))
            col = B["muted"] if q.get("c") is None else (B["up"] if q["c"] >= 0 else B["down"])
            spark(d, (450, 40, 660, 116), q.get("spark") or [], col)
            draw_number(d, 124 + tlen(d, f"${q['p']}", font("black", 48)), 18, f"${q['p']}",
                        font("black", 48), B["text"])
            pct_txt = f"{abs(q.get('c') or 0):.2f}%"
            d.text((124, 90), pct_txt, font=font("bold", 30), fill=col, anchor="la")
            if q.get("c") is not None:
                tri(d, 124 + tlen(d, pct_txt, font("bold", 30)) + 20, 90 + 16, 10, q["c"] >= 0, col)
        layers.append(_block(draw_row))

    # بطاقة السوق الكلية
    def draw_mcap(d):
        hgt = 190
        d.rounded_rectangle([SAFE_R, 0, W-SAFE_R, hgt], radius=30, fill=(255, 255, 255, 12),
                            outline=B["accent2"] + (140,), width=3)
        lbl = t_("قيمة السوق الكلية", "Total market cap")
        d.text((W-124, 26), lbl, font=font("bold", 30), fill=B["muted"], anchor="ra", **kw(lbl))
        if is_en():
            d.text((W-124, 70), f"${_en_amount(mcap_txt)}", font=font("black", 58),
                   fill=B["text"], anchor="ra")
        else:
            d.text((W-124, 70), f"${mcap_txt}", font=font("black", 58), fill=B["text"], anchor="ra")
        col_m = B["muted"] if mcap_chg is None else (B["up"] if mcap_chg >= 0 else B["down"])
        txt = f"{abs(mcap_chg or 0):.1f}% · 24h"
        d.text((W - 124 - tlen(d, lbl, font("bold", 30)) - 26, 26), txt,
               font=font("bold", 27), fill=col_m, anchor="ra")
        if mcap_chg is not None:
            tri(d, W - 124 - tlen(d, lbl, font("bold", 30)) - 26 - tlen(d, txt, font("bold", 27)) - 20,
                42, 9, mcap_chg >= 0, col_m)
    layers.append(_block(draw_mcap))

    # بطاقة الخوف والجشع
    if fng.get("value") is not None:
        def draw_fng(d):
            hgt = 150
            d.rounded_rectangle([SAFE_R, 0, W-SAFE_R, hgt], radius=30, fill=(255, 255, 255, 10))
            fv = fng["value"]
            fc = B["down"] if fv < 30 else (B["up"] if fv > 60 else B["accent"])
            flbl = t_("مؤشر الخوف والجشع", "Fear & Greed")
            d.text((W-124, 22), flbl, font=font("bold", 28), fill=B["muted"],
                   anchor="ra", **kw(flbl))
            lab = fng.get("label", "") if is_en() else fng.get("label_ar", "")
            d.text((W-124, 72), lab, font=font("black", 46), fill=fc, anchor="ra", **kw(lab))
            d.text((124, 62), f"{fv}", font=font("black", 56), fill=fc, anchor="lm")
        layers.append(_block(draw_fng))

    img = flex_compose(img, layers, base_gap=18, max_gap=52)
    footer(img, info.get("page", 2), info.get("total", 6))
    return img


# ---------------- 3) الخبر ----------------
def scene_news(info, headline, source, extra=None, image_path=None):
    img = background(3)
    header(img, t_("TOP STORY · الخبر الأهم", "TOP STORY"))
    _brk = t_("عاجل", "BREAKING")
    layers = [_block(lambda d: pill_right(d, W - 108, 0, _brk, font("bold", 34), (255, 255, 255),
                                          B["down"] + (235,)))]
    if image_path:
        try:
            tw = W - 128
            th = int(tw * 9 / 16)
            im_ = Image.open(image_path).convert("RGB").resize((tw, th))
            dark = Image.new("RGB", (tw, th), (8, 11, 18))
            im_ = Image.blend(im_, dark, 0.28)
            Limg = new_layer()
            mask = Image.new("L", (tw, th), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw, th], radius=30, fill=255)
            Limg.paste(im_, (64, 0), mask)
            ImageDraw.Draw(Limg, "RGBA").rounded_rectangle([64, 0, 64 + tw, th], radius=30,
                                                          outline=B["accent"] + (120,), width=3)
            layers.append(Limg)
        except Exception:
            pass

    def draw_card(d):
        f_head = font("bold", 56)
        th = block_height(d, headline, W - 240, f_head, 18)
        card_h = max(300, th + 190)
        d.rounded_rectangle([64, 0, W-64, card_h], radius=36, fill=(255, 255, 255, 13),
                            outline=B["down"] + (150,), width=3)
        draw_block(d, headline, (108, 56), W - 240, f_head, B["text"], 18, _align())
        if source:
            pill_right(d, W - 100, card_h - 92, source, font("reg", 27), B["text"],
                       (255, 255, 255, 24), outline=B["accent"] + (110,))
    layers.append(_block(draw_card))

    if extra:
        def draw_extra(d):
            y = 0
            _also = t_("أيضًا على الرادار", "Also on the radar")
            d.text((W-SAFE_R, y), _also, font=font("bold", 38), fill=B["muted"],
                   anchor="ra", **kw(_also))
            y += 74
            for n in extra[:2]:
                f_sub = font("reg", 32)
                _nt = (n.get("t_en") or n["t"]) if is_en() else n["t"]
                _nt = _nt[:130]
                th2 = block_height(d, _nt, W - 260, f_sub, 8)
                hh = max(th2 + 52, 118)
                d.rounded_rectangle([SAFE_R, y, W-SAFE_R, y + hh], radius=22, fill=(255, 255, 255, 10))
                d.rounded_rectangle([W-SAFE_R-8, y+18, W-SAFE_R-2, y+hh-18], radius=3,
                                    fill=B["accent"] + (200,))
                draw_block(d, _nt, (SAFE_R + 34, y + 26), W - 260, f_sub, B["text"], 8, _align())
                y += hh + 22
        layers.append(_block(draw_extra))

    img = flex_compose(img, layers, base_gap=44, max_gap=110)
    footer(img, info.get("page", 3), info.get("total", 6))
    return img


# ---------------- 4) ديفاي ----------------
def scene_defi(info, tvl_txt, tvl_chg, mover, top):
    img = background(4)
    header(img, "DEFI · LIQUIDITY")
    _dt = t_("أين تتحرك السيولة؟", "Where liquidity is moving")
    layers = [_block(lambda d: section_title(d, _dt, 0, 62))]

    def draw_tvl(d):
        hgt = 260
        d.rounded_rectangle([SAFE_R, 0, W-SAFE_R, hgt], radius=32, fill=(255, 255, 255, 13),
                            outline=B["accent"] + (150,), width=3)
        tlbl = t_("إجمالي سيولة الديفاي (TVL)", "DeFi total liquidity (TVL)")
        d.text((W-124, 32), tlbl, font=font("bold", 30), fill=B["muted"],
               anchor="ra", **kw(tlbl))
        if is_en():
            d.text((W-124, 82), f"${_en_amount(tvl_txt)}", font=font("black", 82),
                   fill=B["text"], anchor="ra")
        else:
            d.text((W-124, 82), f"${tvl_txt}", font=font("black", 82), fill=B["text"], anchor="ra")
        col = B["muted"] if tvl_chg is None else (B["up"] if tvl_chg >= 0 else B["down"])
        txt = f"{abs(tvl_chg or 0):.2f}% · " + t_("اليوم", "today")
        d.text((W-124, 200), txt, font=font("bold", 30), fill=col, anchor="ra", **kw("اليوم"))
        if tvl_chg is not None:
            tri(d, W - 124 - tlen(d, txt, font("bold", 30)) - 22, 216, 10, tvl_chg >= 0, col)
    layers.append(_block(draw_tvl))

    if mover:
        def draw_mover(d):
            hgt = 220
            d.rounded_rectangle([SAFE_R, 0, W-SAFE_R, hgt], radius=30, fill=B["accent2"] + (42,),
                                outline=B["accent2"] + (120,), width=3)
            _mv = t_("التحرك الأكبر اليوم", "Biggest mover today")
            d.text((W-124, 26), _mv, font=font("bold", 29), fill=B["muted"],
                   anchor="ra", **kw(_mv))
            d.text((W-124, 78), mover["name"], font=font("black", 54), fill=B["text"], anchor="ra")
            col = B["up"] if (mover.get("change24") or 0) >= 0 else B["down"]
            pct_txt = f"{abs(mover['change24']):.1f}%"
            d.text((124, 92), pct_txt, font=font("black", 58), fill=col, anchor="la")
            tri(d, 124 + tlen(d, pct_txt, font("black", 58)) + 26, 92 + 30, 17,
                (mover.get("change24") or 0) >= 0, col)
        layers.append(_block(draw_mover))

    if top:
        def draw_top(d):
            y = 0
            _top = t_("أكبر البروتوكولات", "Largest protocols")
            d.text((W-SAFE_R, y), _top, font=font("bold", 34), fill=B["muted"],
                   anchor="ra", **kw(_top))
            y += 62
            for i, p in enumerate(top[:3]):
                hh = 100
                d.rounded_rectangle([SAFE_R, y, W-SAFE_R, y+hh], radius=18,
                                    fill=(255, 255, 255, 12 if i % 2 == 0 else 7))
                d.text((W-116, y + hh/2), p["name"], font=font("bold", 38), fill=B["text"], anchor="rm")
                chg = p.get("change24")
                col = B["muted"] if chg is None else (B["up"] if chg >= 0 else B["down"])
                txt = f"{abs(chg or 0):.1f}%"
                d.text((124, y + hh/2), txt, font=font("bold", 34), fill=col, anchor="lm")
                if chg is not None:
                    tri(d, 124 + tlen(d, txt, font("bold", 34)) + 20, y + hh/2, 11, chg >= 0, col)
                y += hh + 14
        layers.append(_block(draw_top))

    img = flex_compose(img, layers, base_gap=30, max_gap=80)
    footer(img, info.get("page", 4), info.get("total", 6))
    return img


# ---------------- 5) القراءة ----------------
def scene_reading(info, text):
    img = background(5)
    header(img, t_("THE READ · ماذا يعني؟", "THE READ"))
    _rt = t_("ماذا يعني هذا للسوق؟", "What this means for the market")
    layers = [_block(lambda d: section_title(d, _rt, 0, 60))]

    def draw_card(d):
        f_body = font("reg", 46)
        th = block_height(d, text, W - 260, f_body, 26)
        card_h = th + 200
        d.rounded_rectangle([SAFE_R, 0, W-SAFE_R, card_h], radius=36, fill=(255, 255, 255, 13),
                            outline=B["accent2"] + (150,), width=3)
        if is_en():
            d.text((118, -34), "\u201C", font=font("black", 104), fill=B["accent2"] + (140,), anchor="la")
        else:
            d.text((W - 118, -34), "\u201D", font=font("black", 104), fill=B["accent2"] + (140,), anchor="ra")
        draw_block(d, text, (130, 96), W - 260, f_body, B["text"], 26, _align())
    layers.append(_block(draw_card))

    note = t_("ليس نصيحة مالية — راقب السيولة قبل أي قرار",
              "Not financial advice - watch liquidity before any decision")
    layers.append(_block(lambda d: d.text((W//2, 4), note, font=font("reg", 30), fill=B["muted"],
                                          anchor="ma", **kw(note))))
    img = flex_compose(img, layers, base_gap=40, max_gap=90)
    footer(img, info.get("page", 5), info.get("total", 6))
    return img


# ---------------- 6) النهاية ----------------
def scene_outro(info, disclaimer):
    img = background(6)
    layers = []

    def draw_logo(d):
        cx, cy, r = W//2, 152, 150
        d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=B["accent"] + (210,), width=6, fill=(255, 255, 255, 10))
        # رمز bitcoin: حرف B لاتيني + عمودان علويان
        d.text((cx, cy + 6), "B", font=font("black", 168), fill=B["accent"], anchor="mm")
        for dx in (-26, 26):
            d.line([(cx + dx, cy - 96), (cx + dx, cy - 58)], fill=B["accent"], width=13)
    layers.append(_block(draw_logo))

    def draw_name(d):
        y = draw_block(d, config.BRAND["name_en"] if is_en() else config.BRAND["name_ar"],
                       (84, 0), W-168, font("black", 74), B["text"], 10, "center")
        d.text((W//2, y + 42), config.BRAND["handle"], font=font("bold", 44), fill=B["accent"], anchor="ma")
        y += 122
        draw_block(d, config.BRAND["tagline_en"] if is_en() else config.BRAND["tagline_ar"],
                   (84, y + 16), W-168, font("reg", 40), B["muted"], 8, "center")
    layers.append(_block(draw_name))

    def draw_btn(d):
        bx, by = W//2 - 230, 0
        d.rounded_rectangle([bx, by, bx+460, by+118], radius=59, fill=B["accent"] + (255,))
        t = t_("تابعنا للمزيد", "Follow for more")
        d.text((W//2, by+59), t, font=font("black", 46), fill=(6, 18, 24), anchor="mm", **kw(t))
    layers.append(_block(draw_btn))

    layers.append(_block(lambda d: draw_block(d, disclaimer, (84, 0), W-168, font("reg", 30),
                                              B["muted"], 6, "center")))
    img = flex_compose(img, layers, base_gap=46, max_gap=120)
    footer(img, info.get("page", 6), info.get("total", 6))
    return img
