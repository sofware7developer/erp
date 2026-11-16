# -*- coding: utf-8 -*-
"""
تولید فایل‌های استقرار
=======================
docker-compose، nginx، اسکریپت‌های نصب/پشتیبان/به‌روزرسانی و Makefile.

هدف: استقرار با یک دستور روی هر ماشین دارای Docker، بدون تنظیم دستی.
"""

from __future__ import annotations

from typing import Any

from .writers import Package, render

DB_IMAGES = {
    "mysql": {"image": "mysql:8.4", "port": 3306, "health": "mysqladmin ping -h localhost -u root -p$$MYSQL_ROOT_PASSWORD"},
    "mariadb": {"image": "mariadb:11.4", "port": 3306, "health": "mariadb-admin ping -h localhost -u root -p\"$$MYSQL_ROOT_PASSWORD\""},
    "pgsql": {"image": "postgres:16-alpine", "port": 5432, "health": "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"},
    "sqlite": {"image": None, "port": 0, "health": None},
}

COMPOSE_TEMPLATE = """# ============================================================================
# @@app_name_fa@@ — پشته استقرار کامل
#
# اجرا:  docker compose up -d --build
# نصب:   docker compose exec app php artisan erp:install
# سلامت: curl http://localhost:@@host_port@@/api/v1/health
# ============================================================================

name: @@slug@@

services:
@@db_service@@
@@redis_service@@
@@ai_service@@
@@mqtt_service@@
  app:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: @@slug@@/backend:@@version@@
    container_name: @@slug@@-app
    restart: unless-stopped
@@depends_on@@
    env_file:
      - ./backend/.env
    environment:
      APP_ENV: production
      APP_DEBUG: "false"
@@db_env@@
@@ai_env@@@@redis_env@@
@@mqtt_env@@
    volumes:
      - backend-storage:/var/www/html/storage
      - backend-cache:/var/www/html/bootstrap/cache
    networks:
      - erp
    command: ["php-fpm"]

  queue:
    image: @@slug@@/backend:@@version@@
    container_name: @@slug@@-queue
    restart: unless-stopped
    depends_on:
      - app
    env_file:
      - ./backend/.env
    environment:
      APP_ENV: production
    volumes:
      - backend-storage:/var/www/html/storage
      - backend-cache:/var/www/html/bootstrap/cache
    networks:
      - erp
    command: ["php", "artisan", "queue:work", "--sleep=3", "--tries=3", "--max-time=3600"]

  scheduler:
    image: @@slug@@/backend:@@version@@
    container_name: @@slug@@-scheduler
    restart: unless-stopped
    depends_on:
      - app
    env_file:
      - ./backend/.env
    volumes:
      - backend-storage:/var/www/html/storage
      - backend-cache:/var/www/html/bootstrap/cache
    networks:
      - erp
    command: >
      sh -c "while true; do php /var/www/html/artisan schedule:run --verbose --no-interaction & sleep 60; done"

  web:
    build:
      context: .
      dockerfile: deploy/docker/web.Dockerfile
      args:
        VITE_APP_NAME_FA: "@@app_name_fa@@"
        VITE_COMPANY_NAME: "@@company_name@@"
        VITE_CURRENCY: "@@currency@@"
    image: @@slug@@/web:@@version@@
    container_name: @@slug@@-web
    restart: unless-stopped
    depends_on:
      - app
    ports:
      - "@@host_port@@:80"
    volumes:
      - backend-storage:/var/www/html/storage:ro
      - ./deploy/nginx/erp.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - erp
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/api/v1/health"]
      interval: 30s
      timeout: 6s
      retries: 4
      start_period: 30s

networks:
  erp:
    driver: bridge

volumes:
  backend-storage:
  backend-cache:
@@ai_volumes@@
@@extra_volumes@@
"""


AI_SERVICE_COMPOSE = """  ai-service:
    build:
      context: ./ai-service
      dockerfile: Dockerfile
    image: @@slug@@/ai-service:@@version@@
    container_name: @@slug@@-ai
    restart: unless-stopped
    env_file:
      - ./ai-service/.env
    environment:
      AI_SERVICE_HOST: 0.0.0.0
      AI_SERVICE_PORT: "8001"
      LARAVEL_API_URL: http://app:80/api
    volumes:
      - ai-models:/srv/ai-service/models
      - ai-logs:/srv/ai-service/logs
    networks:
      - erp
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8001/health"]
      interval: 30s
      timeout: 8s
      retries: 4
      start_period: 25s
"""

DB_SERVICE_MYSQL = """  db:
    image: @@image@@
    container_name: @@slug@@-db
    restart: unless-stopped
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci --default-authentication-plugin=mysql_native_password
    environment:
      MYSQL_DATABASE: @@db_database@@
      MYSQL_USER: @@db_username@@
      MYSQL_PASSWORD: @@db_password@@
      MYSQL_ROOT_PASSWORD: @@db_root_password@@
      TZ: @@timezone@@
    volumes:
      - db-data:/var/lib/mysql
    ports:
      - "@@db_host_port@@:@@db_port@@"
    networks:
      - erp
    healthcheck:
      test: ["CMD-SHELL", "@@health@@"]
      interval: 15s
      timeout: 6s
      retries: 10
      start_period: 30s
"""

DB_SERVICE_PGSQL = """  db:
    image: @@image@@
    container_name: @@slug@@-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: @@db_database@@
      POSTGRES_USER: @@db_username@@
      POSTGRES_PASSWORD: @@db_password@@
      TZ: @@timezone@@
    volumes:
      - db-data:/var/lib/postgresql/data
    ports:
      - "@@db_host_port@@:@@db_port@@"
    networks:
      - erp
    healthcheck:
      test: ["CMD-SHELL", "@@health@@"]
      interval: 15s
      timeout: 6s
      retries: 10
      start_period: 20s
"""

REDIS_SERVICE = """  redis:
    image: redis:7-alpine
    container_name: @@slug@@-redis
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes", "--maxmemory", "512mb", "--maxmemory-policy", "allkeys-lru"]
    volumes:
      - redis-data:/data
    networks:
      - erp
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 20s
      timeout: 5s
      retries: 5
"""

MQTT_SERVICE = """  mqtt:
    image: eclipse-mosquitto:2
    container_name: @@slug@@-mqtt
    restart: unless-stopped
    ports:
      - "@@mqtt_port@@:1883"
      - "9001:9001"
    volumes:
      - ./deploy/mosquitto/config:/mosquitto/config:ro
      - mqtt-data:/mosquitto/data
    networks:
      - erp
    healthcheck:
      test: ["CMD-SHELL", "mosquitto_sub -t '$$SYS/#' -C 1 -i healthcheck -W 3 || exit 1"]
      interval: 30s
      timeout: 8s
      retries: 3
"""

WEB_DOCKERFILE = """# ============================================================================
# تصویر nginx: رابط کاربری React (ساخت‌شده) + سرو فایل‌های عمومی لاراول
# ============================================================================

# --- مرحله ۱: ساخت رابط کاربری ---
FROM node:20-alpine AS frontend

WORKDIR /frontend

COPY frontend/package.json ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./

ARG VITE_APP_NAME_FA
ARG VITE_COMPANY_NAME
ARG VITE_CURRENCY
ENV VITE_APP_NAME_FA=$VITE_APP_NAME_FA
ENV VITE_COMPANY_NAME=$VITE_COMPANY_NAME
ENV VITE_CURRENCY=$VITE_CURRENCY
ENV VITE_API_BASE_URL=/api

RUN npm run build

# --- مرحله ۲: nginx ---
FROM nginx:1.27-alpine

ENV TZ=@@timezone@@

RUN rm -f /etc/nginx/conf.d/default.conf

COPY --from=frontend /frontend/dist /var/www/frontend
COPY backend/public /var/www/html/public
COPY deploy/nginx/erp.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""

NGINX_ERP_CONF = """# ============================================================================
# nginx — @@app_name_fa@@
#
#  * /            -> رابط کاربری React (SPA، fallback به index.html)
#  * /api/        -> لاراول (fastcgi به کانتینر app)
#  * /storage/    -> فایل‌های آپلودشده (حجم مشترک)
#  * /up          -> بررسی سلامت لاراول
# ============================================================================

upstream php-fpm {
    server app:9000;
    keepalive 16;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;

    root /var/www/frontend;
    index index.html;

    charset utf-8;
    client_max_body_size 64M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 5;
    gzip_types
        text/plain text/css text/xml application/json application/javascript
        application/xml+rss application/atom+xml image/svg+xml;

    # --- امنیت ---
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-XSS-Protection "1; mode=block" always;

    access_log /var/log/nginx/erp.access.log;
    error_log  /var/log/nginx/erp.error.log warn;

    # --- API لاراول ---
    location /api/ {
        root /var/www/html/public;
        try_files $uri /index.php?$query_string;
    }

    location = /up {
        root /var/www/html/public;
        try_files $uri /index.php?$query_string;
    }

    location = /index.php {
        root /var/www/html/public;
        fastcgi_pass php-fpm;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME /var/www/html/public/index.php;
        fastcgi_param DOCUMENT_ROOT /var/www/html/public;
        fastcgi_param HTTP_PROXY "";
        fastcgi_buffers 16 16k;
        fastcgi_buffer_size 32k;
        fastcgi_read_timeout 300s;
        fastcgi_connect_timeout 30s;
        fastcgi_send_timeout 120s;
        include fastcgi_params;
        internal;
    }

    location ~ \\.php$ {
        return 404;
    }

    # --- فایل‌های آپلودشده ---
    location /storage/ {
        alias /var/www/html/storage/app/public/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public";
        try_files $uri =404;
    }

    # --- فایل‌های ایستای رابط کاربری ---
    location /assets/ {
        alias /var/www/frontend/assets/;
        access_log off;
        expires 30d;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        expires 0;
    }

    # --- پنهان‌سازی فایل‌های حساس ---
    location ~ /\\.(?!well-known) {
        deny all;
    }
}
"""

NGINX_FRONTEND_CONF = """# nginx مخصوص کانتینر مستقل رابط کاربری
# در این حالت /api به سرویس وب یکپارچه پروکسی می‌شود.

server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    charset utf-8;
    client_max_body_size 32M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript image/svg+xml;

    location /api/ {
        proxy_pass http://web:80;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location /storage/ {
        proxy_pass http://web:80;
        proxy_set_header Host $host;
    }

    location /assets/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
"""

MOSQUITTO_CONF = """# Mosquitto — دریافت داده سنسورهای کارخانه
listener 1883
protocol mqtt

listener 9001
protocol websockets

allow_anonymous true
persistence true
persistence_location /mosquitto/data/

log_dest stdout
log_type error
log_type warning
log_type notice

# در استقرار واقعی، احراز هویت با فایل رمز یا JWT فعال شود:
# password_file /mosquitto/config/passwd
# allow_anonymous false

connection_messages true
max_queued_messages 5000
message_size_limit 262144
"""

DEPLOY_SH = """#!/usr/bin/env bash
# ============================================================================
# @@app_name_fa@@ — نصب و استقرار خودکار
#
# استفاده:
#   ./deploy.sh                 نصب کامل و راه‌اندازی
#   ./deploy.sh --no-cache      ساخت مجدد تصویرها بدون کش
#   ./deploy.sh --demo          نصب با داده نمونه
#   ./deploy.sh --stop          توقف سرویس‌ها
#   ./deploy.sh --logs          مشاهده لاگ‌ها
# ============================================================================

set -euo pipefail

APP_NAME="@@app_name_fa@@"
SLUG="@@slug@@"
PORT="${ERP_PORT:-@@host_port@@}"
NO_CACHE=""
WITH_DEMO=""
ACTION="install"

RED='\\033[0;31m'; GREEN='\\033[0;32m'; YELLOW='\\033[1;33m'; BLUE='\\033[0;34m'; NC='\\033[0m'

log()  { printf "${BLUE}[INFO]${NC} %s\\n" "$1"; }
ok()   { printf "${GREEN}[ OK ]${NC} %s\\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC} %s\\n" "$1"; }
err()  { printf "${RED}[FAIL]${NC} %s\\n" "$1" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-cache) NO_CACHE="--no-cache"; shift ;;
    --demo)     WITH_DEMO="--demo"; shift ;;
    --stop)     ACTION="stop"; shift ;;
    --logs)     ACTION="logs"; shift ;;
    --restart)  ACTION="restart"; shift ;;
    --status)   ACTION="status"; shift ;;
    --help|-h)
      grep '^#' "$0" | head -n 14
      exit 0 ;;
    *) err "گزینه ناشناخته: $1"; exit 1 ;;
  esac
done

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

check_requirements() {
  log "بررسی پیش‌نیازها…"
  command -v docker >/dev/null 2>&1 || { err "docker نصب نیست."; exit 1; }
  if ! compose version >/dev/null 2>&1; then err "docker compose در دسترس نیست."; exit 1; fi
  ok "docker و compose آماده‌اند."
}

prepare_env() {
  if [[ ! -f backend/.env ]]; then
    log "ساخت backend/.env از روی الگو…"
    cp backend/.env.example backend/.env
    APP_KEY="base64:$(head -c 32 /dev/urandom | base64)"
    if [[ "$(uname)" == "Darwin" ]]; then
      sed -i '' "s|^APP_KEY=.*|APP_KEY=${APP_KEY}|" backend/.env
    else
      sed -i "s|^APP_KEY=.*|APP_KEY=${APP_KEY}|" backend/.env
    fi
    ok "APP_KEY تولید شد."
  else
    ok "backend/.env موجود است."
  fi

  [[ -f ai-service/.env ]] || cp ai-service/.env.example ai-service/.env

  if [[ ! -f .env ]]; then
    cat > .env <<ENV
ERP_PORT=${PORT}
COMPOSE_PROJECT_NAME=${SLUG}
ENV

  fi
}

build() {
  log "ساخت تصویرهای Docker (ممکن است چند دقیقه طول بکشد)…"
  compose build ${NO_CACHE}
  ok "تصویرها ساخته شدند."
}

start() {
  log "راه‌اندازی سرویس‌ها…"
  compose up -d
  ok "سرویس‌ها در حال اجرا هستند."
}

wait_for_backend() {
  log "انتظار برای آماده‌شدن بک‌اند…"
  for i in $(seq 1 40); do
    if compose exec -T app php artisan --version >/dev/null 2>&1; then
      ok "لاراول آماده است."
      return 0
    fi
    sleep 3
  done
  warn "بک‌اند پس از ۱۲۰ ثانیه آماده نشد؛ لاگ‌ها را بررسی کنید: ./deploy.sh --logs"
  return 1
}

install_app() {
  log "نصب سامانه (مهاجرت، داده پایه، کاربر مدیر، رجیستری قابلیت‌ها)…"
  compose exec -T app php artisan erp:install --force ${WITH_DEMO}
  ok "نصب کامل شد."
}

show_summary() {
  local ip
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  ip="${ip:-localhost}"

  printf "\\n${GREEN}=============================================================${NC}\\n"
  printf "${GREEN}  %s با موفقیت مستقر شد${NC}\\n" "${APP_NAME}"
  printf "${GREEN}=============================================================${NC}\\n"
  printf "  رابط کاربری :  http://%s:%s/\\n" "${ip}" "${PORT}"
  printf "  سلامت API   :  http://%s:%s/api/v1/health\\n" "${ip}" "${PORT}"
  printf "  سرویس AI    :  docker compose exec ai-service curl -s localhost:8001/health\\n"
  printf "\\n"
  printf "  کاربر مدیر  :  %s\\n" "@@admin_email@@"
  printf "  گذرواژه     :  %s  (فوراً تغییر دهید)\\n" "@@admin_password@@"
  printf "\\n"
  printf "  دستورات پرکاربرد:\\n"
  printf "    ./deploy.sh --status     وضعیت سرویس‌ها\\n"
  printf "    ./deploy.sh --logs       مشاهده لاگ\\n"
  printf "    ./deploy.sh --restart    راه‌اندازی مجدد\\n"
  printf "    make backup              پشتیبان‌گیری\\n"
  printf "${GREEN}=============================================================${NC}\\n\\n"
}

case "${ACTION}" in
  stop)
    log "توقف سرویس‌ها…"
    compose down
    ok "متوقف شد." ;;
  restart)
    compose restart
    ok "راه‌اندازی مجدد انجام شد." ;;
  logs)
    compose logs -f --tail=120 ;;
  status)
    compose ps
    ;;
  install)
    check_requirements
    prepare_env
    build
    start
    if wait_for_backend; then
      install_app
    fi
    show_summary
    ;;
esac
"""

BACKUP_SH = """#!/usr/bin/env bash
# پشتیبان‌گیری از پایگاه داده و فایل‌های @@app_name_fa@@
#
# استفاده: ./deploy/scripts/backup.sh  (یا make backup)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="${BACKUP_DIR}/${STAMP}"

mkdir -p "${TARGET}"

echo "[1/3] پشتیبان‌گیری از پایگاه داده…"
if docker compose version >/dev/null 2>&1; then
  docker compose exec -T app php artisan erp:backup --disk=local || echo "هشدار: erp:backup ناموفق بود"
  docker compose cp app:/var/www/html/storage/app/backups "${TARGET}/db" 2>/dev/null || true
else
  docker-compose exec -T app php artisan erp:backup --disk=local || true
fi

echo "[2/3] ذخیره تنظیمات و مانیفست…"
cp -f backend/.env "${TARGET}/backend.env" 2>/dev/null || true
cp -f manifest.json "${TARGET}/manifest.json" 2>/dev/null || true
cp -f docker-compose.yml "${TARGET}/docker-compose.yml" 2>/dev/null || true

echo "[3/3] فشرده‌سازی…"
ARCHIVE="${BACKUP_DIR}/@@slug@@-${STAMP}.tar.gz"
tar -czf "${ARCHIVE}" -C "${BACKUP_DIR}" "$(basename "${TARGET}")"
rm -rf "${TARGET}"

echo "پشتیبان ذخیره شد: ${ARCHIVE}"

# نگهداری ۱۰ نسخه آخر
ls -1t "${BACKUP_DIR}"/@@slug@@-*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
"""

HEALTHCHECK_SH = """#!/usr/bin/env bash
# بررسی سلامت پشته @@app_name_fa@@

set -uo pipefail

PORT="${ERP_PORT:-@@host_port@@}"
BASE="http://localhost:${PORT}"
FAIL=0

check() {
  local label="$1"; local url="$2"
  if curl -fsS --max-time 8 "${url}" >/dev/null 2>&1; then
    printf "  \\033[0;32m✓\\033[0m %s\\n" "${label}"
  else
    printf "  \\033[0;31m✗\\033[0m %s (%s)\\n" "${label}" "${url}"
    FAIL=1
  fi
}

echo "بررسی سلامت ${BASE}"
check "رابط کاربری"          "${BASE}/"
check "سلامت API"            "${BASE}/api/v1/health"
check "مسیر لاراول (up)"     "${BASE}/up"

if docker compose ps >/dev/null 2>&1; then
  echo "کانتینرهای در حال اجرا:"
  docker compose ps --format "table {{.Name}}\\t{{.Status}}" 2>/dev/null || docker compose ps
  echo "سلامت سرویس AI:"
  docker compose exec -T ai-service curl -fsS http://localhost:8001/health >/dev/null 2>&1 \\
    && echo "  ✓ ai-service" || { echo "  ✗ ai-service"; FAIL=1; }
fi

exit ${FAIL}
"""

UPDATE_SH = """#!/usr/bin/env bash
# به‌روزرسانی @@app_name_fa@@ پس از دریافت بسته جدید
#
# ۱) پشتیبان‌گیری خودکار  ۲) جایگزینی کد  ۳) مهاجرت  ۴) پاک‌سازی کش

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "${SCRIPT_DIR}")")"

echo "[1/4] پشتیبان‌گیری پیش از به‌روزرسانی…"
bash "${SCRIPT_DIR}/backup.sh" || echo "هشدار: پشتیبان‌گیری ناموفق بود"

echo "[2/4] مهاجرت پایگاه داده…"
docker compose -f "${ROOT_DIR}/docker-compose.yml" exec -T app php artisan migrate --force

echo "[3/4] همگام‌سازی رجیستری قابلیت‌ها…"
docker compose -f "${ROOT_DIR}/docker-compose.yml" exec -T app php artisan erp:features:sync

echo "[4/4] بهینه‌سازی و راه‌اندازی مجدد…"
docker compose -f "${ROOT_DIR}/docker-compose.yml" exec -T app php artisan config:cache
docker compose -f "${ROOT_DIR}/docker-compose.yml" exec -T app php artisan route:cache
docker compose -f "${ROOT_DIR}/docker-compose.yml" exec -T app php artisan view:clear
docker compose -f "${ROOT_DIR}/docker-compose.yml" restart

echo "به‌روزرسانی کامل شد."
"""

MAKEFILE = """# ============================================================================
# @@app_name_fa@@ — دستورات مدیریتی
# ============================================================================

COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")
SLUG := @@slug@@
PORT ?= @@host_port@@

.PHONY: help install build up down restart logs status shell migrate seed \\
        backup update health test ai-health clean psql mysql

help: ## نمایش این راهنما
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \\
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-14s\\033[0m %s\\n", $$1, $$2}'

install: ## نصب کامل (ساخت، اجرا، مهاجرت، کاربر مدیر)
	bash deploy.sh

build: ## ساخت تصویرها
	$(COMPOSE) build

up: ## راه‌اندازی سرویس‌ها
	$(COMPOSE) up -d

down: ## توقف و حذف کانتینرهای پشته
	$(COMPOSE) down

restart: ## راه‌اندازی مجدد
	$(COMPOSE) restart

logs: ## مشاهده لاگ‌ها
	$(COMPOSE) logs -f --tail=120

status: ## وضعیت سرویس‌ها
	$(COMPOSE) ps

shell: ## پوسته داخل کانتینر لاراول
	$(COMPOSE) exec app bash

migrate: ## اجرای مهاجرت‌ها
	$(COMPOSE) exec app php artisan migrate --force

seed: ## درج داده پایه
	$(COMPOSE) exec app php artisan db:seed --force

demo: ## درج داده نمونه
	$(COMPOSE) exec app php artisan db:seed --class="Database\\\\Seeders\\\\DemoDataSeeder" --force

backup: ## پشتیبان‌گیری
	bash deploy/scripts/backup.sh

update: ## به‌روزرسانی پس از دریافت بسته جدید
	bash deploy/scripts/update.sh

health: ## بررسی سلامت پشته
	bash deploy/scripts/healthcheck.sh

test: ## اجرای آزمون‌های لاراول
	$(COMPOSE) exec app php artisan test

ai-health: ## بررسی سلامت سرویس هوش مصنوعی
	$(COMPOSE) exec app php artisan erp:ai:health

ai-shell: ## پوسته داخل سرویس AI
	$(COMPOSE) exec ai-service bash

clean: ## پاک‌سازی کش و فایل‌های موقت
	$(COMPOSE) exec app php artisan optimize:clear

psql: ## اتصال به پایگاه داده (PostgreSQL)
	$(COMPOSE) exec db psql -U $(SLUG) -d $(SLUG)

mysql: ## اتصال به پایگاه داده (MySQL)
	$(COMPOSE) exec db mysql -u $(SLUG) -p $(SLUG)
"""

ROOT_ENV = """# متغیرهای محیطی پشته Docker — @@app_name_fa@@
ERP_PORT=@@host_port@@
COMPOSE_PROJECT_NAME=@@slug@@

# پایگاه داده (مقادیر باید با backend/.env یکسان باشد)
DB_CONNECTION=@@db_driver@@
DB_HOST=db
DB_PORT=@@db_port@@
DB_DATABASE=@@db_database@@
DB_USERNAME=@@db_username@@
DB_PASSWORD=@@db_password@@
DB_ROOT_PASSWORD=@@db_root_password@@

# Redis
REDIS_HOST=redis

# سرویس هوش مصنوعی
AI_SERVICE_URL=http://ai-service:8001

# AvalAI (اختیاری)
AVALAI_API_KEY=@@avalai_key@@
AVALAI_MODEL=@@avalai_model@@
"""

ROOT_GITIGNORE = """# وابستگی‌ها
vendor/
node_modules/
.venv/
__pycache__/
*.pyc

# محیط و رازها
.env
!.env.example
backend/.env
!backend/.env.example
ai-service/.env
!ai-service/.env.example

# خروجی ساخت
frontend/dist/
backend/public/build/
backend/public/hot
backend/public/storage
ai-service/models/

# ذخیره‌سازی و لاگ
backend/storage/*.key
backend/storage/logs/*
!backend/storage/logs/.gitkeep
backups/
*.log

# پایگاه داده محلی
*.sqlite
*.sqlite3

# ابزارها
.idea/
.vscode/
.phpunit.result.cache
.DS_Store
npm-debug.log*
yarn-error.log*
"""

SYSTEMD_BACKEND = """# واحد systemd برای اجرای لاراول بدون Docker
# نصب: sudo cp deploy/systemd/erp-backend.service /etc/systemd/system/
#      sudo systemctl daemon-reload && sudo systemctl enable --now erp-backend

[Unit]
Description=@@app_name_fa@@ — Laravel Backend
After=network.target @@db_driver@@.service redis.service
Wants=@@db_driver@@.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/@@slug@@/backend
ExecStart=/usr/bin/php artisan serve --host=0.0.0.0 --port=8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
Environment=PHP_CLI_SERVER_WORKERS=4
StandardOutput=append:/var/log/@@slug@@/backend.log
StandardError=append:/var/log/@@slug@@/backend-error.log

[Install]
WantedBy=multi-user.target
"""

SYSTEMD_AI = """# واحد systemd برای سرویس هوش مصنوعی
# نصب: sudo cp deploy/systemd/erp-ai.service /etc/systemd/system/

[Unit]
Description=@@app_name_fa@@ — AI Microservice (FastAPI)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/@@slug@@/ai-service
Environment=PATH=/opt/@@slug@@/ai-service/.venv/bin:/usr/bin:/bin
ExecStart=/opt/@@slug@@/ai-service/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=5
StandardOutput=append:/var/log/@@slug@@/ai.log
StandardError=append:/var/log/@@slug@@/ai-error.log

[Install]
WantedBy=multi-user.target
"""

SYSTEMD_QUEUE = """# واحد systemd برای کارگر صف
[Unit]
Description=@@app_name_fa@@ — Queue Worker
After=network.target @@db_driver@@.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/@@slug@@/backend
ExecStart=/usr/bin/php artisan queue:work --sleep=3 --tries=3 --max-time=3600
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

CRONTAB_FILE = """# cron سامانه @@app_name_fa@@
# نصب: crontab deploy/crontab.txt
#
# پشتیبان‌گیری روزانه — @@backup_cron@@
@@backup_cron@@ cd /opt/@@slug@@ && bash deploy/scripts/backup.sh >> /var/log/@@slug@@/backup.log 2>&1

# اجرای زمان‌بندی لاراول هر دقیقه
* * * * * cd /opt/@@slug@@/backend && php artisan schedule:run --verbose --no-interaction >> /dev/null 2>&1

# بررسی سلامت هر ۱۵ دقیقه
*/15 * * * * cd /opt/@@slug@@ && bash deploy/scripts/healthcheck.sh >> /var/log/@@slug@@/health.log 2>&1

# پاک‌سازی لاگ‌های قدیمی — هفتگی
0 3 * * 0 find /opt/@@slug@@/backend/storage/logs -name "*.log" -mtime +30 -delete
"""


def generate_deploy_files(
    package: Package,
    *,
    settings: dict[str, Any],
    context: dict[str, Any],
) -> None:
    """تولید فایل‌های استقرار و پیکربندی زیرساخت."""
    slug = context["slug"]
    db_driver = settings.get("db_driver", "sqlite")
    db_info = DB_IMAGES.get(db_driver, DB_IMAGES["pgsql"])
    host_port = settings.get("host_port", 8000)

    common = {
        "app_name": settings.get("app_name", slug),
        "app_name_fa": settings.get("app_name_fa", context["app_name_fa"]),
        "company_name": settings.get("company_name", context["app_name_fa"]),
        "slug": slug,
        "version": context["version"],
        "timezone": settings.get("timezone", "Asia/Tehran"),
        "currency": settings.get("currency", "IRR"),
        "host_port": host_port,
        "db_driver": db_driver,
        "db_port": db_info["port"] or 5432,
        "db_host_port": settings.get("db_host_port", db_info["port"] or 5432),
        "db_database": settings.get("db_database", slug),
        "db_username": settings.get("db_username", slug),
        "db_password": settings.get("db_password") or "erp_secret_password",
        "db_root_password": settings.get("db_root_password") or "root_secret_password",
        "redis_host": settings.get("redis_host", "redis"),
        "mqtt_port": int(settings.get("mqtt_port", 1883)),
        "mqtt_host": settings.get("mqtt_host", "mqtt"),
        "mqtt_topic": settings.get("mqtt_topic_prefix", f"erp/{slug}"),
        "sampling_seconds": int(settings.get("iot_sampling_seconds", 30)),
        "avalai_key": settings.get("avalai_api_key", ""),
        "avalai_model": settings.get("avalai_model", "gpt-4o-mini"),
        "admin_email": settings.get("admin_email", "admin@example.com"),
        "admin_password": settings.get("admin_password", "ChangeMe!1405"),
        "backup_cron": settings.get("backup_cron", "0 2 * * *"),
        "ai_service_url": settings.get("ai_service_url", "http://ai-service:8001"),
    }

    # --- سرویس هوش مصنوعی (اختیاری) --------------------------------------- #
    ai_enabled = bool(settings.get("ai_enabled", True))
    if ai_enabled:
        ai_service = render(AI_SERVICE_COMPOSE, **common)
        ai_env = (
            "      AI_SERVICE_URL: http://ai-service:8001\n"
            '      ERP_AI_ENABLED: "true"\n'
        )
        ai_volumes = "  ai-models:\n  ai-logs:\n"
        ai_depends = "      ai-service:\n        condition: service_healthy\n"
        systemd_units = "erp-backend erp-ai erp-queue"
        copy_dirs = "backend frontend ai-service deploy"
        ai_manual_steps = (
            "cd ../ai-service && python3 -m venv .venv && "
            ".venv/bin/pip install -r requirements.txt\n"
        )
        ai_note = "| سرویس هوش مصنوعی | http://localhost:@@host_port@@/api/v1/ai/health |\n"
    else:
        ai_service = "  # سرویس هوش مصنوعی غیرفعال است (ai_enabled=false)\n"
        ai_env = '      ERP_AI_ENABLED: "false"\n'
        ai_volumes = ""
        ai_depends = ""
        systemd_units = "erp-backend erp-queue"
        copy_dirs = "backend frontend deploy"
        ai_manual_steps = ""
        ai_note = ""

    # --- سرویس پایگاه داده ------------------------------------------------- #
    if db_driver == "sqlite":
        db_service = (
            "  # پایگاه داده SQLite — نیازی به سرویس جداگانه نیست\n"
            "  # فایل پایگاه داده در حجم مشترک backend-storage نگهداری می‌شود.\n"
        )
        db_env = "      DB_CONNECTION: sqlite\n      DB_DATABASE: /var/www/html/storage/app/database.sqlite\n"
        depends_on = ai_depends
        extra_volumes = ""
    else:
        template = DB_SERVICE_PGSQL if db_driver == "pgsql" else DB_SERVICE_MYSQL
        db_service = render(template, image=db_info["image"], health=db_info["health"] or "", **common)
        db_env = (
            f"      DB_CONNECTION: {db_driver}\n"
            "      DB_HOST: db\n"
            f"      DB_PORT: \"{db_info['port']}\"\n"
        )
        depends_on = "      db:\n        condition: service_healthy\n" + ai_depends
        extra_volumes = "  db-data:\n"

    # --- Redis ------------------------------------------------------------- #
    needs_redis = "redis" in (
        str(settings.get("cache_driver", ""))
        + str(settings.get("queue_driver", ""))
        + str(settings.get("session_driver", ""))
    )
    if needs_redis:
        redis_service = render(REDIS_SERVICE, **common)
        redis_env = "      REDIS_HOST: redis\n      REDIS_PORT: \"6379\"\n"
        depends_on += "      redis:\n        condition: service_started\n"
        extra_volumes += "  redis-data:\n"
    else:
        redis_service = "  # Redis غیرفعال است (cache/queue روی پایگاه داده)"
        redis_env = "      REDIS_HOST: 127.0.0.1\n"

    # --- MQTT / IoT -------------------------------------------------------- #
    if settings.get("iot_enabled"):
        mqtt_service = render(MQTT_SERVICE, **common)
        mqtt_env = (
            f"      MQTT_HOST: {common['mqtt_host']}\n"
            f"      MQTT_PORT: \"{common['mqtt_port']}\"\n"
            f"      MQTT_TOPIC_PREFIX: {common['mqtt_topic']}\n"
            "      ERP_IOT_ENABLED: \"true\"\n"
        )
        extra_volumes += "  mqtt-data:\n"
        depends_on += "      mqtt:\n        condition: service_started\n"
        package.add_rendered("deploy/mosquitto/config/mosquitto.conf", MOSQUITTO_CONF, area="deploy", **common)
    else:
        mqtt_service = "  # سرویس MQTT غیرفعال است (ماژول IoT انتخاب نشده)"
        mqtt_env = "      ERP_IOT_ENABLED: \"false\"\n"

    depends_block = f"    depends_on:\n{depends_on}" if depends_on.strip() else ""

    package.add_rendered(
        "docker-compose.yml",
        COMPOSE_TEMPLATE,
        area="deploy",
        depends_on=depends_block,
        db_service=db_service,
        redis_service=redis_service,
        mqtt_service=mqtt_service,
        ai_service=ai_service,
        db_env=db_env,
        ai_env=ai_env,
        redis_env=redis_env,
        mqtt_env=mqtt_env,
        ai_volumes=ai_volumes or "  # حجم مربوط به هوش مصنوعی لازم نیست\n",
        extra_volumes=extra_volumes or "  # حجم اضافی لازم نیست",
        **common,
    )

    package.add_rendered("deploy/docker/web.Dockerfile", WEB_DOCKERFILE, area="deploy", **common)
    package.add_rendered("deploy/nginx/erp.conf", NGINX_ERP_CONF, area="deploy", **common)
    package.add_rendered("deploy/nginx/frontend.conf", NGINX_FRONTEND_CONF, area="deploy", **common)

    package.add_rendered("deploy.sh", DEPLOY_SH, area="deploy", executable=True, **common)
    package.add_rendered("deploy/scripts/backup.sh", BACKUP_SH, area="deploy", executable=True, **common)
    package.add_rendered("deploy/scripts/update.sh", UPDATE_SH, area="deploy", executable=True, **common)
    package.add_rendered("deploy/scripts/healthcheck.sh", HEALTHCHECK_SH, area="deploy", executable=True, **common)

    package.add_rendered("Makefile", MAKEFILE, area="deploy", **common)
    package.add_rendered(".env", ROOT_ENV, area="deploy", **common)
    package.add_rendered(".env.example", ROOT_ENV, area="deploy", **common)
    package.add_rendered(".gitignore", ROOT_GITIGNORE, area="deploy", **common)

    package.add_rendered("deploy/systemd/erp-backend.service", SYSTEMD_BACKEND, area="deploy", **common)
    if ai_enabled:
        package.add_rendered("deploy/systemd/erp-ai.service", SYSTEMD_AI, area="deploy", **common)
    package.add_rendered("deploy/systemd/erp-queue.service", SYSTEMD_QUEUE, area="deploy", **common)
    package.add_rendered("deploy/crontab.txt", CRONTAB_FILE, area="deploy", **common)

    # راهنمای استقرار سریع
    common["ai_enabled"] = "true" if ai_enabled else "false"
    common["ai_note"] = render(ai_note, **common)
    common["copy_dirs"] = copy_dirs
    common["ai_manual_steps"] = ai_manual_steps
    common["systemd_units"] = systemd_units
    package.add_rendered(
        "deploy/README-fa.md",
        """# استقرار @@app_name_fa@@

## روش ۱ — Docker (توصیه‌شده)

```bash
./deploy.sh              # ساخت، اجرا، مهاجرت و ساخت کاربر مدیر
./deploy.sh --status     # وضعیت سرویس‌ها
./deploy.sh --logs       # مشاهده لاگ
./deploy.sh --stop       # توقف
```

پس از اجرا:

| سرویس | نشانی |
|---|---|
| رابط کاربری | http://localhost:@@host_port@@/ |
| سلامت API | http://localhost:@@host_port@@/api/v1/health |
| بررسی سلامت پشته | `bash deploy/scripts/healthcheck.sh` |
@@ai_note@@

ورود اولیه با کاربر `@@admin_email@@` و گذرواژه `@@admin_password@@`
(فوراً از مسیر *تنظیمات → تغییر گذرواژه* عوض کنید).

## روش ۲ — systemd بدون Docker

```bash
sudo mkdir -p /opt/@@slug@@ && sudo cp -r @@copy_dirs@@ /opt/@@slug@@/
cd /opt/@@slug@@/backend && composer install --no-dev --optimize-autoloader
cp .env.example .env && php artisan key:generate
php artisan migrate --force && php artisan db:seed --force
@@ai_manual_steps@@
cd ../frontend && npm install && npm run build && sudo cp -r dist/* /var/www/@@slug@@/
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now @@systemd_units@@
crontab deploy/crontab.txt
```

## پیکربندی nginx

* `deploy/nginx/erp.conf` — پیکربندی یکپارچه (SPA + API + storage) برای کانتینر web
* `deploy/nginx/frontend.conf` — برای اجرای رابط کاربری در کانتینر جداگانه

برای HTTPS:

```bash
sudo certbot --nginx -d erp.example.com
```

## پشتیبان‌گیری

```bash
make backup                       # دستی
./deploy/scripts/backup.sh        # معادل مستقیم
```

زمان‌بندی خودکار در `deploy/crontab.txt` تعریف شده است
(پیش‌فرض: `@@backup_cron@@`) و ۱۰ نسخه آخر نگهداری می‌شود.

## ارتقا

```bash
./deploy/scripts/update.sh
```

این اسکریپت پیش از هر تغییر، پشتیبان می‌گیرد و پس از مهاجرت،
رجیستری قابلیت‌ها را همگام‌سازی و کش را پاک می‌کند.
""",
        area="docs",
        **common,
    )
