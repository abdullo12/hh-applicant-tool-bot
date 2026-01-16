#!/usr/bin/env python3
"""Публичный Telegram бот для HH Applicant Tool (мультипользовательский)"""

import asyncio
import logging
import os
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_DIR = Path(__file__).parent
USERS_DIR = BASE_DIR / 'users_data'
USERS_DIR.mkdir(exist_ok=True)

# База данных пользователей
DB_PATH = BASE_DIR / 'users.db'


def init_db():
    """Инициализация базы пользователей"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            access_token TEXT,
            refresh_token TEXT,
            access_expires_at INTEGER,
            cover_letter TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_apply TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def get_user(telegram_id: int):
    """Получить данные пользователя"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user


def save_user_tokens(telegram_id: int, username: str, access_token: str, refresh_token: str, expires_at: int):
    """Сохранить токены пользователя"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users (telegram_id, username, access_token, refresh_token, access_expires_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (telegram_id, username, access_token, refresh_token, expires_at))
    conn.commit()
    conn.close()


def save_cover_letter(telegram_id: int, text: str):
    """Сохранить сопроводительное письмо"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET cover_letter = ? WHERE telegram_id = ?', (text, telegram_id))
    conn.commit()
    conn.close()


def run_command_for_user(telegram_id: int, cmd: list[str]) -> tuple[str, int]:
    """Выполнить команду для конкретного пользователя"""
    user = get_user(telegram_id)
    if not user:
        return "❌ Вы не авторизованы. Используйте /auth", 1
    
    # Создаем временный конфиг для пользователя
    user_dir = USERS_DIR / str(telegram_id)
    user_dir.mkdir(exist_ok=True)
    
    config_file = user_dir / 'config.json'
    config_file.write_text(f'''{{
        "token": {{
            "access_token": "{user[3]}",
            "refresh_token": "{user[4]}",
            "access_expires_at": {user[5]}
        }}
    }}''')
    
    # Сопроводительное письмо
    if user[6]:
        cover_file = user_dir / 'cover_letter.txt'
        cover_file.write_text(user[6])
    
    try:
        result = subprocess.run(
            ['python', '-m', 'hh_applicant_tool', '-c', str(user_dir)] + cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return f"❌ Ошибка: {str(e)}", 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = get_user(update.effective_user.id)
    
    if user:
        await update.message.reply_text(
            f"👋 С возвращением!\n\n"
            f"Вы авторизованы на HH.RU\n\n"
            f"Доступные команды:\n"
            f"/apply - Отправить отклики\n"
            f"/stats - Статистика\n"
            f"/letter - Изменить сопроводительное письмо\n"
            f"/help - Помощь"
        )
    else:
        keyboard = [[InlineKeyboardButton("🔐 Авторизоваться", callback_data='auth')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *HH Applicant Tool Bot*\n\n"
            "Автоматизация откликов на вакансии HH.RU\n\n"
            "✅ До 200 откликов в день\n"
            "✅ Автоматическое обновление резюме\n"
            "✅ Сохранение контактов HR\n"
            "✅ Статистика откликов\n\n"
            "Для начала работы нужно авторизоваться:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


async def auth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки авторизации"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    
    # Генерируем уникальную ссылку для авторизации
    app_url = os.getenv('APP_URL', 'http://localhost:5000')
    auth_url = f"{app_url}/auth?user_id={telegram_id}"
    
    keyboard = [[InlineKeyboardButton("🔐 Авторизоваться на HH.RU", url=auth_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔐 *Авторизация на HH.RU*\n\n"
        "1. Нажмите кнопку ниже\n"
        "2. Войдите в свой аккаунт HH.RU\n"
        "3. Разрешите доступ\n"
        "4. Вернитесь в бот\n\n"
        "После авторизации вы сможете:\n"
        "• Отправлять отклики автоматически\n"
        "• Обновлять резюме\n"
        "• Получать статистику",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /apply"""
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Сначала авторизуйтесь: /start")
        return
    
    if not user[6]:
        await update.message.reply_text(
            "❌ Сначала создайте сопроводительное письмо:\n"
            "/letter"
        )
        return
    
    await update.message.reply_text("📤 Начинаю рассылку откликов...")
    
    output, code = run_command_for_user(
        update.effective_user.id,
        ['apply-similar', '-L', f'users_data/{update.effective_user.id}/cover_letter.txt', '-f']
    )
    
    if len(output) > 4000:
        output = output[-4000:]
    
    await update.message.reply_text(
        f"{'✅' if code == 0 else '❌'} Результат:\n\n{output}"
    )


async def letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /letter - установка сопроводительного письма"""
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Сначала авторизуйтесь: /start")
        return
    
    if context.args:
        text = ' '.join(context.args)
        save_cover_letter(update.effective_user.id, text)
        await update.message.reply_text("✅ Сопроводительное письмо сохранено!")
    else:
        current = user[6] if user[6] else "Не установлено"
        await update.message.reply_text(
            f"📝 *Сопроводительное письмо*\n\n"
            f"Текущее:\n{current}\n\n"
            f"Чтобы изменить, отправьте:\n"
            f"`/letter Ваш текст письма`",
            parse_mode='Markdown'
        )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Сначала авторизуйтесь: /start")
        return
    
    output, _ = run_command_for_user(update.effective_user.id, ['whoami'])
    await update.message.reply_text(f"📊 *Статистика*\n\n{output}", parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "ℹ️ *Справка*\n\n"
        "*Команды:*\n"
        "/start - Начало работы\n"
        "/apply - Отправить отклики\n"
        "/letter - Сопроводительное письмо\n"
        "/stats - Статистика\n"
        "/help - Эта справка\n\n"
        "*Как это работает:*\n"
        "1. Авторизуйтесь через /start\n"
        "2. Создайте письмо через /letter\n"
        "3. Отправляйте отклики через /apply\n\n"
        "*Лимиты:*\n"
        "• 200 откликов в день (ограничение HH)\n"
        "• Обновление резюме раз в 4 часа",
        parse_mode='Markdown'
    )


async def main_async():
    """Запуск бота"""
    if not BOT_TOKEN:
        print("❌ Установите TELEGRAM_BOT_TOKEN")
        return
    
    init_db()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("apply", apply))
    application.add_handler(CommandHandler("letter", letter))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(auth_callback, pattern='^auth$'))
    
    print("🤖 Публичный бот запущен!")
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")


if __name__ == '__main__':
    main()
