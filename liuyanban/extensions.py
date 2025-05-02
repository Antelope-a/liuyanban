# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'main.admin_login'
db = SQLAlchemy()
