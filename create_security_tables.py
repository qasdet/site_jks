from app import create_app
from model.db_models import db, LoginAttempt, SecurityLog
from sqlalchemy import text

def create_security_tables():
    """Создает таблицы безопасности"""
    app = create_app()
    
    with app.app_context():
        try:
            # Создаем таблицы через SQLAlchemy
            db.create_all()
            print("✅ Таблицы безопасности созданы/обновлены")
            
            # Проверяем существование таблиц
            with db.engine.connect() as conn:
                # Проверяем таблицу login_attempt
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='login_attempt'"))
                if result.fetchone():
                    print("✅ Таблица login_attempt существует")
                else:
                    print("❌ Таблица login_attempt не найдена")
                
                # Проверяем таблицу security_log
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='security_log'"))
                if result.fetchone():
                    print("✅ Таблица security_log существует")
                else:
                    print("❌ Таблица security_log не найдена")
                
                # Создаем индексы для производительности
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_attempt_username ON login_attempt(username)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_attempt_ip ON login_attempt(ip_address)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_attempt_time ON login_attempt(attempted_at)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_security_log_user ON security_log(user_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_security_log_type ON security_log(event_type)"))
                    conn.commit()
                    print("✅ Индексы безопасности созданы")
                except Exception as e:
                    print(f"⚠️ Ошибка при создании индексов: {e}")
                    
        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")
        
        print("🎉 Создание таблиц безопасности завершено!")

if __name__ == "__main__":
    create_security_tables() 