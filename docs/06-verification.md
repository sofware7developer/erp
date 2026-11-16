# راستی‌آزمایی

نه اسکریپت در `scripts/` (۱٬۳۰۹ خط) که هر کدام یک سطح از صحت را می‌سنجند. همه با
`.venv/bin/python scripts/<name>.py` اجرا می‌شوند و **کد خروج غیر صفر یعنی شکست**.

```
validate_catalog.py     صحت کاتالوگ            (پیش از هر چیز دیگر)
validate_domain.py      صحت مدل دامنه
smoke_generate.py       تولید سریع یک بسته
validate_package.py     اعتبارسنجی ایستای یک بسته تولیدشده
smoke_matrix.py         چهار سناریوی ترکیبی تنظیمات
check_flags.py          اثر واقعی پرچم‌ها روی خروجی
verify_generated.py     راستی‌آزمایی سرتاسری بسته
verify_ui.py            راستی‌آزمایی رابط کاربری سازنده
package_checks.py       کتابخانه مشترک بررسی‌ها
```

ترتیب پیشنهادی پس از هر تغییر بزرگ:

```bash
.venv/bin/python scripts/validate_catalog.py
.venv/bin/python scripts/validate_domain.py
.venv/bin/python scripts/check_flags.py
.venv/bin/python scripts/smoke_matrix.py
.venv/bin/python scripts/verify_generated.py
.venv/bin/python scripts/verify_ui.py
```

---

## `validate_catalog.py`

| بررسی | جزئیات |
| --- | --- |
| متن خالی | هیچ نام/عنوانی خالی نیست |
| نویسه غیرمجاز | نبود CJK، هیراگانا/کاتاکانا، هانگول، سیریلیک و نویسه‌های کنترلی در متن فارسی |
| کد بخش | یک حرف بزرگ و یکتا |
| ترتیب ماژول | `A1, A2, … A8` به ترتیب و بدون کد تکراری |
| کد زیرماژول | `<module>.<n>` به ترتیب و یکتا |
| زیرماژول خالی | هر زیرماژول دست‌کم یک زیرمجموعه دارد |
| کد زیرمجموعه | `<group>.<n>` به ترتیب و یکتا |
| وابستگی | هر `@@dep=` به کد موجود (زیرمجموعه/زیرماژول/ماژول) اشاره می‌کند |

خروجی جانبی: نوشتن `data/catalog.json` (۶۴۰ کیلوبایت) که در `.gitignore` است.

## `validate_domain.py`

- هر ۱۳۰ ماژول کاتالوگ مشخصات دامنه دارند (دستی یا مشتق)
- `validate_foreign_keys()` — هیچ کلید خارجی بدون مقصد نیست
- گزارش پوشش (دستی/مشتق/جدول/فیلد)
- دو سناریوی نمونه: حل وابستگی `[A1,A2,A3,F1,F2,E1]` و سناریوی کامل ۱۳۰ ماژولی با
  `specs_for_modules()` (که خودش ترتیب توپولوژیک و یکتایی جدول‌ها را hard-fail می‌کند)

## `package_checks.py` — کتابخانه مشترک

`validate_package(root)` یک دیکشنری مشکل برمی‌گرداند با این دسته‌ها:

| دسته | چه چیزی را می‌گیرد |
| --- | --- |
| `empty` | فایل خالی |
| `placeholders` | نشتی `@@something@@` (نشانه قالب جای‌گذاری‌نشده) |
| `bad_chars` | نویسه‌های غیرمجاز (CJK/سیریلیک/کنترلی) |
| `py_syntax` | `ast.parse` روی همه فایل‌های پایتون |
| `json` | JSON معتبر |
| `yaml` | YAML معتبر (PyYAML) |
| `php_structure` | شروع با `<?php`، توازن آکولاد/پرانتز، تطابق namespace با مسیر فایل، تطابق نام کلاس با نام فایل |
| `sh` | `bash -n` روی اسکریپت‌های پوسته |
| `js_syntax` | `node --check` روی فایل‌های JS |

به‌علاوه:

- `run_ai_tests(root)` — اجرای pytest روی `ai-service/tests` تولیدشده
- `build_frontend(root)` — `npm install` و `npm run build` واقعی روی فرانت‌اند تولیدشده
- `check_compose_services(root)` — سازگاری سرویس‌های docker-compose با تنظیمات بسته
- `check_manifest(root)` — سازگاری `manifest.json` با فایل‌های واقعی روی دیسک
- `check_demo_data(root)` — وجود سه‌گانه فایل‌های داده نمونه، معتبر بودن ثابت‌های `MONTHS`/`ROWS`/`SEED` و ترتیب توپولوژیک کلیدهای خارجی اجباری (والد پیش از فرزند)
- `check_policy_bindings(root)` — برای هر نگاشت سیاست در `PolicyServiceProvider`، وجود فایل مدل و سیاست در مسیر متناظر (نگهبان بازگشت برای ناهمسانی فضای‌نام، مثلاً `Core` به‌جای `System`)
- `summarize(problems)` — شمارش و نمونه‌گیری برای چاپ گزارش

## `smoke_generate.py`

تولید سریع یک بسته از یک پریست (`--preset`) و اجرای اعتبارسنجی ایستا؛ برای حلقه توسعه کوتاه.

## `smoke_matrix.py`

چهار سناریوی ترکیبی و مستقل:

| سناریو | انتخاب | تنظیمات کلیدی |
| --- | --- | --- |
| `small-mysql` | `[A1, B1, F9]` | `db_driver=mysql` |
| `full-mysql-iot` | پریست `enterprise_full` (۱۳۰ ماژول) | mysql + IoT + AI + demo data |
| `sqlite-minimal` | پریست `smb_minimal` | sqlite + cache=file + queue=sync + session=file + بدون AI/IoT/آزمون/demo |
| `pgsql-ai-avalai` | پریست `food_pharma` | pgsql + IoT + AI + `avalai_api_key` تستی + `deploy_target=bare-metal` |

برای هر سناریو: اعتبارسنجی ایستا + چاپ شمارش‌ها. هر بسته پس از بررسی پاک می‌شود تا دیسک پُر نشود.

### آخرین نتیجه

```
case                mod   ent    fld     ai     files   lines     zipMB   sec    validation
small-mysql         22    105    1446    73     1191    137986    1.51    0.3    ok
full-mysql-iot      130   442    7020    266    4549    536880    5.74    1.1    ok
sqlite-minimal      38    161    2335    107    1545    180531    1.93    0.4    ok
pgsql-ai-avalai     97    341    5289    205    3541    417916    4.45    1.0    ok

failures: 0
```

## `check_flags.py`

نه گروه پرچم، هر کدام با ساخت **دو بسته** (فعال/غیرفعال) و مقایسه؛ مجموعاً ۴۷ گزاره:

| پرچم | چه چیزی assert می‌شود |
| --- | --- |
| `ai_enabled` | وجود `ai-service/app/main.py` و `deploy/systemd/erp-ai.service`؛ `ai-service:` در compose؛ در حالت خاموش، یادداشت «سرویس هوش مصنوعی غیرفعال است» |
| `include_docs` | وجود `docs/01-architecture.md` و `docs/04-data-model.md`؛ `README-fa.md`/`LICENSE`/`CHANGELOG.md` همیشه هست |
| `generate_api_docs` | وجود `docs/06-api-reference.md` |
| `include_mobile_pwa` | وجود `manifest.webmanifest`, `sw.js`, `icon.svg`؛ ثبت service worker در `main.jsx` و manifest در `index.html` |
| `include_report_templates` | وجود `backend/config/reports.php` |
| `include_tests` | وجود `backend/phpunit.xml` و ≥۱۰ فایل در `tests/Feature` (در حالت خاموش: صفر) |
| `iot_enabled` | وجود `deploy/mosquitto/config/mosquitto.conf` و `mosquitto` در compose |
| `include_demo_data` | وجود `DemoDataSeeder.php` و `Demo/DemoDataSpec.php` و `Demo/DemoHistorySeeder.php`؛ ارجاع `DemoDataSeeder` به `DemoHistorySeeder`؛ یادداشت «داده نمونه فعال/غیرفعال» در seeder ماژول |
| `db_driver` | sqlite ⇒ `DB_CONNECTION: sqlite` در compose؛ pgsql ⇒ `postgres:16-alpine` و `DB_CONNECTION=pgsql` در `.env`؛ mysql ⇒ `mysql:8.4` |

## `verify_generated.py`

راستی‌آزمایی سرتاسری در چهار مرحله:

```bash
.venv/bin/python scripts/verify_generated.py [--no-build] [--preset smb_minimal]
```

۱. اعتبارسنجی ایستای همه فایل‌ها (`validate_package`)
۲. سازگاری `manifest.json` و `docker-compose.yml`، سلامت داده نمونه (`check_demo_data`) و نگاشت سیاست‌ها (`check_policy_bindings`)
۳. اجرای آزمون‌های pytest سرویس AI تولیدشده
۴. ساخت واقعی فرانت‌اند تولیدشده (`npm install && npm run build`) — با `--no-build` رد می‌شود

در پایان `frontend/node_modules` و `frontend/dist` پاک می‌شوند ولی بسته برای مرور می‌ماند.

### آخرین نتیجه

```
بسته: factory-erp-20261116-170649
ماژول‌ها: 95 | جداول: 335 | فیلدها: 5173 | نقاط AI: 202
فایل‌ها: 3481 | خط‌ها: 410845 | zip: 4.38 MB | زمان: 1.0s

۱) اعتبارسنجی ایستا        PASS  0 مشکل
۲) مانیفست و پشته استقرار  PASS  manifest: 3481 فایل، 95 ماژول
                           PASS  docker-compose: 8 سرویس
                           PASS  demo-data: 327 جدول، 146 کلید خارجی اجباری مرتب‌شده
                           PASS  policy-bindings: 335 نگاشت سیاست، همه مدل‌ها/سیاست‌ها موجود
۳) آزمون‌های سرویس AI      PASS  15 passed
۴) ساخت فرانت‌اند          SKIP  (--no-build)

failures: 0
```

با بیلد کامل فرانت‌اند تولیدشده، خروجی Vite چنین است: `index.html` ۱٫۸۸ کیلوبایت، CSS ۱۱٫۵۳
کیلوبایت، JS اصلی ۱۳۵٫۷۰ کیلوبایت، چانک react ۱۶۵٫۱۵ کیلوبایت و چانک lazy اسکیماها
۷۷۷٫۹۱ کیلوبایت (gzip ۷۴٫۳۳ کیلوبایت) — این چانک با تعداد ماژول‌ها بزرگ می‌شود که عمدی است
(فقط وقتی لازم شود بارگذاری می‌شود).

## `verify_ui.py`

```bash
.venv/bin/python scripts/verify_ui.py [--no-build] [--no-smoke] [--port 8123]
```

۱. ساخت باندل رابط کاربری سازنده (`npm run build`)
۲. بالا آوردن سرویس FastAPI روی یک پورت آزاد و بررسی شکل پاسخ‌ها: `health`, `meta`
   (شمارش‌ها، موتورها، ۹۷ کلید تنظیمات، اهداف و صنایع دستیار)، `catalog?depth=4`, `presets`,
   `presets/{key}/apply` + `resolve`, `packages`, `packages/{id}`, `tree`, `file`
۳. اجرای `npm run smoke` با `SMOKE_API` که به همان سرویس موقت اشاره می‌کند

سرویس در پایان بسته می‌شود. آخرین اجرا: **۳۳ بررسی، ۰ شکست**.

---

## چه چیزی آزمون نمی‌شود (و چرا)

| مورد | وضعیت | دلیل |
| --- | --- | --- |
| اجرای کد PHP/لاراول تولیدشده | فقط بررسی ایستای ساختاری | PHP و Composer در محیط توسعه نصب نیستند |
| اجرای `docker compose up` | فقط بررسی سازگاری متن compose | Docker در دسترس نیست |
| اتصال واقعی به AvalAI | با کلید تستی جعلی | کلید واقعی در مخزن نگه داشته نمی‌شود؛ در نبود آن، مسیر قاعده‌محور آزموده می‌شود |
| پایگاه داده واقعی (mysql/pgsql) | مایگریشن‌ها فقط ایستا بررسی می‌شوند | سرور DB در دسترس نیست |
| سرویس AI تولیدشده | **واقعاً اجرا و آزموده می‌شود** (۱۵ آزمون pytest) | پایتون و numpy/pandas/scikit-learn در دسترس‌اند |
| فرانت‌اند تولیدشده | **واقعاً با Vite ساخته می‌شود** | Node در دسترس است |
| رابط کاربری سازنده | **واقعاً رندر می‌شود** (SSR smoke) | Node در دسترس است |

نکته محیطی: در این sandbox بسته `httpx2` نصب است و یک shim محلی
(`.venv/.../httpx/__init__.py`) آن را به نام `httpx` صادر می‌کند تا کد تولیدشده اجرا شود. این
یک ترفند **محلی** است و در کد تولیدی یا `requirements.txt` بازتاب ندارد (آنجا `httpx` آمده است).
