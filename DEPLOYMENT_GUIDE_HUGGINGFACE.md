# 🎁 دليل النشر والرفع المجاني 100% على Hugging Face Spaces (بدون فيزا / بدون كارت)

يشرح هذا الدليل كيفية رفع ونشر تطبيق **Enterprise Arabic Exam SaaS (Quiz Maker)** مجاناً بالكامل **بدون الحاجة لبطاقة إئتمان (Credit Card)** وبدون أي اشتراكات مدفوعة باستخدام خيار **Gradio / Python SDK** المتاح مجاناً 100% على Hugging Face Spaces.

---

## 📋 1. متطلبات النشر (Prerequisites)
1. حساب مجاني على موقع [Hugging Face](https://huggingface.co/).
2. تثبيت أداة `git` على جهازك.
3. مفتاح **Gemini API Key** من [Google AI Studio](https://aistudio.google.com/).

---

## 🛠️ 2. خطوات إنشاء الـ Space المجاني على Hugging Face

1. اذهب إلى صفحة **Hugging Face Spaces**: [https://huggingface.co/spaces](https://huggingface.co/spaces)
2. انقر على زر **Create new Space**.
3. ادخل البيانات التالية:
   - **Space name**: أدخل اسماً للمشروع (مثلاً: `arabic-quiz-maker`).
   - **License**: اختر `mit`.
   - **Select the Space SDK**: اختر **Gradio** (مجاني 100% ولا يتطلب بطاقة إئتمان أو خطة مدفوعة).
   - **App file**: اتركها `app.py` (تم إعداده جاهزاً داخل المشروع).
   - **Space hardware**: اختر `CPU basic - free` (مجاني 100%).
   - **Visibility**: اختر `Public` (عام) أو `Private` (خاص).
4. انقر على **Create Space**.

---

## 💻 3. رفع الكود والمشروع عبر Git

افتح مبسط الأوامر (PowerShell أو Terminal) داخل مجلد المشروع الرئيسي:
`C:\Users\Apdulrahman\Desktop\Quiz Maker`

قم بتنفيذ الأوامر التالية بالترتيب (مع استبدال `YOUR_USERNAME` باسم حسابك على Hugging Face و `arabic-quiz-maker` باسم الـ Space):

```bash
# 1. تهيئة مستودع Git محلي
git init

# 2. إضافة جميع ملفات المشروع
git add .

# 3. عمل الحفظ الأولي (Commit)
git commit -m "Deploy Arabic Quiz Maker via Free Gradio Python SDK"

# 4. تغيير اسم الفرع الرئيسي إلى main
git branch -M main

# 5. ربط المستودع بمستودع Hugging Face Spaces
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/arabic-quiz-maker

# 6. دفع رفع الكود إلى Hugging Face
git push -u origin main -f
```

*(تنويه: عند الدفع قد يطلب منك كلمة المرور؛ استخدم Hugging Face Access Token الخاص بحسابك من Settings -> Access Tokens)*.

---

## 🔑 4. إضافة مفتاح البيئة `GEMINI_API_KEY` (Space Secrets)

لتشغيل الذكاء الاصطناعي و RAG تلقائياً على السيرفر:

1. ادخل لصفحة الـ Space الخاصة بك على Hugging Face.
2. انقر على تبويب **Settings** من الشريط العلوي.
3. انزل إلى قسم **Variables and secrets**.
4. انقر على زر **New secret**.
5. ادخل البيانات التالية:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: أدخل مفتاحك الخاص من Gemini (مثال: `AQ.Ab8RN6...`).
6. انقر على **Save**.

---

## 🎉 5. كيف يعمل المشروع مجاناً؟

- قام النظام بتوفير ملف `app.py` وملف `packages.txt` لتثبيت حزم الـ OCR بأسلوب تلقائي عند تشغيل بيئة Python/Gradio الخاصة بـ Hugging Face.
- يقوم السيرفر بتشغيل الواجهة التفاعلية بالكامل فوراً وتوليد امتحانات الـ 20 سؤالاً مجاناً ودون أي رسوم!
