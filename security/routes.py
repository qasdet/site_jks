from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from . import security
from model.db_models import db, User, LoginAttempt, SecurityLog
from werkzeug.security import generate_password_hash
import re

@security.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Страница смены пароля"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Проверяем текущий пароль
        if not current_user.check_password(current_password):
            flash('Неверный текущий пароль')
            return redirect(url_for('security.change_password'))
        
        # Проверяем совпадение паролей
        if new_password != confirm_password:
            flash('Новые пароли не совпадают')
            return redirect(url_for('security.change_password'))
        
        # Проверяем сложность пароля
        if not current_user.is_password_strong(new_password):
            flash('Пароль должен содержать минимум 8 символов, включая заглавные и строчные буквы, цифры и специальные символы')
            return redirect(url_for('security.change_password'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            
            # Логируем смену пароля
            log_security_event(
                user_id=current_user.id,
                event_type='password_change',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                details='Пароль успешно изменен'
            )
            
            flash('Пароль успешно изменен!')
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash('Ошибка при смене пароля')
            return redirect(url_for('security.change_password'))
    
    return render_template('security/change_password.html')

@security.route('/security-logs')
@login_required
def security_logs():
    """Просмотр логов безопасности пользователя"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = SecurityLog.query.filter_by(user_id=current_user.id)\
        .order_by(SecurityLog.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('security/logs.html', logs=logs)

@security.route('/login-attempts')
@login_required
def login_attempts():
    """Просмотр попыток входа для пользователя"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    attempts = LoginAttempt.query.filter_by(username=current_user.username)\
        .order_by(LoginAttempt.attempted_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('security/login_attempts.html', attempts=attempts)

@security.route('/unlock-account', methods=['POST'])
@login_required
def unlock_account():
    """Разблокировка аккаунта"""
    if current_user.is_locked():
        current_user.unlock_account()
        db.session.commit()
        
        log_security_event(
            user_id=current_user.id,
            event_type='account_unlocked',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details='Аккаунт разблокирован пользователем'
        )
        
        flash('Аккаунт разблокирован!')
    else:
        flash('Аккаунт не заблокирован')
    
    return redirect(url_for('profile'))

@security.route('/admin/security-dashboard')
@login_required
def admin_security_dashboard():
    """Панель администратора безопасности (только для админов)"""
    # Проверяем права администратора (можно добавить поле is_admin в модель User)
    if current_user.username != 'admin':  # Простая проверка
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    # Статистика за последние 24 часа
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    total_attempts = LoginAttempt.query.filter(
        LoginAttempt.attempted_at >= yesterday
    ).count()
    
    failed_attempts = LoginAttempt.query.filter(
        LoginAttempt.attempted_at >= yesterday,
        LoginAttempt.success == False
    ).count()
    
    locked_accounts = User.query.filter(
        User.locked_until > datetime.utcnow()
    ).count()
    
    recent_logs = SecurityLog.query.order_by(
        SecurityLog.created_at.desc()
    ).limit(50).all()
    
    return render_template('security/admin_dashboard.html',
                         total_attempts=total_attempts,
                         failed_attempts=failed_attempts,
                         locked_accounts=locked_accounts,
                         recent_logs=recent_logs)

def log_security_event(user_id, event_type, ip_address, user_agent=None, details=None):
    """Логирование события безопасности"""
    log = SecurityLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    db.session.add(log)
    db.session.commit()

def log_login_attempt(username, ip_address, user_agent=None, success=False):
    """Логирование попытки входа"""
    attempt = LoginAttempt(
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success
    )
    db.session.add(attempt)
    db.session.commit()

def check_ip_rate_limit(ip_address, max_attempts=10, window_minutes=15):
    """Проверка ограничения попыток входа по IP"""
    window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
    
    recent_attempts = LoginAttempt.query.filter(
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.attempted_at >= window_start,
        LoginAttempt.success == False
    ).count()
    
    return recent_attempts < max_attempts 