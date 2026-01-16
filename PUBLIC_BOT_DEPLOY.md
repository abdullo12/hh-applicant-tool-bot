# 🌐 Публичный бот - Инструкция по развертыванию

## Концепция

**Один бот для всех пользователей** - как раньше с API:

1. Пользователь пишет боту `/start`
2. Бот дает кнопку "Авторизоваться"
3. Пользователь переходит по ссылке → авторизуется на HH.RU
4. Токены сохраняются в базу
5. Пользователь возвращается в бот и использует `/apply`

---

## 🚀 Быстрое развертывание

### Вариант 1: Railway (Рекомендуется)

#### 1. Подготовка

```bash
git clone https://github.com/s3rgeym/hh-applicant-tool
cd hh-applicant-tool
```

Добавьте в `requirements.txt`:
```
flask==3.1.0
requests==2.32.5
python-telegram-bot==21.10
```

#### 2. Создайте `Procfile`:

```
web: python auth_server.py
worker: python public_bot.py
```

#### 3. Деплой на Railway

1. Откройте [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub**
3. Выберите репозиторий
4. Добавьте переменные:
   - `TELEGRAM_BOT_TOKEN` = токен от @BotFather
5. Railway автоматически запустит оба процесса

#### 4. Получите URL

Railway даст вам URL типа: `https://your-app.railway.app`

#### 5. Обновите код

В `auth_server.py` замените:
```python
REDIRECT_URI = "https://your-app.railway.app/callback"
```

В `public_bot.py` замените:
```python
auth_url = f"https://your-app.railway.app/auth?user_id={telegram_id}"
```

---

### Вариант 2: Render (2 сервиса)

#### Сервис 1: Web Server (auth_server.py)

1. **New** → **Web Service**
2. Подключите GitHub
3. Настройки:
   - **Build Command:** `pip install flask requests`
   - **Start Command:** `python auth_server.py`
4. Получите URL: `https://your-app.onrender.com`

#### Сервис 2: Background Worker (public_bot.py)

1. **New** → **Background Worker**
2. Настройки:
   - **Build Command:** `pip install -e . && pip install python-telegram-bot==21.10`
   - **Start Command:** `python public_bot.py`
3. Переменные:
   - `TELEGRAM_BOT_TOKEN`

---

### Вариант 3: VPS (Полный контроль)

```bash
# Установка
git clone https://github.com/s3rgeym/hh-applicant-tool
cd hh-applicant-tool
pip install -e .
pip install flask requests python-telegram-bot==21.10

# Настройка Nginx
sudo nano /etc/nginx/sites-available/hhbot

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# SSL через Let's Encrypt
sudo certbot --nginx -d your-domain.com

# Systemd сервисы
sudo nano /etc/systemd/system/hhbot-web.service

[Unit]
Description=HH Bot Web Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/hh-applicant-tool
ExecStart=/usr/bin/python3 auth_server.py
Restart=always

[Install]
WantedBy=multi-user.target

# Аналогично для public_bot.py
sudo nano /etc/systemd/system/hhbot-worker.service

# Запуск
sudo systemctl enable hhbot-web hhbot-worker
sudo systemctl start hhbot-web hhbot-worker
```

---

## 📱 Использование (для пользователей)

### Шаг 1: Найти бота

Пользователь находит вашего бота в Telegram: `@your_public_bot`

### Шаг 2: Авторизация

```
Пользователь: /start

Бот: 🤖 HH Applicant Tool Bot
     
     Автоматизация откликов на HH.RU
     
     ✅ До 200 откликов в день
     ✅ Автоматическое обновление
     ✅ Сохранение контактов
     
     [🔐 Авторизоваться]

Пользователь нажимает кнопку →
Открывается браузер →
Авторизация на HH.RU →
Возврат в бот

Бот: ✅ Авторизация успешна!
     Теперь используйте /letter
```

### Шаг 3: Сопроводительное письмо

```
Пользователь: /letter Здравствуйте! Меня заинтересовала ваша вакансия...

Бот: ✅ Сопроводительное письмо сохранено!
```

### Шаг 4: Отправка откликов

```
Пользователь: /apply

Бот: 📤 Начинаю рассылку...
     📨 Отправлено 50 откликов
     ✅ Готово!
```

---

## 🗄️ База данных

Структура `users.db`:

```sql
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    access_token TEXT,
    refresh_token TEXT,
    access_expires_at INTEGER,
    cover_letter TEXT,
    created_at TIMESTAMP,
    last_apply TIMESTAMP
);
```

Каждый пользователь имеет:
- Свои токены HH
- Свое сопроводительное письмо
- Свою статистику

---

## 🔒 Безопасность

### 1. Защита токенов

```python
# Шифрование токенов в БД
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

# При сохранении
encrypted_token = cipher.encrypt(access_token.encode())

# При чтении
decrypted_token = cipher.decrypt(encrypted_token).decode()
```

### 2. Rate limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/auth')
@limiter.limit("10 per minute")
def auth():
    ...
```

### 3. HTTPS обязательно

Используйте только HTTPS для auth_server!

---

## 📊 Мониторинг

### Логирование

```python
import logging

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Метрики

```python
# Количество пользователей
SELECT COUNT(*) FROM users;

# Активные за последние 24 часа
SELECT COUNT(*) FROM users 
WHERE last_apply > datetime('now', '-1 day');

# Всего откликов
SELECT SUM(applies_count) FROM users;
```

---

## 💰 Монетизация (опционально)

### Бесплатный тариф
- 50 откликов в день
- Базовая статистика

### Премиум ($5/месяц)
- 200 откликов в день
- Расширенная статистика
- Приоритетная поддержка

```python
# Добавить в БД
ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0;

# Проверка в боте
if not user['is_premium'] and applies_today >= 50:
    await update.message.reply_text(
        "⚠️ Достигнут лимит бесплатного тарифа (50/день)\n"
        "Upgrade до Premium: /premium"
    )
```

---

## 🆘 Troubleshooting

**Бот не отвечает:**
- Проверьте логи: `tail -f bot.log`
- Проверьте токен: `echo $TELEGRAM_BOT_TOKEN`

**Ошибка авторизации:**
- Проверьте REDIRECT_URI
- Убедитесь что используется HTTPS
- Проверьте CLIENT_ID и CLIENT_SECRET

**База данных заблокирована:**
```python
# Используйте connection pooling
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    try:
        yield conn
    finally:
        conn.close()
```

---

## 📈 Масштабирование

### Для 1000+ пользователей

1. **PostgreSQL вместо SQLite**
```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="hhbot",
    user="postgres",
    password="password"
)
```

2. **Redis для кеширования**
```python
import redis

r = redis.Redis(host='localhost', port=6379)
r.setex(f'user:{telegram_id}', 3600, json.dumps(user_data))
```

3. **Celery для фоновых задач**
```python
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def send_applies(telegram_id):
    # Отправка откликов в фоне
    ...
```

---

## ✅ Готово!

Теперь у вас есть **публичный бот**, которым может пользоваться кто угодно:

1. Находят бота в Telegram
2. Нажимают "Авторизоваться"
3. Входят на HH.RU
4. Используют `/apply`

**Просто как раньше!** 🎉
