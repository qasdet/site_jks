from app import app, db
from sqlalchemy import text

def add_is_admin_to_user():
    with app.app_context():
        try:
            db.session.execute(text('ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0'))
            db.session.commit()
            print('✅ Поле is_admin успешно добавлено в таблицу user')
        except Exception as e:
            print(f'❌ Ошибка при добавлении поля: {e}')

if __name__ == '__main__':
    add_is_admin_to_user() 