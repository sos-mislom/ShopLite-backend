# ShopLite

ShopLite — сервис для создания и управления интернет-магазинами: витрина, каталог, заказы, аналитика, платежи.

Ссылка на репозиторий: укажите актуальную ссылку.

## Что реализовано
- Регистрация/логин, обновление токенов, восстановление пароля по email.
- Управление магазинами (slug, логотип, домен, активность).
- Конструктор дизайна витрины с публикацией (хранение в JSON).
- Каталог: товары, категории, коллекции и связи коллекций с товарами.
- Оформление заказов, админские списки заказов и статусы оплаты.
- Интеграция с YooKassa: создание платежа и обработка вебхука.
- Трек-номер заказа, публичное окно проверки статуса, письмо с трек-номером и чеком после успешной онлайн-оплаты.
- Загрузка изображений и отдача медиа через API.
- Публичная витрина по slug + трекинг посещений.
- Аналитика продаж и посещений.

## Стек
### Backend
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy 2 (async) + asyncpg
- Alembic (миграции)
- Pydantic v2 + pydantic-settings
- JWT (python-jose), bcrypt/passlib
- httpx для интеграций

### Frontend
- Next.js 16
- React 19
- TypeScript
- Tailwind CSS

### Инфра
- PostgreSQL 15
- Docker + docker-compose

## Архитектура и бэк
- `app/main.py` — точка входа FastAPI, подключение роутеров, CORS, статика.
- `app/routers` — HTTP-модули (auth, stores, catalog, orders, payments, analytics и т.д.).
- `app/services` — бизнес-логика (auth, email, YooKassa).
- `app/schemas` — Pydantic-схемы запросов/ответов.
- `app/database.py` — модели и асинхронная сессия БД.
- Медиа хранятся в `uploads`, доступны через `/uploads` или `/v1/api/media/upload/{filename}`.

## Схема БД (текущая)
Таблицы:
- `users` — пользователи.
- `stores` — магазины пользователя.
- `store_designs` — JSON-дизайн витрины, публикация и версия.
- `categories` — категории, поддержка иерархии.
- `collections` — подборки товаров.
- `products` — товары, цена, изображения, варианты.
- `collection_products` — связь многие-ко-многим коллекций и товаров.
- `orders` — заказы, суммы, статусы оплаты, `tracking_number`.
- `order_items` — позиции заказа.
- `payments` — платежи провайдеров, статус, raw-ответ.
- `store_visits` — посещения витрин.

Ключевые связи:
- `users` 1→N `stores`
- `stores` 1→1 `store_designs`
- `stores` 1→N `products`, `categories`, `collections`, `orders`, `store_visits`
- `collections` N↔N `products` через `collection_products`
- `orders` 1→N `order_items`, `payments`

## Основные API модули
Префикс: `/v1/api`
- `/auth` — регистрация, логин, refresh, reset.
- `/users` — профиль пользователя.
- `/stores` — управление магазинами.
- `/store-design` — дизайн/публикация витрины.
- `/products` — управление товарами.
- `/categories` — управление категориями.
- `/collections` — коллекции и связи с товарами.
- `/orders` — оформление и просмотр заказов.
- `/orders/track/{tracking_number}` — публичное отслеживание статуса заказа.
- `/orders/my`, `/stores/{store_id}/orders` — админские заказы.
- `/checkout` — оформление оплаты (YooKassa).
- `/payments` — вебхук оплат.
- `/media` — загрузка/выдача изображений.
- `/public` — публичная витрина по slug.
- `/analytics` — аналитика продаж/визитов.
- `/visits` — трекинг посещений.

## Авторизация
- JWT-токены (access + refresh), `Authorization: Bearer <token>`.
- Пароли хэшируются bcrypt.
- `POST /auth/forgot` отправляет reset-токен на email, `POST /auth/reset` меняет пароль.
- Доступ к части эндпоинтов защищён `AuthService.get_current_user`.

## Оплата (YooKassa)
1) `POST /checkout/yookassa`:
   - Валидирует товары по БД, считает итоговую сумму.
   - Создаёт заказ и позиции.
   - Запрашивает создание платежа в YooKassa, сохраняет `Payment` и `confirmation_url`.
2) `POST /payments/yookassa/webhook`:
   - Получает вебхук, подтягивает платеж из YooKassa.
   - Обновляет статус платежа и заказа.
   - Если оплата успешна, отправляет email с трек-номером и чеком, формирует ссылку на окно отслеживания.

Требуются `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`.

## Логи и мониторинг
- Логи идут в stdout (Uvicorn/FastAPI), доступны через `docker logs`.
- Ошибки отправки писем пишутся в stdout.
- Отдельного мониторинга/метрик пока нет.

## Docker
- `docker-compose.yml` поднимает PostgreSQL и API.
- При старте API выполняются миграции `alembic upgrade head`.
- Медиа сохраняются в `./uploads` (volume).
- Порты: API `9000:8000`, Postgres `5433:5432`.

## Запуск проекта
### Docker (рекомендуется)
1) Создать `.env` и заполнить переменные:
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
   - `DATABASE_URL` (для локала можно `postgresql+asyncpg://user:pass@localhost:5432/db`)
   - `JWT_SECRET`
   - `SMTP_USER`, `SMTP_PASSWORD`
   - `PUBLIC_BASE_URL`
   - `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` (если нужна оплата)
2) Запуск:
   ```bash
   docker compose up --build
   ```
3) API доступен на `http://localhost:9000`.

### Локально
1) Backend:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```
2) Frontend:
   ```bash
   cd ShopLite-front
   npm install
   npm run dev
   ```
3) Front по умолчанию: `http://localhost:3000`.

## Что можно улучшить
- Разграничение ролей (admin/owner/manager) и ACL на все модули.
- Унификация авторизации (часть CRUD сейчас публичные).
- Централизованный логгер и метрики (Sentry/Prometheus).
- Тесты (unit/integration) и CI.
- Очереди/фоновые задачи для писем и вебхуков.
- Валидация и ограничения для загрузок медиа (размеры, форматы).

## Сложные места и как решено
- Безопасный slug магазина: нормализация + проверка уникальности с суффиксом.
- Оплата: идемпотентный ключ и синхронизация статусов через вебхук.
- Подсчёт суммы заказа: цена берётся из БД, чтобы клиент не мог подменить итог.
- Безопасная отдача медиа: проверка content-type и защита от path traversal.
