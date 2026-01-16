#!/usr/bin/env python3
"""Telegram бот для управления HH Applicant Tool"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменной окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USER_IDS = os.getenv('TELEGRAM_USER_IDS', '').split(',')

# Автоопределение путей
import sys
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PATH = sys.executable  # Используем текущий Python из venv


def check_access(user_id: int) -> bool:
    """Проверка доступа пользователя"""
    if not ALLOWED_USER_IDS or ALLOWED_USER_IDS == ['']:
        return True
    return str(user_id) in ALLOWED_USER_IDS


def run_command(cmd: list[str]) -> tuple[str, int]:
    """Выполнение команды hh-applicant-tool"""
    try:
        # Используем текущий Python интерпретатор
        full_cmd = [VENV_PATH, '-m', 'hh_applicant_tool'] + cmd[3:] if len(cmd) > 3 else cmd
        result = subprocess.run(
            full_cmd,
            cwd=WORK_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "⏱ Команда выполняется слишком долго (таймаут 5 мин)", 1
    except Exception as e:
        return f"❌ Ошибка: {str(e)}", 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен")
        return

    await update.message.reply_text(
        "🤖 *HH Applicant Tool Bot*\n\n"
        "Доступные команды:\n"
        "/apply - Отправить отклики\n"
        "/update - Обновить резюме\n"
        "/whoami - Информация об аккаунте\n"
        "/stats - Статистика откликов\n"
        "/resumes - Список резюме\n"
        "/contacts - Экспорт контактов (последние 20)\n"
        "/help - Помощь",
        parse_mode='Markdown'
    )


async def apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /apply - отправка откликов"""
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен")
        return

    await update.message.reply_text("📤 Начинаю рассылку откликов...")
    
    output, code = run_command([
        VENV_PATH, '-m', 'hh_applicant_tool',
        'apply-similar', '-L', 'cover_letter.txt', '-f'
    ])
    
    # Обрезаем вывод если слишком длинный
    if len(output) > 4000:
        output = output[-4000:]
    
    await update.message.reply_text(
        f"{'✅' if code == 0 else '❌'} Результат:\n\n{output}"
    )


async def update_resumes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /update - обновление резюме"""
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен")
        return

    await update.message.reply_text("🔄 Обновляю резюме...")
    
    output, code = run_command([VENV_PATH, '-m', 'hh_applicant_tool', 'update-resumes'])
    
    await update.message.reply_text(
        f"{'✅' if code == 0 else '⚠️'} {output}"
    )


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /whoami - информация об аккаунте"""
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен")
        return

    output, code = run_command([VENV_PATH, '-m', 'hh_applicant_tool', 'whoami'])
    
    await update.message.reply_text(output if code == 0 else f"❌ {output}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика"""
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен")
        return

    await update.message.reply_text("📊 Собираю статистику...")
    
    # Общее количество откликов
    output1, _ = run_command([
        VENV_PATH, '-m', 'hh_applicant_tool', 'query',
        'SELECT COUNT(*) as total FROM vacancy_contacts'
    ])
    
    # Контакты с телефонами
    output2, _ = run_command([
        VENV_PATH, '-m', 'hh_applicant_tool', 'query',
        "SELECT COUNT(*) as with_phone FROM vacancy_contacts WHERE phone_numbers != ''"
    ])
    
    # Последние отклики
    output3, _ = run_command([
        VENV_PATH, '-m', 'hh_applicant_tool', 'query',
        "SELECT COUNT(*) as today FROM vacancy_contacts WHERE DATE(created_at) = DATE('now')"
    ])
    
    stats_text = f"📊 *Статистика*\n\n{output1}\n{output2}\n{output3}"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')


async def resumes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /resumes - список резюме"""
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен")
        return

    output, code = run_command([VENV_PATH, '-m', 'hh_applicant_tool', 'list-resumes'])
    
    await update.message.reply_text(output if code == 0 else f"❌ {output}")


async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /contacts - экспорт контактов"""
    if not check_access(update.effective_user.id):
        await update.message.reply_text("⛔ Доступ запрещен")
        return

    await update.message.reply_text("📇 Получаю контакты...")
    
    output, code = run_command([
        VENV_PATH, '-m', 'hh_applicant_tool', 'query',
        "SELECT vacancy_name, employer_name, name, email, phone_numbers, created_at "
        "FROM vacancy_contacts ORDER BY created_at DESC LIMIT 20"
    ])
    
    if len(output) > 4000:
        output = output[:4000] + "\n\n... (обрезано)"
    
    await update.message.reply_text(
        f"📇 *Последние контакты:*\n\n```\n{output}\n```",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "ℹ️ *Справка*\n\n"
        "*Основные команды:*\n"
        "/apply - Запустить рассылку откликов с сопроводительным письмом\n"
        "/update - Поднять резюме (раз в 4 часа)\n"
        "/whoami - Показать информацию об аккаунте\n"
        "/stats - Статистика по откликам\n"
        "/resumes - Список ваших резюме\n"
        "/contacts - Последние 20 контактов работодателей\n\n"
        "*Безопасность:*\n"
        "Бот работает только с вашего сервера и использует ваши токены HH.\n"
        "Никакие данные не передаются третьим лицам.",
        parse_mode='Markdown'
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            f"❌ Произошла ошибка: {str(context.error)}"
        )


async def main_async():
    """Асинхронный запуск бота"""
    if not BOT_TOKEN:
        print("❌ Ошибка: установите переменную окружения TELEGRAM_BOT_TOKEN")
        return

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("apply", apply))
    application.add_handler(CommandHandler("update", update_resumes))
    application.add_handler(CommandHandler("whoami", whoami))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("resumes", resumes))
    application.add_handler(CommandHandler("contacts", contacts))
    application.add_handler(CommandHandler("help", help_command))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    print("🤖 Бот запущен!")
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Ждем остановки
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()


def main():
    """Точка входа"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")


if __name__ == '__main__':
    main()
