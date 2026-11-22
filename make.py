#!/usr/bin/env python3
"""نقطة التشغيل الرئيسية.
أمثلة:
  python3 make.py --kind us_open              # فيديو افتتاح أمريكا (عربي)
  python3 make.py --kind daily_recap --lang en
  python3 make.py --auto                      # يختار نوع الفيديو حسب الساعة الحالية (توقيت اليمن)
"""
from __future__ import annotations
import argparse, json, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src import config, datafeed, newsradar, scriptwriter, videobuild, publish

YEMEN = timezone(timedelta(hours=3))


def pick_kind() -> str:
    now = datetime.now(YEMEN)
    hm = now.strftime("%H:%M")
    sched = config.SCHEDULE_YEMEN
    # أقرب افتتاح خلال 45 دقيقة
    for kind, t in sched.items():
        h, m = map(int, t.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if abs((now - target).total_seconds()) <= 45 * 60:
            return kind
    if 3 <= now.hour < 11:
        return "asia_open"
    if 11 <= now.hour < 17:
        return "europe_open"
    if 17 <= now.hour < 23:
        return "us_open"
    return "daily_recap"


def create_script(kind: str) -> tuple[dict, str]:
    """يجمع البيانات ويبني السكربت، ويحفظه JSON. يعيد (script, stamp)."""
    print("▶ جمع بيانات السوق…")
    snap = datafeed.snapshot()
    print("▶ فحص رادار الأخبار…")
    news = newsradar.collect(20)
    print(f"  {len(news)} خبرًا بعد الفلترة — أعلى تقييم: {news[0]['score'] if news else 0}/10")

    script = scriptwriter.build(snap, news, kind)
    config.DATA.mkdir(exist_ok=True)
    stamp = datetime.now(YEMEN).strftime("%Y%m%d_%H%M")
    sp = config.DATA / f"script_{kind}_{stamp}.json"
    sp.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ السكربت: {sp}")
    return script, stamp


def main_kind(langs=("ar",), out: str | None = None):
    """يبني النوع المناسب للساعة الحالية (يستخدمه GitHub Actions)."""
    kind = pick_kind()
    print(f"▶ نوع الفيديو (تلقائي): {kind}")
    script, stamp = create_script(kind)
    config.RENDERS.mkdir(exist_ok=True)
    for lang in langs:
        o = Path(out) if (out and len(langs) == 1) else config.RENDERS / f"{stamp}_{kind}_{lang}.mp4"
        print(f"▶ رندر الفيديو ({lang})…")
        t0 = time.time()
        videobuild.render(script, o, lang=lang)
        print(f"✔ {o}  ({time.time()-t0:.1f}s)")
        write_caption(script, o, lang)
        rec = publish.publish(o, o.with_suffix(".txt"))
        if rec.get("drive"):
            print(f"✔ نسخة إلى Drive: {rec['drive']}")


def write_caption(script: dict, out: Path, lang: str) -> Path:
    cap = script["narration_ar"] if lang == "ar" else script["narration_en"]
    tags = config.HASHTAGS_AR if lang == "ar" else config.HASHTAGS_EN
    disc = config.AI_DISCLOSURE_AR if lang == "ar" else config.AI_DISCLOSURE_EN
    cap_file = out.with_suffix(".txt")
    cap_file.write_text(cap + "\n\n" + disc + "\n" + tags, encoding="utf-8")
    print(f"✔ الكابشن: {cap_file}")
    return cap_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default=None,
                    choices=["asia_open", "europe_open", "us_open", "daily_recap", "breaking"])
    ap.add_argument("--lang", default="ar", choices=["ar", "en"])
    ap.add_argument("--auto", action="store_true", help="اختيار النوع حسب الساعة (توقيت اليمن)")
    ap.add_argument("--no-video", action="store_true", help="سكربت فقط بدون رندر")
    ap.add_argument("--both", action="store_true", help="إنتاج النسختين العربية والإنجليزية")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    kind = "breaking" if args.kind == "breaking" else (args.kind or (pick_kind() if args.auto else "us_open"))
    print(f"▶ نوع الفيديو: {kind}")
    script, stamp = create_script(kind)

    if args.no_video:
        return

    config.RENDERS.mkdir(exist_ok=True)
    langs = ["ar", "en"] if args.both else [args.lang]
    for lang in langs:
        out = Path(args.out) if args.out and len(langs) == 1 else config.RENDERS / f"{stamp}_{kind}_{lang}.mp4"
        print(f"▶ رندر الفيديو ({lang})…")
        t0 = time.time()
        videobuild.render(script, out, lang=lang)
        print(f"✔ {out}  ({time.time()-t0:.1f}s)")
        cap_file = write_caption(script, out, lang)
        rec = publish.publish(out, cap_file)
        if rec.get("drive"):
            print(f"✔ نسخة إلى Drive: {rec['drive']}")


if __name__ == "__main__":
    main()
