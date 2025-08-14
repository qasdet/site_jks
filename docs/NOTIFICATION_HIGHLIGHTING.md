# Выделение сообщений из уведомлений

## Описание

Функциональность автоматического выделения сообщений на форуме при переходе из уведомлений позволяет пользователям быстро находить те сообщения, на которые они получили уведомления.

## Как это работает

### 1. Ссылки в уведомлениях
- В уведомлениях типа `forum_reply` ссылки содержат хэш с ID сообщения
- Формат ссылки: `/forum/topic/{topic_id}#post-{post_id}`
- Пример: `/forum/topic/1#post-5`

### 2. Автоматическое выделение
При загрузке страницы темы JavaScript:
1. Проверяет наличие хэша в URL
2. Находит сообщение с соответствующим ID
3. Плавно прокручивает к сообщению
4. Добавляет визуальное выделение
5. Через 5 секунд убирает выделение

### 3. Визуальные эффекты
- **Фон**: Градиентный желтый фон
- **Рамка**: Желтая рамка толщиной 3px
- **Тень**: Увеличенная тень с желтым оттенком
- **Анимация**: Пульсирующий эффект в течение 3 секунд
- **Иконка**: Колокольчик в правом верхнем углу с анимацией встряхивания

## Техническая реализация

### CSS классы
```css
.post.highlighted {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    border: 3px solid #ffc107;
    box-shadow: 0 6px 20px rgba(255, 193, 7, 0.3);
    animation: highlight-pulse 3s ease-in-out;
    position: relative;
}
```

### JavaScript
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const hash = window.location.hash;
    if (hash && hash.startsWith('#post-')) {
        const postId = hash.substring(6);
        const postElement = document.getElementById('post-' + postId);
        if (postElement) {
            // Плавная прокрутка и выделение
            postElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            });
            postElement.classList.add('highlighted');
            
            // Убираем выделение через 5 секунд
            setTimeout(function() {
                postElement.classList.remove('highlighted');
            }, 5000);
        }
    }
});
```

## Файлы

### Измененные файлы:
- `templates/forum/notifications.html` - Обновлены ссылки с хэшами
- `templates/forum/topic.html` - Добавлены CSS и JavaScript для выделения

### Структура ID сообщений:
- Каждое сообщение имеет ID: `post-{post_id}`
- Шаблон: `templates/forum/post_tree.html`

## Использование

1. Пользователь получает уведомление о новом ответе
2. Переходит по ссылке в уведомлении
3. Автоматически прокручивается к нужному сообщению
4. Сообщение выделяется визуально
5. Выделение исчезает через 5 секунд

## Преимущества

- ✅ Быстрый поиск нужного сообщения
- ✅ Визуальная индикация
- ✅ Плавная анимация
- ✅ Автоматическое исчезновение выделения
- ✅ Работает с вложенными сообщениями
- ✅ Адаптивный дизайн 