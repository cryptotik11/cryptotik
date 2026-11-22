"""تحويل النص إلى صوت عبر edge-tts (مجاني، بدون مفتاح)."""
from __future__ import annotations
import asyncio, subprocess, json
from pathlib import Path
import edge_tts
from . import config


def _sanitize(text: str) -> str:
    """تنظيف نص السرد: إزالة الرموز التعبيرية والأحرف التي تُنطق حرفيًا."""
    for ch in "★•●🚨🧠📌⏰🌍🐋₿▲▼|#🔴🟢⚡💡📊📉📈":
        text = text.replace(ch, " ")
    text = text.replace("…", ".").replace("—", "،").replace(" · ", "، ").replace("%", " في المئة ")
    return " ".join(text.split())


async def _synth(text: str, voice: str, rate: str, out: Path) -> None:
    comm = edge_tts.Communicate(text, voice=voice, rate=rate)
    await comm.save(str(out))


def synthesize(text: str, out_path: Path, lang: str = "ar") -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    voice = config.VOICES["ar"] if lang == "ar" else config.VOICES["en"]
    rate = config.VOICES["ar_rate"] if lang == "ar" else config.VOICES["en_rate"]
    txt = _sanitize(text)
    asyncio.run(_synth(txt, voice, rate, out_path))
    return out_path


def duration(path: Path) -> float:
    """مدة الملف الصوتي بالثواني — ffmpeg فقط (لا حاجة لـ ffprobe)."""
    import imageio_ffmpeg, re
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        out = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True, timeout=30).stderr
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", out)
        if m:
            h, mi, s = m.groups()
            return int(h) * 3600 + int(mi) * 60 + float(s)
    except Exception:
        pass
    return max(3.0, Path(path).stat().st_size / 2000 / 1.0)


def synth_durations(scenes: list, key: str, work, lang: str) -> list[float]:
    """يولّد صوتًا لكل مشهد على حدة ويقيس مدة كل مقطع بالثواني."""
    from concurrent.futures import ThreadPoolExecutor
    items = [(i, str(s.get(key) or "").strip()) for i, s in enumerate(scenes)]

    def one(item):
        i, txt = item
        if not txt:
            return i, 2.0
        p = Path(work) / f"narr_{lang}_{i:02d}.mp3"
        try:
            synthesize(txt, p, lang)
            return i, duration(p)
        except Exception:
            return i, max(2.0, len(txt) / 15.0)

    out = [2.0] * len(scenes)
    with ThreadPoolExecutor(max_workers=4) as ex:
        for i, d in ex.map(one, items):
            out[i] = d
    return out
