from app import create_app
from model.db_models import db
from sqlalchemy import text

def fix_database_migration():
    """Исправляет миграцию базы данных для SQLite"""
    app = create_app()
    
    with app.app_context():
        # Добавляем новые поля в таблицу user по одному (SQLite ограничение)
        try:
            with db.engine.connect() as conn:
                # Проверяем существование колонок и добавляем их по одной
                columns_to_add = [
                    ('last_login', 'DATETIME'),
                    ('failed_login_attempts', 'INTEGER DEFAULT 0'),
                    ('locked_until', 'DATETIME'),
                    ('password_changed_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
                    ('require_password_change', 'BOOLEAN DEFAULT FALSE')
                ]
                
                for column_name, column_type in columns_to_add:
                    try:
                        # Проверяем, существует ли колонка
                        result = conn.execute(text(f"PRAGMA table_info(user)"))
                        columns = [row[1] for row in result.fetchall()]
                        
                        if column_name not in columns:
                            conn.execute(text(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}"))
                            print(f"✅ Добавлена колонка {column_name}")
                        else:
                            print(f"⚠️ Колонка {column_name} уже существует")
                    except Exception as e:
                        print(f"❌ Ошибка при добавлении колонки {column_name}: {e}")
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Ошибка при работе с базой данных: {e}")
        
        print("🎉 Миграция базы данных завершена!")

if __name__ == "__main__":
    fix_database_migration() 