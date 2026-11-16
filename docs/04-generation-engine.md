# موتور تولید

`builder/backend/app/generator/` — ۱۴ فایل، ۱۹٬۶۷۵ خط. این بزرگ‌ترین بخش مخزن است چون هر فایل
خروجی یک قالب واقعی است، نه یک الگوی انتزاعی.

| فایل | خط | مسئولیت |
| --- | ---: | --- |
| `writers.py` | ۲۶۸ | ابزار نوشتن: `render`, `Package`, `php_value`, `php_array`, `slugify`, `pascal` |
| `settings_map.py` | ۲۷۷ | نرمال‌سازی ۹۷ کلید تنظیمات + کلیدهای قدیمی + تولید رمز امن + اشتقاق URLها |
| `domain_naming.py` | ۷۳ | نگاشت بخش کاتالوگ → namespace، نام‌گذاری کلاس‌ها و کارخانه `platform_module()` مشترک |
| `pipeline.py` | ۵۹۰ | هماهنگ‌کننده هفت مرحله‌ای تولید + مانیفست + zip |
| `laravel_routes.py` | ۶۲۹ | روت‌های API هر ماژول، web.php، Seederها و فراخوانی موتور داده نمونه |
| `demo_data.py` | ۸۸۲ | موتور داده نمونه تاریخ‌دار: `DemoDataSpec` (مشخصات توپولوژیک جداول) + `DemoHistorySeeder` (درج با کلید خارجی واقعی و سری زمانی) |
| `deploy.py` | ۱٬۱۸۲ | docker-compose، nginx، systemd، crontab، deploy.sh، Makefile، اسکریپت‌های عملیاتی |
| `laravel_core.py` | ۱٬۳۰۵ | اسکلت لاراول: composer.json، config/*.php، .env، Support/*، Providerها، middleware |
| `laravel_domain.py` | ۱٬۵۴۵ | برای هر موجودیت: migration, model, controller, request, resource, policy, factory, test, seeder, service |
| `docs.py` | ۱٬۷۲۸ | README فارسی و تا ۹ سند در `docs/` بسته |
| `laravel_system.py` | ۳٬۱۶۰ | احراز هویت، مجوزها، ممیزی، گزارش‌ساز، داشبورد، مرکز AI، دستورهای artisan، SystemSeeder |
| `frontend.py` | ۳٬۸۲۲ | SPA تولیدشده: منوی پویا، اسکیماهای جدول، صفحه‌های داده‌محور، مرکز AI، PWA |
| `ai_service.py` | ۴٬۱۷۰ | میکروسرویس FastAPI با ۱۱ موتور واقعی + آزمون‌های pytest |

---

## ۱) `writers.py` — زیرساخت نوشتن

```python
render(template, **values)      # جای‌گذاری @@name@@ — کلید ناشناخته دست‌نخورده می‌ماند
indent(text, prefix="    ")
php_value(value)                # مقدار PHP: رشته/عدد/bool/null (بدون پارامتر level)
php_array(data, level=0)        # آرایه چندسطحی PHP
php_array_literal(mapping, level=2)
json_pretty(data, indent_size=2)
slugify(text, fallback="erp")
pascal(text, fallback="Erp")
b64(data)                       # برای assetهای باینری PWA
```

`Package(root, name)` انباشته‌گر فایل‌هاست:

```python
package.add(rel_path, content, area="laravel-models", executable=False)
package.add_binary(rel_path, data, area="assets")
package.add_rendered(rel_path, template, area, **values)
package.add_many([(rel, content), …], area)
package.file_count / line_count / byte_count
package.stats()        # {files, lines, bytes, areas{…}, extensions{…}}
package.tree(max_depth=4)
package.write()        # نوشتن روی دیسک
```

`area` برچسب آماری است (نه مسیر) و در `stats.areas` و تب «ناحیه‌های خروجی» رابط کاربری دیده
می‌شود: `laravel-models`, `laravel-migrations`, `laravel-controllers`, `laravel-requests`,
`laravel-resources`, `laravel-policies`, `laravel-factories`, `laravel-tests`, `laravel-seeders`,
`laravel-services`, `laravel-routes`, `laravel-core`, `laravel-system`, `laravel-config`,
`laravel-support`, `laravel-middleware`, `laravel-providers`, `laravel-commands`, `frontend`,
`frontend-config`, `ai-service`, `deploy`, `docs`, `manifest`.

**قاعده مهم:** فایل zip همیشه **کنار** پوشه بسته ساخته می‌شود (`dist-packages/<id>.zip`)، نه داخل
آن؛ در غیر این صورت فایل فشرده در حال ساخت، خودش را می‌بلعد و حجم بی‌نهایت می‌شود.

---

## ۲) `settings_map.py` — نرمال‌سازی تنظیمات

```python
normalize_settings(raw, *, project_name, project_name_en, project_description,
                   slug, generate_secrets=True) -> dict
```

مراحل:

1. شروع از `DEFAULT_FACTORY_SETTINGS` (۹۷ کلید) و ادغام `raw`.
2. اعمال `ALIASES` برای کلیدهای قدیمی — `factory_name→company_name`,
   `factory_name_en→company_name_en`, `base_currency→currency`, `national_id→company_national_id`,
   `fiscal_year_start→fiscal_year_start_month`, `backup_schedule→backup_cron`,
   `storage_driver→storage_disk`, `ai_service_enabled→ai_enabled`,
   `iot_mqtt_host→mqtt_host`, `iot_mqtt_port→mqtt_port`.
3. نام‌ها و برچسب‌ها: `company_name`, `company_name_en`, `app_name` (از slug),
   `app_name_fa`, `currency_label` (از **ورودی خام** کاربر، وگرنه از `CURRENCY_LABELS`),
   `mail_from`, `mail_from_name`, `mqtt_topic_prefix`.
4. `ai_service_url` در صورت نبود، از `ai_service_host`/`ai_service_port` ساخته می‌شود.
5. `generate_secrets=True` ⇒ رمز تصادفی برای `db_password`, `db_root_password` (به‌جز sqlite),
   `admin_password` و `app_key` با پیشوند `base64:`.
6. تطبیق نوع بولین‌ها (`include_demo_data`, `include_tests`, `ai_enabled`, `iot_enabled`,
   `ssl_enabled`, `multi_tenant`).

`build_context()` در `pipeline.py` از این تنظیمات یک context می‌سازد که همه قالب‌ها می‌خوانند:

```
slug, pascal, app_name, app_name_fa, app_url, preview_origin, version, catalog_version,
package_id, generated_at, generated_at_jalali, section_meta, module_stats, sections, counts,
system_modules, preset, industry, industry_label, tagline, file_count, line_count,
counters{}, topological_order[], platform_name
```

---

## ۳) مراحل `pipeline.generate_package()`

| مرحله | کار |
| --- | --- |
| ۱ | `specs_for_modules()` — موجودیت‌ها، جداول، فیلدها با ترتیب توپولوژیک + اعتبارسنجی کلید خارجی |
| ۲ | ادغام متادیتای کاتالوگ با مشخصات دامنه برای هر ماژول (`slug`, `label_fa`, `menu_group`, `entities`, `ai_points`, `groups`, `items`, `priority`) |
| ۳ | ساخت `package_id` = `<slug>-<YYYYMMDD>-<HHMMSS>` و پوشه خروجی |
| ۴ | تولید لایه‌ها: `generate_core_files` → `generate_domain_files` → `generate_system_files` → `generate_routes` → `generate_seeders` → `generate_ai_service` (مشروط) → `generate_frontend` → `generate_deploy_files` |
| ۵ | مستندات دو بار: نخست با آمار میانی، سپس بازنویسی README/CHANGELOG با شمارش‌های نهایی |
| ۶ | `manifest.json` (شامل `reproduce.selection` و `reproduce.settings`) + `erp-selection.json` |
| ۷ | `package.write()` و ساخت zip کنار پوشه |

پیش از مرحله ۴ یک تنظیم باز محاسبه می‌شود:

```python
settings["ai_enabled"] = bool(settings.get("ai_enabled", True)) and bool(ai_points)
```

یعنی بدون نقطه AI انتخاب‌شده، سرویس AI، کانتینر آن، مرکز AI در فرانت‌اند و اسناد AI ساخته
نمی‌شوند و یک یادداشت به `notes` افزوده می‌شود.

---

## ۴) لایه لاراول

### دامنه (`laravel_domain.py`)

برای **هر موجودیت** نه فایل:

```
database/migrations/2026_01_01_<seq:06d>_create_<table>_table.php
app/Models/<Ns>/<Entity>.php
app/Http/Controllers/Api/<Ns>/<Entity>Controller.php
app/Http/Requests/<Ns>/Store<Entity>Request.php
app/Http/Requests/<Ns>/Update<Entity>Request.php
app/Http/Resources/<Ns>/<Entity>Resource.php
app/Policies/<Ns>/<Entity>Policy.php
database/factories/<Ns>/<Entity>Factory.php
tests/Feature/<Ns>/<Entity>Test.php
```

و برای **هر ماژول** دو فایل: `database/seeders/<Ns><CODE>Seeder.php` و
`app/Services/<Ns>/<Ns><CODE>Service.php`.

نکته حیاتی که در گذشته خطا می‌داد: نام کلاسی که به قالب داده می‌شود **کامل** است
(`<Ns>A1Seeder`)، پس قالب نباید دوباره پسوند `Seeder`/`Service` اضافه کند. نام‌ها از
`domain_naming.py:module_namespace()` و `_unique_class_name()` می‌آیند و جدول تکراری ⇒ خطای سخت.

### نوع فیلد → مایگریشن

`string,text,integer,bigint,decimal,boolean,date,datetime,time,json,uuid,enum,foreign` به متد
معادل لاراول نگاشت می‌شوند؛ `decimal` با `(18,4)`، `enum` با `options`، `foreign` با
`constrained()->cascadeOnDelete()` یا `nullOnDelete()` بسته به `nullable`، و پرچم‌ها به
`->nullable()`, `->unique()`, `->index()`, `->default()` تبدیل می‌شوند. `soft_deletes` و
`timestamps` از مشخصات موجودیت می‌آیند.

### سیستم (`laravel_system.py`)

احراز هویت Sanctum، کنترلرهای Feature/Ai/Audit/Report/Dashboard/System، `SystemSeeder` با ۱۱ نقش
و همه مجوزها (`<module_slug>.<table>.{view,create,edit,delete,approve}`)،
`config/{features,reports,ai}.php`، دستورهای `erp:install`, `features:sync`, `backup`,
`ai:health`، و کلاس‌های `App\Support\{Jalali,PersianText,AvalAiClient,AiServiceClient,ActivityLogger,ModuleRegistry}`.

### روت‌ها و Seederها (`laravel_routes.py`)

`routes/modules/<slug>.php` با `auth:sanctum` و `permission:` برای هر جدول،
`routes/api.php` و `routes/web.php` که فایل‌های ماژول را بارگذاری می‌کنند، و
`database/seeders/DatabaseSeeder.php` که `SystemSeeder` و همه `<Ns><CODE>Seeder`ها را به ترتیب
توپولوژیک صدا می‌زند. ماژول‌های پلتفرمی با کد مجازی `S0` ⇒ `SystemS0Seeder`.

هنگامی که `include_demo_data=true` باشد، `generate_seeders` موتور داده نمونه
(`demo_data.py`) را صدا می‌زند که `DemoDataSeeder` دو لایه را می‌سازد:

1. **لایه ماژول** — هر `<Ns><CODE>Seeder` فقط جداول *بدون* کلید خارجی اجباری را با
   `Model::factory()->count(5)` درج می‌کند. جداول با کلید خارجی اجباری عمداً با `factory`
   پر نمی‌شوند (کارخانه‌ها ستون کلید خارجی را commented-out می‌گذارند، پس درج واقعی با
   خطای NOT NULL/FK شکست می‌خورد) و به لایه دوم سپرده می‌شوند.
2. **لایه تاریخچه** — `Demo/DemoHistorySeeder.php` مشخصات ستون‌ها را از `Demo/DemoDataSpec.php`
   می‌خواند (که خود از همان مدل دامنه مایگریشن‌ها، به ترتیب توپولوژیک ساخته شده) و برای هر
   جدول: کلید خارجی اجباری را از شناسه‌های واقعی والد انتخاب می‌کند، تاریخ‌ها را در بازه
   `demo_data_months` پخش می‌کند، و برای ستون‌های نشانه‌گذاری‌شده سری زمانی با روند + فصلانگی
   شمسی + نویز + ناهنجاری عمدی + تخریب تدریجی لرزش می‌سازد. جدول با والد ناموجود با هشدار
   رد می‌شود (نه درج ناموفق) و جداول خودارجاع ردیف‌به‌ردیف درج می‌شوند. RNG با بذر
   `demo_data_seed` ⇒ خروجی تکرارپذیر. جزئیات در `docs/07-roadmap.md` (فاز ۴).

---

## ۵) لایه فرانت‌اند تولیدشده (`frontend.py`)

React 18 + Vite 6 + react-router-dom 6.28، راست‌به‌چپ، بدون کتابخانه UI (همه CSS در یک فایل
طراحی‌شده). اجزای کلیدی:

- `src/config/menu.js` — منوی پویا از ماژول‌های انتخابی (سبک، همیشه بارگذاری می‌شود)
- `src/config/schemas.js` + `src/lib/schemas.js` — اسکیماهای جدول به‌صورت **lazy** تا حجم اولیه
  کوچک بماند (با ۹۵ ماژول ~۷۸۰ کیلوبایت، gzip ~۷۴ کیلوبایت)
- `src/lib/api.js` — کلاینت با `Authorization: Bearer` از `localStorage['<slug>.token']` و
  هدر `X-Company-Id`
- صفحه داده‌محور واحد که از اسکیما ساخته می‌شود: فهرست با جست‌وجو/فیلتر/صفحه‌بندی، فرم
  ایجاد/ویرایش از روی نوع و پرچم فیلدها، نمای جزئیات، حذف با تأیید
- مرکز AI، گزارش‌ساز، داشبورد، ممیزی — همه مشروط به فلگ‌های
  `AI_ENABLED`, `PWA_ENABLED`, `REPORT_TEMPLATES_ENABLED`
- PWA (manifest + service worker + آیکون‌ها) فقط با `include_mobile_pwa=true`

---

## ۶) سرویس AI تولیدشده (`ai_service.py`)

FastAPI روی پورت ۸۰۰۱ با ساختار `ai-service/app/…`:

| مسیر | محتوا |
| --- | --- |
| `/health` | سلامت سرویس و نسخه |
| `/capabilities` | `{total, enabled_engines, by_engine, catalog, llm_enabled, company}` |
| `/capabilities/{code}` | جزئیات یک نقطه AI |
| `/models` | فهرست مدل‌های ثبت‌شده (`model_id` هر نقطه) |
| `/ai` | نقطه ورود عمومی |
| `/ai/{forecast,optimize,anomaly,reliability,spc,vision,nlp,recommend,classify,simulate,mlops}` | یازده اندپوینت موتورها |

هر موتور با numpy/pandas/scikit-learn پیاده‌سازی واقعی دارد (مثلاً `quality_spc` قواعد Nelson و
EWMA/CUSUM و شاخص‌های قابلیت `Cp/Cpk` را محاسبه می‌کند) و در نبود داده کافی پاسخ قاعده‌محور با
`fallback=true` و `explanation` فارسی برمی‌گرداند. `tests/` شامل ۱۵ آزمون pytest است که در
`scripts/verify_generated.py` واقعاً اجرا می‌شوند.

کلاینت سمت لاراول (`AiServiceClient`) همان `feature_flag`ها را می‌خواند، پس خاموش کردن یک نقطه AI
در `config/features.php` هم اندپوینت لاراول و هم سرویس پایتون را بی‌اثر می‌کند.

---

## ۷) لایه استقرار (`deploy.py`)

- `docker-compose.yml` با ۸ سرویس: `db`, `redis`, `mqtt` (مشروط به `iot_enabled`),
  `ai-service` (مشروط به `ai_enabled`), `app`, `queue`, `scheduler`, `web` — با healthcheck و
  حجم‌ها و شبکه نام‌گذاری‌شده از `project_slug`
- `deploy/nginx/` با پشتیبانی `ssl_enabled`، `deploy/systemd/erp-*.service` برای استقرار بدون
  Docker، `deploy/crontab` از `backup_cron`
- `deploy.sh` (نصب/ارتقا/پشتیبان/سلامت/بازگردانی)، `Makefile` با ۲۱ هدف، اسکریپت‌های
  `backup.sh`, `restore.sh`, `upgrade.sh`, `healthcheck.sh`
- `.env` و `.env.example` واقعی با همه مقدارهای مشتق‌شده از تنظیمات

اثر هر تنظیم روی این لایه با `scripts/check_flags.py` assert می‌شود (مثلاً `db_driver=sqlite`
⇒ نبود سرویس db در compose و `DB_CONNECTION=sqlite` در `.env`).

---

## ۸) مستندات بسته (`docs.py`)

`README-fa.md` و تا ۹ سند در `docs/` بسته: معماری، راهنمای نصب، فهرست ماژول‌ها، مدل داده،
قابلیت‌های هوش مصنوعی، مرجع API، عملیات و پشتیبان‌گیری، راهنمای کاربر، بازتولید بسته. هر سند
مشروط به فلگ مربوطه است (بدون AI سند AI ساخته نمی‌شود). این فایل‌ها **دو بار** تولید می‌شوند:
بار نخست با آمار میانی و بار دوم با شمارش‌های نهایی، تا اعداد داخل متن با واقعیت بسته یکی باشد.

---

## ۹) مانیفست

`manifest.json` کلیدهای زیر را دارد:

```
package_id, package_name, created_at, created_at_jalali, generator, project, settings,
counts{sections,modules,groups,items,ai_points,tables,fields,ai_engines,estimated_files,files,lines,bytes,entities},
modules[{code,slug,label_fa,name_en,menu_group,derived,priority,entities,ai_points,groups,items}],
ai_engines[{key,engine,name_fa,name_en,category,endpoint,model_dir,algorithms,pip_packages,…}],
ai_points[…], auto_added[…], dependency_reasons{…}, system_modules[…], platform_entities[…],
foreign_key_warnings[…], counters{…}, stats{files,lines,bytes,areas,extensions}, tree[…],
notes[…], reproduce{selection, settings}
```

`reproduce` اجازه می‌دهد همان بسته را دقیقاً دوباره بسازید؛ `erp-selection.json` همان انتخاب
چهارسطحی را به‌تنهایی نگه می‌دارد.
