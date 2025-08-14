# Исправление ошибки отключения 2FA

## Проблема

При попытке отключения Telegram двухфакторной аутентификации возникала ошибка:
```
"GET /telegram/disable-2fa HTTP/1.1" 405 - Method Not Allowed
```

## Причина

Маршрут `/telegram/disable-2fa` был настроен только для POST запросов:
```python
@telegram_bot.route('/disable-2fa', methods=['POST'])
```

Но в профиле пользователя использовалась GET ссылка:
```html
<a href="{{ url_for('telegram_bot.disable_2fa') }}">
```

## Решение

### 1. Обновлен маршрут
Изменен маршрут для поддержки GET и POST запросов:
```python
@telegram_bot.route('/disable-2fa', methods=['GET', 'POST'])
@login_required
def disable_2fa():
    if not current_user.telegram_enabled:
        flash('Telegram 2FA не включен')
        return redirect(url_for('profile'))
    
    # Если это GET запрос, показываем страницу подтверждения
    if request.method == 'GET':
        return render_template('telegram_bot/disable_2fa.html')
    
    # Для POST запросов выполняем отключение
    if request.method == 'POST':
        # Отключаем 2FA
        current_user.disable_telegram_2fa()
        db.session.commit()
        
        # Логируем событие
        log_security_event(
            user_id=current_user.id,
            event_type='telegram_2fa_disabled',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details='Telegram 2FA отключен'
        )
        
        flash('Telegram двухфакторная аутентификация отключена')
        return redirect(url_for('profile'))
```

### 2. Создан шаблон подтверждения
Создан новый шаблон `templates/telegram_bot/disable_2fa.html` с:
- Предупреждением о снижении безопасности
- Кнопкой подтверждения отключения
- Кнопкой отмены
- Современным дизайном

### 3. Безопасность
- GET запрос показывает страницу подтверждения
- POST запрос выполняет фактическое отключение
- Логирование всех операций отключения
- Проверка, что 2FA включен перед отключением

## Файлы

### Измененные файлы:
- `telegram_bot/routes.py` - Обновлен маршрут disable_2fa
- `templates/telegram_bot/disable_2fa.html` - Новый шаблон подтверждения

### Логика работы:
1. Пользователь нажимает "Отключить" в профиле
2. Переходит на страницу подтверждения (GET)
3. Нажимает "Отключить 2FA" (POST)
4. 2FA отключается и пользователь перенаправляется в профиль

## Преимущества

- ✅ Исправлена ошибка 405 Method Not Allowed
- ✅ Добавлено подтверждение перед отключением
- ✅ Улучшена безопасность (POST для критических операций)
- ✅ Логирование всех операций
- ✅ Современный UI с предупреждениями
- ✅ Сохранена вся существующая логика проекта 