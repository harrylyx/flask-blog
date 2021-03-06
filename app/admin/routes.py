import time
import datetime
from flask import redirect, url_for, render_template, flash, request, jsonify
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app
from app.models import User
from app.admin.forms import LoginForm
from wtforms.fields import TextAreaField
from app.utils.nginx_log_parse import get_json_raw_data
from app.utils.nginx_log_parse import stat_daily_page_view
from app.utils.nginx_log_parse import stat_daily_user_view


def format_datetime(self, request, obj, fieldname, *args, **kwargs):
    utc_st = getattr(obj, fieldname)
    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st.strftime("%Y-%m-%d %H:%M")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('admin/login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@app.route('/ip_raw_data', methods=['GET'])
@login_required
def get_log_ip_raw_data():
    if not current_user.is_authenticated and current_user.username == "cabbage":
        return redirect(url_for('login'))
    result = get_json_raw_data()
    return jsonify(result)


@app.route('/ip_pv', methods=['GET'])
@login_required
def get_log_ip_pv():
    if not current_user.is_authenticated and current_user.username == "cabbage":
        return redirect(url_for('login'))
    result = stat_daily_page_view()
    return jsonify(result)


@app.route('/ip_uv', methods=['GET'])
@login_required
def get_log_ip_uv():
    if not current_user.is_authenticated and current_user.username == "cabbage":
        return redirect(url_for('login'))
    result = stat_daily_user_view()
    return jsonify(result)


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        if not current_user.is_authenticated and current_user.username == "cabbage":
            return redirect(url_for('login'))
        # if not current_user.is_administrator():
        #     return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()


class ArticleAdmin(ModelView):
    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"

    column_list = ('title', 'created', 'category', 'tags')

    form_excluded_columns = ('author', 'content_html', 'created')

    column_searchable_list = ('title',)

    column_formatters = dict(created=format_datetime)

    form_create_rules = (
        'title', 'category', 'tags', 'summary', 'content',
    )
    form_edit_rules = form_create_rules

    form_overrides = dict(
        summary=TextAreaField)

    form_widget_args = {
        'title': {'style': 'width:480px;'},
    }

    column_labels = dict(
        title='标题',
        category='分类',
        tags='标签',
        summary='简介',
        content='正文',
        created='创建时间',
    )

    def is_accessible(self):
        if current_user.is_authenticated and current_user.username == "cabbage":
            return True
        return False

    # Model handlers
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.author_id = current_user.id
            model.created = datetime.datetime.utcnow()


class CategoryAdmin(ModelView):
    # create_template = "admin/model/a_create.html"
    # edit_template = "admin/model/a_edit.html"

    column_list = ('name',)

    column_searchable_list = ('name',)

    column_labels = dict(
        name='名称',
    )

    form_widget_args = {
        'name': {'style': 'width:320px;'},
    }

    def is_accessible(self):
        if current_user.is_authenticated and current_user.username == "cabbage":
            return True
        return False


class TagAdmin(ModelView):
    # create_template = "admin/model/a_create.html"
    # edit_template = "admin/model/a_edit.html"

    column_list = ('name',)

    column_searchable_list = ('name',)

    form_excluded_columns = 'articles'

    # column_formatters = dict(view_on_site=view_on_site)

    column_labels = dict(
        name='名称',
    )

    form_widget_args = {
        'name': {'style': 'width:320px;'},
    }

    def is_accessible(self):
        if current_user.is_authenticated and current_user.username == "cabbage":
            return True
        return False
