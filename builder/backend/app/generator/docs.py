# -*- coding: utf-8 -*-
"""
تولید مستندات بسته خروجی
=========================
README فارسی، راهنمای نصب، معماری، فهرست ماژول‌ها، مدل داده،
قابلیت‌های هوش مصنوعی، مرجع API، راهنمای کاربری و راهنمای بازتولید.
"""

from __future__ import annotations

from typing import Any

from .writers import Package, render

README_TEMPLATE = """# @@app_name_fa@@

**@@tagline@@**

> سامانه یکپارچه برنامه‌ریزی منابع سازمانی (ERP) مخصوص **@@company_name@@** در صنعت
> **@@industry_label@@** — تولیدشده توسط «سازنده ERP هوشمند کارخانه‌ای» نسخه @@version@@.

[![Laravel](https://img.shields.io/badge/Laravel-11-FF2D20?logo=laravel&logoColor=white)](./backend)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](./frontend)
[![Python](https://img.shields.io/badge/AI%20Service-FastAPI-3776AB?logo=python&logoColor=white)](./ai-service)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](./docker-compose.yml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

---

## در یک نگاه

| سنجه | مقدار |
|---|---|
| بخش‌های کاتالوگ فعال | **@@sections_count@@** از ۲۲ |
| ماژول‌های فعال | **@@modules_count@@** |
| زیرماژول‌ها | **@@groups_count@@** |
| زیرمجموعه‌های عملیاتی | **@@items_count@@** |
| نقاط هوش مصنوعی | **@@ai_count@@** |
| موتورهای AI فعال | **@@engines_count@@** |
| جداول پایگاه داده | **@@tables_count@@** |
| فیلدهای داده | **@@fields_count@@** |
| فایل‌های بسته | **@@file_count@@** |
| خط کد تولیدشده | **@@line_count@@** |

## آنچه تحویل می‌گیرید

```
@@slug@@/
├── backend/      لاراول ۱۱ — @@backend_files@@ فایل (مهاجرت، مدل، کنترلر، سیاست، آزمون)
├── frontend/     React ۱۸ + Vite — رابط راست‌به‌چپ با تم تیره صنعتی
├── ai-service/   میکروسرویس FastAPI — @@engines_count@@ موتور هوش مصنوعی
├── deploy/       nginx، systemd، cron و اسکریپت‌های عملیاتی
├── docs/         @@docs_count@@ سند فارسی (معماری، نصب، ماژول‌ها، مدل داده، AI، API)
├── docker-compose.yml   پشته کامل: پایگاه داده، Redis، بک‌اند، صف، زمان‌بند، AI، وب
├── deploy.sh     نصب خودکار با یک دستور
├── Makefile      دستورات مدیریتی روزمره
└── manifest.json شرح کامل بسته (برای بازتولید و ممیزی)
```

## شروع سریع (۵ دقیقه)

```bash
# ۱) استقرار کامل
./deploy.sh

# ۲) باز کردن رابط کاربری
xdg-open http://localhost:@@host_port@@/        # یا مرورگر دلخواه

# ۳) ورود
#    کاربر: @@admin_email@@
#    گذرواژه: @@admin_password@@   ← فوراً تغییر دهید
```

نیازمندی‌ها: Docker + Docker Compose. برای استقرار بدون Docker،
[راهنمای systemd](./docs/02-installation.md) را ببینید.

## معماری سه‌لایه

```
┌────────────────────────────────────────────────────────────┐
│  مرورگر کاربر (RTL، تم تیره)                                │
└───────────────────────────┬────────────────────────────────┘
                            │ HTTPS / JSON
┌───────────────────────────▼────────────────────────────────┐
│  frontend — React 18 + Vite                                │
│  صفحه‌های داده‌محور از روی schema ماژول‌ها                    │
└───────────────────────────┬────────────────────────────────┘
                            │ /api/v1/...  (Sanctum Bearer)
┌───────────────────────────▼────────────────────────────────┐
│  backend — Laravel 11                                      │
│  Controller → FormRequest → Policy → Model → Migration      │
│  Service لایه کسب‌وکار هر ماژول                              │
│  Support: Jalali، PersianText، ModuleRegistry، Audit        │
└──────┬────────────────────────────────────┬────────────────┘
       │ SQL                                │ HTTP (JSON)
┌──────▼──────────────┐          ┌──────────▼─────────────────┐
│  @@db_label@@       │          │  ai-service — FastAPI       │
│  @@tables_count@@ جدول         │  @@engines_count@@ موتور:    │
│  با @@fields_count@@ │          │  پیش‌بینی، بهینه‌سازی،       │
│  فیلد                │          │  ناهنجاری، وایبول، SPC،     │
└─────────────────────┘          │  بینایی، NLP، توصیه،        │
                                 │  شبیه‌سازی، MLOps            │
                                 └──────────┬─────────────────┘
                                            │ (اختیاری)
                                 ┌──────────▼─────────────────┐
                                 │  AvalAI — مدل زبانی بزرگ    │
                                 │  چت، خلاصه‌سازی، استخراج     │
                                 └────────────────────────────┘
```

## ماژول‌های فعال

@@modules_table@@

> فهرست کامل زیرماژول‌ها و زیرمجموعه‌ها: [docs/03-modules.md](./docs/03-modules.md)

## قابلیت‌های هوش مصنوعی

@@engines_table@@

مجموعاً **@@ai_count@@ نقطه هوش مصنوعی** در این استقرار فعال است.
جزئیات هر نقطه (کد، موتور، اندپوینت، الگوریتم‌ها):
[docs/05-ai-capabilities.md](./docs/05-ai-capabilities.md)

### AvalAI

برای قابلیت‌های زبانی (چت‌بات، خلاصه‌سازی گزارش، استخراج بند قرارداد، طبقه‌بندی متن)
کلید `AVALAI_API_KEY` را در `backend/.env` و `ai-service/.env` تنظیم کنید.
**این لایه اختیاری است** — در نبود کلید، همه موتورهای عددی به‌صورت کامل کار می‌کنند
و بخش زبانی از الگوریتم‌های داخلی (TF-IDF، واژه‌نامه احساس، خلاصه‌سازی استخراجی)
استفاده می‌کند.

## ویژگی‌های ایرانیزه‌شده

- ✅ تقویم **شمسی** در همه لایه‌ها (ذخیره میلادی، نمایش شمسی) — کلاس `App\\Support\\Jalali`
- ✅ ارقام **فارسی**، نرمال‌سازی «ي/ك» عربی و جداکننده هزارگان در ورودی فرم‌ها
- ✅ واحد پول **@@currency_label@@** و قالب مبلغ فارسی
- ✅ **سامانه مؤدیان** و صورتحساب الکترونیکی مالیاتی (ماژول F9)
- ✅ شناسه ملی، کد اقتصادی، IBAN و شماره صیاد چک در مدل داده
- ✅ هفته کاری از **شنبه** و تعطیلی **جمعه**
- ✅ منطقه زمانی `@@timezone@@`
- ✅ بیمه و مالیات پیمانکاران، مفاصاحساب و حق بیمه (ماژول U)
- ✅ حقوق و دستمزد با فهرست بیمه، مالیات حقوق و وام کارکنان (ماژول G)

## دستورات پرکاربرد

```bash
make install      # نصب کامل
make status       # وضعیت سرویس‌ها
make logs         # لاگ‌ها
make migrate      # مهاجرت پایگاه داده
make seed         # داده پایه
make test         # آزمون‌های لاراول (@@tests_count@@ فایل آزمون)
make backup       # پشتیبان‌گیری
make health       # بررسی سلامت پشته
make ai-health    # سلامت سرویس هوش مصنوعی
make help         # فهرست همه دستورات
```

## مستندات

| سند | محتوا |
|---|---|
| [معماری سامانه](./docs/01-architecture.md) | لایه‌ها، جریان داده، قراردادهای کدنویسی |
| [راهنمای نصب](./docs/02-installation.md) | Docker، systemd، نصب دستی، عیب‌یابی |
| [فهرست ماژول‌ها](./docs/03-modules.md) | @@modules_count@@ ماژول با زیرماژول‌ها و زیرمجموعه‌ها |
| [مدل داده](./docs/04-data-model.md) | @@tables_count@@ جدول، @@fields_count@@ فیلد، وابستگی‌های خارجی |
| [قابلیت‌های AI](./docs/05-ai-capabilities.md) | @@ai_count@@ نقطه AI، موتورها، اندپوینت‌ها |
| [مرجع API](./docs/06-api-reference.md) | همه مسیرهای REST به تفکیک ماژول |
| [عملیات و استقرار](./docs/07-operations.md) | پشتیبان‌گیری، پایش، ارتقا، امنیت |
| [راهنمای کاربری](./docs/08-user-guide.md) | کار با رابط کاربری برای مدیر و اپراتور |
| [بازتولید بسته](./docs/09-regeneration.md) | تغییر انتخاب و ساخت دوباره با سازنده ERP |

## امنیت

* احراز هویت با **Sanctum** (توکن Bearer) و انقضای قابل تنظیم
* سیاست دسترسی (`Policy`) برای **هر موجودیت** با مجوزهای `<ماژول>.<جدول>.<عملیات>`
* میان‌افزار ممیزی خودکار — همه عملیات نوشتاری در `audit_events` ثبت می‌شود
* نرخ‌محدودی ورود (۵ تلاش ناموفق → قفل ۲ دقیقه‌ای) و قفل حساب پس از ۵ خطا
* اعتبارسنجی سمت سرور با `FormRequest` و پیام‌های فارسی
* سرآیندهای امنیتی nginx و پنهان‌سازی فایل‌های dot
* گذرواژه‌ها با `hashed` cast و هرگز در خروجی API (`$hidden`)

## آزمون

```bash
cd backend && composer install && php artisan test      # @@tests_count@@ فایل آزمون عملکردی
cd ai-service && pip install -r requirements.txt && pytest tests -q
```

آزمون‌ها شامل CRUD، احراز هویت، اعتبارسنجی و حذف نرم برای هر موجودیت،
به‌علاوه آزمون واحد تبدیل تاریخ شمسی و @@ai_tests_count@@ آزمون دود برای موتورهای AI است.

## پشتیبانی و لایسنس

این بسته با مجوز [MIT](./LICENSE) ارائه می‌شود. برای بازتولید با انتخابی متفاوت،
به پلتفرم «سازنده ERP هوشمند» مراجعه کنید: [docs/09-regeneration.md](./docs/09-regeneration.md)

---

<div dir="rtl">

**ساخته‌شده توسط سازنده ERP هوشمند کارخانه‌ای** — نسخه @@version@@،
کاتالوگ @@catalog_version@@، در تاریخ **@@generated_at_jalali@@** (شناسه بسته `@@package_id@@`).

</div>
"""

ARCHITECTURE_DOC = """# معماری سامانه @@app_name_fa@@

> این سند ساختار فنی، جریان داده و قراردادهای کدنویسی بسته تولیدشده را شرح می‌دهد.

## ۱. نمای کلی

سامانه از سه سرویس مستقل تشکیل شده است که با Docker Compose یا systemd
روی یک ماشین اجرا می‌شوند:

| سرویس | فناوری | نقش | پورت |
|---|---|---|---|
| `backend` | PHP 8.3 / Laravel 11 | منطق کسب‌وکار، پایگاه داده، احراز هویت، API | 9000 (php-fpm) |
| `frontend` | React 18 / Vite | رابط کاربری RTL، تم تیره | 80 (از طریق nginx) |
| `ai-service` | Python 3.12 / FastAPI | موتورهای هوش مصنوعی و ثبت مدل‌ها | 8001 |
| `db` | @@db_label@@ | ذخیره‌سازی داده | @@db_port@@ |
| `redis` | Redis 7 | صف، حافظه نهان، نشست | 6379 |
| `web` | nginx 1.27 | سرو SPA + پروکسی API + فایل‌های آپلودشده | @@host_port@@ |

## ۲. لایه‌های بک‌اند

```
درخواست HTTP
   │
   ▼
Middleware (bootstrap/app.php)
   ├─ EnsureApiJsonResponse   تنظیم Accept و شناسه رهگیری درخواست
   ├─ NormalizePersianInput   تبدیل ارقام فارسی و یکدست‌سازی متن
   ├─ auth:sanctum            احراز هویت با توکن
   ├─ EnsureCompanyContext    تعیین شرکت/کارخانه فعال (چندشرکتی)
   ├─ permission:<code>       بررسی مجوز عملیات
   └─ AuditRequestMiddleware  ثبت خودکار عملیات نوشتاری
   │
   ▼
Controller (app/Http/Controllers/Api/<بخش>/)
   │  ── فقط هماهنگی: دریافت، اعتبارسنجی، فراخوانی سرویس، پاسخ
   ▼
FormRequest (app/Http/Requests/<بخش>/)
   │  ── قواعد اعتبارسنجی + پیام‌ها و برچسب‌های فارسی
   ▼
Policy (app/Policies/<بخش>/)
   │  ── مجوز <slug>.<table>.<action>
   ▼
Service (app/Services/<بخش>/)
   │  ── منطق کسب‌وکار، داشبورد ماژول، فراخوانی AI
   ▼
Model (app/Models/<بخش>/)  ←→  Migration (database/migrations/)
   │
   ▼
Resource (app/Http/Resources/<بخش>/)   خروجی JSON با تاریخ شمسی
```

### قراردادهای کدنویسی

* **فضای‌نام بر اساس بخش کاتالوگ**: `App\\Models\\Manufacturing\\...`،
  `App\\Models\\Quality\\...` — نگاشت کامل در [مدل داده](./04-data-model.md)
* **یک Policy به ازای هر موجودیت** با نگاشت صریح در `PolicyServiceProvider`
  (چون مدل‌ها در زیرفضای‌نام‌ها هستند و کشف خودکار لاراول کافی نیست)
* **SoftDeletes** برای همه موجودیت‌های کسب‌وکاری (قابل بازیابی)
* **`company_id`** روی همه جداول در حالت چندشرکتی (جداسازی داده کارخانه‌ها)
* **ستون‌های `ai_*`** برای نتایج هوش مصنوعی روی جداول مرتبط
  (مثل `ai_anomaly_flag`، `ai_risk_prediction`، `ai_suggested_price`)
* **ارجاع اسناد مالی** با `journal_entry_id` به دفتر کل

## ۳. لایه پشتیبانی (`app/Support`)

| کلاس | مسئولیت |
|---|---|
| `Jalali` | تبدیل میلادی ↔ شمسی (الگوریتم jalaali، بدون وابستگی خارجی) |
| `PersianText` | ارقام فارسی، نرمال‌سازی متن، قالب مبلغ، شماره‌گذاری اسناد |
| `AvalAiClient` | کلاینت AvalAI (چت، JSON، خلاصه، استخراج، طبقه‌بندی، امبدینگ) |
| `AiServiceClient` | کلاینت میکروسرویس پایتون با پاسخ جایگزین خودکار |
| `ActivityLogger` | ثبت رویداد ممیزی با تابع کمکی `activity()` |
| `ModuleRegistry` | رجیستری ماژول‌های فعال، منوی پویا، آمار استقرار |
| `helpers.php` | توابع سراسری: `activity()`، `jalali()`، `money_fa()`، `erp_feature_enabled()` |

## ۴. جریان داده هوش مصنوعی

```
کاربر در رابط کاربری
   │  کلیک روی ویجت 🤖 AI
   ▼
POST /api/v1/ai/capabilities/{code}        ← لاراول (AiController)
   │  کد قابلیت از config/ai.php خوانده می‌شود
   ▼
AiServiceClient::call(endpoint, payload)   ← HTTP به سرویس پایتون
   │
   ▼
ai-service: /ai/<engine>                    ← موتور مربوطه
   │  numpy / pandas / scikit-learn
   │  اگر مدل آموزش‌دیده لازم است: models/store.py
   ▼
پاسخ: { ok, result, metrics, explanation }  ← توضیح فارسی برای کاربر
   │
   ├─ ثبت در ai_prediction_logs (پایش MLOps)
   └─ اگر سرویس در دسترس نبود: fallback با توضیح و پیشنهاد قاعده‌محور
```

برای وظایف زبانی، `AiController` مستقیماً با `AvalAiClient` کار می‌کند
(چت، خلاصه‌سازی، استخراج بند، طبقه‌بندی، بینش متنی).

**اصل طراحی**: هیچ جریان کاری تولید به‌خاطر در دسترس نبودن AI متوقف نمی‌شود.

## ۵. رابط کاربری

* **داده‌محور**: `src/config/menu.js` شامل ماژول‌ها، موجودیت‌ها و طرحواره
  @@fields_count@@ فیلد با برچسب فارسی، نوع و گزینه‌های enum است.
  `EntityPage.jsx` از همین طرحواره جدول، فرم و اعتبارسنجی می‌سازد.
* **کتابخانه UI داخلی** (بدون وابستگی خارجی): `DataTable`، `Form`، `Modal`،
  `Charts` (Line، Bar، Donut، Sparkline، ControlChart با SVG)، `AiWidget`
* **کنترل دسترسی در رابط**: `hasPermission('<slug>.<table>.<action>')`
* **RTL و تم تیره** با متغیرهای CSS در `styles/global.css`
* **تاریخ شمسی** در سمت کلاینت (`lib/format.js`) برای پایداری در حالت آفلاین

## ۶. داده و ماندگاری

| حجم Docker | محتوا |
|---|---|
| `@@slug@@_db-data` | داده پایگاه @@db_label@@ |
| `@@slug@@_redis-data` | صف، کش و نشست‌ها |
| `@@slug@@_backend-storage` | فایل‌های آپلودشده، اسناد، پشتیبان‌ها |
| `@@slug@@_ai-models` | مدل‌های آموزش‌دیده (pickle) + لاگ پیش‌بینی |

## ۷. مقیاس‌پذیری

* **افقی**: سرویس `app` بدون وضعیت است → افزودن نمونه پشت nginx
* **صف**: کارگر `queue` مستقل است → `docker compose up -d --scale queue=4`
* **AI**: سرویس `ai-service` مستقل و بدون وضعیت (مدل‌ها روی حجم مشترک)
* **پایگاه داده**: در بار بالا، انتقال به PostgreSQL خوشه‌ای یا MySQL Replica
* **جداسازی**: امکان اجرای `ai-service` روی ماشین دارای GPU با تغییر
  `AI_SERVICE_URL` در `backend/.env`

## ۸. آزمون و کیفیت

* @@tests_count@@ فایل آزمون عملکردی لاراول (CRUD، احراز هویت، اعتبارسنجی، حذف نرم)
* آزمون واحد `JalaliTest` برای صحت تبدیل تاریخ شمسی
* @@ai_tests_count@@ آزمون دود سرویس AI با داده نمونه کارخانه ایرانی
* پایپ‌لاین پیشنهادی CI در `docs/07-operations.md`

## ۹. تصمیم‌های طراحی

| تصمیم | دلیل |
|---|---|
| لاراول ۱۱ به‌جای میکروسرویس کامل | سرعت توسعه، اکوسیستم بالغ، تیم‌های ERP ایران آشنا هستند |
| سرویس AI جدا (پایتون) | کتابخانه‌های علمی فقط در پایتون بالغ و آماده‌اند؛ مقیاس مستقل |
| بدون ORM سنگین در AI | داده از API لاراول می‌آید؛ سرویس AI بی‌حالت می‌ماند |
| SPA داده‌محور | افزودن ماژول جدید بدون نوشتن صفحه جدید |
| AvalAI اختیاری | استقرار در شبکه داخلی بدون اینترنت هم ممکن باشد |
| تاریخ میلادی در DB، شمسی در نمایش | سازگاری با استانداردها و محاسبات بازه |
| رجیستری قابلیت‌ها (`system_features`) | کنترل مجوز و منو بر اساس آنچه واقعاً فعال شده |
"""

INSTALLATION_DOC = """# راهنمای نصب و راه‌اندازی @@app_name_fa@@

## پیش‌نیازها

### روش Docker (توصیه‌شده)

| نرم‌افزار | نسخه حداقل |
|---|---|
| Docker Engine | 24.0 |
| Docker Compose | v2.20 |
| فضای دیسک | ۶ گیگابایت آزاد |
| حافظه | ۴ گیگابایت (۸ گیگابایت برای تولید) |

### روش نصب دستی

| نرم‌افزار | نسخه |
|---|---|
| PHP | 8.3 (افزونه‌ها: bcmath، gd، intl، mbstring، pdo_@@db_ext@@، zip) |
| Composer | 2.7 |
| Node.js | 20 LTS |
| Python | 3.12 |
| @@db_label@@ | @@db_version@@ |
| Redis | 7 (اختیاری) |
| nginx | 1.24+ |

---

## روش ۱ — Docker (یک دستور)

```bash
cd @@slug@@
./deploy.sh
```

اسکریپت به‌ترتیب این کارها را انجام می‌دهد:

1. بررسی نصب Docker و Compose
2. ساخت `backend/.env` از `.env.example` و تولید `APP_KEY`
3. ساخت تصویرها (`backend`، `web`، `ai-service`)
4. راه‌اندازی سرویس‌ها (`db`، `redis`، `app`، `queue`، `scheduler`، `ai-service`، `web`)
5. انتظار برای آماده‌شدن لاراول
6. اجرای `php artisan erp:install` → مهاجرت + نقش‌ها/مجوزها + کاربر مدیر + رجیستری قابلیت‌ها
7. نمایش نشانی‌ها و اطلاعات ورود

### نصب با داده نمونه

```bash
./deploy.sh --demo
```

### سایر دستورات

```bash
./deploy.sh --status     # وضعیت کانتینرها
./deploy.sh --logs       # دنبال‌کردن لاگ‌ها
./deploy.sh --restart    # راه‌اندازی مجدد
./deploy.sh --stop       # توقف پشته
./deploy.sh --no-cache   # ساخت مجدد بدون کش
```

### تغییر پورت میزبان

```bash
ERP_PORT=9090 ./deploy.sh
# یا ویرایش ERP_PORT در فایل .env ریشه
```

---

## روش ۲ — نصب دستی (بدون Docker)

### گام ۱: پایگاه داده

```sql
CREATE DATABASE @@db_database@@ CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER '@@db_username@@'@'%' IDENTIFIED BY '@@db_password@@';
GRANT ALL PRIVILEGES ON @@db_database@@.* TO '@@db_username@@'@'%';
FLUSH PRIVILEGES;
```

### گام ۲: بک‌اند

```bash
cd backend
composer install --no-dev --optimize-autoloader
cp .env.example .env
php artisan key:generate

# ویرایش .env: DB_*, APP_URL, MAIL_*, AVALAI_API_KEY (اختیاری)

php artisan erp:install          # مهاجرت + داده پایه + مدیر + قابلیت‌ها
php artisan storage:link
php artisan config:cache && php artisan route:cache
```

### گام ۳: سرویس هوش مصنوعی

```bash
cd ../ai-service
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env             # در صورت نیاز AVALAI_API_KEY را تنظیم کنید
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
```

بررسی: `curl http://localhost:8001/health`

### گام ۴: رابط کاربری

```bash
cd ../frontend
npm install
npm run build
sudo mkdir -p /var/www/@@slug@@
sudo cp -r dist/* /var/www/@@slug@@/
```

### گام ۵: nginx

```bash
sudo cp deploy/nginx/erp.conf /etc/nginx/conf.d/@@slug@@.conf
# ویرایش: root /var/www/@@slug@@; و مسیر fastcgi به php-fpm محلی
sudo nginx -t && sudo systemctl reload nginx
```

برای HTTPS:

```bash
sudo certbot --nginx -d erp.example.com --redirect
```

### گام ۶: سرویس‌های پس‌زمینه

```bash
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now erp-backend erp-ai erp-queue
crontab deploy/crontab.txt
```

---

## ورود اولیه

| فیلد | مقدار |
|---|---|
| نشانی | `http://<میزبان>:@@host_port@@/` |
| نام کاربری | `admin` یا `@@admin_email@@` |
| گذرواژه | `@@admin_password@@` |

> ⚠️ **فوراً گذرواژه را تغییر دهید**: *تنظیمات → تغییر گذرواژه*.
> تغییر گذرواژه همه نشست‌های دیگر را خارج می‌کند.

---

## عیب‌یابی

| نشانه | علت احتمالی | راه‌حل |
|---|---|---|
| صفحه سفید پس از ورود | بیلد frontend انجام نشده | `cd frontend && npm run build` |
| خطای ۵۰۰ روی `/api` | `APP_KEY` خالی یا کش قدیمی | `php artisan key:generate && php artisan optimize:clear` |
| «نشست شما پایان یافته» | توکن منقضی یا `SANCTUM_STATEFUL_DOMAINS` نادرست | ورود مجدد + اصلاح دامنه در `.env` |
| مهاجرت با خطای FK | ترتیب اجرا دستکاری شده | `php artisan migrate:fresh --force` (فقط نصب اولیه) |
| ویجت AI خطا می‌دهد | سرویس `ai-service` بالا نیامده | `docker compose logs ai-service` و `make ai-health` |
| پاسخ‌های زبانی خالی است | `AVALAI_API_KEY` تنظیم نشده | کلید را در `.env` بگذارید یا از حالت داخلی استفاده کنید |
| تاریخ شمسی اشتباه | `APP_TIMEZONE` نادرست | `Asia/Tehran` تنظیم و `config:cache` اجرا شود |
| خطای CORS در توسعه | پروکسی Vite غیرفعال | `npm run dev` را با `VITE_PROXY_TARGET` درست اجرا کنید |
| صف کار نمی‌کند | کارگر `queue` متوقف شده | `docker compose restart queue` |

### لاگ‌های مفید

```bash
docker compose logs -f app           # لاراول
docker compose logs -f ai-service    # موتورهای AI
docker compose logs -f web           # nginx
tail -f backend/storage/logs/ai.log      # رویدادهای AI
tail -f backend/storage/logs/audit.log   # ممیزی
```

---

## نصب در شبکه داخلی (بدون اینترنت)

1. روی ماشین دارای اینترنت: `docker compose build` و سپس
   `docker save @@slug@@/backend:@@version@@ @@slug@@/web:@@version@@ @@slug@@/ai-service:@@version@@ -o erp-images.tar`
2. انتقال `erp-images.tar` و پوشه بسته به سرور مقصد
3. `docker load -i erp-images.tar`
4. `docker compose up -d --no-build` و سپس `docker compose exec app php artisan erp:install`

بدون کلید AvalAI، همه قابلیت‌های عددی AI کار می‌کنند و بخش زبانی
به‌صورت داخلی (بدون اینترنت) پاسخ می‌دهد.
"""

MODULES_DOC = """# فهرست ماژول‌های فعال — @@app_name_fa@@

این سند **@@modules_count@@ ماژول** فعال در این استقرار را با زیرماژول‌ها،
تعداد زیرمجموعه‌ها، جداول داده و نقاط هوش مصنوعی فهرست می‌کند.

| سنجه | مقدار |
|---|---|
| بخش‌های کاتالوگ | @@sections_count@@ |
| ماژول‌ها | @@modules_count@@ |
| زیرماژول‌ها | @@groups_count@@ |
| زیرمجموعه‌ها | @@items_count@@ |
| نقاط هوش مصنوعی | @@ai_count@@ |
| جداول داده | @@tables_count@@ |

---

## فهرست بخش‌ها

@@sections_table@@

---

## جزئیات ماژول‌ها

@@modules_detail@@
"""

DATA_MODEL_DOC = """# مدل داده — @@app_name_fa@@

**@@tables_count@@ جدول** با **@@fields_count@@ فیلد** در این استقرار ساخته می‌شود.
مهاجرت‌ها در `backend/database/migrations/` با ترتیب توپولوژیک
(جدول والد پیش از فرزند) شماره‌گذاری شده‌اند.

## قراردادهای سراسری

| قاعده | توضیح |
|---|---|
| کلید اصلی | `id` از نوع `BIGINT AUTO_INCREMENT` |
| مهر زمانی | `created_at` و `updated_at` روی همه جداول |
| حذف نرم | `deleted_at` (SoftDeletes) برای موجودیت‌های کسب‌وکاری |
| چندشرکتی | `company_id` برای جداسازی داده کارخانه‌ها |
| مالکیت | `owner_id` و `department_id` برای سطح دسترسی داده‌ای |
| وضعیت | ستون `status` از نوع `enum` با مقدار پیش‌فرض و ایندکس |
| پیوست | ستون `attachments` از نوع `json` |
| ویژگی‌های باز | ستون `attributes` از نوع `json` برای فیلدهای سفارشی |
| ستون‌های AI | با پیشوند `ai_` (مثل `ai_anomaly_flag`، `ai_risk_prediction`) |
| اسناد مالی | `journal_entry_id` برای ارتباط با دفتر کل |

## انواع داده به‌کاررفته

@@types_table@@

---

## جدول‌ها به تفکیک بخش

@@tables_by_section@@

---

## ترتیب مهاجرت‌ها (توپولوژیک)

نخستین @@topo_sample_count@@ جدول که پیش از بقیه ساخته می‌شوند:

@@topo_list@@

## نمودار وابستگی‌های کلیدی

@@fk_summary@@

## آمار فیلدها

@@field_stats@@

---

> برای دیدن تعریف کامل هر جدول، فایل مهاجرت متناظر را در
> `backend/database/migrations/` و مدل Eloquent را در
> `backend/app/Models/<بخش>/` ببینید.
"""

AI_DOC = """# قابلیت‌های هوش مصنوعی — @@app_name_fa@@

**@@ai_count@@ نقطه هوش مصنوعی** در **@@engines_count@@ موتور** فعال است.

## موتورهای فعال

@@engines_table@@

## نحوه کارکرد

1. هر نقطه AI در کاتالوگ یک `model_id` و `feature_flag` دارد
   (در `config/ai.php` و رجیستری `system_features`).
2. لاراول از طریق `App\\Support\\AiServiceClient` به سرویس پایتون درخواست می‌دهد.
3. سرویس پایتون الگوریتم مربوطه را اجرا و پاسخ را با `explanation` فارسی برمی‌گرداند.
4. نتیجه در `ai_prediction_logs` ثبت می‌شود (برای پایش MLOps و محاسبه رانش).
5. اگر سرویس در دسترس نباشد، پاسخ `fallback=true` با پیشنهاد قاعده‌محور برمی‌گردد.

## اندپوینت‌های سرویس AI

| مسیر | موتور | ورودی کلیدی | خروجی |
|---|---|---|---|
@@engine_endpoints@@

### اندپوینت‌های مدیریتی

| مسیر | کاربرد |
|---|---|
| `GET /health` | سلامت سرویس، فهرست موتورها، تعداد مدل‌ها |
| `GET /capabilities` | رجیستری قابلیت‌های فعال به تفکیک موتور |
| `GET /capabilities/{code}` | جزئیات یک قابلیت |
| `POST /models/train` | آموزش و ثبت مدل جدید |
| `POST /models/{id}/predict` | پیش‌بینی با مدل ثبت‌شده |
| `GET /models` | فهرست مدل‌های رجیستری |
| `DELETE /models/{id}` | حذف مدل |

## فهرست نقاط AI به تفکیک ماژول

@@ai_by_module@@

## الگوریتم‌های پیاده‌سازی‌شده

### پیش‌بینی (forecasting)
* هموارسازی نمایی هالت (سطح + روند)
* هالت-وینترز فصلی با برآورد مؤلفه فصلی
* میانگین متحرک فصلی (seasonal naive)
* رگرسیون Ridge روی ویژگی زمان (در صورت دسترسی به scikit-learn)
* بازآزمون خودکار با MAPE و RMSE و انتخاب بهترین روش

### قابلیت اطمینان (reliability)
* برازش وایبول دوپارامتری با بیشینه درستنمایی (Newton-Raphson)
* MTBF، MTTR، دسترس‌پذیری، عمر B10 و B50
* عمر باقی‌مانده (RUL) بر اساس سن فعلی
* نرخ خرابی لحظه‌ای و امتیاز ریسک

### بهینه‌سازی (optimization)
* EOQ، ذخیره اطمینان و نقطه سفارش با سطح خدمت دلخواه
* زمان‌بندی تک‌ماشینه با قواعد SPT/LPT/EDD/CR/Priority
* جست‌وجوی محلی (جابه‌جایی جفتی) برای بهبود برنامه
* تخصیص منابع حریصانه بر اساس نسبت ارزش/هزینه

### تشخیص ناهنجاری (anomaly)
* Z-score چندمتغیره با شناسایی ویژگی‌های محرک
* IQR برای دنباله‌های یک‌متغیره
* IsolationForest برای داده جدولی

### کنترل کیفیت آماری (quality_spc)
* نمودار X-bar/R با ضرایب استاندارد A2، D3، D4، D2
* نمودار p برای داده شمارشی
* قواعد غربال الکتریکی نلسون (۵ قاعده پیاده‌سازی‌شده)
* شاخص قابلیت Cp، CpK، CPU، CPL و برآورد PPM

### بینایی ماشین (computer_vision)
* طبقه‌بندی عیب بر اساس شاخص‌های استخراج‌شده از تصویر
  (زبری سطح، درخشش، عمق فرورفتگی، اختلاف رنگ، طول ترک)
* قواعد آستانه‌ای برای انواع عیب (خط‌وخش، فرورفتگی، تغییر رنگ، ترک، پلیسه)
* آموزش RandomForest روی نمونه‌های برچسب‌دار

### پردازش زبان طبیعی (nlp)
* نرمال‌سازی فارسی (ارقام، «ي/ك»، نیم‌فاصله)
* ریشه‌یابی ساده با حذف پسوندها و فهرست توقف‌واژه‌های صنعتی
* TF-IDF داخلی، استخراج کلیدواژه، شباهت کسینوسی، خوشه‌بندی
* تحلیل احساس با واژه‌نامه صنعتی فارسی
* خلاصه‌سازی استخراجی + اختیاری با AvalAI

### توصیه‌گر (recommendation)
* شباهت کسینوسی محتوا-محور
* فیلتر همکاری کاربر-کاربر با امتیازدهی وزنی
* قواعد هم‌رخدادی (حمایت، اطمینان، lift)

### شبیه‌سازی (simulation)
* مونت‌کارلو ظرفیت با توزیع بتا برای دسترس‌پذیری خطوط
* شبیه‌سازی صف با ورود پواسون و خدمت گاما
* مونت‌کارلو روی دنباله با VaR و احتمال کاهش

### MLOps (mlops)
* شاخص پایداری جمعیت (PSI) برای تشخیص رانش
* آماره کولموگروف-اسمیرنف دو نمونه‌ای
* رجیستری مدل با لاگ رویدادها (JSONL)
* سیاست بازآموزی بر اساس آستانه رانش

### طبقه‌بندی (classification)
* خط لوله TF-IDF + رگرسیون لجستیک برای متن
* RandomForest برای داده جدولی با استانداردسازی
* گزارش دقت، F1 ماکرو، ماتریس درهم‌آمیگی و اهمیت ویژگی‌ها
* اعتبارسنجی متقاطع و خط پایه فراوانی

## AvalAI (لایه اختیاری زبانی)

| قابلیت | اندپوینت لاراول | کاربرد در کارخانه |
|---|---|---|
| چت | `POST /api/v1/ai/chat` | دستیار اپراتور و مدیر |
| خلاصه‌سازی | `POST /api/v1/ai/summarize` | گزارش شیفت، عدم انطباق، رخداد نت |
| استخراج | `POST /api/v1/ai/extract` | بند قرارداد، تعهدات، مبالغ، تضامین |
| طبقه‌بندی | `POST /api/v1/ai/classify` | دسته‌بندی تیکت، علت توقف، نوع عیب |
| بینش متنی | `POST /api/v1/ai/insight` | تحلیل شاخص‌های داشبورد به زبان ساده |

فعال‌سازی: تنظیم `AVALAI_API_KEY` در `backend/.env` و `ai-service/.env`.

## پایش کیفیت مدل‌ها

```bash
# از طریق لاراول
php artisan erp:ai:health

# از طریق سرویس AI
curl -X POST http://localhost:8001/ai/mlops \\
  -H 'Content-Type: application/json' \\
  -d '{"options": {"task": "drift", "reference": [...]}, "series": [...]}'
```

اگر `psi` از آستانه (`DRIFT_PSI_THRESHOLD`، پیش‌فرض ۰٫۲۵) عبور کند،
پاسخ شامل `retraining_required: true` و اقدام پیشنهادی است.
"""

API_DOC = """# مرجع API — @@app_name_fa@@

همه مسیرها با پیشوند `/api` و قالب JSON هستند. احراز هویت با توکن **Sanctum**
(سرآیند `Authorization: Bearer <token>`) انجام می‌شود.

## قرارداد پاسخ

```json
{
  "data": [ ... ],
  "meta": { "current_page": 1, "last_page": 4, "per_page": 25, "total": 96 }
}
```

خطاها:

```json
{ "message": "شرح فارسی خطا", "status": 422, "errors": { "field": ["قاعده نقض‌شده"] } }
```

## پارامترهای مشترک فهرست‌ها

| پارامتر | نوع | توضیح |
|---|---|---|
| `q` | string | جست‌وجوی متنی روی فیلدهای searchable |
| `status` | string | فیلتر وضعیت |
| `page` | int | شماره صفحه |
| `per_page` | int | تعداد در صفحه (حداکثر ۲۰۰) |
| `sort_by` | string | ستون مرتب‌سازی |
| `sort_dir` | `asc`/`desc` | جهت مرتب‌سازی |

سرآیند اختیاری `X-Company-Id` برای انتخاب شرکت/کارخانه فعال در استقرار چندشرکتی.

---

## ۱. احراز هویت

| متد | مسیر | توضیح |
|---|---|---|
| POST | `/api/v1/auth/login` | ورود و دریافت توکن |
| POST | `/api/v1/auth/logout` | خروج و حذف توکن جاری |
| GET | `/api/v1/auth/me` | کاربر جاری + نقش‌ها + مجوزها + منو |
| PUT | `/api/v1/auth/profile` | به‌روزرسانی پروفایل |
| POST | `/api/v1/auth/password` | تغییر گذرواژه |
| GET | `/api/v1/health` | سلامت سرویس (بدون احراز هویت) |

**نمونه ورود**

```bash
curl -X POST http://localhost:@@host_port@@/api/v1/auth/login \\
  -H 'Content-Type: application/json' \\
  -d '{"login": "@@admin_email@@", "password": "@@admin_password@@"}'
```

## ۲. سامانه و رجیستری

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/v1/dashboard` | داشبورد فرماندهی (کارت‌ها، هشدارها، سلامت AI) |
| GET | `/api/v1/modules` | ماژول‌های فعال + منوی گروه‌بندی‌شده + آمار |
| GET | `/api/v1/features` | رجیستری قابلیت‌ها (`?module=A1&ai_only=1&q=...`) |
| GET | `/api/v1/permissions` | مجوزهای تعریف‌شده به تفکیک ماژول |
| GET | `/api/v1/audit-events` | گزارش ممیزی (`?user_id=&module=&from=&to=`) |

## ۳. گزارش‌ساز

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/v1/reports/tables` | جدول‌های قابل گزارش‌گیری |
| POST | `/api/v1/reports/aggregate` | تجمیع (count/sum/avg/max/min) با گروه‌بندی |
| POST | `/api/v1/reports/export` | خروجی CSV با فیلتر جست‌وجو |

**نمونه تجمیع**

```bash
curl -X POST http://localhost:@@host_port@@/api/v1/reports/aggregate \\
  -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' \\
  -d '{"table": "@@sample_table@@", "metric": "sum", "column": "amount", "group_by": "status"}'
```

## ۴. هوش مصنوعی

| متد | مسیر | توضیح |
|---|---|---|
| GET | `/api/v1/ai/engines` | موتورهای فعال + سلامت سرویس AI |
| GET | `/api/v1/ai/capabilities` | قابلیت‌های فعال به تفکیک موتور |
| POST | `/api/v1/ai/capabilities/{code}` | اجرای یک قابلیت (مثل `A1.3.4`) |
| POST | `/api/v1/ai/models/{modelId}/train` | آموزش مدل |
| POST | `/api/v1/ai/chat` | گفت‌وگو با دستیار (AvalAI یا داخلی) |
| POST | `/api/v1/ai/summarize` | خلاصه‌سازی متن |
| POST | `/api/v1/ai/extract` | استخراج ساختار از متن قرارداد |
| POST | `/api/v1/ai/classify` | طبقه‌بندی متن در برچسب‌ها |
| POST | `/api/v1/ai/insight` | بینش متنی روی شاخص‌ها |

## ۵. منابع ماژول‌ها

هر موجودیت این مسیر‌ها را دارد (الگوی REST):

| متد | مسیر | مجوز لازم |
|---|---|---|
| GET | `/api/v1/<module_slug>/<table>` | `<module_slug>.<table>.view` |
| POST | `/api/v1/<module_slug>/<table>` | `<module_slug>.<table>.create` |
| GET | `/api/v1/<module_slug>/<table>/{id}` | `<module_slug>.<table>.view` |
| PUT/PATCH | `/api/v1/<module_slug>/<table>/{id}` | `<module_slug>.<table>.edit` |
| PATCH | `/api/v1/<module_slug>/<table>/{id}/status` | `<module_slug>.<table>.edit` |
| DELETE | `/api/v1/<module_slug>/<table>/{id}` | `<module_slug>.<table>.delete` |
| GET | `/api/v1/<module_slug>/dashboard` | ورود به سامانه |

---

@@module_endpoints@@

---

## کدهای وضعیت

| کد | معنا در این سامانه |
|---|---|
| 200 | موفق |
| 201 | رکورد ایجاد شد |
| 401 | احراز هویت لازم است / توکن نامعتبر |
| 403 | مجوز عملیات وجود ندارد |
| 404 | منبع یا قابلیت یافت نشد |
| 422 | اعتبارسنجی ناموفق (با `errors` فارسی) |
| 429 | نرخ درخواست بیش از حد (۱۲۰ در دقیقه) |
| 500 | خطای سرور (با `trace_id`) |

## نرخ محدودسازی

`120` درخواست در دقیقه برای هر کاربر روی مسیرهای API
(قابل تغییر در `bootstrap/app.php` → `throttleApi`).
"""

OPERATIONS_DOC = """# عملیات و نگهداشت — @@app_name_fa@@

## پایش سلامت

```bash
make health              # بررسی رابط کاربری، API، مسیر لاراول و سرویس AI
make status              # وضعیت کانتینرها
make ai-health           # سلامت موتورهای AI و AvalAI
```

اندازه‌گیری‌های کلیدی:

| سنجه | مسیر | آستانه پیشنهادی |
|---|---|---|
| سلامت API | `/api/v1/health` | ۲۰۰ در کمتر از ۵۰۰ms |
| سلامت AI | `ai-service:/health` | `ok: true` |
| عمق صف | `SELECT COUNT(*) FROM jobs` | کمتر از ۱۰۰۰ |
| فضای دیسک | `df -h` | بالای ۲۰٪ آزاد |
| اندازه لاگ | `backend/storage/logs/` | کمتر از ۲GB |

## پشتیبان‌گیری

```bash
make backup                            # دستی
./deploy/scripts/backup.sh             # معادل
```

* زمان‌بندی خودکار: `@@backup_cron@@` (در `deploy/crontab.txt`)
* محل: `backups/<سال>/<ماه>/@@slug@@-<مهرزمانی>.tar.gz`
* محتوا: dump فشرده پایگاه داده، `.env`، `manifest.json`، `docker-compose.yml`
* نگهداری: ۱۰ نسخه آخر + حذف خودکار فایل‌های قدیمی‌تر از @@backup_keep_days@@ روز

### بازیابی

```bash
tar -xzf backups/@@slug@@-<مهرزمانی>.tar.gz -C /tmp/restore
docker compose exec -T db psql -U @@db_username@@ @@db_database@@ < /tmp/restore/db/*.sql
cp /tmp/restore/backend.env backend/.env
docker compose restart
```

## ارتقا

```bash
./deploy/scripts/update.sh
```

ترتیب: پشتیبان‌گیری → مهاجرت → همگام‌سازی رجیستری قابلیت‌ها → پاک‌سازی کش → راه‌اندازی مجدد.

## کار با صف و زمان‌بند

| سرویس | مسئولیت | راه‌اندازی مجدد |
|---|---|---|
| `queue` | پردازش کارهای پس‌زمینه (ایمیل، گزارش، AI) | `docker compose restart queue` |
| `scheduler` | اجرای وظایف زمان‌بندی‌شده هر دقیقه | `docker compose restart scheduler` |

وظایف زمان‌بندی‌شده (در `routes/console.php`):

* `erp:backup` — @@backup_cron@@
* `queue:prune-batches` — هر ساعت
* `queue:prune-failed` — روزانه
* `sanctum:prune-expired` — روزانه
* `erp:ai:health` — هر ساعت
* `model:prune` — روزانه

## امنیت عملیاتی

| موضوع | اقدام |
|---|---|
| گذرواژه مدیر | تغییر فوری پس از نصب (از رابط کاربری) |
| `APP_DEBUG` | در تولید حتماً `false` |
| HTTPS | `certbot --nginx` و هدایت اجباری |
| پورت پایگاه داده | در تولید از `docker-compose.yml` حذف شود |
| کلید AvalAI | فقط در `.env`؛ هرگز در مخزن کد |
| به‌روزرسانی تصویرها | ماهانه `docker compose build --pull` |
| ممیزی | بررسی هفتگی `/api/v1/audit-events` برای عملیات حساس |
| پشتیبان `.env` | جداگانه و رمزنگاری‌شده نگهداری شود |

## پایپ‌لاین پیشنهادی CI/CD

```yaml
# .github/workflows/erp.yml (نمونه)
name: ERP Quality Gate
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with: { php-version: '8.3', extensions: bcmath, intl, pdo_sqlite }
      - run: cd backend && composer install --prefer-dist --no-progress
      - run: cd backend && php artisan test
  ai:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: cd ai-service && pip install -r requirements.txt pytest
      - run: cd ai-service && pytest tests -q
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm install && npm run build
```

## مقیاس‌پذیری افقی

```bash
# افزودن کارگر صف
docker compose up -d --scale queue=4 --no-recreate

# افزودن نمونه بک‌اند (نیاز به بارگذار متعادل بیرونی)
docker compose up -d --scale app=3
```

برای بیش از ۵۰۰ کاربر همزمان:
1. انتقال پایگاه داده به سرویس مدیریت‌شده
2. فعال‌سازی Redis برای نشست و کش (`CACHE_STORE=redis`, `SESSION_DRIVER=redis`)
3. جداسازی `ai-service` روی ماشین اختصاصی
4. افزودن nginx به‌عنوان بارگذار متعادل با چند نمونه `app`

## عیب‌یابی پیشرفته

```bash
# اجرای دستور artisan
docker compose exec app php artisan tinker

# مشاهده مسیرهای ثبت‌شده
docker compose exec app php artisan route:list --path=api/v1 | head -50

# بررسی مهاجرت‌ها
docker compose exec app php artisan migrate:status

# پاک‌سازی کامل کش
docker compose exec app php artisan optimize:clear

# آمار سرویس AI
docker compose exec ai-service curl -s localhost:8001/health | python3 -m json.tool
```
"""

USER_GUIDE_DOC = """# راهنمای کاربری @@app_name_fa@@

این راهنما برای **مدیران، سرپرستان و اپراتورهای کارخانه** نوشته شده است.

## ورود به سامانه

1. نشانی سامانه را در مرورگر باز کنید (کروم یا اج نسخه جدید توصیه می‌شود).
2. نام کاربری، ایمیل یا شماره همراه و گذرواژه را وارد کنید.
3. پس از ورود، داشبورد فرماندهی نمایش داده می‌شود.

> اگر پیام «تعداد تلاش‌های ناموفق بیش از حد مجاز» دیدید، ۲ دقیقه صبر کنید
> یا از مدیر سامانه درخواست بررسی حساب (احتمال قفل شدن) داشته باشید.

## آشنایی با چیدمان

```
┌───────────────────────────────┬──────────────────────────────────┐
│  نوار کناری                   │  سربرگ: تاریخ شمسی، کاربر، خروج   │
│  ─ داشبورد فرماندهی           ├──────────────────────────────────┤
│  ─ ماژول‌ها                    │                                  │
│  ─ مرکز هوش مصنوعی             │        محتوای صفحه                │
│  ─ گزارش‌ساز                   │                                  │
│  ─ ممیزی                      │                                  │
│  ─ تنظیمات                    │                                  │
│  ─ گروه‌های ماژول (تولید،      │                                  │
│     کیفیت، مالی، ...)         │                                  │
└───────────────────────────────┴──────────────────────────────────┘
```

* عدد کنار هر ماژول، تعداد **نقاط هوش مصنوعی** آن ماژول است.
* در نمایشگرهای کوچک، منو با دکمه ☰ باز می‌شود.

## داشبورد فرماندهی

* **کارت‌های شاخص**: تعداد رکوردهای کلیدی (کالاها، دستورهای کار، سفارش‌ها،
  بازرسی‌ها، اسناد مالی و…) — کلیک روی «مشاهده» به ماژول می‌رود.
* **هشدارهای فعال**: موارد نیازمند رسیدگی با درجه شدت.
* **توزیع نقاط AI**: نمودار دایره‌ای قابلیت‌های هوش مصنوعی بر اساس موتور.
* **پوشش استقرار**: تعداد ماژول، زیرماژول، زیرمجموعه و جدول.

## کار با یک موجودیت (جدول داده)

مسیر: *ماژول‌ها → انتخاب ماژول → انتخاب موجودیت*

| عملیات | روش |
|---|---|
| جست‌وجو | نوشتن در کادر جست‌وجو (روی فیلدهای متنی) |
| فیلتر وضعیت | انتخاب از فهرست کشویی |
| مرتب‌سازی | کلیک روی سرستون |
| ایجاد رکورد | دکمه «+ رکورد جدید» |
| ویرایش | کلیک روی سطر یا دکمه «ویرایش» |
| حذف | دکمه «حذف» (حذف نرم — قابل بازیابی توسط مدیر) |
| صفحه‌بندی | دکمه‌های «قبلی/بعدی» زیر جدول |

**نکته‌های فرم:**

* فیلدهای ستاره‌دار الزامی هستند.
* می‌توانید اعداد را با **ارقام فارسی** و جداکننده هزارگان وارد کنید —
  سامانه خودش تبدیل می‌کند.
* تاریخ‌ها با انتخابگر میلادی وارد و به‌صورت **شمسی** نمایش داده می‌شوند.
* خطاهای اعتبارسنجی با پیام فارسی زیر هر فیلد ظاهر می‌شوند.

## مرکز هوش مصنوعی

### دستیار گفت‌وگو
پرسش‌های عملیاتی بپرسید، مانند:
* «چطور ضایعات خط تزریق را کاهش دهم؟»
* «شاخص‌های نت این ماه را تحلیل کن»
* «نقطه سفارش کالای پرمصرف را چگونه تعیین کنم؟»

### برگه «قابلیت‌ها»
هر ویجت 🤖 یک نقطه AI از کاتالوگ است:

1. روی **«اجرای تحلیل»** کلیک کنید.
2. نتیجه با **توضیح فارسی**، سنجه‌ها و زمان پردازش نمایش داده می‌شود.
3. با «مشاهده خروجی کامل» داده خام را ببینید.

اگر نشان **«حالت جایگزین»** دیدید، یعنی سرویس AI در دسترس نبوده و
سامانه پاسخ قاعده‌محور داده است — با پشتیبانی فنی تماس بگیرید.

### برگه «موتورها»
فهرست موتورهای فعال با الگوریتم‌ها و اندپوینت هر کدام.

## گزارش‌ساز

1. جدول موردنظر را انتخاب کنید (همه جداول فعال فهرست شده‌اند).
2. سنجه را تعیین کنید: تعداد، مجموع، میانگین، بیشینه یا کمینه.
3. برای سنجه‌های عددی، نام ستون را بنویسید (مثل `amount`).
4. برای گروه‌بندی، ستون را وارد کنید (مثل `status` یا `department_id`).
5. «اجرای گزارش» → نمودار میله‌ای + جدول نتایج.
6. «⬇ خروجی CSV» → دانلود فایل با ارقام و سرستون‌های اصلی.

## ممیزی

فهرست کامل عملیات نوشتاری: چه کسی، چه زمانی (شمسی)، روی چه چیزی،
از چه آدرس IP. قابل فیلتر بر اساس عملیات، کاربر، ماژول و بازه تاریخ.

## تنظیمات

* **پروفایل من**: نام، نام کاربری، ایمیل، همراه، نقش‌ها
* **تغییر گذرواژه**: پس از تغییر، همه نشست‌های دیگر خارج می‌شوند
* **اطلاعات استقرار**: ماژول‌های فعال، جداول، نقاط AI، واحد پول و تقویم

## نقش‌های پیش‌فرض

| نقش | دسترسی |
|---|---|
| مدیر سامانه | همه مجوزها + کاربر مدیر کل |
| مدیر کارخانه | مشاهده، ایجاد، ویرایش، تأیید همه ماژول‌ها |
| سرپرست | مشاهده، ایجاد، ویرایش در سطح واحد |
| اپراتور | مشاهده و ایجاد رکورد |
| حسابدار | ماژول‌های مالی با حق تأیید |
| برنامه‌ریز تولید | ماژول‌های تولید و موجودی |
| کارشناس کیفیت | ماژول‌های کیفیت با حق تأیید |
| کارشناس نت | ماژول‌های نگهداری و تعمیرات |
| انباردار | انبار، رسید و حواله |
| مشاهده‌کننده | فقط مشاهده |
| ممیز | مشاهده + دسترسی به گزارش ممیزی |

## پرسش‌های پرتکرار

**چرا تاریخ‌ها شمسی است ولی در فرم، میلادی انتخاب می‌کنم؟**
ذخیره‌سازی استاندارد بین‌المللی میلادی است و نمایش برای کاربر شمسی.
در خروجی API هر دو مقدار (`created_at` و `created_at_jalali`) موجود است.

**چرا بعضی دکمه‌ها را نمی‌بینم؟**
دسترسی شما بر اساس مجوز `<ماژول>.<جدول>.<عملیات>` کنترل می‌شود.
برای تغییر، با مدیر سامانه تماس بگیرید.

**حذف رکورد برگشت‌پذیر است؟**
بله — حذف نرم انجام می‌شود و مدیر سامانه می‌تواند بازیابی کند.

**چطور داده نمونه برای آموزش ببینم؟**
با دستور `make demo` (یا `./deploy.sh --demo`) داده نمونه درج می‌شود.
این حالت فقط برای آموزش است، نه تولید.

**آیا بدون اینترنت کار می‌کند؟**
بله. همه موتورهای عددی AI داخلی اجرا می‌شوند. فقط چت و خلاصه‌سازی
پیشرفته به کلید AvalAI نیاز دارد که در نبود آن، پاسخ داخلی داده می‌شود.
"""

REGENERATION_DOC = """# بازتولید بسته با سازنده ERP

این بسته توسط پلتفرم **«سازنده ERP هوشمند کارخانه‌ای»** تولید شده است.
برای تغییر ماژول‌ها، تنظیمات یا بازتولید کامل، مراحل زیر را دنبال کنید.

## شناسنامه این بسته

| مورد | مقدار |
|---|---|
| شناسه بسته | `@@package_id@@` |
| تاریخ تولید | @@generated_at@@ (@@generated_at_jalali@@) |
| نسخه سازنده | @@version@@ |
| نسخه کاتالوگ | @@catalog_version@@ |
| پریست صنعتی | @@preset@@ |
| روش استقرار | @@deploy_target@@ |
| ماژول‌ها | @@modules_count@@ |
| زیرمجموعه‌ها | @@items_count@@ |
| نقاط AI | @@ai_count@@ |
| جداول | @@tables_count@@ |

## چه چیزی در مانیفست ثبت شده است؟

فایل `manifest.json` در ریشه بسته شامل این اطلاعات است:

* مشخصات کارخانه و تنظیمات کامل (`settings`)
* فهرست ماژول‌های منتخب، خودکار اضافه‌شده و دلیل هر افزودن
* فهرست زیرماژول‌ها، زیرمجموعه‌ها و نقاط AI
* آمار فایل‌ها به تفکیک حوزه (لاراول، فرانت‌اند، AI، استقرار، مستندات)
* درخت کامل فایل‌ها
* برنامه فازبندی استقرار

این فایل برای **ممیزی**، **بازتولید** و **مقایسه نسخه‌ها** استفاده می‌شود.

## مراحل بازتولید

1. باز کردن پلتفرم سازنده در مرورگر
2. بارگذاری پروژه ذخیره‌شده (یا واردکردن تنظیمات از `manifest.json`)
3. تغییر انتخاب در **پیکربندگر** (بخش/ماژول/زیرماژول/زیرمجموعه/نقاط AI)
   یا استفاده از **پیشنهاد هوشمند** با مشخصات جدید کارخانه
4. بررسی **حل وابستگی‌ها** (ماژول‌هایی که خودکار افزوده می‌شوند)
5. تنظیم **تنظیمات کارخانه** (پایگاه داده، صف، AvalAI، IoT، استقرار)
6. کلیک روی **تولید بسته** → دانلود zip جدید

## ارتقای درجا بدون بازتولید

اگر فقط می‌خواهید ماژول جدید اضافه کنید:

1. بسته جدید را در پوشه جدا استخراج کنید
2. پوشه‌های `backend/database/migrations` و `backend/app` را با دقت ادغام کنید
   (فایل‌های موجود را رونویسی نکنید — فقط فایل‌های جدید را اضافه کنید)
3. در سرور: `./deploy/scripts/update.sh`
4. رجیستری قابلیت‌ها را همگام کنید:
   `docker compose exec app php artisan erp:features:sync`

> توصیه: برای تغییرهای بزرگ، همیشه بسته کامل را بازتولید کنید و
> داده را با `make backup` پیش از مهاجرت پشتیبان بگیرید.

## افزودن فیلد سفارشی بدون بازتولید

سامانه برای توسعه دستی آماده است:

```bash
cd backend
php artisan make:migration add_custom_field_to_@@sample_table@@_table --table=@@sample_table@@
# افزودن ستون در مهاجرت، سپس:
php artisan migrate --force
```

سپس فیلد را در این سه مکان اضافه کنید:
1. `$fillable` مدل مربوطه
2. `rules()` در `Store*Request` و `Update*Request`
3. `toArray()` در `*Resource`

برای نمایش در رابط کاربری، فیلد را به آرایه `fields` موجودیت متناظر در
`frontend/src/config/menu.js` اضافه کنید (یا بسته را بازتولید کنید تا خودکار بیاید).

## ستون `attributes` — فیلدهای پویا

همه جداول اصلی یک ستون `attributes` از نوع `json` دارند که برای
ویژگی‌های سفارشی هر کارخانه طراحی شده است — بدون نیاز به مهاجرت:

```php
$order = ProductionOrder::find(1);
$order->update(['attributes' => ['color_batch' => 'RAL-7035', 'customer_note' => 'بسته‌بندی ویژه']]);
```

در API این فیلد قابل خواندن و نوشتن است.

## تغییر تنظیمات پس از استقرار

همه تنظیمات کارخانه در `backend/config/erp.php` با متغیر محیطی متناظر است:

| تنظیم | متغیر محیطی |
|---|---|
| نام شرکت | `ERP_COMPANY_NAME` |
| واحد پول | `ERP_CURRENCY` |
| نرخ مالیات پیش‌فرض | `ERP_TAX_RATE_DEFAULT` |
| فعال‌سازی مؤدیان | `ERP_MOADIAN_ENABLED` |
| فعال‌سازی AI | `ERP_AI_ENABLED` |
| تأیید انسانی نتایج AI | `ERP_AI_HUMAN_APPROVAL` |
| فعال‌سازی IoT | `ERP_IOT_ENABLED` |
| زمان‌بندی پشتیبان | `ERP_BACKUP_CRON` |

پس از تغییر `.env`:

```bash
docker compose exec app php artisan config:cache
```
"""

CHANGELOG_TEMPLATE = """# تغییرات @@app_name_fa@@

## @@version@@ — @@generated_at_jalali@@

### تولید اولیه بسته

* @@modules_count@@ ماژول فعال از @@sections_count@@ بخش کاتالوگ
* @@tables_count@@ جدول پایگاه داده با @@fields_count@@ فیلد
* @@migrations_count@@ مهاجرت، @@models_count@@ مدل Eloquent
* @@controllers_count@@ کنترلر REST، @@requests_count@@ FormRequest
* @@policies_count@@ سیاست دسترسی، @@resources_count@@ Resource
* @@tests_count@@ فایل آزمون عملکردی
* رابط کاربری React با @@pages_count@@ صفحه داده‌محور و @@fields_count@@ فیلد فارسی
* سرویس هوش مصنوعی با @@engines_count@@ موتور و @@ai_count@@ نقطه فعال
* پشته Docker: پایگاه داده، Redis، بک‌اند، صف، زمان‌بند، AI، nginx
* @@docs_count@@ سند فارسی
* پشتیبانی از تقویم شمسی، ارقام فارسی، واحد پول @@currency_label@@ و سامانه مؤدیان
"""

LICENSE = """MIT License

Copyright (c) @@year@@ @@company_name@@

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def _modules_table(modules: list[dict[str, Any]], sections: dict[str, dict[str, Any]]) -> str:
    rows = ["| کد | ماژول | بخش | زیرماژول | زیرمجموعه | جداول | نقاط AI | اولویت |",
            "|---|---|---|---|---|---|---|---|"]
    for module in modules:
        section = sections.get(module["code"][:1], {})
        stats = module.get("_stats", {})
        rows.append(
            f"| `{module['code']}` | {module['label_fa']} | {section.get('name', module['code'][:1])} | "
            f"{stats.get('groups', 0)} | {stats.get('items', 0)} | {stats.get('tables', 0)} | "
            f"{stats.get('ai', 0)} | {module.get('priority', 3)} |"
        )
    return "\n".join(rows)


def _engines_table(ai_engines: list[dict[str, Any]], counts: dict[str, int]) -> str:
    rows = ["| موتور | نام فارسی | الگوریتم‌ها | اندپوینت | نقاط فعال |",
            "|---|---|---|---|---|"]
    for engine in ai_engines:
        rows.append(
            f"| `{engine['key']}` | {engine['name_fa']} | "
            f"{', '.join(engine['algorithms'][:4])} | `{engine['endpoint']}` | "
            f"{counts.get(engine['key'], 0)} |"
        )
    return "\n".join(rows)


def generate_docs(
    package: Package,
    *,
    settings: dict[str, Any],
    modules: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    ai_engines: list[dict[str, Any]],
    ai_points: list[dict[str, Any]],
    sections: dict[str, dict[str, Any]],
    groups: list[dict[str, Any]],
    items: list[dict[str, Any]],
    context: dict[str, Any],
    include_docs: bool = True,
    include_api_docs: bool = True,
) -> None:
    """تولید مستندات فارسی بسته.

    `include_docs=False` فقط README، CHANGELOG و LICENSE را می‌سازد و
    `include_api_docs=False` سند مرجع API را حذف می‌کند.
    """
    counters = context.get("counters", {})
    tables_by_module: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        tables_by_module.setdefault(entity["module_code"] or "S0", []).append(entity)

    # آمار هر ماژول روی «کپی» ماژول‌ها نوشته می‌شود تا dictهای فراخوان (که بعداً
    # در manifest.json مصرف می‌شوند) آلوده به کلید داخلی `_stats` نشوند.
    modules = [
        {
            **module,
            "_stats": {
                "groups": sum(1 for g in groups if g["module_code"] == module["code"]),
                "items": sum(1 for i in items if i["module_code"] == module["code"]),
                "ai": sum(1 for p in ai_points if p["module_code"] == module["code"]),
                "tables": len(tables_by_module.get(module["code"], [])),
            },
        }
        for module in modules
    ]

    engine_counts: dict[str, int] = {}
    for point in ai_points:
        engine_counts[point["engine"]] = engine_counts.get(point["engine"], 0) + 1

    db_labels = {
        "mysql": "MySQL 8.4",
        "mariadb": "MariaDB 11.4",
        "pgsql": "PostgreSQL 16",
        "sqlite": "SQLite",
        "sqlsrv": "SQL Server",
    }
    db_driver = settings.get("db_driver", "sqlite")

    common = {
        "app_name": settings.get("app_name", context["slug"]),
        "app_name_fa": settings.get("app_name_fa", context["app_name_fa"]),
        "company_name": settings.get("company_name") or context["app_name_fa"],
        "slug": context["slug"],
        "version": context["version"],
        "catalog_version": context["catalog_version"],
        "package_id": context["package_id"],
        "generated_at": context["generated_at"],
        "generated_at_jalali": context["generated_at_jalali"],
        "year": context["generated_at"][:4],
        "timezone": settings.get("timezone", "Asia/Tehran"),
        "currency": settings.get("currency", "IRR"),
        "currency_label": settings.get("currency_label", "ریال"),
        "industry_label": context["industry_label"],
        "tagline": context["tagline"],
        "host_port": settings.get("host_port", 8000),
        "db_label": db_labels.get(db_driver, db_driver),
        "db_version": db_labels.get(db_driver, db_driver).split()[-1] if db_driver != "sqlite" else "—",
        "db_ext": {"mysql": "mysql", "mariadb": "mysql", "pgsql": "pgsql", "sqlite": "sqlite"}.get(db_driver, "mysql"),
        "db_port": {"mysql": "3306", "mariadb": "3306", "pgsql": "5432", "sqlite": "—"}.get(db_driver, "5432"),
        "db_driver": db_driver,
        "db_host": settings.get("db_host", "mysql"),
        "db_database": settings.get("db_database", "smart_erp"),
        "db_username": settings.get("db_username", "erp_user"),
        "db_password": settings.get("db_password") or "<گذرواژه امن تولیدشده>",
        "redis_host": settings.get("redis_host", "redis"),
        "cache_driver": settings.get("cache_driver", "redis"),
        "queue_driver": settings.get("queue_driver", "redis"),
        "session_driver": settings.get("session_driver", "database"),
        "ai_service_url": settings.get("ai_service_url", "http://ai-service:8001"),
        "app_url": settings.get("app_url", "http://erp.local"),
        "admin_email": settings.get("admin_email", "admin@example.com"),
        "admin_password": settings.get("admin_password", "ChangeMe!1405"),
        "backup_cron": settings.get("backup_cron", "0 2 * * *"),
        "backup_keep_days": int(settings.get("backup_keep_days", 30)),
        "deploy_target": settings.get("deploy_target", "docker"),
        "preset": context.get("preset") or "custom",
        "sections_count": len({m["code"][:1] for m in modules}),
        "modules_count": len(modules),
        "groups_count": len(groups),
        "items_count": len(items),
        "ai_count": len(ai_points),
        "engines_count": len(ai_engines),
        "tables_count": len(entities),
        "fields_count": sum(len(e["fields"]) for e in entities),
        "file_count": context["file_count"],
        "line_count": context["line_count"],
        "docs_count": 10,
        "pages_count": 10,
        "ai_tests_count": 15,
        "sample_table": entities[0]["table"] if entities else "system_features",
        "migrations_count": counters.get("migrations", 0),
        "models_count": counters.get("models", 0),
        "controllers_count": counters.get("controllers", 0),
        "requests_count": counters.get("requests", 0),
        "resources_count": counters.get("resources", 0),
        "policies_count": counters.get("policies", 0),
        "tests_count": counters.get("tests", 0),
        "services_count": counters.get("services", 0),
        "seeders_count": counters.get("seeders", 0),
        "backend_files": counters.get("backend_files", 0),
    }

    def add_doc(rel_path: str, template: str, **values: Any) -> None:
        """افزودن سند فقط وقتی مستندات کامل فعال باشد."""
        if include_docs:
            package.add_rendered(rel_path, template, area="docs", **values)

    package.add_rendered("README-fa.md", README_TEMPLATE, area="docs",
                         modules_table=_modules_table(modules, sections),
                         engines_table=_engines_table(ai_engines, engine_counts),
                         docs_enabled="بله" if include_docs else "خیر (فقط README)",
                         **common)

    add_doc("docs/01-architecture.md", ARCHITECTURE_DOC, **common)
    add_doc("docs/02-installation.md", INSTALLATION_DOC, **common)
    add_doc("docs/07-operations.md", OPERATIONS_DOC, **common)
    add_doc("docs/08-user-guide.md", USER_GUIDE_DOC, **common)
    add_doc("docs/09-regeneration.md", REGENERATION_DOC, **common)
    if include_api_docs:
        add_doc("docs/06-api-reference.md", API_DOC,
                module_endpoints=_module_endpoints(modules, tables_by_module),
                **common)
    package.add_rendered("CHANGELOG.md", CHANGELOG_TEMPLATE, area="docs", **common)
    package.add_rendered("LICENSE", LICENSE, area="docs", **common)

    # --- سند ماژول‌ها ------------------------------------------------------ #
    sections_rows = ["| بخش | نام | نام انگلیسی | ماژول‌ها | زیرماژول‌ها | زیرمجموعه‌ها | نقاط AI |",
                     "|---|---|---|---|---|---|---|"]
    for code, section in sorted(sections.items()):
        section_modules = [m for m in modules if m["code"].startswith(code)]
        if not section_modules:
            continue
        section_groups = sum(m["_stats"]["groups"] for m in section_modules)
        section_items = sum(m["_stats"]["items"] for m in section_modules)
        section_ai = sum(m["_stats"]["ai"] for m in section_modules)
        sections_rows.append(
            f"| {code} | {section['name']} | {section['name_en']} | {len(section_modules)} | "
            f"{section_groups} | {section_items} | {section_ai} |"
        )

    detail_blocks: list[str] = []
    for module in modules:
        stats = module["_stats"]
        tables = tables_by_module.get(module["code"], [])
        module_items = [i for i in items if i["module_code"] == module["code"]]
        module_ai = [p for p in ai_points if p["module_code"] == module["code"]]

        lines = [
            f"### `{module['code']}` — {module['label_fa']}",
            "",
            f"*{module.get('name_en', '')}* — گروه منو: **{module.get('menu_group', '—')}**",
            "",
            module.get("description", "") or "—",
            "",
            f"| زیرماژول | زیرمجموعه | جدول داده | نقطه AI | اولویت | نوع |",
            f"|---|---|---|---|---|---|",
            f"| {stats['groups']} | {stats['items']} | {stats['tables']} | {stats['ai']} | "
            f"{module.get('priority', 3)} | {'پایه' if not module.get('derived') else 'استاندارد'} |",
            "",
        ]

        if tables:
            lines += ["**جدول‌های داده:**", "", "| جدول | عنوان | فیلدها |", "|---|---|---|"]
            for entity in tables:
                lines.append(f"| `{entity['table']}` | {entity['label_fa']} | {len(entity['fields'])} |")
            lines.append("")

        if module_items:
            lines += ["**زیرمجموعه‌های عملیاتی:**", ""]
            by_group: dict[str, list[str]] = {}
            for item in module_items:
                by_group.setdefault(item.get("group_name", "—"), []).append(
                    f"`{item['code']}` {item['name']}" + (" 🤖" if item.get("ai") else "")
                )
            for group_name, group_items in by_group.items():
                lines.append(f"* **{group_name}**: " + "؛ ".join(group_items[:14])
                             + ("؛ …" if len(group_items) > 14 else ""))
            lines.append("")

        if module_ai:
            lines += ["**نقاط هوش مصنوعی:**", "", "| کد | قابلیت | موتور | اندپوینت |", "|---|---|---|---|"]
            for point in module_ai[:24]:
                lines.append(
                    f"| `{point['code']}` | {point['name']} | {point['engine']} | `{point['endpoint']}` |"
                )
            if len(module_ai) > 24:
                lines.append(f"| … | و {len(module_ai) - 24} مورد دیگر | | |")
            lines.append("")

        detail_blocks.append("\n".join(lines))

    add_doc(
        "docs/03-modules.md",
        MODULES_DOC,
        sections_table="\n".join(sections_rows),
        modules_detail="\n---\n\n".join(detail_blocks),
        **common,
    )

    # --- سند مدل داده ------------------------------------------------------ #
    type_counts: dict[str, int] = {}
    for entity in entities:
        for field in entity["fields"]:
            type_counts[field["type"]] = type_counts.get(field["type"], 0) + 1
    types_rows = ["| نوع داده | تعداد فیلد | نگاشت پایگاه داده |", "|---|---|---|"]
    type_mapping = {
        "string": "VARCHAR",
        "text": "TEXT",
        "integer": "INTEGER",
        "bigint": "BIGINT UNSIGNED",
        "decimal": "DECIMAL(18,2/4)",
        "boolean": "BOOLEAN",
        "date": "DATE",
        "datetime": "DATETIME",
        "time": "TIME",
        "json": "JSON",
        "uuid": "UUID",
        "enum": "ENUM",
        "foreign": "FK → BIGINT UNSIGNED",
    }
    for ftype, count in sorted(type_counts.items(), key=lambda kv: -kv[1]):
        types_rows.append(f"| `{ftype}` | {count} | {type_mapping.get(ftype, ftype.upper())} |")

    tables_blocks: list[str] = []
    for code, section in sorted(sections.items()):
        section_entities = [e for e in entities if (e["module_code"] or "S0").startswith(code)]
        if not section_entities:
            continue
        lines = [
            f"### بخش {code} — {section['name']}",
            "",
            f"{len(section_entities)} جدول، "
            f"{sum(len(e['fields']) for e in section_entities)} فیلد",
            "",
            "| جدول | عنوان فارسی | ماژول | فیلدها | کلید خارجی | حذف نرم |",
            "|---|---|---|---|---|---|",
        ]
        for entity in section_entities:
            fks = [f["name"] for f in entity["fields"] if f["type"] == "foreign"]
            lines.append(
                f"| `{entity['table']}` | {entity['label_fa']} | {entity['module_code'] or 'S0'} | "
                f"{len(entity['fields'])} | {', '.join(f'`{fk}`' for fk in fks[:3]) or '—'}"
                f"{' …' if len(fks) > 3 else ''} | {'✓' if entity.get('soft_deletes') else '—'} |"
            )
        tables_blocks.append("\n".join(lines))

    fk_pairs: dict[str, int] = {}
    for entity in entities:
        for field in entity["fields"]:
            if field["type"] == "foreign":
                key = field.get("references_table", "?")
                fk_pairs[key] = fk_pairs.get(key, 0) + 1
    fk_rows = ["| جدول مرجع | تعداد ارجاع |", "|---|---|"]
    for table, count in sorted(fk_pairs.items(), key=lambda kv: -kv[1])[:25]:
        fk_rows.append(f"| `{table}` | {count} |")

    field_stats = [
        "| سنجه | مقدار |",
        "|---|---|",
        f"| مجموع جدول‌ها | {len(entities)} |",
        f"| مجموع فیلدها | {sum(len(e['fields']) for e in entities)} |",
        f"| میانگین فیلد در هر جدول | {round(sum(len(e['fields']) for e in entities) / max(len(entities), 1), 1)} |",
        f"| بزرگ‌ترین جدول | `{max(entities, key=lambda e: len(e['fields']))['table']}` "
        f"با {max(len(e['fields']) for e in entities)} فیلد |" if entities else "| — | — |",
        f"| فیلدهای الزامی | {sum(1 for e in entities for f in e['fields'] if f.get('required'))} |",
        f"| فیلدهای قابل جست‌وجو | {sum(1 for e in entities for f in e['fields'] if f.get('searchable'))} |",
        f"| فیلدهای یکتا | {sum(1 for e in entities for f in e['fields'] if f.get('unique'))} |",
        f"| ایندکس‌ها | {sum(1 for e in entities for f in e['fields'] if f.get('index'))} |",
        f"| روابط خارجی | {sum(fk_pairs.values())} |",
    ]

    topo = context.get("topological_order", [])
    add_doc(
        "docs/04-data-model.md",
        DATA_MODEL_DOC,
        types_table="\n".join(types_rows),
        tables_by_section="\n\n---\n\n".join(tables_blocks),
        topo_sample_count=min(len(topo), 30),
        topo_list="\n".join(f"{i}. `{table}`" for i, table in enumerate(topo[:30], start=1)) or "—",
        fk_summary="\n".join(fk_rows),
        field_stats="\n".join(field_stats),
        **common,
    )

    # --- سند قابلیت‌های AI -------------------------------------------------- #
    endpoint_rows = []
    for engine in ai_engines:
        endpoint_rows.append(
            f"| `POST {engine['endpoint']}` | {engine['name_fa']} | "
            f"{engine['input_hint']} | {engine['output_hint']} |"
        )

    ai_blocks: list[str] = []
    ai_by_module: dict[str, list[dict[str, Any]]] = {}
    for point in ai_points:
        ai_by_module.setdefault(point["module_code"] or "S0", []).append(point)

    for module in modules:
        points = ai_by_module.get(module["code"], [])
        if not points:
            continue
        lines = [
            f"### {module['code']} — {module['label_fa']}",
            "",
            "| کد | قابلیت | موتور | مدل | اندپوینت | الگوریتم‌ها |",
            "|---|---|---|---|---|---|",
        ]
        for point in points:
            lines.append(
                f"| `{point['code']}` | {point['name']} | {point['engine']} | `{point['model_id']}` | "
                f"`{point['endpoint']}` | {', '.join(point['algorithms'][:2])} |"
            )
        ai_blocks.append("\n".join(lines))

    add_doc(
        "docs/05-ai-capabilities.md",
        AI_DOC,
        engines_table=_engines_table(ai_engines, engine_counts),
        engine_endpoints="\n".join(endpoint_rows),
        ai_by_module="\n\n".join(ai_blocks) or "نقطه هوش مصنوعی فعالی در این استقرار نیست.",
        **common,
    )


def _module_endpoints(modules: list[dict[str, Any]], tables_by_module: dict[str, list[dict[str, Any]]]) -> str:
    blocks = []
    for module in modules:
        tables = tables_by_module.get(module["code"], [])
        if not tables:
            continue
        lines = [
            f"### `{module['code']}` — {module['label_fa']}",
            "",
            f"پیشوند: `/api/v1/{module['slug']}` — مجوز: `{module['slug']}.<جدول>.<عملیات>`",
            "",
            "| منبع (جدول) | عنوان | مسیر |",
            "|---|---|---|",
        ]
        for entity in tables[:40]:
            lines.append(
                f"| `{entity['table']}` | {entity['label_fa']} | "
                f"`/api/v1/{module['slug']}/{entity['table']}` |"
            )
        if len(tables) > 40:
            lines.append(f"| … | و {len(tables) - 40} منبع دیگر | |")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
