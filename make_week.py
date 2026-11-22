#!/usr/bin/env python3
"""مولّد الدفعة الأسبوعية: ينتج فيديوهات أسبوع كامل + جدول نشر جاهز.

طريقتان:

1) دفعة سريعة (بيانات السوق الحالية، 8 فيديوهات متنوعة):
     python3 make_week.py --quick
   → renders/week_<تاريخ>/ + جدول CSV جاهز

2) دفعة حقيقية (فيديو لكل يوم بنوعه الصحيح، مع انتظار المواعيد — تلقائيًا في GitHub Actions):
     python3 make_week.py                 # يعمل يوميًا ويصدر فيديو اليوم
"""
from __future__ import annotations
import argparse, csv, json, shutil, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src import config, datafeed, newsradar, scriptwriter, videobuild, publish

YEMEN = timezone(timedelta(hours=3))

# شبكة الأسبوع بتوقيت اليمن (UTC+3)
WEEK_GRID = [
    ("03:00", "asia_open"),
    ("11:00", "europe_open"),
    ("17:30", "us_open"),
    ("23:00", "daily_recap"),
]

AR_DAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
EN_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _slug(kind: str) -> str:
    return {"asia_open": "asia", "europe_open": "europe",
            "us_open": "us", "daily_recap": "recap", "breaking": "breaking"}[kind]


def build_one(snap, news, kind: str, lang: str, out_dir: Path,
              day: datetime, slot: str, idx: int) -> dict:
    script = scriptwriter.build(snap, news, kind)
    stamp = f"{day:%Y%m%d}_{slot.replace(':','')}"
    name = f"{idx:02d}_{_slug(kind)}_{stamp}_{lang}"
    out = out_dir / f"{name}.mp4"

    videobuild.render(script, out, lang=lang)

    cap = script["narration_ar"] if lang == "ar" else script["narration_en"]
    disc = config.AI_DISCLOSURE_AR if lang == "ar" else config.AI_DISCLOSURE_EN
    tags = config.HASHTAGS_AR if lang == "ar" else config.HASHTAGS_EN
    cap_file = out.with_suffix(".txt")
    cap_file.write_text(cap + "\n\n" + disc + "\n" + tags, encoding="utf-8")

    (out_dir / f"{name}.json").write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

    day_ar = AR_DAYS[day.weekday()]
    return {
        "file": out.name, "caption_file": cap_file.name,
        "language": lang, "kind": kind,
        "publish_date": f"{day:%Y-%m-%d}", "publish_time_yemen": slot,
        "day_ar": day_ar, "day_en": EN_DAYS[day.weekday()],
        "caption": " ".join(cap.split()),
        "hashtags": tags,
        "disclaimer": disc,
    }


def write_schedule(rows: list[dict], out_dir: Path) -> Path:
    """جدول النشر + ملف تعليمات واضح."""
    csv_path = out_dir / "schedule.csv"
    cols = ["file", "caption_file", "language", "kind", "publish_date",
            "publish_time_yemen", "day_ar", "day_en", "caption", "hashtags", "disclaimer"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    lines = ["# جدول النشر — نبض الكريبتو (@trade7717)", "",
             "كل صف = فيديو جاهز. المواعيد بتوقيت اليمن (UTC+3).", ""]
    cur = None
    for r in sorted(rows, key=lambda x: (x["publish_date"], x["publish_time_yemen"])):
        if r["publish_date"] != cur:
            cur = r["publish_date"]
            lines += ["", f"## {r['day_ar']} — {cur}", ""]
        lang = "عربي" if r["language"] == "ar" else "English"
        lines.append(f"- **{r['publish_time_yemen']}** · {lang} · `{r['file']}`")
    lines += ["", "---", "",
              "## طريقة النشر (لكل فيديو)",
              "1. نزّل الفيديو من Drive إلى معرض الهاتف.",
              "2. تيك توك → ＋ → رفع الفيديو.",
              "3. افتح ملف `.txt` بجانبه وانسخ الكابشن كاملًا.",
              "4. فعّل خيار **المحتوى المولّد بالذكاء الاصطناعي** (إلزامي).",
              "5. انشر في الموعد المكتوب في الجدول.", ""]
    md_path = out_dir / "SCHEDULE.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path


def quick_week(langs=("ar", "en"), days: int = 7, use_dir: Path | None = None) -> Path:
    """دفعة سريعة: 4 افتتاحات × يوم واحد + تنويع على الأسبوع، ببيانات اللحظة."""
    print("▶ جمع بيانات السوق…")
    snap = datafeed.snapshot()
    print("▶ رادار الأخبار…")
    news = newsradar.collect(20)
    print(f"  {len(news)} خبرًا — أعلى تقييم {news[0]['score'] if news else 0}/10")

    today = datetime.now(YEMEN)
    out_dir = use_dir or (config.RENDERS / f"week_{today:%Y%m%d}")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, idx = [], 1
    for d in range(days):
        day = today + timedelta(days=d)
        for slot, kind in WEEK_GRID:
            for lang in langs:
                print(f"▶ [{idx}] {day:%d/%m} {slot} {kind} {lang}…")
                t0 = time.time()
                rows.append(build_one(snap, news, kind, lang, out_dir, day, slot, idx))
                print(f"   ✔ {rows[-1]['file']}  ({time.time()-t0:.0f}s)")
                idx += 1

    csv_path = write_schedule(rows, out_dir)
    print(f"\n✔ {len(rows)} فيديو في: {out_dir}")
    print(f"✔ الجدول: {csv_path}")
    return out_dir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="دفعة سريعة كاملة (بيانات اللحظة)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--lang", default="both", choices=["both", "ar", "en"])
    ap.add_argument("--one", action="store_true",
                    help="فيديو واحد لليوم الحالي (للاستخدام في GitHub Actions)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    langs = ("ar", "en") if args.lang == "both" else (args.lang,)

    if args.one:
        # يُستدعى من الجدولة اليومية: يبني الفيديو المناسب للساعة الحالية
        import make
        make.main_kind(langs=langs)
        return

    quick_week(langs=langs, days=args.days,
               use_dir=Path(args.out) if args.out else None)


if __name__ == "__main__":
    main()
