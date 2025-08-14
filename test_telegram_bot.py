#!/usr/bin/env python3
"""
Скрипт для тестирования Telegram бота
"""

import os
import requests
import json

def test_telegram_bot():
    """Тестирует подключение к Telegram боту"""
    
    # Получаем токен из переменных окружения
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    username = os.environ.get('TELEGRAM_BOT_USERNAME')
    
    if not token or token == 'your_bot_token_here':
        print("❌ Токен бота не настроен!")
        print("Установите переменную окружения TELEGRAM_BOT_TOKEN")
        return False
    
    if not username or username == 'your_bot_username':
        print("❌ Username бота не настроен!")
        print("Установите переменную окружения TELEGRAM_BOT_USERNAME")
        return False
    
    print(f"🤖 Тестирование бота @{username}")
    print(f"🔑 Токен: {token[:10]}...")
    
    # Тестируем подключение к API
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data['ok']:
            bot_info = data['result']
            print(f"✅ Бот подключен успешно!")
            print(f"   Имя: {bot_info['first_name']}")
            print(f"   Username: @{bot_info['username']}")
            print(f"   ID: {bot_info['id']}")
            
            # Проверяем обновления
            print("\n📋 Проверяем обновления...")
            updates_url = f"https://api.telegram.org/bot{token}/getUpdates"
            updates_response = requests.get(updates_url, timeout=10)
            updates_data = updates_response.json()
            
            if updates_data['ok']:
                updates = updates_data['result']
                print(f"   Получено обновлений: {len(updates)}")
                
                if updates:
                    print("   Последние сообщения:")
                    for update in updates[-3:]:  # Показываем последние 3
                        if 'message' in update:
                            message = update['message']
                            user = message['from']
                            chat_id = message['chat']['id']
                            text = message.get('text', '')
                            username = user.get('username', 'Без username')
                            first_name = user.get('first_name', '')
                            
                            print(f"     👤 @{username} ({first_name}) - Chat ID: {chat_id}")
                            print(f"     💬 {text[:50]}...")
                else:
                    print("   Сообщений пока нет")
            else:
                print(f"   ❌ Ошибка получения обновлений: {updates_data}")
            
            return True
        else:
            print(f"❌ Ошибка подключения к боту: {data}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def send_test_message(chat_id):
    """Отправляет тестовое сообщение"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ Токен бота не настроен!")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': '🧪 Тестовое сообщение от Flask App!',
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Тестовое сообщение отправлено в чат {chat_id}")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

def main():
    """Главная функция"""
    print("🔐 Тестирование Telegram бота для 2FA")
    print("=" * 50)
    
    # Тестируем подключение
    if not test_telegram_bot():
        print("\n❌ Тестирование не удалось!")
        return
    
    print("\n" + "=" * 50)
    print("📝 Инструкция по настройке:")
    print("1. Найдите вашего бота в Telegram")
    print("2. Отправьте ему любое сообщение (например, /start)")
    print("3. Скопируйте Chat ID из списка выше")
    print("4. Используйте этот Chat ID для тестирования")
    
    # Спрашиваем Chat ID для тестирования
    chat_id = input("\nВведите Chat ID для отправки тестового сообщения (или Enter для пропуска): ").strip()
    
    if chat_id:
        send_test_message(chat_id)
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    main() 