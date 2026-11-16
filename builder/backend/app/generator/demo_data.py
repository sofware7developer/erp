# -*- coding: utf-8 -*-
"""
تولید داده نمونه تاریخ‌دار برای بسته خروجی
=============================================
چرا این ماژول لازم است:

  - Seederهای هر ماژول از `Model::factory()->count(5)` استفاده می‌کنند و
    کارخانه‌های داده (Factory) ستون‌های کلید خارجی را پر نمی‌کنند؛ پس درج واقعی
    روی پایگاه داده با خطای NOT NULL / FK شکست می‌خورد.
  - موتورهای هوش مصنوعی به «تاریخچه پیوسته» نیاز دارند (روند، فصلانگی،
    ناهنجاری، تخریب تدریجی) نه چند رکورد تصادفی.

راه‌حل: یک seeder عمومی که مشخصات ستون‌ها را از همان مدل دامنه‌ای می‌گیرد که
مایگریشن‌ها از آن ساخته شده‌اند (پس نام ستون همیشه معتبر است) و رکوردها را به
ترتیب توپولوژیک با کلید خارجی واقعی، تاریخ گسترده در بازه `demo_data_months` و
الگوهای سری زمانی مهندسی‌شده درج می‌کند.

خروجی:
    backend/database/seeders/Demo/DemoDataSpec.php      مشخصات جداول + پیکربندی
    backend/database/seeders/Demo/DemoHistorySeeder.php موتور درج داده نمونه
"""

from __future__ import annotations

import re
from typing import Any

from ..config import APP_NAME_FA
from ..domain.registry import topological_order
from .writers import Package, php_value

# جداولی که SystemSeeder آن‌ها را با معنای واقعی پر می‌کند؛ داده نمونه نباید
# روی آن‌ها بنویسد (کاربر/نقش/مجوز تکراری یا رمزشده ناسازگار می‌سازد).
SKIP_MODULES = {"S1"}
SKIP_TABLES = {"system_features", "companies", "user_roles", "role_permissions"}

DETAIL_HINTS = ("_item", "_items", "_line", "_lines", "_detail", "_details", "_entry", "_entries")
LEDGER_HINTS = ("_log", "_logs", "_event", "_events", "_reading", "_readings", "_record",
                "_records", "_transaction", "_transactions", "_movement", "_movements",
                "_history", "_sample", "_samples", "_inspection", "_inspections")

# الگوهای سری زمانی که موتورهای AI انتظار دارند
SERIES_PATTERNS: tuple[tuple[str, str, float, float, float], ...] = (
    # (kind, regex on "<table>.<column>", base, trend, spike)
    ("demand", r"(demand|forecast|sales|order|production|output|plan)_?(qty|quantity|amount|count|value|total)", 1200.0, 0.22, 1.55),
    ("defect", r"(defect|reject|scrap|ncr|nonconform|failure|fault|incident|accident)_?(count|qty|quantity|rate|number|total)?", 18.0, -0.18, 3.10),
    ("downtime", r"(downtime|stoppage|delay|idle|outage|mttr)_?(minutes|hours|time|count|duration)?", 46.0, -0.12, 2.60),
    ("energy", r"(energy|power|electric|gas|water|steam|fuel|consumption)_?(consumption|usage|kwh|value|amount|total)?", 340.0, 0.08, 1.45),
    ("cost", r"(cost|expense|price|amount|total|value|wage|salary|budget)_?(rial|amount|total|value)?", 850000.0, 0.30, 1.35),
    ("oee", r"(oee|efficiency|availability|performance|yield|capability|cpk|ppm)_?(rate|ratio|percent|index|value)?", 74.0, 0.10, 0.82),
    ("vibration", r"(vibration|temperature|pressure|current|rpm|speed|load|torque)_?(mm_s|c|bar|a|value|level)?", 2.6, 0.35, 3.40),
)

SEASONAL_JALALI = (0.72, 1.05, 1.10, 0.95, 0.85, 0.90, 1.00, 1.05, 1.12, 1.18, 1.02, 1.30)


# --------------------------------------------------------------------------- #
# تحلیل ستون‌ها
# --------------------------------------------------------------------------- #
def series_kind(table: str, column: str) -> str | None:
    """نوع الگوی سری زمانی برای یک ستون عددی (یا None)."""
    target = f"{table}.{column}"
    for kind, pattern, _base, _trend, _spike in SERIES_PATTERNS:
        if re.search(pattern, target):
            return kind
    return None


def series_params(kind: str) -> tuple[float, float, float]:
    for name, _pattern, base, trend, spike in SERIES_PATTERNS:
        if name == kind:
            return base, trend, spike
    return 100.0, 0.10, 1.50


def rows_for(entity: dict[str, Any], base_rows: int) -> int:
    """تعداد رکورد داده نمونه برای یک جدول."""
    table = entity["table"]
    multiplier = 1.0
    if any(hint in table for hint in DETAIL_HINTS):
        multiplier = 4.0
    elif any(hint in table for hint in LEDGER_HINTS):
        multiplier = 3.0
    rows = int(round(base_rows * multiplier))
    return max(3, min(rows, 240))


def skip_entity(entity: dict[str, Any]) -> str | None:
    """دلیل رد کردن یک موجودیت از داده نمونه (یا None)."""
    if entity["table"] in SKIP_TABLES:
        return "جدول پایه/سامانه"
    if (entity.get("module_code") or "") in SKIP_MODULES:
        return "کاربران و مجوزها توسط SystemSeeder پر می‌شوند"
    return None


def _column_spec(entity: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "name": field["name"],
        "type": field["type"],
        "nullable": bool(field.get("nullable")),
        "unique": bool(field.get("unique")),
        "label": field.get("label") or field["name"],
    }
    if field["type"] == "enum":
        spec["options"] = list(field.get("options") or [])
    if field["type"] == "foreign":
        spec["target"] = field.get("references_table") or ""
    if field["type"] in ("decimal", "integer", "bigint"):
        kind = series_kind(entity["table"], field["name"])
        if kind:
            base, trend, spike = series_params(kind)
            spec["series"] = kind
            spec["series_base"] = base
            spec["series_trend"] = trend
            spec["series_spike"] = spike
    if field.get("default") is not None:
        spec["default"] = str(field["default"])
    return spec


def build_demo_spec(
    entities: list[dict[str, Any]],
    *,
    months: int,
    rows: int,
    seed: int,
    company_name: str,
    currency: str,
    multi_tenant: bool,
) -> tuple[list[dict[str, Any]], list[tuple[str, str]], dict[str, Any]]:
    """مشخصات جداول داده نمونه، فهرست (جدول، دلیل) ردشدگان و پیکربندی."""
    tables: list[dict[str, Any]] = []
    skipped: list[tuple[str, str]] = []

    # ترتیب توپولوژیک: والد پیش از فرزند، تا DemoHistorySeeder بتواند کلید
    # خارجی اجباری را از شناسه‌های درج‌شده والد انتخاب کند (نه رد کردن جدول).
    ordered_entities = topological_order(entities)

    for entity in ordered_entities:
        reason = skip_entity(entity)
        if reason:
            skipped.append((entity["table"], reason))
            continue

        columns = [_column_spec(entity, field) for field in entity["fields"]]
        if multi_tenant and not any(col["name"] == "company_id" for col in columns):
            columns.append(
                {"name": "company_id", "type": "foreign", "target": "companies",
                 "nullable": True, "unique": False, "label": "شرکت مالک"}
            )

        tables.append(
            {
                "table": entity["table"],
                "label": entity.get("label_fa") or entity["name"],
                "module": entity.get("module_code") or "S0",
                "rows": rows_for(entity, rows),
                "timestamps": bool(entity.get("timestamps", True)),
                "columns": columns,
            }
        )

    config = {
        "months": max(1, int(months)),
        "rows": max(1, int(rows)),
        "seed": int(seed),
        "company_name": company_name,
        "currency": currency,
    }
    return tables, skipped, config


# --------------------------------------------------------------------------- #
# قالب‌های PHP
# --------------------------------------------------------------------------- #
SPEC_TEMPLATE = r'''<?php

namespace Database\Seeders\Demo;

/**
 * مشخصات داده نمونه — @@app_name_fa@@
 *
 * این فایل توسط «@@generator@@» از مدل دامنه ساخته شده است؛ ستون‌ها دقیقاً همان
 * ستون‌های مایگریشن‌ها هستند. ویرایش دستی توصیه نمی‌شود (بسته را دوباره بسازید).
 *
 * بازه تاریخچه: @@months@@ ماه · ردیف پایه هر جدول: @@rows@@ · بذر تصادفی: @@seed@@
 * جداول کنارگذاشته‌شده: @@skipped_count@@ (@@skipped_note@@)
 */
class DemoDataSpec
{
    /** ماه‌های تاریخچه نمونه */
    public const MONTHS = @@months@@;

    /** تعداد پایه ردیف برای هر جدول (جداول جزئیات/دفتر چند برابر می‌شوند) */
    public const ROWS = @@rows@@;

    /** بذر تولیدکننده اعداد شبه‌تصادفی تا خروجی تکرارپذیر باشد */
    public const SEED = @@seed@@;

    /** نام کارخانه برای متن‌های نمونه */
    public const COMPANY = @@company@@;

    /** واحد پول */
    public const CURRENCY = @@currency@@;

    /** فصلانگی ماه‌های شمسی (فروردین تا اسفند) — الگوی رایج کارخانه‌های ایرانی */
    public const SEASONAL = [@@seasonal@@];

    /**
     * فهرست جداول به ترتیب توپولوژیک (والد پیش از فرزند).
     *
     * @return array<int, array<string, mixed>>
     */
    public static function tables(): array
    {
        return [
@@tables@@
        ];
    }
}
'''

SEEDER_TEMPLATE = r'''<?php

namespace Database\Seeders\Demo;

use Illuminate\Database\Seeder;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

/**
 * داده نمونه تاریخ‌دار — @@months@@ ماه تاریخچه عملیاتی پیوسته
 *
 * این seeder برای هر جدول بسته (به‌جز کاربران/مجوزها که SystemSeeder می‌سازد)
 * رکوردهای سازگار درج می‌کند:
 *
 *   - کلیدهای خارجی از شناسه‌های «واقعی» جداول والد انتخاب می‌شوند؛ اگر والد
 *     اجباری رکوردی نداشته باشد، جدول با هشدار رد می‌شود (نه درج ناموفق).
 *   - تاریخ‌ها در بازه @@months@@ ماه پخش می‌شوند تا نمودارها و موتورهای AI
 *     روند و فصلانگی واقعی ببینند.
 *   - ستون‌های عددیِ نشانه‌گذاری‌شده، سری زمانی با روند + فصلانگی شمسی + نویز و
 *     چند نقطه ناهنجار عمدی می‌گیرند (خوراک موتورهای پیش‌بینی، SPC، ناهنجاری،
 *     قابلیت اطمینان و انرژی).
 *   - اعداد شبه‌تصادفی از بذر ثابت @@seed@@ می‌آیند، پس خروجی تکرارپذیر است.
 *
 * اجرا:  php artisan db:seed --class="Database\\Seeders\\Demo\\DemoHistorySeeder"
 */
class DemoHistorySeeder extends Seeder
{
    /** مقدار نشانه‌گذار «این ستون درج نشود» */
    private const SKIP = '@@skip_marker@@';

    private int $state = @@seed@@;

    /** @var array<string, array<int, int|string>> شناسه‌های هر جدول برای کلید خارجی */
    private array $ids = [];

    private int $inserted = 0;

    private int $seededTables = 0;

    /** @var array<int, string> */
    private array $skipped = [];

    public function run(): void
    {
        $startedAt = microtime(true);
        $tables = DemoDataSpec::tables();

        foreach ($tables as $entry) {
            $this->seedTable($entry);
        }

        $seconds = number_format(microtime(true) - $startedAt, 1);
        $this->command?->info(sprintf(
            'داده نمونه: %s رکورد در %s جدول از %s جدول (%s ثانیه)',
            number_format($this->inserted),
            number_format($this->seededTables),
            number_format(count($tables)),
            $seconds
        ));

        if ($this->skipped !== []) {
            $this->command?->warn(
                'جداول رد شده (' . count($this->skipped) . '): ' . implode(' | ', array_slice($this->skipped, 0, 12))
            );
        }

        $this->command?->warn('این داده برای نمایش و آموزش است؛ در محیط تولید استفاده نکنید.');
    }

    /**
     * درج رکوردهای یک جدول.
     *
     * @param  array<string, mixed>  $entry
     */
    private function seedTable(array $entry): void
    {
        $table = (string) $entry['table'];

        if (! Schema::hasTable($table)) {
            $this->skipped[] = $table . ' (جدول در پایگاه داده نیست)';

            return;
        }

        /** @var array<int, array<string, mixed>> $columns */
        $columns = $entry['columns'];

        // (۱) شناسه‌های جداول والد
        $parents = [];
        foreach ($columns as $column) {
            if (($column['type'] ?? '') !== 'foreign') {
                continue;
            }
            $target = (string) ($column['target'] ?? '');
            if ($target === '') {
                continue;
            }
            if (! array_key_exists($target, $this->ids)) {
                $this->ids[$target] = Schema::hasTable($target)
                    ? DB::table($target)->orderBy('id')->pluck('id')->all()
                    : [];
            }
            $parents[$column['name']] = $this->ids[$target];
        }

        // (۲) کلید خارجی اجباری بدون والد ⇒ درج ممکن نیست
        foreach ($columns as $column) {
            if (($column['type'] ?? '') !== 'foreign') {
                continue;
            }
            $required = empty($column['nullable']);
            $target = (string) ($column['target'] ?? '');

            if ($target === $table) {
                if ($required) {
                    $this->skipped[] = $table . ' (کلید خارجی خودارجاع اجباری است)';

                    return;
                }
                continue;
            }

            if ($required && empty($parents[$column['name']])) {
                $this->skipped[] = $table . ' (والد ' . ($target ?: '?') . ' رکوردی ندارد)';

                return;
            }
        }

        // (۳) ساخت ردیف‌ها
        $count = max(1, (int) ($entry['rows'] ?? DemoDataSpec::ROWS));
        $rows = [];
        for ($index = 1; $index <= $count; $index++) {
            $row = [];
            foreach ($columns as $column) {
                $value = $this->valueFor($column, $index, $count, $table, $parents);
                if ($value === self::SKIP) {
                    continue;
                }
                $row[$column['name']] = $value;
            }

            if (! empty($entry['timestamps'])) {
                $stamp = $this->stampAt($index, $count);
                $row['created_at'] = $stamp;
                $row['updated_at'] = $stamp;
            }

            $rows[] = $row;
        }

        if ($rows === []) {
            return;
        }

        // جدول خودارجاع (مثل سلسله‌مراتب حساب‌ها) باید ردیف‌به‌ردیف درج شود تا
        // فرزندان بتوانند به شناسه والدِ همان جدول ارجاع دهند.
        $selfReferencing = false;
        foreach ($columns as $column) {
            if (($column['type'] ?? '') === 'foreign' && ($column['target'] ?? '') === $table) {
                $selfReferencing = true;
                break;
            }
        }

        if ($selfReferencing) {
            $this->ids[$table] = DB::table($table)->orderBy('id')->pluck('id')->all();
            foreach ($rows as $row) {
                foreach ($columns as $column) {
                    if (($column['type'] ?? '') !== 'foreign' || ($column['target'] ?? '') !== $table) {
                        continue;
                    }
                    if (! array_key_exists($column['name'], $row)) {
                        continue;
                    }
                    // نخستین ردیف والد ندارد؛ ردیف‌های بعدی به یکی از ردیف‌های
                    // درج‌شده همان جدول ارجاع می‌دهند (سلسله‌مراتب تصادفی).
                    $row[$column['name']] = $this->ids[$table] === []
                        ? null
                        : $this->pick($this->ids[$table]);
                }
                $id = DB::table($table)->insertGetId($row);
                $this->ids[$table][] = $id;
            }
        } else {
            foreach (array_chunk($rows, 200) as $chunk) {
                DB::table($table)->insert($chunk);
            }
            $this->ids[$table] = DB::table($table)->orderBy('id')->pluck('id')->all();
        }
        $this->inserted += count($rows);
        $this->seededTables++;
    }

    /**
     * مقدار یک ستون برای ردیف شماره $index.
     *
     * @param  array<string, mixed>  $column
     * @param  array<string, array<int, int|string>>  $parents
     */
    private function valueFor(array $column, int $index, int $count, string $table, array $parents): mixed
    {
        $name = (string) $column['name'];
        $type = (string) ($column['type'] ?? 'string');
        $nullable = ! empty($column['nullable']);

        if ($nullable && $this->next01() < 0.12) {
            return null;
        }

        if ($type === 'foreign') {
            $candidates = $parents[$name] ?? [];
            if ($candidates === []) {
                // خودارجعی یا والد ناموجود: اگر ممکن است null، درج نکن
                return $nullable ? null : self::SKIP;
            }
            if (($column['target'] ?? '') === $table) {
                // مقدار نهایی در مسیر درج ردیف‌به‌ردیف تعیین می‌شود
                return null;
            }

            return $this->pick($candidates);
        }

        if ($type === 'enum') {
            $options = (array) ($column['options'] ?? []);

            return $options === [] ? null : $this->pick($options);
        }

        if (array_key_exists($name, $this->settingValues())) {
            return $this->settingValues()[$name];
        }

        return match ($type) {
            'boolean' => $this->next01() < 0.72,
            'integer', 'bigint' => $this->integerValue($name, $index),
            'decimal' => $this->decimalValue($column, $name, $index, $count),
            'date' => $this->dateAt($index, $count),
            'datetime' => $this->stampAt($index, $count),
            'time' => sprintf('%02d:%02d:00', (int) $this->between(6, 22), (int) $this->between(0, 59)),
            'json' => json_encode(
                ['demo' => true, 'row' => $index, 'source' => 'DemoHistorySeeder'],
                JSON_UNESCAPED_UNICODE
            ),
            'uuid' => $this->uuid($index),
            'text' => $this->paragraph($index),
            default => $this->stringValue($name, $table, $index, ! empty($column['unique'])),
        };
    }

    /** @return array<string, string> */
    private function settingValues(): array
    {
        static $values = null;

        if ($values === null) {
            $values = [
                'currency' => DemoDataSpec::CURRENCY,
                'currency_code' => DemoDataSpec::CURRENCY,
            ];
        }

        return $values;
    }

    private function stringValue(string $name, string $table, int $index, bool $unique): string
    {
        $lower = strtolower($name);

        if ($lower === 'code' || str_ends_with($lower, '_code') || str_contains($lower, 'number')) {
            return $unique || $lower === 'code'
                ? sprintf('DEMO-%s-%05d', strtoupper(substr(preg_replace('/[^a-z]/', '', $table) ?: 'TBL', 0, 3)), $index)
                : (string) (1000 + $index);
        }

        if (str_contains($lower, 'email') || str_contains($lower, 'mail')) {
            return sprintf('demo%d@%s.test', $index, preg_replace('/[^a-z]/', '', $table) ?: 'erp');
        }

        if (str_contains($lower, 'mobile') || str_contains($lower, 'phone') || str_contains($lower, 'tel')) {
            return '0' . (str_starts_with($lower, 'mobile') || $lower === 'phone_number' ? '912' : '21')
                . str_pad((string) (($index * 7919) % 100000000), 8, '0', STR_PAD_LEFT);
        }

        if (str_contains($lower, 'national') || str_contains($lower, 'economic')) {
            return str_pad((string) ((($index * 2654435761) % 10000000000)), 10, '0', STR_PAD_LEFT);
        }

        if (str_contains($lower, 'password')) {
            return password_hash('demo-password', PASSWORD_BCRYPT);
        }

        if (str_contains($lower, 'slug') || str_contains($lower, 'key')) {
            return sprintf('%s-%d', preg_replace('/[^a-z0-9]+/', '-', $table), $index);
        }

        if (str_contains($lower, 'address') || str_contains($lower, 'city') || str_contains($lower, 'province')) {
            return $this->pick(self::PLACES) . ($unique ? ' — ' . $index : '');
        }

        if (str_contains($lower, 'name') && str_contains($lower, 'person')) {
            return $this->pick(self::PEOPLE);
        }

        $text = $this->pick(self::NOUNS) . ' ' . $this->pick(self::ADJECTIVES);

        return $unique ? $text . ' ' . $index : $text;
    }

    private function integerValue(string $name, int $index): int
    {
        $lower = strtolower($name);

        if (str_contains($lower, 'year')) {
            return 1400 + ($index % 6);
        }
        if (str_contains($lower, 'month')) {
            return 1 + ($index % 12);
        }
        if (str_contains($lower, 'day')) {
            return 1 + ($index % 28);
        }
        if (str_contains($lower, 'shift')) {
            return 1 + ($index % 3);
        }
        if (preg_match('/(qty|quantity|count|number|num|persons|hours|minutes|level|priority|seq)/', $lower)) {
            return (int) round($this->between(1, 240));
        }

        return (int) round($this->between(1, 1000));
    }

    /**
     * @param  array<string, mixed>  $column
     */
    private function decimalValue(array $column, string $name, int $index, int $count): float
    {
        $kind = $column['series'] ?? null;
        if (is_string($kind) && $kind !== '') {
            return $this->series(
                $kind,
                (float) ($column['series_base'] ?? 100.0),
                (float) ($column['series_trend'] ?? 0.1),
                (float) ($column['series_spike'] ?? 1.5),
                $index,
                $count
            );
        }

        $lower = strtolower($name);
        $max = preg_match('/(rate|ratio|percent|score|index|coefficient|factor)/', $lower)
            ? 100.0
            : (preg_match('/(amount|total|price|cost|value|salary|wage|budget|balance)/', $lower) ? 95000000.0 : 10000.0);

        return round($this->between($max / 100, $max), 2);
    }

    /**
     * سری زمانی با روند + فصلانگی شمسی + نویز + ناهنجاری عمدی.
     */
    private function series(string $kind, float $base, float $trend, float $spike, int $index, int $count): float
    {
        $progress = ($index - 1) / max(1, $count - 1);
        $month = (int) floor($progress * DemoDataSpec::MONTHS);
        $seasonal = DemoDataSpec::SEASONAL[$month % 12] ?? 1.0;
        $noise = 0.94 + $this->next01() * 0.12;

        $value = $base * (1 + $progress * $trend) * $seasonal * $noise;

        // ناهنجاری عمدی: هر ۱۷ رکورد یک جهش (برای موتورهای تشخیص ناهنجاری/SPC)
        if ($index % 17 === 0) {
            $value *= $spike;
        }

        // تخریب تدریجی در انتهای بازه (برای موتور قابلیت اطمینان/RUL)
        if ($kind === 'vibration' && $progress > 0.75) {
            $value *= 1 + ($progress - 0.75) * 2.4;
        }

        return round(max($value, 0), 2);
    }

    private function dateAt(int $index, int $count): string
    {
        return substr($this->stampAt($index, $count), 0, 10);
    }

    private function stampAt(int $index, int $count): string
    {
        $totalDays = DemoDataSpec::MONTHS * 30;
        $progress = $count > 1 ? ($index - 1) / ($count - 1) : 1.0;
        $day = (int) floor($progress * $totalDays);

        return Carbon::now()
            ->subMonths(DemoDataSpec::MONTHS)
            ->startOfDay()
            ->addDays($day)
            ->addMinutes((int) $this->between(0, 1439))
            ->format('Y-m-d H:i:s');
    }

    private function uuid(int $index): string
    {
        $hex = str_pad(dechex(($index * 2654435761) % 4294967295), 8, '0', STR_PAD_LEFT)
            . str_pad(dechex((int) ($this->next01() * 65535)), 4, '0', STR_PAD_LEFT);

        return sprintf(
            '%s-%s-4%s-%s-%s%07d',
            substr($hex, 0, 8),
            substr($hex, 8, 4),
            substr($hex, 4, 3),
            substr($hex, 10, 3),
            substr($hex, 13, 3),
            $index
        );
    }

    private function paragraph(int $index): string
    {
        return sprintf(
            '%s %s — رکورد نمونه شماره %d برای %s (ساخته‌شده توسط DemoHistorySeeder).',
            $this->pick(self::NOUNS),
            $this->pick(self::SENTENCES),
            $index,
            DemoDataSpec::COMPANY
        );
    }

    /* ------------------------------------------------------------- تصادفی */

    /** عدد شبه‌تصادفی در بازه [0,1] با بذر ثابت (LCG) */
    private function next01(): float
    {
        $this->state = (int) (($this->state * 1103515245 + 12345) & 0x7FFFFFFF);

        return $this->state / 0x7FFFFFFF;
    }

    private function between(float $min, float $max): float
    {
        return $min + $this->next01() * ($max - $min);
    }

    /**
     * @template T
     *
     * @param  array<int, T>  $items
     * @return T
     */
    private function pick(array $items): mixed
    {
        if ($items === []) {
            return null;
        }

        $keys = array_keys($items);

        return $items[$keys[(int) floor($this->next01() * count($keys)) % count($keys)]];
    }

    /* ---------------------------------------------------------- متن فارسی */

    private const NOUNS = [
        'بازرسی', 'سفارش', 'برنامه تولید', 'گزارش', 'درخواست', 'قرارداد', 'فاکتور', 'حواله',
        'رسید', 'سند', 'پرونده', 'نمونه', 'اندازه‌گیری', 'کالیبراسیون', 'تعمیر', 'سرویس',
        'محموله', 'پارت تولید', 'دوره آموزشی', 'ارزیابی', 'ممیزی', 'هشدار', 'شاخص', 'بودجه',
    ];

    private const ADJECTIVES = [
        'خط یک', 'خط دو', 'شیفت صبح', 'شیفت عصر', 'شیفت شب', 'انبار مرکزی', 'انبار ملزومات',
        'کارگاه مونتاژ', 'واحد کیفیت', 'واحد نت', 'واحد تدارکات', 'فروش داخلی', 'صادرات',
        'محصول درجه یک', 'محصول درجه دو', 'ماده اولیه', 'قطعه نیمه‌ساخته', 'بازیافتی',
    ];

    private const SENTENCES = [
        'با مقادیر سازگار با بازه تاریخچه درج شد',
        'برای نمایش روند و فصلانگی تولید شد',
        'دارای الگوی قابل تشخیص برای موتورهای هوش مصنوعی',
        'در بازه زمانی تعیین‌شده پخش شده است',
        'برای آموزش کاربران آماده شده است',
    ];

    private const PLACES = [
        'تهران، خیابان صنعت', 'اصفهان، شهرک صنعتی مبارکه', 'البرز، شهرک صنعتی اشتهارد',
        'خراسان رضوی، شهرک صنعتی توس', 'فارس، شهرک صنعتی شیراز', 'خوزستان، شهرک صنعتی اهواز',
        'قزوین، شهرک صنعتی البرز', 'مرکزی، شهرک صنعتی اراک', 'یزد، شهرک صنعتی یزد',
        'آذربایجان شرقی، شهرک صنعتی تبریز',
    ];

    private const PEOPLE = [
        'علی محمدی', 'زهرا کریمی', 'رضا احمدی', 'مریم حسینی', 'حسن رضایی', 'فاطمه موسوی',
        'امیر صادقی', 'سارا نوری', 'مهدی جعفری', 'نگار صالحی', 'کاظم رحیمی', 'الهام شریفی',
    ];
}
'''

ENTRY_TEMPLATE = r'''<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

/**
 * داده نمونه برای محیط نمایش و آموزش
 *
 * دو لایه:
 *   ۱. seeder هر ماژول — فقط جداول بدون کلید خارجی اجباری (داده پایه)
 *   ۲. Demo\DemoHistorySeeder — تاریخچه سازگار @@months@@ ماهه با کلید خارجی واقعی
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

        $this->call([
            \Database\Seeders\Demo\DemoHistorySeeder::class,
        ]);

        $this->command?->warn('داده نمونه درج شد — در محیط تولید استفاده نکنید.');
    }
}
'''


# --------------------------------------------------------------------------- #
# انتشار PHP
# --------------------------------------------------------------------------- #
def _emit_columns(columns: list[dict[str, Any]], indent: str) -> str:
    lines: list[str] = []
    for column in columns:
        parts = [f"'name' => {php_value(column['name'])}", f"'type' => {php_value(column['type'])}"]
        if column.get("nullable"):
            parts.append("'nullable' => true")
        if column.get("unique"):
            parts.append("'unique' => true")
        if column.get("options"):
            parts.append("'options' => [" + ", ".join(php_value(o) for o in column["options"]) + "]")
        if column.get("target"):
            parts.append(f"'target' => {php_value(column['target'])}")
        if column.get("series"):
            parts.append(f"'series' => {php_value(column['series'])}")
            parts.append(f"'series_base' => {column['series_base']}")
            parts.append(f"'series_trend' => {column['series_trend']}")
            parts.append(f"'series_spike' => {column['series_spike']}")
        lines.append(f"{indent}['label' => {php_value(column.get('label') or '')}, " + ", ".join(parts) + "],")
    return "\n".join(lines)


def _emit_tables(tables: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for entry in tables:
        blocks.append(
            "            [\n"
            f"                'table' => {php_value(entry['table'])},\n"
            f"                'label' => {php_value(entry['label'])},\n"
            f"                'module' => {php_value(entry['module'])},\n"
            f"                'rows' => {entry['rows']},\n"
            f"                'timestamps' => {'true' if entry['timestamps'] else 'false'},\n"
            "                'columns' => [\n"
            f"{_emit_columns(entry['columns'], ' ' * 20)}\n"
            "                ],\n"
            "            ],"
        )
    return "\n".join(blocks)


def generate_demo_data(
    package: Package,
    *,
    settings: dict[str, Any],
    entities: list[dict[str, Any]],
    modules: list[dict[str, Any]],
    context: dict[str, Any],
    module_seeders: list[str] | None = None,
) -> dict[str, Any]:
    """ساخت فایل‌های داده نمونه و برگرداندن آمار آن‌ها."""
    months = int(settings.get("demo_data_months", 18) or 18)
    rows = int(settings.get("demo_data_rows", 12) or 12)
    seed = int(settings.get("demo_data_seed", 20260101) or 20260101)

    tables, skipped, config = build_demo_spec(
        entities,
        months=months,
        rows=rows,
        seed=seed,
        company_name=str(settings.get("company_name") or context.get("app_name_fa") or "کارخانه"),
        currency=str(settings.get("currency", "IRR")),
        multi_tenant=bool(settings.get("multi_tenant", False)),
    )

    total_rows = sum(entry["rows"] for entry in tables)
    series_columns = sum(
        1
        for entry in tables
        for column in entry["columns"]
        if column.get("series")
    )

    package.add_rendered(
        "backend/database/seeders/Demo/DemoDataSpec.php",
        SPEC_TEMPLATE,
        area="laravel-seeders",
        app_name_fa=context.get("app_name_fa", "ERP کارخانه"),
        generator=APP_NAME_FA,
        months=config["months"],
        rows=config["rows"],
        seed=config["seed"],
        company=php_value(config["company_name"]),
        currency=php_value(config["currency"]),
        seasonal=", ".join(str(value) for value in SEASONAL_JALALI),
        skipped_count=len(skipped),
        skipped_note=(
            "، ".join(table for table, _reason in skipped[:6])
            + ("…" if len(skipped) > 6 else "")
            or "—"
        ),
        tables=_emit_tables(tables) or "            // جدول قابل درج نیست",
    )

    package.add_rendered(
        "backend/database/seeders/Demo/DemoHistorySeeder.php",
        SEEDER_TEMPLATE,
        area="laravel-seeders",
        months=config["months"],
        seed=config["seed"],
        skip_marker="__demo_skip__",
    )

    seeders = module_seeders or [
        f"{module['seeder_class']}" for module in modules if module.get("seeder_class")
    ]
    if seeders:
        lines = "\n".join(f"            {name}::class," for name in seeders)
    else:
        lines = "            // seeder ماژولی تعریف نشده است"

    package.add_rendered(
        "backend/database/seeders/DemoDataSeeder.php",
        ENTRY_TEMPLATE,
        area="laravel-seeders",
        months=config["months"],
        module_seeders=lines,
    )

    return {
        "tables": len(tables),
        "rows": total_rows,
        "series_columns": series_columns,
        "skipped": skipped,
        "months": config["months"],
    }
