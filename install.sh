#!/bin/bash

echo "🚀 Установка HH Applicant Tool + Telegram Bot"
echo "=============================================="
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.10 или новее"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION найден"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# Активация
source venv/bin/activate

# Установка зависимостей
echo "📥 Устанавливаю зависимости..."
pip install -q --upgrade pip
pip install -q -e .
pip install -q python-telegram-bot==21.10

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1️⃣  Авторизуйтесь на HH.RU:"
echo "   hh-applicant-tool auth"
echo ""
echo "2️⃣  Создайте сопроводительное письмо:"
echo "   nano cover_letter.txt"
echo ""
echo "3️⃣  Создайте Telegram бота:"
echo "   - Найдите @BotFather в Telegram"
echo "   - Отправьте /newbot"
echo "   - Скопируйте токен"
echo ""
echo "4️⃣  Узнайте свой Telegram ID:"
echo "   - Найдите @userinfobot"
echo "   - Отправьте /start"
echo "   - Скопируйте ID"
echo ""
echo "5️⃣  Запустите бота:"
echo "   export TELEGRAM_BOT_TOKEN='ваш_токен'"
echo "   export TELEGRAM_USER_IDS='ваш_id'"
echo "   python telegram_bot.py"
echo ""
echo "📖 Подробная инструкция: cat SETUP_GUIDE.md"
echo ""
