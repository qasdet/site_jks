# 🚀 Быстрая настройка Telegram 2FA

## Шаг 1: Создание бота
1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте `/newbot`
4. Введите имя: "Flask Security Bot"
5. Введите username: "your_flask_bot"
6. Сохраните токен

## Шаг 2: Настройка переменных
```bash
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="ваш_токен_здесь"
$env:TELEGRAM_BOT_USERNAME="your_flask_bot"

# Linux/Mac
export TELEGRAM_BOT_TOKEN="ваш_токен_здесь"
export TELEGRAM_BOT_USERNAME="your_flask_bot"
```

## Шаг 3: Тестирование
```bash
python test_telegram_bot.py
```

## Шаг 4: Настройка 2FA пользователем
1. Пользователь находит бота в Telegram
2. Отправляет любое сообщение боту
3. На сайте: Профиль → Безопасность → Включить Telegram 2FA
4. Вводит свой Telegram username
5. Получает код в Telegram
6. Вводит код на сайте

## Готово! 🎉

Теперь при каждом входе пользователь будет получать код подтверждения в Telegram. 