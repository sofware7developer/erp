# -*- coding: utf-8 -*-
"""
تولید مسیرهای API و داده اولیه (Seeder)
========================================
* `routes/api.php` — مسیرهای سامانه (احراز هویت، داشبورد، قابلیت‌ها، AI، گزارش، ممیزی)
* `routes/modules/<slug>.php` — یک فایل مسیر به ازای هر ماژول با REST کامل
* `routes/web.php` و `routes/console.php`
* `database/seeders/DatabaseSeeder.php`، `SystemSeeder.php`، `DemoDataSeeder.php`
"""

from __future__ import annotations

from typing import Any

from .laravel_domain import module_namespace, section_namespace
from .domain_naming import platform_module, singular_route_param
from .writers import Package, render

ROUTES_API_TEMPLATE = r"""<?php

use App\Http\Controllers\Api\AiController;
use App\Http\Controllers\Api\AuditController;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\DashboardController;
use App\Http\Controllers\Api\FeatureController;
use App\Http\Controllers\Api\ReportController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| مسیرهای API — @@app_name_fa@@
|--------------------------------------------------------------------------
|
| این فایل توسط «سازنده ERP هوشمند» تولید شده است.
| بخش سامانه (احراز هویت، داشبورد، قابلیت‌ها، هوش مصنوعی، گزارش و ممیزی)
| در این فایل و مسیرهای هر ماژول در پوشه routes/modules قرار دارد.
|
| ماژول‌های فعال: @@modules_count@@ | زیرمجموعه‌ها: @@items_count@@ |
| نقاط هوش مصنوعی: @@ai_count@@
|
*/

Route::prefix('v1')->group(function () {

    /* مسیرهای عمومی (بدون احراز هویت) */
    Route::post('auth/login', [AuthController::class, 'login'])->name('auth.login');
    Route::get('health', fn () => response()->json([
        'status' => 'ok',
        'app' => config('app.name_fa'),
        'version' => config('app.version'),
        'build' => config('erp.build.package_id'),
        'calendar' => config('erp.localization.calendar'),
        'timezone' => config('app.timezone'),
        'server_time' => now()->toIso8601String(),
        'server_time_jalali' => \App\Support\Jalali::format(now(), true),
    ]))->name('health');

    /* مسیرهای محافظت‌شده با Sanctum */
    Route::middleware('auth:sanctum')->group(function () {

        // --- احراز هویت و پروفایل ---
        Route::post('auth/logout', [AuthController::class, 'logout'])->name('auth.logout');
        Route::get('auth/me', [AuthController::class, 'me'])->name('auth.me');
        Route::put('auth/profile', [AuthController::class, 'updateProfile'])->name('auth.profile');
        Route::post('auth/password', [AuthController::class, 'changePassword'])->name('auth.password');

        // --- داشبورد فرماندهی ---
        Route::get('dashboard', [DashboardController::class, 'index'])->name('dashboard');

        // --- رجیستری قابلیت‌ها و منوها ---
        Route::get('modules', [FeatureController::class, 'modules'])->name('modules.index');
        Route::get('features', [FeatureController::class, 'features'])->name('features.index');
        Route::get('permissions', [FeatureController::class, 'permissions'])->name('permissions.index');

        // --- ممیزی ---
        Route::get('audit-events', [AuditController::class, 'index'])
            ->middleware('permission:system.audit.view')
            ->name('audit.index');

        // --- گزارش‌ساز عمومی ---
        Route::get('reports/tables', [ReportController::class, 'tables'])->name('reports.tables');
        Route::get('reports/templates', [ReportController::class, 'templates'])->name('reports.templates');
        Route::post('reports/aggregate', [ReportController::class, 'aggregate'])->name('reports.aggregate');
        Route::post('reports/export', [ReportController::class, 'export'])->name('reports.export');

        // --- هوش مصنوعی ---
        Route::prefix('ai')->name('ai.')->group(function () {
            Route::get('engines', [AiController::class, 'engines'])->name('engines');
            Route::get('capabilities', [FeatureController::class, 'aiCapabilities'])->name('capabilities');
            Route::post('capabilities/{code}', [AiController::class, 'run'])
                ->where('code', '[A-Z][0-9]+(?:\.[0-9]+)*')
                ->name('run');
            Route::post('models/{modelId}/train', [AiController::class, 'train'])->name('train');
            Route::post('chat', [AiController::class, 'chat'])->name('chat');
            Route::post('summarize', [AiController::class, 'summarize'])->name('summarize');
            Route::post('extract', [AiController::class, 'extract'])->name('extract');
            Route::post('classify', [AiController::class, 'classify'])->name('classify');
            Route::post('insight', [AiController::class, 'insight'])->name('insight');
        });
    });
});

/*
|--------------------------------------------------------------------------
| مسیرهای ماژول‌های کسب‌وکاری
|--------------------------------------------------------------------------
| هر ماژول یک فایل مسیر مستقل دارد که در زمان اجرا بارگذاری می‌شود.
*/
foreach (glob(__DIR__ . '/modules/*.php') as $moduleRouteFile) {
    require $moduleRouteFile;
}
"""

ROUTES_MODULE_TEMPLATE = r"""<?php

@@imports@@

/*
|--------------------------------------------------------------------------
| ماژول @@module_code@@ — @@module_name@@
|--------------------------------------------------------------------------
| @@module_description@@
|
| زیرماژول‌ها: @@groups_count@@ | زیرمجموعه‌ها: @@items_count@@ |
| جداول: @@tables_count@@ | نقاط AI: @@ai_count@@
| مسیر پایه: /api/@@route_prefix@@
*/

Route::prefix('@@route_prefix@@')
    ->middleware(['auth:sanctum'])
    ->name('@@route_name@@.')
    ->group(function () {

        // داشبورد ماژول
        Route::get('dashboard', fn () => response()->json(
            app(\App\Services\@@namespace@@\@@service_class@@::class)->dashboard()
        ))->name('dashboard');

@@resource_routes@@
    });
"""

ROUTES_WEB = r"""<?php

use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| مسیرهای وب
|--------------------------------------------------------------------------
| رابط کاربری یک SPA از نوع React است که از پوشه frontend/dist سرو می‌شود.
| همه مسیرهای غیر API به index.html سپرده می‌شوند (مسیریابی سمت کلاینت).
*/

Route::get('/', fn () => response()->file(public_path('index.html')))
    ->name('home');

Route::get('/login', fn () => response()->file(public_path('index.html')))
    ->name('login');

Route::fallback(fn () => file_exists(public_path('index.html'))
    ? response()->file(public_path('index.html'))
    : response()->json([
        'message' => 'رابط کاربری ساخته نشده است. دستور npm run build را در پوشه frontend اجرا کنید.',
        'api_docs' => '/api/v1/health',
    ], 404));
"""

ROUTES_CONSOLE_TEMPLATE = r"""<?php

use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule;

/*
|--------------------------------------------------------------------------
| مسیرهای کنسول و زمان‌بندی
|--------------------------------------------------------------------------
*/

Artisan::command('inspire', function () {
    /** @var \Illuminate\Console\Command $this */
    $this->comment(Inspiring::quote());
})->purpose('نمایش یک جمله الهام‌بخش');

/*
 * زمان‌بندی وظایف سامانه
 *
 * پشتیبان‌گیری: @@backup_cron@@
 */
Schedule::command('erp:backup')->cron('@@backup_cron@@')->withoutOverlapping();
Schedule::command('queue:prune-batches --hours=72')->hourly();
Schedule::command('queue:prune-failed --hours=168')->daily();
Schedule::command('sanctum:prune-expired --hours=24')->daily();
Schedule::command('erp:ai:health')->hourly()->withoutOverlapping();
Schedule::command('model:prune')->daily();
"""

DATABASE_SEEDER_TEMPLATE = r"""<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Artisan;

/**
 * داده اولیه سامانه @@app_name@@
 *
 * ترتیب اجرا مهم است: ابتدا داده پایه سامانه (کاربر، نقش، مجوز)،
 * سپس ماژول‌ها بر اساس ترتیب توپولوژیک وابستگی‌ها، و در پایان
 * همگام‌سازی رجیستری قابلیت‌ها.
 */
class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
            SystemSeeder::class,
@@module_seeders@@
        ]);

        Artisan::call('erp:features:sync');
        $this->command?->info('رجیستری قابلیت‌ها همگام‌سازی شد.');
    }
}
"""

SYSTEM_SEEDER = r"""<?php

namespace Database\Seeders;

use App\Models\System\Permission;
use App\Models\System\Role;
use App\Models\System\RolePermission;
use App\Models\System\User;
use App\Support\ModuleRegistry;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

/**
 * داده پایه سامانه: نقش‌ها، مجوزها و کاربر مدیر
 *
 * مجوزها به‌صورت پویا از رجیستری ماژول‌ها ساخته می‌شوند:
 *   <slug ماژول>.<جدول>.<عملیات>
 */
class SystemSeeder extends Seeder
{
    /** @var array<int, array{code: string, title: string, scope: string, permissions: string}> */
    protected array $roles = [
        [
            'code' => 'admin',
            'title' => 'مدیر سامانه',
            'scope' => 'system',
            'permissions' => '*',
        ],
        [
            'code' => 'manager',
            'title' => 'مدیر کارخانه',
            'scope' => 'company',
            'permissions' => 'view,create,edit,approve',
        ],
        [
            'code' => 'supervisor',
            'title' => 'سرپرست',
            'scope' => 'department',
            'permissions' => 'view,create,edit',
        ],
        [
            'code' => 'operator',
            'title' => 'اپراتور',
            'scope' => 'own',
            'permissions' => 'view,create',
        ],
        [
            'code' => 'accountant',
            'title' => 'حسابدار',
            'scope' => 'company',
            'permissions' => 'view,create,edit,approve',
        ],
        [
            'code' => 'planner',
            'title' => 'برنامه‌ریز تولید',
            'scope' => 'company',
            'permissions' => 'view,create,edit',
        ],
        [
            'code' => 'quality',
            'title' => 'کارشناس کیفیت',
            'scope' => 'company',
            'permissions' => 'view,create,edit,approve',
        ],
        [
            'code' => 'maintenance',
            'title' => 'کارشناس نت',
            'scope' => 'company',
            'permissions' => 'view,create,edit',
        ],
        [
            'code' => 'warehouse',
            'title' => 'انباردار',
            'scope' => 'department',
            'permissions' => 'view,create,edit',
        ],
        [
            'code' => 'viewer',
            'title' => 'مشاهده‌کننده',
            'scope' => 'own',
            'permissions' => 'view',
        ],
        [
            'code' => 'auditor',
            'title' => 'ممیز',
            'scope' => 'system',
            'permissions' => 'view',
        ],
    ];

    public function run(): void
    {
        $this->seedPermissions();
        $roles = $this->seedRoles();
        $this->seedAdmin($roles);
    }

    /** ساخت مجوزها برای هر جدول فعال */
    protected function seedPermissions(): void
    {
        $actions = ['view', 'create', 'edit', 'delete', 'approve'];
        $actionLabels = [
            'view' => 'مشاهده',
            'create' => 'ایجاد',
            'edit' => 'ویرایش',
            'delete' => 'حذف',
            'approve' => 'تأیید',
        ];

        $rows = [];
        $now = now();

        foreach (ModuleRegistry::all() as $module) {
            foreach ($module['tables'] as $table) {
                foreach ($actions as $action) {
                    $rows[] = [
                        'code' => "{$module['slug']}.{$table}.{$action}",
                        'title' => "{$actionLabels[$action]} {$table}",
                        'module_code' => $module['code'],
                        'item_code' => $module['code'],
                        'action' => $action,
                        'guard_name' => 'api',
                        'created_at' => $now,
                        'updated_at' => $now,
                    ];
                }
            }
        }

        // مجوزهای سطح سامانه
        foreach (['system.audit.view', 'system.features.view', 'system.reports.view', 'system.ai.use'] as $code) {
            $rows[] = [
                'code' => $code,
                'title' => $code,
                'module_code' => 'S1',
                'item_code' => 'S1.1',
                'action' => 'view',
                'guard_name' => 'api',
                'created_at' => $now,
                'updated_at' => $now,
            ];
        }

        foreach (array_chunk($rows, 500) as $chunk) {
            Permission::insertOrIgnore($chunk);
        }

        $this->command?->info('مجوزهای ساخته‌شده: ' . count($rows));
    }

    /** ساخت نقش‌ها و اتصال مجوزها */
    protected function seedRoles(): array
    {
        $roles = [];
        $now = now();

        foreach ($this->roles as $definition) {
            $role = Role::firstOrCreate(
                ['code' => $definition['code']],
                [
                    'title' => $definition['title'],
                    'description' => 'نقش پیش‌فرض سامانه',
                    'scope' => $definition['scope'],
                    'is_system' => true,
                    'is_active' => true,
                ]
            );

            $permissions = $definition['permissions'] === '*'
                ? Permission::query()->pluck('id')
                : Permission::query()
                    ->whereIn('action', explode(',', $definition['permissions']))
                    ->pluck('id');

            foreach ($permissions as $permissionId) {
                RolePermission::firstOrCreate([
                    'role_id' => $role->id,
                    'permission_id' => $permissionId,
                ], [
                    'data_scope' => $definition['scope'],
                    'created_at' => $now,
                    'updated_at' => $now,
                ]);
            }

            $roles[$definition['code']] = $role;
        }

        $this->command?->info('نقش‌های ساخته‌شده: ' . count($roles));

        return $roles;
    }

    /** ساخت کاربر مدیر کل */
    protected function seedAdmin(array $roles): void
    {
        $email = (string) env('ERP_ADMIN_EMAIL', 'admin@example.com');

        $admin = User::firstOrCreate(
            ['email' => $email],
            [
                'username' => 'admin',
                'full_name' => (string) env('ERP_ADMIN_NAME', 'مدیر سامانه'),
                'mobile' => '09120000000',
                'password' => Hash::make((string) env('ERP_ADMIN_PASSWORD', 'ChangeMe!1405')),
                'locale' => 'fa',
                'is_active' => true,
                'is_super_admin' => true,
                'mfa_enabled' => false,
                'password_changed_at' => now(),
            ]
        );

        if (isset($roles['admin'])) {
            DB::table('user_roles')->insertOrIgnore([
                'user_id' => $admin->id,
                'role_id' => $roles['admin']->id,
                'valid_from' => now()->toDateString(),
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }

        $this->command?->info("کاربر مدیر آماده است: {$email}");
    }
}
"""

DEMO_SEEDER_TEMPLATE = r"""<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

/**
 * داده نمونه برای محیط نمایش و آموزش
 *
 * فقط وقتی فعال می‌شود که در تنظیمات کارخانه include_demo_data=true باشد
 * یا دستور `php artisan db:seed --class=DemoDataSeeder` اجرا شود.
 */
class DemoDataSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
@@module_seeders@@
        ]);

        $this->command?->warn('داده نمونه درج شد — در محیط تولید استفاده نکنید.');
    }
}
"""


def build_module_routes(
    module: dict[str, Any],
    module_entities: list[dict[str, Any]],
    *,
    groups_count: int,
    items_count: int,
    ai_count: int,
    service_class: str,
) -> tuple[str, str]:
    """ساخت فایل مسیر یک ماژول."""
    namespace = module_namespace(module)
    imports = ["use Illuminate\\Support\\Facades\\Route;"]
    blocks: list[str] = []

    for entity in module_entities:
        controller_class = f"{entity['name']}Controller"
        imports.append(f"use App\\Http\\Controllers\\Api\\{namespace}\\{controller_class};")

        table = entity["table"]
        param = singular_route_param(table)
        permission_base = f"{module['slug']}.{table}"
        has_status = any(f["name"] == "status" for f in entity["fields"])

        lines = [
            f"        // {entity['label_fa']} ({table})",
            f"        Route::get('{table}', [{controller_class}::class, 'index'])",
            f"            ->middleware('permission:{permission_base}.view')",
            f"            ->name('{table}.index');",
            f"        Route::post('{table}', [{controller_class}::class, 'store'])",
            f"            ->middleware('permission:{permission_base}.create')",
            f"            ->name('{table}.store');",
            f"        Route::get('{table}/{{{param}}}', [{controller_class}::class, 'show'])",
            f"            ->middleware('permission:{permission_base}.view')",
            f"            ->name('{table}.show');",
            f"        Route::match(['put', 'patch'], '{table}/{{{param}}}', [{controller_class}::class, 'update'])",
            f"            ->middleware('permission:{permission_base}.edit')",
            f"            ->name('{table}.update');",
        ]
        if has_status:
            lines += [
                f"        Route::patch('{table}/{{{param}}}/status', [{controller_class}::class, 'changeStatus'])",
                f"            ->middleware('permission:{permission_base}.edit')",
                f"            ->name('{table}.status');",
            ]
        lines += [
            f"        Route::delete('{table}/{{{param}}}', [{controller_class}::class, 'destroy'])",
            f"            ->middleware('permission:{permission_base}.delete')",
            f"            ->name('{table}.destroy');",
        ]
        blocks.append("\n".join(lines))

    resource_routes = "\n\n".join(blocks) or "        // این ماژول موجودیت قابل مسیردهی ندارد"

    path = f"backend/routes/modules/{module['slug']}.php"
    content = render(
        ROUTES_MODULE_TEMPLATE,
        imports="\n".join(imports),
        module_code=module["code"],
        module_name=module["label_fa"],
        module_description=module.get("description", ""),
        groups_count=groups_count,
        items_count=items_count,
        tables_count=len(module_entities),
        ai_count=ai_count,
        route_prefix=f"v1/{module['slug']}",
        route_name=f"{section_namespace(module['code']).lower()}.{module['slug']}",
        namespace=namespace,
        service_class=service_class,
        resource_routes=resource_routes,
    )
    return path, content


def generate_routes(
    package: Package,
    *,
    settings: dict[str, Any],
    modules: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    module_stats: dict[str, dict[str, int]],
    context: dict[str, Any],
) -> None:
    """تولید همه فایل‌های مسیر."""
    # موجودیت‌های پلتفرمی module_code خالی دارند و به ماژول مجازی S0 نگاشت
    # می‌شوند؛ هر دو شکل («» و «S0») پذیرفته می‌شود تا یکدست بماند.
    entities_by_module: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        entities_by_module.setdefault(entity["module_code"] or "S0", []).append(entity)

    package.add_rendered(
        "backend/routes/api.php",
        ROUTES_API_TEMPLATE,
        area="laravel-routes",
        app_name_fa=context["app_name_fa"],
        modules_count=len(modules),
        items_count=context["counts"]["items"],
        ai_count=context["counts"]["ai_points"],
    )

    catalog_codes = {m["code"] for m in modules}
    for module in modules + ([platform_module()] if "S0" in entities_by_module else []):
        code = module["code"]
        module_entities = entities_by_module.get(code, [])
        if not module_entities:
            continue

        namespace = section_namespace(code)
        service_class = f"{namespace}{code}Service"
        stats = module_stats.get(code, {})
        path, content = build_module_routes(
            module,
            module_entities,
            groups_count=stats.get("groups", 0),
            items_count=stats.get("items", 0),
            ai_count=stats.get("ai", 0),
            service_class=service_class,
        )
        package.add(path, content, area="laravel-routes")

    package.add("backend/routes/web.php", ROUTES_WEB, area="laravel-routes")
    package.add_rendered(
        "backend/routes/console.php",
        ROUTES_CONSOLE_TEMPLATE,
        area="laravel-routes",
        backup_cron=settings.get("backup_cron", "0 2 * * *"),
    )


def generate_seeders(
    package: Package,
    *,
    modules: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    include_demo_data: bool,
    context: dict[str, Any],
) -> None:
    """تولید سیدرهای پایگاه داده."""
    module_codes = {e["module_code"] or "S0" for e in entities}
    seeder_classes: list[str] = []
    for module in modules:
        if module["code"] not in module_codes:
            continue
        namespace = section_namespace(module["code"])
        seeder_classes.append(f"{namespace}{module['code']}Seeder")
    if "S0" in module_codes:
        seeder_classes.append("SystemS0Seeder")

    seeder_lines = "\n".join(f"            {name}::class," for name in seeder_classes)

    package.add_rendered(
        "backend/database/seeders/DatabaseSeeder.php",
        DATABASE_SEEDER_TEMPLATE,
        area="laravel-seeders",
        app_name=context["app_name_fa"],
        module_seeders=seeder_lines or "            // ماژولی برای seed وجود ندارد",
    )
    package.add("backend/database/seeders/SystemSeeder.php", SYSTEM_SEEDER, area="laravel-seeders")

    if include_demo_data:
        package.add_rendered(
            "backend/database/seeders/DemoDataSeeder.php",
            DEMO_SEEDER_TEMPLATE,
            area="laravel-seeders",
            module_seeders=seeder_lines or "            // داده نمونه‌ای تعریف نشده است",
        )
