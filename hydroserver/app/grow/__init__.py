from flask import Blueprint

bp = Blueprint('grow', __name__)

from app.grow import routes
