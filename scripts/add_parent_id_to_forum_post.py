import sqlite3
import os

# Путь к базе данных (скорее всего instance/app.db)
db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'app.db')

def add_parent_id_column():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Проверяем, есть ли уже столбец parent_id
    cursor.execute("PRAGMA table_info(forum_post);")
    columns = [row[1] for row in cursor.fetchall()]
    if 'parent_id' in columns:
        print('Столбец parent_id уже существует.')
        conn.close()
        return
    # Добавляем столбец
    cursor.execute("ALTER TABLE forum_post ADD COLUMN parent_id INTEGER REFERENCES forum_post(id);")
    conn.commit()
    print('Столбец parent_id успешно добавлен!')
    conn.close()

if __name__ == '__main__':
    add_parent_id_column() 