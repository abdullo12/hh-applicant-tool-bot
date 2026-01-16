# 🚀 Деплой @clever8_bot как публичного бота

## Вариант 1: Railway (Рекомендуется)

### 1. Откройте Railway
https://railway.app

### 2. Войдите через GitHub

### 3. New Project → Deploy from GitHub repo

### 4. Выберите репозиторий `hh-applicant-tool`

### 5. Добавьте переменные окружения:

```
TELEGRAM_BOT_TOKEN=1885942942:AAGzEmy7tdiA8fl-YxwaU_PEIPk3rbMSHK0
APP_URL=https://ваш-проект.up.railway.app
```

**Важно:** `APP_URL` вы получите после первого деплоя. Сначала задеплойте, получите URL, потом добавьте эту переменную и перезапустите.

### 6. Railway автоматически:
- Установит зависимости из `requirements_public.txt`
- Запустит `web` (auth_server) и `worker` (public_bot) из `Procfile`

### 7. Получите URL
Railway даст URL типа: `https://hh-applicant-tool-production-xxxx.up.railway.app`

### 8. Обновите переменную APP_URL
Добавьте в Variables:
```
APP_URL=https://ваш-реальный-url.up.railway.app
```

### 9. Перезапустите
Railway → Settings → Restart

---

## Вариант 2: Render (Альтернатива)

### Сервис 1: Web Server

1. New → Web Service
2. Connect GitHub → `hh-applicant-tool`
3. Settings:
   - **Build:** `pip install -r requirements_public.txt`
   - **Start:** `gunicorn auth_server:app`
4. Environment Variables:
   - `APP_URL` = (получите после деплоя)

### Сервис 2: Background Worker

1. New → Background Worker
2. Connect GitHub → `hh-applicant-tool`
3. Settings:
   - **Build:** `pip install -e . && pip install -r requirements_public.txt`
   - **Start:** `python public_bot.py`
4. Environment Variables:
   - `TELEGRAM_BOT_TOKEN` = `1885942942:AAGzEmy7tdiA8fl-YxwaU_PEIPk3rbMSHK0`
   - `APP_URL` = URL от первого сервиса

---

## Тестирование

1. Откройте Telegram
2. Найдите @clever8_bot
3. Отправьте `/start`
4. Нажмите "Авторизоваться"
5. Войдите на HH.RU
6. Вернитесь в бот
7. `/letter Ваше письмо`
8. `/apply`

---

## Для других пользователей

Теперь любой может:
1. Найти @clever8_bot
2. Авторизоваться
3. Отправлять отклики

**Просто!** 🎉
