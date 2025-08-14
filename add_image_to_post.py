import os
from flask import Flask
from model.db_models import db
from sqlalchemy import text

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'app.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Добавляем поле image, если его нет
    with db.engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(post)"))
        columns = [row[1] for row in result]
        if 'image' not in columns:
            conn.execute(text('ALTER TABLE post ADD COLUMN image VARCHAR(255)'))
            print('Поле image успешно добавлено в таблицу post.')
        else:
            print('Поле image уже существует.') 