from app import create_app
from model.db_models import db
from sqlalchemy import text

def check_and_fix_columns():
    """Проверяет и исправляет колонки в таблице user"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Получаем информацию о таблице user
                result = conn.execute(text("PRAGMA table_info(user)"))
                columns = {row[1]: row[2] for row in result.fetchall()}
                
                print("📋 Текущие колонки в таблице user:")
                for col_name, col_type in columns.items():
                    print(f"  - {col_name}: {col_type}")
                
                # Проверяем необходимые колонки
                required_columns = {
                    'last_login': 'DATETIME',
                    'failed_login_attempts': 'INTEGER DEFAULT 0',
                    'locked_until': 'DATETIME',
                    'password_changed_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
                    'require_password_change': 'BOOLEAN DEFAULT FALSE'
                }
                
                print("\n🔍 Проверка необходимых колонок:")
                for col_name, col_type in required_columns.items():
                    if col_name in columns:
                        print(f"  ✅ {col_name}: существует")
                    else:
                        print(f"  ❌ {col_name}: отсутствует")
                        try:
                            conn.execute(text(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}"))
                            print(f"  ✅ Добавлена колонка {col_name}")
                        except Exception as e:
                            print(f"  ❌ Ошибка при добавлении {col_name}: {e}")
                
                conn.commit()
                
                # Проверяем результат
                result = conn.execute(text("PRAGMA table_info(user)"))
                final_columns = {row[1]: row[2] for row in result.fetchall()}
                
                print("\n📋 Финальные колонки в таблице user:")
                for col_name, col_type in final_columns.items():
                    print(f"  - {col_name}: {col_type}")
                
        except Exception as e:
            print(f"❌ Ошибка при проверке колонок: {e}")
        
        print("\n🎉 Проверка и исправление колонок завершено!")

if __name__ == "__main__":
    check_and_fix_columns() 