"""تجميع الفيديو: مشاهد PNG + تعليق صوتي ar/en + موسيقى خلفية اختيارية → MP4 عمودي 9:16.
يستخدم ffmpeg من imageio-ffmpeg (بدون تثبيت نظامي).
"""
from __future__ import annotations
import io, math, subprocess, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import imageio_ffmpeg
from . import config, scenes, voice

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = config.VIDEO["w"], config.VIDEO["h"], config.VIDEO["fps"]


# ---------- موسيقى خلفية مولّدة (بدون حقوق) ----------
def make_bed(duration: float, out: Path, sr: int = 44100) -> Path:
    """نغمة خلفية هادئة: طبقات سينث بسيطة + ضجيج ناعم، بلا إيقاع صارخ."""
    n = int(duration * sr)
    t = np.arange(n) / sr
    # وتر Am ناعم (A2–E3–C4) بتدفق بطيء
    freqs = [110.0, 164.81, 261.63]
    wave = np.zeros(n)
    for i, f in enumerate(freqs):
        wave += (0.22 - i * 0.05) * np.sin(2 * np.pi * f * t + i)
        wave += 0.05 * np.sin(2 * np.pi * f * 2 * t)
    # تفاعل بطيء + فيبراتو
    wave *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t)
    # ضجيج هواء منخفض
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, n)
    kernel = np.ones(2000) / 2000
    noise = np.convolve(noise, kernel, mode="same") * 0.25
    wave = wave * 0.32 + noise * 0.5
    # فيد إن/أوت
    fade = int(1.5 * sr)
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    wave = np.clip(wave * 0.5, -1, 1)
    pcm = (wave * 32767).astype(np.int16)
    p = subprocess.Popen([FFMPEG, "-y", "-f", "s16le", "-ar", str(sr), "-ac", "2",
                          "-i", "-", str(out)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    p.communicate(stereo.tobytes())
    return out


# ---------- إطار متحرك خفيف: تحريك الشارت/النبض داخل صورة ثابتة ----------
def render_clip(image: Path, seconds: float, out: Path, zoom: bool = True) -> Path:
    """حول PNG ثابت إلى مقطع MP4 بمدة محددة مع حركة زوم/بان خفيفة (Ken Burns)."""
    dur = max(0.5, seconds)
    if zoom:
        # زوم من 1.0 إلى 1.04 حول المنتصف
        vf = (f"scale={W*2}:{H*2},zoompan=z='min(1.0+0.0009*on,1.05)':x='(iw-iw/zoom)/2':"
              f"y='(ih-ih/zoom)/2':d={int(dur*FPS)}:s={W}x{H}:fps={FPS},format=yuv420p")
    else:
        vf = f"scale={W}:{H},format=yuv420p"
    subprocess.run([FFMPEG, "-y", "-loop", "1", "-i", str(image), "-t", f"{dur:.2f}",
                    "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", str(out)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return out


def concat_clips(clips: list[Path], out: Path) -> Path:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for c in clips:
            f.write(f"file '{c.resolve()}'\n")
        list_file = f.name
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
                    "-c", "copy", str(out)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return out


def mux(video: Path, audio: Path, out: Path, bed: Path | None = None,
        bed_gain: float = 0.18, fade_out: float = 1.2, total: float | None = None) -> Path:
    """دمج الصوت مع خفض الموسيقى وfade-out في النهاية."""
    args = [FFMPEG, "-y", "-i", str(video), "-i", str(audio)]
    if bed:
        args += ["-i", str(bed)]
        fc = (f"[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[voice];"
              f"[2:a]volume={bed_gain}[bg];[voice][bg]amix=inputs=2:duration=first:normalize=0[a]")
        args += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]"]
    else:
        args += ["-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11"]
    if total:
        args += ["-af", f"afade=t=out:st={max(0,total-fade_out):.2f}:d={fade_out}"] if not bed else []
    args += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return out


def render(script: dict, out_path: Path, lang: str = "ar") -> Path:
    """يبني الفيديو كاملًا من السكربت."""
    out_path = Path(out_path)
    work = Path(tempfile.mkdtemp(prefix="ctk_"))
    sc = script["scenes"]
    total_scenes = len(sc)

    # 0) لغة واجهة المشاهد
    scenes.set_lang(lang)

    # 1) صور المشاهد
    imgs: list[Path] = []
    for i, s in enumerate(sc):
        info = {"label": s.get("label", ""), "page": i + 1, "total": total_scenes}
        t = s["type"]
        if t == "hook":
            q = {x["symbol"]: x for x in (s.get("quotes") or [])}
            hk = s.get("headline_en") if lang != "ar" else s["headline_ar"]
            img = scenes.scene_hook(info, hk or s["headline_ar"],
                                    s.get("price_txt", script.get("price_txt", "—")),
                                    s.get("btc_change"),
                                    stamp=(s.get("stamp_en") if lang != "ar" else s.get("stamp")),
                                    stats=s.get("stats"))
        elif t == "prices":
            img = scenes.scene_market(info, s.get("quotes_rich", []), s.get("mcap_txt", "—"),
                                      s.get("mcap_chg"), s.get("fng", {}))
        elif t == "news":
            from .newsradar import news_image
            ipath = None
            if s.get("image_query"):
                ipath = news_image(s["image_query"], None, work)
            hl = s.get("headline_en") if lang != "ar" else s.get("headline_ar")
            img = scenes.scene_news(info, hl or s.get("headline_ar", ""), s.get("source", ""),
                                    s.get("news"), image_path=ipath)
        elif t == "defi":
            dd = s.get("defi", {})
            img = scenes.scene_defi(info, s.get("tvl_txt", "—"), dd.get("tvl_change_pct"),
                                    s.get("mover"), dd.get("top", []))
        elif t == "reading":
            rt = s.get("read_en") if lang != "ar" else s.get("read_ar")
            img = scenes.scene_reading(info, rt or s.get("read_ar", ""))
        else:
            img = scenes.scene_outro(info, config.BRAND["disclaimer_en"] if lang != "ar"
                                     else config.BRAND["disclaimer_ar"])
        p = work / f"scene_{i:02d}.png"
        img.save(p)
        imgs.append(p)

    # 2) صوت التعليق
    narr_key = "narration_ar" if lang == "ar" else "narration_en"
    full_text = " ... ".join(x[narr_key] for x in sc if x.get(narr_key))
    narration = voice.synthesize(full_text, work / f"narration_{lang}.mp3", lang)
    adur = voice.duration(narration)

    # 3) مدد حقيقية بحسب طول صوت كل مشهد (لا افتراضات)
    try:
        adurs = voice.synth_durations(sc, narr_key, work, lang)
        gap = 0.35
        durs = [max(2.2, d + gap) for d in adurs]
        adur = sum(durs)                     # المدة الكلية = مجموع مدد المشاهد
    except Exception as e:
        print("   ! قياس مدد المشاهد فشل، استخدام التوزيع التقريبي:", e)
        weights = [max(0.12, len(x.get(narr_key, ""))) for x in sc]
        tw = sum(weights)
        durs = [max(2.4, adur * w / tw) for w in weights]
        scale = adur / sum(durs)
        durs = [d * scale for d in durs]

    # 4) مقاطع
    clips = []
    for i, (img, d) in enumerate(zip(imgs, durs)):
        clips.append(render_clip(img, d, work / f"clip_{i:02d}.mp4"))
    silent = concat_clips(clips, work / "silent.mp4")

    # 5) موسيقى خلفية + دمج
    adur_real = voice.duration(narration)
    bed = make_bed(max(adur, adur_real) + 0.4, work / "bed.wav")
    final = mux(silent, narration, out_path, bed=bed, total=adur)
    return final


if __name__ == "__main__":
    print("استخدم make.py")
