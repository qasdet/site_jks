#!/usr/bin/env python3
"""
Скрипт для добавления таблиц паролей контента в базу данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from model.db_models import db, ContentPassword, ContentAccess

def add_content_password_tables():
    """Добавляет таблицы для паролей контента"""
    app = create_app()
    
    with app.app_context():
        print("Создание таблиц для паролей контента...")
        
        # Создаем таблицы
        db.create_all()
        
        print("✅ Таблицы ContentPassword и ContentAccess успешно созданы!")
        print("Теперь можно использовать функционал паролей для голосований, постов и тем форума.")

if __name__ == '__main__':
    add_content_password_tables() 