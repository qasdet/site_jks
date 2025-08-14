"""
Конфигурация Telegram бота для двухфакторной аутентификации
"""

import os

# Настройки Telegram бота
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', 'your_bot_username')

# Настройки безопасности
VERIFICATION_CODE_LENGTH = 6
VERIFICATION_CODE_EXPIRY_MINUTES = 10
LOGIN_VERIFICATION_EXPIRY_MINUTES = 5

# Настройки сообщений
MESSAGE_TEMPLATES = {
    'welcome': """
🔐 <b>Добро пожаловать в систему безопасности!</b>

Пользователь: @{username}
Chat ID: {chat_id}

Теперь вы будете получать коды подтверждения для входа в систему.

Для настройки 2FA перейдите на сайт и введите ваш username: @{username}
    """,
    
    'setup_code': """
🔐 <b>Код подтверждения для Flask App</b>

Пользователь: <b>{username}</b>
Код: <b>{code}</b>

⏰ Код действителен {expiry} минут
🌐 IP: {ip}

Для подтверждения введите этот код на сайте.
    """,
    
    'login_code': """
🚨 <b>Попытка входа в Flask App</b>

Пользователь: <b>{username}</b>
Код подтверждения: <b>{code}</b>
IP: {ip}
Время: {time}

⏰ Код действителен {expiry} минут

Если это вы, введите код на сайте.
Если нет - игнорируйте это сообщение.
    """,
    
    'login_success': """
✅ <b>Успешный вход в систему</b>

Пользователь: <b>{username}</b>
Время: {time}
IP: {ip}

Вход выполнен успешно с использованием Telegram 2FA.
    """,
    
    'login_failed': """
❌ <b>Неудачная попытка входа</b>

Пользователь: <b>{username}</b>
Время: {time}
IP: {ip}

Кто-то пытался войти в ваш аккаунт с неверным кодом.
    """
}

def is_bot_configured():
    """Проверяет, настроен ли бот"""
    return (TELEGRAM_BOT_TOKEN and 
            TELEGRAM_BOT_TOKEN != 'your_bot_token_here' and
            TELEGRAM_BOT_USERNAME and 
            TELEGRAM_BOT_USERNAME != 'your_bot_username')

def get_bot_info():
    """Возвращает информацию о боте"""
    return {
        'token': TELEGRAM_BOT_TOKEN,
        'username': TELEGRAM_BOT_USERNAME,
        'configured': is_bot_configured()
    }

def format_message(template_name, **kwargs):
    """Форматирует сообщение по шаблону"""
    template = MESSAGE_TEMPLATES.get(template_name, '')
    return template.format(**kwargs) 