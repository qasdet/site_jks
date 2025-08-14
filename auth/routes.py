# Импорт функции render_template для рендеринга HTML-шаблонов,
# redirect и url_for для перенаправления и построения URL,
# flash для отображения сообщений пользователю,
# request для доступа к данным запроса,
# session для работы с сессиями пользователя
from flask import render_template, redirect, url_for, flash, request, session
# Импорт функций и объектов для управления сессией пользователя:
# login_user — вход пользователя, logout_user — выход,
# login_required — декоратор для ограничения доступа,
# current_user — объект текущего пользователя
from flask_login import login_user, logout_user, login_required, current_user
# Импорт функции urlparse для разбора URL (используется для проверки next_page)
from urllib.parse import urlparse
# Импорт blueprint-а auth из текущего пакета
from . import auth
# Импорт моделей пользователя, базы данных, попыток входа и логов безопасности
from model.db_models import User, db, LoginAttempt, SecurityLog
# Импорт класса datetime для работы с датой и временем, timedelta — для вычисления интервалов времени
from datetime import datetime, timedelta
# Импорт функций для логирования событий безопасности и проверки лимитов по IP
from security.routes import log_login_attempt, log_security_event, check_ip_rate_limit
# Импорт функции для отправки кода подтверждения через Telegram
from telegram_bot.routes import send_login_verification
# Импорт модуля регулярных выражений для проверки сложности пароля
import re

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Страница входа с защитой от взлома и поддержкой Telegram 2FA.
    Обрабатывает GET и POST запросы, проверяет лимиты по IP, блокировку аккаунта,
    валидность пароля, а также реализует двухфакторную аутентификацию через Telegram.
    """
    if current_user.is_authenticated:
        # Если пользователь уже вошёл, перенаправляем на главную
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        # Проверяем ограничение по количеству неудачных попыток входа с одного IP
        if not check_ip_rate_limit(ip_address):
            flash('Слишком много неудачных попыток входа с вашего IP. Попробуйте позже.')
            log_login_attempt(username, ip_address, user_agent, success=False)
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        # Проверяем, заблокирован ли аккаунт пользователя
        if user and user.is_locked():
            remaining_time = user.locked_until - datetime.utcnow()
            minutes = int(remaining_time.total_seconds() / 60)
            flash(f'Аккаунт заблокирован. Попробуйте через {minutes} минут.')
            log_login_attempt(username, ip_address, user_agent, success=False)
            return redirect(url_for('auth.login'))
        
        if user is None or not user.check_password(password):
            # Неудачная попытка входа: увеличиваем счётчик, логируем событие
            if user:
                user.record_failed_login()
                db.session.commit()
            
            log_login_attempt(username, ip_address, user_agent, success=False)
            flash('Неверное имя пользователя или пароль')
            return redirect(url_for('auth.login'))
        
        # Проверяем, включена ли двухфакторная аутентификация через Telegram
        if user.telegram_enabled:
            # Отправляем код подтверждения в Telegram
            verification_id = send_login_verification(user, ip_address)
            if verification_id:
                # Сохраняем ID верификации и пользователя в сессии
                session['pending_verification_id'] = verification_id
                session['pending_user_id'] = user.id
                
                flash('Код подтверждения отправлен в Telegram. Проверьте сообщения.')
                return redirect(url_for('telegram_bot.verify_login'))
            else:
                flash('Ошибка отправки кода подтверждения. Попробуйте позже.')
                return redirect(url_for('auth.login'))
        
        # Успешный вход без 2FA: сбрасываем счётчик неудачных попыток, логируем событие
        user.record_successful_login()
        db.session.commit()
        
        login_user(user)
        
        # Логируем успешный вход
        log_login_attempt(username, ip_address, user_agent, success=True)
        log_security_event(
            user_id=user.id,
            event_type='login',
            ip_address=ip_address,
            user_agent=user_agent,
            details='Успешный вход в систему'
        )
        
        # Проверяем, требуется ли смена пароля
        if user.require_password_change:
            flash('Требуется смена пароля')
            return redirect(url_for('security.change_password'))
        
        # Проверяем возраст пароля (рекомендуется менять каждые 90 дней)
        if user.get_password_age_days() > 90:
            flash('Рекомендуется сменить пароль. Ваш пароль не менялся более 90 дней.')
        
        # Получаем next_page из параметров запроса, если есть
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    
    # GET-запрос: отображаем форму входа
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Страница регистрации с проверкой сложности пароля и уникальности пользователя.
    Обрабатывает GET и POST запросы, проверяет совпадение паролей, сложность,
    уникальность имени и email, а также логирует событие регистрации.
    """
    if current_user.is_authenticated:
        # Если пользователь уже вошёл, перенаправляем на главную
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Проверяем совпадение паролей
        if password != confirm_password:
            flash('Пароли не совпадают')
            return redirect(url_for('auth.register'))
        
        # Проверяем сложность пароля: длина, наличие заглавных, строчных, цифр и спецсимволов
        if len(password) < 8:
            flash('Пароль должен содержать минимум 8 символов')
            return redirect(url_for('auth.register'))
        
        if not re.search(r'[A-Z]', password):
            flash('Пароль должен содержать хотя бы одну заглавную букву')
            return redirect(url_for('auth.register'))
        
        if not re.search(r'[a-z]', password):
            flash('Пароль должен содержать хотя бы одну строчную букву')
            return redirect(url_for('auth.register'))
        
        if not re.search(r'\d', password):
            flash('Пароль должен содержать хотя бы одну цифру')
            return redirect(url_for('auth.register'))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash('Пароль должен содержать хотя бы один специальный символ')
            return redirect(url_for('auth.register'))
        
        # Проверяем уникальность имени пользователя
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('auth.register'))
        
        # Проверяем уникальность email
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует')
            return redirect(url_for('auth.register'))
        
        try:
            # Создаём нового пользователя и сохраняем в базе
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Логируем событие регистрации
            log_security_event(
                user_id=user.id,
                event_type='registration',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                details='Новый пользователь зарегистрирован'
            )
            
            flash('Регистрация успешна! Теперь вы можете войти.')
            return redirect(url_for('auth.login'))
            
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('auth.register'))
        except Exception as e:
            flash('Ошибка при регистрации')
            return redirect(url_for('auth.register'))
    
    # GET-запрос: отображаем форму регистрации
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    """
    Выход из системы с логированием события безопасности.
    Завершает сессию пользователя, логирует событие и перенаправляет на главную страницу.
    """
    user_id = current_user.id
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    
    logout_user()
    
    # Логируем выход пользователя
    log_security_event(
        user_id=user_id,
        event_type='logout',
        ip_address=ip_address,
        user_agent=user_agent,
        details='Выход из системы'
    )
    
    return redirect(url_for('index'))
