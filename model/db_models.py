from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Добавлено поле для админов
    
    # Новые поля для безопасности
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    require_password_change = db.Column(db.Boolean, default=False)
    
    # Поля для Telegram двухфакторной аутентификации
    telegram_enabled = db.Column(db.Boolean, default=False)
    telegram_chat_id = db.Column(db.String(50), nullable=True)
    telegram_username = db.Column(db.String(100), nullable=True)
    
    def set_password(self, password):
        """Установка хешированного пароля с проверкой сложности"""
        if not self.is_password_strong(password):
            raise ValueError("Пароль не соответствует требованиям безопасности")
        
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
        self.password_changed_at = datetime.utcnow()
        self.require_password_change = False
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def is_password_strong(self, password):
        """Проверка сложности пароля"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):  # Заглавные буквы
            return False
        if not re.search(r'[a-z]', password):  # Строчные буквы
            return False
        if not re.search(r'\d', password):     # Цифры
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Спецсимволы
            return False
        return True
    
    def is_locked(self):
        """Проверяет, заблокирован ли аккаунт"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """Блокирует аккаунт на указанное время"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Разблокирует аккаунт"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_failed_login(self):
        """Записывает неудачную попытку входа"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    def record_successful_login(self):
        """Записывает успешный вход"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def get_password_age_days(self):
        """Возвращает возраст пароля в днях"""
        return (datetime.utcnow() - self.password_changed_at).days
    
    def enable_telegram_2fa(self, chat_id, username):
        """Включает Telegram двухфакторную аутентификацию"""
        self.telegram_enabled = True
        self.telegram_chat_id = chat_id
        self.telegram_username = username
    
    def disable_telegram_2fa(self):
        """Отключает Telegram двухфакторную аутентификацию"""
        self.telegram_enabled = False
        self.telegram_chat_id = None
        self.telegram_username = None
    
    def __repr__(self):
        return f'<User {self.username}>'

class LoginAttempt(db.Model):
    """Модель для отслеживания попыток входа"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # Поддержка IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    success = db.Column(db.Boolean, default=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LoginAttempt {self.username}:{self.success}>'

class SecurityLog(db.Model):
    """Модель для логирования событий безопасности"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # login, logout, password_change, etc.
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    user = db.relationship('User', backref=db.backref('security_logs', lazy=True))
    
    def __repr__(self):
        return f'<SecurityLog {self.event_type}:{self.user_id}>'

class TelegramVerification(db.Model):
    """Модель для хранения кодов подтверждения Telegram"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)  # 6-значный код
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    # Связи
    user = db.relationship('User', backref=db.backref('telegram_verifications', lazy=True))
    
    def is_expired(self):
        """Проверяет, истек ли срок действия кода"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Проверяет, действителен ли код"""
        return not self.used and not self.is_expired()
    
    def __repr__(self):
        return f'<TelegramVerification {self.user_id}:{self.code}>'

class Post(db.Model):
    """Модель поста/записи"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(255), nullable=True)  # Имя файла изображения (опционально)
    is_published = db.Column(db.Boolean, default=True)  # Статус публикации поста
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Property(db.Model):
    """Модель собственности/квартиры"""
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)  # Номер квартиры
    area = db.Column(db.Float, nullable=False)  # Площадь в кв.м
    street = db.Column(db.String(200), nullable=False)  # Название улицы
    house_number = db.Column(db.String(20), nullable=False)  # Номер дома
    entrance = db.Column(db.String(10), nullable=True)  # Подъезд
    floor = db.Column(db.Integer, nullable=True)  # Этаж
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    owner = db.relationship('User', backref=db.backref('properties', lazy=True))
    votes = db.relationship('Vote', backref='property', lazy=True)
    
    def get_full_address(self):
        """Возвращает полный адрес собственности"""
        address_parts = [f"ул. {self.street}", f"д. {self.house_number}"]
        if self.entrance:
            address_parts.append(f"подъезд {self.entrance}")
        if self.floor:
            address_parts.append(f"этаж {self.floor}")
        address_parts.append(f"кв. {self.number}")
        return ", ".join(address_parts)
    
    def __repr__(self):
        return f'<Property {self.get_full_address()}>'

class Voting(db.Model):
    """Модель голосования"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    question = db.Column(db.String(500), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    creator = db.relationship('User', backref=db.backref('created_votings', lazy=True))
    options = db.relationship('VotingOption', back_populates='voting', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='voting', lazy=True, cascade='all, delete-orphan')
    
    def is_open(self):
        """Проверяет, открыто ли голосование"""
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date and self.is_active
    
    def get_results(self):
        """Получает результаты голосования"""
        results = {}
        total_votes = 0
        
        for option in self.options:
            vote_count = Vote.query.filter_by(voting_id=self.id, option_id=option.id).count()
            results[option.id] = {
                'text': option.text,
                'votes': vote_count,
                'percentage': 0
            }
            total_votes += vote_count
        
        # Вычисляем проценты
        if total_votes > 0:
            for option_id in results:
                results[option_id]['percentage'] = round(
                    (results[option_id]['votes'] / total_votes) * 100, 1
                )
        
        return results, total_votes
    
    def __repr__(self):
        return f'<Voting {self.title}>'

class VotingOption(db.Model):
    """Модель варианта ответа для голосования"""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    voting_id = db.Column(db.Integer, db.ForeignKey('voting.id', ondelete='CASCADE'), nullable=False)
    
    # Связи
    voting = db.relationship('Voting', back_populates='options')
    votes = db.relationship('Vote', back_populates='option', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<VotingOption {self.text}>'

class Vote(db.Model):
    """Модель голоса"""
    id = db.Column(db.Integer, primary_key=True)
    voting_id = db.Column(db.Integer, db.ForeignKey('voting.id', ondelete='CASCADE'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id', ondelete='CASCADE'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('voting_option.id', ondelete='CASCADE'), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Добавляем для совместимости
    
    # Связь с вариантом ответа
    option = db.relationship('VotingOption', back_populates='votes')
    
    def __repr__(self):
        return f'<Vote {self.voting_id}:{self.property_id}:{self.option_id}>'

class ForumTopic(db.Model):
    """Тема форума"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)  # Ссылка на изображение
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Связи
    user = db.relationship('User', backref=db.backref('forum_topics', lazy=True))
    posts = db.relationship('ForumPost', backref='topic', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ForumTopic {self.title}>'

class ForumPost(db.Model):
    """Сообщение в теме форума"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topic.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=True)
    
    # Связи
    user = db.relationship('User', backref=db.backref('forum_posts', lazy=True))
    replies = db.relationship('ForumPost', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
    def get_replies_tree(self):
        """Получает дерево ответов для этого сообщения"""
        def build_tree(post):
            tree = {
                'post': post,
                'replies': []
            }
            for reply in post.replies:
                tree['replies'].append(build_tree(reply))
            return tree
        return build_tree(self)
    
    def get_all_replies_count(self):
        """Получает общее количество ответов (включая вложенные)"""
        count = len(self.replies)
        for reply in self.replies:
            count += reply.get_all_replies_count()
        return count
    
    def __repr__(self):
        return f'<ForumPost {self.id}>'

class Notification(db.Model):
    """Уведомления для пользователей"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'forum_reply', 'voting_created', etc.
    related_id = db.Column(db.Integer, nullable=True)  # ID связанного объекта (темы, голосования)
    post_id = db.Column(db.Integer, nullable=True)  # ID конкретного сообщения для форума
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

class ContentPassword(db.Model):
    """Модель для хранения паролей доступа к контенту"""
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False)  # 'voting', 'post', 'topic'
    content_id = db.Column(db.Integer, nullable=False)  # ID голосования, поста или темы
    password_hash = db.Column(db.String(128), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связи
    creator = db.relationship('User', backref=db.backref('content_passwords', lazy=True))
    
    def set_password(self, password):
        """Установка хешированного пароля"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:600000')
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<ContentPassword {self.content_type}:{self.content_id}>'

class ContentAccess(db.Model):
    """Модель для отслеживания доступа пользователей к защищенному контенту"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'voting', 'post', 'topic'
    content_id = db.Column(db.Integer, nullable=False)  # ID голосования, поста или темы
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    user = db.relationship('User', backref=db.backref('content_accesses', lazy=True))
    
    def __repr__(self):
        return f'<ContentAccess {self.user_id}:{self.content_type}:{self.content_id}>'


