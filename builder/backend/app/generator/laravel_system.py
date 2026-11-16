# -*- coding: utf-8 -*-
"""
تولید لایه سیستمی لاراول
=========================
کلاس‌های پشتیبانی (تاریخ شمسی، متن فارسی، کلاینت AvalAI و سرویس AI)،
میان‌افزارها، ارائه‌دهنده‌ها، کنترلرهای سامانه (احراز هویت، داشبورد،
قابلیت‌ها، هوش مصنوعی) و دستورهای کنسول.
"""

from __future__ import annotations

import json
from typing import Any

from .writers import Package, php_array, php_value, render

# --------------------------------------------------------------------------- #
# کلاس‌های پشتیبانی
# --------------------------------------------------------------------------- #
JALALI_CLASS = r"""<?php

namespace App\Support;

use DateTimeImmutable;
use DateTimeInterface;
use DateTimeZone;
use Throwable;

/**
 * تبدیل تاریخ میلادی به شمسی و برعکس — بدون وابستگی خارجی
 *
 * الگوریتم: jalaali (نسخه اصلاح‌شده کاظم کوکبی / jdf.ir)
 * همه تاریخ‌های سامانه در پایگاه داده میلادی ذخیره و در لایه نمایش شمسی می‌شوند.
 */
class Jalali
{
    public const MONTH_NAMES = [
        1 => 'فروردین', 2 => 'اردیبهشت', 3 => 'خرداد', 4 => 'تیر',
        5 => 'مرداد', 6 => 'شهریور', 7 => 'مهر', 8 => 'آبان',
        9 => 'آذر', 10 => 'دی', 11 => 'بهمن', 12 => 'اسفند',
    ];

    public const WEEK_DAY_NAMES = [
        'Saturday' => 'شنبه', 'Sunday' => 'یکشنبه', 'Monday' => 'دوشنبه',
        'Tuesday' => 'سه‌شنبه', 'Wednesday' => 'چهارشنبه',
        'Thursday' => 'پنجشنبه', 'Friday' => 'جمعه',
    ];

    /** تبدیل میلادی به شمسی */
    public static function toJalali(int $gy, int $gm, int $gd): array
    {
        $gDaysInMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
        $gy2 = ($gm > 2) ? ($gy + 1) : $gy;

        $days = 355666 + (365 * $gy) + intdiv($gy2 + 3, 4) - intdiv($gy2 + 99, 100)
            + intdiv($gy2 + 399, 400) + $gd + $gDaysInMonth[$gm - 1];

        $jy = -1595 + (33 * intdiv($days, 12053));
        $days %= 12053;

        $jy += 4 * intdiv($days, 1461);
        $days %= 1461;

        if ($days > 365) {
            $jy += intdiv($days - 1, 365);
            $days = ($days - 1) % 365;
        }

        if ($days < 186) {
            $jm = 1 + intdiv($days, 31);
            $jd = 1 + ($days % 31);
        } else {
            $jm = 7 + intdiv($days - 186, 30);
            $jd = 1 + (($days - 186) % 30);
        }

        return ['year' => $jy, 'month' => $jm, 'day' => $jd];
    }

    /** تبدیل شمسی به میلادی */
    public static function toGregorian(int $jy, int $jm, int $jd): array
    {
        $jy += 1595;

        $days = -355668 + (365 * $jy) + (intdiv($jy, 33) * 8) + intdiv((($jy % 33) + 3), 4)
            + $jd + (($jm < 7) ? ($jm - 1) * 31 : (($jm - 7) * 30) + 186);

        $gy = 400 * intdiv($days, 146097);
        $days %= 146097;

        if ($days > 36524) {
            $gy += 100 * intdiv(--$days, 36524);
            $days %= 36524;
            if ($days >= 365) {
                $days++;
            }
        }

        $gy += 4 * intdiv($days, 1461);
        $days %= 1461;

        if ($days > 365) {
            $gy += intdiv($days - 1, 365);
            $days = ($days - 1) % 365;
        }

        $gd = $days + 1;

        $isLeap = ($gy % 4 === 0 && $gy % 100 !== 0) || ($gy % 400 === 0);
        $gDaysInMonth = [0, 31, $isLeap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

        $gm = 0;
        for ($i = 1; $i <= 12; $i++) {
            if ($gd <= $gDaysInMonth[$i]) {
                $gm = $i;
                break;
            }
            $gd -= $gDaysInMonth[$i];
        }

        return ['year' => $gy, 'month' => $gm, 'day' => $gd];
    }

    /** فرمت «۱۴۰۵/۰۱/۰۱» یا «۱۴۰۵/۰۱/۰۱ ۱۰:۲۰» */
    public static function format(mixed $value, bool $withTime = false, string $separator = '/'): string
    {
        $date = self::parse($value);
        if ($date === null) {
            return '';
        }

        $j = self::toJalali((int) $date->format('Y'), (int) $date->format('n'), (int) $date->format('j'));
        $out = sprintf('%04d%s%02d%s%02d', $j['year'], $separator, $j['month'], $separator, $j['day']);

        if ($withTime) {
            $out .= ' ' . $date->format('H:i');
        }

        return $out;
    }

    /** فرمت بلند فارسی: «شنبه ۱ فروردین ۱۴۰۵» */
    public static function formatLong(mixed $value): string
    {
        $date = self::parse($value);
        if ($date === null) {
            return '';
        }

        $j = self::toJalali((int) $date->format('Y'), (int) $date->format('n'), (int) $date->format('j'));

        return sprintf(
            '%s %d %s %d',
            self::WEEK_DAY_NAMES[$date->format('l')] ?? $date->format('l'),
            $j['day'],
            self::MONTH_NAMES[$j['month']] ?? '',
            $j['year']
        );
    }

    /** نام ماه شمسی */
    public static function monthName(int $month): string
    {
        return self::MONTH_NAMES[$month] ?? '';
    }

    /** تبدیل رشته/آبجکت تاریخ به DateTimeImmutable در منطقه زمانی سامانه */
    public static function parse(mixed $value): ?DateTimeImmutable
    {
        if ($value === null || $value === '') {
            return null;
        }

        $timezone = new DateTimeZone(config('app.timezone', 'Asia/Tehran'));

        try {
            if ($value instanceof DateTimeInterface) {
                return DateTimeImmutable::createFromInterface($value)->setTimezone($timezone);
            }

            if (is_numeric($value)) {
                return (new DateTimeImmutable('@' . (int) $value))->setTimezone($timezone);
            }

            return new DateTimeImmutable((string) $value, $timezone);
        } catch (Throwable) {
            return null;
        }
    }

    /** تبدیل رشته شمسی «1405-01-01» به میلادی */
    public static function parseJalali(string $jalaliDate): ?DateTimeImmutable
    {
        $normalized = PersianText::toLatinDigits(trim($jalaliDate));
        $parts = preg_split('/[\/\-\s]+/', $normalized) ?: [];

        if (count($parts) < 3) {
            return null;
        }

        [$jy, $jm, $jd] = [(int) $parts[0], (int) $parts[1], (int) $parts[2]];
        if ($jy < 1300 || $jy > 1500 || $jm < 1 || $jm > 12 || $jd < 1 || $jd > 31) {
            return null;
        }

        $g = self::toGregorian($jy, $jm, $jd);

        try {
            return new DateTimeImmutable(sprintf(
                '%04d-%02d-%02d',
                $g['year'],
                $g['month'],
                $g['day']
            ), new DateTimeZone(config('app.timezone', 'Asia/Tehran')));
        } catch (Throwable) {
            return null;
        }
    }

    /** شماره روز سال شمسی (برای محاسبات دوره‌ای) */
    public static function dayOfYear(mixed $value): int
    {
        $date = self::parse($value);
        if ($date === null) {
            return 0;
        }

        $j = self::toJalali((int) $date->format('Y'), (int) $date->format('n'), (int) $date->format('j'));

        return ($j['month'] <= 6)
            ? (($j['month'] - 1) * 31) + $j['day']
            : ((($j['month'] - 7) * 30) + 186) + $j['day'];
    }

    /** تعداد روزهای سال شمسی (۳۶۵ یا ۳۶۶) */
    public static function yearLength(int $jy): int
    {
        $leap = [1, 5, 9, 13, 17, 22, 26, 30];

        return in_array($jy % 33, $leap, true) ? 366 : 365;
    }

    /** آغاز سال مالی شمسی به صورت میلادی */
    public static function fiscalYearStart(int $jy, int $startMonth = 1): DateTimeImmutable
    {
        $g = self::toGregorian($jy, $startMonth, 1);

        return new DateTimeImmutable(sprintf('%04d-%02d-01', $g['year'], $g['month']));
    }
}
"""

PERSIAN_TEXT_CLASS = r"""<?php

namespace App\Support;

/**
 * نرمال‌سازی متن و ارقام فارسی
 *
 * ورودی‌های کاربر معمولاً با ارقام فارسی/عربی، «ي» و «ك» عربی
 * و جداکننده هزارگان ارسال می‌شوند؛ این کلاس آن‌ها را یکدست می‌کند.
 */
class PersianText
{
    private const PERSIAN_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    private const ARABIC_DIGITS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    private const LATIN_DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];

    /** تبدیل ارقام فارسی و عربی به لاتین */
    public static function toLatinDigits(mixed $value): string
    {
        $text = (string) $value;
        $text = str_replace(self::PERSIAN_DIGITS, self::LATIN_DIGITS, $text);

        return str_replace(self::ARABIC_DIGITS, self::LATIN_DIGITS, $text);
    }

    /** تبدیل ارقام لاتین به فارسی (برای نمایش) */
    public static function toPersianDigits(mixed $value): string
    {
        return str_replace(self::LATIN_DIGITS, self::PERSIAN_DIGITS, self::toLatinDigits($value));
    }

    /** یکدست‌سازی «ي» و «ك» عربی و حذف نویزهای نیم‌فاصله */
    public static function normalize(mixed $value): string
    {
        $text = (string) $value;
        $text = str_replace(['ي', 'ى'], 'ی', $text);
        $text = str_replace(['ك', 'ڪ'], 'ک', $text);
        $text = str_replace(["\u{200C}\u{200C}", "\u{200F}", "\u{200E}"], "\u{200C}", $text);
        $text = str_replace(['ة'], 'ه', $text);
        $text = str_replace(['‏', '‎'], '', $text);

        return trim(preg_replace('/[ \t]+/u', ' ', $text) ?? $text);
    }

    /** تبدیل ورودی عددی فارسی (با جداکننده هزارگان و درصد) به عدد لاتین */
    public static function toNumber(mixed $value): int|float|null
    {
        if ($value === null || $value === '') {
            return null;
        }

        if (is_int($value) || is_float($value)) {
            return $value;
        }

        $text = self::toLatinDigits($value);
        $text = str_replace([',', '،', ' ', "\u{00A0}", '﷼', 'ریال', 'تومان'], '', $text);

        if ($text === '' || $text === '-') {
            return null;
        }

        if (!is_numeric($text)) {
            return null;
        }

        return str_contains($text, '.') ? (float) $text : (int) $text;
    }

    /** قالب‌بندی مبلغ به ریال با جداکننده هزارگان و ارقام فارسی */
    public static function money(mixed $amount, bool $persianDigits = true, ?string $suffix = null): string
    {
        $number = self::toNumber($amount) ?? 0;
        $formatted = number_format((float) $number, 0, '.', ',');
        $suffix = $suffix ?? config('erp.localization.currency_label', 'ریال');

        $out = trim($formatted . ' ' . $suffix);

        return $persianDigits ? self::toPersianDigits($out) : $out;
    }

    /** قالب‌بندی عدد با ارقام فارسی */
    public static function number(mixed $value, int $decimals = 0, bool $persianDigits = true): string
    {
        $number = self::toNumber($value) ?? 0;
        $formatted = number_format((float) $number, $decimals, '.', ',');

        return $persianDigits ? self::toPersianDigits($formatted) : $formatted;
    }

    /** ساخت کد یکتا با پیشوند و تاریخ شمسی: WO-14050101-0001 */
    public static function documentNumber(string $prefix, int|string $sequence, string $separator = '-'): string
    {
        $j = Jalali::toJalali(
            (int) now()->format('Y'),
            (int) now()->format('n'),
            (int) now()->format('j')
        );

        return sprintf(
            '%s%s%02d%02d%02d%s%04d',
            strtoupper($prefix),
            $separator,
            $j['year'] % 1000,
            $j['month'],
            $j['day'],
            $separator,
            (int) $sequence
        );
    }

    /** خلاصه‌سازی متن برای پیش‌نمایش */
    public static function excerpt(mixed $value, int $length = 120): string
    {
        $text = self::normalize($value);

        if (mb_strlen($text) <= $length) {
            return $text;
        }

        return mb_substr($text, 0, $length) . '…';
    }
}
"""

AVALAI_CLIENT = r"""<?php

namespace App\Support;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Throwable;

/**
 * کلاینت AvalAI — سازگار با قالب OpenAI Chat Completions
 *
 * این لایه کاملاً اختیاری است: اگر کلید API تنظیم نشده باشد یا خطایی رخ دهد،
 * مقدار null برگردانده می‌شود و فراخوان باید مسیر جایگزین (قاعده‌محور) را اجرا کند.
 *
 * کاربرد در ERP کارخانه‌ای:
 *  - چت‌بات راهنمای اپراتور و مدیر
 *  - خلاصه‌سازی گزارش شیفت، عدم انطباق‌ها و رخدادهای نت
 *  - استخراج بند و تعهد از متن قرارداد
 *  - تولید بینش متنی روی خروجی داشبورد
 *  - طبقه‌بندی شرح درخواست‌های خدمات و تیکت‌ها
 */
class AvalAiClient
{
    public function __construct(
        protected ?string $apiKey = null,
        protected ?string $baseUrl = null,
        protected ?string $model = null,
    ) {
        $this->apiKey = $apiKey ?: config('services.avalai.key');
        $this->baseUrl = rtrim($baseUrl ?: config('services.avalai.base_url', 'https://api.avalai.ir/v1'), '/');
        $this->model = $model ?: config('services.avalai.model', 'gpt-4o-mini');
    }

    public function isEnabled(): bool
    {
        return filled($this->apiKey);
    }

    /** گفت‌وگوی ساده با حافظه مکالمه */
    public function chat(array $messages, array $options = []): ?string
    {
        if (!$this->isEnabled()) {
            return null;
        }

        $response = $this->request('chat/completions', array_merge([
            'model' => $this->model,
            'messages' => $messages,
            'temperature' => 0.2,
            'max_tokens' => (int) config('services.avalai.timeout') ? 1200 : 1200,
        ], $options));

        return $response['choices'][0]['message']['content'] ?? null;
    }

    /** پاسخ ساخت‌یافته JSON */
    public function json(string $prompt, string $system = '', array $options = []): ?array
    {
        $messages = [];
        if ($system !== '') {
            $messages[] = ['role' => 'system', 'content' => $system];
        }
        $messages[] = ['role' => 'user', 'content' => $prompt];

        $text = $this->chat($messages, array_merge(['response_format' => ['type' => 'json_object']], $options));

        if ($text === null) {
            return null;
        }

        $decoded = json_decode($this->stripCodeFence($text), true);

        return is_array($decoded) ? $decoded : null;
    }

    /** تولید متن: گزارش، نامه، توضیح */
    public function complete(string $prompt, array $options = []): ?string
    {
        return $this->chat([['role' => 'user', 'content' => $prompt]], $options);
    }

    /** تولید امبدینگ برای جست‌وجوی معنایی */
    public function embeddings(array $inputs, ?string $model = null): ?array
    {
        if (!$this->isEnabled()) {
            return null;
        }

        $response = $this->request('embeddings', [
            'model' => $model ?: config('ai.embedding_model', 'text-embedding-3-small'),
            'input' => $inputs,
        ]);

        if (!isset($response['data']) || !is_array($response['data'])) {
            return null;
        }

        return array_map(static fn (array $row) => $row['embedding'] ?? [], $response['data']);
    }

    /** خلاصه‌سازی متن بلند با کش */
    public function summarize(string $text, int $maxLength = 400): ?string
    {
        $key = 'avalai:summary:' . md5($text . $maxLength);

        return Cache::remember($key, now()->addDay(), function () use ($text, $maxLength) {
            return $this->complete(sprintf(
                "متن زیر را در حداکثر %d کاراکتر، به فارسی روان و بدون حذف اطلاعات کلیدی خلاصه کن:\n\n%s",
                $maxLength,
                $text
            ));
        });
    }

    /** استخراج ساختار از متن آزاد (مثل بند قرارداد) */
    public function extract(string $text, array $schema): ?array
    {
        return $this->json(sprintf(
            "از متن زیر این فیلدها را استخراج کن و فقط JSON برگردان.\nفیلدها: %s\n\nمتن:\n%s",
            json_encode($schema, JSON_UNESCAPED_UNICODE),
            PersianText::excerpt($text, 6000)
        ), 'تو یک استخراج‌کننده اطلاعات ساخت‌یافته از متون فارسی صنعتی هستی.');
    }

    /** طبقه‌بندی متن در یکی از برچسب‌ها */
    public function classify(string $text, array $labels): ?string
    {
        $result = $this->json(sprintf(
            "متن را در یکی از این دسته‌ها طبقه‌بندی کن و فقط JSON با کلید label برگردان.\nدسته‌ها: %s\n\nمتن: %s",
            implode('، ', $labels),
            PersianText::excerpt($text, 2000)
        ));

        $label = $result['label'] ?? null;

        return is_string($label) && in_array($label, $labels, true) ? $label : null;
    }

    /** ارسال درخواست به AvalAI */
    protected function request(string $path, array $payload): array
    {
        try {
            $response = Http::withToken((string) $this->apiKey)
                ->acceptJson()
                ->timeout((int) config('services.avalai.timeout', 45))
                ->retry(2, 500, throw: false)
                ->post($this->baseUrl . '/' . ltrim($path, '/'), $payload);

            if ($response->failed()) {
                Log::channel(config('ai.log_channel', 'ai'))->warning('AvalAI request failed', [
                    'path' => $path,
                    'status' => $response->status(),
                    'body' => mb_substr($response->body(), 0, 400),
                ]);

                return [];
            }

            return $response->json() ?? [];
        } catch (Throwable $exception) {
            Log::channel(config('ai.log_channel', 'ai'))->error('AvalAI exception: ' . $exception->getMessage());

            return [];
        }
    }

    protected function stripCodeFence(string $text): string
    {
        $text = trim($text);

        if (str_starts_with($text, '```')) {
            $text = preg_replace('/^```(?:json)?\s*/i', '', $text) ?? $text;
            $text = preg_replace('/\s*```$/i', '', $text) ?? $text;
        }

        return trim($text);
    }
}
"""

AI_SERVICE_CLIENT = r"""<?php

namespace App\Support;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Throwable;

/**
 * کلاینت سرویس هوش مصنوعی (میکروسرویس پایتون — FastAPI)
 *
 * همه موتورهای پیش‌بینی، بهینه‌سازی، تشخیص ناهنجاری، بینایی ماشین و SPC
 * در سرویس پایتون اجرا می‌شوند؛ لاراول فقط داده را آماده و نتیجه را
 * ثبت/ارائه می‌کند. اگر سرویس در دسترس نبود، پاسخ fallback برگردانده
 * می‌شود تا هیچ فرآیند تولیدی متوقف نماند.
 */
class AiServiceClient
{
    public function __construct(
        protected ?string $baseUrl = null,
        protected int $timeout = 30,
    ) {
        $this->baseUrl = rtrim($baseUrl ?: config('services.ai_service.base_url', 'http://ai-service:8001'), '/');
        $this->timeout = (int) config('services.ai_service.timeout', $this->timeout);
    }

    public function isEnabled(): bool
    {
        return (bool) config('services.ai_service.enabled', true) && (bool) config('erp.ai.enabled', true);
    }

    /** فراخوانی عمومی یک اندپوینت AI */
    public function call(string $endpoint, array $payload = []): array
    {
        if (!$this->isEnabled()) {
            return $this->fallback($endpoint, $payload, 'سرویس هوش مصنوعی غیرفعال است');
        }

        try {
            $response = Http::acceptJson()
                ->timeout($this->timeout)
                ->withHeaders(['X-Module' => (string) ($payload['module_code'] ?? 'general')])
                ->post($this->baseUrl . '/' . ltrim($endpoint, '/'), $payload);

            if ($response->failed()) {
                return $this->fallback($endpoint, $payload, 'پاسخ ناموفق از سرویس AI: ' . $response->status());
            }

            $data = $response->json() ?? [];
            $this->logPrediction($endpoint, $payload, $data, true);

            return is_array($data) ? $data : ['ok' => true, 'result' => $data];
        } catch (Throwable $exception) {
            return $this->fallback($endpoint, $payload, $exception->getMessage());
        }
    }

    /** بررسی سلامت سرویس و فهرست مدل‌های آماده */
    public function health(): array
    {
        try {
            $response = Http::acceptJson()->timeout(5)->get($this->baseUrl . '/health');

            return $response->successful() ? ($response->json() ?? []) : ['ok' => false, 'status' => $response->status()];
        } catch (Throwable $exception) {
            return ['ok' => false, 'error' => $exception->getMessage()];
        }
    }

    /** آموزش/بازآموزی یک مدل به صورت ناهمگام */
    public function train(string $modelId, array $payload = []): array
    {
        return $this->call('ai/train', array_merge($payload, ['model_id' => $modelId]));
    }

    /** پاسخ جایگزین قاعده‌محور (بدون AI) */
    protected function fallback(string $endpoint, array $payload, string $reason): array
    {
        Log::channel(config('ai.log_channel', 'ai'))->info('AI fallback used', [
            'endpoint' => $endpoint,
            'reason' => $reason,
            'capability' => $payload['capability'] ?? null,
        ]);

        $this->logPrediction($endpoint, $payload, ['fallback' => true, 'reason' => $reason], false);

        return [
            'ok' => false,
            'fallback' => true,
            'endpoint' => $endpoint,
            'reason' => $reason,
            'capability' => $payload['capability'] ?? null,
            'suggestion' => 'مقدار را بر اساس قواعد کسب‌وکاری تعیین کنید.',
        ];
    }

    /** ثبت نتیجه پیش‌بینی برای پایش مدل (MLOps) */
    protected function logPrediction(string $endpoint, array $payload, array $result, bool $succeeded): void
    {
        if (!config('ai.log_predictions', true)) {
            return;
        }

        try {
            if (!class_exists(\App\Models\Ai\AiPredictionLog::class)) {
                return;
            }

            \App\Models\Ai\AiPredictionLog::create([
                'model_id' => $payload['model_id'] ?? null,
                'model_code' => $payload['model_id'] ?? null,
                'capability_code' => $payload['feature_flag'] ?? null,
                'endpoint' => $endpoint,
                'input_payload' => $payload,
                'output_payload' => $result,
                'is_fallback' => !$succeeded,
                'status' => $succeeded ? 'success' : 'fallback',
                'latency_ms' => null,
                'created_at' => now(),
            ]);
        } catch (Throwable $exception) {
            Log::channel(config('ai.log_channel', 'ai'))->debug('AI prediction log skipped: ' . $exception->getMessage());
        }
    }
}
"""

ACTIVITY_LOGGER = r"""<?php

namespace App\Support;

use App\Models\System\AuditEvent;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Request;
use Throwable;

/**
 * ثبت رویداد ممیزی (Audit Log) — جایگزین داخلی پکیج‌های فعالیت
 *
 * استفاده:
 *   activity()->causedBy($user)->performedOn($model)->withProperties([...])->log('update');
 */
class ActivityLogger
{
    protected ?Model $subject = null;
    protected ?Model $causer = null;
    protected array $properties = [];
    protected string $moduleCode = '';

    public function causedBy(?Model $causer): self
    {
        $this->causer = $causer;

        return $this;
    }

    public function performedOn(?Model $subject): self
    {
        $this->subject = $subject;

        return $this;
    }

    public function withProperties(array $properties): self
    {
        $this->properties = array_merge($this->properties, $properties);

        return $this;
    }

    public function inModule(string $moduleCode): self
    {
        $this->moduleCode = $moduleCode;

        return $this;
    }

    public function log(string $action): ?AuditEvent
    {
        try {
            $causer = $this->causer ?? (auth()->user() instanceof Model ? auth()->user() : null);

            return AuditEvent::create([
                'code' => PersianText::documentNumber('AUD', AuditEvent::max('id') + 1),
                'user_id' => $causer?->getKey(),
                'action' => $action,
                'entity_type' => $this->subject ? get_class($this->subject) : null,
                'entity_id' => $this->subject?->getKey(),
                'module_code' => $this->moduleCode ?: ($this->properties['module'] ?? ''),
                'old_values' => $this->properties['old'] ?? null,
                'new_values' => $this->properties ?: null,
                'ip_address' => Request::ip(),
                'user_agent' => mb_substr((string) Request::userAgent(), 0, 250),
                'occurred_at' => now(),
            ]);
        } catch (Throwable $exception) {
            Log::channel('audit')->warning('ثبت رویداد ممیزی ناموفق بود: ' . $exception->getMessage());

            return null;
        }
    }
}
"""

HELPERS = r"""<?php

use App\Support\ActivityLogger;
use App\Support\Jalali;
use App\Support\PersianText;

if (!function_exists('activity')) {
    /** شروع یک رویداد ممیزی */
    function activity(): ActivityLogger
    {
        return new ActivityLogger();
    }
}

if (!function_exists('jalali')) {
    /** فرمت تاریخ شمسی */
    function jalali(mixed $date, bool $withTime = false): string
    {
        return Jalali::format($date, $withTime);
    }
}

if (!function_exists('jalali_long')) {
    /** فرمت بلند تاریخ شمسی */
    function jalali_long(mixed $date): string
    {
        return Jalali::formatLong($date);
    }
}

if (!function_exists('money_fa')) {
    /** قالب‌بندی مبلغ با ارقام فارسی */
    function money_fa(mixed $amount, ?string $suffix = null): string
    {
        return PersianText::money($amount, true, $suffix);
    }
}

if (!function_exists('erp_feature_enabled')) {
    /** بررسی فعال بودن یک قابلیت کاتالوگ در این استقرار */
    function erp_feature_enabled(string $code): bool
    {
        $features = config('features.items', []);

        return isset($features[$code]) && (bool) ($features[$code]['enabled'] ?? false);
    }
}

if (!function_exists('erp_ai')) {
    /** کلاینت سرویس هوش مصنوعی */
    function erp_ai(): \App\Support\AiServiceClient
    {
        return app(\App\Support\AiServiceClient::class);
    }
}

if (!function_exists('erp_llm')) {
    /** کلاینت AvalAI */
    function erp_llm(): \App\Support\AvalAiClient
    {
        return app(\App\Support\AvalAiClient::class);
    }
}
"""

MODULE_REGISTRY_TEMPLATE = r"""<?php

namespace App\Support;

/**
 * رجیستری ماژول‌های فعال این استقرار
 *
 * این فایل توسط «سازنده ERP هوشمند» تولید شده است و منبع حقیقت برای:
 *  - ساخت منوی سمت راست (بر اساس گروه منو)
 *  - تولید مجوزهای دسترسی
 *  - گزارش پوشش ماژول‌ها و نقاط هوش مصنوعی
 */
class ModuleRegistry
{
    /** @var array<int, array<string, mixed>> */
    public const MODULES = @@modules@@;

    /** @var array<int, string> */
    public const AI_ENGINES = @@engines@@;

    public static function all(): array
    {
        return self::MODULES;
    }

    public static function find(string $code): ?array
    {
        foreach (self::MODULES as $module) {
            if ($module['code'] === $code) {
                return $module;
            }
        }

        return null;
    }

    public static function codes(): array
    {
        return array_column(self::MODULES, 'code');
    }

    /** گروه‌بندی ماژول‌ها بر اساس گروه منو برای ساخت ناوبری */
    public static function menu(): array
    {
        $groups = [];

        foreach (self::MODULES as $module) {
            $groups[$module['menu_group']][] = [
                'code' => $module['code'],
                'title' => $module['label_fa'],
                'slug' => $module['slug'],
                'icon' => $module['icon'],
                'color' => $module['color'],
                'items' => $module['items_count'],
                'ai_points' => $module['ai_points'],
            ];
        }

        ksort($groups);

        return $groups;
    }

    /** آمار کلی استقرار */
    public static function stats(): array
    {
        return [
            'modules' => count(self::MODULES),
            'groups' => array_sum(array_column(self::MODULES, 'groups_count')),
            'items' => array_sum(array_column(self::MODULES, 'items_count')),
            'ai_points' => array_sum(array_column(self::MODULES, 'ai_points')),
            'tables' => array_sum(array_column(self::MODULES, 'tables_count')),
            'ai_engines' => self::AI_ENGINES,
            'sections' => array_values(array_unique(array_column(self::MODULES, 'section_code'))),
        ];
    }

    /** مسیر پایه API هر ماژول */
    public static function routePrefix(string $code): string
    {
        $module = self::find($code);

        return $module ? 'v1/' . $module['slug'] : 'v1';
    }
}
"""

# --------------------------------------------------------------------------- #
# میان‌افزارها
# --------------------------------------------------------------------------- #
MIDDLEWARE_JSON = r"""<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * اطمینان از قالب JSON در همه درخواست‌های API و افزودن شناسه رهگیری
 */
class EnsureApiJsonResponse
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        $traceId = $request->header('X-Request-Id') ?: ('erp_' . uniqid());
        $request->headers->set('X-Request-Id', $traceId);

        /** @var Response $response */
        $response = $next($request);

        $response->headers->set('X-Request-Id', $traceId);

        return $response;
    }
}
"""

MIDDLEWARE_PERSIAN = r"""<?php

namespace App\Http\Middleware;

use App\Support\PersianText;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * نرمال‌سازی ورودی فارسی: ارقام، «ي/ك» عربی و جداکننده هزارگان
 */
class NormalizePersianInput
{
    public function handle(Request $request, Closure $next): Response
    {
        $input = $request->all();

        if (!empty($input) && is_array($input)) {
            $request->merge($this->walk($input));
        }

        return $next($request);
    }

    /** @param array<string, mixed> $data */
    protected function walk(array $data): array
    {
        $result = [];

        foreach ($data as $key => $value) {
            if (is_array($value)) {
                $result[$key] = $this->walk($value);
                continue;
            }

            if (is_string($value)) {
                $result[$key] = $this->isNumericField($key)
                    ? (PersianText::toNumber($value) ?? PersianText::normalize($value))
                    : PersianText::normalize($value);
                continue;
            }

            $result[$key] = $value;
        }

        return $result;
    }

    protected function isNumericField(string $key): bool
    {
        $numericKeywords = [
            'amount', 'price', 'cost', 'quantity', 'qty', 'count', 'total', 'rate',
            'percent', 'weight', 'volume', 'salary', 'balance', 'sum', 'duration',
        ];

        foreach ($numericKeywords as $keyword) {
            if (str_contains($key, $keyword)) {
                return true;
            }
        }

        return false;
    }
}
"""

MIDDLEWARE_COMPANY = r"""<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * تعیین زمینه شرکت/کارخانه فعال برای استقرارهای چندشرکتی
 *
 * مقدار از سرآیند X-Company-Id یا اولین شرکت فعال گرفته می‌شود
 * و در کانتینر با کلید `current_company_id` در دسترس قرار می‌گیرد.
 */
class EnsureCompanyContext
{
    public function handle(Request $request, Closure $next): Response
    {
        $companyId = $request->header('X-Company-Id');

        if (!$companyId && config('erp.modules.multi_company', true)) {
            $companyId = $this->resolveDefaultCompany($request);
        }

        app()->instance('current_company_id', $companyId ? (int) $companyId : null);
        config(['erp.current_company_id' => $companyId ? (int) $companyId : null]);

        return $next($request);
    }

    protected function resolveDefaultCompany(Request $request): ?int
    {
        try {
            if (!class_exists(\App\Models\HumanResources\Company::class)) {
                return null;
            }

            $user = $request->user();

            if ($user && method_exists($user, 'company_id')) {
                return (int) $user->company_id;
            }

            return (int) (\App\Models\HumanResources\Company::query()
                ->where('is_active', true)
                ->orderBy('id')
                ->value('id') ?? 0) ?: null;
        } catch (\Throwable) {
            return null;
        }
    }
}
"""

MIDDLEWARE_AUDIT = r"""<?php

namespace App\Http\Middleware;

use App\Models\System\AuditEvent;
use App\Support\PersianText;
use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Symfony\Component\HttpFoundation\Response;
use Throwable;

/**
 * ثبت خودکار عملیات نوشتاری در جدول ممیزی (audit_events)
 *
 * فقط درخواست‌های POST/PUT/PATCH/DELETE روی /api ثبت می‌شوند.
 */
class AuditRequestMiddleware
{
    /** @var array<int, string> */
    protected array $auditedMethods = ['POST', 'PUT', 'PATCH', 'DELETE'];

    /** @var array<int, string> */
    protected array $excludedPaths = ['api/v1/auth', 'api/v1/ai/chat'];

    public function handle(Request $request, Closure $next): Response
    {
        $response = $next($request);

        if (!in_array($request->method(), $this->auditedMethods, true)) {
            return $response;
        }

        foreach ($this->excludedPaths as $excluded) {
            if ($request->is($excluded . '*')) {
                return $response;
            }
        }

        try {
            AuditEvent::create([
                'code' => PersianText::documentNumber('AUD', (int) AuditEvent::max('id') + 1),
                'user_id' => $request->user()?->id,
                'action' => strtolower($request->method()) . ':' . $request->path(),
                'entity_type' => $request->route()?->getName(),
                'entity_id' => null,
                'module_code' => $this->guessModule($request),
                'old_values' => null,
                'new_values' => [
                    'status' => $response->getStatusCode(),
                    'query' => $request->query(),
                    'ip' => $request->ip(),
                ],
                'ip_address' => $request->ip(),
                'user_agent' => mb_substr((string) $request->userAgent(), 0, 250),
                'occurred_at' => now(),
            ]);
        } catch (Throwable $exception) {
            Log::channel('audit')->debug('ثبت ممیزی خودکار ناموفق: ' . $exception->getMessage());
        }

        return $response;
    }

    protected function guessModule(Request $request): string
    {
        $segments = $request->segments();

        foreach (\App\Support\ModuleRegistry::all() as $module) {
            if (in_array($module['slug'], $segments, true)) {
                return $module['code'];
            }
        }

        return $segments[1] ?? 'system';
    }
}
"""

MIDDLEWARE_PERMISSION = r"""<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * بررسی مجوز دسترسی: Route::...->middleware('permission:module.table.edit')
 */
class CheckPermission
{
    public function handle(Request $request, Closure $next, string ...$permissions): Response
    {
        $user = $request->user();

        if (!$user) {
            return response()->json(['message' => 'احراز هویت لازم است.'], 401);
        }

        if ($user->is_super_admin) {
            return $next($request);
        }

        foreach ($permissions as $permission) {
            if ($user->hasPermissionTo($permission)) {
                return $next($request);
            }
        }

        return response()->json([
            'message' => 'شما مجوز انجام این عملیات را ندارید.',
            'required_permissions' => $permissions,
        ], 403);
    }
}
"""

# --------------------------------------------------------------------------- #
# ارائه‌دهنده‌ها
# --------------------------------------------------------------------------- #
APP_SERVICE_PROVIDER = r"""<?php

namespace App\Providers;

use App\Support\AiServiceClient;
use App\Support\AvalAiClient;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Date;
use Illuminate\Support\Facades\URL;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(AvalAiClient::class, fn () => new AvalAiClient());
        $this->app->singleton(AiServiceClient::class, fn () => new AiServiceClient());
    }

    public function boot(): void
    {
        // جلوگیری از بارگذاری تنبل ناخواسته در محیط تولید
        Model::preventLazyLoading(!app()->isProduction());
        Model::preventSilentlyDiscardingAttributes(!app()->isProduction());

        // منطقه زمانی و زبان پیش‌فرض
        date_default_timezone_set(config('app.timezone', 'Asia/Tehran'));
        Date::use(\Illuminate\Support\Carbon::class);

        if (app()->isProduction()) {
            URL::forceScheme('https');
        }
    }
}
"""

EVENT_SERVICE_PROVIDER = r"""<?php

namespace App\Providers;

use Illuminate\Foundation\Support\Providers\EventServiceProvider as ServiceProvider;

class EventServiceProvider extends ServiceProvider
{
    /** @var array<class-string, array<int, class-string>> */
    protected $listen = [];

    public function boot(): void
    {
        //
    }

    public function shouldDiscoverEvents(): bool
    {
        return false;
    }
}
"""

POLICY_PROVIDER_TEMPLATE = r"""<?php

namespace App\Providers;

use Illuminate\Support\Facades\Gate;
use Illuminate\Support\ServiceProvider;

/**
 * ثبت سیاست‌های دسترسی
 *
 * چون مدل‌ها در زیرفضای‌نام‌های بخش‌ها قرار دارند، کشف خودکار لاراول
 * کافی نیست و نگاشت به‌صورت صریح تولید شده است.
 */
class PolicyServiceProvider extends ServiceProvider
{
    /** @var array<class-string, class-string> */
    protected array $policies = @@policies@@;

    public function boot(): void
    {
        foreach ($this->policies as $model => $policy) {
            if (class_exists($model) && class_exists($policy)) {
                Gate::policy($model, $policy);
            }
        }
    }
}
"""

BASE_CONTROLLER = r"""<?php

namespace App\Http\Controllers;

/**
 * کنترلر پایه — لاراول ۱۱
 */
abstract class Controller
{
    //
}
"""

# --------------------------------------------------------------------------- #
# کنترلرهای سامانه
# --------------------------------------------------------------------------- #
AUTH_CONTROLLER = r"""<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\System\User;
use App\Support\AvalAiClient;
use App\Support\ModuleRegistry;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Validation\ValidationException;

/**
 * احراز هویت — ورود با Sanctum Token، خروج، پروفایل و مجوزها
 */
class AuthController extends Controller
{
    /** ورود کاربر و صدور توکن */
    public function login(Request $request): JsonResponse
    {
        $credentials = $request->validate([
            'login' => ['required', 'string'],
            'password' => ['required', 'string'],
            'device_name' => ['nullable', 'string', 'max:120'],
        ], [], [
            'login' => 'نام کاربری یا ایمیل',
            'password' => 'گذرواژه',
            'device_name' => 'نام دستگاه',
        ]);

        $throttleKey = 'login:' . $request->ip();
        if (RateLimiter::tooManyAttempts($throttleKey, 5)) {
            throw ValidationException::withMessages([
                'login' => 'تعداد تلاش‌های ناموفق بیش از حد مجاز است. چند دقیقه دیگر دوباره تلاش کنید.',
            ]);
        }

        /** @var User|null $user */
        $user = User::query()
            ->where('username', $credentials['login'])
            ->orWhere('email', $credentials['login'])
            ->orWhere('mobile', $credentials['login'])
            ->first();

        if (!$user || !Hash::check($credentials['password'], $user->password)) {
            RateLimiter::hit($throttleKey, 120);

            throw ValidationException::withMessages([
                'login' => 'نام کاربری یا گذرواژه نادرست است.',
            ]);
        }

        if (!$user->is_active) {
            throw ValidationException::withMessages([
                'login' => 'حساب کاربری شما غیرفعال است. با مدیر سامانه تماس بگیرید.',
            ]);
        }

        if ($user->locked_until && $user->locked_until->isFuture()) {
            throw ValidationException::withMessages([
                'login' => 'حساب کاربری تا ' . $user->locked_until->toDateTimeString() . ' قفل است.',
            ]);
        }

        RateLimiter::clear($throttleKey);

        $user->forceFill([
            'last_login_at' => now(),
            'last_login_ip' => $request->ip(),
            'failed_attempts' => 0,
        ])->save();

        $token = $user->createToken(
            $credentials['device_name'] ?? $request->userAgent() ?? 'api'
        )->plainTextToken;

        return response()->json([
            'token' => $token,
            'user' => $this->profilePayload($user),
        ]);
    }

    /** خروج و حذف توکن جاری */
    public function logout(Request $request): JsonResponse
    {
        $request->user()?->currentAccessToken()?->delete();

        return response()->json(['message' => 'با موفقیت از سامانه خارج شدید.']);
    }

    /** اطلاعات کاربر جاری، نقش‌ها و مجوزها */
    public function me(Request $request): JsonResponse
    {
        $user = $request->user();

        return response()->json([
            'user' => $this->profilePayload($user),
            'system' => [
                'app_name' => config('app.name'),
                'app_name_fa' => config('app.name_fa'),
                'company' => config('erp.identity.company_name'),
                'calendar' => config('erp.localization.calendar'),
                'currency' => config('erp.localization.currency'),
                'timezone' => config('app.timezone'),
                'version' => config('app.version'),
                'stats' => ModuleRegistry::stats(),
            ],
        ]);
    }

    /** به‌روزرسانی پروفایل کاربر جاری */
    public function updateProfile(Request $request): JsonResponse
    {
        $user = $request->user();

        $data = $request->validate([
            'full_name' => ['sometimes', 'string', 'max:191'],
            'mobile' => ['sometimes', 'string', 'max:20'],
            'locale' => ['sometimes', 'string', 'in:fa,en'],
            'avatar_path' => ['sometimes', 'nullable', 'string', 'max:191'],
        ]);

        $user->update($data);

        return response()->json(['message' => 'پروفایل به‌روزرسانی شد.', 'user' => $this->profilePayload($user)]);
    }

    /** تغییر گذرواژه */
    public function changePassword(Request $request): JsonResponse
    {
        $user = $request->user();

        $data = $request->validate([
            'current_password' => ['required', 'string'],
            'password' => ['required', 'string', 'min:8', 'confirmed'],
        ], [], [
            'current_password' => 'گذرواژه فعلی',
            'password' => 'گذرواژه جدید',
        ]);

        if (!Hash::check($data['current_password'], $user->password)) {
            throw ValidationException::withMessages([
                'current_password' => 'گذرواژه فعلی نادرست است.',
            ]);
        }

        $user->forceFill([
            'password' => Hash::make($data['password']),
            'password_changed_at' => now(),
        ])->save();

        // خروج همه دستگاه‌های دیگر
        $user->tokens()->where('id', '!=', $request->user()->currentAccessToken()->id)->delete();

        return response()->json(['message' => 'گذرواژه با موفقیت تغییر کرد.']);
    }

    protected function profilePayload(?User $user): array
    {
        if (!$user) {
            return [];
        }

        return [
            'id' => $user->id,
            'username' => $user->username,
            'full_name' => $user->full_name,
            'email' => $user->email,
            'mobile' => $user->mobile,
            'avatar_path' => $user->avatar_path,
            'locale' => $user->locale ?? 'fa',
            'is_super_admin' => (bool) $user->is_super_admin,
            'mfa_enabled' => (bool) $user->mfa_enabled,
            'roles' => $user->roles()->pluck('code'),
            'permissions' => $user->permissionCodes(),
            'menu' => ModuleRegistry::menu(),
        ];
    }
}
"""

FEATURE_CONTROLLER_TEMPLATE = r"""<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\System\SystemFeature;
use App\Support\ModuleRegistry;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * رجیستری قابلیت‌ها — چه چیزی در این استقرار فعال است؟
 *
 * این کنترلر به رابط کاربری اجازه می‌دهد بدون سخت‌کد، منوها و
 * امکانات فعال را بر اساس کاتالوگ کشف کند.
 */
class FeatureController extends Controller
{
    /** فهرست ماژول‌های فعال به تفکیک گروه منو */
    public function modules(): JsonResponse
    {
        return response()->json([
            'stats' => ModuleRegistry::stats(),
            'menu' => ModuleRegistry::menu(),
            'modules' => ModuleRegistry::all(),
        ]);
    }

    /** زیرمجموعه‌های فعال (سطح ۳ و ۴ کاتالوگ) */
    public function features(Request $request): JsonResponse
    {
        $query = SystemFeature::query();

        if ($section = $request->query('section')) {
            $query->where('section_code', strtoupper($section));
        }
        if ($module = $request->query('module')) {
            $query->where('module_code', strtoupper($module));
        }
        if ($request->boolean('ai_only')) {
            $query->where('is_ai_capability', true);
        }
        if ($term = $request->query('q')) {
            $query->where(fn ($q) => $q
                ->where('title', 'like', "%{$term}%")
                ->orWhere('code', 'like', "%{$term}%"));
        }

        $features = $query->orderBy('code')->limit(5000)->get();

        return response()->json([
            'count' => $features->count(),
            'features' => $features->groupBy('module_code')->map(fn ($group) => $group->map(fn ($feature) => [
                'code' => $feature->code,
                'title' => $feature->title,
                'feature_level' => $feature->feature_level,
                'group_code' => $feature->group_code,
                'module_code' => $feature->module_code,
                'section_code' => $feature->section_code,
                'is_ai' => (bool) $feature->is_ai_capability,
                'ai_engine' => $feature->ai_engine,
                'enabled' => (bool) $feature->is_enabled,
                'license_scope' => $feature->license_scope,
                'dependencies' => $feature->config['dependencies'] ?? [],
                'roles' => $feature->config['roles'] ?? [],
                'entity_table' => $feature->config['entity_table'] ?? null,
            ]))->all(),
        ]);
    }

    /** نقاط هوش مصنوعی فعال به تفکیک موتور */
    public function aiCapabilities(): JsonResponse
    {
        $capabilities = config('ai.capabilities', []);
        $grouped = [];

        foreach ($capabilities as $capability) {
            $grouped[$capability['engine']][] = $capability;
        }

        return response()->json([
            'engines' => config('ai.engines', []),
            'capabilities_by_engine' => $grouped,
            'total' => count($capabilities),
            'llm' => [
                'provider' => config('ai.llm.provider'),
                'model' => config('ai.llm.model'),
                'enabled' => app(\App\Support\AvalAiClient::class)->isEnabled(),
            ],
        ]);
    }

    /** مجوزهای تعریف‌شده در سامانه */
    public function permissions(): JsonResponse
    {
        if (!class_exists(\App\Models\System\Permission::class)) {
            return response()->json(['permissions' => []]);
        }

        return response()->json([
            'permissions' => \App\Models\System\Permission::query()
                ->orderBy('module_code')
                ->orderBy('code')
                ->get(['code', 'title', 'module_code', 'action'])
                ->groupBy('module_code'),
        ]);
    }
}
"""

DASHBOARD_CONTROLLER_TEMPLATE = r"""<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Support\AiServiceClient;
use App\Support\Jalali;
use App\Support\ModuleRegistry;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Throwable;

/**
 * داشبورد فرماندهی — نمای کلی کارخانه
 *
 * کارت‌ها از جدول‌های کلیدی و سرویس هر ماژول پر می‌شوند؛ اگر ماژولی
 * فعال نباشد، کارت مربوطه حذف می‌شود (بدون خطا).
 */
class DashboardController extends Controller
{
    public function __construct(protected AiServiceClient $ai)
    {
    }

    /** خلاصه مدیریتی صفحه اول */
    public function index(Request $request): JsonResponse
    {
        $today = Jalali::format(now());

        return response()->json([
            'date_jalali' => $today,
            'date_jalali_long' => Jalali::formatLong(now()),
            'company' => config('erp.identity.company_name'),
            'stats' => ModuleRegistry::stats(),
            'cards' => $this->cards(),
            'alerts' => $this->alerts(),
            'ai_health' => $this->ai->health(),
            'quick_links' => array_slice(ModuleRegistry::menu(), 0, 8, true),
        ]);
    }

    /** کارت‌های شاخص — فقط جدول‌های موجود در این استقرار */
    protected function cards(): array
    {
        $definitions = @@cards@@;

        $cards = [];
        foreach ($definitions as $definition) {
            try {
                if (!class_exists($definition['model'])) {
                    continue;
                }

                $model = new $definition['model']();
                $query = $model->newQuery();

                $value = match ($definition['metric']) {
                    'count' => $query->count(),
                    'sum' => (float) $query->sum($definition['column'] ?? 'id'),
                    'avg' => (float) $query->avg($definition['column'] ?? 'id'),
                    'open' => $query->whereNotIn('status', $definition['closed'] ?? ['done', 'closed', 'completed'])->count(),
                    default => 0,
                };

                $cards[] = [
                    'key' => $definition['key'],
                    'title' => $definition['title'],
                    'value' => $value,
                    'unit' => $definition['unit'] ?? '',
                    'icon' => $definition['icon'] ?? 'activity',
                    'color' => $definition['color'] ?? '#4f46e5',
                    'route' => $definition['route'] ?? null,
                ];
            } catch (Throwable) {
                continue;
            }
        }

        return $cards;
    }

    /** هشدارهای فعال سامانه */
    protected function alerts(): array
    {
        try {
            if (!class_exists(\App\Models\Performance\SystemAlert::class)) {
                return [];
            }

            return \App\Models\Performance\SystemAlert::query()
                ->where('is_resolved', false)
                ->orderByDesc('severity')
                ->orderByDesc('id')
                ->limit(10)
                ->get(['id', 'title', 'severity', 'status', 'created_at'])
                ->map(fn ($alert) => [
                    'id' => $alert->id,
                    'title' => $alert->title,
                    'severity' => $alert->severity,
                    'status' => $alert->status,
                    'created_at_jalali' => Jalali::format($alert->created_at, true),
                ])
                ->all();
        } catch (Throwable) {
            return [];
        }
    }
}
"""

AI_CONTROLLER = r"""<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Support\AiServiceClient;
use App\Support\AvalAiClient;
use App\Support\ModuleRegistry;
use App\Support\PersianText;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * دروازه هوش مصنوعی
 *
 * همه قابلیت‌های AI (پیش‌بینی، بهینه‌سازی، تشخیص ناهنجاری، بینایی ماشین،
 * SPC و...) از اینجا به سرویس پایتون ارسال می‌شوند؛ قابلیت‌های زبانی
 * (چت، خلاصه‌سازی، استخراج) مستقیماً با AvalAI انجام می‌شود.
 */
class AiController extends Controller
{
    public function __construct(
        protected AiServiceClient $ai,
        protected AvalAiClient $llm,
    ) {
    }

    /** فهرست موتورهای فعال و وضعیت سرویس AI */
    public function engines(): JsonResponse
    {
        return response()->json([
            'service' => $this->ai->health(),
            'engines' => config('ai.engines', []),
            'registry_engines' => ModuleRegistry::AI_ENGINES,
            'llm_enabled' => $this->llm->isEnabled(),
            'capabilities_total' => count(config('ai.capabilities', [])),
        ]);
    }

    /**
     * فراخوانی یک قابلیت AI
     *
     * POST /api/v1/ai/capabilities/{code}
     */
    public function run(Request $request, string $code): JsonResponse
    {
        $code = strtoupper($code);
        $capability = collect(config('ai.capabilities', []))->firstWhere('code', $code);

        if (!$capability) {
            return response()->json([
                'message' => "قابلیت {$code} در این استقرار فعال نیست.",
                'available' => array_column(config('ai.capabilities', []), 'code'),
            ], 404);
        }

        $payload = $request->validate([
            'payload' => ['sometimes', 'array'],
            'model_id' => ['sometimes', 'string', 'max:191'],
            'context' => ['sometimes', 'array'],
        ]);

        $result = $this->ai->call($capability['endpoint'], array_merge($payload['payload'] ?? [], [
            'capability' => $code,
            'capability_name' => $capability['name'],
            'engine' => $capability['engine'],
            'model_id' => $payload['model_id'] ?? $capability['model_id'],
            'feature_flag' => $capability['feature_flag'],
            'module_code' => $capability['module'],
            'context' => $payload['context'] ?? [],
            'requested_by' => $request->user()?->id,
        ]));

        return response()->json($result);
    }

    /** آموزش یا بازآموزی یک مدل */
    public function train(Request $request, string $modelId): JsonResponse
    {
        $payload = $request->validate([
            'dataset' => ['sometimes', 'array'],
            'algorithm' => ['sometimes', 'string', 'max:80'],
            'hyperparameters' => ['sometimes', 'array'],
            'period' => ['sometimes', 'array'],
        ]);

        return response()->json($this->ai->train($modelId, $payload));
    }

    /** گفت‌وگو با دستیار هوشمند کارخانه (AvalAI) */
    public function chat(Request $request): JsonResponse
    {
        $data = $request->validate([
            'message' => ['required', 'string', 'min:2', 'max:4000'],
            'history' => ['sometimes', 'array'],
            'context' => ['sometimes', 'array'],
        ], [], ['message' => 'پیام']);

        if (!$this->llm->isEnabled()) {
            return response()->json([
                'answer' => 'دستیار زبانی در این استقرار فعال نیست (کلید AvalAI تنظیم نشده است). '
                    . 'برای فعال‌سازی، متغیر AVALAI_API_KEY را در فایل .env تنظیم کنید.',
                'llm_used' => false,
                'fallback' => true,
                'suggestions' => $this->localSuggestions($data['message']),
            ]);
        }

        $system = $this->buildSystemPrompt($request);
        $messages = [['role' => 'system', 'content' => $system]];

        foreach (array_slice((array) ($data['history'] ?? []), -8) as $item) {
            if (is_array($item) && isset($item['role'], $item['content'])) {
                $messages[] = ['role' => (string) $item['role'], 'content' => (string) $item['content']];
            }
        }

        $messages[] = ['role' => 'user', 'content' => PersianText::normalize($data['message'])];

        $answer = $this->llm->chat($messages, ['temperature' => 0.3, 'max_tokens' => 900]);

        return response()->json([
            'answer' => $answer ?: 'پاسخی از سرویس زبانی دریافت نشد؛ لطفاً دوباره تلاش کنید.',
            'llm_used' => $answer !== null,
            'suggestions' => $answer ? [] : $this->localSuggestions($data['message']),
        ]);
    }

    /** خلاصه‌سازی متن (گزارش شیفت، عدم انطباق، رخداد نت) */
    public function summarize(Request $request): JsonResponse
    {
        $data = $request->validate([
            'text' => ['required', 'string', 'max:20000'],
            'max_length' => ['sometimes', 'integer', 'min:80', 'max:2000'],
        ], [], ['text' => 'متن']);

        $summary = $this->llm->summarize($data['text'], (int) ($data['max_length'] ?? 400));

        return response()->json([
            'summary' => $summary ?: PersianText::excerpt($data['text'], (int) ($data['max_length'] ?? 400)),
            'llm_used' => $summary !== null,
        ]);
    }

    /** استخراج ساختار از متن قرارداد/نامه */
    public function extract(Request $request): JsonResponse
    {
        $data = $request->validate([
            'text' => ['required', 'string', 'max:40000'],
            'schema' => ['sometimes', 'array'],
        ], [], ['text' => 'متن']);

        $schema = $data['schema'] ?? [
            'subject', 'parties', 'amount', 'currency', 'start_date', 'end_date',
            'obligations', 'penalties', 'guarantees', 'termination_conditions',
        ];

        $result = $this->llm->extract($data['text'], $schema);

        return response()->json([
            'extracted' => $result ?: [],
            'llm_used' => $result !== null,
            'schema' => $schema,
        ]);
    }

    /** طبقه‌بندی متن (دسته‌بندی تیکت، علت توقف، نوع عدم انطباق) */
    public function classify(Request $request): JsonResponse
    {
        $data = $request->validate([
            'text' => ['required', 'string', 'max:4000'],
            'labels' => ['required', 'array', 'min:2'],
            'labels.*' => ['string', 'max:80'],
        ], [], ['text' => 'متن', 'labels' => 'برچسب‌ها']);

        $label = $this->llm->classify($data['text'], $data['labels']);

        return response()->json([
            'label' => $label,
            'llm_used' => $label !== null,
            'fallback_label' => $label ?? ($data['labels'][0] ?? null),
        ]);
    }

    /** بینش متنی روی داده‌های داشبورد */
    public function insight(Request $request): JsonResponse
    {
        $data = $request->validate([
            'metrics' => ['required', 'array'],
            'question' => ['sometimes', 'string', 'max:500'],
        ], [], ['metrics' => 'شاخص‌ها']);

        $prompt = sprintf(
            "%s\n\nشاخص‌ها (JSON):\n%s\n\nتحلیل را در سه بخش «وضعیت فعلی»، «علت‌های محتمل» و "
            . "«اقدام پیشنهادی» به فارسی بنویس.",
            $data['question'] ?? 'این شاخص‌های کارخانه را تحلیل کن.',
            json_encode($data['metrics'], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)
        );

        $answer = $this->llm->complete($prompt, ['temperature' => 0.25, 'max_tokens' => 900]);

        return response()->json([
            'insight' => $answer ?: 'برای تولید بینش متنی، کلید AvalAI لازم است.',
            'llm_used' => $answer !== null,
        ]);
    }

    protected function buildSystemPrompt(Request $request): string
    {
        $stats = ModuleRegistry::stats();

        return sprintf(
            'تو دستیار هوشمند سامانه ERP کارخانه «%s» هستی. '
            . 'به فارسی روان، دقیق و کوتاه پاسخ بده و در صورت نیاز کد ماژول را ذکر کن. '
            . 'این استقرار %d ماژول، %d زیرمجموعه و %d نقطه هوش مصنوعی دارد. '
            . 'هرگز داده واقعی مشتری را حدس نزن و اگر اطلاعات کافی نیست، سؤال بپرس. '
            . 'در پاسخ‌های عددی از واحد %s استفاده کن.',
            config('erp.identity.company_name', 'کارخانه'),
            $stats['modules'],
            $stats['items'],
            $stats['ai_points'],
            config('erp.localization.currency_label', 'ریال')
        );
    }

    /** پیشنهاد قاعده‌محور وقتی AvalAI در دسترس نیست */
    protected function localSuggestions(string $message): array
    {
        $normalized = mb_strtolower(PersianText::normalize($message));

        if (str_contains($normalized, 'کیفیت') || str_contains($normalized, 'ضایعات')) {
            return ['ماژول‌های B (مدیریت کیفیت) را بررسی کنید.', 'شاخص‌های SPC در داشبورد کیفیت موجود است.'];
        }
        if (str_contains($normalized, 'توقف') || str_contains($normalized, 'خرابی')) {
            return ['ماژول C (نت) و گزارش MTBF/MTTR را ببینید.', 'هشدارهای PdM در بخش قابلیت‌های AI ثبت می‌شود.'];
        }
        if (str_contains($normalized, 'موجودی') || str_contains($normalized, 'انبار')) {
            return ['ماژول D (زنجیره تأمین) و نقطه سفارش کالاها را بررسی کنید.'];
        }
        if (str_contains($normalized, 'مالیات') || str_contains($normalized, 'مؤدیان')) {
            return ['ماژول F9 (مالیات و مؤدیان) برای ارسال صورتحساب الکترونیکی.'];
        }

        return [
            'می‌توانید نام ماژول یا کلیدواژه فارسی را در جست‌وجوی قابلیت‌ها وارد کنید.',
            'برای تحلیل عددی، داشبورد فرماندهی را باز کنید.',
        ];
    }
}
"""

AUDIT_CONTROLLER = r"""<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\System\AuditEvent;
use App\Support\Jalali;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * گزارش ممیزی — چه کسی، چه چیزی را، چه زمانی تغییر داد؟
 */
class AuditController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $query = AuditEvent::query()->with('user:id,username,full_name');

        if ($userId = $request->query('user_id')) {
            $query->where('user_id', $userId);
        }
        if ($module = $request->query('module')) {
            $query->where('module_code', strtoupper($module));
        }
        if ($action = $request->query('action')) {
            $query->where('action', 'like', "%{$action}%");
        }
        if ($from = $request->query('from')) {
            $query->where('occurred_at', '>=', Jalali::parseJalali($from)?->startOfDay() ?? $from);
        }
        if ($to = $request->query('to')) {
            $query->where('occurred_at', '<=', Jalali::parseJalali($to)?->endOfDay() ?? $to);
        }

        $events = $query->orderByDesc('occurred_at')
            ->paginate(min((int) $request->query('per_page', 25), 200));

        return response()->json([
            'data' => collect($events->items())->map(fn (AuditEvent $event) => [
                'id' => $event->id,
                'code' => $event->code,
                'action' => $event->action,
                'user' => $event->user?->full_name ?? 'سامانه',
                'entity_type' => $event->entity_type,
                'entity_id' => $event->entity_id,
                'module_code' => $event->module_code,
                'ip_address' => $event->ip_address,
                'occurred_at' => $event->occurred_at?->toIso8601String(),
                'occurred_at_jalali' => Jalali::format($event->occurred_at, true),
                'ai_anomaly_score' => $event->ai_anomaly_score !== null ? (float) $event->ai_anomaly_score : null,
            ])->all(),
            'meta' => [
                'current_page' => $events->currentPage(),
                'last_page' => $events->lastPage(),
                'per_page' => $events->perPage(),
                'total' => $events->total(),
            ],
        ]);
    }
}
"""

REPORT_CONTROLLER = r"""<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Support\Jalali;
use App\Support\ModuleRegistry;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Throwable;

/**
 * گزارش‌ساز عمومی
 *
 * امکان شمارش/جمع روی هر جدول فعال با فیلتر بازه تاریخ شمسی،
 * به‌همراه خروجی CSV آماده دانلود در رابط کاربری.
 */
class ReportController extends Controller
{
    /** فهرست جدول‌های قابل گزارش‌گیری در این استقرار */
    public function tables(): JsonResponse
    {
        return response()->json([
            'tables' => collect(ModuleRegistry::all())
                ->map(fn (array $module) => [
                    'module' => $module['code'],
                    'module_name' => $module['label_fa'],
                    'tables' => $module['tables'],
                ])
                ->values(),
        ]);
    }

    /** قالب‌های گزارش آماده (تولیدشده بر اساس ماژول‌های انتخابی) */
    public function templates(): JsonResponse
    {
        $templates = collect(config('reports.templates', []))
            ->filter(fn (array $template) => in_array($template['table'] ?? '', $this->allowedTables(), true))
            ->values();

        return response()->json([
            'templates' => $templates,
            'count' => $templates->count(),
            'source' => 'config/reports.php',
        ]);
    }

    /** اجرای گزارش تجمیعی روی یک جدول */
    public function aggregate(Request $request): JsonResponse
    {
        $data = $request->validate([
            'table' => ['required', 'string', 'max:80'],
            'metric' => ['required', 'in:count,sum,avg,max,min'],
            'column' => ['sometimes', 'string', 'max:80'],
            'group_by' => ['sometimes', 'string', 'max:80'],
            'date_column' => ['sometimes', 'string', 'max:80'],
            'from_jalali' => ['sometimes', 'date_format:Y/m/d'],
            'to_jalali' => ['sometimes', 'date_format:Y/m/d'],
            'limit' => ['sometimes', 'integer', 'min:1', 'max:1000'],
        ], [], [
            'table' => 'جدول',
            'metric' => 'سنجه',
            'column' => 'ستون',
            'group_by' => 'ستون گروه‌بندی',
        ]);

        $allowed = $this->allowedTables();
        if (!in_array($data['table'], $allowed, true)) {
            return response()->json([
                'message' => 'جدول درخواستی در این استقرار فعال نیست.',
                'allowed_tables' => array_slice($allowed, 0, 100),
            ], 422);
        }

        $query = DB::table($data['table']);

        if (!empty($data['date_column']) && !empty($data['from_jalali'])) {
            $from = Jalali::parseJalali($data['from_jalali']);
            if ($from) {
                $query->where($data['date_column'], '>=', $from->startOfDay());
            }
        }
        if (!empty($data['date_column']) && !empty($data['to_jalali'])) {
            $to = Jalali::parseJalali($data['to_jalali']);
            if ($to) {
                $query->where($data['date_column'], '<=', $to->endOfDay());
            }
        }

        $column = $data['column'] ?? 'id';
        $expression = match ($data['metric']) {
            'count' => DB::raw('COUNT(*) as value'),
            'sum' => DB::raw("SUM({$column}) as value"),
            'avg' => DB::raw("AVG({$column}) as value"),
            'max' => DB::raw("MAX({$column}) as value"),
            'min' => DB::raw("MIN({$column}) as value"),
        };

        try {
            if (!empty($data['group_by'])) {
                $rows = $query->select($data['group_by'], $expression)
                    ->groupBy($data['group_by'])
                    ->orderByDesc('value')
                    ->limit($data['limit'] ?? 100)
                    ->get();
            } else {
                $rows = collect([$query->select($expression)->first()]);
            }
        } catch (Throwable $exception) {
            return response()->json(['message' => 'اجرای گزارش ناموفق بود: ' . $exception->getMessage()], 422);
        }

        return response()->json([
            'table' => $data['table'],
            'metric' => $data['metric'],
            'rows' => $rows,
            'generated_at_jalali' => Jalali::format(now(), true),
        ]);
    }

    /** خروجی CSV یک جدول با فیلتر جست‌وجو */
    public function export(Request $request): JsonResponse
    {
        $data = $request->validate([
            'table' => ['required', 'string', 'max:80'],
            'q' => ['sometimes', 'string', 'max:191'],
            'limit' => ['sometimes', 'integer', 'min:1', 'max:50000'],
        ], [], ['table' => 'جدول']);

        if (!in_array($data['table'], $this->allowedTables(), true)) {
            return response()->json(['message' => 'جدول درخواستی فعال نیست.'], 422);
        }

        $query = DB::table($data['table']);

        if (!empty($data['q'])) {
            // ستون‌های متنی مناسب جست‌وجو (سازگار با MySQL/PostgreSQL/SQLite)
            $columns = collect(DB::getSchemaBuilder()->getColumnListing($data['table']))
                ->reject(fn ($name) => str_ends_with($name, '_at') || str_ends_with($name, '_id')
                    || in_array($name, ['id', 'deleted_at', 'remember_token', 'password'], true))
                ->take(6)
                ->values();

            $query->where(function ($builder) use ($columns, $data) {
                foreach ($columns as $column) {
                    $builder->orWhere((string) $column, 'like', '%' . $data['q'] . '%');
                }
            });
        }

        $rows = $query->limit($data['limit'] ?? 10000)->get();
        $headers = $rows->isEmpty() ? [] : array_keys((array) $rows->first());

        $csv = [];
        $csv[] = implode(',', $headers);
        foreach ($rows as $row) {
            $csv[] = implode(',', array_map(
                static fn ($value) => is_scalar($value) ? str_replace(',', '،', (string) $value) : '',
                (array) $row
            ));
        }

        return response()->json([
            'filename' => $data['table'] . '-' . now()->format('Ymd-His') . '.csv',
            'headers' => $headers,
            'rows' => $rows->count(),
            'content' => implode("\n", $csv),
            'generated_at_jalali' => Jalali::format(now(), true),
        ]);
    }

    /** @return array<int, string> */
    protected function allowedTables(): array
    {
        $tables = [];
        foreach (ModuleRegistry::all() as $module) {
            foreach ($module['tables'] as $table) {
                $tables[] = $table;
            }
        }

        return array_values(array_unique($tables));
    }
}
"""

# --------------------------------------------------------------------------- #
# دستورهای کنسول
# --------------------------------------------------------------------------- #
COMMAND_INSTALL = r"""<?php

namespace App\Console\Commands;

use App\Models\System\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Hash;

/**
 * نصب یک‌مرحله‌ای سامانه: مهاجرت، داده پایه، کاربر مدیر و همگام‌سازی قابلیت‌ها
 *
 * استفاده: php artisan erp:install --fresh
 */
class ErpInstall extends Command
{
    protected $signature = 'erp:install
        {--fresh : حذف و ساخت مجدد پایگاه داده}
        {--demo : درج داده نمونه}
        {--no-interaction : بدون پرسش}';

    protected $description = 'نصب کامل سامانه ERP (مهاجرت، داده پایه، مدیر، قابلیت‌ها)';

    public function handle(): int
    {
        $startedAt = microtime(true);

        $this->components->info('در حال نصب ' . config('app.name_fa'));
        $this->line('  ماژول‌های فعال: ' . count(\App\Support\ModuleRegistry::all()));
        $stats = \App\Support\ModuleRegistry::stats();
        $this->line("  زیرمجموعه‌ها: {$stats['items']} | نقاط AI: {$stats['ai_points']} | جداول: {$stats['tables']}");

        if ($this->option('fresh')) {
            $this->components->warn('حالت fresh: پایگاه داده از نو ساخته می‌شود.');
            Artisan::call('migrate:fresh', ['--force' => true], $this->output);
        } else {
            Artisan::call('migrate', ['--force' => true], $this->output);
        }

        Artisan::call('db:seed', [
            '--class' => 'Database\\Seeders\\SystemSeeder',
            '--force' => true,
        ], $this->output);

        Artisan::call('erp:features:sync', [], $this->output);

        if ($this->option('demo')) {
            Artisan::call('db:seed', [
                '--class' => 'Database\\Seeders\\DemoDataSeeder',
                '--force' => true,
            ], $this->output);
        }

        $this->ensureAdmin();

        Artisan::call('config:cache', [], $this->output);
        Artisan::call('route:cache', [], $this->output);
        Artisan::call('event:cache', [], $this->output);

        $elapsed = round(microtime(true) - $startedAt, 1);
        $this->components->info("نصب در {$elapsed} ثانیه کامل شد.");
        $this->line('  ایمیل مدیر: ' . config('erp.identity.company_name'));

        return self::SUCCESS;
    }

    protected function ensureAdmin(): void
    {
        $email = (string) env('ERP_ADMIN_EMAIL', 'admin@example.com');

        $user = User::query()->where('email', $email)->first();

        if ($user) {
            $this->components->info("کاربر مدیر از قبل وجود دارد: {$email}");

            return;
        }

        User::query()->create([
            'username' => 'admin',
            'full_name' => (string) env('ERP_ADMIN_NAME', 'مدیر سامانه'),
            'email' => $email,
            'mobile' => '09120000000',
            'password' => Hash::make((string) env('ERP_ADMIN_PASSWORD', 'ChangeMe!1405')),
            'locale' => 'fa',
            'is_active' => true,
            'is_super_admin' => true,
            'password_changed_at' => now(),
        ]);

        $this->components->info("کاربر مدیر ساخته شد: {$email}");
    }
}
"""

COMMAND_SYNC_FEATURES = r"""<?php

namespace App\Console\Commands;

use App\Models\System\SystemFeature;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;

/**
 * همگام‌سازی رجیستری قابلیت‌ها با کاتالوگ این استقرار
 *
 * منبع: config/features.php (تولیدشده توسط سازنده ERP)
 */
class SyncFeatures extends Command
{
    protected $signature = 'erp:features:sync {--prune : حذف قابلیت‌هایی که دیگر در کاتالوگ نیستند}';

    protected $description = 'به‌روزرسانی جدول system_features از کاتالوگ انتخاب‌شده';

    public function handle(): int
    {
        $features = config('features.items', []);
        $this->components->info('تعداد قابلیت‌های کاتالوگ: ' . count($features));

        $now = now();
        $inserted = 0;
        $updated = 0;

        DB::transaction(function () use ($features, $now, &$inserted, &$updated) {
            foreach ($features as $code => $feature) {
                $row = [
                    'code' => $code,
                    'title' => $feature['title'],
                    'section_code' => $feature['section_code'],
                    'module_code' => $feature['module_code'],
                    'group_code' => $feature['group_code'],
                    'feature_level' => $feature['feature_level'] ?? 'item',
                    'is_ai_capability' => (bool) ($feature['is_ai'] ?? false),
                    'ai_engine' => $feature['ai_engine'] ?? null,
                    'is_enabled' => (bool) ($feature['enabled'] ?? true),
                    'license_scope' => $feature['license_scope'] ?? 'standard',
                    'enabled_at' => $now,
                    'config' => $feature['config'] ?? [],
                    'updated_at' => $now,
                ];

                $existing = SystemFeature::query()->where('code', $code)->first();

                if ($existing) {
                    $existing->update($row);
                    $updated++;
                    continue;
                }

                SystemFeature::query()->create($row + ['created_at' => $now]);
                $inserted++;
            }

            if ($this->option('prune')) {
                SystemFeature::query()->whereNotIn('code', array_keys($features))->delete();
            }
        });

        $this->components->info("انجام شد — جدید: {$inserted}، به‌روزرسانی: {$updated}");

        return self::SUCCESS;
    }
}
"""

COMMAND_BACKUP = r"""<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Artisan;
use Throwable;

/**
 * پشتیبان‌گیری از پایگاه داده و فایل‌های آپلودشده
 *
 * زمان‌بندی پیش‌فرض: @@backup_cron@@
 */
class BackupDatabase extends Command
{
    protected $signature = 'erp:backup
        {--disk=local : دیسک مقصد پشتیبان}
        {--keep=@@backup_keep_days@@ : تعداد روزهای نگهداری}
        {--files : پشتیبان از فایل‌های آپلودشده نیز گرفته شود}';

    protected $description = 'پشتیبان‌گیری کامل از پایگاه داده و فایل‌ها';

    public function handle(): int
    {
        $disk = Storage::disk($this->option('disk'));
        $folder = 'backups/' . now()->format('Y/m');
        $name = config('app.name') . '-' . now()->format('Ymd-His');

        try {
            $disk->makeDirectory($folder);

            $sqlPath = storage_path("app/{$name}.sql");
            $this->dumpDatabase($sqlPath);

            if (file_exists($sqlPath)) {
                $disk->put("{$folder}/{$name}.sql.gz", gzencode((string) file_get_contents($sqlPath), 6));
                @unlink($sqlPath);
                $this->components->info("پشتیبان پایگاه داده ذخیره شد: {$folder}/{$name}.sql.gz");
            } else {
                $this->components->warn('خروجی dump خالی بود؛ از snapshot داخلی لاراول استفاده شد.');
                $disk->put("{$folder}/{$name}-snapshot.json", (string) json_encode([
                    'generated_at' => now()->toIso8601String(),
                    'connection' => config('database.default'),
                    'database' => config('database.connections.' . config('database.default') . '.database'),
                ]));
            }

            if ($this->option('files')) {
                $this->backupFiles($disk, $folder, $name);
            }

            $this->prune((int) $this->option('keep'));

            return self::SUCCESS;
        } catch (Throwable $exception) {
            $this->components->error('پشتیبان‌گیری ناموفق بود: ' . $exception->getMessage());

            return self::FAILURE;
        }
    }

    protected function dumpDatabase(string $path): void
    {
        $connection = config('database.default');

        if ($connection === 'sqlite') {
            $database = config('database.connections.sqlite.database');
            if (is_string($database) && file_exists($database)) {
                copy($database, $path . '.sqlite');
                rename($path . '.sqlite', $path);
            }

            return;
        }

        $binary = $connection === 'pgsql' ? 'pg_dump' : 'mysqldump';
        $host = escapeshellarg((string) config("database.connections.{$connection}.host"));
        $port = escapeshellarg((string) config("database.connections.{$connection}.port"));
        $database = escapeshellarg((string) config("database.connections.{$connection}.database"));
        $username = escapeshellarg((string) config("database.connections.{$connection}.username"));
        $password = escapeshellarg((string) config("database.connections.{$connection}.password"));

        $command = $connection === 'pgsql'
            ? "PGPASSWORD={$password} {$binary} -h {$host} -p {$port} -U {$username} {$database} > " . escapeshellarg($path)
            : "{$binary} -h {$host} -P {$port} -u {$username} -p{$password} {$database} > " . escapeshellarg($path);

        @exec($command . ' 2>/dev/null');
    }

    protected function backupFiles($disk, string $folder, string $name): void
    {
        $files = collect(Storage::disk('documents')->allFiles())->take(5000);
        $manifest = $files->mapWithKeys(fn (string $file) => [
            $file => Storage::disk('documents')->size($file),
        ]);

        $disk->put("{$folder}/{$name}-files.json", (string) $manifest->toJson(JSON_UNESCAPED_UNICODE));
        $this->components->info('فهرست فایل‌های اسناد ذخیره شد: ' . $manifest->count() . ' فایل');
    }

    protected function prune(int $keepDays): void
    {
        if ($keepDays <= 0) {
            return;
        }

        $cutoff = now()->subDays($keepDays);
        $removed = 0;

        foreach (Storage::disk($this->option('disk'))->allFiles('backups') as $file) {
            if (Storage::disk($this->option('disk'))->lastModified($file) < $cutoff->timestamp) {
                Storage::disk($this->option('disk'))->delete($file);
                $removed++;
            }
        }

        if ($removed) {
            $this->components->info("پشتیبان‌های قدیمی‌تر از {$keepDays} روز حذف شد: {$removed} فایل");
        }
    }
}
"""

COMMAND_AI_HEALTH = r"""<?php

namespace App\Console\Commands;

use App\Support\AiServiceClient;
use App\Support\AvalAiClient;
use Illuminate\Console\Command;

/**
 * بررسی سلامت سرویس‌های هوش مصنوعی
 */
class AiHealth extends Command
{
    protected $signature = 'erp:ai:health {--verbose-service : نمایش جزئیات سرویس}';

    protected $description = 'بررسی وضعیت سرویس AI (پایتون) و AvalAI';

    public function handle(AiServiceClient $ai, AvalAiClient $llm): int
    {
        $service = $ai->health();

        $rows = [];
        foreach ((array) config('ai.engines', []) as $engine) {
            $rows[] = [
                $engine['key'] ?? '',
                $engine['name_fa'] ?? '',
                $engine['endpoint'] ?? '',
                $engine['uses_llm'] ? 'بله' : 'خیر',
                in_array($engine['key'] ?? '', (array) ($service['engines'] ?? []), true) ? 'فعال' : 'آماده',
            ];
        }

        $this->components->info('وضعیت سرویس AI: ' . (($service['ok'] ?? false) ? 'در دسترس' : 'در دسترس نیست'));
        $this->line('  آدرس: ' . config('services.ai_service.base_url'));
        $this->line('  مدل‌های ثبت‌شده: ' . ($service['models'] ?? 0));

        $this->table(['موتور', 'نام فارسی', 'اندپوینت', 'نیاز به LLM', 'وضعیت'], $rows);

        $this->line('AvalAI: ' . ($llm->isEnabled() ? 'کلید تنظیم شده ✓' : 'کلید تنظیم نشده (غیرفعال)'));
        $this->line('مدل زبانی: ' . config('ai.llm.model'));

        if ($this->option('verbose-service')) {
            $this->line((string) json_encode($service, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        }

        return self::SUCCESS;
    }
}
"""

# --------------------------------------------------------------------------- #
# مدل کاربر (بازنویسی مدل تولیدشده برای S1)
# --------------------------------------------------------------------------- #
USER_MODEL_TEMPLATE = r"""<?php

namespace App\Models\System;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Laravel\Sanctum\HasApiTokens;

/**
 * کاربر سامانه
 *
 * ماژول: S1 — امنیت و مدیریت دسترسی
 * جدول: users
 *
 * این مدل بازنویسی‌شده مدل تولیدشده است تا احراز هویت Sanctum،
 * نقش‌ها و مجوزها را پیاده‌سازی کند.
 */
class User extends Authenticatable
{
    use HasApiTokens;
    use HasFactory;
    use Notifiable;
    use SoftDeletes;

    protected $table = 'users';

    /** @var array<int, string> */
    protected $fillable = [
@@fillable@@
    ];

    /** @var array<int, string> */
    protected $hidden = [
        'password',
        'mfa_secret',
        'remember_token',
    ];

    /** @var array<string, string> */
    protected $casts = [
@@casts@@
    ];

    public static string $labelFa = 'کاربر';

    /** نقش‌های کاربر */
    public function roles(): BelongsToMany
    {
        return $this->belongsToMany(Role::class, 'user_roles')
            ->withPivot(['valid_from', 'valid_to', 'granted_by'])
            ->withTimestamps();
    }

    /** کارمند مرتبط */
    public function employee(): BelongsTo
    {
        return $this->belongsTo(\App\Models\HumanResources\Employee::class, 'employee_id');
    }

    /** رویدادهای ممیزی این کاربر */
    public function auditEvents(): HasMany
    {
        return $this->hasMany(AuditEvent::class, 'user_id');
    }

    /** همه مجوزهای کاربر از طریق نقش‌ها */
    public function permissionCodes(): array
    {
        if ($this->is_super_admin) {
            return ['*'];
        }

        return Cache::remember("user:{$this->id}:permissions", now()->addMinutes(10), function () {
            $roleIds = $this->roles()->pluck('roles.id');

            if ($roleIds->isEmpty()) {
                return [];
            }

            return DB::table('role_permissions')
                ->join('permissions', 'permissions.id', '=', 'role_permissions.permission_id')
                ->whereIn('role_permissions.role_id', $roleIds)
                ->pluck('permissions.code')
                ->unique()
                ->values()
                ->all();
        });
    }

    /** بررسی داشتن یک مجوز */
    public function hasPermissionTo(string $permission): bool
    {
        if ($this->is_super_admin) {
            return true;
        }

        $codes = $this->permissionCodes();

        if (in_array('*', $codes, true) || in_array($permission, $codes, true)) {
            return true;
        }

        // مجوز سطح ماژول: module.* همه زیرمجوزها را پوشش می‌دهد
        $prefix = explode('.', $permission)[0];

        return in_array($prefix . '.*', $codes, true);
    }

    /** بررسی داشتن یک نقش */
    public function hasRole(string $role): bool
    {
        if ($this->is_super_admin) {
            return true;
        }

        return $this->roles()->where('code', $role)->exists()
            || $this->roles()->where('title', $role)->exists();
    }

    /** بررسی داشتن حداقل یکی از نقش‌ها */
    public function hasAnyRole(array $roles): bool
    {
        foreach ($roles as $role) {
            if ($this->hasRole($role)) {
                return true;
            }
        }

        return false;
    }

    /** آیا حساب قفل است؟ */
    public function isLocked(): bool
    {
        return $this->locked_until !== null && $this->locked_until->isFuture();
    }

    /** ثبت تلاش ناموفق ورود و قفل خودکار */
    public function registerFailedAttempt(int $maxAttempts = 5, int $lockMinutes = 15): void
    {
        $this->failed_attempts = (int) $this->failed_attempts + 1;

        if ($this->failed_attempts >= $maxAttempts) {
            $this->locked_until = now()->addMinutes($lockMinutes);
            $this->failed_attempts = 0;
        }

        $this->save();
    }

    /** دامنه جست‌وجو */
    public function scopeSearch($query, ?string $term)
    {
        if (!$term) {
            return $query;
        }

        return $query->where(function ($q) use ($term) {
            $q->where('username', 'like', "%{$term}%")
              ->orWhere('full_name', 'like', "%{$term}%")
              ->orWhere('email', 'like', "%{$term}%")
              ->orWhere('mobile', 'like', "%{$term}%");
        });
    }

    /** دامنه کاربران فعال */
    public function scopeActive($query)
    {
        return $query->where('is_active', true)->whereNull('locked_until');
    }

    public function displayLabel(): string
    {
        return (string) ($this->full_name ?? $this->username ?? $this->id);
    }
}
"""


USER_FACTORY_TEMPLATE = r"""<?php

namespace Database\Factories\System;

use App\Models\System\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

/**
 * کارخانه داده کاربر سامانه
 *
 * @extends Factory<User>
 */
class UserFactory extends Factory
{
    protected $model = User::class;

    protected static ?string $password = null;

    /**
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'username' => $this->faker->unique()->userName(),
            'full_name' => $this->faker->name(),
            'email' => $this->faker->unique()->safeEmail(),
            'mobile' => '0912' . $this->faker->unique()->numerify('#######'),
            'password' => static::$password ??= Hash::make('password'),
            'locale' => 'fa',
            'is_active' => true,
            'is_super_admin' => false,
            'mfa_enabled' => false,
            'failed_attempts' => 0,
            'remember_token' => Str::random(10),
        ];
    }

    /** کاربر مدیر کل */
    public function admin(): static
    {
        return $this->state(fn () => [
            'is_super_admin' => true,
            'username' => 'admin',
            'email' => config('erp.admin_email', 'admin@example.com'),
        ]);
    }

    /** کاربر غیرفعال */
    public function inactive(): static
    {
        return $this->state(fn () => ['is_active' => false]);
    }

    /** کاربر قفل‌شده */
    public function locked(): static
    {
        return $this->state(fn () => ['locked_until' => now()->addMinutes(15)]);
    }
}
"""


def _user_fillable(entity: dict[str, Any] | None) -> str:
    names = [f["name"] for f in entity["fields"]] if entity else ["username", "full_name", "email", "password"]
    if "password" not in names:
        names.append("password")
    return "\n".join(f"        '{name}'," for name in names)


def _user_casts(entity: dict[str, Any] | None) -> str:
    lines = [
        "        'email_verified_at' => 'datetime',",
        "        'password' => 'hashed',",
        "        'is_active' => 'boolean',",
        "        'is_super_admin' => 'boolean',",
        "        'mfa_enabled' => 'boolean',",
        "        'last_login_at' => 'datetime',",
        "        'locked_until' => 'datetime',",
        "        'password_changed_at' => 'datetime',",
        "        'failed_attempts' => 'integer',",
    ]
    if entity:
        for field in entity["fields"]:
            if field["type"] in ("date", "datetime") and "password" not in field["name"]:
                cast = "'date:Y-m-d'" if field["type"] == "date" else "'datetime'"
                line = f"        '{field['name']}' => {cast},"
                if line not in lines:
                    lines.append(line)
    return "\n".join(lines)


def build_reports_config(
    modules: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    *,
    context: dict[str, Any] | None = None,
    per_module: int = 3,
) -> str:
    """ساخت `config/reports.php` با قالب‌های گزارش آماده برای هر ماژول.

    برای هر موجودیت مهم، یک قالب گزارش تجمیعی تعریف می‌شود که رابط کاربری
    می‌تواند آن را مستقیماً به `/api/v1/reports/aggregate` بفرستد.
    """
    context = context or {}
    entities_by_module: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        entities_by_module.setdefault(entity.get("module_code") or "S0", []).append(entity)

    templates: list[dict[str, Any]] = []
    for module in modules:
        candidates = entities_by_module.get(module["code"], [])

        def score(entity: dict[str, Any]) -> tuple[int, str]:
            fields = entity["fields"]
            has_status = any(f["type"] == "enum" for f in fields)
            has_metric = any(f["type"] in ("decimal", "integer", "bigint") for f in fields)
            return (-(int(has_status) * 2 + int(has_metric)), entity["table"])

        for entity in sorted(candidates, key=score)[:per_module]:
            fields = entity["fields"]
            metric_field = next(
                (f for f in fields if f["type"] == "decimal" and not f["nullable"]),
                next((f for f in fields if f["type"] in ("decimal", "integer", "bigint")), None),
            )
            group_field = next(
                (f for f in fields if f["type"] == "enum" and f["name"] in ("status", "state", "priority", "type")),
                next((f for f in fields if f["type"] == "enum"), None),
            )
            date_field = next(
                (f for f in fields if f["type"] in ("date", "datetime") and f["name"] != "created_at"),
                None,
            )
            numeric_label = metric_field["label"] if metric_field else "تعداد رکوردها"

            templates.append(
                {
                    "id": f"{module['slug']}_{entity['table']}",
                    "module_code": module["code"],
                    "module_name": module["label_fa"],
                    "title": f"{entity['label_fa']} — "
                    + (f"میانگین {numeric_label}" if metric_field and metric_field["type"] == "decimal"
                       else f"تعداد {entity['label_fa']}"),
                    "table": entity["table"],
                    "metric": "sum" if metric_field and metric_field["type"] == "decimal" else "count",
                    "column": metric_field["name"] if metric_field else None,
                    "group_by": group_field["name"] if group_field else None,
                    "date_column": date_field["name"] if date_field else "created_at",
                    "chart": "bar" if group_field else "line",
                    "permission": f"{module['slug']}.{entity['table']}.view",
                }
            )

    header = (
        "<?php\n\n"
        "/**\n"
        f" * قالب‌های گزارش آماده — {context.get('app_name_fa', 'ERP کارخانه')}\n"
        " *\n"
        f" * {len(templates)} قالب از {len(modules)} ماژول و {len(entities)} جدول\n"
        " * تولیدشده توسط سازنده ERP؛ ویرایش دستی با ساخت مجدد بسته بازنویسی می‌شود.\n"
        " */\n\nreturn "
    )
    return header + php_array(
        {
            "version": context.get("version", "1.0.0"),
            "generated_at": context.get("generated_at", ""),
            "timezone": "Asia/Tehran",
            "default_limit": 100,
            "templates": templates,
        },
        level=0,
    ) + ";\n"


def generate_system_files(
    package: Package,
    *,
    settings: dict[str, Any],
    modules: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    ai_engines: list[dict[str, Any]],
    ai_points: list[dict[str, Any]],
    catalog_items: list[dict[str, Any]],
    context: dict[str, Any],
) -> None:
    """تولید لایه سیستمی: پشتیبانی، میان‌افزار، ارائه‌دهنده، کنترلر، دستور."""
    # -- کلاس‌های پشتیبانی -------------------------------------------------- #
    package.add("backend/app/Support/Jalali.php", JALALI_CLASS, area="laravel-support")
    package.add("backend/app/Support/PersianText.php", PERSIAN_TEXT_CLASS, area="laravel-support")
    package.add("backend/app/Support/AvalAiClient.php", AVALAI_CLIENT, area="laravel-support")
    package.add("backend/app/Support/AiServiceClient.php", AI_SERVICE_CLIENT, area="laravel-support")
    package.add("backend/app/Support/ActivityLogger.php", ACTIVITY_LOGGER, area="laravel-support")
    package.add("backend/app/Support/helpers.php", HELPERS, area="laravel-support")

    # -- رجیستری ماژول‌ها ---------------------------------------------------- #
    entity_tables: dict[str, list[str]] = {}
    for entity in entities:
        entity_tables.setdefault(entity["module_code"], []).append(entity["table"])

    section_icons = context["section_meta"]
    registry_modules = []
    for module in modules:
        section_code = module["code"][:1]
        registry_modules.append(
            {
                "code": module["code"],
                "slug": module["slug"],
                "label_fa": module["label_fa"],
                "name_en": module.get("name_en", ""),
                "menu_group": module.get("menu_group") or section_icons.get(section_code, {}).get("menu", "سایر"),
                "section_code": section_code,
                "section_name": section_icons.get(section_code, {}).get("name", ""),
                "icon": section_icons.get(section_code, {}).get("icon", "box"),
                "color": section_icons.get(section_code, {}).get("color", "#4f46e5"),
                "description": module.get("description", ""),
                "priority": module.get("priority", 3),
                "derived": bool(module.get("derived")),
                "groups_count": context["module_stats"].get(module["code"], {}).get("groups", 0),
                "items_count": context["module_stats"].get(module["code"], {}).get("items", 0),
                "ai_points": context["module_stats"].get(module["code"], {}).get("ai", 0),
                "tables": entity_tables.get(module["code"], []),
                "tables_count": len(entity_tables.get(module["code"], [])),
                "route_prefix": "v1/" + module["slug"],
            }
        )

    # ماژول مجازی پلتفرم (S0) — موجودیت‌هایی مانند system_features که کد ماژول
    # کاتالوگ ندارند؛ بدون این ورودی، مجوزهای مسیر routes/modules/system.php
    # هرگز در SystemSeeder ساخته نمی‌شدند.
    platform_tables = entity_tables.get("", [])
    if platform_tables:
        section_meta_s = section_icons.get("S", {})
        registry_modules.append(
            {
                "code": "S0",
                "slug": "system",
                "label_fa": "هسته پلتفرم",
                "name_en": "Platform Core",
                "menu_group": section_meta_s.get("menu", "سامانه"),
                "section_code": "S",
                "section_name": section_meta_s.get("name", "مدیریت سیستم"),
                "icon": section_meta_s.get("icon", "shield"),
                "color": section_meta_s.get("color", "#6366f1"),
                "description": "رجیستری قابلیت‌ها و موجودیت‌های پلتفرمی",
                "priority": 1,
                "derived": False,
                "groups_count": 0,
                "items_count": 0,
                "ai_points": 0,
                "tables": platform_tables,
                "tables_count": len(platform_tables),
                "route_prefix": "v1/system",
                "platform": True,
            }
        )

    package.add_rendered(
        "backend/app/Support/ModuleRegistry.php",
        MODULE_REGISTRY_TEMPLATE,
        area="laravel-support",
        modules=php_array(registry_modules, level=1),
        engines=php_array([e["key"] for e in ai_engines], level=1),
    )

    # -- میان‌افزارها -------------------------------------------------------- #
    package.add("backend/app/Http/Middleware/EnsureApiJsonResponse.php", MIDDLEWARE_JSON, area="laravel-middleware")
    package.add("backend/app/Http/Middleware/NormalizePersianInput.php", MIDDLEWARE_PERSIAN, area="laravel-middleware")
    package.add("backend/app/Http/Middleware/EnsureCompanyContext.php", MIDDLEWARE_COMPANY, area="laravel-middleware")
    package.add("backend/app/Http/Middleware/AuditRequestMiddleware.php", MIDDLEWARE_AUDIT, area="laravel-middleware")
    package.add("backend/app/Http/Middleware/CheckPermission.php", MIDDLEWARE_PERMISSION, area="laravel-middleware")

    # -- ارائه‌دهنده‌ها ------------------------------------------------------ #
    package.add("backend/app/Providers/AppServiceProvider.php", APP_SERVICE_PROVIDER, area="laravel-providers")
    package.add("backend/app/Providers/EventServiceProvider.php", EVENT_SERVICE_PROVIDER, area="laravel-providers")
    package.add("backend/app/Http/Controllers/Controller.php", BASE_CONTROLLER, area="laravel-controllers")

    # نگاشت سیاست‌ها
    policy_map = {}
    for entity in entities:
        from .laravel_domain import module_namespace

        # موجودیت پلتفرمی module_code خالی دارد؛ باید به S0 نگاشت شود تا
        # فضای‌نام System (نه Core) برای کلید سیاست به‌کار رود، وگرنه سیاستِ
        # App\Models\System\SystemFeature هرگز در PolicyServiceProvider ثبت نمی‌شود.
        namespace = module_namespace({"code": entity["module_code"] or "S0", "slug": ""})
        policy_map[f"App\\Models\\{namespace}\\{entity['name']}"] = (
            f"App\\Policies\\{namespace}\\{entity['name']}Policy"
        )
    package.add_rendered(
        "backend/app/Providers/PolicyServiceProvider.php",
        POLICY_PROVIDER_TEMPLATE,
        area="laravel-providers",
        policies=json.dumps(policy_map, ensure_ascii=False, indent=8).replace('"', "'"),
    )

    # -- کنترلرهای سامانه ---------------------------------------------------- #
    package.add("backend/app/Http/Controllers/Api/AuthController.php", AUTH_CONTROLLER, area="laravel-controllers")
    package.add("backend/app/Http/Controllers/Api/FeatureController.php", FEATURE_CONTROLLER_TEMPLATE, area="laravel-controllers")
    package.add("backend/app/Http/Controllers/Api/AiController.php", AI_CONTROLLER, area="laravel-controllers")
    package.add("backend/app/Http/Controllers/Api/AuditController.php", AUDIT_CONTROLLER, area="laravel-controllers")
    package.add("backend/app/Http/Controllers/Api/ReportController.php", REPORT_CONTROLLER, area="laravel-controllers")

    # کارت‌های داشبورد از موجودیت‌های کلیدی موجود
    key_cards = [
        ("items", "کالاها", "Item", "SupplyChain", "count", "package", "#2563eb"),
        ("production_plans", "برنامه‌های تولید", "ProductionPlan", "Manufacturing", "count", "calendar-clock", "#4f46e5"),
        ("work_orders", "دستورهای کار", "WorkOrder", "Manufacturing", "open", "factory", "#dc2626"),
        ("purchase_orders", "سفارش‌های خرید", "PurchaseOrder", "SupplyChain", "open", "shopping-cart", "#0891b2"),
        ("sales_orders", "سفارش‌های فروش", "SalesOrder", "Sales", "open", "trending-up", "#db2777"),
        ("inspections", "بازرسی‌های کیفیت", "InspectionOrder", "Quality", "count", "award", "#16a34a"),
        ("work_orders_maintenance", "کارهای نت", "MaintenanceOrder", "Maintenance", "open", "wrench", "#ea580c"),
        ("journal_entries", "اسناد حسابداری", "JournalEntry", "Finance", "count", "book", "#0d9488"),
        ("invoices", "فاکتورهای فروش", "SalesInvoice", "Sales", "open", "file-text", "#7c3aed"),
        ("employees", "کارکنان", "Employee", "HumanResources", "count", "users", "#a855f7"),
        ("ai_models", "مدل‌های AI", "AiModel", "Ai", "count", "brain", "#f59e0b"),
    ]
    table_names = {e["table"]: e for e in entities}
    cards = []
    for key, title, model, namespace, metric, icon, color in key_cards:
        match = next((e for e in entities if e["name"] == model), None)
        if not match:
            continue
        cards.append(
            {
                "key": key,
                "title": title,
                "model": f"App\\Models\\{namespace}\\{model}",
                "metric": metric,
                "icon": icon,
                "color": color,
                "route": f"/modules/{match['table']}",
                "unit": "",
                "closed": ["done", "closed", "completed", "cancelled", "paid"],
            }
        )
    if not cards:
        cards.append(
            {
                "key": "features",
                "title": "قابلیت‌های فعال",
                "model": "App\\Models\\System\\SystemFeature",
                "metric": "count",
                "icon": "box",
                "color": "#4f46e5",
                "route": "/system/features",
            }
        )

    package.add_rendered(
        "backend/app/Http/Controllers/Api/DashboardController.php",
        DASHBOARD_CONTROLLER_TEMPLATE,
        area="laravel-controllers",
        cards=json.dumps(cards, ensure_ascii=False, indent=12).replace('"', "'"),
    )

    # -- دستورهای کنسول ------------------------------------------------------ #
    package.add_rendered(
        "backend/app/Console/Commands/ErpInstall.php",
        COMMAND_INSTALL,
        area="laravel-commands",
    )
    package.add("backend/app/Console/Commands/SyncFeatures.php", COMMAND_SYNC_FEATURES, area="laravel-commands")
    package.add_rendered(
        "backend/app/Console/Commands/BackupDatabase.php",
        COMMAND_BACKUP,
        area="laravel-commands",
        backup_cron=settings.get("backup_cron", "0 2 * * *"),
        backup_keep_days=int(settings.get("backup_keep_days", 30)),
    )
    package.add("backend/app/Console/Commands/AiHealth.php", COMMAND_AI_HEALTH, area="laravel-commands")

    # -- بازنویسی مدل کاربر -------------------------------------------------- #
    user_entity = next((e for e in entities if e["table"] == "users"), None)
    if user_entity is not None:
        package.add_rendered(
            "backend/app/Models/System/User.php",
            USER_MODEL_TEMPLATE,
            area="laravel-models",
            fillable=_user_fillable(user_entity),
            casts=_user_casts(user_entity),
        )
        package.add(
            "backend/database/factories/System/UserFactory.php",
            USER_FACTORY_TEMPLATE,
            area="laravel-factories",
        )

    # -- config/features.php ------------------------------------------------- #
    features_payload = {}
    for order, item in enumerate(catalog_items):
        features_payload[item["code"]] = {
            "title": item["name"],
            "section_code": item["section_code"],
            "module_code": item["module_code"],
            "group_code": item.get("group_code") or item["module_code"],
            "feature_level": item.get("level", "item"),
            "is_ai": bool(item.get("ai")),
            "ai_engine": item.get("engine"),
            "license_scope": "standard",
            "enabled": True,
            "sort_order": order,
            "config": {
                "dependencies": item.get("deps", []),
                "roles": item.get("roles", []),
                "entity_table": item.get("entity"),
                "sort_order": order,
                "module_name": item.get("module_name", ""),
                "group_name": item.get("group_name", ""),
                "section_name": item.get("section_name", ""),
            },
        }
    package.add(
        "backend/config/features.php",
        "<?php\n\n/**\n * رجیستری قابلیت‌های فعال این استقرار\n *\n"
        " * منبع: کاتالوگ سازنده ERP — "
        f"{len(features_payload)} زیرمجموعه\n */\n\nreturn "
        + php_array({"items": features_payload}, level=0)
        + ";\n",
        area="laravel-config",
    )

    # -- config/reports.php (قالب‌های گزارش آماده) --------------------------- #
    if bool(settings.get("include_report_templates", True)):
        package.add(
            "backend/config/reports.php",
            build_reports_config(modules, entities, context=context),
            area="laravel-config",
        )
