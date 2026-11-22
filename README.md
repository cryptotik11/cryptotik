# 🎬 نبض الكريبتو — Crypto Pulse AI (@trade7717)

نظام آلي كامل يحوّل بيانات السوق والأخبار الحية إلى **فيديوهات تيك توك عمودية (9:16) بالعربية والإنجليزية** جاهزة للمراجعة والنشر — بدون أي اشتراك مدفوع.

```
CoinMarketCap + DefiLlama + RSS + Google News
             ↓
     رادار أخبار + تقييم 1–10
             ↓
   سكربت عربي/إنجليزي + ترجمة تلقائية
             ↓
 تعليق صوتي (edge-tts) + مشاهد 9:16 (Pillow)
             ↓
        MP4 + كابشن + هاشتاجات
             ↓
   رندر محلي → Google Drive → مراجعة → TikTok
```

---

## ⚡ التشغيل السريع

```bash
pip install -r requirements.txt

# فيديو افتتاح السوق الأمريكي (عربي)
python3 make.py --kind us_open --lang ar

# اختيار النوع تلقائيًا حسب الساعة (توقيت اليمن)
python3 make.py --auto

# النسختان العربية والإنجليزية معًا
python3 make.py --auto --both

# سكربت فقط بدون رندر (سريع)
python3 make.py --kind daily_recap --no-video

# 🔥 أسبوع كامل دفعة واحدة (4 مواعيد × 7 أيام × لغتين = 56 فيديو)
python3 make_week.py --quick --days 7 --lang both

# يوم واحد فقط (4 فيديوهات) للتجربة
python3 make_week.py --quick --days 1 --lang ar
```

**النواتج في `renders/`:**
- `YYYYMMDD_HHMM_<kind>_<lang>.mp4` — الفيديو
- `..._<lang>.txt` — الكابشن + الإفصاح + الهاشتاجات
- `data/script_*.json` — السكربت الكامل + الأرقام (للتحقق)

**نواتج الدفعة الأسبوعية في `renders/week_<تاريخ>/`:**
- `01_asia_20261223_0300_ar.mp4` — مُرقّمة بالترتيب الزمني
- `schedule.csv` — جدول: الملف، اللغة، التاريخ، الساعة، الكابشن، الهاشتاجات
- `SCHEDULE.md` — نفس الجدول للقراءة السريعة على الهاتف

---

## 🧩 المكوّنات

| الملف | الوظيفة |
|---|---|
| `src/config.py` | **كل الإعدادات هنا**: الهوية، الألوان، العملات، المصادر، أوقات النشر، الأصوات |
| `src/datafeed.py` | أسعار + قيمة السوق + TVL + مؤشر الخوف/الجشع · 3 طبقات احتياطية |
| `src/newsradar.py` | RSS + Google News (CZ/Musk/Trump) + **تقييم أهمية 1–10** |
| `src/translate.py` | ترجمة العناوين للعربية (MyMemory مجانًا + ذاكرة تخزين) |
| `src/scriptwriter.py` | يبني السكربت والمشاهد · يحسّن الصياغة إن وُجد `OPENAI_API_KEY` |
| `src/scenes.py` | رسم المشاهد 9:16 (خلفيات، بطاقات، شارتات، RTL كامل) |
| `src/voice.py` | تعليق صوتي edge-tts + تنظيف النص |
| `src/videobuild.py` | ffmpeg: زوم Ken Burns + موسيقى مولّدة + دمج الصوت |
| `src/publish.py` | نسخ إلى Google Drive + سجل + مولّد جدول `--batch` |
| `make.py` | نقطة التشغيل (فيديو واحد) |
| `make_week.py` | **مولّد دفعة أسبوعية** (حتى 56 فيديو + جدول نشر) |
| `tools/fetch_fonts.py` | تنزيل الخطوط تلقائيًا على أي جهاز |

---

## ⚙️ التخصيص في 5 دقائق

كل شيء من `src/config.py`:

```python
BRAND = {
    "handle": "@trade7717",     # ← غيّره
    "name_ar": "نبض الكريبتو",       # ← غيّره
    "accent": (34, 211, 238),       # ← لونك
}
COINS = [...]                        # ← عملاتك
NEWS_FEEDS = [...]                   # ← مصادرك
VOICES = {"ar": "ar-SA-HamedNeural"} # ← بديل: ar-EG-ShakirNeural · ar-SA-ZariyahNeural (أنثى)
```

**تغيير الأصوات:** `edge-tts --list-voices | grep ar-`

---

## 🕐 الجدولة — الخيار الموصى به: GitHub Actions (مجاني 24/7)

### الإعداد (10 دقائق، مرة واحدة)

1. أنشئ مستودعًا **خاصًا** على GitHub وارفع المشروع:
   ```bash
   git init && git add . && git commit -m "Crypto Pulse AI"
   git remote add origin https://github.com/<user>/crypto-pulse-ai.git
   git push -u origin main
   ```
2. يعمل الملف `.github/workflows/make-video.yml` تلقائيًا في المواعيد:
   - `00:00 UTC` = **03:00** اليمن (آسيا)
   - `08:00 UTC` = **11:00** اليمن (أوروبا)
   - `14:30 UTC` = **17:30** اليمن (أمريكا)
   - `20:00 UTC` = **23:00** اليمن (الملخص)
3. شغّل يدويًا من **Actions → Run workflow** لاختيار النوع واللغة.
4. نزّل الفيديوهات من **Artifacts** بعد كل تشغيل.

### إضافة Google Drive تلقائيًا (اختياري)
1. ثبّت [rclone](https://rclone.org/drive/) على جهازك: `rclone config` → جديد → Google Drive → وافق.
2. انسخ محتوى ملف الإعداد وضعه في GitHub: **Settings → Secrets → Actions → New secret** باسم `RCLONE_CONF`.
3. ينسخ الـ workflow تلقائيًا إلى `gdrive:CryptoPulse/ready/`.

### تشغيل على جهازك (بديل)
```bash
# Linux/Mac
(crontab -l; echo "30 14 * * * cd ~/cryptotik && python3 make.py --auto --both") | crontab -
```
```powershell
# Windows (Task Scheduler) — أو ببساطة شغّل يدويًا قبل الافتتاح
schtasks /create /tn "CryptoPulse" /tr "python C:\cryptotik\make.py --auto" /sc daily /st 14:30
```

---

## 📤 النشر إلى TikTok

الأتمتة الكاملة للنشر تخالف سياسات تيك توك (لا API رسمي للفيديو من طرف ثالث بدون اعتماد).
**الطريقة الموصى بها (نصف آلية):**

1. الفيديو + الكابشن يصلان إلى مجلد Drive على هاتفك (`My Drive/CryptoPulse/...`).
2. افتح Drive على الجوال → نزّل الفيديو → انسخ الكابشن من ملف `.txt`.
3. انشره من تطبيق TikTok (أفضل وصول من الرفع عبر الويب).

بهذا تبقى دورة العمل: **تشغيل آلي كامل → نشر يدوي في 60 ثانية.**

---

## 🧪 أوضاع التشغيل

| الأمر | النتيجة |
|---|---|
| `--kind asia_open \| europe_open \| us_open \| daily_recap \| breaking` | نوع محدد |
| `--auto` | يختار حسب أقرب افتتاح سوق |
| `--lang ar \| en` | لغة واحدة |
| `--both` | نسختان |
| `--no-video` | سكربت JSON فقط (سريع) |

`OPENAI_API_KEY` (اختياري): يحسّن صياغة السرد تلقائيًا، ويُهمَل بهدوء إن غاب.

---

## 🛠️ استكشاف الأعطال

| المشكلة | الحل |
|---|---|
| مربّعات في النص العربي | ثبّت `libraqm`: `sudo apt install libraqm0` · Pillow يجب أن يكون ≥ 10 |
| «البيانات غير متاحة» | CoinGecko يحد الطلبات — النظام ينتقل تلقائيًا إلى CoinMarketCap ثم Binance |
| صوت طويل > 60 ث | قلّل نص أي مشهد في `scriptwriter.py` أو ارفع `VOICES["ar_rate"]` |
| فيديو لا يفتح | تأكد أن `imageio-ffmpeg` مثبّت (`pip install imageio-ffmpeg`) |
| فشل الترجمة | يعملون على النص الإنجليزي كما هو — لا يتوقف النظام |

---

## 📋 قائمة التحقق قبل النشر

- [ ] الأرقام في الفيديو تطابق `data/script_*.json`
- [ ] الخبر من مصدر معروف (ظاهر على الشاشة)
- [ ] لا وعود أرباح / لا «مضمون»
- [ ] إخلاء المسؤولية موجود
- [ ] الكابشن يحتوي Hook + 3–5 هاشتاجات
- [ ] صوت واضح (اسمع أول 5 ثوان)

---

## ✅ ما لا يفعله النظام (بوعي)

- ❌ لا ينشر إلى TikTok تلقائيًا (سياسة المنصة + حصة رفع).
- ❌ لا يعطي إشارات تداول أو أسعار مستهدفة.
- ❌ لا يستخدم صورًا محمية بحقوق (Wikimedia Commons فقط + صور مولّدة).
- ❌ لا يبني تحليلًا على شائعة بلا مصدر.

---

## 🗺️ خطة التطوير

1. **MVP (جاهز)** — أسعار + رادار + سكربت + فيديو + جدولة.
2. **تحسين جودة** — ترجمة LLM اختيارية، أصوات متعددة، وصفات مشاهد إضافية.
3. **نمو** — A/B لعناوين الـ Hook، تقرير أسبوعي آلي للمؤشرات.
4. **توسّع** — نسخة إنجليزية مستقلة (جمهور مختلف)، إعادة استخدام المحتوى في Reels وShorts.
