import sqlite3
import os
from datetime import datetime

def update_database():
    """Обновляет базу данных, добавляя все необходимые поля"""
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Начинаю обновление базы данных...")
        
        # 1. Добавляем поле image_url в forum_topic
        cursor.execute("PRAGMA table_info(forum_topic)")
        forum_topic_columns = [column[1] for column in cursor.fetchall()]
        
        if 'image_url' not in forum_topic_columns:
            cursor.execute("ALTER TABLE forum_topic ADD COLUMN image_url VARCHAR(500)")
            print("✅ Добавлено поле image_url в таблицу forum_topic")
        else:
            print("ℹ️ Поле image_url уже существует в forum_topic")
        
        # 2. Проверяем и добавляем поле parent_id в forum_post
        cursor.execute("PRAGMA table_info(forum_post)")
        forum_post_columns = [column[1] for column in cursor.fetchall()]
        
        if 'parent_id' not in forum_post_columns:
            cursor.execute("ALTER TABLE forum_post ADD COLUMN parent_id INTEGER")
            print("✅ Добавлено поле parent_id в таблицу forum_post")
        else:
            print("ℹ️ Поле parent_id уже существует в forum_post")
        
        # 3. Проверяем и добавляем поле updated_at в forum_post
        if 'updated_at' not in forum_post_columns:
            cursor.execute("ALTER TABLE forum_post ADD COLUMN updated_at DATETIME")
            # Устанавливаем updated_at равным created_at для существующих записей
            cursor.execute("UPDATE forum_post SET updated_at = created_at WHERE updated_at IS NULL")
            print("✅ Добавлено поле updated_at в таблицу forum_post")
        else:
            print("ℹ️ Поле updated_at уже существует в forum_post")
        
        # 4. Проверяем и добавляем поле updated_at в post (блог)
        cursor.execute("PRAGMA table_info(post)")
        post_columns = [column[1] for column in cursor.fetchall()]
        
        if 'updated_at' not in post_columns:
            cursor.execute("ALTER TABLE post ADD COLUMN updated_at DATETIME")
            # Устанавливаем updated_at равным created_at для существующих записей
            cursor.execute("UPDATE post SET updated_at = created_at WHERE updated_at IS NULL")
            print("✅ Добавлено поле updated_at в таблицу post")
        else:
            print("ℹ️ Поле updated_at уже существует в post")
        
        # 5. Проверяем и добавляем поле is_active в user
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in user_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✅ Добавлено поле is_active в таблицу user")
        else:
            print("ℹ️ Поле is_active уже существует в user")
        
        # 6. Проверяем и добавляем поле created_at в user
        if 'created_at' not in user_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
            # Устанавливаем текущее время для существующих пользователей
            current_time = datetime.utcnow().isoformat()
            cursor.execute("UPDATE user SET created_at = ? WHERE created_at IS NULL", (current_time,))
            print("✅ Добавлено поле created_at в таблицу user")
        else:
            print("ℹ️ Поле created_at уже существует в user")
        
        # 7. Проверяем и добавляем поле created_at в property
        cursor.execute("PRAGMA table_info(property)")
        property_columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' not in property_columns:
            cursor.execute("ALTER TABLE property ADD COLUMN created_at DATETIME")
            # Устанавливаем текущее время для существующих записей
            current_time = datetime.utcnow().isoformat()
            cursor.execute("UPDATE property SET created_at = ? WHERE created_at IS NULL", (current_time,))
            print("✅ Добавлено поле created_at в таблицу property")
        else:
            print("ℹ️ Поле created_at уже существует в property")
        
        # 8. Проверяем и добавляем поле created_at в voting
        cursor.execute("PRAGMA table_info(voting)")
        voting_columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' not in voting_columns:
            cursor.execute("ALTER TABLE voting ADD COLUMN created_at DATETIME")
            # Устанавливаем текущее время для существующих записей
            current_time = datetime.utcnow().isoformat()
            cursor.execute("UPDATE voting SET created_at = ? WHERE created_at IS NULL", (current_time,))
            print("✅ Добавлено поле created_at в таблицу voting")
        else:
            print("ℹ️ Поле created_at уже существует в voting")
        
        # 9. Проверяем и добавляем поле created_at в forum_topic
        if 'created_at' not in forum_topic_columns:
            cursor.execute("ALTER TABLE forum_topic ADD COLUMN created_at DATETIME")
            # Устанавливаем текущее время для существующих записей
            current_time = datetime.utcnow().isoformat()
            cursor.execute("UPDATE forum_topic SET created_at = ? WHERE created_at IS NULL", (current_time,))
            print("✅ Добавлено поле created_at в таблицу forum_topic")
        else:
            print("ℹ️ Поле created_at уже существует в forum_topic")
        
        # 10. Проверяем и добавляем поле created_at в forum_post
        if 'created_at' not in forum_post_columns:
            cursor.execute("ALTER TABLE forum_post ADD COLUMN created_at DATETIME")
            # Устанавливаем текущее время для существующих записей
            current_time = datetime.utcnow().isoformat()
            cursor.execute("UPDATE forum_post SET created_at = ? WHERE created_at IS NULL", (current_time,))
            print("✅ Добавлено поле created_at в таблицу forum_post")
        else:
            print("ℹ️ Поле created_at уже существует в forum_post")
        
        # 11. Проверяем и создаем таблицу уведомлений
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE notification (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    related_id INTEGER,
                    is_read BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')
            
            # Создаем индексы для уведомлений
            cursor.execute('CREATE INDEX idx_notification_user_id ON notification (user_id)')
            cursor.execute('CREATE INDEX idx_notification_is_read ON notification (is_read)')
            cursor.execute('CREATE INDEX idx_notification_created_at ON notification (created_at)')
            
            print("✅ Создана таблица notification")
            print("✅ Созданы индексы для уведомлений")
        else:
            print("ℹ️ Таблица notification уже существует")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print("🎉 База данных успешно обновлена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")
        return False

def show_database_info():
    """Показывает информацию о структуре базы данных"""
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 Информация о структуре базы данных:")
        print("=" * 50)
        
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Таблица: {table_name}")
            print("-" * 30)
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for column in columns:
                col_id, col_name, col_type, not_null, default_val, pk = column
                pk_mark = " 🔑" if pk else ""
                not_null_mark = " NOT NULL" if not_null else ""
                default_mark = f" DEFAULT {default_val}" if default_val else ""
                print(f"  • {col_name} ({col_type}){not_null_mark}{default_mark}{pk_mark}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении информации о базе данных: {e}")

if __name__ == "__main__":
    print("🚀 Скрипт обновления базы данных")
    print("=" * 40)
    
    # Обновляем базу данных
    success = update_database()
    
    if success:
        # Показываем информацию о структуре
        show_database_info()
    else:
        print("❌ Обновление базы данных не удалось!") 