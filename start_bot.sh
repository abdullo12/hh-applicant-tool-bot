#!/bin/bash

# Скрипт для запуска Telegram бота

echo "🤖 Запуск HH Applicant Tool Telegram Bot"
echo ""

# Проверка токена
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Ошибка: не установлена переменная TELEGRAM_BOT_TOKEN"
    echo ""
    echo "Получите токен у @BotFather и выполните:"
    echo "export TELEGRAM_BOT_TOKEN='ваш_токен'"
    echo ""
    exit 1
fi

# Проверка ID пользователя
if [ -z "$TELEGRAM_USER_IDS" ]; then
    echo "⚠️  Предупреждение: не установлена переменная TELEGRAM_USER_IDS"
    echo "Бот будет доступен всем пользователям!"
    echo ""
    echo "Узнайте свой ID у @userinfobot и выполните:"
    echo "export TELEGRAM_USER_IDS='ваш_id'"
    echo ""
    read -p "Продолжить без ограничения доступа? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Активация виртуального окружения
source venv/bin/activate

# Запуск бота
echo "✅ Запускаю бота..."
python telegram_bot.py
