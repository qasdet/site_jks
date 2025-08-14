from flask import Blueprint

telegram_bot = Blueprint('telegram_bot', __name__)

from . import routes 