"""النشر والإخراج: نسخ الفيديو إلى Google Drive (عبر Google Drive Desktop أو rclone)
وإنشاء ملف manifest للتتبع. النشر إلى TikTok يبقى يدويًا/نصف آلي لاحقًا حسب السياسات.
"""
from __future__ import annotations
import json, os, shutil, subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from . import config

YEMEN = timezone(timedelta(hours=3))


def _drive_target() -> Path | None:
    """يبحث عن مجلد Google Drive المحلي (Google Drive Desktop / rclone mount)."""
    env = os.getenv("DRIVE_PATH")
    candidates = [env] if env else []
    candidates += [
        str(Path.home() / "Google Drive" / "My Drive"),
        str(Path.home() / "GoogleDrive" / "My Drive"),
        str(Path.home() / "Library" / "CloudStorage"),
        "/mnt/gdrive",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    return None


def publish(video: Path, caption_file: Path, extra_dir: str | None = None) -> dict:
    """ينسخ الفيديو + الكابشن إلى مجلد Drive (إن وُجد) ويسجل manifest."""
    video, caption_file = Path(video), Path(caption_file)
    stamp = datetime.now(YEMEN).strftime("%Y-%m-%d_%H%M")
    record = {"created": stamp, "video": video.name, "caption": caption_file.name,
              "drive": None, "status": "ready_for_review"}

    target_root = _drive_target()
    if target_root:
        # مجلد مقترح: CryptoPulse/<السنة>/<الشهر>/ready
        sub = Path(extra_dir) if extra_dir else Path("CryptoPulse") / stamp[:7] / "ready"
        dest = target_root / sub
        dest.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(video, dest / video.name)
            shutil.copy2(caption_file, dest / caption_file.name)
            record["drive"] = str(dest)
        except Exception as e:
            record["drive_error"] = str(e)

    # سجل محلي
    log = config.DATA / "published.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def batch_manifest(renders_dir: Path | None = None) -> Path:
    """يجمع كل الفيديوهات الجاهزة في مجلد batch + ملف CSV للاستيراد في أدوات الجدولة.

    الأعمدة: file, caption_file, language, kind, created, caption, hashtags
    """
    import csv
    renders_dir = Path(renders_dir or config.RENDERS)
    out_dir = renders_dir / "batch"
    out_dir.mkdir(parents=True, exist_ok=True)

    def caption_of(v: Path) -> str:
        c = v.with_suffix(".txt")
        if not c.exists():
            return ""
        txt = c.read_text(encoding="utf-8").strip()
        return " ".join(txt.split())

    rows = []
    for v in sorted(renders_dir.glob("*.mp4")):
        lang = "ar" if v.stem.endswith("_ar") else ("en" if v.stem.endswith("_en") else "")
        parts = v.stem.split("_")            # 20261122_2330_us_open_ar
        kind = "_".join(parts[2:-1]) if len(parts) > 3 else ""
        created = "_".join(parts[:2])
        cap = caption_of(v)
        body, _, tags = cap.partition("#")
        rows.append({"file": v.name, "caption_file": v.with_suffix(".txt").name,
                     "language": lang, "kind": kind, "created": created,
                     "caption": body.strip(), "hashtags": ("#" + tags).strip() if tags else ""})
        shutil.copy2(v, out_dir / v.name)
        if v.with_suffix(".txt").exists():
            shutil.copy2(v.with_suffix(".txt"), out_dir / v.with_suffix(".txt").name)

    csv_path = out_dir / "schedule.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["file", "caption_file", "language", "kind",
                                          "created", "caption", "hashtags"])
        w.writeheader()
        w.writerows(rows)
    return csv_path


if __name__ == "__main__":
    import sys
    if "--batch" in sys.argv:
        print("CSV:", batch_manifest())
    else:
        print("DRIVE_PATH:", os.getenv("DRIVE_PATH"))
        print("detected:", _drive_target())
