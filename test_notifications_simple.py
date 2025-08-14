#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест для проверки работы уведомлений о сообщениях
"""

import requests
import json
import time

def test_messages_api():
    """Тестируем API для сообщений"""
    
    # Базовый URL (измените на ваш)
    base_url = "http://localhost:5000"
    
    print("🧪 Тестирование API уведомлений о сообщениях")
    print("=" * 50)
    
    # Тест 1: Проверка количества непрочитанных сообщений
    print("\n1️⃣ Тест API /messages/api/unread-count")
    try:
        response = requests.get(f"{base_url}/messages/api/unread-count")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    # Тест 2: Проверка последних сообщений
    print("\n2️⃣ Тест API /messages/api/latest-messages")
    try:
        response = requests.get(f"{base_url}/messages/api/latest-messages")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    # Тест 3: Проверка статуса сообщений
    print("\n3️⃣ Тест API /messages/api/status")
    try:
        response = requests.get(f"{base_url}/messages/api/status")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

def test_forum_notifications():
    """Тестируем API для уведомлений форума"""
    
    base_url = "http://localhost:5000"
    
    print("\n\n🧪 Тестирование API уведомлений форума")
    print("=" * 50)
    
    # Тест 1: Проверка количества уведомлений форума
    print("\n1️⃣ Тест API /forum/notifications/count")
    try:
        response = requests.get(f"{base_url}/forum/notifications/count")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

if __name__ == "__main__":
    print("🔍 Запуск тестов уведомлений...")
    print("Убедитесь, что Flask сервер запущен на http://localhost:5000")
    print("И вы авторизованы в системе")
    
    # Ждем немного для запуска сервера
    time.sleep(2)
    
    test_messages_api()
    test_forum_notifications()
    
    print("\n✅ Тестирование завершено!")
    print("\n💡 Для проверки в браузере:")
    print("1. Откройте http://localhost:5000")
    print("2. Войдите в систему")
    print("3. Откройте консоль разработчика (F12)")
    print("4. Проверьте логи на наличие ошибок")
    print("5. Попробуйте вызвать window.testMessageNotification() в консоли") 