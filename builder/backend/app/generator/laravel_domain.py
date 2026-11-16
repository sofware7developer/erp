# -*- coding: utf-8 -*-
"""
تولید لایه دامنه لاراول
========================
برای هر موجودیت (Entity) این فایل‌ها تولید می‌شود:

  database/migrations/<n>_create_<table>_table.php
  app/Models/<Module>/<Model>.php
  app/Http/Controllers/Api/<Module>/<Model>Controller.php
  app/Http/Requests/<Module>/Store<Model>Request.php
  app/Http/Requests/<Module>/Update<Model>Request.php
  app/Http/Resources/<Module>/<Model>Resource.php
  app/Policies/<Module>/<Model>Policy.php
  database/factories/<Module>/<Model>Factory.php
  tests/Feature/<Module>/<Model>Test.php

و برای هر ماژول:
  app/Services/<Module>/<Module>Service.php
  database/seeders/<Module>Seeder.php
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from ..domain.dsl import pascal_case, singularize
from .domain_naming import route_param_for
from .writers import Package, php_value, render

# --------------------------------------------------------------------------- #
# نگاشت نوع داده به Blueprint لاراول
# --------------------------------------------------------------------------- #
LENGTH_HINTS = {
    "code": 64,
    "national_id": 10,
    "economic_code": 15,
    "postal_code": 10,
    "phone": 20,
    "mobile": 20,
    "email": 191,
    "iban": 34,
    "sayyad_id": 32,
    "title": 191,
    "name": 191,
    "slug": 128,
    "unit": 16,
    "currency": 8,
    "status": 32,
    "color": 16,
    "icon": 48,
    "lat": 24,
    "lng": 24,
    "latitude": 24,
    "longitude": 24,
}

NUMERIC_TYPES = {"integer", "bigint", "decimal"}
DATE_TYPES = {"date", "datetime", "time"}
SKIP_DEFAULTS = {"now", "today", "current_timestamp", "null", "none", ""}


def camel(text: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", text) if p]
    if not parts:
        return "item"
    return parts[0].lower() + "".join(p[:1].upper() + p[1:] for p in parts[1:])


def studly(text: str) -> str:
    return pascal_case(text)


#: فضای‌نام PHP هر بخش کاتالوگ (A تا V)
SECTION_NAMESPACE = {
    "A": "Manufacturing",
    "B": "Quality",
    "C": "Maintenance",
    "D": "SupplyChain",
    "E": "Sales",
    "F": "Finance",
    "G": "HumanResources",
    "H": "Engineering",
    "I": "Projects",
    "J": "Iot",
    "K": "Ai",
    "L": "Analytics",
    "M": "Hse",
    "N": "Energy",
    "O": "Governance",
    "P": "Documents",
    "Q": "Fleet",
    "R": "Strategy",
    "S": "System",
    "T": "Industry",
    "U": "Contractors",
    "V": "Performance",
}


def section_namespace(module_code: str) -> str:
    """فضای‌نام PHP بر اساس حرف بخش کاتالوگ."""
    return SECTION_NAMESPACE.get((module_code or "")[:1].upper(), "Core")


def module_namespace(module: dict[str, Any]) -> str:
    return section_namespace(module["code"])


def php_string(value: Any) -> str:
    return php_value(value)


def is_required(field: dict[str, Any]) -> bool:
    return bool(field.get("required")) or (not field.get("nullable") and field.get("type") != "foreign")


def column_definition(field: dict[str, Any]) -> str:
    """ساخت یک ستون Blueprint لاراول."""
    name = field["name"]
    ftype = field["type"]
    parts: list[str] = []

    if ftype == "foreign":
        target = field.get("references_table", "users")
        base = f"$table->foreignId('{name}')"
        if field.get("nullable"):
            base += "->nullable()"
        base += f"->constrained('{target}')"
        base += "->nullOnDelete()" if field.get("nullable") else "->cascadeOnDelete()"
        if field.get("index") is False:
            base += ""
        return base + ";"

    if ftype == "enum":
        options = ", ".join(f"'{opt}'" for opt in field.get("options", []))
        base = f"$table->enum('{name}', [{options}])"
    elif ftype == "string":
        length = LENGTH_HINTS.get(name, 191 if not name.endswith("_no") else 64)
        base = f"$table->string('{name}', {length})"
    elif ftype == "text":
        base = f"$table->text('{name}')"
    elif ftype == "integer":
        base = f"$table->integer('{name}')" + ("->unsigned()" if name.endswith("_count") else "")
    elif ftype == "bigint":
        base = f"$table->unsignedBigInteger('{name}')"
    elif ftype == "decimal":
        precision = (18, 4)
        if any(k in name for k in ("price", "rate", "amount", "cost", "value", "sum", "total", "balance")):
            precision = (18, 2)
        if "lat" in name or "lng" in name:
            precision = (12, 8)
        base = f"$table->decimal('{name}', {precision[0]}, {precision[1]})"
    elif ftype == "boolean":
        base = f"$table->boolean('{name}')"
    elif ftype == "date":
        base = f"$table->date('{name}')"
    elif ftype == "datetime":
        base = f"$table->dateTime('{name}')"
    elif ftype == "time":
        base = f"$table->time('{name}')"
    elif ftype == "json":
        base = f"$table->json('{name}')"
    elif ftype == "uuid":
        base = f"$table->uuid('{name}')"
    else:
        base = f"$table->string('{name}')"

    if field.get("nullable"):
        base += "->nullable()"
    default = field.get("default")
    if default is not None and str(default).lower() not in SKIP_DEFAULTS:
        if ftype == "boolean":
            base += f"->{'default(true)' if str(default).lower() in ('1', 'true', 'yes') else 'default(false)'}"
        elif ftype in NUMERIC_TYPES:
            try:
                numeric = float(default)
                base += f"->default({int(numeric) if numeric.is_integer() else numeric})"
            except (TypeError, ValueError):
                pass
        else:
            base += f"->default({php_value(str(default))})"
    if field.get("unique"):
        base += "->unique()"
    elif field.get("index"):
        base += "->index()"

    parts.append(base + ";")
    return "\n            ".join(parts)


def cast_for(field: dict[str, Any]) -> str | None:
    ftype = field["type"]
    mapping = {
        "integer": "'integer'",
        "bigint": "'integer'",
        "decimal": "'decimal:4'",
        "boolean": "'boolean'",
        "date": "'date:Y-m-d'",
        "datetime": "'datetime:Y-m-d H:i:s'",
        "json": "'array'",
        "enum": "'string'",
    }
    return mapping.get(ftype)


def validation_rules(
    field: dict[str, Any],
    *,
    table: str,
    route_param: str,
    for_update: bool,
    known_tables: set[str],
) -> list[str]:
    """ساخت فهرست عبارات PHP برای قواعد اعتبارسنجی یک فیلد."""
    name = field["name"]
    ftype = field["type"]
    rules: list[str] = []

    if for_update:
        rules.append("'sometimes'")
    if is_required(field) and not for_update:
        rules.append("'required'")
    elif field.get("nullable"):
        rules.append("'nullable'")

    if ftype == "foreign":
        target = field.get("references_table", "users")
        rules.append("'integer'")
        if target in known_tables:
            rules.append(f"'exists:{target},id'")
    elif ftype == "enum":
        options = ",".join(field.get("options", []))
        rules.append(f"'in:{options}'")
    elif ftype == "string":
        length = LENGTH_HINTS.get(name, 191)
        rules.append(f"'string:{length}'")
    elif ftype == "text":
        rules.append("'string'")
    elif ftype in ("integer", "bigint"):
        rules.append("'integer'")
        if name.endswith("_count") or name.endswith("_no"):
            rules.append("'min:0'")
    elif ftype == "decimal":
        rules.append("'numeric'")
        if "rate" in name or "percent" in name:
            rules.append("'between:0,100'")
    elif ftype == "boolean":
        rules.append("'boolean'")
    elif ftype == "date":
        rules.append("'date_format:Y-m-d'")
    elif ftype == "datetime":
        rules.append("'date'")
    elif ftype == "time":
        rules.append("'date_format:H:i:s'")
    elif ftype == "json":
        rules.append("'array'")
    elif ftype == "uuid":
        rules.append("'uuid'")

    if field.get("unique"):
        unique = f"Rule::unique('{table}', '{name}')"
        if for_update:
            unique += f"->ignore($this->route('{route_param}')?->id)"
        rules.append(unique)

    return rules


# --------------------------------------------------------------------------- #
# قالب‌های PHP
# --------------------------------------------------------------------------- #
MIGRATION_TEMPLATE = """<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

/**
 * @@comment@@
 *
 * ماژول: @@module_code@@ — @@module_name@@
 * موجودیت: @@entity_name@@ (@@entity_label@@)
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('@@table@@', function (Blueprint $table) {
            $table->id();
@@columns@@
@@tenant_column@@
            $table->timestamps();
@@soft_deletes@@
        });
@@extra_indexes@@
    }

    public function down(): void
    {
        Schema::dropIfExists('@@table@@');
    }
};
"""

MODEL_TEMPLATE = """<?php

namespace App\\Models\\@@namespace@@;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;
@@uses@@

/**
 * @@entity_label@@
 *
 * ماژول: @@module_code@@ — @@module_name@@
 * جدول: @@table@@
@@notes_doc@@
 */
class @@model@@ extends Model
{
@@traits@@

    protected $table = '@@table@@';

    /** فیلدهای قابل انتساب دسته‌جمعی */
    protected $fillable = [
@@fillable@@
    ];

    /** تبدیل نوع داده‌ها */
    protected $casts = [
@@casts@@
    ];

    /** مقادیر پیش‌فرض */
    protected $attributes = [
@@defaults@@
    ];

    /** فیلدهای قابل جست‌وجو در لیست‌ها */
    public static array $searchable = [@@searchable@@];

    /** برچسب نمایشی فارسی */
    public static string $labelFa = '@@entity_label@@';

@@relations@@
@@scopes@@
    /** نمایش خوانا برای ارجاع در سایر فرم‌ها */
    public function displayLabel(): string
    {
@@display_label@@
    }
}
"""

CONTROLLER_TEMPLATE = """<?php

namespace App\\Http\\Controllers\\Api\\@@namespace@@;

use App\\Http\\Controllers\\Controller;
use App\\Http\\Requests\\@@namespace@@\\Store@@model@@Request;
use App\\Http\\Requests\\@@namespace@@\\Update@@model@@Request;
use App\\Http\\Resources\\@@namespace@@\\@@model@@Resource;
use App\\Models\\@@namespace@@\\@@model@@;
use Illuminate\\Http\\JsonResponse;
use Illuminate\\Http\\Request;
use Illuminate\\Http\\Resources\\Json\\AnonymousResourceCollection;
use Illuminate\\Support\\Facades\\Gate;

/**
 * @@entity_label@@ — کنترلر REST
 *
 * ماژول: @@module_code@@ — @@module_name@@
 * مسیر پایه: /api/v1/@@route_prefix@@/@@route_name@@
 */
class @@model@@Controller extends Controller
{
    /**
     * فهرست با جست‌وجو، فیلتر، مرتب‌سازی و صفحه‌بندی
     */
    public function index(Request $request): AnonymousResourceCollection
    {
        Gate::authorize('viewAny', @@model@@::class);

        $query = @@model@@::query()@@with_relations@@;

        // جست‌وجوی متنی
        if ($term = $request->query('q')) {
            $query->search($term);
        }

        // فیلتر بر اساس وضعیت
        if ($status = $request->query('status')) {
            $query->where('status', $status);
        }

@@filters@@

        // مرتب‌سازی
        $sortBy = $request->query('sort_by', '@@default_sort@@');
        $sortDir = strtolower($request->query('sort_dir', 'desc')) === 'asc' ? 'asc' : 'desc';
        $allowedSorts = @@sortable@@;
        $query->orderBy(in_array($sortBy, $allowedSorts, true) ? $sortBy : '@@default_sort@@', $sortDir);

        $perPage = min((int) $request->query('per_page', 25), 200);

        return @@model@@Resource::collection($query->paginate($perPage)->withQueryString());
    }

    /**
     * نمایش یک رکورد
     */
    public function show(@@model@@ $@@route_param@@): @@model@@Resource
    {
        Gate::authorize('view', $@@route_param@@);

        return new @@model@@Resource($@@route_param@@->load(@@load_relations@@));
    }

    /**
     * ایجاد رکورد جدید
     */
    public function store(Store@@model@@Request $request): JsonResponse
    {
        Gate::authorize('create', @@model@@::class);

        $@@route_param@@ = @@model@@::create($request->validated());

        activity()
            ->causedBy($request->user())
            ->performedOn($@@route_param@@)
            ->withProperties(['module' => '@@module_code@@'])
            ->log('create');

        return (new @@model@@Resource($@@route_param@@))
            ->response()
            ->setStatusCode(201);
    }

    /**
     * به‌روزرسانی رکورد
     */
    public function update(Update@@model@@Request $request, @@model@@ $@@route_param@@): JsonResponse
    {
        Gate::authorize('update', $@@route_param@@);

        $@@route_param@@->update($request->validated());

        activity()
            ->causedBy($request->user())
            ->performedOn($@@route_param@@)
            ->withProperties(['changed' => array_keys($request->validated())])
            ->log('update');

        return (new @@model@@Resource($@@route_param@@))->response();
    }

    /**
     * حذف (نرم) رکورد
     */
    public function destroy(Request $request, @@model@@ $@@route_param@@): JsonResponse
    {
        Gate::authorize('delete', $@@route_param@@);

        $@@route_param@@->delete();

        activity()
            ->causedBy($request->user())
            ->performedOn($@@route_param@@)
            ->log('delete');

        return response()->json(['message' => 'رکورد با موفقیت حذف شد.']);
    }
@@extra_actions@@
}
"""

REQUEST_TEMPLATE = """<?php

namespace App\\Http\\Requests\\@@namespace@@;

use Illuminate\\Foundation\\Http\\FormRequest;
use Illuminate\\Support\\Facades\\Auth;

/**
 * اعتبارسنجی @@action_label@@ «@@entity_label@@»
 *
 * ماژول: @@module_code@@ — @@module_name@@
 */
class @@class_name@@ extends FormRequest
{
    public function authorize(): bool
    {
        return Auth::check();
    }

    /**
     * @return array<string, mixed>
     */
    public function rules(): array
    {
        return [
@@rules@@
        ];
    }

    /**
     * پیام‌های فارسی اعتبارسنجی
     *
     * @return array<string, string>
     */
    public function messages(): array
    {
        return [
@@messages@@
        ];
    }

    /**
     * نام فارسی فیلدها برای نمایش در خطاها
     *
     * @return array<string, string>
     */
    public function attributes(): array
    {
        return [
@@attribute_labels@@
        ];
    }

    protected function prepareForValidation(): void
    {
@@prepare@@
    }
}
"""

RESOURCE_TEMPLATE = """<?php

namespace App\\Http\\Resources\\@@namespace@@;

use Illuminate\\Http\\Request;
use Illuminate\\Http\\Resources\\Json\\JsonResource;

/**
 * خروجی API برای «@@entity_label@@»
 *
 * مقادیر تاریخ به صورت میلادی و در فیلدهای *_jalali به شمسی برگردانده می‌شود
 * تا کلاینت React بتواند هر دو را مصرف کند.
 */
class @@model@@Resource extends JsonResource
{
    /**
     * @return array<string, mixed>
     */
    public function toArray(Request $request): array
    {
        return [
@@fields@@
@@relations@@
@@jalali@@
@@meta@@
        ];
    }
}
"""

POLICY_TEMPLATE = """<?php

namespace App\\Policies\\@@namespace@@;

use App\\Models\\@@namespace@@\\@@model@@;
use App\\Models\\System\\User;

/**
 * سیاست دسترسی «@@entity_label@@»
 *
 * ماژول: @@module_code@@ — @@module_name@@
 * نام مجوز: @@permission_base@@.*
 */
class @@model@@Policy
{
    public function viewAny(User $user): bool
    {
        return $user->hasPermissionTo('@@permission_base@@.view') || $user->hasRole('admin');
    }

    public function view(User $user, @@model@@ $@@route_param@@): bool
    {
        return $this->viewAny($user);
    }

    public function create(User $user): bool
    {
        return $user->hasPermissionTo('@@permission_base@@.create') || $user->hasRole('admin');
    }

    public function update(User $user, @@model@@ $@@route_param@@): bool
    {
        return $user->hasPermissionTo('@@permission_base@@.edit') || $user->hasRole('admin');
    }

    public function delete(User $user, @@model@@ $@@route_param@@): bool
    {
        return $user->hasPermissionTo('@@permission_base@@.delete') || $user->hasRole('admin');
    }

    public function approve(User $user, @@model@@ $@@route_param@@): bool
    {
        return $user->hasPermissionTo('@@permission_base@@.approve') || $user->hasRole('admin');
    }

    public function restore(User $user, @@model@@ $@@route_param@@): bool
    {
        return $user->hasRole('admin');
    }

    public function forceDelete(User $user, @@model@@ $@@route_param@@): bool
    {
        return $user->hasRole('admin');
    }
}
"""

FACTORY_TEMPLATE = """<?php

namespace Database\\Factories\\@@namespace@@;

use App\\Models\\@@namespace@@\\@@model@@;
use Illuminate\\Database\\Eloquent\\Factories\\Factory;

/**
 * کارخانه داده آزمایشی «@@entity_label@@»
 *
 * @extends Factory<@@model@@>
 */
class @@model@@Factory extends Factory
{
    protected $model = @@model@@::class;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
@@definitions@@
        ];
    }
}
"""

SEEDER_TEMPLATE = """<?php

namespace Database\\Seeders;

use Illuminate\\Database\\Seeder;
@@model_imports@@

/**
 * داده اولیه ماژول @@module_code@@ — @@module_name@@
@@demo_note@@
 */
class @@module_namespace@@ extends Seeder
{
    public function run(): void
    {
@@body@@
    }
}
"""

TEST_TEMPLATE = """<?php

namespace Tests\\Feature\\@@namespace@@;

use App\\Models\\@@namespace@@\\@@model@@;
use App\\Models\\System\\User;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

/**
 * آزمون عملکردی «@@entity_label@@» — ماژول @@module_code@@
 */
class @@model@@Test extends TestCase
{
    use RefreshDatabase;

    private function actingAsAdmin(): User
    {
        $user = User::factory()->create(['is_super_admin' => true]);
        $this->actingAs($user, 'sanctum');

        return $user;
    }

    public function test_admin_can_list_records(): void
    {
        $this->actingAsAdmin();
        @@model@@::factory()->count(3)->create();

        $response = $this->getJson('/api/v1/@@route_prefix@@/@@route_name@@?per_page=10');

        $response->assertOk()->assertJsonCount(3, 'data');
    }

    public function test_guest_cannot_list_records(): void
    {
        $response = $this->getJson('/api/v1/@@route_prefix@@/@@route_name@@');

        $response->assertUnauthorized();
    }

    public function test_admin_can_create_record(): void
    {
        $this->actingAsAdmin();

        $payload = @@model@@::factory()->make()->toArray();
@@payload_clean@@

        $response = $this->postJson('/api/v1/@@route_prefix@@/@@route_name@@', $payload);

        $response->assertCreated();
        $this->assertDatabaseCount('@@table@@', 1);
    }

    public function test_validation_rejects_empty_payload(): void
    {
        $this->actingAsAdmin();

        $response = $this->postJson('/api/v1/@@route_prefix@@/@@route_name@@', []);

        $response->assertStatus(422);
    }

    public function test_admin_can_soft_delete_record(): void
    {
        $this->actingAsAdmin();
        $record = @@model@@::factory()->create();

        $response = $this->deleteJson("/api/v1/@@route_prefix@@/@@route_name@@/{$record->id}");

        $response->assertOk();
        $this->assertSoftDeleted('@@table@@', ['id' => $record->id]);
    }
}
"""

SERVICE_TEMPLATE = """<?php

namespace App\\Services\\@@namespace@@;

use App\\Models\\@@namespace@@\\@@primary_model@@;
use App\\Support\\AvalAiClient;
use App\\Support\\AiServiceClient;
use Illuminate\\Support\\Collection;
use Illuminate\\Support\\Facades\\DB;
use Illuminate\\Support\\Facades\\Log;

/**
 * سرویس کسب‌وکاری ماژول @@module_code@@ — @@module_name@@
 *
 * @@module_description@@
 *
 * نقاط هوش مصنوعی این ماژول از سرویس پایتون (@@ai_service_url@@)
 * و در صورت نیاز به پردازش زبانی از AvalAI فراخوانی می‌شوند.
 */
class @@module_namespace@@
{
    public function __construct(
        protected AiServiceClient $ai,
        protected AvalAiClient $llm,
    ) {
    }

    /** خلاصه وضعیت ماژول برای داشبورد */
    public function dashboard(): array
    {
@@dashboard_body@@
    }

@@ai_methods@@

    /** گزارش ساده CSV-ready از رکوردهای ماژول */
    public function export(Collection $filters): array
    {
        $query = @@primary_model@@::query();

        if ($term = $filters->get('q')) {
            $query->search($term);
        }

        return $query->orderBy('id')->limit(50000)->get()->toArray();
    }
}
"""


# --------------------------------------------------------------------------- #
# ساخت فایل‌ها
# --------------------------------------------------------------------------- #
def _relation_method_name(field_name: str) -> str:
    base = re.sub(r"_id$", "", field_name)
    return camel(base)


def _sortable_fields(entity: dict[str, Any]) -> list[str]:
    sortable = ["id", "created_at", "updated_at"]
    for field in entity["fields"]:
        if field["type"] in ("date", "datetime", "decimal", "integer", "bigint") or field["name"] in (
            "code",
            "title",
            "status",
        ):
            sortable.append(field["name"])
    return sortable


def _default_sort(entity: dict[str, Any]) -> str:
    for candidate in ("occurred_at", "due_date", "start_date", "created_at", "id"):
        names = {f["name"] for f in entity["fields"]}
        if candidate in names:
            return candidate
    return "id"


def build_migration(
    entity: dict[str, Any],
    module: dict[str, Any],
    sequence: int,
    *,
    multi_tenant: bool,
    indexed_search: list[str],
) -> tuple[str, str]:
    columns = []
    for field in entity["fields"]:
        columns.append(column_definition(field))

    extra_indexes = []
    for col in indexed_search:
        extra_indexes.append(
            f"        // ایندکس جست‌وجو بر اساس نیاز گزارش‌گیری\n"
            f"        Schema::table('{entity['table']}', function (Blueprint $table) {{\n"
            f"            $table->index('{col}');\n"
            f"        }});"
        )

    tenant_column = ""
    if multi_tenant and not any(f["name"] == "company_id" for f in entity["fields"]):
        tenant_column = "            $table->foreignId('company_id')->nullable()->index()->comment('شرکت/کارخانه مالک رکورد');"

    soft_deletes = "            $table->softDeletes();" if entity.get("soft_deletes", True) else ""

    timestamp = f"2026_01_01_{sequence:06d}"
    path = f"backend/database/migrations/{timestamp}_create_{entity['table']}_table.php"
    content = render(
        MIGRATION_TEMPLATE,
        comment=f"ساخت جدول {entity['table']} — {entity['label_fa']}",
        module_code=module["code"],
        module_name=module["label_fa"],
        entity_name=entity["name"],
        entity_label=entity["label_fa"],
        table=entity["table"],
        columns="\n            ".join(columns) if columns else "            // بدون ستون اختصاصی",
        tenant_column=tenant_column,
        soft_deletes=soft_deletes,
        extra_indexes="\n\n".join(extra_indexes) if extra_indexes else "        // ایندکس اضافی لازم نیست",
    )
    return path, content


def build_model(entity: dict[str, Any], module: dict[str, Any], table_models: dict[str, str]) -> tuple[str, str]:
    namespace = module_namespace(module)
    fillable = "\n".join(f"        '{field['name']}'," for field in entity["fields"])
    if not fillable:
        fillable = "        // فیلدها در مهاجرت تعریف شده‌اند"

    casts_lines = []
    for field in entity["fields"]:
        cast = cast_for(field)
        if cast:
            casts_lines.append(f"        '{field['name']}' => {cast},")
    casts = "\n".join(casts_lines) or "        'id' => 'integer',"

    defaults_lines = []
    for field in entity["fields"]:
        default = field.get("default")
        if default is None or str(default).lower() in SKIP_DEFAULTS:
            continue
        if field["type"] == "boolean":
            rendered = "true" if str(default).lower() in ("1", "true", "yes") else "false"
        elif field["type"] in NUMERIC_TYPES:
            try:
                numeric = float(default)
                rendered = str(int(numeric)) if numeric.is_integer() else str(numeric)
            except (TypeError, ValueError):
                continue
        else:
            rendered = php_value(str(default))
        defaults_lines.append(f"        '{field['name']}' => {rendered},")
    defaults = "\n".join(defaults_lines) or "        // بدون مقدار پیش‌فرض"

    uses = ["use Illuminate\\Database\\Eloquent\\Relations\\BelongsTo;"]
    traits = ["    use HasFactory;"]
    if entity.get("soft_deletes", True):
        uses.insert(0, "use Illuminate\\Database\\Eloquent\\SoftDeletes;")
        traits.append("    use SoftDeletes;")

    relations: list[str] = []
    for field in entity["fields"]:
        if field["type"] != "foreign":
            continue
        target_table = field.get("references_table", "")
        target_model = table_models.get(target_table)
        if not target_model:
            continue
        method = _relation_method_name(field["name"])
        relations.append(
            f"    /** {field['label']} */\n"
            f"    public function {method}(): BelongsTo\n"
            f"    {{\n"
            f"        return $this->belongsTo(\\{target_model}::class, '{field['name']}');\n"
            f"    }}\n"
        )

    searchable = ", ".join(
        f"'{field['name']}'" for field in entity["fields"] if field.get("searchable")
    ) or "'id'"

    scopes = [
        "    /** دامنه جست‌وجوی متنی روی فیلدهای searchable */",
        "    public function scopeSearch($query, ?string $term)",
        "    {",
        "        if (!$term) {",
        "            return $query;",
        "        }",
        "",
        "        return $query->where(function ($q) use ($term) {",
    ]
    searchable_fields = [f["name"] for f in entity["fields"] if f.get("searchable")] or ["id"]
    for i, name in enumerate(searchable_fields[:6]):
        prefix = "            $q->where" if i == 0 else "              ->orWhere"
        scopes.append(f"{prefix}('{name}', 'like', \"%{{$term}}%\")")
    scopes.append("        });")
    scopes.append("    }")
    scopes.append("")
    scopes.append("    /** دامنه فیلتر بر اساس وضعیت */")
    scopes.append("    public function scopeStatus($query, ?string $status)")
    scopes.append("    {")
    scopes.append("        return $status ? $query->where('status', $status) : $query;")
    scopes.append("    }")

    display_field = next(
        (f["name"] for f in entity["fields"] if f["name"] in ("title", "name", "code", "subject", "plan_name")),
        "id",
    )
    display_label = f"        return (string) ($this->{display_field} ?? $this->id);"

    notes_doc = f" * یادداشت: {entity['notes']}" if entity.get("notes") else ""

    path = f"backend/app/Models/{namespace}/{entity['name']}.php"
    content = render(
        MODEL_TEMPLATE,
        namespace=namespace,
        uses="\n".join(uses),
        entity_label=entity["label_fa"],
        module_code=module["code"],
        module_name=module["label_fa"],
        table=entity["table"],
        notes_doc=notes_doc,
        model=entity["name"],
        traits="\n".join(traits),
        fillable=fillable,
        casts=casts,
        defaults=defaults,
        searchable=searchable,
        relations="\n".join(relations) if relations else "    // این موجودیت رابطه خارجی ندارد",
        scopes="\n".join(scopes),
        display_label=display_label,
    )
    return path, content


def build_controller(entity: dict[str, Any], module: dict[str, Any], route_prefix: str) -> tuple[str, str]:
    namespace = module_namespace(module)
    route_name = entity["table"]
    route_param = route_param_for(entity["table"]) or "record"
    with_relations = [
        _relation_method_name(f["name"]) for f in entity["fields"] if f["type"] == "foreign"
    ][:6]
    load_relations = ", ".join(f"'{r}'" for r in with_relations) or ""

    filters = []
    for field in entity["fields"]:
        if field["type"] == "enum":
            filters.append(
                f"        if ($value = $request->query('{field['name']}')) {{\n"
                f"            $query->where('{field['name']}', $value);\n"
                f"        }}"
            )
        elif field["type"] == "foreign":
            filters.append(
                f"        if ($value = $request->query('{field['name']}')) {{\n"
                f"            $query->where('{field['name']}', $value);\n"
                f"        }}"
            )
    filters = filters[:8]

    has_status = any(f["name"] == "status" for f in entity["fields"])
    extra_actions = []
    if has_status:
        extra_actions.append(
            f"""
    /**
     * تغییر وضعیت رکورد (گردش کار ساده)
     */
    public function changeStatus(Request $request, @@model@@ $@@route_param@@): JsonResponse
    {{
        Gate::authorize('update', $@@route_param@@);

        $validated = $request->validate([
            'status' => ['required', 'string'],
            'note' => ['nullable', 'string'],
        ], [], ['status' => 'وضعیت', 'note' => 'یادداشت']);

        $@@route_param@@->update($validated);

        activity()
            ->causedBy($request->user())
            ->performedOn($@@route_param@@)
            ->withProperties($validated)
            ->log('status-change');

        return (new @@model@@Resource($@@route_param@@))->response();
    }}"""
        )

    content = render(
        CONTROLLER_TEMPLATE,
        namespace=namespace,
        model=entity["name"],
        entity_label=entity["label_fa"],
        module_code=module["code"],
        module_name=module["label_fa"],
        route_prefix=route_prefix,
        route_name=route_name,
        route_param=route_param,
        with_relations=f"->with([{', '.join(f'{chr(39)}{r}{chr(39)}' for r in with_relations)}])" if with_relations else "",
        filters="\n\n".join(filters) if filters else "        // فیلتر اختصاصی تعریف نشده است",
        default_sort=_default_sort(entity),
        sortable=str(_sortable_fields(entity)),
        load_relations=load_relations,
        extra_actions="".join(
            render(action, model=entity["name"], route_param=route_param) for action in extra_actions
        )
        or "\n    // اکشن اختصاصی این موجودیت در سرویس ماژول پیاده‌سازی می‌شود\n",
    )
    path = f"backend/app/Http/Controllers/Api/{namespace}/{entity['name']}Controller.php"
    return path, content


def build_requests(entity: dict[str, Any], module: dict[str, Any], known_tables: set[str]) -> list[tuple[str, str]]:
    namespace = module_namespace(module)
    route_param = route_param_for(entity["table"]) or "record"
    outputs: list[tuple[str, str]] = []

    for for_update in (False, True):
        class_name = f"{'Update' if for_update else 'Store'}{entity['name']}Request"
        rules_lines: list[str] = []
        messages_lines: list[str] = []
        labels_lines: list[str] = []
        for field in entity["fields"]:
            rules = validation_rules(
                field,
                table=entity["table"],
                route_param=route_param,
                for_update=for_update,
                known_tables=known_tables,
            )
            if not rules:
                rules = ["'nullable'"]
            rendered_rules = ",\n".join(f"                {rule}," for rule in rules)
            rules_lines.append(f"            '{field['name']}' => [\n{rendered_rules}\n            ],")
            if is_required(field) and not for_update:
                messages_lines.append(f"            '{field['name']}.required' => '{field['label']} الزامی است.',")
            labels_lines.append(f"            '{field['name']}' => '{field['label']}',")

        prepare_lines = []
        for field in entity["fields"]:
            if field["type"] == "string" and field["name"] in ("code", "national_id", "economic_code", "phone", "mobile"):
                prepare_lines.append(
                    f"        if ($this->has('{field['name']}')) {{\n"
                    f"            $this->merge(['{field['name']}' => trim((string) $this->input('{field['name']}'))]);\n"
                    f"        }}"
                )
        numeric_fields = [f["name"] for f in entity["fields"] if f["type"] in NUMERIC_TYPES][:12]
        if numeric_fields:
            prepare_lines.append(
                "        // تبدیل ارقام فارسی/عربی به لاتین و حذف جداکننده هزارگان\n"
                "        foreach (['" + "', '".join(numeric_fields) + "'] as $numericField) {\n"
                "            if ($this->filled($numericField)) {\n"
                "                $this->merge([\n"
                "                    $numericField => \\App\\Support\\PersianText::toNumber($this->input($numericField)),\n"
                "                ]);\n"
                "            }\n"
                "        }"
            )

        content = render(
            REQUEST_TEMPLATE,
            namespace=namespace,
            action_label="به‌روزرسانی" if for_update else "ایجاد",
            entity_label=entity["label_fa"],
            module_code=module["code"],
            module_name=module["label_fa"],
            class_name=class_name,
            rules="\n".join(rules_lines) or "            // بدون قاعده الزامی",
            messages="\n".join(messages_lines[:40]) or "            // پیام پیش‌فرض لاراول استفاده می‌شود",
            attribute_labels="\n".join(labels_lines),
            prepare="\n\n".join(prepare_lines) if prepare_lines else "        // آماده‌سازی ویژه‌ای لازم نیست",
        )
        outputs.append((f"backend/app/Http/Requests/{namespace}/{class_name}.php", content))

    return outputs


def build_resource(entity: dict[str, Any], module: dict[str, Any], table_models: dict[str, str]) -> tuple[str, str]:
    namespace = module_namespace(module)
    field_lines = ["            'id' => $this->id,"]
    relation_lines: list[str] = []
    jalali_lines: list[str] = []

    for field in entity["fields"]:
        name = field["name"]
        if field.get("hidden"):
            field_lines.append(f"            '{name}' => $this->when(app('request')->user()?->hasRole('admin'), $this->{name}),")
        elif field["type"] == "decimal":
            field_lines.append(f"            '{name}' => $this->{name} !== null ? (float) $this->{name} : null,")
        else:
            field_lines.append(f"            '{name}' => $this->{name},")

        if field["type"] == "foreign":
            method = _relation_method_name(name)
            target_table = field.get("references_table", "")
            target_model = table_models.get(target_table, "")
            display = "displayLabel()" if target_model else "'id'"
            relation_lines.append(
                f"            '{method}' => $this->whenLoaded('{method}', fn () => ["
                f"'id' => $this->{method}?->id, 'label' => $this->{method}?->{display}]),"
            )

        if field["type"] in DATE_TYPES:
            jalali_lines.append(
                f"            '{name}_jalali' => \\App\\Support\\Jalali::format($this->{name}),"
            )

    meta = [
        "            'created_at' => $this->created_at?->toIso8601String(),",
        "            'created_at_jalali' => \\App\\Support\\Jalali::format($this->created_at),",
        "            'updated_at' => $this->updated_at?->toIso8601String(),",
    ]
    if entity.get("soft_deletes", True):
        meta.append("            'deleted_at' => $this->deleted_at?->toIso8601String(),")

    path = f"backend/app/Http/Resources/{namespace}/{entity['name']}Resource.php"
    content = render(
        RESOURCE_TEMPLATE,
        namespace=namespace,
        model=entity["name"],
        entity_label=entity["label_fa"],
        fields="\n".join(field_lines),
        relations="\n".join(relation_lines) if relation_lines else "            // بدون رابطه خارجی",
        jalali="\n".join(jalali_lines) if jalali_lines else "            // بدون فیلد تاریخ",
        meta="\n".join(meta),
    )
    return path, content


def build_policy(entity: dict[str, Any], module: dict[str, Any]) -> tuple[str, str]:
    namespace = module_namespace(module)
    route_param = route_param_for(entity["table"]) or "record"
    permission_base = f"{module['slug']}.{entity['table']}"
    path = f"backend/app/Policies/{namespace}/{entity['name']}Policy.php"
    content = render(
        POLICY_TEMPLATE,
        namespace=namespace,
        model=entity["name"],
        entity_label=entity["label_fa"],
        module_code=module["code"],
        module_name=module["label_fa"],
        route_param=route_param,
        permission_base=permission_base,
    )
    return path, content


def build_factory(entity: dict[str, Any], module: dict[str, Any]) -> tuple[str, str]:
    namespace = module_namespace(module)
    code_prefix = entity["table"][:3].upper()
    lines: list[str] = []
    for field in entity["fields"]:
        name = field["name"]
        ftype = field["type"]
        if ftype == "foreign":
            lines.append(f"            // '{name}' در آزمون با رکورد واقعی مقداردهی می‌شود")
        elif ftype == "enum":
            options = field.get("options") or ["draft"]
            quoted = ", ".join(f"'{o}'" for o in options)
            lines.append(f"            '{name}' => $this->faker->randomElement([{quoted}]),")
        elif ftype == "string":
            if "code" in name:
                lines.append(f"            '{name}' => strtoupper($this->faker->unique()->bothify('{code_prefix}-####-##')),")
            elif "email" in name:
                lines.append(f"            '{name}' => $this->faker->unique()->safeEmail(),")
            elif "phone" in name or "mobile" in name:
                lines.append(f"            '{name}' => '0912' . $this->faker->numerify('#######'),")
            elif "national_id" in name:
                lines.append(f"            '{name}' => $this->faker->numerify('##########'),")
            elif "color" in name:
                lines.append(f"            '{name}' => $this->faker->hexColor(),")
            else:
                lines.append(f"            '{name}' => $this->faker->words(3, true),")
        elif ftype == "text":
            lines.append(f"            '{name}' => $this->faker->paragraph(),")
        elif ftype == "integer":
            lines.append(f"            '{name}' => $this->faker->numberBetween(1, 100),")
        elif ftype == "bigint":
            lines.append(f"            '{name}' => $this->faker->numberBetween(1000, 999999),")
        elif ftype == "decimal":
            lines.append(f"            '{name}' => $this->faker->randomFloat(2, 1, 100000),")
        elif ftype == "boolean":
            lines.append(f"            '{name}' => $this->faker->boolean(70),")
        elif ftype == "date":
            lines.append(f"            '{name}' => $this->faker->dateTimeBetween('-1 year', '+1 year')->format('Y-m-d'),")
        elif ftype == "datetime":
            lines.append(f"            '{name}' => $this->faker->dateTimeBetween('-6 months', '+1 month'),")
        elif ftype == "time":
            lines.append(f"            '{name}' => $this->faker->time('H:i:s'),")
        elif ftype == "json":
            lines.append(f"            '{name}' => ['source' => 'factory', 'generated' => now()->toIso8601String()],")
        elif ftype == "uuid":
            lines.append(f"            '{name}' => (string) \\Illuminate\\Support\\Str::uuid(),")

    if not lines:
        lines.append("            // فیلدی برای مقداردهی خودکار وجود ندارد")

    path = f"backend/database/factories/{namespace}/{entity['name']}Factory.php"
    content = render(
        FACTORY_TEMPLATE,
        namespace=namespace,
        model=entity["name"],
        entity_label=entity["label_fa"],
        definitions="\n".join(lines),
        code_prefix=entity["table"][:3].upper(),
    )
    return path, content


def build_test(entity: dict[str, Any], module: dict[str, Any], route_prefix: str) -> tuple[str, str]:
    namespace = module_namespace(module)
    route_name = entity["table"]
    payload_clean = [
        "        unset($payload['created_at'], $payload['updated_at'], $payload['deleted_at'], $payload['id']);",
    ]
    for field in entity["fields"]:
        if field["type"] == "foreign":
            payload_clean.append(f"        unset($payload['{field['name']}']);")

    path = f"backend/tests/Feature/{namespace}/{entity['name']}Test.php"
    content = render(
        TEST_TEMPLATE,
        namespace=namespace,
        model=entity["name"],
        entity_label=entity["label_fa"],
        module_code=module["code"],
        table=entity["table"],
        route_prefix=route_prefix,
        route_name=route_name,
        payload_clean="\n".join(payload_clean),
    )
    return path, content


def build_seeder(
    module: dict[str, Any],
    entities: list[dict[str, Any]],
    *,
    include_demo_data: bool,
) -> tuple[str, str]:
    namespace = module_namespace(module)
    imports = "\n".join(f"use App\\Models\\{namespace}\\{entity['name']};" for entity in entities)
    body_lines: list[str] = []

    for entity in entities:
        if include_demo_data:
            body_lines.append(
                f"        {entity['name']}::factory()->count(5)->create();"
            )
        else:
            body_lines.append(
                f"        // {entity['name']}::factory()->count(5)->create(); // فقط در حالت داده نمونه"
            )

    body = "\n".join(body_lines) or "        // این ماژول موجودیت قابل seed ندارد"
    demo_note = (
        " * داده نمونه فعال است (include_demo_data=true)."
        if include_demo_data
        else " * داده نمونه غیرفعال است؛ فقط ساختار آماده است."
    )

    seeder_class = f"{namespace}{module['code']}Seeder"
    path = f"backend/database/seeders/{seeder_class}.php"
    content = render(
        SEEDER_TEMPLATE,
        module_code=module["code"],
        module_name=module["label_fa"],
        module_namespace=seeder_class,
        model_imports=imports,
        demo_note=demo_note,
        body=body,
    )
    return path, content


def build_service(
    module: dict[str, Any],
    entities: list[dict[str, Any]],
    ai_points: list[dict[str, Any]],
    *,
    ai_service_url: str,
) -> tuple[str, str]:
    namespace = module_namespace(module)
    primary = entities[0] if entities else None
    primary_model = primary["name"] if primary else "SystemFeature"

    dashboard_lines: list[str] = ["        return ["]
    dashboard_lines.append(f"            'module' => '{module['code']}',")
    dashboard_lines.append(f"            'module_name' => '{module['label_fa']}',")
    for entity in entities[:6]:
        dashboard_lines.append(
            f"            '{entity['table']}_count' => {entity['name']}::count(),"
        )
    if primary:
        dashboard_lines.append(
            f"            'latest' => {primary_model}::latest('id')->limit(5)->get(['id', 'created_at'])->toArray(),"
        )
    dashboard_lines.append("        ];")

    ai_methods: list[str] = []
    for point in ai_points[:14]:
        method = camel(point["name"].split("🤖")[-1].strip()[:40] or point["code"].replace(".", "_"))
        method = re.sub(r"[^A-Za-z0-9]", "", method) or f"ai{point['code'].replace('.', '')}"
        ai_methods.append(
            f"""    /**
     * 🤖 {point['name']}
     *
     * موتور: {point['engine_name_fa']} ({point['engine']})
     * اندپوینت سرویس AI: {point['endpoint']}
     */
    public function {method}(array $payload): array
    {{
        $payload['model_id'] = '{point['model_id']}';
        $payload['feature_flag'] = '{point['feature_flag']}';

        try {{
            return $this->ai->call('{point['endpoint']}', $payload);
        }} catch (\\Throwable $exception) {{
            Log::warning('AI call failed for {point['code']}: ' . $exception->getMessage());

            return [
                'ok' => false,
                'fallback' => true,
                'error' => $exception->getMessage(),
                'capability' => '{point['code']}',
            ];
        }}
    }}
"""
        )

    if not ai_methods:
        ai_methods.append(
            """    /**
     * این ماژول نقطه هوش مصنوعی فعالی ندارد.
     */
    public function aiStatus(): array
    {
        return ['ok' => true, 'engines' => []];
    }
"""
        )

    service_class = f"{namespace}{module['code']}Service"
    path = f"backend/app/Services/{namespace}/{service_class}.php"
    content = render(
        SERVICE_TEMPLATE,
        namespace=namespace,
        module_code=module["code"],
        module_name=module["label_fa"],
        module_description=module.get("description", ""),
        module_namespace=service_class,
        primary_model=primary_model,
        ai_service_url=ai_service_url,
        dashboard_body="\n".join(dashboard_lines),
        ai_methods="\n".join(ai_methods),
    )
    return path, content


def generate_domain_files(
    package: Package,
    modules: list[dict[str, Any]],
    specs: dict[str, Any],
    *,
    settings: dict[str, Any],
    ai_points_by_module: dict[str, list[dict[str, Any]]],
    route_prefix: str = "v1",
) -> dict[str, Any]:
    """تولید همه فایل‌های لایه دامنه لاراول."""
    entities = specs["entities"]
    table_models: dict[str, str] = {}
    module_of_entity: dict[str, dict[str, Any]] = {}
    module_by_code = {m["code"]: m for m in modules}

    # ماژول مجازی برای موجودیت‌های پلتفرمی (بدون کد ماژول کاتالوگ)
    PLATFORM_MODULE = {
        "code": "S0",
        "slug": "system",
        "label_fa": "هسته پلتفرم",
        "name_en": "Platform Core",
        "description": "رجیستری قابلیت‌ها و موجودیت‌های پلتفرمی",
        "ai_endpoints": [],
        "menu_group": "سامانه",
        "priority": 1,
        "derived": False,
    }
    known_codes = set(module_by_code)
    if any(e["module_code"] not in known_codes for e in entities):
        module_by_code["S0"] = PLATFORM_MODULE

    def module_for(entity: dict[str, Any]) -> dict[str, Any] | None:
        return module_by_code.get(entity["module_code"]) or module_by_code.get("S0")

    for entity in entities:
        module = module_for(entity)
        if module is None:
            continue
        namespace = module_namespace(module)
        table_models[entity["table"]] = f"App\\Models\\{namespace}\\{entity['name']}"
        module_of_entity[entity["table"]] = module

    known_tables = set(table_models)
    multi_tenant = bool(settings.get("multi_tenant", True))
    include_tests = bool(settings.get("include_tests", True))
    include_demo = bool(settings.get("include_demo_data", False))
    ai_service_url = settings.get("ai_service_url", "http://ai-service:8001")

    counters = {"migrations": 0, "models": 0, "controllers": 0, "requests": 0,
                "resources": 0, "policies": 0, "factories": 0, "tests": 0,
                "seeders": 0, "services": 0}

    # موجودیت‌های پلتفرمی (مثل SystemFeature) هیچ ماژول کاتالوگی ندارند؛
    # آن‌ها با ماژول مجازی S0 در فضای‌نام System تولید می‌شوند.
    build_modules = list(modules)
    if "S0" in module_by_code:
        build_modules.append(module_by_code["S0"])
    catalog_codes = {m["code"] for m in modules}

    sequence = 1
    for module in build_modules:
        if module["code"] == "S0":
            module_entities = [e for e in entities if e["module_code"] not in catalog_codes]
        else:
            module_entities = [e for e in entities if e["module_code"] == module["code"]]
        if not module_entities:
            continue

        # ۱) مهاجرت‌ها بر اساس ترتیب توپولوژیک (والد قبل از فرزند)
        for entity in module_entities:
            indexed = [f["name"] for f in entity["fields"] if f.get("searchable")][:1]
            path, content = build_migration(
                entity, module, sequence, multi_tenant=multi_tenant, indexed_search=indexed
            )
            package.add(path, content, area="laravel-migrations")
            counters["migrations"] += 1
            sequence += 1

        # ۲) مدل‌ها، کنترلرها، ریکوئست‌ها، ریسورس‌ها، سیاست‌ها
        for entity in module_entities:
            for builder in (
                lambda e=entity: build_model(e, module, table_models),
                lambda e=entity: build_controller(e, module, route_prefix),
                lambda e=entity: build_resource(e, module, table_models),
                lambda e=entity: build_policy(e, module),
                lambda e=entity: build_factory(e, module),
            ):
                path, content = builder()
                area = (
                    "laravel-models" if "/Models/" in path
                    else "laravel-controllers" if "/Controllers/" in path
                    else "laravel-resources" if "/Resources/" in path
                    else "laravel-policies" if "/Policies/" in path
                    else "laravel-factories"
                )
                package.add(path, content, area=area)
                key = (
                    "models" if area == "laravel-models"
                    else "controllers" if area == "laravel-controllers"
                    else "resources" if area == "laravel-resources"
                    else "policies" if area == "laravel-policies"
                    else "factories"
                )
                counters[key] += 1

            for path, content in build_requests(entity, module, known_tables):
                package.add(path, content, area="laravel-requests")
                counters["requests"] += 1

            if include_tests:
                path, content = build_test(entity, module, route_prefix)
                package.add(path, content, area="laravel-tests")
                counters["tests"] += 1

        # ۳) سرویس و سیدر ماژول
        path, content = build_service(
            module, module_entities, ai_points_by_module.get(module["code"], []),
            ai_service_url=ai_service_url,
        )
        package.add(path, content, area="laravel-services")
        counters["services"] += 1

        path, content = build_seeder(module, module_entities, include_demo_data=include_demo)
        package.add(path, content, area="laravel-seeders")
        counters["seeders"] += 1

    return {"counters": counters, "table_models": table_models, "entities": entities}
