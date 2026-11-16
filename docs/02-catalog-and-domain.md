# کاتالوگ و مدل دامنه

دو منبع حقیقت مستقل ولی متصل:

- **کاتالوگ** (`builder/backend/app/catalog/`) پاسخ می‌دهد «کارخانه چه قابلیت‌هایی می‌خواهد» —
  ۲۲ بخش، ۱۳۰ ماژول، ۵۱۵ زیرماژول، ۲٬۱۵۷ زیرمجموعه، ۲۶۶ نقطه هوش مصنوعی.
- **مدل دامنه** (`builder/backend/app/domain/`) پاسخ می‌دهد «آن قابلیت‌ها چه داده‌هایی لازم دارند» —
  ۴۴۲ جدول و ۷٬۰۰۸ فیلد برای همان ۱۳۰ ماژول.

---

## ۱) DSL کاتالوگ

### چهار سطح

| سطح | تابع | کد | نمونه |
| --- | --- | --- | --- |
| ۱ بخش | `section()` | یک حرف | `A` — هسته تولید |
| ۲ ماژول | `module()` | حرف + شماره | `A1` — برنامه‌ریزی تولید |
| ۳ زیرماژول | `group()` | `A1.1` | برنامه‌ریزی اصلی تولید (MPS) |
| ۴ زیرمجموعه | رشته در `items` | `A1.1.4` | هماهنگی با سفارشات فروش |

کد سطح چهارم خودکار ساخته می‌شود: `{کد زیرماژول}.{شماره از ۱}`.

### نحو رشته زیرمجموعه

```python
group("A1.1", "برنامه‌ریزی اصلی تولید (MPS)", [
    "تعریف افق برنامه‌ریزی (کوتاه‌مدت / میان‌مدت / بلندمدت)",      # ساده
    "هماهنگی با سفارشات فروش @@dep=E1.2",                          # وابسته به یک زیرمجموعه
    "یکپارچگی MRP با مالی @@dep=F6",                               # وابسته به یک ماژول
    "مدیریت موجودی ایمنی @@dep=D4.5 @@ent=SafetyStock @@role=master",
    "🤖 پیشنهاد خودکار MPS بهینه بر اساس تقاضا و ظرفیت",           # نقطه هوش مصنوعی
], "Master Production Schedule")
```

| برچسب | معنا |
| --- | --- |
| `🤖` (یا `🤖 AI:`) | این زیرمجموعه یک نقطه هوش مصنوعی است (`ai=true`) |
| `@@dep=A,B` | پیش‌نیاز: کد زیرمجموعه، زیرماژول یا ماژول — در حل انتخاب، خودکار افزوده می‌شود |
| `@@ent=EntityName` | این قابلیت به موجودیت دامنه با این نام گره می‌خورد |
| `@@role=master\|detail\|config` | نقش داده‌ای برای طبقه‌بندی در UI و مستندات |

خروجی `_build_item()` یک `ITEM` با کلیدهای `code,name,ai,deps,entity,role,level` است.

### توابع سازنده

```python
section(code, name, name_en, modules, *, icon="layers", color="#6366f1", description="")
module(code, name, name_en, groups, *, icon="cube", summary="", color="#6366f1")
group(code, name, items, name_en=None)
```

شمارش‌ها (`module_count`, `group_count`, `item_count`, `ai_count`) همیشه **محاسبه** می‌شوند، نه
دستی — پس هیچ‌گاه عدد غلط در UI یا مستندات نمی‌آید.

### registry و نمایه

`catalog/registry.py` همه ۲۲ فایل بخش را جمع می‌کند و یک `CatalogIndex` (dataclass) می‌سازد با
نمایه‌های `sections/modules/groups/items` به‌همراه نگاشت‌های والد/فرزند. توابع عمومی:

| تابع | خروجی |
| --- | --- |
| `catalog()` | فهرست کامل ۲۲ بخش |
| `index()` | نمایه تک‌نمونه (singleton) برای حل وابستگی و جست‌وجو |
| `stats()` | شمارش‌های کل و تفکیک هر بخش |
| `ai_points()` | ۲۶۶ نقطه AI با `code,name,module_code,module_name,section_code` |
| `search(query, limit)` | جست‌وجوی فارسی/انگلیسی روی نام و کد در هر چهار سطح |
| `to_json()` | خروجی JSON (برای `data/catalog.json`) |

### ۲۲ بخش کاتالوگ

| کد | بخش | ماژول | قابلیت | AI |
| --- | --- | ---: | ---: | ---: |
| A | هسته تولید | ۸ | ۲۶۱ | ۲۹ |
| B | کیفیت | ۷ | ۱۸۳ | ۱۵ |
| C | نگهداری و تعمیرات | ۶ | ۱۵۳ | ۱۹ |
| D | زنجیره تأمین | ۸ | ۲۱۵ | ۱۹ |
| E | فروش و بازاریابی | ۷ | ۱۴۵ | ۲۱ |
| F | مالی و حسابداری | ۱۲ | ۲۳۹ | ۱۵ |
| G | منابع انسانی | ۱۲ | ۱۹۴ | ۱۲ |
| H | مهندسی و R&D | ۵ | ۶۵ | ۴ |
| I | مدیریت پروژه | ۵ | ۵۰ | ۴ |
| J | IoT و اتوماسیون صنعتی | ۶ | ۵۶ | ۶ |
| K | هسته هوش مصنوعی | ۷ | ۸۱ | ۷۴ |
| L | هوش تجاری و گزارشگری | ۴ | ۵۲ | ۵ |
| M | بهداشت، ایمنی و محیط‌زیست | ۵ | ۶۷ | ۵ |
| N | انرژی و تأسیسات | ۳ | ۳۲ | ۶ |
| O | حاکمیت، ریسک و انطباق | ۴ | ۴۵ | ۳ |
| P | مدیریت اسناد و فرآیندها | ۴ | ۵۲ | ۶ |
| Q | ناوگان و لجستیک داخلی | ۳ | ۳۰ | ۳ |
| R | مدیریت استراتژیک | ۴ | ۳۵ | ۴ |
| S | زیرساخت فنی و یکپارچگی | ۷ | ۷۴ | ۳ |
| T | ماژول‌های تخصصی صنایع | ۷ | ۶۹ | ۷ |
| U | پیمانکاران و برون‌سپاری | ۳ | ۳۳ | ۳ |
| V | پایش و تحلیل عملکرد | ۳ | ۲۶ | ۳ |

---

## ۲) DSL مدل دامنه

### تعریف فیلد

هر فیلد یک رشته با جداکننده `|` است:

```
نام | نوع | برچسب فارسی | پرچم‌ها
```

```python
entity("ProductionOrder", "سفارش تولید", [
    "code|string|کد سفارش|unique,searchable",
    "product_id|foreign(products)|محصول|index",
    "planned_qty|decimal|مقدار برنامه‌ریزی‌شده|default=0",
    "status|enum(draft,released,in_progress,done,closed)|وضعیت|index,default=draft",
    "notes|text|یادداشت|nullable",
])
```

**انواع ساده** (`SIMPLE_TYPES`): `string`, `text`, `integer`, `bigint`, `decimal`, `boolean`,
`date`, `datetime`, `time`, `json`, `uuid` — به‌علاوه `enum(...)` و `foreign(table)`.
`decimal` با دقت پیش‌فرض `(18, 4)` ساخته می‌شود و `foreign()` به‌طور خودکار `index=true` و
`nullable=false` می‌گیرد (مگر آنکه صریحاً `nullable` داده شود).

**پرچم‌ها**: `nullable`, `unique`, `index` (یا `indexed`), `searchable`, `hidden`, `required`,
`default=<value>`.

کلیدهای فیلد پس از تجزیه: `name,label,type,nullable,unique,index,searchable,hidden,required` و در
صورت نیاز `default,options,references_table`.

### تعریف موجودیت و ماژول

```python
entity(name, label_fa, fields, *, table=None, label_en=None, soft_deletes=True,
       timestamps=True, has_code=True, icon="file-text", notes="", owner="tenant")

module_spec(code, name_en, label_fa, entities, *, menu_group="", description="",
            ai_endpoints=None, priority=3)
```

- `table` به‌طور پیش‌فرض `pluralize(snake_case(name))` است؛ برای جمع‌های بی‌قاعده
  `IRREGULAR_PLURALS` وجود دارد (`analysis→analyses`, `status→statuses`, `index→indices`, …) و در
  موارد خاص `table=` صریح داده می‌شود.
- `has_code` فقط وقتی `true` می‌ماند که واقعاً فیلد `code` تعریف شده باشد.
- فیلد تکراری در یک موجودیت ⇒ `ValueError` در زمان import.

### registry دامنه

| عنصر | نقش |
| --- | --- |
| `SYSTEM_MODULES` | ۹ ماژول زیرساختی که همیشه افزوده می‌شوند: `S1, G1, D4, D3, F1, P1, V3, K7, P2` |
| `SUPPORT_MODULES` | نگاشت «ماژول → پیش‌نیازهای پشتیبان» (مثلاً `A1 → A3, A4, D4`) |
| `PLATFORM_ENTITY` | موجودیت پلتفرمی `SystemFeature` (جدول `system_features`) با `module_code` خالی که به ماژول مجازی `S0` نگاشت می‌شود |
| `all_specs()` | همه مشخصات: ۶۲ ماژول دستی (`base_specs.py`, `core_specs_*.py`) + ۶۸ ماژول مشتق (`derived.py`) |
| `entity_table_map()` | نگاشت نام موجودیت → جدول؛ نام جدول تکراری ⇒ خطای سخت |
| `validate_foreign_keys()` | فهرست کلیدهای خارجی بدون مقصد |
| `resolve_modules(selected)` | افزودن `SYSTEM_MODULES` + `SUPPORT_MODULES` به انتخاب |
| `topological_order(entities)` | ترتیب ساخت جداول بر پایه وابستگی کلید خارجی |
| `specs_for_modules(codes)` | `{"modules","entities","tables","counts"}` آماده تولید |
| `coverage_report()` | آمار پوشش (دستی/مشتق/جدول/فیلد) که در `/api/meta` می‌آید |

### ماژول‌های مشتق

۶۸ ماژول که مشخصات دستی ندارند، در `derived.py` از کاتالوگ **استخراج** می‌شوند: از زیرماژول‌ها و
زیرمجموعه‌های دارای `@@ent=` موجودیت ساخته می‌شود و فیلدهای پایه (کد، نام، وضعیت، تاریخ،
مقادیر عددی، کلیدهای خارجی به ماژول‌های همسایه) به‌طور قاعده‌مند افزوده می‌گردند. این یعنی افزودن
یک ماژول جدید به کاتالوگ، بدون نوشتن مشخصات دامنه، همچنان خروجی قابل ساخت تولید می‌کند.

### پوشش فعلی

```
ماژول با مدل داده : ۱۳۰ از ۱۳۰ (۶۲ دستی + ۶۸ مشتق)
جدول              : ۴۴۲
فیلد              : ۷٬۰۰۸
اولین جداول       : accounts, companies, positions, shifts, users, work_calendars
```

---

## ۳) قواعد ویرایش

1. پس از هر تغییر در کاتالوگ: `.venv/bin/python scripts/validate_catalog.py`
   (یکتایی کدها، `@@dep=` با مقصد موجود، نبود نویسه‌های CJK/سیریلیک/کنترلی در متن فارسی،
   بازنویسی `data/catalog.json`).
2. پس از هر تغییر در دامنه: `.venv/bin/python scripts/validate_domain.py`
   (یکتایی جدول‌ها، کلید خارجی با مقصد، ترتیب توپولوژیک).
3. از مخفف‌های camel-case برای نام موجودیت پرهیز کنید (`SPCReport` ⇒ جدول `spc_reports` مبهم است)؛
   نام‌های کامل و جمع‌پذیر انتخاب کنید یا `table=` صریح بدهید.
4. نقطه AI جدید فقط با پیشوند `🤖` ساخته می‌شود؛ موتور و اندپوینت آن از
   `ai/registry.py:engine_for(code, name)` استنتاج می‌شود، پس نام قابلیت را با کلیدواژه‌های موتور
   هم‌خوان نگه دارید.
5. شمارش‌ها را هیچ‌جا دستی ننویسید — همه از `stats()` و `coverage_report()` می‌آیند.
