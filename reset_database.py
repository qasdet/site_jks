import sqlite3
import os
from datetime import datetime

def reset_database():
    """Полностью пересоздает базу данных"""
    db_path = 'instance/app.db'
    
    # Удаляем существующую базу данных
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("🗑️ Существующая база данных удалена")
        except Exception as e:
            print(f"❌ Ошибка при удалении базы данных: {e}")
            return False
    
    try:
        # Создаем новую базу данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Создаю новую базу данных...")
        
        # Создаем таблицу пользователей
        cursor.execute('''
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        print("✅ Создана таблица user")
        
        # Создаем таблицу постов блога
        cursor.execute('''
            CREATE TABLE post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        print("✅ Создана таблица post")
        
        # Создаем таблицу собственности
        cursor.execute('''
            CREATE TABLE property (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number VARCHAR(20) UNIQUE NOT NULL,
                area FLOAT NOT NULL,
                owner_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES user (id)
            )
        ''')
        print("✅ Создана таблица property")
        
        # Создаем таблицу голосований
        cursor.execute('''
            CREATE TABLE voting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                question VARCHAR(500) NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES user (id)
            )
        ''')
        print("✅ Создана таблица voting")
        
        # Создаем таблицу вариантов голосования
        cursor.execute('''
            CREATE TABLE voting_option (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text VARCHAR(200) NOT NULL,
                voting_id INTEGER NOT NULL,
                FOREIGN KEY (voting_id) REFERENCES voting (id)
            )
        ''')
        print("✅ Создана таблица voting_option")
        
        # Создаем таблицу голосов
        cursor.execute('''
            CREATE TABLE vote (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voting_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (voting_id) REFERENCES voting (id),
                FOREIGN KEY (property_id) REFERENCES property (id),
                FOREIGN KEY (option_id) REFERENCES voting_option (id)
            )
        ''')
        print("✅ Создана таблица vote")
        
        # Создаем таблицу тем форума
        cursor.execute('''
            CREATE TABLE forum_topic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                image_url VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        print("✅ Создана таблица forum_topic")
        
        # Создаем таблицу сообщений форума
        cursor.execute('''
            CREATE TABLE forum_post (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                parent_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES user (id),
                FOREIGN KEY (topic_id) REFERENCES forum_topic (id),
                FOREIGN KEY (parent_id) REFERENCES forum_post (id)
            )
        ''')
        print("✅ Создана таблица forum_post")
        
        # Создаем индексы для улучшения производительности
        cursor.execute('CREATE INDEX idx_post_user_id ON post (user_id)')
        cursor.execute('CREATE INDEX idx_property_owner_id ON property (owner_id)')
        cursor.execute('CREATE INDEX idx_voting_created_by ON voting (created_by)')
        cursor.execute('CREATE INDEX idx_vote_voting_id ON vote (voting_id)')
        cursor.execute('CREATE INDEX idx_vote_property_id ON vote (property_id)')
        cursor.execute('CREATE INDEX idx_vote_option_id ON vote (option_id)')
        cursor.execute('CREATE INDEX idx_voting_option_voting_id ON voting_option (voting_id)')
        cursor.execute('CREATE INDEX idx_forum_topic_user_id ON forum_topic (user_id)')
        cursor.execute('CREATE INDEX idx_forum_post_user_id ON forum_post (user_id)')
        cursor.execute('CREATE INDEX idx_forum_post_topic_id ON forum_post (topic_id)')
        cursor.execute('CREATE INDEX idx_forum_post_parent_id ON forum_post (parent_id)')
        print("✅ Созданы индексы")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print("🎉 База данных успешно создана!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании базы данных: {e}")
        return False

def create_sample_data():
    """Создает тестовые данные"""
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Создаю тестовые данные...")
        
        # Создаем тестового пользователя
        cursor.execute('''
            INSERT INTO user (username, email, password_hash, created_at, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@example.com', 'pbkdf2:sha256:600000$test$hash', datetime.utcnow().isoformat(), 1))
        
        user_id = cursor.lastrowid
        print(f"✅ Создан тестовый пользователь (ID: {user_id})")
        
        # Создаем тестовую собственность
        cursor.execute('''
            INSERT INTO property (number, area, owner_id, created_at)
            VALUES (?, ?, ?, ?)
        ''', ('101', 45.5, user_id, datetime.utcnow().isoformat()))
        
        property_id = cursor.lastrowid
        print(f"✅ Создана тестовая собственность (ID: {property_id})")
        
        # Создаем тестовый пост блога
        cursor.execute('''
            INSERT INTO post (title, content, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Добро пожаловать!', 'Это первый пост в блоге жильцов.', user_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        print("✅ Создан тестовый пост блога")
        
        # Создаем тестовую тему форума
        cursor.execute('''
            INSERT INTO forum_topic (title, user_id, created_at)
            VALUES (?, ?, ?)
        ''', ('Общие вопросы', user_id, datetime.utcnow().isoformat()))
        
        topic_id = cursor.lastrowid
        print(f"✅ Создана тестовая тема форума (ID: {topic_id})")
        
        # Создаем тестовое сообщение в теме
        cursor.execute('''
            INSERT INTO forum_post (content, user_id, topic_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Добро пожаловать на форум жильцов!', user_id, topic_id, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        print("✅ Создано тестовое сообщение форума")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print("🎉 Тестовые данные успешно созданы!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Скрипт сброса базы данных")
    print("=" * 40)
    
    # Сбрасываем базу данных
    success = reset_database()
    
    if success:
        # Создаем тестовые данные
        create_sample_data()
        print("\n✅ База данных готова к использованию!")
    else:
        print("❌ Сброс базы данных не удался!") 