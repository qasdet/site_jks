from app import create_app
from model.db_models import db, User
from datetime import datetime

def update_existing_users():
    """Обновляет существующих пользователей с значениями по умолчанию"""
    app = create_app()
    
    with app.app_context():
        try:
            # Получаем всех пользователей
            users = User.query.all()
            print(f"📊 Найдено пользователей: {len(users)}")
            
            updated_count = 0
            for user in users:
                # Проверяем и обновляем поля безопасности
                needs_update = False
                
                # Устанавливаем password_changed_at если не установлено
                if not hasattr(user, 'password_changed_at') or user.password_changed_at is None:
                    user.password_changed_at = user.created_at
                    needs_update = True
                
                # Устанавливаем require_password_change если не установлено
                if not hasattr(user, 'require_password_change') or user.require_password_change is None:
                    user.require_password_change = False
                    needs_update = True
                
                # Устанавливаем failed_login_attempts если не установлено
                if not hasattr(user, 'failed_login_attempts') or user.failed_login_attempts is None:
                    user.failed_login_attempts = 0
                    needs_update = True
                
                if needs_update:
                    db.session.add(user)
                    updated_count += 1
                    print(f"✅ Обновлен пользователь: {user.username}")
            
            # Сохраняем изменения
            db.session.commit()
            print(f"🎉 Обновлено пользователей: {updated_count}")
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении пользователей: {e}")
            db.session.rollback()
        
        print("🎉 Обновление пользователей завершено!")

if __name__ == "__main__":
    update_existing_users() 