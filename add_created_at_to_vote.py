from app import app, db
from model.db_models import Vote
from sqlalchemy import text

def add_created_at_to_vote():
    """Добавляет поле created_at в таблицу Vote"""
    with app.app_context():
        try:
            # Добавляем новое поле created_at
            db.session.execute(text('ALTER TABLE vote ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            db.session.commit()
            print("✅ Поле created_at успешно добавлено в таблицу Vote")
            
            # Обновляем существующие записи, устанавливая created_at равным voted_at
            db.session.execute(text('UPDATE vote SET created_at = voted_at WHERE created_at IS NULL'))
            db.session.commit()
            print("✅ Существующие записи обновлены")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении поля: {e}")
            # Проверяем, существует ли уже поле
            try:
                result = db.session.execute(text("PRAGMA table_info(vote)"))
                columns = [row[1] for row in result]
                if 'created_at' in columns:
                    print("✅ Поле created_at уже существует")
                else:
                    print("❌ Поле created_at не найдено")
            except Exception as e2:
                print(f"❌ Ошибка при проверке структуры таблицы: {e2}")

if __name__ == '__main__':
    add_created_at_to_vote() 