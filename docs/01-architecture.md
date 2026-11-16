# معماری

دو سامانه در این مخزن زندگی می‌کنند: **سازنده** (که در این مخزن اجرا می‌شود) و **بسته تولیدشده**
(که خروجی آن است و در کارخانه مشتری اجرا می‌شود). این سند هر دو را توصیف می‌کند.

---

## ۱) نمای کلی سازنده

```
┌────────────────────────── رابط کاربری سازنده (React 18 + Vite 6) ─────────────────────────┐
│  Home · Configure (کاتالوگ/تنظیمات/دستیار/پروژه‌ها/تولید) · Engines · Packages · Detail     │
│  src/lib/store.jsx — وضعیت سراسری، localStorage، /resolve دیبانس‌شده                        │
└───────────────────────────────────────────────┬────────────────────────────────────────────┘
                                                │  /api  (پروکسی Vite یا همان پورت FastAPI)
┌───────────────────────────────────────────────▼────────────────────────────────────────────┐
│                                  سرویس سازنده (FastAPI)                                    │
│  api/routes.py — ۳۰ اندپوینت                                                               │
│  ├─ catalog/       کاتالوگ چهارسطحی (DSL + registry + ۲۲ sections/*.py)                    │
│  ├─ domain/        مدل دامنه: specs دستی + derived + registry (۴۴۲ جدول)                   │
│  ├─ selection.py   گسترش انتخاب، حل پیش‌نیازها، برآورد فایل/جدول                           │
│  ├─ presets.py     ۱۱ پریست صنعتی                                                          │
│  ├─ ai/            registry موتورهای AI · llm (AvalAI) · advisor (پیشنهاد ماژول/فاز/چت)     │
│  ├─ projects.py    ذخیره پروژه‌ها در data/projects.json                                    │
│  └─ generator/     موتور تولید سه‌لایه → dist-packages/<package-id>/ + zip                 │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

### جریان یک درخواست تولید

```
POST /api/generate {project}
  ├─ projects.save_project()            (اختیاری، با save_project)
  ├─ pipeline.generate_package()
  │   ├─ settings_map.normalize_settings()   ← ۹۴ کلید متعارف + کلیدهای قدیمی
  │   ├─ selection.resolve()                 ← ماژول‌های نهایی + پیش‌نیازهای خودکار
  │   ├─ domain.specs_for_modules()          ← موجودیت‌ها با ترتیب توپولوژیک
  │   ├─ build_context()                     ← slug/pascal/شمارش‌ها/آمار ماژول‌ها
  │   ├─ generate_core_files()               ← اسکلت لاراول + config + Support
  │   ├─ generate_domain_files()             ← مایگریشن/مدل/کنترلر/… برای هر موجودیت
  │   ├─ generate_system_files()             ← احراز هویت، مجوز، ممیزی، گزارش، داشبورد
  │   ├─ generate_routes() + generate_seeders()
  │   ├─ generate_ai_service()               ← فقط اگر ai_enabled و نقطه AI وجود داشته باشد
  │   ├─ generate_frontend()                 ← SPA داده‌محور + منوی پویا
  │   ├─ generate_deploy_files()             ← compose/nginx/systemd/Makefile/deploy.sh
  │   ├─ generate_docs()  (دو بار: آمار میانی، سپس آمار نهایی)
  │   ├─ manifest.json + erp-selection.json
  │   └─ Package.write() + zip کنار پوشه
  └─ GenerateResult → مرور در /packages/{id}
```

### لایه‌های کد سازنده

| لایه | مسیر | نقش |
| --- | --- | --- |
| کاتالوگ | `builder/backend/app/catalog/` | تنها منبع حقیقت «چه قابلیت‌هایی وجود دارد» — ۲۲ فایل بخش، DSL مشترک، registry با نمایه‌های جست‌وجو و وابستگی |
| دامنه | `builder/backend/app/domain/` | «چه داده‌هایی لازم است» — مشخصات دستی ۶۲ ماژول، اشتقاق ۶۸ ماژول از کاتالوگ، موجودیت‌های پلتفرمی، اعتبارسنجی کلید خارجی |
| انتخاب | `builder/backend/app/selection.py` | «کاربر چه خواسته و چه چیزی لازم می‌شود» — گسترش سلسله‌مراتبی، پیش‌نیاز خودکار، برآورد |
| AI | `builder/backend/app/ai/` | ثبت ۱۱ موتور، نگاشت نقطه AI → موتور/اندپوینت/مدل/فلگ، کلاینت AvalAI، دستیار پیشنهاد و فازبندی و چت |
| تولید | `builder/backend/app/generator/` | «کد واقعی» — ۱۳ فایل، ۱۸٬۷۶۵ خط قالب و منطق نوشتن |
| سرویس | `builder/backend/app/api/`, `main.py` | REST + سرو کردن باندل رابط کاربری |

اصل طراحی: **هیچ داده‌ای در قالب‌ها hard-code نیست**. هر عدد (شمارش ماژول، جدول، فایل، نقطه AI)
در زمان تولید محاسبه می‌شود و هر متن فارسی از کاتالوگ یا `settings` می‌آید. به همین دلیل
`scripts/check_flags.py` می‌تواند اثر هر تنظیم را روی خروجی assert کند.

---

## ۲) پشته بسته تولیدشده

```
<package-id>/
├── backend/                    لاراول ۱۱ (PHP 8.3)
│   ├── app/
│   │   ├── Models/<Ns>/        یک مدل به ازای هر موجودیت
│   │   ├── Http/Controllers/Api/<Ns>/   کنترلر CRUD + approve/export
│   │   ├── Http/Requests/<Ns>/          Store + Update برای هر موجودیت
│   │   ├── Http/Resources/<Ns>/         Resource هر موجودیت
│   │   ├── Policies/<Ns>/               مجوز مبتنی بر permission
│   │   ├── Services/<Ns>/               سرویس دامنه هر ماژول
│   │   └── Support/            Jalali · PersianText · AvalAiClient · AiServiceClient
│   │                           ActivityLogger · ModuleRegistry
│   ├── database/migrations/    2026_01_01_<seq>_create_<table>_table.php
│   ├── database/seeders/       SystemSeeder + <Ns><CODE>Seeder برای هر ماژول
│   ├── database/factories/<Ns>/
│   ├── routes/modules/<slug>.php   auth:sanctum + permission
│   ├── tests/Feature/<Ns>/     آزمون PHPUnit برای هر موجودیت
│   └── config/{features,reports,ai}.php
├── frontend/                   React 18 + Vite 6 (RTL، بدون کتابخانه UI)
│   └── src/{config/menu.js,config/schemas.js,lib/api.js,pages/…}
├── ai-service/                 FastAPI (پورت ۸۰۰۱) + ۱۱ موتور + tests/
├── deploy/                     nginx · systemd · crontab · mosquitto (مشروط)
├── docker-compose.yml          db · redis · mqtt · ai-service · app · queue · scheduler · web
├── deploy.sh · Makefile (۲۱ هدف) · .env.example · README-fa.md · CHANGELOG.md
├── docs/                       تا ۹ سند فارسی (مشروط به include_docs)
├── manifest.json               شناسنامه بسته + reproduce
└── erp-selection.json          انتخاب چهارسطحی کاربر
```

### قرارداد نام‌گذاری

| عنصر | قاعده | نمونه |
| --- | --- | --- |
| namespace | از **بخش** کاتالوگ (`SECTION_NAMESPACE`) | `A` → `App\Models\Manufacturing` |
| ماژول بدون بخش (پلتفرم) | `S0` → `App\Models\System` | `Company`, `User` |
| Seeder | `<Ns><CODE>Seeder` | `ManufacturingA1Seeder` |
| Service | `<Ns><CODE>Service` | `ManufacturingA1Service` |
| جدول | از مدل دامنه (جمع فارسی‌پسند/انگلیسی) | `production_orders` |
| روت API | `/api/v1/<table>` در `routes/modules/<slug>.php` | `/api/v1/production_orders` |
| مجوز | `<module_slug>.<table>.{view,create,edit,delete,approve}` | `production_planning.production_orders.view` |
| مدل AI | `<engine_key>_<code با _ >` | `forecasting_a1_4_5` |
| فلگ AI | `ai.<engine_key>.<code>` | `ai.forecasting.a1_4_5` |

### تصمیم‌های معماری در بسته تولیدشده

- **مجوز مبتنی بر permission نه نقش سخت** — نقش‌ها (۱۱ نقش) در `SystemSeeder` ساخته می‌شوند اما
  هر روت یک `permission:` مشخص دارد؛ افزودن نقش جدید بدون تغییر کد ممکن است.
- **جداسازی منو از اسکیما** — `src/config/menu.js` سبک است و `src/config/schemas.js` به‌صورت
  lazy بارگذاری می‌شود تا حجم اولیه SPA کوچک بماند (با ۹۵ ماژول، چانک اسکیما ~۷۸۰ کیلوبایت و
  gzip ~۷۴ کیلوبایت است).
- **سرویس AI جدا** — همه محاسبات سنگین در میکروسرویس پایتون است و لاراول فقط کلاینت سبک
  `AiServiceClient` دارد؛ با `ai_enabled=false` کل این لایه حذف می‌شود.
- **fallback قاعده‌محور** — هر موتور AI در نبود داده کافی پاسخ قاعده‌محور با توضیح فارسی و
  `fallback=true` می‌دهد، پس سرویس هرگز با خطای ۵۰۰ پاسخ نمی‌دهد.
- **تأیید انسانی** — با `ai_human_approval=true` پیشنهادها فقط ثبت می‌شوند و اعمال آن‌ها نیازمند
  تأیید کاربر است.
- **پشتیبانی جلالی در هسته** — `App\Support\Jalali` و `PersianText` در همه لایه‌ها (تاریخ،
  ارقام، حروف‌چینی پول) استفاده می‌شوند؛ تقویم شمسی یک افزودنی نیست.
