# First Step Backend (Django + DRF)

Минимальный backend по ТЗ: регистрация, логин/логаут, профиль, смена пароля, JWT (access+refresh), blacklist refresh, OpenAPI.

## Быстрый старт

```bash
cd first-step-backend
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver

# Если вы тестируете с физического телефона (Expo Go на iOS/Android),
# запускайте так, чтобы сервер был доступен из локальной сети:
python3 manage.py runserver 0.0.0.0:8000
```

## Эндпоинты

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/token/refresh/`
- `POST /api/v1/auth/logout/`
- `GET /api/v1/profile/me/`
- `PATCH /api/v1/profile/me/`
- `POST /api/v1/profile/change-password/`

OpenAPI:
- `GET /api/schema/`
- `GET /api/docs/`

## Настройки через env

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`1`/`0`)
- `DJANGO_ALLOWED_HOSTS`

DB (PostgreSQL):
- `DB_ENGINE=django.db.backends.postgresql`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

CORS:
- `CORS_ALLOWED_ORIGINS`
- `CORS_ALLOW_ALL_ORIGINS=1` (только для локальной разработки)

Throttling:
- `DRF_THROTTLE_ANON`, `DRF_THROTTLE_USER`, `DRF_THROTTLE_LOGIN`

## Тесты

```bash
cd first-step-backend
python3 -m pytest
```

## Админка

1) Создать администратора:

```bash
cd first-step-backend
python3 manage.py createsuperuser
```

2) Запустить сервер и открыть:

- `http://127.0.0.1:8000/admin/`

Важно: если вы меняли `DB_ENGINE/DB_NAME/...`, то админка может смотреть в другую БД — в этом случае “пользователь не появляется”, потому что регистрация и админка работают с разными базами.
