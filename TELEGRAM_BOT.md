# Telegram Bot для HH Applicant Tool

## Быстрый старт

### 1. Создайте бота в Telegram

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Придумайте имя и username для бота
4. Скопируйте токен (выглядит как `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Узнайте свой Telegram ID

1. Найдите [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Скопируйте ваш ID (например, `123456789`)

### 3. Установите зависимости

```bash
cd /Users/sus/hh-applicant-tool
source venv/bin/activate
pip install -r bot_requirements.txt
```

### 4. Запустите бота

```bash
# Экспортируйте переменные окружения
export TELEGRAM_BOT_TOKEN="ваш_токен_от_BotFather"
export TELEGRAM_USER_IDS="ваш_telegram_id"

# Запустите бота
python telegram_bot.py
```

### 5. Используйте бота

Откройте вашего бота в Telegram и отправьте `/start`

## Команды бота

- `/start` - Приветствие и список команд
- `/apply` - Отправить отклики на вакансии
- `/update` - Обновить резюме
- `/whoami` - Информация об аккаунте HH
- `/stats` - Статистика откликов
- `/resumes` - Список резюме
- `/contacts` - Последние 20 контактов работодателей
- `/help` - Справка

## Запуск в фоне (Linux/Mac)

### Вариант 1: nohup

```bash
export TELEGRAM_BOT_TOKEN="ваш_токен"
export TELEGRAM_USER_IDS="ваш_id"
nohup python telegram_bot.py > bot.log 2>&1 &
```

### Вариант 2: systemd (рекомендуется)

Создайте файл `/etc/systemd/system/hh-telegram-bot.service`:

```ini
[Unit]
Description=HH Applicant Tool Telegram Bot
After=network.target

[Service]
Type=simple
User=ваш_пользователь
WorkingDirectory=/Users/sus/hh-applicant-tool
Environment="TELEGRAM_BOT_TOKEN=ваш_токен"
Environment="TELEGRAM_USER_IDS=ваш_id"
ExecStart=/Users/sus/hh-applicant-tool/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запустите:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hh-telegram-bot
sudo systemctl start hh-telegram-bot
sudo systemctl status hh-telegram-bot
```

### Вариант 3: Docker

Добавьте в `docker-compose.yml`:

```yaml
  telegram_bot:
    extends: hh_applicant_tool
    container_name: hh_telegram_bot
    command: python /app/telegram_bot.py
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_USER_IDS=${TELEGRAM_USER_IDS}
```

Создайте `.env` файл:

```
TELEGRAM_BOT_TOKEN=ваш_токен
TELEGRAM_USER_IDS=ваш_id
```

Запустите:

```bash
docker-compose up -d telegram_bot
```

## Безопасность

- Никогда не публикуйте токен бота
- Обязательно укажите `TELEGRAM_USER_IDS` для ограничения доступа
- Можно указать несколько ID через запятую: `123456,789012,345678`

## Логи

Просмотр логов:

```bash
# nohup
tail -f bot.log

# systemd
sudo journalctl -u hh-telegram-bot -f

# docker
docker logs -f hh_telegram_bot
```

## Остановка бота

```bash
# nohup
pkill -f telegram_bot.py

# systemd
sudo systemctl stop hh-telegram-bot

# docker
docker-compose stop telegram_bot
```
