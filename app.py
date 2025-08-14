# Импорт стандартного модуля os для работы с операционной системой (не используется явно в этом файле, но может быть нужен для расширения)
import os
# Импорт основных компонентов Flask: Flask — основной класс приложения, render_template — функция для рендеринга HTML-шаблонов
from flask import Flask, render_template
# Импорт расширения Flask-Login для управления сессиями пользователей:
# LoginManager — менеджер входа, login_required — декоратор для ограничения доступа, current_user — текущий пользователь
from flask_login import LoginManager, login_required, current_user
# Импорт класса datetime для работы с датой и временем
from datetime import datetime
# Импорт конфигурационного объекта config из локального модуля config
from config import config
# Импорт базы данных и модели пользователя из модуля model.db_models
from model.db_models import db, User
# Импорт blueprint-ов (модулей) приложения
from auth import auth
from blog import blog
from voting import voting
from forum import forum
from security import security
from telegram_bot import telegram_bot
from admin import admin_bp



def create_app(config_name='default'):
    """
    Фабрика приложений Flask.
    Создаёт и настраивает экземпляр приложения Flask с нужной конфигурацией, расширениями и blueprint-ами.
    :param config_name: имя конфигурации (по умолчанию 'default')
    :return: настроенный экземпляр Flask
    """
    app = Flask(__name__)
    
    # Загрузка конфигурации приложения из объекта config
    app.config.from_object(config[config_name])
    
    # Инициализация расширения SQLAlchemy для работы с базой данных
    db.init_app(app)
    
    # Настройка менеджера входа Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # type: ignore — игнорируем предупреждение типов
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    @login_manager.user_loader
    def load_user(user_id):
        """
        Функция загрузки пользователя по ID для Flask-Login.
        :param user_id: идентификатор пользователя
        :return: объект пользователя или None
        """
        return db.session.get(User, int(user_id))
    
    # Регистрация blueprint-ов (модулей) приложения с указанием префиксов URL
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(blog, url_prefix='/blog')
    app.register_blueprint(voting, url_prefix='/voting')
    app.register_blueprint(forum, url_prefix='/forum')
    app.register_blueprint(security, url_prefix='/security')
    app.register_blueprint(telegram_bot, url_prefix='/telegram')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    
    # Создание всех таблиц базы данных, если они ещё не созданы
    with app.app_context():
        db.create_all()
    
    # Добавление переменной datetime в контекст всех шаблонов Jinja2
    @app.context_processor
    def inject_datetime():
        """
        Добавляет объект datetime в контекст шаблонов для использования в HTML.
        :return: словарь с datetime
        """
        return dict(datetime=datetime)
    
    # Главная страница сайта
    @app.route('/')
    def index():
        """
        Обработчик главной страницы. Передаёт текущую дату и время в шаблон index.html.
        """
        return render_template('index.html', now=datetime.now())
    
    # Страница профиля пользователя (требует входа в систему)
    @app.route('/profile')
    @login_required
    def profile():
        """
        Обработчик страницы профиля пользователя. Показывает статистику пользователя и последние попытки входа.
        """
        # Подсчитываем статистику пользователя по связанным объектам
        user_stats = {
            'posts_count': len(current_user.posts),  # Количество блог-постов
            'forum_posts_count': len(current_user.forum_posts),  # Количество сообщений на форуме
            'votings_count': len(current_user.created_votings),  # Количество созданных голосований
            'properties_count': len(current_user.properties)  # Количество свойств пользователя
        }
        
        # Импорт модели LoginAttempt для получения попыток входа
        from model.db_models import LoginAttempt
        # Получаем последние 5 попыток входа пользователя
        recent_login_attempts = LoginAttempt.query.filter_by(username=current_user.username)\
            .order_by(LoginAttempt.attempted_at.desc())\
            .limit(5).all()
        
        # Подсчитываем общее количество попыток входа, успешных и неуспешных
        total_attempts = LoginAttempt.query.filter_by(username=current_user.username).count()
        successful_attempts = LoginAttempt.query.filter_by(username=current_user.username, success=True).count()
        failed_attempts = total_attempts - successful_attempts
        
        login_stats = {
            'total_attempts': total_attempts,  # Всего попыток
            'successful_attempts': successful_attempts,  # Успешных попыток
            'failed_attempts': failed_attempts,  # Неуспешных попыток
            'recent_attempts': recent_login_attempts  # Список последних попыток
        }
        
        return render_template('profile.html', user_stats=user_stats, login_stats=login_stats)
    
    # Тестовая страница для проверки уведомлений
    @app.route('/test-notifications')
    @login_required
    def test_notifications():
        """
        Тестовая страница для диагностики проблем с уведомлениями.
        """
        return render_template('test_notifications.html')
    
    return app

# Создание экземпляра приложения Flask с использованием фабрики
app = create_app()

if __name__ == '__main__':
    # Запуск приложения в режиме отладки
    app.run(debug=True)