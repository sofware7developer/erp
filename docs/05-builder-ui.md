# رابط کاربری سازنده

`builder/frontend/` — React 18.3 + Vite 6 + react-router-dom 6.28، راست‌به‌چپ، تم تاریک/صنعتی،
**بدون هیچ کتابخانه UI یا تاریخ‌شمسی بیرونی**. همه ۵٬۸۶۳ خط (شامل CSS) در ۲۵ فایل.

| فایل | خط | نقش |
| --- | ---: | --- |
| `src/styles/global.css` | ۱٬۳۱۰ | سامانه طراحی کامل: متغیرها، چیدمان، کارت‌ها، درخت، جدول، فرم، کد، PWA |
| `src/lib/store.jsx` | ۴۵۵ | Context سراسری: بارگذاری داده، انتخاب، تنظیمات، تولید، پروژه‌ها، پیام‌ها |
| `src/pages/PackageDetail.jsx` | ۴۰۵ | درخت فایل، نمایشگر کد رنگ‌آمیزی‌شده، جدول ماژول‌ها، مانیفست، ناحیه‌ها |
| `src/components/CatalogTree.jsx` | ۳۹۷ | درخت چهارسطحی با چک‌باکس سه‌حالته، جست‌وجو، فیلتر AI/انتخاب‌شده |
| `src/lib/selection.js` | ۳۹۳ | منطق انتخاب چهارسطحی (derive/toggle/materialize/collapse) |
| `src/components/SettingsForm.jsx` | ۳۹۳ | فرم ۹۴ کلید تنظیمات در ۸ گروه + اطلاعات پروژه |
| `src/pages/Configure.jsx` | ۲۸۵ | پنج تب: کاتالوگ، تنظیمات، دستیار/چت، پروژه‌ها، تولید |
| `src/components/AdvisorPanel.jsx` | ۲۸۱ | دستیار هوشمند: فرم کارخانه، اهداف، پیشنهاد ماژول، فازبندی |
| `src/pages/Engines.jsx` | ۲۱۶ | کارت ۱۱ موتور AI + جدول نقاط AI با فیلتر |
| `src/pages/Home.jsx` | ۲۰۸ | آمار کاتالوگ، بخش‌ها، پریست‌ها، موتورها، پوشش دامنه |
| `src/lib/format.js` | ۲۰۵ | رقم فارسی، تاریخ جلالی، بایت، highlight کد |
| `src/components/SelectionCart.jsx` | ۱۸۳ | سبد انتخاب: آمار، برآورد، پوشش، پیش‌نیازها، موتورها |
| `src/pages/Packages.jsx` | ۱۲۷ | فهرست بسته‌های تولیدشده |
| `src/components/GenerateBar.jsx` | ۱۲۶ | بررسی نهایی، تولید بسته، نمایش نتیجه و دانلود |
| `src/lib/api.js` | ۱۲۱ | کلاینت ۳۰ اندپوینت با `ApiError` |
| `src/components/ChatPanel.jsx` | ۱۱۷ | گفت‌وگو با دستیار (AvalAI یا قاعده‌محور) |
| بقیه | ~۳۴۰ | `App.jsx`, `main.jsx`, `TopBar`, `PresetGrid`, `Toasts`, `StatCard` |
| `smoke/render-smoke.jsx` | ۳۵۸ | آزمون دود رندر با داده واقعی API |

---

## اجرا و ساخت

```bash
cd builder/frontend
npm install
npm run dev       # ۵۱۷۳ با پروکسی /api → http://localhost:8000 (VITE_PROXY_TARGET)
npm run build     # dist/ — خود FastAPI آن را روی / سرو می‌کند (حالت تک‌پورتی)
npm run preview   # ۴۱۷۳ برای پیش‌نمایش باندل
npm run smoke     # آزمون دود رندر (نیاز به سرویس در حال اجرا)
```

`vite.config.js`:
- `server.host = 0.0.0.0` و `allowedHosts: true` تا پشت پروکسی/preview هم کار کند
- پروکسی `/api` در هر دو حالت dev و preview
- `manualChunks: {react: [...]}` فقط در بیلد مرورگر (در بیلد SSR آزمون دود غیرفعال می‌شود، چون
  وابستگی‌ها external‌اند و رول‌آپ خطا می‌دهد)

---

## فروشگاه وضعیت (`src/lib/store.jsx`)

یک Context با کلید `erp-builder.state.v1` در `localStorage`:

**بارگذاری:** `health` + `meta` موازی، سپس `catalog?depth=4`، سپس `presets` و `packages`.
`default_settings` از `/meta` با تنظیمات ذخیره‌شده کاربر ادغام می‌شود (تنظیمات کاربر اولویت دارد).

**حل وابستگی‌ها:** هر تغییر انتخاب، پس از ۳۸۰ ms debounce یک `POST /resolve` می‌زند؛ تا رسیدن
پاسخ، شمارش‌های سمت کاربر (`derive`) نمایش داده می‌شوند تا UI هرگز منتظر نماند.

**عملیات‌های در دسترس کامپوننت‌ها:**

```
toggleCode(code) · toggleAi(code) · clearSelection() · selectEverything()
applyPreset(key) · applyAdvisor(modules, aiPoints, note) · loadProject(project)
patchSettings(patch) · patchProject(patch)
generate({saveProject}) · refreshPackages() · refreshProjects()
removePackage(id) · removeProject(id) · askAssistant(message, history)
notify(message, kind, timeout) · dismissToast(id)
```

**وضعیت:** `healthInfo, meta, catalog, hierarchy, derived, loading, error, selection, resolution,
resolving, hasSelection, settings, project, presets, packages, projects, projectsLoading,
generating, lastPackage, toasts`.

`useSelectionSummary()` آمار آماده نمایش می‌دهد: شمارش‌های محلی + `tables/fields/estimated_files`
از سرور + `auto_added/reasons/coverage`.

---

## الگوریتم انتخاب چهارسطحی (`src/lib/selection.js`)

payload ارسالی به سرور باید کوچک بماند ولی دقیق باشد؛ بنابراین انتخاب **صریح** در چهار سطح
نگه داشته می‌شود و دو عملیات متقارن دارد:

```
derive(hierarchy, selection)      → مجموعه «فعال» در هر چهار سطح + نقاط AI
toggle(hierarchy, selection, code) → انتخاب/لغو انتخاب یک گره در هر سطح
```

قواعد:

1. **انتخاب یک گره** ⇒ همه زیرمجموعه‌هایش فعال می‌شوند ولی صریح نگه داشته نمی‌شوند
   (`dropChildren`). اگر خودش یک نقطه AI باشد، فعال می‌شود.
2. **لغو انتخاب گره‌ای که از والدش فعال شده** ⇒ والد «ماده‌سازی» می‌شود
   (`materializeAncestors`): والد از فهرست صریح حذف و همه فرزندان دیگرش صریح افزوده می‌شوند، پس
   بقیه انتخاب‌ها حفظ می‌شوند.
3. **انتخاب همه فرزندان یک والد** ⇒ فشرده‌سازی (`collapse`): فرزندان حذف و خود والد انتخاب
   می‌شود؛ این کار تا بالاترین سطح ممکن ادامه می‌یابد.
4. `mode` می‌تواند `custom`, `all` یا `none` باشد؛ `all`/`none` بدون فهرست کد کار می‌کنند و با
   نخستین کلیک کاربر به `custom` برمی‌گردند.
5. نقاط AI فقط وقتی فعال‌اند که زیرمجموعه‌شان فعال باشد، و `toggleAiPoint` می‌تواند یک نقطه AI را
   بدون حذف خود زیرمجموعه خاموش کند.

`selectionFromModules(hierarchy, modules, aiPoints, extra)` برای پریست، دستیار و **بازیابی یک
پروژه ذخیره‌شده** استفاده می‌شود (با `extra.sections/groups/items`).

این منطق دقیقاً هم‌راستا با `expand_selection` در بک‌اند است، و `smoke/render-smoke.jsx` این
هم‌ارزی را با داده واقعی assert می‌کند (`contract:derived.modules` در برابر
`resolution.counts.modules`).

---

## ابزارهای نمایش (`src/lib/format.js`)

بدون وابستگی بیرونی:

- `toPersianDigits` / `toLatinDigits` — تبدیل دوطرفه رقم (ورودی عددی کاربر با رقم فارسی هم پذیرفته
  می‌شود)
- `formatNumber`, `compactNumber`, `formatPercent`, `formatBytes`
- `toJalali(gy,gm,gd)` + `JALALI_MONTHS` + `formatJalali(iso, withTime)` + `timeAgo(iso)`
- `humanKey('db_driver')` → `Db Driver`
- `coverageColor(percent)`, `iconFor(name, fallback)` — نگاشت آیکون‌های emoji
- `highlight(code, language)` — رنگ‌آمیزی PHP/JS/JSON/Python با regex (رشته، کامنت، کلیدواژه،
  عدد) بدون کتابخانه؛ `languageOf(path)` زبان را از پسوند حدس می‌زند

---

## صفحه‌ها

### خانه
آمار شش‌گانه کاتالوگ، ۲۲ بخش به‌صورت چیپ رنگی (لینک به `/configure?section=X`)، جدول ۱۱ موتور AI،
گرید پریست‌ها، شش کارت «بسته خروجی چه دارد؟» و آمار پوشش مدل داده از `meta.domain_coverage`.

### پیکربندگر (۵ تب، در URL با `?tab=`)
- **کاتالوگ و انتخاب** — `CatalogTree` + `SelectionCart` کنار هم
- **تنظیمات کارخانه** — `SettingsForm`: هویت، تقویم/مالی، زیرساخت، AI، IoT، ایمیل/پیامک،
  مدیر/پشتیبان، محتوای بسته؛ به‌همراه نام/توضیح پروژه
- **دستیار و گفت‌وگو** — `AdvisorPanel` (فرم کارخانه + ۳۷ هدف + پیشنهاد + فازبندی + اعمال در
  انتخاب) و `ChatPanel`
- **پروژه‌های ذخیره‌شده** — فهرست، جزئیات، فازبندی، کپی، حذف و «باز کردن در پیکربندی فعلی»
- **تولید بسته** — `GenerateBar` با برآورد نهایی و لینک دانلود/مرور

`CatalogTree`: جست‌وجوی debounced (نمای نتایج جداگانه)، فیلتر «فقط AI» و «فقط انتخاب‌شده»،
چک‌باکس سه‌حالته (`all`/`partial`/`none`)، سوئیچ AI برای هر زیرمجموعه، نشان «پیش‌نیاز خودکار»
برای ماژول‌های `auto_added` و شمارش‌های زنده روی هر گره.

### موتورهای AI
کارت هر موتور (الگوریتم‌ها، اندپوینت، LLM/بلادرنگ، تعداد نقاط در کاتالوگ)، پنل جزئیات فنی با
فیلتر موتور و جدول ۲۶۶ نقطه AI شامل `model_id` و `feature_flag` و نشان «در انتخاب».

### بسته‌ها و جزئیات بسته
فهرست با آمار و دانلود؛ صفحه جزئیات با چهار تب (فایل‌ها با درخت و جست‌وجوی مسیر، ماژول‌ها،
مانیفست JSON، ناحیه‌های خروجی) و نمایشگر کد با شماره خط و رنگ‌آمیزی.

---

## آزمون دود رندر (`npm run smoke`)

`smoke/render-smoke.jsx` با `vite build --ssr` ساخته و با Node اجرا می‌شود:

1. داده واقعی را از API می‌گیرد (`health`, `meta`, `catalog?depth=4`, `presets`, `packages`,
   `projects`, `presets/{key}/apply`, `resolve`, جزئیات/درخت/یک فایل بسته)
2. از همان داده‌ها یک مقدار فروشگاه می‌سازد (با `buildHierarchy` و `selectionFromModules` واقعی)
3. هر کامپوننت و هر صفحه (و هر پنج تب پیکربندگر) را با `renderToStaticMarkup` رندر می‌کند
4. assert می‌کند: خروجی کوتاه نباشد، متن‌های انتظار‌رفته فارسی دیده شوند، و
   `>undefined<`, `[object Object]`, `NaN`, `>null<` نشت نکنند
5. قرارداد داده‌ها را بررسی می‌کند: ۲۲ بخش، ۱۳۰ ماژول، ۵۱۵ زیرماژول، ۲٬۱۵۷ زیرمجموعه،
   ۲۶۶ نقطه AI، ۱۱ پریست و هم‌ارزی شمارش سمت کاربر با `resolution.counts`

۳۳ بررسی، و در آخرین اجرا ۰ شکست. هشدارهای `useLayoutEffect` سمت سرور (از react-router) در
`smoke/globals-shim.js` فیلتر می‌شوند تا هشدارهای واقعی دیده شوند.

`scripts/verify_ui.py` همین آزمون را همراه با ساخت باندل و بررسی شکل پاسخ API به‌صورت یک‌جا
اجرا می‌کند (سرویس را خودش روی یک پورت آزاد بالا می‌آورد و پس از پایان می‌بندد).
