# سازنده ERP هوشمند کارخانه‌ای

یک پلتفرم **تولید کد** برای ERP صنعتی: کاتالوگ کامل قابلیت‌های یک کارخانه را در چهار سطح
مرور می‌کنید، ماژول‌های مورد نیاز خود را انتخاب می‌کنید و در کمتر از دو ثانیه یک **بسته استقرار
کامل** تحویل می‌گیرید — بک‌اند لاراول، رابط کاربری ری‌اکت راست‌به‌چپ، میکروسرویس هوش مصنوعی
پایتون، پیکربندی Docker/Nginx و مستندات فارسی.

هیچ قالب آماده‌ای کپی نمی‌شود: هر فایل (مایگریشن، مدل، کنترلر، FormRequest، Resource، Policy،
Factory، آزمون، Seeder، Service، روت، صفحه فرانت‌اند، اندپوینت AI، سند) از **کاتالوگ انتخابی شما
و مدل دامنه همان ماژول‌ها** ساخته می‌شود؛ بنابراین خروجی برای هر کارخانه یکتاست.

```
۲۲ بخش صنعتی · ۱۳۰ ماژول · ۵۱۵ زیرماژول · ۲٬۱۵۷ قابلیت · ۲۶۶ نقطه هوش مصنوعی
۴۴۲ جدول داده · ۷٬۰۰۸ فیلد · ۱۱ موتور الگوریتمی AI · ۱۱ پریست صنعتی
```

---

## شروع سریع

### ۱) سرویس بک‌اند (FastAPI)

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r builder/backend/requirements.txt

cd builder/backend
../../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- مستندات تعاملی API: `http://localhost:8000/api/docs`
- سلامت سرویس: `http://localhost:8000/api/health`

### ۲) رابط کاربری سازنده (React + Vite)

```bash
cd builder/frontend
npm install
npm run dev          # http://localhost:5173 — /api به پورت ۸۰۰۰ پروکسی می‌شود
```

برای حالت تک‌پورتی، باندل را بسازید تا خود FastAPI آن را سرو کند:

```bash
npm run build        # → builder/frontend/dist
# حالا http://localhost:8000/ همان رابط کاربری است
```

### ۳) تولید بسته از خط فرمان (بدون مرورگر)

```bash
.venv/bin/python scripts/smoke_generate.py --preset automotive
# خروجی: dist-packages/<package-id>/ و <package-id>.zip
```

یا با API:

```bash
curl -X POST http://localhost:8000/api/generate \
  -H 'Content-Type: application/json' \
  -d '{"project":{"name":"ERP کارخانه من","preset_key":"food_pharma",
       "selection":{"modules":["A1","B1","C1","D3","F1"],"mode":"custom"}},
       "save_project":true}'
```

---

## ساختار مخزن

```
builder/
├── backend/app/
│   ├── catalog/        کاتالوگ چهارسطحی: DSL + ۲۲ فایل sections/ (۴٬۶۵۸ خط)
│   ├── domain/         مدل دامنه: مشخصات دستی ۶۲ ماژول + اشتقاق ۶۸ ماژول (۵٬۰۱۴ خط)
│   ├── generator/      موتور تولید سه‌لایه: لاراول، ری‌اکت، ai-service، deploy، docs (۱۹٬۶۷۵ خط)
│   ├── ai/             ثبت موتورهای AI، کلاینت AvalAI، دستیار انتخاب ماژول (۹۹۹ خط)
│   ├── api/            ۳۰ اندپوینت REST (۷۰۲ خط)
│   ├── config.py       ۹۷ کلید تنظیمات متعارف، مسیرها، درایورها، اهداف استقرار
│   ├── selection.py    حل وابستگی‌ها و گسترش انتخاب
│   ├── presets.py      ۱۱ پریست صنعتی
│   ├── projects.py     ذخیره/بارگذاری پروژه‌ها در data/projects.json
│   └── main.py         برنامه FastAPI + سرو کردن باندل رابط کاربری
├── frontend/           رابط کاربری سازنده (React 18 + Vite 6، RTL، ۵٬۴۷۰ خط در ۲۲ فایل)
│   ├── src/lib/        api.js · format.js · selection.js · store.jsx
│   ├── src/components/ TopBar · CatalogTree · SelectionCart · SettingsForm · AdvisorPanel · …
│   ├── src/pages/      Home · Configure · Engines · Packages · PackageDetail
│   └── smoke/          آزمون دود رندر با داده واقعی API
scripts/                ۹ اسکریپت اعتبارسنجی و راستی‌آزمایی (۱٬۳۰۹ خط)
data/                   catalog.json (خروجی اعتبارسنج) و projects.json (پروژه‌های ذخیره‌شده)
dist-packages/          بسته‌های تولیدشده (در .gitignore)
docs/                   مستندات معماری، کاتالوگ، API، موتور تولید، UI و راستی‌آزمایی
```

---

## خط لوله: از کاتالوگ تا بسته استقرار

```
کاتالوگ (۲۲ sections/*.py)          مدل دامنه (specs + derived)
        │                                    │
        ▼                                    ▼
   انتخاب کاربر  ──►  حل وابستگی‌ها  ──►  مدل داده ۴۴۲ جدولی  ──►  موتور تولید
   (۴ سطح + AI)      (پیش‌نیاز خودکار،     (ترتیب توپولوژیک،        │
                      اعتبارسنجی)          کلید خارجی)              ▼
                                                          بسته استقرار + zip
                                                                     │
                                                                     ▼
                                                    راستی‌آزمایی (۹ اسکریپت)
```

۱. **کاتالوگ** — هر قابلیت یک `ITEM` با کلیدهای `code,name,ai,deps,entity,role,level` است که در
   `GROUP` (زیرماژول) و `MODULE` و `SECTION` جمع می‌شود. `deps` می‌تواند به یک زیرمجموعه، یک
   زیرماژول یا یک ماژول اشاره کند.
۲. **حل وابستگی‌ها** — انتخاب کاربر گسترش می‌یابد (انتخاب ماژول ⇒ همه زیرماژول‌ها و
   زیرمجموعه‌هایش)، پیش‌نیازها به‌صورت خودکار افزوده می‌شوند و دلیل هر افزودن در
   `auto_added`/`reasons` برمی‌گردد.
۳. **مدل دامنه** — برای ماژول‌های انتخابی، موجودیت‌ها با ترتیب توپولوژیک ساخته می‌شوند؛
   ۶۲ ماژول مشخصات دستی دارند و ۶۸ ماژول از کاتالوگ مشتق می‌شوند.
۴. **تولید** — برای هر موجودیت: مایگریشن، مدل، کنترلر API، FormRequest (Store/Update)، Resource،
   Policy، Factory، آزمون Feature و Seeder؛ به‌علاوه روت‌ها، مجوزها، منوی فرانت‌اند، صفحه‌های
   داده‌محور، اندپوینت‌های AI، پیکربندی استقرار و مستندات.
۵. **راستی‌آزمایی** — اعتبارسنجی ایستای همه فایل‌ها، سازگاری مانیفست و docker-compose، اجرای
   آزمون‌های pytest سرویس AI تولیدشده، ساخت واقعی فرانت‌اند تولیدشده با Vite و آزمون دود رابط
   کاربری سازنده.

جزئیات هر مرحله در [`docs/`](docs) آمده است.

---

## بسته خروجی چه دارد؟

| مسیر | محتوا |
| --- | --- |
| `backend/` | لاراول ۱۱: مایگریشن، مدل، کنترلر API، FormRequest، Resource، Policy، Factory، آزمون Feature، Seeder، Service، روت ماژول‌ها، مجوزها، پشتیبانی جلالی، ممیزی، دستورهای `artisan` (`erp:install`, `features:sync`, `backup`, `ai:health`) |
| `frontend/` | React 18 + Vite 6 راست‌به‌چپ بدون کتابخانه UI: منوی پویا از ماژول‌های انتخابی، صفحه داده‌محور CRUD برای هر جدول، مرکز AI، گزارش‌ساز، داشبورد، ممیزی و PWA موبایل |
| `ai-service/` | FastAPI روی پورت ۸۰۰۱ با ۱۱ موتور واقعی (numpy/pandas/scikit-learn)، مسیرهای `/health /capabilities /models /ai/{forecast,optimize,anomaly,reliability,spc,vision,nlp,recommend,classify,simulate,mlops}` |
| `deploy/` | `docker-compose.yml` (db، redis، mqtt، ai-service، app، queue، scheduler، web)، nginx، systemd، crontab، `deploy.sh`، اسکریپت پشتیبان/ارتقا/سلامت و `Makefile` با ۲۱ هدف |
| `docs/` | README فارسی و تا ۹ سند: معماری، نصب، ماژول‌ها، مدل داده، قابلیت‌های AI، مرجع API، عملیات، راهنمای کاربر و بازتولید بسته |
| `manifest.json` | شناسنامه بسته: شمارش‌ها، فهرست ماژول‌ها، موتورهای AI، پیش‌نیازهای خودکار، هشدارهای کلید خارجی و بخش `reproduce` برای ساخت مجدد با همان انتخاب |
| `erp-selection.json` | انتخاب چهارسطحی کاربر (برای بازتولید دقیق) |

همه محتوا مشروط به تنظیمات است: بدون AI سرویس `ai-service` و کانتینر آن ساخته نمی‌شود، بدون IoT
سرویس `mosquitto` حذف می‌شود، با `db_driver=sqlite` سرویس پایگاه داده و Redis تغییر می‌کند و بدون
`include_docs` پوشه مستندات کوچک می‌ماند.

### پریست‌های صنعتی

| پریست | ماژول | قابلیت | نقطه AI |
| --- | ---: | ---: | ---: |
| `automotive` — خودروسازی و قطعه‌سازی | ۱۱۸ | ۲٬۰۴۱ | ۲۵۷ |
| `electronics` — الکترونیک و SMT | ۱۰۵ | ۱٬۸۸۵ | ۲۳۴ |
| `petrochemical` — پتروشیمی و انرژی | ۱۰۵ | ۱٬۸۶۵ | ۲۱۰ |
| `metals_foundry` — فلزی، ذوب و ریخته‌گری | ۱۰۳ | ۱٬۸۵۹ | ۲۰۸ |
| `food_pharma` — غذایی، دارویی و بهداشتی | ۹۴ | ۱٬۷۶۰ | ۲۰۳ |
| `general_discrete` — تولیدی عمومی (گسسته) | ۹۰ | ۱٬۷۲۹ | ۱۹۷ |
| `process_general` — صنایع فرآیندی عمومی | ۸۹ | ۱٬۶۹۱ | ۱۹۶ |
| `textile` — نساجی و پوشاک | ۸۳ | ۱٬۵۶۷ | ۱۸۳ |
| `packaging_print` — بسته‌بندی و چاپ | ۷۱ | ۱٬۴۲۱ | ۱۶۳ |
| `smb_minimal` — کارخانه کوچک (حداقلی) | ۳۲ | ۸۲۵ | ۱۰۱ |
| `enterprise_full` — فول ماژول (همه ۲۲ بخش) | ۱۳۰ | ۲٬۱۵۷ | ۲۶۶ |

### موتورهای هوش مصنوعی

| موتور | اندپوینت | الگوریتم‌ها |
| --- | --- | --- |
| `forecasting` | `/api/ai/forecast` | Prophet، XGBoost، LSTM |
| `reliability` | `/api/ai/reliability` | Weibull، Cox PH، Random Survival Forest |
| `optimization` | `/api/ai/optimize` | الگوریتم ژنتیک، Simulated Annealing، MILP |
| `anomaly` | `/api/ai/anomaly` | Isolation Forest، One-Class SVM، Autoencoder |
| `computer_vision` | `/api/ai/vision` | YOLOv8، ResNet Transfer Learning، OpenCV |
| `nlp` | `/api/ai/nlp` | Transformers (ParsBERT)، استخراج کلیدواژه، شباهت Embedding |
| `recommendation` | `/api/ai/recommend` | Matrix Factorization، KNN CF، Gradient Boosting Ranker |
| `quality_spc` | `/api/ai/quality` | قواعد Nelson، EWMA/CUSUM، شاخص‌های قابلیت |
| `classification` | `/api/ai/classify` | XGBoost، Logistic Regression، Random Forest |
| `simulation` | `/api/ai/simulate` | شبیه‌سازی رویداد گسسته، Monte Carlo، Agent-based |
| `mlops` | `/api/ai/mlops` | Feature Store، تشخیص Drift (PSI/KS)، AutoML |

هر موتور در نبود داده کافی، پاسخ **قاعده‌محور** با توضیح فارسی و `fallback=true` برمی‌گرداند؛ به
همین دلیل سرویس AI همیشه قابل اجرا و آزمون است. لایه زبانی (چت، خلاصه‌سازی، استخراج بند قرارداد)
اختیاری است و با کلید **AvalAI** فعال می‌شود.

---

## رابط کاربری سازنده

| صفحه | کار |
| --- | --- |
| خانه | آمار کاتالوگ، ۲۲ بخش، پریست‌ها، موتورهای AI، پوشش مدل داده |
| پیکربندگر | درخت چهارسطحی با چک‌باکس سه‌حالته و جست‌وجو، سبد انتخاب با برآورد/پوشش/پیش‌نیازها/موتورها، فرم ۹۷ کلید تنظیمات در ۸ گروه، دستیار هوشمند و گفت‌وگو، پروژه‌های ذخیره‌شده با فازبندی، تولید بسته |
| موتورهای AI | کارت ۱۱ موتور + جدول ۲۶۶ نقطه AI با فیلتر موتور و مدل/فلگ هر نقطه |
| بسته‌ها | فهرست بسته‌های تولیدشده با آمار و دانلود zip |
| جزئیات بسته | درخت فایل، نمایشگر کد با رنگ‌آمیزی، جدول ماژول‌ها، مانیفست JSON و آمار ناحیه‌ها |

ویژگی‌های پیاده‌سازی: راست‌به‌چپ کامل، رقم و تاریخ شمسی، تاریک/صنعتی، بدون هیچ کتابخانه UI،
ذخیره انتخاب در `localStorage`، حل وابستگی‌ها با debounce و منطق انتخاب چهارسطحی در سمت کاربر
که دقیقاً هم‌راستا با `expand_selection` بک‌اند است (انتخاب والد ⇒ فرزندان، لغو یک فرزند ⇒
ماده‌سازی والد، انتخاب همه فرزندان ⇒ فشرده‌سازی به والد).

---

## راستی‌آزمایی

همه اسکریپت‌ها با `.venv/bin/python` اجرا می‌شوند و کد خروج غیر صفر یعنی شکست.

| اسکریپت | چه چیزی را بررسی می‌کند |
| --- | --- |
| `scripts/validate_catalog.py` | ساختار چهارسطحی، یکتایی کدها، `deps` بدون مقصد، نویسه‌های نامجاز، شمارش‌ها → `data/catalog.json` |
| `scripts/validate_domain.py` | موجودیت‌ها، یکتایی جدول‌ها، کلیدهای خارجی، ترتیب توپولوژیک |
| `scripts/validate_package.py` | اعتبارسنجی ایستای یک بسته تولیدشده (نشتی `@@placeholder@@`، namespace/class PHP، syntax JS، JSON/YAML معتبر) |
| `scripts/smoke_generate.py` | تولید سریع یک بسته از یک پریست |
| `scripts/smoke_matrix.py` | چهار سناریوی ترکیبی (mysql/pgsql/sqlite × IoT × AvalAI × حجم ماژول) |
| `scripts/check_flags.py` | ۴۷ گزاره درباره اثر واقعی تنظیمات روی خروجی (فلگ‌ها، compose، env، داده نمونه) |
| `scripts/verify_generated.py` | راستی‌آزمایی سرتاسری: ایستا + مانیفست + pytest سرویس AI + ساخت فرانت‌اند |
| `scripts/verify_ui.py` | ساخت باندل سازنده + شکل پاسخ API + آزمون دود رندر همه صفحه‌ها |
| `scripts/package_checks.py` | کتابخانه مشترک بررسی‌ها (بین سه اسکریپت بالا) |

### آخرین نتایج

```
validate_catalog.py     ✓  ۲۲ بخش / ۱۳۰ ماژول / ۵۱۵ زیرماژول / ۲٬۱۵۷ قابلیت / ۲۶۶ AI
validate_domain.py      ✓  ۴۴۲ جدول / ۷٬۰۰۸ فیلد
smoke_matrix.py         ✓  ۴ از ۴ سناریو — ۰ شکست
check_flags.py          ✓  ۴۷ گزاره — ۰ شکست
verify_generated.py     ✓  ۰ شکست — ۳٬۴۸۱ فایل / ۴۱۰٬۸۴۵ خط / zip ۴٫۳۸ MB / ۱٫۰ ثانیه
                           ۱۵ آزمون pytest سرویس AI سبز، docker-compose ۸ سرویس، demo-data ۳۲۷ جدول، policy-bindings ۳۳۵ نگاشت
verify_ui.py            ✓  ۰ شکست — ۳۳ بررسی رندر و قرارداد داده
```

| سناریو (`smoke_matrix.py`) | ماژول | جدول | فیلد | AI | فایل | خط | zip | زمان |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `small-mysql` | ۲۲ | ۱۰۵ | ۱٬۴۴۶ | ۷۳ | ۱٬۱۹۱ | ۱۳۷٬۹۸۶ | ۱٫۵۱ MB | ۰٫۳ s |
| `sqlite-minimal` | ۳۸ | ۱۶۱ | ۲٬۳۳۵ | ۱۰۷ | ۱٬۵۴۵ | ۱۸۰٬۵۳۱ | ۱٫۹۳ MB | ۰٫۴ s |
| `pgsql-ai-avalai` | ۹۷ | ۳۴۱ | ۵٬۲۸۹ | ۲۰۵ | ۳٬۵۴۱ | ۴۱۷٬۹۱۶ | ۴٫۴۵ MB | ۱٫۰ s |
| `full-mysql-iot` | ۱۳۰ | ۴۴۲ | ۷٬۰۲۰ | ۲۶۶ | ۴٬۵۴۹ | ۵۳۶٬۸۸۰ | ۵٫۷۴ MB | ۱٫۱ s |

---

## API سازنده

۳۰ اندپوینت زیر `/api` (فهرست کامل و طرح درخواست/پاسخ در [`docs/03-builder-api.md`](docs/03-builder-api.md)):

| گروه | اندپوینت‌ها |
| --- | --- |
| سرویس | `GET /health` · `GET /meta` |
| کاتالوگ | `GET /catalog[?section=&depth=1..4]` · `/catalog/stats` · `/catalog/search` · `/catalog/modules/{code}` · `/catalog/ai-points` · `/catalog/dependencies` |
| پریست | `GET /presets` · `POST /presets/{key}/apply` |
| انتخاب | `POST /resolve` · `POST /selection/expand` |
| دستیار | `POST /advisor/recommend` (با AvalAI) · `POST /advisor/recommend-fast` (قاعده‌محور) · `POST /advisor/phases` · `POST /chat` |
| پروژه | `GET/POST /projects` · `GET/PUT/DELETE /projects/{id}` · `POST /projects/{id}/phases` |
| تولید | `POST /generate` |
| بسته‌ها | `GET /packages` · `GET /packages/{id}` · `/manifest` · `/tree` · `/file?path=` · `/download` · `DELETE /packages/{id}` |

---

## تنظیمات کارخانه

۹۷ کلید متعارف در `builder/backend/app/config.py:DEFAULT_FACTORY_SETTINGS` که از طریق
`normalize_settings()` نرمال‌سازی می‌شوند (کلیدهای قدیمی مثل `factory_name` و `base_currency` هم
پذیرفته می‌شوند). گروه‌ها:

| گروه | نمونه کلیدها |
| --- | --- |
| هویت | `company_name`, `company_name_en`, `company_national_id`, `economic_code`, `industry`, `employees_count`, `shifts_per_day` |
| مالی/تقویم | `currency`, `currency_label`, `calendar`, `timezone`, `week_start`, `weekend_days`, `fiscal_year_start_month`, `tax_rate_default`, `moadian_enabled`, `costing_method` |
| زیرساخت | `db_driver`, `db_host`, `db_port`, `db_database`, `cache_driver`, `queue_driver`, `session_driver`, `storage_disk`, `redis_host` |
| هوش مصنوعی | `ai_enabled`, `ai_human_approval`, `ai_service_url`, `avalai_enabled`, `avalai_api_key`, `avalai_model` |
| IoT | `iot_enabled`, `mqtt_host`, `mqtt_port`, `mqtt_topic_prefix`, `iot_sampling_seconds` |
| اطلاع‌رسانی | `mail_driver`, `mail_host`, `mail_from`, `sms_enabled`, `sms_provider` |
| مدیر/پشتیبان | `admin_email`, `admin_password`, `backup_enabled`, `backup_cron`, `backup_keep_days` |
| خروجی | `deploy_target`, `app_env`, `ssl_enabled`, `multi_tenant`, `include_demo_data`, `demo_data_months`, `demo_data_rows`, `demo_data_seed`, `include_tests`, `include_docs`, `include_mobile_pwa` |

گذرواژه‌های خالی هنگام تولید با مقدار امن تصادفی پر می‌شوند و در `.env` و `manifest.json` بسته
نوشته می‌شوند.

---

## محیط اجرا و محدودیت‌ها

- **پایتون ۳٫۱۱** و **Node ۱۸+** (این مخزن با Node ۲۲ آزموده شده).
- کد PHP/لاراول تولیدشده در این مخزن **اجرا نمی‌شود** (PHP و Composer نصب نیستند)؛ به‌جای آن
  بررسی‌های ایستای ساختاری انجام می‌شود (`php_structure`، namespace/class، نشتی placeholder،
  `check_demo_data` برای ترتیب توپولوژیک داده نمونه و `check_policy_bindings` برای نگاشت سیاست‌ها).
  کد پایتون تولیدشده (سرویس AI) واقعاً اجرا و با pytest آزموده می‌شود و فرانت‌اند تولیدشده
  واقعاً با Vite ساخته می‌شود.
- خروجی `dist-packages/` و `data/*.json` در `.gitignore` هستند.

---

## مستندات

| سند | محتوا |
| --- | --- |
| [`docs/01-architecture.md`](docs/01-architecture.md) | معماری سازنده و پشته تولیدشده |
| [`docs/02-catalog-and-domain.md`](docs/02-catalog-and-domain.md) | DSL کاتالوگ، ۲۲ بخش، مدل دامنه و قواعد نام‌گذاری |
| [`docs/03-builder-api.md`](docs/03-builder-api.md) | مرجع ۳۰ اندپوینت با شکل درخواست/پاسخ |
| [`docs/04-generation-engine.md`](docs/04-generation-engine.md) | مراحل خط لوله تولید، API `writers` و نگاشت تنظیمات |
| [`docs/05-builder-ui.md`](docs/05-builder-ui.md) | ساختار رابط کاربری، فروشگاه وضعیت و الگوریتم انتخاب |
| [`docs/06-verification.md`](docs/06-verification.md) | ۹ اسکریپت راستی‌آزمایی و نتایج |
| [`docs/07-roadmap.md`](docs/07-roadmap.md) | وضعیت فازها و کارهای باز |
