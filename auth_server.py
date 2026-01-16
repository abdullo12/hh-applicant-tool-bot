#!/usr/bin/env python3
"""Веб-сервер для OAuth авторизации HH.RU"""

import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# Конфиг
CLIENT_ID = "HIOMIAS39CA9DICTA7JIO64LQKQJF5AGIK74G9ITJKLNEDAOH5FHS5G1JI7FOEGD"
CLIENT_SECRET = "V9M870DE342BGHFRUJ5FTCGCUA1482AN0DI8C5TFI9ULMA89H10N60NOP8I4JMVS"
REDIRECT_URI = os.getenv('APP_URL', 'http://localhost:5000') + '/callback'
DB_PATH = Path(__file__).parent / 'users.db'

# HTML шаблоны
SUCCESS_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Авторизация успешна</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 400px;
        }
        .success-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .button {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✅</div>
        <h1>Авторизация успешна!</h1>
        <p>Вы успешно авторизовались на HH.RU</p>
        <p>Теперь вернитесь в Telegram бот и используйте команду <code>/apply</code> для отправки откликов</p>
        <a href="https://t.me/clever8_bot" class="button">Открыть бота</a>
    </div>
</body>
</html>
"""

ERROR_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ошибка авторизации</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 400px;
        }
        .error-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .button {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: #f5576c;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="error-icon">❌</div>
        <h1>Ошибка авторизации</h1>
        <p>{{ error }}</p>
        <a href="https://t.me/clever8_bot" class="button">Попробовать снова</a>
    </div>
</body>
</html>
"""


@app.route('/auth')
def auth():
    """Перенаправление на HH для авторизации"""
    user_id = request.args.get('user_id')
    if not user_id:
        return "Missing user_id", 400
    
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'state': user_id  # Передаем telegram_id через state
    }
    
    auth_url = f"https://hh.ru/oauth/authorize?{urlencode(params)}"
    return redirect(auth_url)


@app.route('/callback')
def callback():
    """Обработка callback от HH"""
    code = request.args.get('code')
    state = request.args.get('state')  # telegram_id
    error = request.args.get('error')
    
    if error:
        return render_template_string(ERROR_PAGE, error=f"HH вернул ошибку: {error}")
    
    if not code or not state:
        return render_template_string(ERROR_PAGE, error="Отсутствуют необходимые параметры")
    
    # Обмениваем code на токены
    import requests
    
    try:
        response = requests.post('https://hh.ru/oauth/token', data={
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': REDIRECT_URI
        })
        
        if response.status_code != 200:
            return render_template_string(ERROR_PAGE, error=f"Ошибка получения токена: {response.text}")
        
        tokens = response.json()
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        expires_at = int(time.time()) + tokens.get('expires_in', 0)
        
        # Получаем информацию о пользователе
        me_response = requests.get('https://api.hh.ru/me', headers={
            'Authorization': f'Bearer {access_token}'
        })
        
        if me_response.status_code != 200:
            return render_template_string(ERROR_PAGE, error="Не удалось получить информацию о пользователе")
        
        user_info = me_response.json()
        username = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        
        # Сохраняем в БД
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO users (telegram_id, username, access_token, refresh_token, access_expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (int(state), username, access_token, refresh_token, expires_at))
        conn.commit()
        conn.close()
        
        return render_template_string(SUCCESS_PAGE)
        
    except Exception as e:
        return render_template_string(ERROR_PAGE, error=f"Ошибка: {str(e)}")


@app.route('/health')
def health():
    """Health check"""
    return {'status': 'ok'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
