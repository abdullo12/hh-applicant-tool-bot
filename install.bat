@echo off
chcp 65001 >nul
echo 🚀 Установка HH Applicant Tool + Telegram Bot
echo ==============================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.10 или новее
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% найден

REM Создание виртуального окружения
if not exist "venv" (
    echo 📦 Создаю виртуальное окружение...
    python -m venv venv
)

REM Активация
call venv\Scripts\activate

REM Установка зависимостей
echo 📥 Устанавливаю зависимости...
pip install -q --upgrade pip
pip install -q -e .
pip install -q python-telegram-bot==21.10

echo.
echo ✅ Установка завершена!
echo.
echo 📋 Следующие шаги:
echo.
echo 1️⃣  Авторизуйтесь на HH.RU:
echo    hh-applicant-tool auth
echo.
echo 2️⃣  Создайте сопроводительное письмо:
echo    notepad cover_letter.txt
echo.
echo 3️⃣  Создайте Telegram бота:
echo    - Найдите @BotFather в Telegram
echo    - Отправьте /newbot
echo    - Скопируйте токен
echo.
echo 4️⃣  Узнайте свой Telegram ID:
echo    - Найдите @userinfobot
echo    - Отправьте /start
echo    - Скопируйте ID
echo.
echo 5️⃣  Запустите бота:
echo    set TELEGRAM_BOT_TOKEN=ваш_токен
echo    set TELEGRAM_USER_IDS=ваш_id
echo    python telegram_bot.py
echo.
echo 📖 Подробная инструкция: type SETUP_GUIDE.md
echo.
pause
