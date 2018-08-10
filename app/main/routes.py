from flask import render_template
from app import login
from app.models import User
from . import bp


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('main/index.html', title='Home')


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
