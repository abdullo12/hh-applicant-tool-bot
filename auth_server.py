#!/usr/bin/env python3
"""Веб-сервер для OAuth авторизации HH.RU"""

import json
import os
import requests
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
    """Инструкция по получению токенов"""
    user_id = request.args.get('user_id')
    if not user_id:
        return "Missing user_id", 400
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Авторизация HH.RU</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 500px;
            margin: 20px auto;
        }
        h1 { color: #333; margin-bottom: 20px; font-size: 22px; }
        .method { 
            background: #f9f9f9; 
            padding: 20px; 
            margin: 15px 0; 
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .method h3 { color: #667eea; margin-bottom: 10px; font-size: 18px; }
        .method p { color: #666; line-height: 1.6; margin: 8px 0; font-size: 14px; }
        code { 
            background: #eee; 
            padding: 3px 8px; 
            border-radius: 4px;
            font-size: 13px;
            display: inline-block;
            margin: 5px 0;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin-top: 20px;
            font-weight: 600;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-top: 20px;
            border-radius: 5px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Как получить токены HH.RU</h1>
        
        <div class="method">
            <h3>📱 Способ 1: Android (рекомендуется)</h3>
            <p>1. Установите приложение для извлечения токенов из HH</p>
            <p>2. Авторизуйтесь в официальном приложении HH</p>
            <p>3. Извлеките <code>access_token</code> и <code>refresh_token</code></p>
            <p>4. Отправьте боту:</p>
            <code>/settoken ACCESS_TOKEN REFRESH_TOKEN</code>
        </div>
        
        <div class="method">
            <h3>💻 Способ 2: Компьютер</h3>
            <p>1. Установите <code>hh-applicant-tool</code></p>
            <p>2. Выполните: <code>hh-applicant-tool auth</code></p>
            <p>3. Получите токены: <code>hh-applicant-tool config</code></p>
            <p>4. Отправьте боту:</p>
            <code>/settoken ACCESS_TOKEN REFRESH_TOKEN</code>
        </div>
        
        <div class="method">
            <h3>👥 Способ 3: Попросите друга</h3>
            <p>Попросите друга с ПК получить токены и отправить вам</p>
        </div>
        
        <div class="warning">
            ⚠️ <strong>Важно:</strong> Не делитесь токенами с незнакомыми людьми!
        </div>
        
        <a href="https://t.me/clever8_bot" class="button">Вернуться в бота</a>
    </div>
</body>
</html>
    ''', user_id=user_id)


@app.route('/do_auth', methods=['POST'])
def do_auth():
    """Выполнение авторизации"""
    data = request.json
    user_id = data.get('user_id')
    login = data.get('login')
    password = data.get('password')
    
    if not all([user_id, login, password]):
        return {'success': False, 'error': 'Не все поля заполнены'}
    
    try:
        # Используем прямую авторизацию
        response = requests.post('https://hh.ru/oauth/token', data={
            'grant_type': 'password',
            'username': login,
            'password': password,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        })
        
        if response.status_code != 200:
            return {'success': False, 'error': 'Неверный логин или пароль'}
        
        tokens = response.json()
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        expires_at = int(time.time()) + tokens.get('expires_in', 0)
        
        # Получаем инфо о пользователе
        me_response = requests.get('https://api.hh.ru/me', headers={
            'Authorization': f'Bearer {access_token}'
        })
        
        if me_response.status_code == 200:
            user_info = me_response.json()
            username = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        else:
            username = login
        
        # Сохраняем в БД
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO users (telegram_id, username, access_token, refresh_token, access_expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (int(user_id), username, access_token, refresh_token, expires_at))
        conn.commit()
        conn.close()
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


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
