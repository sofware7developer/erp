# مرجع API سازنده

۳۰ اندپوینت زیر `/api` به‌همراه `GET /` (سرو کردن رابط کاربری یا اطلاعات سرویس).
مستندات تعاملی خودکار: `/api/docs` (Swagger) و `/api/redoc`.

- پروتکل: JSON با `Content-Type: application/json`
- خطاها: `{"detail": "پیام فارسی"}` با کد وضعیت مناسب (۴۰۰ انتخاب نامعتبر، ۴۰۴ یافت نشد)
- پاسخ‌های بزرگ‌تر از ۱ کیلوبایت gzip می‌شوند (کاتالوگ کامل: ۴۰۰ → ۶۶ کیلوبایت)
- CORS برای همه مبدأها باز است (`allow_origins=["*"]`) چون سرویس محلی/داخلی است

---

## سرویس

### `GET /api/health`

```json
{"status":"ok","app":"Smart Factory ERP Builder","app_fa":"سازنده ERP هوشمند کارخانه‌ای",
 "version":"1.0.0","catalog_version":"1.0.0","time":"2026-11-16T15:58:25+00:00",
 "avalai_configured":false}
```

### `GET /api/meta`

| کلید | محتوا |
| --- | --- |
| `counts` | `{sections:22, modules:130, groups:515, items:2157, ai_points:266}` |
| `db_drivers`, `queue_drivers`, `storage_drivers`, `deploy_targets` | فهرست `{id,label,note}` برای فرم تنظیمات |
| `default_settings` | ۹۷ کلید متعارف تنظیمات کارخانه |
| `ai_engines` | ۱۱ موتور با `{key,name_fa,name_en,category,algorithms,endpoint,uses_llm,realtime,metrics,description}` |
| `advisor_goals` | ۳۷ هدف کسب‌وکاری شناخته‌شده برای دستیار (`GOAL_MODULES`) |
| `industries` | ۱۱ صنعت `{id,label,note}` هم‌تراز با پریست‌ها |
| `avalai` | `{configured, base_url, model, key_set}` |
| `domain_coverage` | `{total_modules, handwritten[], handwritten_count, derived[], derived_count, entities_total, fields_total}` |
| `system_modules` | ۹ ماژول زیرساختی که همیشه افزوده می‌شوند |

---

## کاتالوگ

### `GET /api/catalog?section=A&depth=1..4`

`depth` عمق درخت را کنترل می‌کند (۱ = فقط بخش‌ها، ۴ = تا زیرمجموعه‌ها). پاسخ:

```json
{"sections":[{"code":"A","name":"هسته تولید","name_en":"Manufacturing Core","color":"#4f46e5",
   "icon":"factory","level":1,"module_count":8,"item_count":261,"ai_count":29,"description":"…",
   "modules":[{"code":"A1","name":"برنامه‌ریزی تولید","name_en":"Production Planning","level":2,
     "icon":"calendar-clock","summary":"…","color":"#4f46e5","group_count":8,"item_count":62,
     "ai_count":12,"groups":[{"code":"A1.1","name":"…","name_en":"…","level":3,"item_count":8,
       "ai_count":1,"items":[{"code":"A1.1.4","name":"هماهنگی با سفارشات فروش","ai":false,
         "deps":["E1.2"],"entity":null,"role":null,"level":4}]}]}]}],
 "stats":{ … }}
```

### `GET /api/catalog/stats`

`{totals:{…}, per_section:[{code,name,name_en,color,icon,modules,groups,items,ai_points}], version}`

### `GET /api/catalog/search?q=کالیبراسیون&limit=60`

```json
{"query":"کالیبراسیون","count":7,"results":[
  {"code":"B5.2.3","name":"کالیبراسیون تجهیزات اندازه‌گیری","ai":false,"group_code":"B5.2",
   "group_name":"…","module_code":"B5","module_name":"…","section_code":"B","section_name":"…"}]}
```

### `GET /api/catalog/modules/{code}`

```json
{"module":{…},"section":{…},
 "dependencies":[{"code":"A3","name":"مدیریت BOM","reason":"وابستگی زیرمجموعه A1.2.5"},
                 {"code":"D4","name":"کالا و موجودی","reason":"ماژول پشتیبانی دامنه"}],
 "domain":{"entities":[{"name":"…","table":"…","label_fa":"…","fields":34,"derived":false}]},
 "ai_points":[…]}
```

`dependencies` از دو منبع ساخته می‌شود: `@@dep=` های زیرمجموعه‌های ماژول (که به یک کد ماژول
می‌رسند) و `SUPPORT_MODULES` در دامنه.

### `GET /api/catalog/ai-points?module=A&engine=forecasting`

```json
{"count":47,"ai_points":[{"code":"A1.4.5","name":"پیش‌بینی تنگناهای ظرفیتی","module_code":"A1",
  "module_name":"برنامه‌ریزی تولید","section_code":"A","engine":"forecasting",
  "engine_name_fa":"موتور پیش‌بینی سری زمانی","endpoint":"/api/ai/forecast",
  "algorithms":["Prophet","XGBoost","LSTM"],"uses_llm":false,"realtime":false,
  "model_id":"forecasting_a1_4_5","feature_flag":"ai.forecasting.a1_4_5"}]}
```

### `GET /api/catalog/dependencies`

`{item_dependencies:{…}, module_dependencies:{…}, system_modules:[…]}` — نگاشت کامل وابستگی‌ها برای
تحلیل سمت کاربر.

---

## پریست‌ها

### `GET /api/presets`

```json
{"presets":[{"key":"automotive","name":"خودروسازی و قطعه‌سازی","name_en":"Automotive",
  "icon":"car","color":"#dc2626","description":"…","module_count":118,"item_count":2041,
  "ai_count":257,"sections":["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V"]}]}
```

### `POST /api/presets/{key}/apply`

علاوه بر خود پریست: `resolution` (خروجی کامل `/resolve`)، `settings` (زیرمجموعه تنظیمات پیشنهادی
پریست)، `ai_points` و `modules/groups/items` برای ساخت انتخاب در سمت کاربر. کد نامعتبر ⇒ ۴۰۴.

---

## انتخاب

### `POST /api/resolve`

```json
{"selection":{"sections":[],"modules":["A1"],"groups":[],"items":[],"ai_points":[],"mode":"custom"}}
```

پاسخ:

| کلید | محتوا |
| --- | --- |
| `selection` | انتخاب نرمال‌سازی‌شده |
| `resolved_modules` | ماژول‌های نهایی پس از افزودن پیش‌نیازها |
| `auto_added` | ماژول‌هایی که خودکار افزوده شدند |
| `reasons` | دلیل هر افزودن (`{code: reason}`) |
| `invalid` | کدهای نامعتبر در ورودی |
| `counts` | `{sections,modules,groups,items,ai_points,tables,fields,ai_engines,estimated_files}` |
| `sections` | پوشش هر بخش: `{code,name,modules_total,modules_selected,items_total,items_selected,ai_total,ai_selected,percent}` |
| `ai_engines` | موتورهای درگیر |
| `ai_points` | جزئیات نقاط AI فعال |
| `estimated_tables`, `estimated_files`, `table_count` | برآوردها |

برآورد فایل: `96 + entities*9 + modules*7 + ai_points*3`.

### `POST /api/selection/expand`

`{expanded, counts, coverage, ai_engines, module_names}` — گسترش سریع بدون محاسبه کامل دامنه.

---

## دستیار هوشمند

### `POST /api/advisor/recommend-fast` (قاعده‌محور، بدون تماس خارجی)

```json
{"industry":"automotive","employees_count":320,"shifts_per_day":3,"production_lines":4,
 "warehouses_count":3,"goals":["کاهش ضایعات","بهبود کیفیت"],
 "budget_level":"high","ai_appetite":"high","note":""}
```

پاسخ: `{modules, ai_points, rationale[{type,title,detail}], ai_level, size_bucket, preset_key, auto_added}`

منطق: نزدیک‌ترین پریست صنعتی ⇒ ماژول‌های تخصصی صنعت ⇒ ماژول‌های اهداف اعلام‌شده
(`GOAL_MODULES`) ⇒ سقف ماژول بر پایه اندازه سازمان ⇒ سطح AI بر پایه بودجه و اشتیاق ⇒ حل
پیش‌نیازها. `rationale` دلیل هر مرحله را به فارسی برمی‌گرداند.

### `POST /api/advisor/recommend`

همان ورودی، اما در صورت فعال بودن AvalAI نتیجه قاعده‌محور توسط LLM بازبینی می‌شود
(افزودن/حذف ماژول با JSON mode؛ ماژول‌های سیستمی هرگز حذف نمی‌شوند).

پاسخ: `{recommended_modules, recommended_ai_points, phases, coverage, rationale, ai_level,
size_bucket, llm_used, llm_note}`.

> توجه: کلیدهای این مسیر (`recommended_modules`/`recommended_ai_points`) با مسیر سریع
> (`modules`/`ai_points`) متفاوت است. `AdvisorPanel` در رابط کاربری پاسخ را در مرز دریافت
> یکدست می‌کند تا هر دو مسیر یکسان کار کنند.

### `POST /api/advisor/phases`

`{"modules":["A1","B1"],"ai_points":[…]}` → `{phases[{order,title,description,duration_months,modules,ai_points,milestones,deliverables}], total_months}`

### `POST /api/chat`

`{message, context{}, history[{role,content}]}` → `{answer, llm_used, source: "avalai"|"heuristic", note}`

در نبود کلید AvalAI، پاسخ قاعده‌محور از جست‌وجوی کاتالوگ ساخته می‌شود (همراه با نزدیک‌ترین
قابلیت‌ها و کد ماژول‌ها).

---

## پروژه‌ها

| اندپوینت | کار |
| --- | --- |
| `GET /api/projects` | `{projects:[…]}` |
| `GET /api/projects/{id}` | یک پروژه کامل |
| `POST /api/projects` | ایجاد (بدنه: `ProjectConfig`) |
| `PUT /api/projects/{id}` | به‌روزرسانی |
| `DELETE /api/projects/{id}` | `{deleted: id}` یا ۴۰۴ |
| `POST /api/projects/{id}/phases` | ساخت و ذخیره فازبندی → `{project, phases, total_months}` |

شکل پروژه: `{id,name,name_en,description,preset_key,selection{…},settings{…},phases[],created_at,updated_at}`
ذخیره در `data/projects.json` (در `.gitignore`).

---

## تولید بسته

### `POST /api/generate`

```json
{"project":{"name":"ERP صنایع غذایی پارس","name_en":"Pars Food ERP","description":"…",
   "preset_key":"food_pharma",
   "selection":{"modules":["A1","B1","C1"],"groups":[],"items":[],"ai_points":[],"mode":"custom"},
   "settings":{"db_driver":"pgsql","iot_enabled":true}},
 "save_project":true}
```

پاسخ (`GenerateResult`):

```json
{"package_id":"pars-food-industries-erp-20261116-155853","package_name":"ERP کارخانه نمونه — …",
 "output_dir":"pars-food-industries-erp-20261116-155853",
 "zip_path":"pars-food-industries-erp-20261116-155853.zip",
 "zip_size_bytes":1665181,"file_count":1259,"line_count":142798,
 "created_at":"2026-11-16T15:58:54","stats":{"files":…,"lines":…,"bytes":…,"areas":{…},"extensions":{…}},
 "tree":[…],"manifest":{…},"notes":["بسته در `…` نوشته شد …","برای استقرار: ./deploy.sh …"]}
```

`output_dir` و `zip_path` فقط **نام** هستند (مسیر مطلق سرور به کلاینت داده نمی‌شود). انتخاب خالی
یا نامعتبر ⇒ ۴۰۰ با پیام فارسی.

---

## بسته‌ها

| اندپوینت | پاسخ |
| --- | --- |
| `GET /api/packages` | `{packages:[{package_id,name,created_at,created_at_jalali,preset_key,project_name,modules,entities,ai_points,file_count,line_count,zip_exists,zip_size_bytes,stats,notes}]}` |
| `GET /api/packages/{id}` | همان خلاصه + `manifest_counts`, `modules[]` (با `code,label_fa,name_en,slug,menu_group,entities,ai_points,groups,items,derived,priority`), `ai_engines[]`, `selection`, `top_level[]` |
| `GET /api/packages/{id}/manifest` | `manifest.json` کامل |
| `GET /api/packages/{id}/tree` | `{package_id, tree:[{name,path,type,size,lines?,children?}]}` تا عمق ۸ |
| `GET /api/packages/{id}/file?path=backend/app/Models/…` | `{path,size,lines,content}` — فایل باینری به‌صورت `FileResponse` |
| `GET /api/packages/{id}/download` | فایل zip |
| `DELETE /api/packages/{id}` | حذف پوشه و zip |

`path` در `/file` پس از resolve بررسی می‌شود که خارج از پوشه بسته نرود (۴۰۰ در صورت تلاش).
