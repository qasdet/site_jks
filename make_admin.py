from app import app, db
from model.db_models import User
from sqlalchemy import text

def make_admin(username):
    """Назначает пользователя администратором"""
    with app.app_context():
        try:
            # Обновляем пользователя
            db.session.execute(
                text('UPDATE user SET is_admin = 1 WHERE username = :username'),
                {'username': username}
            )
            db.session.commit()
            
            # Проверяем результат
            user = User.query.filter_by(username=username).first()
            if user and user.is_admin:
                print(f'✅ Пользователь {username} успешно назначен администратором')
            else:
                print(f'❌ Пользователь {username} не найден')
                
        except Exception as e:
            print(f'❌ Ошибка: {e}')

def list_users():
    """Показывает список всех пользователей"""
    with app.app_context():
        users = User.query.all()
        print('\n📋 Список пользователей:')
        print('-' * 50)
        for user in users:
            admin_status = '👑 Админ' if user.is_admin else '👤 Пользователь'
            print(f'{user.id:2d} | {user.username:15s} | {user.email:25s} | {admin_status}')
        print('-' * 50)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
        make_admin(username)
    else:
        print('Использование: python make_admin.py <username>')
        print('\nПример: python make_admin.py admin')
        list_users() 