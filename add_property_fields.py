#!/usr/bin/env python3
"""
Скрипт для добавления новых полей в таблицу Property
Добавляет поля: street, house_number, entrance, floor
"""

import sqlite3
import os
from datetime import datetime

def add_property_fields():
    """Добавляет новые поля в таблицу Property"""
    
    # Путь к базе данных
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Проверяем текущую структуру таблицы Property...")
        
        # Получаем информацию о таблице
        cursor.execute("PRAGMA table_info(property)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Текущие поля: {', '.join(column_names)}")
        
        # Проверяем, какие поля нужно добавить
        new_fields = []
        
        if 'street' not in column_names:
            new_fields.append("ADD COLUMN street VARCHAR(200) NOT NULL DEFAULT 'Не указано'")
        
        if 'house_number' not in column_names:
            new_fields.append("ADD COLUMN house_number VARCHAR(20) NOT NULL DEFAULT 'Не указано'")
        
        if 'entrance' not in column_names:
            new_fields.append("ADD COLUMN entrance VARCHAR(10)")
        
        if 'floor' not in column_names:
            new_fields.append("ADD COLUMN floor INTEGER")
        
        if not new_fields:
            print("✅ Все новые поля уже существуют в таблице Property")
            return True
        
        print(f"🔧 Добавляем новые поля: {len(new_fields)}")
        
        # Добавляем новые поля
        for field in new_fields:
            try:
                sql = f"ALTER TABLE property {field}"
                print(f"   Выполняем: {sql}")
                cursor.execute(sql)
                print(f"   ✅ Поле добавлено успешно")
            except sqlite3.OperationalError as e:
                print(f"   ⚠️ Ошибка при добавлении поля: {e}")
                # Продолжаем с другими полями
        
        # Сохраняем изменения
        conn.commit()
        
        # Проверяем результат
        cursor.execute("PRAGMA table_info(property)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Обновленные поля: {', '.join(column_names)}")
        
        # Обновляем существующие записи с дефолтными значениями
        print("🔄 Обновляем существующие записи...")
        
        # Обновляем записи, где street или house_number равны дефолтным значениям
        cursor.execute("""
            UPDATE property 
            SET street = 'Не указано', house_number = 'Не указано' 
            WHERE street = 'Не указано' OR house_number = 'Не указано'
        """)
        
        updated_count = cursor.rowcount
        if updated_count > 0:
            print(f"   ✅ Обновлено записей: {updated_count}")
        
        conn.commit()
        conn.close()
        
        print("✅ Миграция завершена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск миграции для добавления полей собственности")
    print("=" * 60)
    
    success = add_property_fields()
    
    print("=" * 60)
    if success:
        print("🎉 Миграция выполнена успешно!")
        print("📝 Теперь в таблице Property доступны новые поля:")
        print("   • street - название улицы")
        print("   • house_number - номер дома")
        print("   • entrance - подъезд (необязательно)")
        print("   • floor - этаж (необязательно)")
    else:
        print("💥 Миграция завершилась с ошибками!")
        print("🔧 Проверьте логи и попробуйте снова") 