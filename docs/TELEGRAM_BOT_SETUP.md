# Настройка Telegram бота для двухфакторной аутентификации

## 1. Создание Telegram бота

### Шаг 1: Создание бота через @BotFather
1. Откройте Telegram и найдите @BotFather
2. Отправьте команду `/newbot`
3. Введите имя бота (например: "Flask App Security Bot")
4. Введите username бота (например: "flask_security_bot")
5. Сохраните полученный токен бота

### Шаг 2: Получение токена
BotFather выдаст вам токен вида:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

## 2. Настройка переменных окружения

### Создайте файл `.env` в корне проекта:
```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_BOT_USERNAME=имя_пользователя_бота
```

### Или установите переменные окружения в системе:
```bash
# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN="ваш_токен_бота"
$env:TELEGRAM_BOT_USERNAME="имя_пользователя_бота"

# Linux/Mac
export TELEGRAM_BOT_TOKEN="ваш_токен_бота"
export TELEGRAM_BOT_USERNAME="имя_пользователя_бота"
```

## 3. Обновление кода для получения chat_id

### Проблема: Как получить chat_id пользователя?

Для отправки сообщений пользователю нужно знать его chat_id. Есть несколько способов:

### Способ 1: Через веб-хук (рекомендуется)

Обновите файл `telegram_bot/routes.py`:

```python
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user, login_user
from datetime import datetime, timedelta
import random
import string
import requests
import os
from . import telegram_bot
from model.db_models import db, User, TelegramVerification, SecurityLog
from security.routes import log_security_event

# Конфигурация Telegram бота
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', 'your_bot_username')

# Словарь для хранения chat_id пользователей (в продакшене используйте Redis или БД)
user_chat_ids = {}

def send_telegram_message(chat_id, message):
    """Отправляет сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки Telegram сообщения: {e}")
        return False

def get_chat_id_by_username(username):
    """Получает chat_id по username (работает только если пользователь уже писал боту)"""
    try:
        # Получаем обновления бота
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['ok']:
            for update in data['result']:
                if 'message' in update:
                    message = update['message']
                    if 'from' in message:
                        user = message['from']
                        if user.get('username') == username:
                            return user['id']
        return None
    except Exception as e:
        print(f"Ошибка получения chat_id: {e}")
        return None

@telegram_bot.route('/webhook', methods=['POST'])
def webhook():
    """Веб-хук для получения сообщений от Telegram"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            user = message['from']
            username = user.get('username')
            
            if username:
                # Сохраняем chat_id пользователя
                user_chat_ids[username] = chat_id
                
                # Отправляем приветственное сообщение
                welcome_message = f"""
🔐 <b>Добро пожаловать в систему безопасности!</b>

Пользователь: @{username}
Chat ID: {chat_id}

Теперь вы будете получать коды подтверждения для входа в систему.

Для настройки 2FA перейдите на сайт и введите ваш username: @{username}
                """
                send_telegram_message(chat_id, welcome_message)
        
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Ошибка обработки веб-хука: {e}")
        return jsonify({'ok': False})

def setup_webhook():
    """Настройка веб-хука для бота"""
    try:
        # URL вашего веб-хука (замените на ваш домен)
        webhook_url = "https://your-domain.com/telegram_bot/webhook"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        data = {'url': webhook_url}
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("Веб-хук успешно настроен")
        else:
            print(f"Ошибка настройки веб-хука: {response.text}")
    except Exception as e:
        print(f"Ошибка настройки веб-хука: {e}")

@telegram_bot.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Настройка Telegram двухфакторной аутентификации"""
    if request.method == 'POST':
        telegram_username = request.form.get('telegram_username')
        
        if not telegram_username:
            flash('Введите имя пользователя Telegram')
            return redirect(url_for('telegram_bot.setup_2fa'))
        
        # Убираем @ если пользователь его добавил
        if telegram_username.startswith('@'):
            telegram_username = telegram_username[1:]
        
        # Проверяем, есть ли chat_id для этого пользователя
        chat_id = user_chat_ids.get(telegram_username)
        
        if not chat_id:
            # Пытаемся получить chat_id из обновлений
            chat_id = get_chat_id_by_username(telegram_username)
            
        if not chat_id:
            flash(f'Пользователь @{telegram_username} не найден. Убедитесь, что вы написали боту @{TELEGRAM_BOT_USERNAME}')
            return redirect(url_for('telegram_bot.setup_2fa'))
        
        # Генерируем код подтверждения
        verification_code = generate_verification_code()
        
        # Создаем запись верификации
        verification = TelegramVerification(
            user_id=current_user.id,
            code=verification_code,
            ip_address=request.remote_addr,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(verification)
        db.session.commit()
        
        # Отправляем сообщение в Telegram
        message = f"""
🔐 <b>Код подтверждения для Flask App</b>

Пользователь: <b>{current_user.username}</b>
Код: <b>{verification_code}</b>

⏰ Код действителен 10 минут
🌐 IP: {request.remote_addr}

Для подтверждения введите этот код на сайте.
        """
        
        # Отправляем сообщение
        if send_telegram_message(chat_id, message):
            flash(f'Код подтверждения отправлен в Telegram пользователю @{telegram_username}')
        else:
            flash('Ошибка отправки кода. Попробуйте еще раз.')
            return redirect(url_for('telegram_bot.setup_2fa'))
        
        # Сохраняем данные в сессии для подтверждения
        session['telegram_username'] = telegram_username
        session['verification_id'] = verification.id
        session['chat_id'] = chat_id
        
        return redirect(url_for('telegram_bot.confirm_2fa'))
    
    return render_template('telegram_bot/setup_2fa.html')

@telegram_bot.route('/confirm-2fa', methods=['GET', 'POST'])
@login_required
def confirm_2fa():
    """Подтверждение настройки Telegram 2FA"""
    if 'verification_id' not in session:
        flash('Сначала настройте Telegram 2FA')
        return redirect(url_for('telegram_bot.setup_2fa'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        verification_id = session.get('verification_id')
        
        # Проверяем код
        verification = TelegramVerification.query.get(verification_id)
        
        if not verification or not verification.is_valid():
            flash('Неверный или истекший код')
            return redirect(url_for('telegram_bot.confirm_2fa'))
        
        if verification.code != code:
            flash('Неверный код подтверждения')
            return redirect(url_for('telegram_bot.confirm_2fa'))
        
        # Активируем 2FA
        telegram_username = session.get('telegram_username')
        chat_id = session.get('chat_id')
        
        current_user.enable_telegram_2fa(
            chat_id=str(chat_id),  # Сохраняем chat_id
            username=telegram_username
        )
        
        # Отмечаем код как использованный
        verification.used = True
        db.session.commit()
        
        # Логируем событие
        log_security_event(
            user_id=current_user.id,
            event_type='telegram_2fa_enabled',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details=f'Telegram 2FA включен для @{telegram_username}'
        )
        
        # Очищаем сессию
        session.pop('verification_id', None)
        session.pop('telegram_username', None)
        session.pop('chat_id', None)
        
        flash('Telegram двухфакторная аутентификация успешно включена!')
        return redirect(url_for('profile'))
    
    return render_template('telegram_bot/confirm_2fa.html')

def send_login_verification(user, ip_address):
    """Отправляет код подтверждения для входа"""
    if not user.telegram_enabled or not user.telegram_chat_id:
        return False
    
    # Генерируем код подтверждения
    verification_code = generate_verification_code()
    
    # Создаем запись верификации
    verification = TelegramVerification(
        user_id=user.id,
        code=verification_code,
        ip_address=ip_address,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.session.add(verification)
    db.session.commit()
    
    # Отправляем сообщение в Telegram
    message = f"""
🚨 <b>Попытка входа в Flask App</b>

Пользователь: <b>{user.username}</b>
Код подтверждения: <b>{verification_code}</b>
IP: {ip_address}
Время: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}

⏰ Код действителен 5 минут

Если это вы, введите код на сайте.
Если нет - игнорируйте это сообщение.
    """
    
    # Отправляем сообщение
    if send_telegram_message(user.telegram_chat_id, message):
        return verification.id
    else:
        return False
```

## 4. Обновление модели User

Обновите метод `enable_telegram_2fa` в модели User:

```python
def enable_telegram_2fa(self, chat_id, username):
    """Включает Telegram 2FA"""
    self.telegram_enabled = True
    self.telegram_chat_id = chat_id  # Сохраняем chat_id
    self.telegram_username = username
    self.updated_at = datetime.utcnow()
```

## 5. Инструкция для пользователей

### Как пользователю настроить 2FA:

1. **Найдите бота**: В Telegram найдите вашего бота по username
2. **Напишите боту**: Отправьте любое сообщение боту (например, "/start")
3. **Настройте 2FA**: На сайте перейдите в профиль → Безопасность → Включить Telegram 2FA
4. **Введите username**: Введите ваш Telegram username (без @)
5. **Получите код**: Бот отправит вам код подтверждения
6. **Подтвердите**: Введите код на сайте

## 6. Альтернативный способ (без веб-хука)

Если у вас нет возможности настроить веб-хук, можно использовать polling:

```python
def get_user_chat_id(username):
    """Получает chat_id пользователя через polling"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['ok']:
            for update in data['result']:
                if 'message' in update:
                    message = update['message']
                    if 'from' in message:
                        user = message['from']
                        if user.get('username') == username:
                            return user['id']
        return None
    except Exception as e:
        print(f"Ошибка получения chat_id: {e}")
        return None
```

## 7. Тестирование

1. Создайте бота через @BotFather
2. Установите переменные окружения
3. Запустите приложение
4. Напишите боту в Telegram
5. Попробуйте настроить 2FA на сайте

## 8. Безопасность

- Храните токен бота в секрете
- Используйте HTTPS для веб-хуков
- Ограничьте доступ к API бота
- Логируйте все попытки использования 2FA 