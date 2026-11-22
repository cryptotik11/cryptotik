# 🚀 رفع المشروع إلى GitHub — 3 دقائق

**المستودع:** https://github.com/cryptotik11/cryptotik (فارغ وجاهز ✅)
**الحالة:** لا أملك صلاحية الدفع إليه (لا يوجد اتصال GitHub في هذه الجلسة)، لذا جهّزت لك كل شيء لتفعلها بأمر واحد.

---

## الطريقة أ — سكربت بضغطة واحدة (الأسهل)

### على الحاسوب
```bash
# 1) نزّل الحزمة من Google Drive: cryptotik-ready.zip
# 2) ضعها في مجلد، ثم:
unzip cryptotik-ready.zip
cd cryptotik
git init && git branch -M main
git add -A
git commit -m "نبض الكريبتو: نظام إنتاج فيديو آلي"
git remote add origin https://github.com/cryptotik11/cryptotik.git
git push -u origin main
```

### أو استخدم السكربت الجاهز
```bash
bash push-to-github.sh
```
> يطلب منك اسم المستخدم وكلمة مرور — استخدم **Personal Access Token** لا كلمة السر:
> GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic) → صلاحية `repo` → انسخ التوكن والصقه مكان كلمة المرور.

---

## الطريقة ب — بدون أوامر (من المتصفح فقط)

1. نزّل `cryptotik-ready.zip` من Drive وفك ضغطه.
2. افتح https://github.com/cryptotik11/cryptotik/upload/main
3. اسحب **محتويات** مجلد `cryptotik` (لا المجلد نفسه) وأفلتها.
   ⚠️ مهم: يجب أن تظهر `make.py` و `src/` في الجذر مباشرة.
4. Commit changes.

> ملاحظة: الرفع من المتصفح قد لا يرفع المجلد المخفي `.github/` — إن لم يظهر ملف الـ workflow، أنشئه يدويًا:
> Add file → Create new file → الاسم: `.github/workflows/make-video.yml` → الصق محتواه من الحزمة.

---

## بعد الرفع — 3 خطوات

1. افتح **Actions** → «نبض الكريبتو — توليد الفيديو تلقائيًا» → **Run workflow**
   - mode: `single` · kind: `auto` · lang: `both`
2. انتظر ~3–5 دقائق (يولّد فيديوهين + كابشنات).
3. نزّل النواتج من **Artifacts**.

من الآن يعمل تلقائيًا في: **03:00 / 11:00 / 17:30 / 23:00** بتوقيت اليمن.

### إضافة Drive تلقائيًا (اختياري)
Settings → Secrets and variables → Actions → New repository secret
- `RCLONE_CONF` = محتوى `rclone.conf` بعد `rclone config` على جهازك (أو `base64 -w0 rclone.conf`)

### إضافة تحسين الصياغة بالذكاء الاصطناعي (اختياري)
- `OPENAI_API_KEY` = مفتاحك. بدونه يعمل النظام كما هو.

---

## ما سُيُدفع (26 ملفًا · 1.8MB · بلا أسرار)

```
.github/workflows/make-video.yml   ← الجدولة الآلية
src/  (config, datafeed, newsradar, translate,
       scriptwriter, scenes, voice, videobuild, publish)
make.py · make_week.py
tools/fetch_fonts.py
assets/fonts/  (6 خطوط عربية — مضمّنة)
docs/  (الهوية · دليل تيك توك · دليل التشغيل)
README.md · requirements.txt · .gitignore
```

**تحققت:** لا مفاتيح، لا فيديوهات، لا مجلد renders — تم اختبار الـ commit محليًا ونجح.

---

## تنبيه أمني
المستودع **عام (public)** حاليًا. لا شيء سري بداخله، لكن إن أردت:
Settings → General → Danger Zone → **Change visibility → Private**.

> المهام المجدولة في GitHub تتوقف إذا لم يحدث نشاط 60 يومًا. يكفي فتح Actions وتشغيل يدوي كل شهر، أو تعديل README حرفًا واحدًا.
