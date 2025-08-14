from flask import Blueprint

voting = Blueprint('voting', __name__)

from . import routes 