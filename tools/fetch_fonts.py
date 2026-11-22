"""احتياطي: تنزيل خطوط Cairo / Tajawal / Noto Naskh من Google Fonts إن لم تكن في assets/fonts."""
from pathlib import Path
import io
import urllib.request
import zipfile

DEST = Path("assets/fonts")
DEST.mkdir(parents=True, exist_ok=True)

WANTED = [
    "Cairo-ExtraBold.ttf",
    "Tajawal-Bold.ttf",
    "Tajawal-Regular.ttf",
    "NotoNaskhArabic-Bold.ttf",
]

# (اسم عائلة Google Fonts, اسم الملف داخل الأرشيف, الاسم المتوقع محليًا)
SOURCES = [
    ("Cairo", {"Cairo-ExtraBold.ttf": "Cairo-ExtraBold.ttf", "Cairo-Bold.ttf": "Cairo-Bold.ttf"}),
    ("Tajawal", {"Tajawal-Bold.ttf": "Tajawal-Bold.ttf", "Tajawal-Regular.ttf": "Tajawal-Regular.ttf"}),
    ("Noto Naskh Arabic", {"NotoNaskhArabic-Bold.ttf": "NotoNaskhArabic-Bold.ttf",
                           "NotoNaskhArabic-Regular.ttf": "NotoNaskhArabic.ttf"}),
]


def grab(family: str, mapping: dict) -> int:
    url = "https://fonts.google.com/download?family=" + family.replace(" ", "%20")
    try:
        data = urllib.request.urlopen(url, timeout=90).read()
        z = zipfile.ZipFile(io.BytesIO(data))
    except Exception as e:  # noqa: BLE001
        print("skip", family, e)
        return 0
    got = 0
    for name in z.namelist():
        if not name.lower().endswith(".ttf"):
            continue
        base = name.split("/")[-1].replace(" ", "")
        target = mapping.get(base)
        if not target:
            continue
        (DEST / target).write_bytes(z.read(name))
        print("ok", target)
        got += 1
    return got


if __name__ == "__main__":
    missing = [w for w in WANTED if not (DEST / w).exists()]
    if not missing:
        print("all fonts present")
        raise SystemExit(0)
    print("missing:", missing)
    for fam, mapping in SOURCES:
        grab(fam, mapping)
    still = [w for w in WANTED if not (DEST / w).exists()]
    print("missing after fetch:", still)
