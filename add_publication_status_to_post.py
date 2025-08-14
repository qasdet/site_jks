#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления поля статуса публикации к постам блога
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from model.db_models import db, Post
from sqlalchemy import create_engine, text

def add_publication_status():
    """Добавляет поле is_published к таблице постов"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Добавление поля статуса публикации к постам...")
        
        try:
            engine = create_engine('sqlite:///instance/app.db')  # путь к вашей БД
            
            with engine.connect() as conn:
                conn.execute(text('ALTER TABLE post ADD COLUMN is_published BOOLEAN DEFAULT 1'))
            
            print("✅ Поле is_published успешно добавлено к таблице post")
            print("✅ Все существующие посты помечены как опубликованные")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении поля: {e}")
            print("Возможно, поле уже существует")
            
        finally:
            db.session.close()

if __name__ == "__main__":
    add_publication_status() 