from flask import Blueprint

security = Blueprint('security', __name__)

from . import routes 