# Скрипты для работы с базой данных

Этот документ описывает Python скрипты для управления базой данных приложения Flask.

## 📁 Доступные скрипты

### 1. `update_database.py` - Обновление структуры базы данных

**Назначение:** Добавляет новые поля в существующую базу данных без потери данных.

**Использование:**
```bash
python update_database.py
```

**Что делает:**
- Добавляет поле `image_url` в таблицу `forum_topic` для хранения ссылок на изображения
- Добавляет поле `parent_id` в таблицу `forum_post` для древовидных ответов
- Добавляет поля `updated_at` в таблицы `post` и `forum_post`
- Добавляет поля `created_at` во все таблицы
- Добавляет поле `is_active` в таблицу `user`
- Показывает структуру базы данных после обновления

### 2. `reset_database.py` - Полный сброс базы данных

**Назначение:** Полностью пересоздает базу данных с нуля.

**Использование:**
```bash
python reset_database.py
```

**Что делает:**
- Удаляет существующую базу данных
- Создает новую базу данных со всеми таблицами
- Создает индексы для улучшения производительности
- Добавляет тестовые данные (пользователь, собственность, пост, тема форума)

**⚠️ Внимание:** Этот скрипт удаляет все существующие данные!

### 3. `backup_database.py` - Управление резервными копиями

**Назначение:** Создание, восстановление и управление резервными копиями базы данных.

**Использование:**

#### Создание резервной копии:
```bash
python backup_database.py backup
```

#### Просмотр списка резервных копий:
```bash
python backup_database.py list
```

#### Восстановление из резервной копии:
```bash
python backup_database.py restore app_backup_20241201_143022.db
```

#### Очистка старых резервных копий (оставить 5 последних):
```bash
python backup_database.py cleanup 5
```

#### Интерактивный режим:
```bash
python backup_database.py
```

**Что делает:**
- Создает резервные копии в папке `backups/`
- Автоматически добавляет временные метки к именам файлов
- Показывает размер и дату создания резервных копий
- Создает резервную копию перед восстановлением
- Удаляет старые резервные копии для экономии места

## 🗂️ Структура базы данных

### Таблицы:

1. **user** - Пользователи системы
   - `id` (INTEGER, PRIMARY KEY)
   - `username` (VARCHAR(80), UNIQUE)
   - `email` (VARCHAR(120), UNIQUE)
   - `password_hash` (VARCHAR(128))
   - `created_at` (DATETIME)
   - `is_active` (BOOLEAN)

2. **post** - Посты блога
   - `id` (INTEGER, PRIMARY KEY)
   - `title` (VARCHAR(200))
   - `content` (TEXT)
   - `created_at` (DATETIME)
   - `updated_at` (DATETIME)
   - `user_id` (INTEGER, FOREIGN KEY)

3. **property** - Собственность/квартиры
   - `id` (INTEGER, PRIMARY KEY)
   - `number` (VARCHAR(20), UNIQUE)
   - `area` (FLOAT)
   - `owner_id` (INTEGER, FOREIGN KEY)
   - `created_at` (DATETIME)

4. **voting** - Голосования
   - `id` (INTEGER, PRIMARY KEY)
   - `title` (VARCHAR(200))
   - `description` (TEXT)
   - `question` (VARCHAR(500))
   - `start_date` (DATETIME)
   - `end_date` (DATETIME)
   - `is_active` (BOOLEAN)
   - `created_by` (INTEGER, FOREIGN KEY)
   - `created_at` (DATETIME)

5. **voting_option** - Варианты ответов для голосования
   - `id` (INTEGER, PRIMARY KEY)
   - `text` (VARCHAR(200))
   - `voting_id` (INTEGER, FOREIGN KEY)

6. **vote** - Голоса
   - `id` (INTEGER, PRIMARY KEY)
   - `voting_id` (INTEGER, FOREIGN KEY)
   - `property_id` (INTEGER, FOREIGN KEY)
   - `option_id` (INTEGER, FOREIGN KEY)
   - `voted_at` (DATETIME)

7. **forum_topic** - Темы форума
   - `id` (INTEGER, PRIMARY KEY)
   - `title` (VARCHAR(200))
   - `image_url` (VARCHAR(500)) - **НОВОЕ ПОЛЕ**
   - `created_at` (DATETIME)
   - `user_id` (INTEGER, FOREIGN KEY)

8. **forum_post** - Сообщения форума
   - `id` (INTEGER, PRIMARY KEY)
   - `content` (TEXT)
   - `created_at` (DATETIME)
   - `updated_at` (DATETIME)
   - `user_id` (INTEGER, FOREIGN KEY)
   - `topic_id` (INTEGER, FOREIGN KEY)
   - `parent_id` (INTEGER, FOREIGN KEY) - для древовидных ответов

## 🔧 Рекомендуемый порядок использования

1. **При первом запуске:**
   ```bash
   python reset_database.py
   ```

2. **При добавлении новых функций (как сейчас с изображениями):**
   ```bash
   python update_database.py
   ```

3. **Регулярное резервное копирование:**
   ```bash
   python backup_database.py backup
   ```

4. **Перед крупными изменениями:**
   ```bash
   python backup_database.py backup
   # ... выполняем изменения ...
   python update_database.py
   ```

## 🚨 Важные замечания

- **Всегда создавайте резервную копию** перед выполнением `reset_database.py`
- Скрипт `update_database.py` безопасен и не удаляет данные
- Резервные копии сохраняются в папке `backups/`
- База данных находится в `instance/app.db`

## 🐛 Устранение проблем

### Ошибка "no such column"
Если возникает ошибка о отсутствующем поле, выполните:
```bash
python update_database.py
```

### Поврежденная база данных
Если база данных повреждена:
```bash
python backup_database.py list
python backup_database.py restore <имя_файла_резервной_копии>
```

### Полный сброс
Если нужно начать с чистого листа:
```bash
python reset_database.py
``` 