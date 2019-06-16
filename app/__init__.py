
# __init__.py
# @author Cabbage
# @description 
# @created 2019-05-01T20:54:05.913Z+08:00
# @last-modified 2019-06-16T22:23:51.348Z+08:00
#

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
moment = Moment()

from app.main import bp as main_bp
app.register_blueprint(main_bp)

from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from app.templates import bp as templates_bp
app.register_blueprint(templates_bp)

# admin
from .admin import admin
admin.init_app(app)

from app import models

moment.init_app(app)
