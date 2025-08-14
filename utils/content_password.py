"""
Утилиты для работы с паролями контента
"""

from flask import session
from flask_login import current_user
from model.db_models import db, ContentPassword, ContentAccess
from datetime import datetime, timedelta
import re

def set_content_password(content_type, content_id, password, user_id):
    """
    Устанавливает пароль для контента
    
    Args:
        content_type (str): Тип контента ('voting', 'post', 'topic')
        content_id (int): ID контента
        password (str): Пароль
        user_id (int): ID пользователя, устанавливающего пароль
    """
    # Удаляем существующий пароль, если есть
    existing_password = ContentPassword.query.filter_by(
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if existing_password:
        db.session.delete(existing_password)
    
    # Создаем новый пароль
    content_password = ContentPassword(
        content_type=content_type,
        content_id=content_id,
        created_by=user_id
    )
    content_password.set_password(password)
    
    db.session.add(content_password)
    db.session.commit()

def remove_content_password(content_type, content_id):
    """
    Удаляет пароль для контента
    
    Args:
        content_type (str): Тип контента ('voting', 'post', 'topic')
        content_id (int): ID контента
    """
    content_password = ContentPassword.query.filter_by(
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if content_password:
        db.session.delete(content_password)
        db.session.commit()

def check_content_access(content_type, content_id, password=None):
    """
    Проверяет доступ к контенту
    
    Args:
        content_type (str): Тип контента ('voting', 'post', 'topic')
        content_id (int): ID контента
        password (str): Пароль для проверки (если None, проверяется сессия)
    
    Returns:
        bool: True если доступ разрешен, False если нет
    """
    if not current_user.is_authenticated:
        return False
    
    # Проверяем, есть ли пароль для этого контента
    content_password = ContentPassword.query.filter_by(
        content_type=content_type,
        content_id=content_id,
        is_active=True
    ).first()
    
    if not content_password:
        return True  # Пароль не установлен, доступ свободный
    
    # Проверяем, является ли пользователь создателем пароля
    if content_password.created_by == current_user.id:
        return True
    
    # Проверяем, есть ли уже доступ в сессии
    session_key = f"content_access_{content_type}_{content_id}"
    if session.get(session_key):
        return True
    
    # Проверяем, есть ли запись о доступе в базе данных
    access_record = ContentAccess.query.filter_by(
        user_id=current_user.id,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if access_record:
        # Проверяем, не истек ли доступ (24 часа)
        if access_record.accessed_at > datetime.utcnow() - timedelta(hours=24):
            return True
    
    # Если передан пароль, проверяем его
    if password and content_password.check_password(password):
        # Сохраняем доступ в сессии
        session[session_key] = True
        
        # Сохраняем или обновляем запись о доступе
        if access_record:
            access_record.accessed_at = datetime.utcnow()
        else:
            access_record = ContentAccess(
                user_id=current_user.id,
                content_type=content_type,
                content_id=content_id
            )
            db.session.add(access_record)
        
        db.session.commit()
        return True
    
    return False

def has_content_password(content_type, content_id):
    """
    Проверяет, установлен ли пароль для контента
    
    Args:
        content_type (str): Тип контента ('voting', 'post', 'topic')
        content_id (int): ID контента
    
    Returns:
        bool: True если пароль установлен, False если нет
    """
    return ContentPassword.query.filter_by(
        content_type=content_type,
        content_id=content_id,
        is_active=True
    ).first() is not None

def blur_text(text, blur_ratio=0.7):
    """
    Замыливает текст, заменяя часть символов на символы замыливания
    
    Args:
        text (str): Исходный текст
        blur_ratio (float): Коэффициент замыливания (0.0 - 1.0)
    
    Returns:
        str: Замыленный текст
    """
    if not text:
        return text
    
    # Символы для замыливания
    blur_chars = ['█', '▓', '▒', '░', '▄', '▌', '▐', '▀']
    
    # Разбиваем текст на слова
    words = text.split()
    blurred_words = []
    
    for word in words:
        if len(word) <= 2:
            # Короткие слова оставляем как есть
            blurred_words.append(word)
        else:
            # Для длинных слов заменяем часть символов
            word_chars = list(word)
            num_to_blur = max(1, int(len(word_chars) * blur_ratio))
            
            # Выбираем случайные позиции для замыливания
            import random
            positions = random.sample(range(len(word_chars)), min(num_to_blur, len(word_chars)))
            
            for pos in positions:
                word_chars[pos] = random.choice(blur_chars)
            
            blurred_words.append(''.join(word_chars))
    
    return ' '.join(blurred_words)

def get_blurred_content(content_type, content_id, original_content):
    """
    Возвращает замыленный контент, если пост защищен паролем и у пользователя нет доступа
    
    Args:
        content_type (str): Тип контента ('voting', 'post', 'topic')
        content_id (int): ID контента
        original_content (str): Исходный контент
    
    Returns:
        str: Замыленный контент или исходный контент
    """
    # Проверяем, есть ли пароль для этого контента
    if not has_content_password(content_type, content_id):
        return original_content
    
    # Проверяем доступ
    if check_content_access(content_type, content_id):
        return original_content
    
    # Если нет доступа, возвращаем замыленный контент
    return blur_text(original_content, blur_ratio=0.6)

def get_content_password_info(content_type, content_id):
    """
    Получает информацию о пароле контента
    
    Args:
        content_type (str): Тип контента ('voting', 'post', 'topic')
        content_id (int): ID контента
    
    Returns:
        ContentPassword: Объект пароля или None
    """
    return ContentPassword.query.filter_by(
        content_type=content_type,
        content_id=content_id,
        is_active=True
    ).first() 