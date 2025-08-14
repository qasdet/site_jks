from app import create_app
from model.db_models import db, User
from sqlalchemy import text
from datetime import datetime

def fix_password_changed_at():
    """Добавляет колонку password_changed_at и обновляет существующие записи"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Добавляем колонку без значения по умолчанию
                try:
                    conn.execute(text("ALTER TABLE user ADD COLUMN password_changed_at DATETIME"))
                    print("✅ Добавлена колонка password_changed_at")
                except Exception as e:
                    print(f"⚠️ Колонка уже существует или ошибка: {e}")
                
                # Обновляем существующие записи
                conn.execute(text("UPDATE user SET password_changed_at = created_at WHERE password_changed_at IS NULL"))
                print("✅ Обновлены существующие записи")
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("🎉 Исправление password_changed_at завершено!")

if __name__ == "__main__":
    fix_password_changed_at() 