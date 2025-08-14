from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from . import voting
from model.db_models import db, Voting, VotingOption, Vote, Property, User
from datetime import datetime, timedelta
from utils.content_password import check_content_access, has_content_password, set_content_password, remove_content_password
import json

@voting.route('/')
def index():
    """Главная страница системы голосования"""
    page = request.args.get('page', 1, type=int)
    votings = Voting.query.order_by(Voting.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('voting/index.html', votings=votings)

@voting.route('/voting/<int:voting_id>')
def view_voting(voting_id):
    """Просмотр голосования"""
    voting_obj = db.session.get(Voting, voting_id)
    if voting_obj is None:
        abort(404)
    
    # Проверяем доступ к голосованию
    if not check_content_access('voting', voting_id):
        return render_template('voting/password_required.html', 
                             voting=voting_obj,
                             content_type='voting',
                             content_id=voting_id)
    
    results, total_votes = voting_obj.get_results()
    
    # Проверяем, голосовал ли текущий пользователь
    user_voted = False
    user_vote = None
    if current_user.is_authenticated:
        for property in current_user.properties:
            vote = db.session.query(Vote).filter_by(
                voting_id=voting_id, 
                property_id=property.id
            ).first()
            if vote:
                user_voted = True
                user_vote = vote
                break
    
    return render_template('voting/view.html', 
                         voting=voting_obj, 
                         results=results, 
                         total_votes=total_votes,
                         user_voted=user_voted,
                         user_vote=user_vote)

@voting.route('/create', methods=['GET', 'POST'])
@login_required
def create_voting():
    """Создание нового голосования"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        question = request.form.get('question')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        options = request.form.getlist('options')
        
        # Валидация
        if not all([title, description, question, start_date_str, end_date_str]):
            flash('Все поля должны быть заполнены')
            return redirect(url_for('voting.create_voting'))
        
        if len(options) < 2:
            flash('Должно быть минимум 2 варианта ответа')
            return redirect(url_for('voting.create_voting'))
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Неверный формат даты')
            return redirect(url_for('voting.create_voting'))
        
        if start_date >= end_date:
            flash('Дата окончания должна быть позже даты начала')
            return redirect(url_for('voting.create_voting'))
        
        if start_date < datetime.utcnow():
            flash('Дата начала не может быть в прошлом')
            return redirect(url_for('voting.create_voting'))
        
        # Создаем голосование
        voting_obj = Voting(
            title=title,
            description=description,
            question=question,
            start_date=start_date,
            end_date=end_date,
            created_by=current_user.id
        )
        db.session.add(voting_obj)
        db.session.flush()  # Получаем ID голосования
        
        # Добавляем варианты ответа
        for option_text in options:
            if option_text.strip():
                option = VotingOption(
                    text=option_text.strip(),
                    voting_id=voting_obj.id
                )
                db.session.add(option)
        
        db.session.commit()
        flash('Голосование успешно создано!')
        return redirect(url_for('voting.view_voting', voting_id=voting_obj.id))
    
    return render_template('voting/create.html')

@voting.route('/vote/<int:voting_id>', methods=['POST'])
@login_required
def submit_vote(voting_id):
    """Подача голоса"""
    voting_obj = db.session.get(Voting, voting_id)
    if voting_obj is None:
        abort(404)
    option_id = request.form.get('option_id', type=int)
    
    # Проверяем, открыто ли голосование
    if not voting_obj.is_open():
        flash('Голосование закрыто или еще не началось')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    # Проверяем, есть ли у пользователя собственность
    if not current_user.properties:
        flash('У вас должна быть зарегистрирована собственность для участия в голосовании')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    # Проверяем, голосовал ли уже пользователь
    for property in current_user.properties:
        existing_vote = db.session.query(Vote).filter_by(
            voting_id=voting_id, 
            property_id=property.id
        ).first()
        if existing_vote:
            flash('Вы уже участвовали в этом голосовании')
            return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    # Проверяем, существует ли вариант ответа
    option = db.session.query(VotingOption).filter_by(
        id=option_id, 
        voting_id=voting_id
    ).first()
    if not option:
        flash('Неверный вариант ответа')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    # Создаем голос для каждой собственности пользователя
    for property in current_user.properties:
        vote = Vote(
            voting_id=voting_id,
            property_id=property.id,
            option_id=option_id
        )
        db.session.add(vote)
    
    db.session.commit()
    flash('Ваш голос учтен!')
    return redirect(url_for('voting.view_voting', voting_id=voting_id))

@voting.route('/results/<int:voting_id>')
def results(voting_id):
    """Результаты голосования"""
    voting_obj = db.session.get(Voting, voting_id)
    if voting_obj is None:
        abort(404)
    
    # Проверяем доступ к результатам голосования
    if not check_content_access('voting', voting_id):
        return render_template('voting/password_required.html', 
                             voting=voting_obj,
                             content_type='voting',
                             content_id=voting_id)
    
    results, total_votes = voting_obj.get_results()
    
    # Получаем статистику по собственности
    property_stats = {}
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        # Администратор видит все квартиры
        properties = db.session.query(Property).all()
    elif current_user.is_authenticated:
        # Обычный пользователь видит только свои квартиры
        properties = current_user.properties
    else:
        properties = []
    for property in properties:
        vote = db.session.query(Vote).filter_by(
            voting_id=voting_id, 
            property_id=property.id
        ).first()
        if vote:
            property_stats[property.number] = {
                'area': property.area,
                'vote': vote.option.text,
                'owner': property.owner.username,
                'street': property.street,
                'house_number': property.house_number
            }
    
    return render_template('voting/results.html', 
                         voting=voting_obj, 
                         results=results, 
                         total_votes=total_votes,
                         property_stats=property_stats)

@voting.route('/my-votings')
@login_required
def my_votings():
    """Голосования, созданные текущим пользователем"""
    page = request.args.get('page', 1, type=int)
    votings = Voting.query.filter_by(created_by=current_user.id).order_by(
        Voting.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('voting/my_votings.html', votings=votings)

@voting.route('/edit/<int:voting_id>', methods=['GET', 'POST'])
@login_required
def edit_voting(voting_id):
    """Редактирование голосования"""
    voting_obj = db.session.get(Voting, voting_id)
    if voting_obj is None:
        abort(404)
    
    # Проверяем права доступа
    if voting_obj.created_by != current_user.id:
        abort(403)
    
    # Проверяем, можно ли редактировать
    if voting_obj.is_open():
        flash('Нельзя редактировать активное голосование')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        question = request.form.get('question')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        options = request.form.getlist('options')
        
        # Валидация
        if not all([title, description, question, start_date_str, end_date_str]):
            flash('Все поля должны быть заполнены')
            return redirect(url_for('voting.edit_voting', voting_id=voting_id))
        
        if len(options) < 2:
            flash('Должно быть минимум 2 варианта ответа')
            return redirect(url_for('voting.edit_voting', voting_id=voting_id))
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Неверный формат даты')
            return redirect(url_for('voting.edit_voting', voting_id=voting_id))
        
        if start_date >= end_date:
            flash('Дата окончания должна быть позже даты начала')
            return redirect(url_for('voting.edit_voting', voting_id=voting_id))
        
        # Обновляем голосование
        voting_obj.title = title
        voting_obj.description = description
        voting_obj.question = question
        voting_obj.start_date = start_date
        voting_obj.end_date = end_date
        
        # Удаляем старые варианты и добавляем новые
        db.session.query(VotingOption).filter_by(voting_id=voting_id).delete()
        for option_text in options:
            if option_text.strip():
                option = VotingOption(
                    text=option_text.strip(),
                    voting_id=voting_id
                )
                db.session.add(option)
        
        db.session.commit()
        flash('Голосование успешно обновлено!')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    return render_template('voting/edit.html', voting=voting_obj)

@voting.route('/delete/<int:voting_id>', methods=['POST'])
@login_required
def delete_voting(voting_id):
    """Удаление голосования"""
    voting_obj = db.session.get(Voting, voting_id)
    if voting_obj is None:
        abort(404)
    
    # Проверяем права доступа
    if voting_obj.created_by != current_user.id:
        abort(403)
    
    # Проверяем, можно ли удалить
    if voting_obj.is_open():
        flash('Нельзя удалить активное голосование')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    db.session.delete(voting_obj)
    db.session.commit()
    
    flash('Голосование удалено!')
    return redirect(url_for('voting.index'))

@voting.route('/properties')
@login_required
def my_properties():
    """Управление собственностью пользователя"""
    return render_template('voting/properties.html', properties=current_user.properties)

@voting.route('/add-property', methods=['GET', 'POST'])
@login_required
def add_property():
    """Добавление собственности"""
    if request.method == 'POST':
        street = request.form.get('street')
        house_number = request.form.get('house_number')
        entrance = request.form.get('entrance')
        floor = request.form.get('floor', type=int)
        number = request.form.get('number')
        area = request.form.get('area', type=float)
        
        # Проверяем обязательные поля
        if not all([street, house_number, number, area]):
            flash('Поля "Название улицы", "Номер дома", "Номер квартиры" и "Площадь" обязательны для заполнения')
            return redirect(url_for('voting.add_property'))
        
        if area <= 0:
            flash('Площадь должна быть больше нуля')
            return redirect(url_for('voting.add_property'))
        
        # Проверяем, не занят ли номер
        existing = db.session.query(Property).filter_by(number=number).first()
        if existing:
            flash('Собственность с таким номером уже зарегистрирована')
            return redirect(url_for('voting.add_property'))
        
        property_obj = Property(
            street=street,
            house_number=house_number,
            entrance=entrance if entrance else None,
            floor=floor if floor else None,
            number=number,
            area=area,
            owner_id=current_user.id
        )
        db.session.add(property_obj)
        db.session.commit()
        
        flash('Собственность успешно добавлена!')
        return redirect(url_for('voting.my_properties'))
    
    return render_template('voting/add_property.html')

@voting.route('/my-votes')
@login_required
def my_votes():
    """Страница с голосами текущего пользователя"""
    page = request.args.get('page', 1, type=int)
    
    # Получаем голоса пользователя через его собственность
    votes = db.session.query(Vote).join(Vote.property).filter(
        Property.owner_id == current_user.id
    ).join(Vote.voting).join(Vote.option).order_by(
        Vote.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('voting/my_votes.html', votes=votes, datetime=datetime)

@voting.route('/edit-property/<int:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    """Редактирование собственности"""
    property_obj = db.session.get(Property, property_id)
    if property_obj is None:
        abort(404)
    
    # Проверяем права доступа
    if property_obj.owner_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        street = request.form.get('street')
        house_number = request.form.get('house_number')
        entrance = request.form.get('entrance')
        floor = request.form.get('floor', type=int)
        number = request.form.get('number')
        area = request.form.get('area', type=float)
        
        # Проверяем обязательные поля
        if not all([street, house_number, number, area]):
            flash('Поля "Название улицы", "Номер дома", "Номер квартиры" и "Площадь" обязательны для заполнения')
            return redirect(url_for('voting.edit_property', property_id=property_id))
        
        if area <= 0:
            flash('Площадь должна быть больше нуля')
            return redirect(url_for('voting.edit_property', property_id=property_id))
        
        # Проверяем, не занят ли номер другим объектом
        existing = db.session.query(Property).filter_by(number=number).first()
        if existing and existing.id != property_id:
            flash('Собственность с таким номером уже зарегистрирована')
            return redirect(url_for('voting.edit_property', property_id=property_id))
        
        # Обновляем собственность
        property_obj.street = street
        property_obj.house_number = house_number
        property_obj.entrance = entrance if entrance else None
        property_obj.floor = floor if floor else None
        property_obj.number = number
        property_obj.area = area
        db.session.commit()
        
        flash('Собственность успешно обновлена!')
        return redirect(url_for('voting.my_properties'))
    
    return render_template('voting/edit_property.html', property=property_obj)

@voting.route('/delete-property/<int:property_id>', methods=['POST'])
@login_required
def delete_property(property_id):
    """Удаление собственности"""
    property_obj = db.session.get(Property, property_id)
    if property_obj is None:
        abort(404)
    
    # Проверяем права доступа
    if property_obj.owner_id != current_user.id:
        abort(403)
    
    # Проверяем, нет ли активных голосований
    active_votes = db.session.query(Vote).filter_by(property_id=property_id).first()
    if active_votes:
        flash('Нельзя удалить собственность, которая участвовала в голосованиях')
        return redirect(url_for('voting.my_properties'))
    
    db.session.delete(property_obj)
    db.session.commit()
    
    flash('Собственность удалена!')
    return redirect(url_for('voting.my_properties'))

@voting.route('/voting/<int:voting_id>/set-password', methods=['GET', 'POST'])
@login_required
def set_voting_password(voting_id):
    """Установка пароля для голосования"""
    voting_obj = db.session.get(Voting, voting_id)
    if voting_obj is None:
        abort(404)
    
    # Проверяем, что пользователь является создателем голосования
    if voting_obj.created_by != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        password = request.form.get('password')
        action = request.form.get('action')
        
        if action == 'set' and password:
            set_content_password('voting', voting_id, password, current_user.id)
            flash('Пароль для голосования установлен!')
        elif action == 'remove':
            remove_content_password('voting', voting_id)
            flash('Пароль для голосования удален!')
        else:
            flash('Пароль не может быть пустым')
        
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    has_password = has_content_password('voting', voting_id)
    return render_template('voting/set_password.html', 
                         voting=voting_obj, 
                         has_password=has_password)

@voting.route('/voting/<int:voting_id>/check-password', methods=['POST'])
@login_required
def check_voting_password(voting_id):
    """Проверка пароля для доступа к голосованию"""
    voting_obj = db.session.get(Voting, voting_id)
    if voting_obj is None:
        abort(404)
    
    password = request.form.get('password')
    if not password:
        flash('Введите пароль')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    
    if check_content_access('voting', voting_id, password):
        flash('Доступ разрешен!')
        return redirect(url_for('voting.view_voting', voting_id=voting_id))
    else:
        flash('Неверный пароль')
        return redirect(url_for('voting.view_voting', voting_id=voting_id)) 