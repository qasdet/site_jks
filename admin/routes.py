from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import admin_bp
from model.db_models import User, Post, ForumTopic, ForumPost, Voting, VotingOption, Vote, Property, db
from sqlalchemy import or_, and_, desc, asc
from datetime import datetime, timedelta
from sqlalchemy.orm import aliased

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('Доступ разрешён только администраторам.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Статистика
    user_count = User.query.count()
    post_count = Post.query.count()
    topic_count = ForumTopic.query.count()
    forum_post_count = ForumPost.query.count()
    voting_count = Voting.query.filter(Voting.is_active.is_(True)).count()
    vote_count = Vote.query.count()

    
    # Последние действия
    recent_users = User.query.order_by(desc(User.created_at)).limit(5).all()
    recent_posts = Post.query.order_by(desc(Post.created_at)).limit(5).all()
    recent_topics = ForumTopic.query.order_by(desc(ForumTopic.created_at)).limit(5).all()
    recent_votings = Voting.query.order_by(desc(Voting.created_at)).limit(5).all()

    
    # Статистика по дням
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_posts_week = Post.query.filter(Post.created_at >= week_ago).count()
    new_topics_week = ForumTopic.query.filter(ForumTopic.created_at >= week_ago).count()

    
    return render_template('admin/dashboard.html', 
                         user_count=user_count, 
                         post_count=post_count, 
                         topic_count=topic_count,
                         forum_post_count=forum_post_count,
                         voting_count=voting_count,
                         vote_count=vote_count,
                         recent_users=recent_users,
                         recent_posts=recent_posts,
                         recent_topics=recent_topics,
                         recent_votings=recent_votings,
                         new_users_week=new_users_week,
                         new_posts_week=new_posts_week,
                         new_topics_week=new_topics_week)

# ===== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ =====
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Фильтры
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    admin_filter = request.args.get('admin', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    query = User.query
    
    # Поиск
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    # Фильтр по статусу
    if status == 'active':
        query = query.filter(User.is_active.is_(True))
    elif status == 'inactive':
        query = query.filter(User.is_active.is_(False))
    
    # Фильтр по админам
    if admin_filter == 'admin':
        query = query.filter(User.is_admin.is_(True))
    elif admin_filter == 'user':
        query = query.filter(User.is_admin.is_(False))
    
    # Сортировка
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(User, sort_by)))
    else:
        query = query.order_by(asc(getattr(User, sort_by)))
    
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=users, 
                         search=search, status=status, admin_filter=admin_filter,
                         sort_by=sort_by, sort_order=sort_order)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Статус пользователя {user.username} изменен', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Права администратора для {user.username} изменены', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/mass-action', methods=['POST'])
@login_required
@admin_required
def users_mass_action():
    action = request.form.get('action')
    user_ids = request.form.getlist('user_ids')
    
    if not user_ids:
        flash('Не выбрано ни одного пользователя', 'warning')
        return redirect(url_for('admin.users'))
    
    users = User.query.filter(User.id.in_(user_ids)).all()
    
    if action == 'activate':
        for user in users:
            user.is_active = True
        flash(f'Активировано {len(users)} пользователей', 'success')
    elif action == 'deactivate':
        for user in users:
            user.is_active = False
        flash(f'Деактивировано {len(users)} пользователей', 'success')
    elif action == 'delete':
        for user in users:
            db.session.delete(user)
        flash(f'Удалено {len(users)} пользователей', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.users'))

# ===== УПРАВЛЕНИЕ ПОСТАМИ =====
@admin_bp.route('/posts')
@login_required
@admin_required
def posts():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Фильтры
    search = request.args.get('search', '')
    author = request.args.get('author', '')
    status = request.args.get('status', '')  # Фильтр по статусу публикации
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    query = Post.query.join(User)
    
    # Поиск
    if search:
        query = query.filter(
            or_(
                Post.title.ilike(f'%{search}%'),
                Post.content.ilike(f'%{search}%')
            )
        )
    
    # Фильтр по автору
    if author:
        query = query.filter(User.username.ilike(f'%{author}%'))
    
    # Фильтр по статусу публикации
    if status == 'published':
        query = query.filter(Post.is_published.is_(True))
    elif status == 'unpublished':
        query = query.filter(Post.is_published.is_(False))
    
    # Сортировка
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(Post, sort_by)))
    else:
        query = query.order_by(asc(getattr(Post, sort_by)))
    
    posts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/posts.html', posts=posts, 
                         search=search, author=author, status=status,
                         sort_by=sort_by, sort_order=sort_order)

@admin_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    title = post.title
    db.session.delete(post)
    db.session.commit()
    flash(f'Пост "{title}" удален', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/<int:post_id>/toggle-publication', methods=['POST'])
@login_required
@admin_required
def toggle_post_publication(post_id):
    """Переключение статуса публикации поста"""
    post = Post.query.get_or_404(post_id)
    post.is_published = not post.is_published
    db.session.commit()
    
    status = "опубликован" if post.is_published else "снят с публикации"
    flash(f'Пост "{post.title}" {status}', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/<int:post_id>/publish', methods=['POST'])
@login_required
@admin_required
def publish_post(post_id):
    """Публикация поста"""
    post = Post.query.get_or_404(post_id)
    post.is_published = True
    db.session.commit()
    flash(f'Пост "{post.title}" опубликован', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/<int:post_id>/unpublish', methods=['POST'])
@login_required
@admin_required
def unpublish_post(post_id):
    """Снятие поста с публикации"""
    post = Post.query.get_or_404(post_id)
    post.is_published = False
    db.session.commit()
    flash(f'Пост "{post.title}" снят с публикации', 'success')
    return redirect(url_for('admin.posts'))

@admin_bp.route('/posts/mass-action', methods=['POST'])
@login_required
@admin_required
def posts_mass_action():
    action = request.form.get('action')
    post_ids = request.form.getlist('post_ids')
    
    if not post_ids:
        flash('Не выбрано ни одного поста', 'warning')
        return redirect(url_for('admin.posts'))
    
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    
    if action == 'delete':
        for post in posts:
            db.session.delete(post)
        flash(f'Удалено {len(posts)} постов', 'success')
    elif action == 'publish':
        for post in posts:
            post.is_published = True
        flash(f'Опубликовано {len(posts)} постов', 'success')
    elif action == 'unpublish':
        for post in posts:
            post.is_published = False
        flash(f'Снято с публикации {len(posts)} постов', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.posts'))

# ===== УПРАВЛЕНИЕ ФОРУМОМ =====
@admin_bp.route('/forum-topics')
@login_required
@admin_required
def forum_topics():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Фильтры
    search = request.args.get('search', '')
    author = request.args.get('author', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    query = ForumTopic.query.join(User)
    
    # Поиск
    if search:
        query = query.filter(ForumTopic.title.ilike(f'%{search}%'))
    
    # Фильтр по автору
    if author:
        query = query.filter(User.username.ilike(f'%{author}%'))
    
    # Сортировка
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(ForumTopic, sort_by)))
    else:
        query = query.order_by(asc(getattr(ForumTopic, sort_by)))
    
    topics = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/forum_topics.html', topics=topics,
                         search=search, author=author,
                         sort_by=sort_by, sort_order=sort_order)

@admin_bp.route('/forum-topics/<int:topic_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_forum_topic(topic_id):
    topic = ForumTopic.query.get_or_404(topic_id)
    title = topic.title
    db.session.delete(topic)
    db.session.commit()
    flash(f'Тема "{title}" удалена', 'success')
    return redirect(url_for('admin.forum_topics'))

@admin_bp.route('/forum-topics/mass-action', methods=['POST'])
@login_required
@admin_required
def forum_topics_mass_action():
    action = request.form.get('action')
    topic_ids = request.form.getlist('topic_ids')
    
    if not topic_ids:
        flash('Не выбрано ни одной темы', 'warning')
        return redirect(url_for('admin.forum_topics'))
    
    topics = ForumTopic.query.filter(ForumTopic.id.in_(topic_ids)).all()
    
    if action == 'delete':
        for topic in topics:
            db.session.delete(topic)
        flash(f'Удалено {len(topics)} тем', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.forum_topics'))

# ===== УПРАВЛЕНИЕ СООБЩЕНИЯМИ ФОРУМА =====
@admin_bp.route('/forum-posts')
@login_required
@admin_required
def forum_posts():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Фильтры
    search = request.args.get('search', '')
    author = request.args.get('author', '')
    topic = request.args.get('topic', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    query = ForumPost.query.join(User).join(ForumTopic)
    
    # Поиск
    if search:
        query = query.filter(ForumPost.content.ilike(f'%{search}%'))
    
    # Фильтр по автору
    if author:
        query = query.filter(User.username.ilike(f'%{author}%'))
    
    # Фильтр по теме
    if topic:
        query = query.filter(ForumTopic.title.ilike(f'%{topic}%'))
    
    # Сортировка
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(ForumPost, sort_by)))
    else:
        query = query.order_by(asc(getattr(ForumPost, sort_by)))
    
    posts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/forum_posts.html', posts=posts,
                         search=search, author=author, topic=topic,
                         sort_by=sort_by, sort_order=sort_order)

@admin_bp.route('/forum-posts/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
    db.session.delete(post)
    db.session.commit()
    flash(f'Сообщение "{content_preview}" удалено', 'success')
    return redirect(url_for('admin.forum_posts'))

@admin_bp.route('/forum-posts/mass-action', methods=['POST'])
@login_required
@admin_required
def forum_posts_mass_action():
    action = request.form.get('action')
    post_ids = request.form.getlist('post_ids')
    
    if not post_ids:
        flash('Не выбрано ни одного сообщения', 'warning')
        return redirect(url_for('admin.forum_posts'))
    
    posts = ForumPost.query.filter(ForumPost.id.in_(post_ids)).all()
    
    if action == 'delete':
        for post in posts:
            db.session.delete(post)
        flash(f'Удалено {len(posts)} сообщений', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.forum_posts'))

# ===== API для AJAX =====
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API для получения статистики"""
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'users': {
            'total': User.query.count(),
            'new_week': User.query.filter(User.created_at >= week_ago).count(),
            'new_month': User.query.filter(User.created_at >= month_ago).count()
        },
        'posts': {
            'total': Post.query.count(),
            'new_week': Post.query.filter(Post.created_at >= week_ago).count(),
            'new_month': Post.query.filter(Post.created_at >= month_ago).count()
        },
        'topics': {
            'total': ForumTopic.query.count(),
            'new_week': ForumTopic.query.filter(ForumTopic.created_at >= week_ago).count(),
            'new_month': ForumTopic.query.filter(ForumTopic.created_at >= month_ago).count()
        },
        'forum_posts': {
            'total': ForumPost.query.count(),
            'new_week': ForumPost.query.filter(ForumPost.created_at >= week_ago).count(),
            'new_month': ForumPost.query.filter(ForumPost.created_at >= month_ago).count()
        }
    }
    
    return jsonify(stats)

# ===== УПРАВЛЕНИЕ ГОЛОСОВАНИЯМИ =====
@admin_bp.route('/votings')
@login_required
@admin_required
def votings():
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Фильтры
    search = request.args.get('search', '')
    creator = request.args.get('creator', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    query = Voting.query.join(User)
    
    # Поиск
    if search:
        query = query.filter(
            or_(
                Voting.title.ilike(f'%{search}%'),
                Voting.description.ilike(f'%{search}%'),
                Voting.question.ilike(f'%{search}%')
            )
        )
    
    # Фильтр по создателю
    if creator:
        query = query.filter(User.username.ilike(f'%{creator}%'))
    
    # Фильтр по статусу
    if status == 'active':
        query = query.filter(Voting.is_active.is_(True))
    elif status == 'inactive':
        query = query.filter(Voting.is_active.is_(False))
    elif status == 'open':
        now = datetime.utcnow()
        query = query.filter(
            and_(
                Voting.start_date <= now,
                Voting.end_date >= now,
                Voting.is_active.is_(True)
            )
        )
    elif status == 'closed':
        now = datetime.utcnow()
        query = query.filter(Voting.end_date < now)
    elif status == 'upcoming':
        now = datetime.utcnow()
        query = query.filter(Voting.start_date > now)
    
    # Сортировка
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(Voting, sort_by)))
    else:
        query = query.order_by(asc(getattr(Voting, sort_by)))
    
    votings = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/votings.html', votings=votings,
                         search=search, creator=creator, status=status,
                         sort_by=sort_by, sort_order=sort_order,
                         datetime=datetime)

@admin_bp.route('/votings/<int:voting_id>')
@login_required
@admin_required
def voting_detail(voting_id):
    voting = Voting.query.get_or_404(voting_id)
    results, total_votes = voting.get_results()
    return render_template('admin/voting_detail.html', voting=voting, results=results, total_votes=total_votes, datetime=datetime)

@admin_bp.route('/votings/<int:voting_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_voting_status(voting_id):
    voting = Voting.query.get_or_404(voting_id)
    voting.is_active = not voting.is_active
    db.session.commit()
    flash(f'Статус голосования "{voting.title}" изменен', 'success')
    return redirect(url_for('admin.votings'))

@admin_bp.route('/votings/<int:voting_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_voting(voting_id):
    voting = Voting.query.get_or_404(voting_id)
    title = voting.title
    db.session.delete(voting)
    db.session.commit()
    flash(f'Голосование "{title}" удалено', 'success')
    return redirect(url_for('admin.votings'))

@admin_bp.route('/votings/mass-action', methods=['POST'])
@login_required
@admin_required
def votings_mass_action():
    action = request.form.get('action')
    voting_ids = request.form.getlist('voting_ids')
    
    if not voting_ids:
        flash('Не выбрано ни одного голосования', 'warning')
        return redirect(url_for('admin.votings'))
    
    votings = Voting.query.filter(Voting.id.in_(voting_ids)).all()
    
    if action == 'activate':
        for voting in votings:
            voting.is_active = True
        flash(f'Активировано {len(votings)} голосований', 'success')
    elif action == 'deactivate':
        for voting in votings:
            voting.is_active = False
        flash(f'Деактивировано {len(votings)} голосований', 'success')
    elif action == 'delete':
        for voting in votings:
            db.session.delete(voting)
        flash(f'Удалено {len(votings)} голосований', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.votings'))

# ===== УПРАВЛЕНИЕ ГОЛОСАМИ =====
@admin_bp.route('/votes')
@login_required
@admin_required
def votes():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Фильтры
    voting_title = request.args.get('voting', '')
    property_number = request.args.get('property', '')
    sort_by = request.args.get('sort', 'voted_at')
    sort_order = request.args.get('order', 'desc')
    
    query = Vote.query.join(Voting).join(Property)
    
    # Фильтр по голосованию
    if voting_title:
        query = query.filter(Voting.title.ilike(f'%{voting_title}%'))
    
    # Фильтр по собственности
    if property_number:
        query = query.filter(Property.number.ilike(f'%{property_number}%'))
    
    # Сортировка
    if sort_order == 'desc':
        query = query.order_by(desc(getattr(Vote, sort_by)))
    else:
        query = query.order_by(asc(getattr(Vote, sort_by)))
    
    votes = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/votes.html', votes=votes,
                         voting_title=voting_title, property_number=property_number,
                         sort_by=sort_by, sort_order=sort_order)

@admin_bp.route('/votes/<int:vote_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_vote(vote_id):
    vote = Vote.query.get_or_404(vote_id)
    db.session.delete(vote)
    db.session.commit()
    flash('Голос удален', 'success')
    return redirect(url_for('admin.votes'))

@admin_bp.route('/votes/mass-action', methods=['POST'])
@login_required
@admin_required
def votes_mass_action():
    action = request.form.get('action')
    vote_ids = request.form.getlist('vote_ids')
    
    if not vote_ids:
        flash('Не выбрано ни одного голоса', 'warning')
        return redirect(url_for('admin.votes'))
    
    votes = Vote.query.filter(Vote.id.in_(vote_ids)).all()
    
    if action == 'delete':
        for vote in votes:
            db.session.delete(vote)
        flash(f'Удалено {len(votes)} голосов', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.votes'))

 