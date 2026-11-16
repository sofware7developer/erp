# -*- coding: utf-8 -*-
"""
تولید اسکلت پروژه لاراول ۱۱
=============================
فایل‌های زیرساختی: composer.json، artisan، bootstrap، config، .env، phpunit،
public، Dockerfile و لایه‌های پشتیبانی (Jalali، PersianText، AvalAiClient،
AiServiceClient، ActivityLogger، Middleware، Provider، Command).

همه چیز خودکفاست: هیچ پکیج جانبی غیر از هسته لاراول و Sanctum لازم نیست.
"""

from __future__ import annotations

import json
from typing import Any

from .writers import Package, php_array, render

# --------------------------------------------------------------------------- #
# composer.json
# --------------------------------------------------------------------------- #
def build_composer(settings: dict[str, Any], project_slug: str) -> str:
    require = {
        "php": "^8.2",
        "ext-json": "*",
        "ext-mbstring": "*",
        "ext-openssl": "*",
        "laravel/framework": "^11.9",
        "laravel/sanctum": "^4.0",
        "laravel/tinker": "^2.9",
        "guzzlehttp/guzzle": "^7.8",
    }
    if "redis" in (str(settings.get("queue_driver", "")) + str(settings.get("cache_driver", ""))):
        require["predis/predis"] = "^2.2"
    if settings.get("db_driver") == "mysql":
        require["ext-pdo_mysql"] = "*"
    elif settings.get("db_driver") == "pgsql":
        require["ext-pdo_pgsql"] = "*"

    require_dev = {
        "fakerphp/faker": "^1.23",
        "laravel/pint": "^1.15",
        "mockery/mockery": "^1.6",
        "nunomaduro/collision": "^8.1",
        "phpunit/phpunit": "^11.0",
    }

    payload = {
        "name": f"erp/{project_slug}",
        "type": "project",
        "description": settings.get(
            "project_description",
            "سامانه برنامه‌ریزی منابع سازمانی کارخانه — تولیدشده با سازنده ERP هوشمند",
        ),
        "keywords": ["erp", "laravel", "manufacturing", "iran", "jalali", "ai"],
        "license": "MIT",
        "require": require,
        "require-dev": require_dev,
        "autoload": {
            "psr-4": {
                "App\\": "app/",
                "Database\\Factories\\": "database/factories/",
                "Database\\Seeders\\": "database/seeders/",
            },
            "files": ["app/Support/helpers.php"],
        },
        "autoload-dev": {"psr-4": {"Tests\\": "tests/"}},
        "scripts": {
            "post-autoload-dump": [
                "Illuminate\\Foundation\\ComposerScripts::postAutoloadDump",
                "@php artisan package:discover --ansi",
            ],
            "post-update-cmd": ["@php artisan vendor:publish --tag=laravel-assets --ansi --force"],
            "post-root-package-install": ["@php -r \"file_exists('.env') || copy('.env.example', '.env');\""],
            "post-create-project-cmd": ["@php artisan key:generate --ansi"],
            "test": ["@php artisan test"],
            "lint": ["./vendor/bin/pint"],
        },
        "extra": {"laravel": {"dont-discover": []}},
        "config": {
            "optimize-autoloader": True,
            "preferred-install": "dist",
            "sort-packages": True,
            "allow-plugins": {"pestphp/pest-plugin": True, "php-http/discovery": True},
        },
        "minimum-stability": "stable",
        "prefer-stable": True,
    }
    return json.dumps(payload, ensure_ascii=False, indent=4) + "\n"


# --------------------------------------------------------------------------- #
# bootstrap و مسیرها
# --------------------------------------------------------------------------- #
ARTISAN = """#!/usr/bin/env php
<?php

use Symfony\\Component\\Console\\Input\\ArgvInput;

define('LARAVEL_START', microtime(true));

require __DIR__.'/vendor/autoload.php';

$status = (require_once __DIR__.'/bootstrap/app.php')
    ->handleCommand(new ArgvInput);

exit($status);
"""

BOOTSTRAP_APP = """<?php

use App\\Http\\Middleware\\AuditRequestMiddleware;
use App\\Http\\Middleware\\EnsureApiJsonResponse;
use App\\Http\\Middleware\\EnsureCompanyContext;
use App\\Http\\Middleware\\NormalizePersianInput;
use Illuminate\\Foundation\\Application;
use Illuminate\\Foundation\\Configuration\\Exceptions;
use Illuminate\\Foundation\\Configuration\\Middleware;
use Illuminate\\Http\\Request;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
        apiPrefix: 'api',
    )
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->trustProxies(at: '*');

        $middleware->validateCsrfTokens(except: ['api/*', 'sanctum/csrf-cookie']);

        $middleware->web(append: [
            \\Illuminate\\Http\\Middleware\\HandleCors::class,
        ]);

        $middleware->api(prepend: [
            EnsureApiJsonResponse::class,
            NormalizePersianInput::class,
        ], append: [
            EnsureCompanyContext::class,
            AuditRequestMiddleware::class,
        ]);

        $middleware->alias([
            'permission' => \\App\\Http\\Middleware\\CheckPermission::class,
            'company' => EnsureCompanyContext::class,
        ]);

        $middleware->throttleApi('120,1');
    })
    ->withExceptions(function (Exceptions $exceptions) {
        $exceptions->respond(function ($response, Throwable $e, Request $request) {
            if (!$request->is('api/*')) {
                return $response;
            }

            $status = method_exists($e, 'getStatusCode') ? (int) $e->getStatusCode() : 500;

            return response()->json([
                'message' => $e->getMessage() ?: 'خطای نامشخص در پردازش درخواست',
                'status' => $status,
                'trace_id' => request()->header('X-Request-Id', uniqid('erp_')),
            ], $status ?: 500);
        });
    })
    ->create();
"""

BOOTSTRAP_PROVIDERS = """<?php

return [
    App\\Providers\\AppServiceProvider::class,
    App\\Providers\\PolicyServiceProvider::class,
    App\\Providers\\EventServiceProvider::class,
];
"""

# --------------------------------------------------------------------------- #
# فایل‌های config
# --------------------------------------------------------------------------- #
CONFIG_APP = """<?php

return [
    'name' => env('APP_NAME', '@@app_name@@'),
    'name_fa' => env('APP_NAME_FA', '@@app_name_fa@@'),
    'env' => env('APP_ENV', 'production'),
    'debug' => (bool) env('APP_DEBUG', false),
    'url' => env('APP_URL', 'http://localhost'),
    'asset_url' => env('ASSET_URL'),
    'timezone' => env('APP_TIMEZONE', '@@timezone@@'),
    'locale' => env('APP_LOCALE', 'fa'),
    'fallback_locale' => env('APP_FALLBACK_LOCALE', 'en'),
    'faker_locale' => env('APP_FAKER_LOCALE', 'fa_IR'),
    'calendar' => env('APP_CALENDAR', '@@calendar@@'),
    'cipher' => 'AES-256-CBC',
    'key' => env('APP_KEY'),
    'previous_keys' => [
        ...array_filter((array) env('APP_PREVIOUS_KEYS', '')),
    ],
    'maintenance' => [
        'driver' => env('APP_MAINTENANCE_DRIVER', 'file'),
        'store' => env('APP_MAINTENANCE_STORE', 'database'),
    ],
    'version' => env('APP_VERSION', '@@version@@'),
    'build_id' => env('BUILD_ID', '@@build_id@@'),
];
"""

CONFIG_AUTH = """<?php

return [
    'defaults' => [
        'guard' => env('AUTH_GUARD', 'web'),
        'passwords' => env('AUTH_PASSWORD_BROKER', 'users'),
    ],

    'guards' => [
        'web' => [
            'driver' => 'session',
            'provider' => 'users',
        ],
        'api' => [
            'driver' => 'sanctum',
            'provider' => 'users',
        ],
    ],

    'providers' => [
        'users' => [
            'driver' => 'eloquent',
            'model' => env('AUTH_MODEL', App\\Models\\System\\User::class),
        ],
    ],

    'passwords' => [
        'users' => [
            'provider' => 'users',
            'table' => env('AUTH_PASSWORD_RESET_TOKEN_TABLE', 'password_reset_tokens'),
            'expire' => 60,
            'throttle' => 60,
        ],
    ],

    'password_timeout' => env('AUTH_PASSWORD_TIMEOUT', 10800),
];
"""

CONFIG_DATABASE = """<?php

use Illuminate\\Support\\Str;

return [
    'default' => env('DB_CONNECTION', '@@db_driver@@'),

    'connections' => [
        'sqlite' => [
            'driver' => 'sqlite',
            'url' => env('DB_URL'),
            'database' => env('DB_DATABASE', database_path('database.sqlite')),
            'prefix' => '',
            'foreign_key_constraints' => env('DB_FOREIGN_KEYS', true),
        ],

        'mysql' => [
            'driver' => 'mysql',
            'url' => env('DB_URL'),
            'host' => env('DB_HOST', '127.0.0.1'),
            'port' => env('DB_PORT', '3306'),
            'database' => env('DB_DATABASE', '@@db_database@@'),
            'username' => env('DB_USERNAME', '@@db_username@@'),
            'password' => env('DB_PASSWORD', ''),
            'unix_socket' => env('DB_SOCKET', ''),
            'charset' => env('DB_CHARSET', 'utf8mb4'),
            'collation' => env('DB_COLLATION', 'utf8mb4_unicode_ci'),
            'prefix' => '',
            'prefix_indexes' => true,
            'strict' => true,
            'engine' => 'InnoDB',
            'options' => extension_loaded('pdo_mysql') ? array_filter([
                PDO::MYSQL_ATTR_SSL_CA => env('MYSQL_ATTR_SSL_CA'),
            ]) : [],
        ],

        'mariadb' => [
            'driver' => 'mariadb',
            'url' => env('DB_URL'),
            'host' => env('DB_HOST', '127.0.0.1'),
            'port' => env('DB_PORT', '3306'),
            'database' => env('DB_DATABASE', '@@db_database@@'),
            'username' => env('DB_USERNAME', '@@db_username@@'),
            'password' => env('DB_PASSWORD', ''),
            'charset' => env('DB_CHARSET', 'utf8mb4'),
            'collation' => env('DB_COLLATION', 'utf8mb4_unicode_ci'),
            'prefix' => '',
            'prefix_indexes' => true,
            'strict' => true,
            'engine' => 'InnoDB',
        ],

        'pgsql' => [
            'driver' => 'pgsql',
            'url' => env('DB_URL'),
            'host' => env('DB_HOST', '127.0.0.1'),
            'port' => env('DB_PORT', '5432'),
            'database' => env('DB_DATABASE', '@@db_database@@'),
            'username' => env('DB_USERNAME', '@@db_username@@'),
            'password' => env('DB_PASSWORD', ''),
            'charset' => env('DB_CHARSET', 'utf8'),
            'prefix' => '',
            'prefix_indexes' => true,
            'search_path' => 'public',
            'sslmode' => 'prefer',
        ],

        'sqlsrv' => [
            'driver' => 'sqlsrv',
            'url' => env('DB_URL'),
            'host' => env('DB_HOST', 'localhost'),
            'port' => env('DB_PORT', '1433'),
            'database' => env('DB_DATABASE', '@@db_database@@'),
            'username' => env('DB_USERNAME', '@@db_username@@'),
            'password' => env('DB_PASSWORD', ''),
            'charset' => env('DB_CHARSET', 'utf8'),
            'prefix' => '',
            'prefix_indexes' => true,
            'encrypt' => env('DB_ENCRYPT', 'yes'),
            'trust_server_certificate' => env('DB_TRUST_SERVER_CERTIFICATE', 'false'),
        ],
    ],

    'migrations' => [
        'table' => 'migrations',
        'update_date_on_publish' => true,
    ],

    'redis' => [
        'client' => env('REDIS_CLIENT', 'phpredis'),
        'options' => [
            'cluster' => env('REDIS_CLUSTER', 'redis'),
            'prefix' => env('REDIS_PREFIX', Str::slug(env('APP_NAME', 'erp'), '_').'_database_'),
        ],
        'default' => [
            'url' => env('REDIS_URL'),
            'host' => env('REDIS_HOST', '127.0.0.1'),
            'username' => env('REDIS_USERNAME'),
            'password' => env('REDIS_PASSWORD'),
            'port' => env('REDIS_PORT', '6379'),
            'database' => env('REDIS_DB', '0'),
        ],
        'cache' => [
            'url' => env('REDIS_URL'),
            'host' => env('REDIS_HOST', '127.0.0.1'),
            'username' => env('REDIS_USERNAME'),
            'password' => env('REDIS_PASSWORD'),
            'port' => env('REDIS_PORT', '6379'),
            'database' => env('REDIS_CACHE_DB', '1'),
        ],
    ],
];
"""

CONFIG_CACHE = """<?php

use Illuminate\\Support\\Str;

return [
    'default' => env('CACHE_STORE', '@@cache_driver@@'),

    'stores' => [
        'array' => [
            'driver' => 'array',
            'serialize' => false,
        ],
        'database' => [
            'driver' => 'database',
            'table' => env('DB_CACHE_TABLE', 'cache'),
            'connection' => env('DB_CACHE_CONNECTION'),
            'lock_connection' => env('DB_CACHE_LOCK_CONNECTION'),
        ],
        'file' => [
            'driver' => 'file',
            'path' => storage_path('framework/cache/data'),
            'lock_path' => storage_path('framework/cache/data'),
        ],
        'redis' => [
            'driver' => 'redis',
            'connection' => env('REDIS_CACHE_CONNECTION', 'cache'),
            'lock_connection' => env('REDIS_CACHE_LOCK_CONNECTION', 'default'),
        ],
    ],

    'prefix' => env('CACHE_PREFIX', Str::slug(env('APP_NAME', 'erp'), '_').'_cache_'),
];
"""

CONFIG_QUEUE = """<?php

return [
    'default' => env('QUEUE_CONNECTION', '@@queue_driver@@'),

    'connections' => [
        'sync' => ['driver' => 'sync'],

        'database' => [
            'driver' => 'database',
            'connection' => env('DB_QUEUE_CONNECTION'),
            'table' => env('DB_QUEUE_TABLE', 'jobs'),
            'queue' => env('DB_QUEUE', 'default'),
            'retry_after' => (int) env('DB_QUEUE_RETRY_AFTER', 90),
            'after_commit' => false,
        ],

        'redis' => [
            'driver' => 'redis',
            'connection' => env('REDIS_QUEUE_CONNECTION', 'default'),
            'queue' => env('REDIS_QUEUE', 'default'),
            'retry_after' => (int) env('REDIS_QUEUE_RETRY_AFTER', 90),
            'block_for' => null,
            'after_commit' => false,
        ],
    ],

    'batching' => [
        'database' => env('DB_CONNECTION', 'sqlite'),
        'table' => 'job_batches',
    ],

    'failed' => [
        'driver' => env('QUEUE_FAILED_DRIVER', 'database-uuids'),
        'database' => env('DB_CONNECTION', 'sqlite'),
        'table' => 'failed_jobs',
    ],
];
"""

CONFIG_FILESYSTEMS = """<?php

return [
    'default' => env('FILESYSTEM_DISK', '@@storage_driver@@'),

    'disks' => [
        'local' => [
            'driver' => 'local',
            'root' => storage_path('app'),
            'throw' => false,
        ],
        'public' => [
            'driver' => 'local',
            'root' => storage_path('app/public'),
            'url' => env('APP_URL').'/storage',
            'visibility' => 'public',
            'throw' => false,
        ],
        'documents' => [
            'driver' => 'local',
            'root' => storage_path('app/documents'),
            'url' => env('APP_URL').'/storage/documents',
            'visibility' => 'private',
            'throw' => false,
        ],
        's3' => [
            'driver' => 's3',
            'key' => env('AWS_ACCESS_KEY_ID'),
            'secret' => env('AWS_SECRET_ACCESS_KEY'),
            'region' => env('AWS_DEFAULT_REGION'),
            'bucket' => env('AWS_BUCKET'),
            'url' => env('AWS_URL'),
            'endpoint' => env('AWS_ENDPOINT'),
            'use_path_style_endpoint' => env('AWS_USE_PATH_STYLE_ENDPOINT', false),
            'throw' => false,
        ],
    ],

    'links' => [
        public_path('storage') => storage_path('app/public'),
    ],
];
"""

CONFIG_LOGGING = """<?php

use Monolog\\Handler\\NullHandler;
use Monolog\\Handler\\StreamHandler;
use Monolog\\Processor\\PsrLogMessageProcessor;

return [
    'default' => env('LOG_CHANNEL', 'stack'),

    'deprecations' => [
        'channel' => env('LOG_DEPRECATIONS_CHANNEL', 'null'),
        'trace' => (bool) env('LOG_DEPRECATIONS_TRACE', false),
    ],

    'channels' => [
        'stack' => [
            'driver' => 'stack',
            'channels' => explode(',', env('LOG_STACK', 'single')),
            'ignore_exceptions' => false,
        ],
        'single' => [
            'driver' => 'single',
            'path' => storage_path('logs/laravel.log'),
            'level' => env('LOG_LEVEL', 'debug'),
            'replace_placeholders' => true,
        ],
        'daily' => [
            'driver' => 'daily',
            'path' => storage_path('logs/laravel.log'),
            'level' => env('LOG_LEVEL', 'debug'),
            'days' => env('LOG_DAILY_DAYS', 14),
            'replace_placeholders' => true,
        ],
        'ai' => [
            'driver' => 'daily',
            'path' => storage_path('logs/ai.log'),
            'level' => 'info',
            'days' => 30,
            'replace_placeholders' => true,
        ],
        'audit' => [
            'driver' => 'daily',
            'path' => storage_path('logs/audit.log'),
            'level' => 'info',
            'days' => 180,
            'replace_placeholders' => true,
        ],
        'stderr' => [
            'driver' => 'monolog',
            'level' => env('LOG_LEVEL', 'debug'),
            'handler' => StreamHandler::class,
            'formatter' => env('LOG_STDERR_FORMATTER'),
            'with' => ['stream' => 'php://stderr'],
            'processors' => [PsrLogMessageProcessor::class],
        ],
        'null' => [
            'driver' => 'monolog',
            'handler' => NullHandler::class,
        ],
        'emergency' => [
            'path' => storage_path('logs/laravel.log'),
        ],
    ],
];
"""

CONFIG_CORS = """<?php

return [
    'paths' => ['api/*', 'sanctum/csrf-cookie'],

    'allowed_methods' => ['*'],

    'allowed_origins' => explode(',', env('CORS_ALLOWED_ORIGINS', '@@cors_origins@@')),

    'allowed_origins_patterns' => [],

    'allowed_headers' => ['*'],

    'exposed_headers' => ['X-Total-Count', 'X-Request-Id'],

    'max_age' => 0,

    'supports_credentials' => true,
];
"""

CONFIG_SANCTUM = """<?php

return [
    'stateful' => explode(',', env('SANCTUM_STATEFUL_DOMAINS', sprintf(
        '%s%s',
        'localhost,localhost:3000,localhost:5173,127.0.0.1,127.0.0.1:8000,::1',
        env('APP_URL') ? ','.parse_url(env('APP_URL'), PHP_URL_HOST) : ''
    ))),

    'guard' => ['web'],

    'expiration' => env('SANCTUM_TOKEN_EXPIRATION', 1440),

    'token_prefix' => env('SANCTUM_TOKEN_PREFIX', '@@slug@@_'),

    'middleware' => [
        'authenticate_session' => Laravel\\Sanctum\\Http\\Middleware\\AuthenticateSession::class,
        'encrypt_cookies' => Illuminate\\Cookie\\Middleware\\EncryptCookies::class,
        'validate_csrf_token' => Illuminate\\Foundation\\Http\\Middleware\\ValidateCsrfToken::class,
    ],
];
"""

CONFIG_SESSION = """<?php

use Illuminate\\Support\\Str;

return [
    'driver' => env('SESSION_DRIVER', 'database'),
    'lifetime' => env('SESSION_LIFETIME', 120),
    'expire_on_close' => env('SESSION_EXPIRE_ON_CLOSE', false),
    'encrypt' => env('SESSION_ENCRYPT', false),
    'files' => storage_path('framework/sessions'),
    'connection' => env('SESSION_CONNECTION'),
    'table' => env('SESSION_TABLE', 'sessions'),
    'store' => env('SESSION_STORE'),
    'lottery' => [2, 100],
    'cookie' => env('SESSION_COOKIE', Str::slug(env('APP_NAME', 'erp'), '_').'_session'),
    'path' => env('SESSION_PATH', '/'),
    'domain' => env('SESSION_DOMAIN'),
    'secure' => env('SESSION_SECURE_COOKIE'),
    'http_only' => env('SESSION_HTTP_ONLY', true),
    'same_site' => env('SESSION_SAME_SITE', 'lax'),
    'partitioned' => env('SESSION_PARTITIONED_COOKIE', false),
];
"""

CONFIG_SERVICES = """<?php

return [
    'postmark' => ['token' => env('POSTMARK_TOKEN')],

    'ses' => [
        'key' => env('AWS_ACCESS_KEY_ID'),
        'secret' => env('AWS_SECRET_ACCESS_KEY'),
        'region' => env('AWS_DEFAULT_REGION', 'us-east-1'),
    ],

    'slack' => [
        'notifications' => [
            'bot_user_oauth_token' => env('SLACK_BOT_USER_OAUTH_TOKEN'),
            'channel' => env('SLACK_BOT_USER_DEFAULT_CHANNEL'),
        ],
    ],

    'avalai' => [
        'key' => env('AVALAI_API_KEY'),
        'base_url' => env('AVALAI_BASE_URL', 'https://api.avalai.ir/v1'),
        'model' => env('AVALAI_MODEL', 'gpt-4o-mini'),
        'timeout' => (int) env('AVALAI_TIMEOUT', 45),
    ],

    'sms' => [
        'driver' => env('SMS_DRIVER', 'log'),
        'api_key' => env('SMS_API_KEY'),
        'sender' => env('SMS_SENDER', '30005005'),
        'base_url' => env('SMS_BASE_URL', 'https://api.sms-provider.ir/v1'),
    ],

    'ai_service' => [
        'base_url' => env('AI_SERVICE_URL', '@@ai_service_url@@'),
        'timeout' => (int) env('AI_SERVICE_TIMEOUT', 30),
        'enabled' => (bool) env('AI_SERVICE_ENABLED', true),
    ],
];
"""

CONFIG_ERP = """<?php

/**
 * پیکربندی اختصاصی کارخانه — از تنظیمات «سازنده ERP» تولید شده است.
 * هر مقدار با متغیر محیطی متناظر قابل بازنویسی است.
 */

return [
    'identity' => [
        'company_name' => env('ERP_COMPANY_NAME', '@@company_name@@'),
        'company_name_en' => env('ERP_COMPANY_NAME_EN', '@@company_name_en@@'),
        'industry' => env('ERP_INDUSTRY', '@@industry@@'),
        'registration_no' => env('ERP_REGISTRATION_NO', '@@registration_no@@'),
        'economic_code' => env('ERP_ECONOMIC_CODE', '@@economic_code@@'),
        'national_id' => env('ERP_NATIONAL_ID', '@@national_id@@'),
        'address' => env('ERP_ADDRESS', '@@address@@'),
        'postal_code' => env('ERP_POSTAL_CODE', '@@postal_code@@'),
        'phone' => env('ERP_PHONE', '@@phone@@'),
    ],

    'operations' => [
        'employees_count' => (int) env('ERP_EMPLOYEES_COUNT', @@employees_count@@),
        'shifts_per_day' => (int) env('ERP_SHIFTS_PER_DAY', @@shifts_per_day@@),
        'production_lines' => (int) env('ERP_PRODUCTION_LINES', @@production_lines@@),
        'warehouses_count' => (int) env('ERP_WAREHOUSES_COUNT', @@warehouses_count@@),
    ],

    'localization' => [
        'currency' => env('ERP_CURRENCY', '@@currency@@'),
        'currency_label' => env('ERP_CURRENCY_LABEL', '@@currency_label@@'),
        'calendar' => env('ERP_CALENDAR', '@@calendar@@'),
        'timezone' => env('ERP_TIMEZONE', '@@timezone@@'),
        'week_start' => env('ERP_WEEK_START', '@@week_start@@'),
        'weekend_days' => @@weekend_days@@,
        'language' => env('ERP_LANGUAGE', 'fa'),
    ],

    'accounting' => [
        'fiscal_year_start_month' => (int) env('ERP_FISCAL_YEAR_START_MONTH', @@fiscal_start@@),
        'tax_rate_default' => (float) env('ERP_TAX_RATE_DEFAULT', @@tax_rate@@),
        'moadian_enabled' => (bool) env('ERP_MOADIAN_ENABLED', @@moadian_enabled@@),
        'costing_method' => env('ERP_COSTING_METHOD', '@@costing_method@@'),
    ],

    'modules' => [
        // فهرست ماژول‌های فعال در این استقرار
        'enabled' => @@enabled_modules@@,

        // ماژول‌های همیشه فعال (هسته سامانه)
        'system' => @@system_modules@@,

        // تعداد زیرمجموعه‌های فعال هر ماژول
        'items_count' => (int) @@items_count@@,
    ],

    'ai' => [
        'enabled' => (bool) env('ERP_AI_ENABLED', @@ai_enabled@@),
        'engines' => @@ai_engines@@,
        'capabilities' => @@ai_capabilities@@,
        'service_url' => env('AI_SERVICE_URL', '@@ai_service_url@@'),
        'require_human_approval' => (bool) env('ERP_AI_HUMAN_APPROVAL', @@ai_human_approval@@),
        'explainability' => (bool) env('ERP_AI_EXPLAINABILITY', true),
    ],

    'iot' => [
        'enabled' => (bool) env('ERP_IOT_ENABLED', @@iot_enabled@@),
        'mqtt_host' => env('MQTT_HOST', '@@mqtt_host@@'),
        'mqtt_port' => (int) env('MQTT_PORT', @@mqtt_port@@),
        'mqtt_topic_prefix' => env('MQTT_TOPIC_PREFIX', '@@mqtt_topic@@'),
        'sampling_seconds' => (int) env('IOT_SAMPLING_SECONDS', @@sampling_seconds@@),
    ],

    'backup' => [
        'cron' => env('ERP_BACKUP_CRON', '@@backup_cron@@'),
        'keep_days' => (int) env('ERP_BACKUP_KEEP_DAYS', @@backup_keep_days@@),
        'disk' => env('ERP_BACKUP_DISK', '@@backup_disk@@'),
    ],

    'mail' => [
        'from_address' => env('MAIL_FROM_ADDRESS', '@@mail_from@@'),
        'from_name' => env('MAIL_FROM_NAME', '@@mail_from_name@@'),
    ],

    'build' => [
        'generator_version' => '@@generator_version@@',
        'catalog_version' => '@@catalog_version@@',
        'generated_at' => '@@generated_at@@',
        'package_id' => '@@package_id@@',
        'preset' => '@@preset@@',
        'deploy_target' => '@@deploy_target@@',
    ],
];
"""

CONFIG_AI_ENGINES = """<?php

/**
 * رجیستری موتورهای هوش مصنوعی این استقرار.
 *
 * هر موتور یک اندپوینت در سرویس پایتون (ai-service) دارد و لاراول از طریق
 * `App\\Support\\AiServiceClient` آن را صدا می‌زند. اگر سرویس در دسترس نبود،
 * پاسخ fallback (قاعده‌محور) برگردانده می‌شود و جریان کاری متوقف نمی‌شود.
 */

return [
    'default_timeout' => (int) env('AI_TIMEOUT', 30),
    'fallback_enabled' => (bool) env('AI_FALLBACK_ENABLED', true),
    'log_predictions' => (bool) env('AI_LOG_PREDICTIONS', true),
    'log_channel' => 'ai',

    'engines' => @@engines_array@@,

    // نگاشت نقطه هوش مصنوعی (کد کاتالوگ) به موتور و مدل
    'capabilities' => @@capabilities_array@@,

    'llm' => [
        'provider' => env('AI_LLM_PROVIDER', 'avalai'),
        'model' => env('AVALAI_MODEL', '@@llm_model@@'),
        'temperature' => (float) env('AI_LLM_TEMPERATURE', 0.2),
        'max_tokens' => (int) env('AI_LLM_MAX_TOKENS', 1200),
        'persian_only' => true,
    ],
];
"""

# --------------------------------------------------------------------------- #
# محیط و تست
# --------------------------------------------------------------------------- #
ENV_TEMPLATE = """APP_NAME="@@app_name@@"
APP_NAME_FA="@@app_name_fa@@"
APP_ENV=production
APP_KEY=
APP_DEBUG=false
APP_TIMEZONE=@@timezone@@
APP_LOCALE=fa
APP_CALENDAR=@@calendar@@
APP_URL=@@app_url@@
APP_VERSION=@@version@@
BUILD_ID=@@build_id@@

APP_LOCALE=fa
APP_FALLBACK_LOCALE=en
APP_FAKER_LOCALE=fa_IR

LOG_CHANNEL=daily
LOG_STACK=single
LOG_DEPRECATIONS_CHANNEL=null
LOG_LEVEL=info

DB_CONNECTION=@@db_driver@@
DB_HOST=@@db_host@@
DB_PORT=@@db_port@@
DB_DATABASE=@@db_database@@
DB_USERNAME=@@db_username@@
DB_PASSWORD=@@db_password@@

SESSION_DRIVER=@@session_driver@@
SESSION_LIFETIME=120
SESSION_ENCRYPT=false
QUEUE_CONNECTION=@@queue_driver@@
CACHE_STORE=@@cache_driver@@
FILESYSTEM_DISK=@@storage_driver@@
REDIS_HOST=@@redis_host@@
REDIS_PORT=6379

BROADCAST_CONNECTION=log
MAIL_MAILER=@@mail_driver@@
MAIL_HOST=@@mail_host@@
MAIL_PORT=@@mail_port@@
MAIL_USERNAME=@@mail_username@@
MAIL_PASSWORD=@@mail_password@@
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=@@mail_from@@
MAIL_FROM_NAME=@@mail_from_name@@

SANCTUM_STATEFUL_DOMAINS=@@stateful_domains@@
CORS_ALLOWED_ORIGINS=@@cors_origins@@

# --- هویت کارخانه ---
ERP_COMPANY_NAME="@@company_name@@"
ERP_COMPANY_NAME_EN="@@company_name_en@@"
ERP_INDUSTRY="@@industry@@"
ERP_ECONOMIC_CODE="@@economic_code@@"
ERP_NATIONAL_ID="@@national_id@@"
ERP_CURRENCY=@@currency@@
ERP_AI_ENABLED=true
ERP_AI_HUMAN_APPROVAL=true
ERP_IOT_ENABLED=@@iot_enabled@@

# --- سرویس هوش مصنوعی ---
AI_SERVICE_URL=@@ai_service_url@@
AI_SERVICE_ENABLED=true
AI_TIMEOUT=30
AI_FALLBACK_ENABLED=true

# --- AvalAI (اختیاری — برای قابلیت‌های زبانی) ---
AVALAI_API_KEY=@@avalai_key@@
AVALAI_BASE_URL=@@avalai_base_url@@
AVALAI_MODEL=@@avalai_model@@

# --- IoT / MQTT ---
MQTT_HOST=@@mqtt_host@@
MQTT_PORT=@@mqtt_port@@
MQTT_TOPIC_PREFIX=@@mqtt_topic@@
IOT_SAMPLING_SECONDS=@@sampling_seconds@@

# --- پیامک ---
SMS_DRIVER=log
SMS_API_KEY=
SMS_SENDER=30005005

# --- مدیر اولیه ---
ERP_ADMIN_NAME="@@admin_name@@"
ERP_ADMIN_EMAIL=@@admin_email@@
ERP_ADMIN_PASSWORD=@@admin_password@@

# --- پشتیبان‌گیری ---
ERP_BACKUP_CRON="@@backup_cron@@"
ERP_BACKUP_KEEP_DAYS=@@backup_keep_days@@
ERP_BACKUP_DISK=@@backup_disk@@

VITE_APP_NAME="${APP_NAME}"
VITE_API_URL="${APP_URL}/api"
VITE_APP_LOCALE=fa
VITE_APP_DIR=rtl
"""

PHPUNIT = """<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="vendor/autoload.php"
         colors="true"
>
    <testsuites>
        <testsuite name="Unit">
            <directory>tests/Unit</directory>
        </testsuite>
        <testsuite name="Feature">
            <directory>tests/Feature</directory>
        </testsuite>
    </testsuites>
    <source>
        <include>
            <directory>app</directory>
        </include>
    </source>
    <php>
        <env name="APP_ENV" value="testing"/>
        <env name="APP_MAINTENANCE_DRIVER" value="file"/>
        <env name="BCRYPT_ROUNDS" value="4"/>
        <env name="CACHE_STORE" value="array"/>
        <env name="DB_CONNECTION" value="sqlite"/>
        <env name="DB_DATABASE" value=":memory:"/>
        <env name="MAIL_MAILER" value="array"/>
        <env name="QUEUE_CONNECTION" value="sync"/>
        <env name="SESSION_DRIVER" value="array"/>
        <env name="AI_SERVICE_ENABLED" value="false"/>
    </php>
</phpunit>
"""

TESTCASE = """<?php

namespace Tests;

use Illuminate\\Foundation\\Testing\\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    protected function setUp(): void
    {
        parent::setUp();

        $this->withoutVite();
    }
}
"""

UNIT_TEST_JALALI = """<?php

namespace Tests\\Unit;

use App\\Support\\Jalali;
use App\\Support\\PersianText;
use PHPUnit\\Framework\\TestCase;

/**
 * آزمون واحد تبدیل تاریخ شمسی و نرمال‌سازی متن فارسی
 */
class JalaliTest extends TestCase
{
    public function test_converts_gregorian_to_jalali(): void
    {
        $result = Jalali::toJalali(2026, 3, 21);

        $this->assertSame(1405, $result['year']);
        $this->assertSame(1, $result['month']);
        $this->assertSame(1, $result['day']);
    }

    public function test_converts_jalali_to_gregorian(): void
    {
        $result = Jalali::toGregorian(1405, 1, 1);

        $this->assertSame(2026, $result['year']);
        $this->assertSame(3, $result['month']);
        $this->assertSame(21, $result['day']);
    }

    public function test_formats_persian_date_string(): void
    {
        $date = new \\DateTimeImmutable('2026-03-21');

        $this->assertMatchesRegularExpression('/^\\d{4}\\/\\d{2}\\/\\d{2}$/', Jalali::format($date));
    }

    public function test_normalizes_persian_digits(): void
    {
        $this->assertSame('1234', PersianText::toLatinDigits('۱۲۳۴'));
        $this->assertSame('1234', PersianText::toLatinDigits('١٢٣٤'));
        $this->assertSame(1234, PersianText::toNumber('۱,۲۳۴'));
    }

    public function test_normalizes_arabic_characters(): void
    {
        $this->assertSame('یک نمونه', PersianText::normalize('يك نمونة'));
    }
}
"""

PUBLIC_INDEX = """<?php

use Illuminate\\Http\\Request;

define('LARAVEL_START', microtime(true));

// تعیین وضعیت تعمیرات
if (file_exists($maintenance = __DIR__.'/../storage/framework/maintenance.php')) {
    require $maintenance;
}

require __DIR__.'/../vendor/autoload.php';

/** @var Application $app */
$app = require_once __DIR__.'/../bootstrap/app.php';

$app->handleRequest(Request::capture());
"""

PUBLIC_HTACCESS = """<IfModule mod_rewrite.c>
    <IfModule mod_negotiation.c>
        Options -MultiViews -Indexes
    </IfModule>

    RewriteEngine On

    # مدیریت احراز هویت HTTP
    RewriteCond %{HTTP:Authorization} .
    RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]

    # هدایت اسلش انتهایی
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteCond %{REQUEST_URI} (.+)/$
    RewriteRule ^ %1 [L,R=301]

    # ارسال همه درخواست‌ها به index.php
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^ index.php [L]
</IfModule>

<IfModule mod_headers.c>
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
"""

DOCKERFILE_BACKEND = """# syntax=docker/dockerfile:1
FROM php:8.3-fpm-alpine AS base

ARG APP_ENV=production

WORKDIR /var/www/html

RUN apk add --no-cache \\
        bash \\
        git \\
        unzip \\
        icu-dev \\
        libzip-dev \\
        oniguruma-dev \\
        freetype-dev \\
        libjpeg-turbo-dev \\
        libpng-dev \\
        postgresql-dev \\
        sqlite-dev \\
        tzdata \\
    && docker-php-ext-configure gd --with-freetype --with-jpeg \\
    && docker-php-ext-install -j"$(nproc)" \\
        bcmath \\
        gd \\
        intl \\
        mbstring \\
        opcache \\
        pcntl \\
        pdo_mysql \\
        pdo_pgsql \\
        pdo_sqlite \\
        zip \\
    && cp /usr/share/zoneinfo/@@timezone@@ /etc/localtime \\
    && echo "@@timezone@@" > /etc/timezone

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

COPY composer.json composer.lock* ./
RUN composer install --no-dev --no-scripts --no-autoloader --prefer-dist --no-interaction || true

COPY . .
RUN composer dump-autoload --optimize || true

RUN mkdir -p storage/app/public storage/logs storage/framework/cache/data \\
        storage/framework/sessions storage/framework/views bootstrap/cache \\
    && chown -R www-data:www-data storage bootstrap/cache

EXPOSE 9000

CMD ["php-fpm"]
"""

DOCKERFILE_NGINX = """FROM nginx:1.27-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY deploy/nginx/erp.conf /etc/nginx/conf.d/erp.conf
COPY --from=backend /var/www/html/public /var/www/html/public

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""


def _php_list(values: list[str]) -> str:
    return "[" + ", ".join(f"'{v}'" for v in values) + "]"


def generate_core_files(
    package: Package,
    *,
    settings: dict[str, Any],
    modules: list[dict[str, Any]],
    ai_engines: list[dict[str, Any]],
    ai_points: list[dict[str, Any]],
    context: dict[str, Any],
) -> None:
    """نوشتن فایل‌های زیرساختی لاراول در بسته."""
    slug = context["slug"]
    db_driver = settings.get("db_driver", "sqlite")
    db_ports = {"mysql": "3306", "mariadb": "3306", "pgsql": "5432", "sqlite": "", "sqlsrv": "1433"}

    common = {
        "app_name": settings.get("app_name", slug),
        "app_name_fa": settings.get("app_name_fa", context["app_name_fa"]),
        "version": context["version"],
        "build_id": context["package_id"],
        "timezone": settings.get("timezone", "Asia/Tehran"),
        "calendar": settings.get("calendar", "jalali"),
        "db_driver": db_driver,
        "db_host": "db" if db_driver != "sqlite" else "localhost",
        "db_port": db_ports.get(db_driver, "3306"),
        "db_database": settings.get("db_database", slug),
        "db_username": settings.get("db_username", slug),
        "db_password": settings.get("db_password", ""),
        "redis_host": settings.get("redis_host", "redis"),
        "cache_driver": settings.get("cache_driver", "database"),
        "queue_driver": settings.get("queue_driver", "database"),
        "session_driver": settings.get("session_driver", "database"),
        # کلید متعارف storage_disk است؛ storage_driver فقط برای سازگاری عقب‌رو
        "storage_driver": settings.get("storage_disk") or settings.get("storage_driver", "local"),
        "mail_driver": settings.get("mail_driver", "smtp"),
        "mail_host": settings.get("mail_host", "smtp.example.com"),
        "mail_port": str(settings.get("mail_port", 587)),
        "mail_username": settings.get("mail_username", ""),
        "mail_password": settings.get("mail_password", ""),
        "mail_from": settings.get("mail_from", "erp@example.com"),
        "mail_from_name": settings.get("mail_from_name", settings.get("company_name", slug)),
        "cors_origins": settings.get("cors_origins", context["preview_origin"]),
        "stateful_domains": settings.get("stateful_domains", "localhost:5173,localhost:3000"),
        "app_url": settings.get("app_url", context["app_url"]),
        "slug": slug,
        "company_name": settings.get("company_name", ""),
        "company_name_en": settings.get("company_name_en", ""),
        "industry": settings.get("industry", "general"),
        "registration_no": settings.get("registration_no", ""),
        "economic_code": settings.get("economic_code", ""),
        "national_id": settings.get("company_national_id", ""),
        "address": settings.get("address", ""),
        "postal_code": settings.get("postal_code", ""),
        "phone": settings.get("phone", ""),
        "employees_count": int(settings.get("employees_count", 150)),
        "shifts_per_day": int(settings.get("shifts_per_day", 2)),
        "production_lines": int(settings.get("production_lines", 3)),
        "warehouses_count": int(settings.get("warehouses_count", 2)),
        "currency": settings.get("currency", "IRR"),
        "currency_label": settings.get("currency_label", "ریال"),
        "week_start": settings.get("week_start", "saturday"),
        "weekend_days": _php_list(settings.get("weekend_days", ["friday"])),
        "fiscal_start": int(settings.get("fiscal_year_start_month", 1)),
        "tax_rate": float(settings.get("tax_rate_default", 0.10)),
        "moadian_enabled": "true" if settings.get("moadian_enabled", True) else "false",
        "costing_method": settings.get("costing_method", "weighted_average"),
        "enabled_modules": _php_list([m["code"] for m in modules]),
        "system_modules": _php_list(context["system_modules"]),
        "items_count": context["counts"]["items"],
        "ai_enabled": "true" if settings.get("ai_enabled", True) else "false",
        "ai_human_approval": "true" if settings.get("ai_human_approval", True) else "false",
        "ai_engines": _php_list([e["key"] for e in ai_engines]),
        "ai_capabilities": len(ai_points),
        "ai_service_url": settings.get("ai_service_url", "http://ai-service:8001"),
        "iot_enabled": "true" if settings.get("iot_enabled", False) else "false",
        "mqtt_host": settings.get("mqtt_host", "mqtt"),
        "mqtt_port": int(settings.get("mqtt_port", 1883)),
        "mqtt_topic": settings.get("mqtt_topic_prefix", f"erp/{slug}"),
        "sampling_seconds": int(settings.get("iot_sampling_seconds", 30)),
        "backup_cron": settings.get("backup_cron", "0 2 * * *"),
        "backup_keep_days": int(settings.get("backup_keep_days", 30)),
        "backup_disk": settings.get("backup_disk", "local"),
        "admin_name": settings.get("admin_name", "مدیر سامانه"),
        "admin_email": settings.get("admin_email", "admin@example.com"),
        "admin_password": settings.get("admin_password", "ChangeMe!1405"),
        "avalai_key": settings.get("avalai_api_key", ""),
        "avalai_base_url": settings.get("avalai_base_url", "https://api.avalai.ir/v1"),
        "avalai_model": settings.get("avalai_model", "gpt-4o-mini"),
        "llm_model": settings.get("avalai_model", "gpt-4o-mini"),
        "generator_version": context["version"],
        "catalog_version": context["catalog_version"],
        "generated_at": context["generated_at"],
        "package_id": context["package_id"],
        "preset": context.get("preset") or "custom",
        "deploy_target": settings.get("deploy_target", "docker"),
    }

    package.add("backend/composer.json", build_composer(settings, slug), area="laravel-config")
    package.add("backend/artisan", ARTISAN, area="laravel-core", executable=True)
    package.add_rendered("backend/bootstrap/app.php", BOOTSTRAP_APP, area="laravel-core")
    package.add("backend/bootstrap/providers.php", BOOTSTRAP_PROVIDERS, area="laravel-core")
    package.add_rendered("backend/.env.example", ENV_TEMPLATE, area="laravel-config", **common)
    package.add_rendered("backend/.env", ENV_TEMPLATE, area="laravel-config", **common)
    package.add("backend/phpunit.xml", PHPUNIT, area="laravel-tests")
    package.add("backend/tests/TestCase.php", TESTCASE, area="laravel-tests")
    package.add("backend/tests/Unit/JalaliTest.php", UNIT_TEST_JALALI, area="laravel-tests")
    package.add("backend/public/index.php", PUBLIC_INDEX, area="laravel-core")
    package.add("backend/public/.htaccess", PUBLIC_HTACCESS, area="laravel-core")
    package.add("backend/public/robots.txt", "User-agent: *\nDisallow: /api/\n", area="laravel-core")
    package.add_rendered("backend/Dockerfile", DOCKERFILE_BACKEND, area="deploy", **common)
    package.add("deploy/docker/nginx.Dockerfile", DOCKERFILE_NGINX, area="deploy")

    # فایل‌های config
    config_map = {
        "app": CONFIG_APP,
        "auth": CONFIG_AUTH,
        "database": CONFIG_DATABASE,
        "cache": CONFIG_CACHE,
        "queue": CONFIG_QUEUE,
        "filesystems": CONFIG_FILESYSTEMS,
        "logging": CONFIG_LOGGING,
        "cors": CONFIG_CORS,
        "sanctum": CONFIG_SANCTUM,
        "session": CONFIG_SESSION,
        "services": CONFIG_SERVICES,
        "erp": CONFIG_ERP,
    }
    for name, template in config_map.items():
        package.add_rendered(f"backend/config/{name}.php", template, area="laravel-config", **common)

    # config/ai.php با رجیستری موتورها و قابلیت‌ها
    engines_array = []
    for engine in ai_engines:
        engines_array.append(
            {
                "key": engine["key"],
                "name_fa": engine["name_fa"],
                "endpoint": engine["endpoint"],
                "algorithms": engine["algorithms"],
                "uses_llm": engine["uses_llm"],
                "realtime": engine["realtime"],
                "metrics": engine["metrics"],
            }
        )
    capabilities_array = []
    for point in ai_points:
        capabilities_array.append(
            {
                "code": point["code"],
                "name": point["name"],
                "engine": point["engine"],
                "endpoint": point["endpoint"],
                "model_id": point["model_id"],
                "feature_flag": point["feature_flag"],
                "module": point["module_code"],
                "section": point["section_code"],
            }
        )

    package.add_rendered(
        "backend/config/ai.php",
        CONFIG_AI_ENGINES,
        area="laravel-config",
        engines_array=php_array(engines_array, level=1),
        capabilities_array=php_array(capabilities_array, level=1),
        **common,
    )

    # دایرکتوری‌های ذخیره‌سازی
    for path in (
        "backend/storage/app/public/.gitkeep",
        "backend/storage/app/documents/.gitkeep",
        "backend/storage/logs/.gitkeep",
        "backend/storage/framework/cache/data/.gitkeep",
        "backend/storage/framework/sessions/.gitkeep",
        "backend/storage/framework/views/.gitkeep",
        "backend/storage/framework/testing/.gitkeep",
        "backend/bootstrap/cache/.gitkeep",
    ):
        package.add(path, "", area="laravel-core")

    package.add(
        "backend/.gitignore",
        "/node_modules\n/public/build\n/public/hot\n/public/storage\n/storage/*.key\n/vendor\n"
        ".env\n.env.backup\n.phpunit.result.cache\nHomestead.json\nHomestead.yaml\n"
        "npm-debug.log\nyarn-error.log\n/.idea\n/.vscode\n",
        area="laravel-core",
    )
    package.add(
        "backend/.editorconfig",
        "root = true\n\n[*]\ncharset = utf-8\nend_of_line = lf\nindent_size = 4\n"
        "indent_style = space\ninsert_final_newline = true\ntrim_trailing_whitespace = true\n\n"
        "[*.md]\ntrim_trailing_whitespace = false\n\n[*.{yml,yaml}]\nindent_size = 2\n",
        area="laravel-core",
    )
    package.add(
        "backend/pint.json",
        json.dumps(
            {"preset": "laravel", "rules": {"not_operator_with_successor_space": True}},
            ensure_ascii=False,
            indent=4,
        )
        + "\n",
        area="laravel-core",
    )
