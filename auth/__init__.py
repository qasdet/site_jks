# Импорт класса Blueprint из Flask для организации модульной структуры приложения
from flask import Blueprint

# Создание blueprint-а для модуля аутентификации (auth)
auth = Blueprint('auth', __name__)

# Импорт маршрутов (routes) для регистрации обработчиков URL в этом blueprint-е
from . import routes
