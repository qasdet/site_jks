# Импорт функции render_template для рендеринга HTML-шаблонов,
# redirect и url_for для перенаправления и построения URL,
# flash для отображения сообщений пользователю,
# request для доступа к данным запроса,
# abort для генерации ошибок HTTP (например, 404, 403)
from flask import render_template, redirect, url_for, flash, request, abort
# Импорт декоратора login_required для ограничения доступа,
# current_user — объект текущего пользователя
from flask_login import login_required, current_user
# Импорт blueprint-а blog из текущего пакета
from . import blog
# Импорт базы данных, модели поста и пользователя
from model.db_models import db, Post, User
# Импорт класса datetime для работы с датой и временем
from datetime import datetime
# Импорт функций для работы с паролями к контенту (постам)
from utils.content_password import check_content_access, has_content_password, set_content_password, remove_content_password, get_blurred_content
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blog.route('/')
def index():
    """
    Главная страница блога — список всех опубликованных постов с пагинацией.
    """
    page = request.args.get('page', 1, type=int)
    posts_pagination = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=5, error_out=False)
    
    # Обрабатываем посты для отображения замыленного контента
    posts = []
    for post in posts_pagination.items:
        post_data = {
            'id': post.id,
            'title': post.title,
            'content': get_blurred_content('post', post.id, post.content),
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'user': post.user,
            'user_id': post.user_id,
            'has_password': has_content_password('post', post.id),
            'has_access': check_content_access('post', post.id)
        }
        posts.append(post_data)
    
    return render_template('blog/index.html', posts=posts, pagination=posts_pagination)

@blog.route('/post/<int:post_id>')
def post(post_id):
    """
    Просмотр отдельного поста. Если пост защищён паролем — показывает замыленный контент.
    """
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    
    # Проверяем, что пост опубликован (кроме автора и админов)
    if not post.is_published and (not current_user.is_authenticated or 
                                 (post.user_id != current_user.id and not getattr(current_user, 'is_admin', False))):
        abort(404)
    
    # Получаем замыленный контент, если пост защищен паролем
    blurred_content = get_blurred_content('post', post_id, post.content)
    has_password = has_content_password('post', post_id)
    has_access = check_content_access('post', post_id)
    
    return render_template('blog/post.html', 
                         post=post, 
                         content=blurred_content,
                         has_password=has_password,
                         has_access=has_access)

@blog.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """
    Создание нового поста. Доступно только авторизованным пользователям.
    """
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_file = request.files.get('image')
        image_filename = None
        
        if image_file and image_file.filename and allowed_file(image_file.filename):
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            filename = secure_filename(image_file.filename)
            # Уникальное имя файла
            import uuid
            ext = filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join(UPLOAD_FOLDER, unique_name)
            image_file.save(image_path)
            image_filename = unique_name
        
        if not title or not content:
            flash('Заголовок и содержание не могут быть пустыми')
            return redirect(url_for('blog.create'))
        
        post = Post(title=title, content=content, user_id=current_user.id, image=image_filename)
        db.session.add(post)
        db.session.commit()
        
        flash('Пост успешно создан!')
        return redirect(url_for('blog.post', post_id=post.id))
    
    return render_template('blog/create.html')

@blog.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    """
    Редактирование поста. Доступно только автору поста.
    """
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    
    # Проверяем, что текущий пользователь — автор поста
    if post.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_file = request.files.get('image')
        
        if not title or not content:
            flash('Заголовок и содержание не могут быть пустыми')
            return redirect(url_for('blog.edit', post_id=post.id))
        
        # Если загружено новое изображение — сохраняем и обновляем поле
        if image_file and image_file.filename and allowed_file(image_file.filename):
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            filename = secure_filename(image_file.filename)
            import uuid
            ext = filename.rsplit('.', 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join(UPLOAD_FOLDER, unique_name)
            image_file.save(image_path)
            post.image = unique_name
        # Если не загружено — оставляем старое изображение
        post.title = title
        post.content = content
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Пост успешно обновлён!')
        return redirect(url_for('blog.post', post_id=post.id))
    
    return render_template('blog/edit.html', post=post)

@blog.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete(post_id):
    """
    Удаление поста. Доступно только автору поста.
    """
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    
    # Проверяем, что текущий пользователь — автор поста
    if post.user_id != current_user.id:
        abort(403)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Пост успешно удалён!')
    return redirect(url_for('blog.index'))

@blog.route('/my-posts')
@login_required
def my_posts():
    """
    Страница с постами текущего пользователя (личный блог).
    """
    page = request.args.get('page', 1, type=int)
    posts_pagination = Post.query.filter_by(user_id=current_user.id).order_by(
        Post.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    # Обрабатываем посты для отображения замыленного контента
    posts = []
    for post in posts_pagination.items:
        post_data = {
            'id': post.id,
            'title': post.title,
            'content': get_blurred_content('post', post.id, post.content),
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'user': post.user,
            'user_id': post.user_id,
            'has_password': has_content_password('post', post.id),
            'has_access': check_content_access('post', post.id)
        }
        posts.append(post_data)
    
    return render_template('blog/my_posts.html', posts=posts, pagination=posts_pagination)

@blog.route('/user/<int:user_id>')
def user_posts(user_id):
    """
    Посты конкретного пользователя (чужой блог).
    """
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    
    # Показываем только опубликованные посты (кроме случаев, когда пользователь смотрит свои посты или является админом)
    query = Post.query.filter_by(user_id=user_id)
    if not current_user.is_authenticated or (current_user.id != user_id and not getattr(current_user, 'is_admin', False)):
        query = query.filter_by(is_published=True)
    
    posts_pagination = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    # Обрабатываем посты для отображения замыленного контента
    posts = []
    for post in posts_pagination.items:
        post_data = {
            'id': post.id,
            'title': post.title,
            'content': get_blurred_content('post', post.id, post.content),
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'user': post.user,
            'user_id': post.user_id,
            'has_password': has_content_password('post', post.id),
            'has_access': check_content_access('post', post.id)
        }
        posts.append(post_data)
    
    return render_template('blog/user_posts.html', posts=posts, pagination=posts_pagination, user=user)

@blog.route('/post/<int:post_id>/set-password', methods=['GET', 'POST'])
@login_required
def set_post_password(post_id):
    """
    Установка или удаление пароля для поста. Доступно только автору поста.
    """
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    
    # Проверяем, что текущий пользователь — автор поста
    if post.user_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        password = request.form.get('password')
        action = request.form.get('action')
        
        if action == 'set' and password:
            set_content_password('post', post_id, password, current_user.id)
            flash('Пароль для поста установлен!')
        elif action == 'remove':
            remove_content_password('post', post_id)
            flash('Пароль для поста удалён!')
        else:
            flash('Пароль не может быть пустым')
        
        return redirect(url_for('blog.post', post_id=post_id))
    
    has_password = has_content_password('post', post_id)
    return render_template('blog/set_password.html', 
                         post=post, 
                         has_password=has_password)

@blog.route('/post/<int:post_id>/check-password', methods=['POST'])
def check_post_password(post_id):
    """
    Проверка пароля для доступа к посту.
    """
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    
    password = request.form.get('password')
    if not password:
        flash('Введите пароль')
        return redirect(url_for('blog.post', post_id=post_id))
    
    if check_content_access('post', post_id, password):
        flash('Доступ разрешён!')
        return redirect(url_for('blog.post', post_id=post_id))
    else:
        flash('Неверный пароль')
        return redirect(url_for('blog.post', post_id=post_id)) 