from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from . import forum
from model.db_models import db, ForumTopic, ForumPost, User, Notification
from datetime import datetime
from utils.content_password import check_content_access, has_content_password, set_content_password, remove_content_password

@forum.route('/')
def index():
    """Список тем форума"""
    page = request.args.get('page', 1, type=int)
    topics = ForumTopic.query.order_by(ForumTopic.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('forum/index.html', topics=topics)

@forum.route('/topic/<int:topic_id>')
def view_topic(topic_id):
    """Просмотр темы и сообщений"""
    topic = db.session.get(ForumTopic, topic_id)
    if topic is None:
        abort(404)
    
    # Проверяем доступ к теме
    if not check_content_access('topic', topic_id):
        return render_template('forum/password_required.html', 
                             topic=topic,
                             content_type='topic',
                             content_id=topic_id)
    
    # Получаем только корневые сообщения (без parent_id) с загрузкой связанных ответов
    root_posts = ForumPost.query.filter_by(topic_id=topic_id, parent_id=None).order_by(ForumPost.created_at.asc()).all()
    return render_template('forum/topic.html', topic=topic, posts=root_posts)

@forum.route('/create', methods=['GET', 'POST'])
@login_required
def create_topic():
    """Создание новой темы"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_url = request.form.get('image_url', '').strip()  # Получаем ссылку на изображение
        
        if not title or not content:
            flash('Заполните все обязательные поля')
            return redirect(url_for('forum.create_topic'))
        
        # Валидация URL изображения (если указан)
        if image_url and not (image_url.startswith('http://') or image_url.startswith('https://')):
            flash('Ссылка на изображение должна начинаться с http:// или https://')
            return redirect(url_for('forum.create_topic'))
        
        topic = ForumTopic(
            title=title, 
            user_id=current_user.id,
            image_url=image_url if image_url else None
        )
        db.session.add(topic)
        db.session.flush()  # Получаем id темы
        post = ForumPost(content=content, user_id=current_user.id, topic_id=topic.id)
        db.session.add(post)
        db.session.commit()
        flash('Тема создана!')
        return redirect(url_for('forum.view_topic', topic_id=topic.id))
    return render_template('forum/create_topic.html')

@forum.route('/topic/<int:topic_id>/reply', methods=['POST'])
@login_required
def reply(topic_id):
    """Добавление сообщения в тему"""
    topic = db.session.get(ForumTopic, topic_id)
    if topic is None:
        abort(404)
    content = request.form.get('content')
    parent_id = request.form.get('parent_id', type=int)
    if not content:
        flash('Сообщение не может быть пустым')
        return redirect(url_for('forum.view_topic', topic_id=topic_id))
    
    # Проверяем, что parent_id существует, если указан
    if parent_id:
        parent_post = db.session.get(ForumPost, parent_id)
        if parent_post is None or parent_post.topic_id != topic_id:
            flash('Ошибка: родительское сообщение не найдено')
            return redirect(url_for('forum.view_topic', topic_id=topic_id))
    
    post = ForumPost(content=content, user_id=current_user.id, topic_id=topic_id, parent_id=parent_id)
    db.session.add(post)
    
    # Создаем уведомления
    if parent_id and parent_post.user_id != current_user.id:
        # Уведомление для автора родительского сообщения
        notification = Notification(
            user_id=parent_post.user_id,
            title=f'Ответ на ваше сообщение в теме "{topic.title}"',
            message=f'{current_user.username} ответил на ваше сообщение',
            type='forum_reply',
            related_id=topic.id,
            post_id=post.id
        )
        db.session.add(notification)
    elif topic.user_id != current_user.id:
        # Уведомление для автора темы (если это не ответ на конкретное сообщение)
        notification = Notification(
            user_id=topic.user_id,
            title=f'Новый ответ в теме "{topic.title}"',
            message=f'{current_user.username} ответил в вашей теме',
            type='forum_reply',
            related_id=topic.id,
            post_id=post.id
        )
        db.session.add(notification)
    
    db.session.commit()
    flash('Сообщение добавлено!')
    return redirect(url_for('forum.view_topic', topic_id=topic_id))

@forum.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = db.session.get(ForumPost, post_id)
    if post is None:
        abort(404)
    if post.user_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Сообщение не может быть пустым')
            return redirect(url_for('forum.edit_post', post_id=post_id))
        post.content = content
        post.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Сообщение обновлено!')
        return redirect(url_for('forum.view_topic', topic_id=post.topic_id))
    return render_template('forum/edit_post.html', post=post)

@forum.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = db.session.get(ForumPost, post_id)
    if post is None:
        abort(404)
    if post.user_id != current_user.id:
        abort(403)
    topic_id = post.topic_id
    db.session.delete(post)
    db.session.commit()
    flash('Сообщение удалено!')
    return redirect(url_for('forum.view_topic', topic_id=topic_id))

@forum.route('/post/<int:post_id>/reply', methods=['GET', 'POST'])
@login_required
def reply_to_post(post_id):
    """Ответ на конкретное сообщение"""
    post = db.session.get(ForumPost, post_id)
    if post is None:
        abort(404)
    
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Сообщение не может быть пустым')
            return redirect(url_for('forum.reply_to_post', post_id=post_id))
        
        reply_post = ForumPost(
            content=content, 
            user_id=current_user.id, 
            topic_id=post.topic_id, 
            parent_id=post.id
        )
        db.session.add(reply_post)
        
        # Создаем уведомление для автора исходного сообщения
        if post.user_id != current_user.id:
            notification = Notification(
                user_id=post.user_id,
                title=f'Ответ на ваше сообщение в теме "{post.topic.title}"',
                message=f'{current_user.username} ответил на ваше сообщение',
                type='forum_reply',
                related_id=post.topic_id,
                post_id=reply_post.id
            )
            db.session.add(notification)
        
        db.session.commit()
        flash('Ответ добавлен!')
        return redirect(url_for('forum.view_topic', topic_id=post.topic_id))
    
    return render_template('forum/reply_to_post.html', post=post)

@forum.route('/notifications')
@login_required
def notifications():
    """Страница уведомлений"""
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('forum/notifications.html', notifications=notifications)

@forum.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Отметить уведомление как прочитанное"""
    notification = db.session.get(Notification, notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@forum.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Отметить все уведомления как прочитанные"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@forum.route('/notifications/count')
@login_required
def notifications_count():
    """Получить количество непрочитанных уведомлений"""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

@forum.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Удалить уведомление"""
    notification = db.session.get(Notification, notification_id)
    if notification and notification.user_id == current_user.id:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@forum.route('/notifications/delete-all', methods=['POST'])
@login_required
def delete_all_notifications():
    """Удалить все уведомления пользователя"""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})

@forum.route('/my-posts')
@login_required
def my_posts():
    """Страница с постами текущего пользователя на форуме"""
    page = request.args.get('page', 1, type=int)
    posts = ForumPost.query.filter_by(user_id=current_user.id).join(
        ForumPost.topic).join(ForumPost.user).order_by(
        ForumPost.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('forum/my_posts.html', posts=posts)

@forum.route('/topic/<int:topic_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_topic(topic_id):
    """Редактирование темы"""
    topic = db.session.get(ForumTopic, topic_id)
    if topic is None:
        abort(404)
    if topic.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        image_url = request.form.get('image_url', '').strip()
        
        if not title:
            flash('Название темы не может быть пустым')
            return redirect(url_for('forum.edit_topic', topic_id=topic_id))
        
        # Валидация URL изображения (если указан)
        if image_url and not (image_url.startswith('http://') or image_url.startswith('https://')):
            flash('Ссылка на изображение должна начинаться с http:// или https://')
            return redirect(url_for('forum.edit_topic', topic_id=topic_id))
        
        topic.title = title
        topic.image_url = image_url if image_url else None
        db.session.commit()
        flash('Тема обновлена!')
        return redirect(url_for('forum.view_topic', topic_id=topic_id))
    
    return render_template('forum/edit_topic.html', topic=topic)

@forum.route('/topic/<int:topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(topic_id):
    """Удаление темы"""
    topic = db.session.get(ForumTopic, topic_id)
    if topic is None:
        abort(404)
    if topic.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Удаляем все сообщения в теме
    ForumPost.query.filter_by(topic_id=topic_id).delete()
    # Удаляем тему
    db.session.delete(topic)
    db.session.commit()
    flash('Тема удалена!')
    return redirect(url_for('forum.index'))

@forum.route('/topic/<int:topic_id>/set-password', methods=['GET', 'POST'])
@login_required
def set_topic_password(topic_id):
    """Установка пароля для темы"""
    topic = db.session.get(ForumTopic, topic_id)
    if topic is None:
        abort(404)
    
    # Проверяем, что пользователь является автором темы
    if topic.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        password = request.form.get('password')
        action = request.form.get('action')
        
        if action == 'set' and password:
            set_content_password('topic', topic_id, password, current_user.id)
            flash('Пароль для темы установлен!')
        elif action == 'remove':
            remove_content_password('topic', topic_id)
            flash('Пароль для темы удален!')
        else:
            flash('Пароль не может быть пустым')
        
        return redirect(url_for('forum.view_topic', topic_id=topic_id))
    
    has_password = has_content_password('topic', topic_id)
    return render_template('forum/set_password.html', 
                         topic=topic, 
                         has_password=has_password)

@forum.route('/topic/<int:topic_id>/check-password', methods=['POST'])
@login_required
def check_topic_password(topic_id):
    """Проверка пароля для доступа к теме"""
    topic = db.session.get(ForumTopic, topic_id)
    if topic is None:
        abort(404)
    
    password = request.form.get('password')
    if not password:
        flash('Введите пароль')
        return redirect(url_for('forum.view_topic', topic_id=topic_id))
    
    if check_content_access('topic', topic_id, password):
        flash('Доступ разрешен!')
        return redirect(url_for('forum.view_topic', topic_id=topic_id))
    else:
        flash('Неверный пароль')
        return redirect(url_for('forum.view_topic', topic_id=topic_id)) 