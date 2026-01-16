#!/bin/bash

# Запуск бота в фоне

export TELEGRAM_BOT_TOKEN="1885942942:AAGzEmy7tdiA8fl-YxwaU_PEIPk3rbMSHK0"

cd /Users/sus/hh-applicant-tool
source venv/bin/activate

nohup python telegram_bot.py > bot.log 2>&1 &

echo "🤖 Бот запущен в фоне!"
echo "📝 Логи: tail -f bot.log"
echo "🛑 Остановить: pkill -f telegram_bot.py"
